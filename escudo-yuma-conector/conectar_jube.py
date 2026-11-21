"""Conecta el conector Escudo Yuma (/evaluar) con Jube.

Flujo:
  1. Lee una operación de ejemplo (o un JSON propio) y la envía a  POST {CONECTOR}/evaluar.
  2. Traduce los puntajes 0-1000 a los campos que Jube espera (Request XPath):
       score_sim_swapping, score_cuenta_mula, score_phishing, n_salidas_60min
  3. Envía el evento a  POST {JUBE}/api/Invoke/EntityAnalysisModel/{GUID}.
     Las reglas SIM_SWAPPING_YUMA, MULA_YUMA, PHISHING_QR_YUMA y VELOCIDAD_YUMA
     (ya creadas y aprobadas en Jube) abren el caso si se cumple su umbral.

No modifica el código de Jube: solo usa su API pública de invocación.

Credencial: Jube exige una API Key (cabecera x-api-key). Se genera en
  Administration > Users > <usuario> > Generate API Key
y se pasa por variable de entorno; nunca se escribe en este archivo:

  PowerShell:  $env:JUBE_API_KEY = "<tu clave>"
  Uso:         python conectar_jube.py --caso sim_swapping

Variables opcionales: CONECTOR_URL (def. http://localhost:8000),
JUBE_URL (def. http://localhost:5001), JUBE_MODEL_GUID.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime

CONECTOR_URL = os.environ.get("CONECTOR_URL", "http://localhost:8000")
JUBE_URL = os.environ.get("JUBE_URL", "http://localhost:5001")
# Modelo "Detailed Account Financial Transactions" (GUID leído de la base de datos de Jube)
JUBE_MODEL_GUID = os.environ.get("JUBE_MODEL_GUID", "90c425fd-101a-420b-91d1-cb7a24a969cc")

# Umbrales del conector (los mismos que usan las reglas de Jube)
UMBRALES = (("critico", 800), ("alto", 600), ("medio", 300))

CASOS = {
    # Toma de cuenta con cambio de SIM: debe dar sim_swapping = 1000
    "sim_swapping": {
        "id_transaccion": "T-SIM-0001", "id_cliente": "C-DEMO-SIM",
        "tipo_operacion": "transferencia_inmediata", "canal": "app",
        "monto_cop": 900000, "saldo_antes_cop": 1000000, "tipo_destino": "otra_entidad",
        "destino_nuevo": True, "dispositivo_nuevo": True, "cambio_clave_24h": True,
        "cambio_sim_48h": True, "min_registro_dispositivo": 10,
    },
    # Destino mula: fraude previo + muchos remitentes
    "mula": {
        "id_transaccion": "T-MULA-0001", "id_cliente": "C-DEMO-MULA",
        "tipo_operacion": "transferencia_inmediata", "canal": "app",
        "monto_cop": 300000, "saldo_antes_cop": 2000000, "tipo_destino": "cuenta_yuma",
        "destino_nuevo": True, "fi_all": 8, "dest_fraude_previo": True,
    },
    # Engaño QR: destino nuevo, monto 6x el promedio
    "phishing": {
        "id_transaccion": "T-QR-0001", "id_cliente": "C-DEMO-QR",
        "tipo_operacion": "pago_qr", "canal": "qr", "monto_cop": 250000,
        "saldo_antes_cop": 600000, "tipo_destino": "comercio", "destino_nuevo": True,
        "promedio_monto_cliente": 40000,
    },
    # Cliente normal: no debe crear caso
    "normal": {
        "id_transaccion": "T-OK-0001", "id_cliente": "C-DEMO-OK",
        "tipo_operacion": "pago_qr", "canal": "qr", "monto_cop": 20000,
        "saldo_antes_cop": 900000, "tipo_destino": "comercio",
    },
}


def _post(url: str, payload: dict, headers: dict | None = None, timeout: int = 30) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        return 0, f"No se pudo conectar a {url}: {e.reason}"


def nivel(puntaje: int) -> str:
    return next((n for n, u in UMBRALES if puntaje >= u), "bajo")


def evaluar(operacion: dict) -> dict:
    estado, cuerpo = _post(f"{CONECTOR_URL}/evaluar", operacion)
    if estado != 200:
        raise SystemExit(f"[conector] /evaluar respondió {estado}: {cuerpo[:300]}")
    return json.loads(cuerpo)


def a_payload_jube(operacion: dict, ev: dict) -> dict:
    """Campos que Jube lee por XPath ($.campo). AccountId es la clave del caso."""
    return {
        "AccountId": operacion["id_cliente"],
        "TxnId": operacion["id_transaccion"],
        "TxnDateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "CurrencyAmount": str(operacion["monto_cop"]),
        "score_sim_swapping": ev["sim_swapping"]["puntaje"],
        "score_cuenta_mula": ev["cuenta_mula"]["puntaje"],
        "score_phishing": ev["phishing"]["puntaje"],
        "n_salidas_60min": int(operacion.get("n_salidas_60min", 0)),
    }


def enviar_a_jube(payload: dict, api_key: str) -> tuple[int, str]:
    url = f"{JUBE_URL}/api/Invoke/EntityAnalysisModel/{JUBE_MODEL_GUID}"
    return _post(url, payload, headers={"x-api-key": api_key}, timeout=60)


def main() -> int:
    ap = argparse.ArgumentParser(description="Envía una evaluación del conector a Jube")
    ap.add_argument("--caso", choices=sorted(CASOS), default="sim_swapping")
    ap.add_argument("--json", help="Ruta de un JSON con una operación propia (campos de /evaluar)")
    ap.add_argument("--solo-evaluar", action="store_true", help="No envía a Jube (solo muestra los puntajes)")
    a = ap.parse_args()

    operacion = json.load(open(a.json, encoding="utf-8")) if a.json else CASOS[a.caso]
    ev = evaluar(operacion)
    mx = ev["puntaje_maximo"]
    print(f"[conector] {ev['id_transaccion']}  sim_swapping={ev['sim_swapping']['puntaje']}  "
          f"cuenta_mula={ev['cuenta_mula']['puntaje']}  phishing={ev['phishing']['puntaje']}  "
          f"máximo={mx} ({nivel(mx)})  principal={ev['modalidad_principal']}")
    if a.solo_evaluar:
        return 0

    api_key = os.environ.get("JUBE_API_KEY", "").strip()
    if not api_key:
        print("[jube] Falta la variable de entorno JUBE_API_KEY (genera una en Administration > Users "
              "> Generate API Key).", file=sys.stderr)
        return 2

    payload = a_payload_jube(operacion, ev)
    estado, cuerpo = enviar_a_jube(payload, api_key)
    print(f"[jube] POST /api/Invoke/EntityAnalysisModel/{JUBE_MODEL_GUID} -> HTTP {estado}")
    if estado != 200:
        print(cuerpo[:500], file=sys.stderr)
        return 1
    try:
        print(json.dumps(json.loads(cuerpo), indent=2, ensure_ascii=False)[:2500])
    except ValueError:
        print(cuerpo[:2500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
