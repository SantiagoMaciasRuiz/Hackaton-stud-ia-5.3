#!/usr/bin/env python3
"""
Generador de los datos sintéticos de Yuma Pay (organización ficticia).

SOLO PARA ORGANIZADORES: este archivo describe cómo se simuló el fraude.
No lo compartas con los equipos participantes.

Uso:  python generar_datos.py [carpeta_de_salida]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_Datos"))
import linea_base  # noqa: E402

SEMILLA = 20261112
rng = np.random.default_rng(SEMILLA)
SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "03_Datos"

INICIO = pd.Timestamp("2026-05-01")
FIN = pd.Timestamp("2026-10-31 23:59:59")
DIAS = (FIN.normalize() - INICIO).days + 1
N_CLIENTES = 6000
N_MULAS = 90
N_LEGITIMAS = 118_000

DEPARTAMENTOS = ["Bogotá D.C.", "Antioquia", "Valle del Cauca", "Cundinamarca", "Atlántico", "Santander",
                 "Bolívar", "Norte de Santander", "Tolima", "Risaralda", "Caldas", "Nariño", "Córdoba",
                 "Huila", "Meta", "Boyacá", "Magdalena", "Cesar", "Cauca", "Quindío"]
P_DEP = np.array([22, 15, 10, 6, 6, 5, 4, 3, 3, 3, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2, 2, 2, 2], dtype=float)
P_DEP /= P_DEP.sum()

TIPOS = ["transferencia_inmediata", "pago_qr", "retiro_corresponsal", "retiro_cajero",
         "pago_servicios", "recarga_celular", "compra_tarjeta_virtual"]
P_TIPOS = np.array([0.42, 0.22, 0.09, 0.05, 0.10, 0.08, 0.04])
MEDIANA = dict(zip(TIPOS, [60_000, 28_000, 150_000, 200_000, 85_000, 10_000, 55_000]))
SIGMA = dict(zip(TIPOS, [1.15, 0.9, 0.8, 0.7, 0.7, 0.6, 1.0]))
CANAL = {"retiro_corresponsal": "corresponsal", "retiro_cajero": "cajero"}

# Distribución horaria de la operación legítima
P_HORA = np.array([0.5, 0.3, 0.2, 0.2, 0.3, 0.8, 2.2, 4.0, 5.5, 6.2, 6.6, 6.9, 7.2, 6.6, 6.2,
                   6.2, 6.4, 6.8, 7.0, 6.5, 5.3, 4.0, 2.4, 1.2])
P_HORA /= P_HORA.sum()


def id_dispositivo():
    return "D" + "".join(rng.choice(list("0123456789ABCDEF"), 7))


def redondear(monto, tipo):
    paso = 10_000 if tipo.startswith("retiro") else (1_000 if tipo == "recarga_celular" else 100)
    return int(max(paso, round(monto / paso) * paso))


# ---------------------------------------------------------------- clientes
clientes = pd.DataFrame({"id_cliente": [f"C{n:05d}" for n in range(1, N_CLIENTES + 1)]})
clientes["tipo_cliente"] = rng.choice(["persona", "microcomerciante"], N_CLIENTES, p=[0.85, 0.15])
clientes["departamento"] = rng.choice(DEPARTAMENTOS, N_CLIENTES, p=P_DEP)
clientes["rango_edad"] = rng.choice(["18-25", "26-35", "36-45", "46-60", "60+"], N_CLIENTES, p=[0.30, 0.34, 0.20, 0.12, 0.04])
antiguos = pd.Timestamp("2019-06-01") + pd.to_timedelta(rng.integers(0, (INICIO - pd.Timestamp("2019-06-01")).days, N_CLIENTES), unit="D")
nuevos = INICIO + pd.to_timedelta(rng.integers(0, DIAS - 20, N_CLIENTES), unit="D")
es_nuevo = rng.random(N_CLIENTES) < 0.06
clientes["fecha_vinculacion"] = np.where(es_nuevo, nuevos, antiguos)
mulas_idx = rng.choice(N_CLIENTES, N_MULAS, replace=False)
clientes["cuenta_mula_confirmada"] = 0
clientes.loc[mulas_idx, "cuenta_mula_confirmada"] = 1
clientes.loc[mulas_idx, "tipo_cliente"] = "persona"
clientes.loc[mulas_idx, "fecha_vinculacion"] = INICIO + pd.to_timedelta(rng.integers(0, DIAS - 35, N_MULAS), unit="D")
clientes["fecha_vinculacion"] = pd.to_datetime(clientes["fecha_vinculacion"])
clientes["canal_vinculacion"] = rng.choice(["app", "corresponsal", "referido"], N_CLIENTES, p=[0.82, 0.08, 0.10])

escala = rng.lognormal(0, 0.5, N_CLIENTES) * np.where(clientes["tipo_cliente"] == "microcomerciante", 2.5, 1.0)
actividad = rng.lognormal(0, 0.8, N_CLIENTES) * np.where(clientes["tipo_cliente"] == "microcomerciante", 3.0, 1.0)
actividad[mulas_idx] *= 0.15
dispositivos = [[id_dispositivo() for _ in range(rng.choice([1, 2], p=[0.8, 0.2]))] for _ in range(N_CLIENTES)]
ids = clientes["id_cliente"].to_numpy()
vinc = clientes["fecha_vinculacion"].to_numpy()
dep = clientes["departamento"].to_numpy()


def destino_externo():
    return f"EXT{rng.integers(10000, 99999)}"


destinos_habituales = []
comercios_habituales = []
for i in range(N_CLIENTES):
    k = rng.integers(2, 9)
    destinos_habituales.append([ids[rng.integers(0, N_CLIENTES)] if rng.random() < 0.55 else destino_externo() for _ in range(k)])
    comercios_habituales.append([f"COM{rng.integers(1, 1500):04d}" for _ in range(rng.integers(3, 11))])
MULAS_EXTERNAS = [destino_externo() for _ in range(120)]
COMERCIOS_FRAUDE = [f"COM{n:04d}" for n in rng.choice(np.arange(1500, 1700), 40, replace=False)]

filas = []


def agregar(ts, c, tipo, monto, saldo, destino, tipo_destino, destino_nuevo, disp, disp_nuevo,
            clave=0, sim=0, dep_ip=None, fraude=0, modalidad=""):
    dep_ip = dep_ip or dep[c]
    filas.append(dict(
        fecha_hora=ts, id_cliente=ids[c], tipo_operacion=tipo, canal=CANAL.get(tipo, "app"),
        monto_cop=int(monto), saldo_antes_cop=int(max(saldo, monto)), id_destino=destino,
        tipo_destino=tipo_destino, destino_nuevo=int(destino_nuevo), id_dispositivo=disp,
        dispositivo_nuevo=int(disp_nuevo), cambio_clave_24h=int(clave), cambio_sim_48h=int(sim),
        departamento_ip=dep_ip, ip_departamento_distinto=int(dep_ip != dep[c]),
        es_fraude=int(fraude), modalidad_fraude=modalidad, idx_c=c))


def otro_departamento(c):
    while True:
        d = rng.choice(DEPARTAMENTOS, p=P_DEP)
        if d != dep[c]:
            return d


def destino_legitimo(c, tipo):
    if tipo == "transferencia_inmediata":
        if rng.random() < 0.82:
            d = destinos_habituales[c][rng.integers(0, len(destinos_habituales[c]))]
            return d, ("cuenta_yuma" if d.startswith("C") else "otra_entidad"), 0
        d = ids[rng.integers(0, N_CLIENTES)] if rng.random() < 0.5 else destino_externo()
        return d, ("cuenta_yuma" if d.startswith("C") else "otra_entidad"), 1
    if tipo in ("pago_qr", "compra_tarjeta_virtual"):
        if rng.random() < 0.75:
            return comercios_habituales[c][rng.integers(0, len(comercios_habituales[c]))], "comercio", 0
        return f"COM{rng.integers(1, 1500):04d}", "comercio", 1
    if tipo == "retiro_corresponsal":
        return f"COR{rng.integers(1, 400):03d}", "corresponsal", int(rng.random() < 0.3)
    if tipo == "retiro_cajero":
        return f"CAJ{rng.integers(1, 250):03d}", "cajero", int(rng.random() < 0.3)
    if tipo == "pago_servicios":
        return f"SRV{rng.integers(1, 60):02d}", "servicio", int(rng.random() < 0.05)
    return f"OPE{rng.integers(1, 5):02d}", "operador", 0


# ------------------------------------------------- transacciones legítimas
dia_num = np.arange(DIAS)
fechas = INICIO + pd.to_timedelta(dia_num, unit="D")
peso_dia = np.ones(DIAS)
peso_dia[np.isin(fechas.day, [1, 15, 16, 30, 31])] = 1.6
peso_dia[(fechas.month == 6) & (fechas.day >= 15)] *= 1.2
peso_dia /= peso_dia.sum()

c_leg = rng.choice(N_CLIENTES, N_LEGITIMAS, p=actividad / actividad.sum())
ts_leg = (INICIO + pd.to_timedelta(rng.choice(dia_num, N_LEGITIMAS, p=peso_dia), unit="D")
          + pd.to_timedelta(rng.choice(24, N_LEGITIMAS, p=P_HORA), unit="h")
          + pd.to_timedelta(rng.integers(0, 3600, N_LEGITIMAS), unit="s"))
tipo_leg = rng.choice(TIPOS, N_LEGITIMAS, p=P_TIPOS)

for k in range(N_LEGITIMAS):
    c, ts, tipo = int(c_leg[k]), ts_leg[k], str(tipo_leg[k])
    if ts < vinc[c]:  # la cuenta aún no existía: se reubica después de la vinculación
        ts = pd.Timestamp(vinc[c]) + pd.to_timedelta(int(rng.integers(3600, max(7200, int((FIN - pd.Timestamp(vinc[c])).total_seconds())))), unit="s")
    monto = redondear(rng.lognormal(np.log(MEDIANA[tipo] * escala[c]), SIGMA[tipo]), tipo)
    monto = min(monto, 9_000_000)
    if rng.random() < 0.07 and tipo == "transferencia_inmediata":
        saldo = monto * rng.uniform(1.0, 1.08)       # el cliente saca casi todo lo que tiene
    else:
        saldo = monto / max(rng.beta(1.2, 3.0), 0.02)
    disp_nuevo = rng.random() < 0.02
    disp = id_dispositivo() if disp_nuevo else dispositivos[c][rng.integers(0, len(dispositivos[c]))]
    dep_ip = otro_departamento(c) if rng.random() < 0.04 else None   # viajes
    d, td, dn = destino_legitimo(c, tipo)
    agregar(ts, c, tipo, monto, saldo, d, td, dn, disp, disp_nuevo,
            clave=rng.random() < (0.05 if disp_nuevo else 0.012), sim=rng.random() < 0.004, dep_ip=dep_ip)

# Ráfagas legítimas: comerciantes que pagan a varios proveedores seguidos
comerciantes = np.flatnonzero(clientes["tipo_cliente"].to_numpy() == "microcomerciante")
for _ in range(260):
    c = int(rng.choice(comerciantes))
    t = INICIO + pd.to_timedelta(int(rng.integers(0, DIAS)), unit="D") + pd.to_timedelta(int(rng.integers(8 * 60, 19 * 60)), unit="m")
    if t < vinc[c]:
        continue
    saldo = rng.lognormal(np.log(2_500_000), 0.6)
    for _ in range(rng.integers(4, 7)):
        monto = redondear(rng.lognormal(np.log(220_000), 0.7), "transferencia_inmediata")
        d, td, dn = destino_legitimo(c, "transferencia_inmediata")
        agregar(t, c, "transferencia_inmediata", monto, saldo, d, td, dn, dispositivos[c][0], 0)
        saldo = max(saldo - monto, 50_000)
        t += pd.to_timedelta(int(rng.integers(60, 600)), unit="s")

# --------------------------------------------------------------- fraude
no_mulas = np.setdiff1d(np.arange(N_CLIENTES), mulas_idx)
antiguos_idx = no_mulas[vinc[no_mulas] < np.datetime64(INICIO)]
eventos_fraude = []  # precursores que luego se vuelven eventos de la app


def momento(p_noche):
    dia = INICIO + pd.to_timedelta(int(rng.integers(0, DIAS)), unit="D")
    if rng.random() < p_noche:
        hora = rng.choice([23, 0, 1, 2, 3, 4])
    else:
        hora = rng.integers(7, 23)
    return dia + pd.to_timedelta(int(hora) * 3600 + int(rng.integers(0, 3600)), unit="s")


def mula_destino(ts):
    activas = [m for m in mulas_idx if vinc[m] <= np.datetime64(ts) <= vinc[m] + np.timedelta64(45, "D")]
    if activas and rng.random() < 0.6:
        return ids[int(rng.choice(activas))], "cuenta_yuma"
    return MULAS_EXTERNAS[rng.integers(0, len(MULAS_EXTERNAS))], "otra_entidad"


def repartir(total, n, fraccionado):
    if fraccionado:  # montos partidos para quedar bajo los topes de las reglas
        return [redondear(rng.uniform(90_000, 240_000), "transferencia_inmediata") for _ in range(n)]
    pesos = rng.dirichlet(np.ones(n) * 2)
    return [redondear(max(total * p, 30_000), "transferencia_inmediata") for p in pesos]


def robo_de_cuenta(modalidad, n_incidentes, mediana_saldo, p_noche, p_disp_nuevo, p_clave, sim):
    for _ in range(n_incidentes):
        c = int(rng.choice(antiguos_idx))
        t = momento(p_noche)
        saldo = max(rng.lognormal(np.log(mediana_saldo), 0.9), 150_000)
        n = int(rng.integers(2, 6 if modalidad == "toma_de_cuenta" else 5))
        fraccionado = rng.random() < 0.45
        montos = repartir(saldo * rng.uniform(0.6, 1.0), n, fraccionado)
        disp_nuevo = rng.random() < p_disp_nuevo
        disp = id_dispositivo() if disp_nuevo else dispositivos[c][0]
        clave = rng.random() < p_clave
        dep_ip = otro_departamento(c) if rng.random() < 0.55 else None
        eventos_fraude.append(dict(c=c, t=t, disp=disp, disp_nuevo=disp_nuevo, clave=clave, sim=sim, dep_ip=dep_ip or dep[c], fallidos=int(rng.integers(0, 6))))
        for j, monto in enumerate(montos):
            monto = min(monto, int(saldo))
            if monto < 20_000:
                break
            if modalidad == "sim_swapping" and j == n - 1 and rng.random() < 0.3:
                tipo, d, td = "retiro_cajero", f"CAJ{rng.integers(1, 250):03d}", "cajero"
                monto = redondear(monto, tipo)
            else:
                tipo = "transferencia_inmediata"
                d, td = mula_destino(t)
            agregar(t, c, tipo, monto, saldo, d, td, 1, disp, disp_nuevo, clave=clave, sim=sim,
                    dep_ip=dep_ip, fraude=1, modalidad=modalidad)
            saldo -= monto
            t += pd.to_timedelta(int(rng.integers(50, 400)), unit="s")


robo_de_cuenta("toma_de_cuenta", 210, 700_000, p_noche=0.40, p_disp_nuevo=0.85, p_clave=0.70, sim=0)
robo_de_cuenta("sim_swapping", 70, 1_800_000, p_noche=0.50, p_disp_nuevo=0.95, p_clave=0.50, sim=1)

# Ingeniería social: el propio cliente envía el dinero convencido por un falso asesor
for _ in range(160):
    c = int(rng.choice(antiguos_idx))
    t = INICIO + pd.to_timedelta(int(rng.integers(0, DIAS)), unit="D") + pd.to_timedelta(int(rng.integers(9 * 3600, 20 * 3600)), unit="s")
    saldo = max(rng.lognormal(np.log(520_000), 0.8), 80_000)
    for _ in range(rng.choice([1, 2], p=[0.65, 0.35])):
        monto = redondear(saldo * rng.uniform(0.3, 0.95), "transferencia_inmediata")
        if monto < 20_000:
            break
        d, td = mula_destino(t)
        agregar(t, c, "transferencia_inmediata", monto, saldo, d, td, 1, dispositivos[c][0], 0, fraude=1, modalidad="ingenieria_social")
        saldo -= monto
        t += pd.to_timedelta(int(rng.integers(120, 900)), unit="s")

# Engaño con QR: pago a un comercio falso
for _ in range(95):
    c = int(rng.choice(antiguos_idx))
    t = momento(0.05)
    monto = redondear(rng.lognormal(np.log(160_000), 0.7), "pago_qr")
    agregar(t, c, "pago_qr", monto, monto / max(rng.beta(2, 2), 0.1), COMERCIOS_FRAUDE[rng.integers(0, 40)], "comercio", 1,
            dispositivos[c][0], 0, fraude=1, modalidad="engano_qr")

# Cuentas mula: retiran o reenvían rápido el dinero que reciben
for m in mulas_idx:
    t = pd.Timestamp(vinc[m]) + pd.to_timedelta(int(rng.integers(1, 13)), unit="D") + pd.to_timedelta(int(rng.integers(7 * 3600, 22 * 3600)), unit="s")
    for _ in range(rng.integers(3, 9)):
        if t > FIN:
            break
        if rng.random() < 0.6:
            tipo = str(rng.choice(["retiro_corresponsal", "retiro_cajero"]))
            d, td = (f"COR{rng.integers(1, 400):03d}", "corresponsal") if tipo == "retiro_corresponsal" else (f"CAJ{rng.integers(1, 250):03d}", "cajero")
            monto = redondear(rng.uniform(150_000, 1_600_000), tipo)
        else:
            tipo, d, td = "transferencia_inmediata", MULAS_EXTERNAS[rng.integers(0, len(MULAS_EXTERNAS))], "otra_entidad"
            monto = redondear(rng.uniform(200_000, 1_900_000), tipo)
        agregar(t, int(m), tipo, monto, monto * rng.uniform(1.0, 1.15), d, td, int(rng.random() < 0.7),
                dispositivos[m][0], 0, fraude=1, modalidad="cuenta_mula")
        t += pd.to_timedelta(int(rng.integers(1800, 3 * 86400)), unit="s")

# ------------------------------------------------------------ ensamblar
tx = pd.DataFrame(filas)
tx = tx[tx["fecha_hora"] <= FIN].sort_values("fecha_hora", kind="stable").reset_index(drop=True)
tx.insert(0, "id_transaccion", [f"T{n:08d}" for n in range(1, len(tx) + 1)])
tx["antiguedad_cuenta_dias"] = (tx["fecha_hora"] - pd.to_datetime(vinc[tx["idx_c"].to_numpy()])).dt.days.clip(lower=0)
columnas = ["id_transaccion", "fecha_hora", "id_cliente", "tipo_operacion", "canal", "monto_cop", "saldo_antes_cop",
            "id_destino", "tipo_destino", "destino_nuevo", "id_dispositivo", "dispositivo_nuevo", "cambio_clave_24h",
            "cambio_sim_48h", "departamento_ip", "ip_departamento_distinto", "antiguedad_cuenta_dias",
            "es_fraude", "modalidad_fraude"]

# ------------------------------------------------------------- alertas
evaluada, reglas = linea_base.evaluar(tx[columnas].copy())
evaluada = evaluada.set_index("id_transaccion").loc[tx["id_transaccion"]].reset_index()
al = evaluada[evaluada["alertada"]].copy()
lote = al["fecha_hora"].dt.ceil("15min") + pd.to_timedelta(rng.integers(60, 240, len(al)), unit="s")
al["fecha_hora_alerta"] = lote
al["severidad"] = al["reglas_activadas"].apply(lambda s: max((linea_base.SEVERIDAD[r] for r in s.split("|")), key=linea_base.ORDEN.get))
p_rev = al["severidad"].map({"alta": 0.50, "media": 0.33, "baja": 0.22}).to_numpy()
revisada = rng.random(len(al)) < p_rev
al["estado"] = np.where(revisada, "revisada", "sin_revisar")
al["minutos_hasta_revision"] = np.where(revisada, np.round(rng.lognormal(np.log(170), 0.8, len(al))).astype(int), np.nan)
al["decision_analista"] = np.where(revisada, np.where(al["es_fraude"] == 1, "fraude_confirmado", "falso_positivo"), "")
al["accion"] = np.where(~revisada, "", np.where(al["es_fraude"] == 1, "bloqueo_de_cuenta_y_reporte",
                        np.where(rng.random(len(al)) < 0.15, "bloqueo_preventivo_levantado", "ninguna")))
al = al.sort_values("fecha_hora_alerta", kind="stable").reset_index(drop=True)
al.insert(0, "id_alerta", [f"A{n:07d}" for n in range(1, len(al) + 1)])
alertas = al[["id_alerta", "id_transaccion", "id_cliente", "fecha_hora_alerta", "reglas_activadas", "severidad",
              "estado", "minutos_hasta_revision", "decision_analista", "accion"]].copy()
alertas["minutos_hasta_revision"] = alertas["minutos_hasta_revision"].astype("Int64")

# ------------------------------------------------- eventos de la aplicación
ev = []
SO = ["Android", "Android", "Android", "iOS"]


def evento(ts, c, tipo, disp, dep_ip, resultado="exitoso"):
    ev.append(dict(fecha_hora=ts, id_cliente=ids[c], tipo_evento=tipo, id_dispositivo=disp,
                   sistema_operativo=SO[sum(map(ord, disp)) % 4], departamento_ip=dep_ip, resultado=resultado))


ya = set()
for f in tx.itertuples(index=False):
    c, ts = f.idx_c, f.fecha_hora
    if f.es_fraude and f.modalidad_fraude in ("toma_de_cuenta", "sim_swapping"):
        continue  # se generan abajo, una vez por incidente
    if f.dispositivo_nuevo and (c, f.id_dispositivo) not in ya:
        ya.add((c, f.id_dispositivo))
        evento(ts - pd.to_timedelta(int(rng.integers(120, 20 * 3600)), unit="s"), c, "registro_dispositivo", f.id_dispositivo, f.departamento_ip)
    if f.cambio_clave_24h and (c, "clave", ts.date()) not in ya:
        ya.add((c, "clave", ts.date()))
        evento(ts - pd.to_timedelta(int(rng.integers(300, 22 * 3600)), unit="s"), c, "cambio_clave", f.id_dispositivo, f.departamento_ip)
    if f.cambio_sim_48h and (c, "sim", ts.date()) not in ya:
        ya.add((c, "sim", ts.date()))
        evento(ts - pd.to_timedelta(int(rng.integers(3600, 46 * 3600)), unit="s"), c, "cambio_sim_detectado", f.id_dispositivo, f.departamento_ip)
    if f.canal == "app" and rng.random() < 0.40:
        t_login = ts - pd.to_timedelta(int(rng.integers(20, 600)), unit="s")
        if rng.random() < 0.03:
            evento(t_login - pd.to_timedelta(int(rng.integers(10, 90)), unit="s"), c, "inicio_sesion", f.id_dispositivo, f.departamento_ip, "fallido")
        evento(t_login, c, "inicio_sesion", f.id_dispositivo, f.departamento_ip)

for e in eventos_fraude:
    t = e["t"]
    if e["sim"]:
        evento(t - pd.to_timedelta(int(rng.integers(1800, 30 * 3600)), unit="s"), e["c"], "cambio_sim_detectado", e["disp"], e["dep_ip"])
    t0 = t - pd.to_timedelta(int(rng.integers(240, 1500)), unit="s")
    for j in range(e["fallidos"]):
        evento(t0 + pd.to_timedelta(j * int(rng.integers(8, 40)), unit="s"), e["c"], "inicio_sesion", e["disp"], e["dep_ip"], "fallido")
    if e["disp_nuevo"]:
        evento(t0 + pd.to_timedelta(200, unit="s"), e["c"], "registro_dispositivo", e["disp"], e["dep_ip"])
    if e["clave"]:
        evento(t - pd.to_timedelta(int(rng.integers(60, 200)), unit="s"), e["c"], "cambio_clave", e["disp"], e["dep_ip"])
    evento(t - pd.to_timedelta(int(rng.integers(15, 55)), unit="s"), e["c"], "inicio_sesion", e["disp"], e["dep_ip"])

eventos = pd.DataFrame(ev)
eventos = eventos[eventos["fecha_hora"] >= INICIO - pd.Timedelta(days=2)].sort_values("fecha_hora", kind="stable").reset_index(drop=True)
eventos.insert(0, "id_evento", [f"E{n:08d}" for n in range(1, len(eventos) + 1)])

# ------------------------------------------------------------- escribir
SALIDA.mkdir(parents=True, exist_ok=True)
fmt = "%Y-%m-%d %H:%M:%S"
tx[columnas].to_csv(SALIDA / "transacciones.csv", index=False, date_format=fmt, encoding="utf-8-sig")
alertas.to_csv(SALIDA / "alertas.csv", index=False, date_format=fmt, encoding="utf-8-sig")
eventos.to_csv(SALIDA / "eventos_app.csv", index=False, date_format=fmt, encoding="utf-8-sig")
clientes.to_csv(SALIDA / "clientes.csv", index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")

print(f"clientes {len(clientes)} · transacciones {len(tx)} · alertas {len(alertas)} · eventos {len(eventos)}")
print(f"alertas revisadas: {100 * revisada.mean():.1f} %")
linea_base.imprimir_indicadores(evaluada, linea_base.aplicar_reglas(evaluada))
