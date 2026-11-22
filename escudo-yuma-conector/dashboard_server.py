"""Servidor del dashboard de Escudo Yuma (no modifica app.py).

Sirve dashboard.html y los JSON de casos_prueba/ y reenvía POST /evaluar al conector real
(por defecto http://localhost:8000). Como la página y la API llegan desde el mismo origen
(http://127.0.0.1:8765), el navegador no hace peticiones entre orígenes y no hay errores de CORS.

Ejecutar (con el conector ya corriendo en el puerto 8000):
    python -m uvicorn dashboard_server:app --host 127.0.0.1 --port 8765
Abrir:  http://127.0.0.1:8765/

(Se usa el 8765 porque el 8090 puede estar ocupado por otros programas, p. ej. Wondershare.)
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

AQUI = Path(__file__).resolve().parent
# 127.0.0.1 y no "localhost": en Windows "localhost" prueba primero IPv6 y añade ~2 s a cada petición.
CONECTOR_URL = os.environ.get("CONECTOR_URL", "http://127.0.0.1:8000")
JUBE_URL = os.environ.get("JUBE_URL", "http://127.0.0.1:5001")
NOMBRE_CASO = re.compile(r"^caso[1-4]_[a-z_]+\.json$")  # solo los 4 casos de prueba

app = FastAPI(title="Dashboard Escudo Yuma", docs_url=None, redoc_url=None)


def _get(url: str, timeout: int = 5) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, str(e)


@app.get("/")
def inicio() -> FileResponse:
    return FileResponse(AQUI / "dashboard.html", media_type="text/html; charset=utf-8")


@app.get("/casos_prueba/{nombre}")
def caso(nombre: str) -> FileResponse:
    if not NOMBRE_CASO.match(nombre):
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    ruta = AQUI / "casos_prueba" / nombre
    if not ruta.is_file():
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return FileResponse(ruta, media_type="application/json")


@app.get("/estado")
def estado() -> dict:
    """Estado de las dos piezas que usa la demo (lecturas, sin credenciales)."""
    c_status, c_body = _get(f"{CONECTOR_URL}/salud")
    j_status, _ = _get(f"{JUBE_URL}/api/ready")
    return {
        "conector": {"ok": c_status == 200, "detalle": c_body[:120] if c_status == 200 else "sin respuesta"},
        "jube": {"ok": j_status == 200, "detalle": f"HTTP {j_status}" if j_status else "sin respuesta"},
    }


@app.post("/evaluar")
async def evaluar(request: Request) -> JSONResponse:
    """Reenvía la operación al conector (puerto 8000) y devuelve su respuesta tal cual."""
    cuerpo = await request.body()
    req = urllib.request.Request(
        f"{CONECTOR_URL}/evaluar", data=cuerpo, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return JSONResponse(json.loads(r.read().decode("utf-8")), status_code=r.status)
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read().decode("utf-8", "replace"))
        except ValueError:
            detalle = {"detalle": "Respuesta no válida del conector"}
        return JSONResponse(detalle, status_code=e.code)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return JSONResponse({"detalle": f"No se pudo conectar con el conector: {e}"}, status_code=502)
