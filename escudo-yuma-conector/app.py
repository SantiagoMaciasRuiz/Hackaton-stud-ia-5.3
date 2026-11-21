"""Escudo Yuma - conector de puntajes de riesgo (0 a 1000).

Recibe una operación y devuelve un puntaje por modalidad de fraude:
  - sim_swapping : cambio de SIM + toma del dispositivo/cuenta
  - cuenta_mula  : destino que funciona como cuenta mula
  - phishing     : ingeniería social / engaño QR (la víctima autoriza el pago)

Es un motor de reglas ponderadas y explicable: cada punto del puntaje viene de una
señal concreta y se devuelve como razón. Todavía NO está conectado a Jube.

Ejecutar:  uvicorn app:app --port 8000
"""

from __future__ import annotations

import time
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

VERSION = "0.1.0-reglas"

SALIDAS = {"transferencia_inmediata", "retiro_corresponsal", "retiro_cajero"}
RETIROS = {"retiro_corresponsal", "retiro_cajero"}


# --------------------------------------------------------------------------- #
# Entrada / salida
# --------------------------------------------------------------------------- #
class Operacion(BaseModel):
    """Nombres de campo idénticos a transacciones.csv del reto. Solo los marcados
    como obligatorios son necesarios; los opcionales suben la precisión si llegan."""

    id_transaccion: str
    id_cliente: str
    tipo_operacion: str = Field(
        description="transferencia_inmediata, retiro_corresponsal, retiro_cajero, pago_qr, ..."
    )
    canal: str = Field(description="app, qr, corresponsal, cajero, ...")
    monto_cop: float = Field(ge=0)
    saldo_antes_cop: float = Field(ge=0)
    tipo_destino: str = Field(default="desconocido", description="cuenta_yuma, otra_entidad, comercio, ...")
    destino_nuevo: bool = False
    dispositivo_nuevo: bool = False
    cambio_clave_24h: bool = False
    cambio_sim_48h: bool = False
    ip_departamento_distinto: bool = False
    antiguedad_cuenta_dias: int = Field(default=365, ge=0)

    # Variables derivadas (las calcula el feature store; opcionales para pruebas con curl)
    promedio_monto_cliente: float | None = Field(default=None, ge=0, description="Monto promedio histórico del cliente")
    fi_all: int = Field(default=0, ge=0, description="Remitentes distintos acumulados al destino")
    dest_fraude_previo: bool = Field(default=False, description="Destino ligado a un fraude confirmado antes (causal)")
    fallos_60m: int = Field(default=0, ge=0, description="Inicios de sesión fallidos en los últimos 60 min")
    min_registro_dispositivo: int | None = Field(default=None, ge=0, description="Minutos desde que se registró el dispositivo")
    n_salidas_60min: int = Field(default=0, ge=0, description="Salidas de dinero del cliente en los últimos 60 min")


class PuntajeModalidad(BaseModel):
    puntaje: int = Field(ge=0, le=1000)
    nivel: Literal["bajo", "medio", "alto", "critico"]
    razones: list[str]


class Evaluacion(BaseModel):
    id_transaccion: str
    sim_swapping: PuntajeModalidad
    cuenta_mula: PuntajeModalidad
    phishing: PuntajeModalidad
    puntaje_maximo: int = Field(ge=0, le=1000)
    modalidad_principal: str | None
    latencia_ms: float
    version: str


# --------------------------------------------------------------------------- #
# Lógica de puntaje
# --------------------------------------------------------------------------- #
def _nivel(p: int) -> str:
    if p >= 800:
        return "critico"
    if p >= 600:
        return "alto"
    if p >= 300:
        return "medio"
    return "bajo"


def _resultado(senales: list[tuple[int, str]]) -> PuntajeModalidad:
    """Suma las señales activas, topa en 1000 y ordena las razones de mayor a menor peso."""
    puntaje = min(1000, sum(p for p, _ in senales))
    razones = [t for _, t in sorted(senales, key=lambda s: -s[0])]
    return PuntajeModalidad(puntaje=puntaje, nivel=_nivel(puntaje), razones=razones)


def _ratio_saldo(op: Operacion) -> float:
    return op.monto_cop / op.saldo_antes_cop if op.saldo_antes_cop > 0 else 0.0


def _ratio_media(op: Operacion) -> float | None:
    if op.promedio_monto_cliente and op.promedio_monto_cliente > 0:
        return op.monto_cop / op.promedio_monto_cliente
    return None


def puntaje_sim_swapping(op: Operacion) -> PuntajeModalidad:
    s: list[tuple[int, str]] = []
    if op.cambio_sim_48h:
        s.append((450, "Cambio de SIM en las últimas 48 horas"))
    if op.dispositivo_nuevo:
        s.append((150, "Operación desde un dispositivo nuevo"))
    if op.min_registro_dispositivo is not None and op.min_registro_dispositivo <= 60:
        s.append((100, f"Dispositivo registrado hace {op.min_registro_dispositivo} minutos"))
    if op.cambio_clave_24h:
        s.append((150, "Clave cambiada en las últimas 24 horas"))
    if op.ip_departamento_distinto:
        s.append((50, "Ingreso desde un departamento distinto al habitual"))
    # Los cambios de SIM solo importan si además se intenta sacar el dinero
    if op.cambio_sim_48h and op.tipo_operacion in SALIDAS:
        s.append((100, "Salida de dinero justo después del cambio de SIM"))
    if op.cambio_sim_48h and _ratio_saldo(op) >= 0.8:
        s.append((100, f"El monto es el {_ratio_saldo(op):.0%} del saldo"))
    return _resultado(s)


def puntaje_cuenta_mula(op: Operacion) -> PuntajeModalidad:
    s: list[tuple[int, str]] = []
    if op.dest_fraude_previo:
        s.append((450, "Destino ligado a un fraude confirmado antes"))
    if op.fi_all >= 6 and op.tipo_destino in {"otra_entidad", "cuenta_yuma"}:
        s.append((350, f"Destino que ya recibió de {op.fi_all} remitentes distintos"))
    elif op.fi_all >= 3:
        s.append((120, f"Destino que ya recibió de {op.fi_all} remitentes distintos"))
    if op.destino_nuevo and op.tipo_destino in {"otra_entidad", "cuenta_yuma"}:
        s.append((100, "Primera vez que se envía a este destino"))
    if op.n_salidas_60min >= 3:
        s.append((100, f"{op.n_salidas_60min} salidas de dinero en la última hora"))
    if op.tipo_operacion in RETIROS and op.n_salidas_60min >= 2:
        s.append((100, "Retiro en efectivo tras varias salidas seguidas"))
    return _resultado(s)


def puntaje_phishing(op: Operacion) -> PuntajeModalidad:
    s: list[tuple[int, str]] = []
    es_qr = op.canal == "qr" or op.tipo_operacion == "pago_qr"
    if es_qr and op.destino_nuevo and op.monto_cop >= 50_000:
        s.append((400, "Pago QR a un destino nuevo por un monto relevante"))
    elif op.destino_nuevo:
        s.append((150, "Primera vez que se envía a este destino"))
    if op.fallos_60m >= 3:
        s.append((200, f"{op.fallos_60m} intentos fallidos de inicio de sesión en la última hora"))
    if _ratio_saldo(op) >= 0.5:
        s.append((150, f"El monto es el {_ratio_saldo(op):.0%} del saldo"))
    rm = _ratio_media(op)
    if rm is not None and rm > 3:
        s.append((150, f"Monto {rm:.1f} veces superior al promedio del cliente"))
    if op.cambio_clave_24h:
        s.append((100, "Clave cambiada en las últimas 24 horas"))
    if op.dispositivo_nuevo:
        s.append((100, "Operación desde un dispositivo nuevo"))
    # La víctima autoriza ella misma: sin cambio de SIM, un destino nuevo con monto alto es la señal central
    if op.destino_nuevo and op.monto_cop >= 500_000 and op.tipo_operacion == "transferencia_inmediata":
        s.append((100, "Transferencia inmediata de monto alto a destino nuevo"))
    return _resultado(s)


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
app = FastAPI(title="Escudo Yuma - conector", version=VERSION)


@app.get("/salud")
def salud() -> dict:
    return {"estado": "ok", "version": VERSION}


@app.post("/evaluar", response_model=Evaluacion)
def evaluar(op: Operacion) -> Evaluacion:
    t0 = time.perf_counter()
    r = {
        "sim_swapping": puntaje_sim_swapping(op),
        "cuenta_mula": puntaje_cuenta_mula(op),
        "phishing": puntaje_phishing(op),
    }
    maximo = max(r.values(), key=lambda x: x.puntaje)
    principal = next((k for k, v in r.items() if v is maximo), None) if maximo.puntaje > 0 else None
    return Evaluacion(
        id_transaccion=op.id_transaccion,
        **r,
        puntaje_maximo=maximo.puntaje,
        modalidad_principal=principal,
        latencia_ms=round((time.perf_counter() - t0) * 1000, 3),
        version=VERSION,
    )
