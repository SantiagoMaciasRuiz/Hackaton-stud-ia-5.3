#!/usr/bin/env python3
"""
Genera Yuma_Pay_Arquitectura.drawio (cuatro páginas) y una vista previa SVG de cada página.
Uso: python generar_diagramas.py [carpeta_de_salida]
"""
import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "02_Arquitectura"

COLORES = {  # relleno, borde
    "canal": ("#dae8fc", "#6c8ebf"),
    "servicio": ("#d5e8d4", "#82b366"),
    "datos": ("#fff2cc", "#d6b656"),
    "externo": ("#f5f5f5", "#666666"),
    "riesgo": ("#e1d5e7", "#9673a6"),
    "problema": ("#f8cecc", "#b85450"),
    "persona": ("#ffe6cc", "#d79b00"),
    "neutro": ("#ffffff", "#444444"),
}
ZONAS = {
    "azul": ("#f3f8ff", "#6c8ebf"), "verde": ("#f3faf2", "#82b366"), "amarillo": ("#fffbea", "#d6b656"),
    "gris": ("#fafafa", "#999999"), "morado": ("#f7f1fa", "#9673a6"), "rojo": ("#fdf1f0", "#b85450"),
    "naranja": ("#fff6ea", "#d79b00"),
}


class Pagina:
    def __init__(self, nombre, ancho, alto, titulo):
        self.nombre, self.ancho, self.alto, self.titulo = nombre, ancho, alto, titulo
        self.nodos, self.orden, self.aristas = {}, [], []

    # ------------------------------------------------------------ nodos
    def _nodo(self, id_, etiqueta, x, y, w, h, forma, relleno, borde, extra=""):
        self.nodos[id_] = dict(id=id_, etiqueta=etiqueta, x=x, y=y, w=w, h=h, forma=forma,
                               relleno=relleno, borde=borde, extra=extra)
        self.orden.append(id_)

    def zona(self, id_, etiqueta, x, y, w, h, color):
        relleno, borde = ZONAS[color]
        self._nodo(id_, etiqueta, x, y, w, h, "zona", relleno, borde)

    def caja(self, id_, etiqueta, x, y, w=170, h=60, tipo="servicio", forma="caja"):
        relleno, borde = COLORES[tipo]
        self._nodo(id_, etiqueta, x, y, w, h, forma, relleno, borde, "dashed=1;" if tipo == "externo" else "")

    def texto(self, id_, etiqueta, x, y, w, h=30, tam=12):
        self._nodo(id_, etiqueta, x, y, w, h, "texto", "none", "none", f"fontSize={tam};")

    # ----------------------------------------------------------- aristas
    def flecha(self, a, b, etiqueta="", sal=None, ent=None, puntos=None, punteada=False, doble=False, pos=0.0):
        na, nb = self.nodos[a], self.nodos[b]
        if sal is None or ent is None:
            dx = (nb["x"] + nb["w"] / 2) - (na["x"] + na["w"] / 2)
            dy = (nb["y"] + nb["h"] / 2) - (na["y"] + na["h"] / 2)
            if abs(dx) >= abs(dy):
                auto_s, auto_e = ((1, 0.5), (0, 0.5)) if dx > 0 else ((0, 0.5), (1, 0.5))
            else:
                auto_s, auto_e = ((0.5, 1), (0.5, 0)) if dy > 0 else ((0.5, 0), (0.5, 1))
            sal, ent = sal or auto_s, ent or auto_e
        p1 = (na["x"] + na["w"] * sal[0], na["y"] + na["h"] * sal[1])
        p2 = (nb["x"] + nb["w"] * ent[0], nb["y"] + nb["h"] * ent[1])
        if puntos is None:
            puntos = self._ruta(p1, sal, p2, ent)
        self.aristas.append(dict(a=a, b=b, etiqueta=etiqueta, sal=sal, ent=ent, p1=p1, p2=p2,
                                 puntos=puntos, punteada=punteada, doble=doble, pos=pos))

    @staticmethod
    def _lado(f):
        return "H" if f[0] in (0, 1) and f[1] not in (0, 1) else "V"

    def _ruta(self, p1, sal, p2, ent):
        ls, le = self._lado(sal), self._lado(ent)
        if ls == "H" and le == "H":
            if abs(p1[1] - p2[1]) < 1:
                return []
            if sal[0] == ent[0]:
                x = (max(p1[0], p2[0]) + 30) if sal[0] == 1 else (min(p1[0], p2[0]) - 30)
            else:
                x = (p1[0] + p2[0]) / 2
            return [(x, p1[1]), (x, p2[1])]
        if ls == "V" and le == "V":
            if abs(p1[0] - p2[0]) < 1:
                return []
            y = (p1[1] + p2[1]) / 2
            return [(p1[0], y), (p2[0], y)]
        return [(p2[0], p1[1])] if ls == "H" else [(p1[0], p2[1])]

    # ------------------------------------------------------------ draw.io
    def _estilo(self, n):
        base = f"whiteSpace=wrap;html=1;fillColor={n['relleno']};strokeColor={n['borde']};fontColor=#1a1a1a;{n['extra']}"
        f = n["forma"]
        if f == "zona":
            return "rounded=1;arcSize=3;verticalAlign=top;align=left;spacingLeft=10;spacingTop=6;fontStyle=1;fontSize=13;" + base
        if f == "caja":
            return "rounded=1;arcSize=14;fontSize=12;" + base
        if f == "cilindro":
            return "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;fontSize=12;" + base
        if f == "rombo":
            return "rhombus;fontSize=12;" + base
        if f == "terminal":
            return "rounded=1;arcSize=50;fontSize=12;fontStyle=1;" + base
        if f == "nota":
            return "shape=note;size=14;align=left;spacingLeft=8;spacingRight=6;fontSize=11;" + base
        if f == "carril":
            return "rounded=0;fontStyle=1;fontSize=13;" + base
        if f == "texto":
            return f"text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontStyle=1;fontColor=#1a1a1a;{n['extra']}"
        raise ValueError(f)

    @staticmethod
    def _valor(etiqueta, forma):
        partes = [escape(p) for p in etiqueta.split("\n")]
        if forma in ("zona", "texto", "carril", "terminal"):   # el estilo ya define la negrilla
            return "<br>".join(partes)
        return "<br>".join([f"<b>{partes[0]}</b>"] + partes[1:])

    def a_drawio(self, mxfile, indice):
        d = ET.SubElement(mxfile, "diagram", id=f"pagina-{indice}", name=self.nombre)
        m = ET.SubElement(d, "mxGraphModel", dx="1400", dy="900", grid="1", gridSize="10", guides="1", tooltips="1",
                          connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=str(self.ancho),
                          pageHeight=str(self.alto), math="0", shadow="0")
        r = ET.SubElement(m, "root")
        ET.SubElement(r, "mxCell", id="0")
        ET.SubElement(r, "mxCell", id="1", parent="0")
        pre = f"p{indice}-"
        t = ET.SubElement(r, "mxCell", id=pre + "titulo", value=escape(self.titulo), vertex="1", parent="1",
                          style="text;html=1;align=left;verticalAlign=middle;fontSize=20;fontStyle=1;fontColor=#1f3a5f;")
        ET.SubElement(t, "mxGeometry", x="40", y="25", width=str(self.ancho - 80), height="40", **{"as": "geometry"})
        for id_ in self.orden:
            n = self.nodos[id_]
            c = ET.SubElement(r, "mxCell", id=pre + id_, value=self._valor(n["etiqueta"], n["forma"]),
                              style=self._estilo(n), vertex="1", parent="1")
            ET.SubElement(c, "mxGeometry", x=str(n["x"]), y=str(n["y"]), width=str(n["w"]), height=str(n["h"]), **{"as": "geometry"})
        for k, e in enumerate(self.aristas):
            estilo = ("edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;"
                      "strokeColor=#444444;strokeWidth=1.5;fontSize=11;fontColor=#333333;labelBackgroundColor=#ffffff;"
                      f"exitX={e['sal'][0]};exitY={e['sal'][1]};exitDx=0;exitDy=0;entryX={e['ent'][0]};entryY={e['ent'][1]};entryDx=0;entryDy=0;")
            if e["punteada"]:
                estilo += "dashed=1;"
            if e["doble"]:
                estilo += "startArrow=block;startFill=1;"
            c = ET.SubElement(r, "mxCell", id=f"{pre}flecha-{k}", value=escape(e["etiqueta"]), style=estilo, edge="1",
                              parent="1", source=pre + e["a"], target=pre + e["b"])
            g = ET.SubElement(c, "mxGeometry", relative="1", **({"x": str(e["pos"])} if e["pos"] else {}), **{"as": "geometry"})
            if e["puntos"]:
                arr = ET.SubElement(g, "Array", **{"as": "points"})
                for x, y in e["puntos"]:
                    ET.SubElement(arr, "mxPoint", x=str(round(x)), y=str(round(y)))

    # ------------------------------------------------------------ vista previa
    @staticmethod
    def _partir(texto, ancho_px, tam):
        max_c = max(6, int(ancho_px / (tam * 0.56)))
        lineas, actual = [], ""
        for palabra in texto.split():
            if len(actual) + len(palabra) + 1 <= max_c:
                actual = (actual + " " + palabra).strip()
            else:
                lineas.append(actual)
                actual = palabra
        return lineas + [actual] if actual else lineas

    def a_svg(self):
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.ancho}" height="{self.alto}" viewBox="0 0 {self.ancho} {self.alto}" font-family="DejaVu Sans, Arial, sans-serif">',
             '<defs><marker id="fl" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto-start-reverse"><path d="M0,0 L10,4 L0,8 z" fill="#444"/></marker></defs>',
             f'<rect width="{self.ancho}" height="{self.alto}" fill="#ffffff"/>',
             f'<text x="40" y="52" font-size="20" font-weight="bold" fill="#1f3a5f">{escape(self.titulo)}</text>']
        for id_ in self.orden:
            n = self.nodos[id_]
            x, y, w, h, f = n["x"], n["y"], n["w"], n["h"], n["forma"]
            guion = ' stroke-dasharray="6 4"' if "dashed=1" in n["extra"] else ""
            trazo = f'fill="{n["relleno"]}" stroke="{n["borde"]}" stroke-width="1.3"{guion}'
            if f == "texto":
                tam = int(n["extra"].split("fontSize=")[1].split(";")[0])
                for i, linea in enumerate(self._partir(n["etiqueta"], w, tam)):
                    o.append(f'<text x="{x}" y="{y + tam + i * (tam + 4)}" font-size="{tam}" font-weight="bold" fill="#1a1a1a">{escape(linea)}</text>')
                continue
            if f == "zona":
                o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" {trazo}/>')
                o.append(f'<text x="{x + 12}" y="{y + 22}" font-size="13" font-weight="bold" fill="#1a1a1a">{escape(n["etiqueta"])}</text>')
                continue
            if f == "rombo":
                o.append(f'<polygon points="{x + w / 2},{y} {x + w},{y + h / 2} {x + w / 2},{y + h} {x},{y + h / 2}" {trazo}/>')
            elif f == "cilindro":
                o.append(f'<path d="M{x},{y + 10} a{w / 2},10 0 0 1 {w},0 v{h - 20} a{w / 2},10 0 0 1 {-w},0 z" {trazo}/>')
                o.append(f'<path d="M{x},{y + 10} a{w / 2},10 0 0 0 {w},0" fill="none" stroke="{n["borde"]}" stroke-width="1.3"/>')
            elif f == "nota":
                o.append(f'<path d="M{x},{y} h{w - 14} l14,14 v{h - 14} h{-w} z" {trazo}/>')
            else:
                rx = h / 2 if f == "terminal" else (0 if f == "carril" else 8)
                o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" {trazo}/>')
            partes = n["etiqueta"].split("\n")
            margen = 60 if f == "rombo" else 16
            lineas = [(l, True) for l in self._partir(partes[0], w - margen, 12)]
            for p in partes[1:]:
                lineas += [(l, f in ("carril", "terminal")) for l in self._partir(p, w - margen, 11)]
            alto_l = 15
            y0 = y + h / 2 - len(lineas) * alto_l / 2 + 11 + (5 if f == "cilindro" else 0)
            for i, (linea, negrita) in enumerate(lineas):
                if f == "nota":
                    o.append(f'<text x="{x + 9}" y="{y0 + i * alto_l}" font-size="11" {"font-weight=\"bold\"" if negrita else ""} fill="#1a1a1a">{escape(linea)}</text>')
                else:
                    o.append(f'<text x="{x + w / 2}" y="{y0 + i * alto_l}" text-anchor="middle" font-size="{12 if negrita else 11}" {"font-weight=\"bold\"" if negrita else ""} fill="#1a1a1a">{escape(linea)}</text>')
        for e in self.aristas:
            pts = [e["p1"]] + list(e["puntos"]) + [e["p2"]]
            d = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
            guion = ' stroke-dasharray="6 4"' if e["punteada"] else ""
            ini = ' marker-start="url(#fl)"' if e["doble"] else ""
            o.append(f'<polyline points="{d}" fill="none" stroke="#444" stroke-width="1.5"{guion} marker-end="url(#fl)"{ini}/>')
            if e["etiqueta"]:
                largos = [abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:])]
                meta, cx, cy = sum(largos) * (0.5 + e["pos"] / 2), pts[0][0], pts[0][1]
                for (a, b), largo in zip(zip(pts, pts[1:]), largos):
                    if meta <= largo and largo > 0:
                        cx, cy = a[0] + (b[0] - a[0]) * meta / largo, a[1] + (b[1] - a[1]) * meta / largo
                        break
                    meta -= largo
                ancho = len(e["etiqueta"]) * 6.1 + 8
                o.append(f'<rect x="{cx - ancho / 2}" y="{cy - 9}" width="{ancho}" height="17" fill="#ffffff"/>')
                o.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="11" fill="#333">{escape(e["etiqueta"])}</text>')
        o.append("</svg>")
        return "\n".join(o)


# =====================================================================
# Página 1 — Arquitectura actual
# =====================================================================
p1 = Pagina("1. Arquitectura actual", 1500, 860, "Yuma Pay · Arquitectura actual: el fraude se evalúa después de autorizar")
p1.zona("zc", "Canales", 40, 90, 210, 450, "azul")
p1.caja("app", "App móvil\nAndroid y iOS", 60, 140, tipo="canal")
p1.caja("corr", "Corresponsales y cajeros", 60, 240, tipo="canal")
p1.caja("com", "Comercios\nPagos con QR", 60, 340, tipo="canal")
p1.zona("zb", "Borde y acceso", 290, 90, 210, 450, "verde")
p1.caja("gw", "API Gateway y WAF", 310, 140)
p1.caja("auth", "Autenticación\nClave + OTP por SMS", 310, 240)
p1.caja("vinc", "Vinculación digital\nBiometría facial", 310, 340)
p1.zona("zt", "Servicios transaccionales", 540, 90, 420, 450, "verde")
p1.caja("orq", "Orquestador de transacciones\nAutoriza sin consultar riesgo", 560, 140, w=380)
p1.zona("prod", "Servicios de producto", 560, 225, 380, 195, "gris")
p1.caja("s1", "Transferencias inmediatas", 575, 260, w=170, h=60)
p1.caja("s2", "Pagos con QR", 755, 260, w=170, h=60)
p1.caja("s3", "Retiros", 575, 340, w=170, h=60)
p1.caja("s4", "Pagos y recargas", 755, 340, w=170, h=60)
p1.caja("nuc", "Núcleo de depósitos\nSaldos y libro mayor", 560, 450, w=380)
p1.zona("ze", "Externos", 1000, 90, 210, 450, "gris")
p1.caja("spi", "Sistema de pagos inmediatos\ny otras entidades", 1020, 250, h=70, tipo="externo")
p1.caja("red", "Redes de corresponsales\ny cajeros", 1020, 345, h=70, tipo="externo")
p1.zona("zf", "Antifraude actual: fuera de línea, después de la operación", 40, 580, 1170, 230, "rojo")
p1.caja("bd", "BD transaccional", 60, 660, w=165, h=70, tipo="datos", forma="cilindro")
p1.caja("lote", "Extracción por lotes\nCada 15 minutos", 255, 665, w=165, tipo="problema")
p1.caja("reg", "Motor de reglas\n140 reglas estáticas", 450, 665, w=165, tipo="problema")
p1.caja("cola", "Cola de alertas\n≈ 4.000 al día", 645, 665, w=165, tipo="problema")
p1.caja("ana", "12 analistas\nRevisan 1 de cada 3", 840, 665, w=165, tipo="persona")
p1.caja("blo", "Bloqueo manual\ny llamada al cliente", 1035, 665, w=165, tipo="persona")
p1.zona("zg", "Brechas", 1240, 90, 230, 720, "rojo")
p1.caja("g1", "1. Decisión tardía\nLa alerta llega hasta 15 min después. Una transferencia inmediata sale en segundos y no se reversa.", 1255, 130, w=200, h=140, tipo="problema", forma="nota")
p1.caja("g2", "2. Sin contexto\nLas reglas no ven el dispositivo, el comportamiento ni las redes de cuentas mula.", 1255, 290, w=200, h=125, tipo="problema", forma="nota")
p1.caja("g3", "3. Ruido\n92 % de las alertas son falsos positivos y dos tercios quedan sin revisar.", 1255, 435, w=200, h=115, tipo="problema", forma="nota")
p1.caja("g4", "4. Sin aprendizaje\nLos casos confirmados no vuelven a las reglas; se ajustan a mano.", 1255, 570, w=200, h=115, tipo="problema", forma="nota")
p1.flecha("app", "gw")
p1.flecha("corr", "gw", sal=(1, 0.5), ent=(0, 0.5))
p1.flecha("com", "gw", sal=(1, 0.5), ent=(0, 0.75))
p1.flecha("gw", "auth")
p1.flecha("gw", "orq")
p1.flecha("orq", "prod")
p1.flecha("prod", "nuc")
p1.flecha("prod", "spi", sal=(1, 0.3077), ent=(0, 0.5), puntos=[])
p1.flecha("prod", "red", sal=(1, 0.7949), ent=(0, 0.5), puntos=[])
p1.flecha("nuc", "bd", "operación ya autorizada", sal=(0.5, 1), ent=(0.5, 0), puntos=[(750, 560), (142, 560)])
p1.flecha("bd", "lote")
p1.flecha("lote", "reg")
p1.flecha("reg", "cola")
p1.flecha("cola", "ana")
p1.flecha("ana", "blo")
p1.flecha("ana", "reg", "ajuste manual tras cada incidente", sal=(0.5, 1), ent=(0.5, 1), puntos=[(922, 770), (532, 770)], punteada=True)

# =====================================================================
# Página 2 — Arquitectura objetivo
# =====================================================================
p2 = Pagina("2. Arquitectura objetivo", 1570, 910, "Yuma Pay · Arquitectura objetivo: Escudo Yuma decide antes de autorizar")
p2.zona("zc", "Canales", 40, 90, 210, 330, "azul")
p2.caja("app", "App móvil\nAndroid y iOS", 60, 140, tipo="canal")
p2.caja("corr", "Corresponsales y cajeros", 60, 240, tipo="canal")
p2.caja("com", "Comercios\nPagos con QR", 60, 340, tipo="canal")
p2.zona("zb", "Borde y acceso", 290, 90, 210, 330, "verde")
p2.caja("gw", "API Gateway y WAF", 310, 140)
p2.caja("auth", "Autenticación adaptativa\nBiometría y OTP según riesgo", 310, 240)
p2.caja("vinc", "Vinculación digital\nCon prueba de vida", 310, 340)
p2.zona("zt", "Transaccional", 540, 90, 230, 330, "verde")
p2.caja("orq", "Orquestador de transacciones", 560, 140, w=190)
p2.caja("prod", "Servicios de producto", 560, 240, w=190)
p2.caja("nuc", "Núcleo de depósitos", 560, 340, w=190)
p2.zona("ze", "Externos", 810, 200, 210, 125, "gris")
p2.caja("spi", "Sistema de pagos inmediatos\nRecibe solo lo aprobado", 830, 240, tipo="externo")
p2.zona("zr", "Escudo Yuma: decisión de riesgo en línea", 1060, 90, 470, 330, "morado")
p2.caja("dec", "Servicio de decisión de riesgo\nAprobar · desafiar · retener · rechazar", 1080, 140, w=430, tipo="riesgo")
p2.caja("rtr", "Motor de reglas\nen tiempo real", 1080, 240, w=205, tipo="riesgo")
p2.caja("ml", "Modelo de aprendizaje\nautomático", 1305, 240, w=205, tipo="riesgo")
p2.caja("grafo", "Análisis de redes\nCuentas mula", 1080, 340, w=205, tipo="riesgo")
p2.caja("perfil", "Perfil de comportamiento\ny dispositivo", 1305, 340, w=205, tipo="riesgo")
p2.zona("zd", "Datos en tiempo real", 40, 490, 730, 170, "amarillo")
p2.caja("bus", "Bus de eventos\nTransacciones, sesión, SIM", 60, 560, w=190, tipo="datos")
p2.caja("str", "Procesamiento en streaming\nVariables por ventanas", 300, 560, w=190, tipo="datos")
p2.caja("fs", "Almacén de variables\nen línea", 560, 555, w=190, h=70, tipo="datos", forma="cilindro")
p2.zona("zk", "Gestión de casos", 810, 490, 720, 170, "naranja")
p2.caja("cli", "Confirmación con el cliente\nNotificación en la app", 830, 560, w=200, tipo="persona")
p2.caja("ana", "Analistas de fraude", 1070, 560, w=200, tipo="persona")
p2.caja("casos", "Gestión de casos\nCon la explicación del puntaje", 1310, 560, w=200, tipo="persona")
p2.zona("za", "Analítica y aprendizaje: fuera de línea", 40, 700, 970, 170, "amarillo")
p2.caja("lago", "Lago de datos\nHistórico y etiquetas", 60, 765, w=190, h=70, tipo="datos", forma="cilindro")
p2.caja("ent", "Entrenamiento\nde modelos", 300, 770, w=190, tipo="riesgo")
p2.caja("val", "Validación\nPrecisión, sesgo, latencia", 540, 770, w=190, tipo="riesgo")
p2.caja("desp", "Registro y despliegue\nde modelos", 780, 770, w=190, tipo="riesgo")
p2.zona("zx", "Transversal: aplica a todo", 1050, 700, 480, 170, "gris")
p2.caja("obs", "Observabilidad\nTableros y alertas", 1070, 770, w=200, tipo="neutro")
p2.caja("aud", "Auditoría\nRegistro de cada decisión", 1310, 770, w=200, tipo="neutro")
p2.flecha("app", "gw")
p2.flecha("corr", "gw", sal=(1, 0.5), ent=(0, 0.5))
p2.flecha("com", "gw", sal=(1, 0.5), ent=(0, 0.75))
p2.flecha("gw", "auth")
p2.flecha("gw", "orq")
p2.flecha("orq", "dec", "puntaje y decisión · síncrono, < 300 ms", doble=True)
p2.flecha("orq", "prod")
p2.flecha("prod", "nuc")
p2.flecha("prod", "spi")
p2.flecha("dec", "rtr", sal=(0.2384, 1), ent=(0.5, 0), puntos=[])
p2.flecha("dec", "ml", sal=(0.7616, 1), ent=(0.5, 0), puntos=[])
p2.flecha("rtr", "grafo")
p2.flecha("ml", "perfil")
p2.flecha("nuc", "bus", "eventos de transacción, sesión y dispositivo", sal=(0.25, 1), ent=(0.5, 0), puntos=[(607, 455), (155, 455)])
p2.flecha("bus", "str")
p2.flecha("str", "fs")
p2.flecha("fs", "zr", "variables en milisegundos", sal=(0.75, 0), ent=(0.25, 1), puntos=[(702, 472), (1177, 472)])
p2.flecha("zr", "casos", "riesgo alto", sal=(0.7447, 1), ent=(0.5, 0), puntos=[])
p2.flecha("casos", "ana")
p2.flecha("ana", "cli")
p2.flecha("bus", "lago", sal=(0.25, 1), ent=(0.25, 0), puntos=[])
p2.flecha("lago", "ent")
p2.flecha("ent", "val")
p2.flecha("val", "desp")
p2.flecha("casos", "lago", "etiquetas confirmadas: retroalimentación", sal=(0.5, 1), ent=(0.75, 0), puntos=[(1410, 680), (202, 680)], punteada=True, pos=-0.3)
p2.flecha("desp", "zr", "modelo nuevo", sal=(0.0526, 0), ent=(0.5106, 1), puntos=[(790, 445), (1300, 445)], punteada=True)

# =====================================================================
# Página 3 — Flujo de autorización
# =====================================================================
p3 = Pagina("3. Flujo de autorización", 1040, 1130, "Yuma Pay · Flujo de autorización de una transferencia con Escudo Yuma")
p3.caja("ini", "El cliente confirma una transferencia", 400, 90, w=220, tipo="canal", forma="terminal")
p3.caja("a1", "La app envía la solicitud\nIncluye datos del dispositivo", 400, 190, w=220, tipo="canal")
p3.caja("a2", "API Gateway\nValida la sesión y el token", 400, 290, w=220)
p3.caja("a3", "Orquestador\nPide el puntaje de riesgo", 400, 390, w=220)
p3.caja("a4", "Escudo Yuma calcula el puntaje\nReglas + modelo + redes, < 300 ms", 400, 490, w=220, tipo="riesgo")
p3.caja("d1", "¿Nivel de riesgo?", 400, 600, w=220, h=100, tipo="datos", forma="rombo")
p3.caja("ok", "Autorizar\nEnviar al sistema de pagos", 80, 620, w=220, tipo="servicio")
p3.caja("ret", "Retener o rechazar\nEl dinero no sale", 720, 620, w=220, tipo="problema")
p3.caja("ref", "Autenticación reforzada\nBiometría facial en la app", 400, 760, w=220, tipo="persona")
p3.caja("caso", "Crear caso con explicación\nEl analista confirma con el cliente", 720, 760, w=220, tipo="persona")
p3.caja("d2", "¿La supera?", 400, 880, w=220, h=90, tipo="datos", forma="rombo")
p3.caja("fin", "Registrar decisión y etiqueta\nRetroalimenta reglas y modelo", 400, 1030, w=220, tipo="riesgo", forma="terminal")
p3.caja("n1", "Qué cambia frente a hoy\nLa decisión ocurre antes de autorizar. Cada puntaje queda explicado y auditado. Solo el riesgo alto llega al analista.", 720, 380, w=250, h=130, tipo="datos", forma="nota")
p3.flecha("ini", "a1")
p3.flecha("a1", "a2")
p3.flecha("a2", "a3")
p3.flecha("a3", "a4")
p3.flecha("a4", "d1")
p3.flecha("d1", "ok", "bajo")
p3.flecha("d1", "ret", "alto")
p3.flecha("d1", "ref", "medio")
p3.flecha("ref", "d2")
p3.flecha("ret", "caso")
p3.flecha("d2", "ok", "sí", sal=(0, 0.5), ent=(0.5, 1))
p3.flecha("d2", "caso", "no", sal=(1, 0.5), ent=(0, 0.5))
p3.flecha("ok", "fin", sal=(0, 0.5), ent=(0, 0.5), puntos=[(50, 650), (50, 1060)])
p3.flecha("caso", "fin", sal=(0.5, 1), ent=(1, 0.5))

# =====================================================================
# Página 4 — Proceso actual de alertas y reclamaciones
# =====================================================================
p4 = Pagina("4. Proceso actual", 1640, 850, "Yuma Pay · Proceso actual de gestión de alertas y reclamaciones")
carriles = [("Cliente", 90, 120, "azul"), ("Sistemas", 210, 120, "verde"), ("Prevención de Fraude", 330, 230, "naranja"),
            ("Servicio al Cliente", 560, 120, "amarillo"), ("Cumplimiento y Jurídica", 680, 120, "gris")]
for i, (nombre, y, h, color) in enumerate(carriles):
    p4.zona(f"l{i}", "", 40, y, 1560, h, color)
    relleno, borde = ZONAS[color]
    p4._nodo(f"h{i}", nombre, 40, y, 150, h, "carril", relleno, borde)
p4.caja("k1", "Ve un movimiento que no reconoce y lo reporta", 220, 120, w=160, tipo="canal")
p4.caja("k4", "Confirma o niega la operación", 1020, 120, w=160, tipo="canal")
p4.caja("s1", "Operación autorizada\nEl dinero ya salió", 420, 240, w=160)
p4.caja("s2", "Lote cada 15 min\nAplica 140 reglas", 620, 240, w=160, tipo="problema")
p4.caja("s3", "Alerta en la cola\n≈ 4.000 al día", 820, 240, w=160, tipo="problema")
p4.caja("f1", "Analista toma la alerta\nRevisa 1 de cada 3", 820, 360, w=160, tipo="persona")
p4.caja("f2", "Llama al cliente para confirmar", 1020, 360, w=160, tipo="persona")
p4.caja("f3", "¿Es fraude?", 1220, 350, w=160, h=80, tipo="datos", forma="rombo")
p4.caja("f4", "Bloquea la cuenta\nAjusta reglas a mano", 1420, 360, w=160, tipo="persona")
p4.caja("f5", "Cierra la alerta\n92 % son falsos positivos", 1220, 470, w=160, tipo="problema")
p4.caja("f7", "Investiga el caso\nHasta 15 días hábiles", 420, 470, w=160, tipo="problema")
p4.caja("f8", "¿Procede?", 620, 460, w=160, h=80, tipo="datos", forma="rombo")
p4.caja("sc1", "Radica la reclamación", 220, 590, w=160)
p4.caja("sc2", "Devuelve el dinero al cliente", 620, 590, w=160)
p4.caja("sc3", "Niega la reclamación", 820, 590, w=160, tipo="problema")
p4.caja("c2", "Atiende quejas ante la Superintendencia", 820, 710, w=160)
p4.caja("c1", "Reporta la cuenta mula y responde a autoridades", 1420, 710, w=160)
p4.flecha("s1", "s2")
p4.flecha("s2", "s3")
p4.flecha("s3", "f1")
p4.flecha("f1", "f2")
p4.flecha("f2", "k4", doble=True)
p4.flecha("f2", "f3")
p4.flecha("f3", "f4", "sí")
p4.flecha("f3", "f5", "no")
p4.flecha("f4", "c1")
p4.flecha("k1", "sc1")
p4.flecha("sc1", "f7", sal=(1, 0.5), ent=(0.5, 1))
p4.flecha("f7", "f8")
p4.flecha("f8", "sc2", "sí")
p4.flecha("f8", "sc3", "no", sal=(1, 0.5), ent=(0.5, 0))
p4.flecha("sc3", "c2")

PAGINAS = [p1, p2, p3, p4]
NOMBRES = ["1_arquitectura_actual", "2_arquitectura_objetivo", "3_flujo_de_autorizacion", "4_proceso_actual"]

if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "vista_previa").mkdir(exist_ok=True)
    mx = ET.Element("mxfile", host="app.diagrams.net", agent="Yuma Pay", version="24.7.17", type="device")
    for i, p in enumerate(PAGINAS, 1):
        p.a_drawio(mx, i)
        (SALIDA / "vista_previa" / f"{NOMBRES[i - 1]}.svg").write_text(p.a_svg(), encoding="utf-8")
    ET.indent(mx, space="  ")
    ET.ElementTree(mx).write(SALIDA / "Yuma_Pay_Arquitectura.drawio", encoding="utf-8", xml_declaration=True)
    print("ok", len(PAGINAS), "páginas")
