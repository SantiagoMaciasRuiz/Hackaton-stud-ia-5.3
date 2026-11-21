// Genera Caso_de_estudio_Yuma_Pay.docx.  Uso: node construir_caso.js [salida.docx]
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel,
  WidthType, ShadingType, BorderStyle, LevelFormat, AlignmentType, VerticalAlign, Footer, PageNumber,
} = require("docx");

const RAIZ = path.resolve(__dirname, "..");
const F = "Arial";
const ANCHO = 9026;
const AZUL = "0E3A44";

const nb = (t) => t.replace(/(\d) %/g, "$1 %");
function runs(texto, extra = {}) {
  return nb(texto).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((p) =>
    p.startsWith("**") ? new TextRun({ text: p.slice(2, -2), bold: true, font: F, size: 21, ...extra })
                       : new TextRun({ text: p, font: F, size: 21, ...extra }));
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { before: 60, after: 120, line: 288 }, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t })] });
const B = (t) => new Paragraph({ children: runs(t), numbering: { reference: "vin", level: 0 }, spacing: { before: 30, after: 60, line: 276 } });
const N = (t, ref = "num") => new Paragraph({ children: runs(t), numbering: { reference: ref, level: 0 }, spacing: { before: 30, after: 60, line: 276 } });
const nota = (t) => new Paragraph({ children: runs(t, { italics: true, color: "595959", size: 18 }), spacing: { before: 60, after: 160 } });

const borde = { style: BorderStyle.SINGLE, size: 4, color: "B8C7C4" };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };
function tabla(encabezados, filas, anchos) {
  const celda = (t, w, cab) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders: bordes, verticalAlign: VerticalAlign.TOP,
    margins: { top: 80, bottom: 80, left: 110, right: 110 },
    shading: cab ? { type: ShadingType.CLEAR, fill: AZUL, color: "auto" } : undefined,
    children: String(t).split("\n").map((l) => new Paragraph({
      children: cab ? [new TextRun({ text: l, bold: true, color: "FFFFFF", font: F, size: 19 })] : runs(l, { size: 19 }),
      spacing: { before: 20, after: 20 },
    })),
  });
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA }, columnWidths: anchos,
    rows: [new TableRow({ tableHeader: true, children: encabezados.map((t, i) => celda(t, anchos[i], true)) }),
           ...filas.map((f) => new TableRow({ cantSplit: true, children: f.map((t, i) => celda(t, anchos[i], false)) }))],
  });
}
function imagen(archivo, w, h) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(RAIZ, "02_Arquitectura", "vista_previa", archivo)),
      transformation: { width: w, height: h }, altText: { title: archivo, description: archivo, name: archivo } })],
  });
}
const esp = () => new Paragraph({ children: [], spacing: { before: 0, after: 80 } });

const hijos = [
  new Paragraph({ children: [new TextRun({ text: "Caso de estudio", font: F, size: 24, color: "1C8C8C", bold: true })], spacing: { after: 40 } }),
  new Paragraph({ children: [new TextRun({ text: "Escudo Yuma: un sistema antifraude en tiempo real para Yuma Pay", font: F, size: 44, bold: true, color: AZUL })], spacing: { after: 120 } }),
  P("Material para los equipos participantes de la hackatón. Contacto del reto: **John Mazo**, CISO de Yuma Pay, Jmazo@yumapay.online."),
  nota("Yuma Pay S.A. es una organización ficticia creada para la hackatón. Su nombre, sus cifras y sus datos son inventados; ningún registro corresponde a una persona real."),

  H1("1. El reto en una página"),
  P("Yuma Pay detecta el fraude después de que el dinero ya salió de la cuenta. El reto es construir un prototipo que califique el riesgo de cada operación **antes de autorizarla**, en menos de 300 milisegundos, que explique su decisión y que moleste menos a los clientes legítimos que el motor actual."),
  tabla(["Pregunta", "Respuesta"], [
    ["Qué se construye", "Un servicio que recibe una transacción y responde aprobar, desafiar, retener o rechazar, con un puntaje y las razones."],
    ["Con qué datos", "Seis meses de operaciones sintéticas con etiqueta de fraude, eventos de la app, alertas históricas y las reglas vigentes."],
    ["Cómo se mide", "Fraude detectado, falsos positivos, tiempo de respuesta y calidad de la explicación. El sandbox calcula los indicadores."],
    ["Qué hay que superar", "El motor de reglas actual: en la muestra alerta el 62,6 % del fraude, pero el 89,0 % de sus alertas son falsos positivos y llegan tarde."],
  ], [2400, 6626]),

  H1("2. La empresa"),
  P("Yuma Pay es una billetera digital colombiana, 100 % móvil, que opera como sociedad especializada en depósitos y pagos electrónicos. Desde 2019 ofrece depósitos de bajo monto, transferencias inmediatas con llaves, pagos con QR, recargas, pago de servicios, tarjeta débito virtual y retiros en corresponsales."),
  P("Atiende a 4,2 millones de usuarios, en su mayoría jóvenes, trabajadores independientes y microcomerciantes. Procesa cerca de 1,8 millones de transacciones al día con un equipo de 380 personas. La Gerencia de Seguridad de la Información, a cargo del CISO, incluye la célula de Prevención de Fraude."),

  H1("3. El problema"),
  P("El motor antifraude usa unas 140 reglas estáticas y revisa las operaciones por lotes cada 15 minutos. Una transferencia inmediata se completa en segundos y no se puede reversar, así que la alerta llega cuando el dinero ya no está."),
  P("Las reglas tampoco ven el comportamiento del cliente, el dispositivo ni las redes de cuentas que reciben el dinero. El resultado es mucho ruido: los analistas reciben más alertas de las que pueden revisar y la mayoría no son fraude."),
  tabla(["Indicador de la operación real (cifras ficticias)", "Valor"], [
    ["Alertas generadas al día", "≈ 4.000"],
    ["Alertas que resultan falsos positivos", "92 %"],
    ["Alertas que los 12 analistas alcanzan a revisar", "1 de cada 3"],
    ["Casos de fraude confirmados al mes", "2.300 (unos 75 al día)"],
    ["Pérdida mensual por fraude", "COP 1.150 millones"],
    ["Pérdida promedio por caso", "COP 500.000"],
    ["Reclamaciones mensuales relacionadas con fraude", "6.500"],
    ["Tiempo de respuesta a una reclamación", "Hasta 15 días hábiles"],
  ], [6026, 3000]),

  H1("4. Modalidades de fraude"),
  P("Estas cinco modalidades están etiquetadas en los datos. La última columna muestra qué parte de sus operaciones alcanza a alertar hoy el motor de reglas en la muestra."),
  tabla(["Modalidad", "Cómo opera", "Señales en los datos", "Alertado hoy"], [
    ["**Toma de cuenta**\ntoma_de_cuenta", "El delincuente roba la clave con phishing o smishing, entra desde otro celular y vacía la cuenta con varias transferencias seguidas.", "Inicios de sesión fallidos, dispositivo nuevo, cambio de clave, destinos nuevos, montos partidos, horario nocturno.", "60,4 %"],
    ["**Duplicación de SIM**\nsim_swapping", "Duplica la SIM de la víctima para recibir los códigos OTP y tomar el control de la cuenta.", "Cambio de SIM en las 48 horas previas, dispositivo nuevo, saldos altos, a veces un retiro en cajero al final.", "73,9 %"],
    ["**Ingeniería social**\ningenieria_social", "Un falso asesor convence al cliente de enviar el dinero él mismo a una “cuenta segura”.", "Dispositivo y ubicación habituales. Solo delatan el destino nuevo y un monto alto frente al saldo.", "14,8 %"],
    ["**Engaño con QR**\nengano_qr", "La víctima paga con QR a un comercio falso.", "Pago QR a un comercio nuevo para el cliente; el mismo comercio recibe de muchas víctimas.", "31,6 %"],
    ["**Cuenta mula**\ncuenta_mula", "Cuentas recién abiertas reciben el dinero robado y lo sacan rápido en efectivo o hacia otra entidad.", "Cuenta con pocos días, entradas de muchas víctimas, retiros casi iguales al saldo.", "87,2 %"],
  ], [1750, 2900, 3176, 1200]),
  nota("Las operaciones de cuenta mula son la segunda salida del mismo dinero robado. Para estimar pérdidas de clientes, no sumes su monto al de las demás modalidades."),

  H1("5. Arquitectura"),
  P("El archivo **Yuma_Pay_Arquitectura.drawio** tiene cuatro páginas editables: arquitectura actual, arquitectura objetivo, flujo de autorización y proceso actual de alertas y reclamaciones. Ábrelo en app.diagrams.net o en draw.io de escritorio."),
  H2("Arquitectura actual"),
  P("El orquestador autoriza sin consultar el riesgo. El antifraude trabaja fuera de línea sobre la base transaccional."),
  imagen("1_arquitectura_actual.png", 600, 344),
  H2("Arquitectura objetivo"),
  P("El orquestador pide un puntaje a Escudo Yuma antes de autorizar. Los casos confirmados vuelven como etiquetas al lago de datos y mejoran las reglas y el modelo."),
  imagen("2_arquitectura_objetivo.png", 600, 348),
  nota("La arquitectura objetivo es una referencia. Los equipos pueden proponer otra si cumple las restricciones de la sección 9."),

  H1("6. Datos entregados"),
  P("Los archivos están en la carpeta 03_Datos, en formato CSV con codificación UTF-8 y separados por comas. Cubren del 1 de mayo al 31 de octubre de 2026. El archivo diccionario_de_datos.csv describe cada campo."),
  tabla(["Archivo", "Filas", "Contenido"], [
    ["transacciones.csv", "120.972", "Operaciones con monto, saldo, destino, dispositivo, señales de riesgo y la etiqueta es_fraude con su modalidad."],
    ["clientes.csv", "6.000", "Tipo de cliente, departamento, rango de edad, fecha de vinculación y marca de cuenta mula confirmada."],
    ["eventos_app.csv", "48.281", "Inicios de sesión exitosos y fallidos, registros de dispositivo, cambios de clave y cambios de SIM."],
    ["alertas.csv", "9.687", "Alertas del motor actual, reglas activadas, severidad y decisión del analista cuando hubo revisión."],
    ["reglas_vigentes.csv", "12", "Extracto de las reglas del motor actual con su condición exacta y severidad."],
    ["linea_base.py", "—", "Programa que aplica las 12 reglas y calcula los indicadores de la línea base."],
  ], [2300, 1000, 5726]),
  P("**La muestra está enriquecida.** Tiene 1.704 operaciones fraudulentas, el 1,41 % del total, para que el problema sea trabajable. En la operación real el fraude es cerca de una de cada 10.000 operaciones. Un modelo entrenado aquí debe evaluarse pensando en esa diferencia."),

  H1("7. Línea base que hay que superar"),
  P("Estos indicadores salen de ejecutar linea_base.py sobre la muestra. “Alertado” significa que una regla marcó la operación en el lote siguiente; no significa que el fraude se haya evitado."),
  tabla(["Indicador en la muestra", "Motor de reglas actual"], [
    ["Operaciones alertadas", "9.687 de 120.972"],
    ["Alertas que son falsos positivos", "89,0 %"],
    ["Operaciones de fraude alertadas", "62,6 %"],
    ["Monto de fraude alertado", "85,4 %"],
    ["Alertas revisadas por un analista", "33,7 %"],
    ["Tiempo mediano entre la alerta y la revisión", "169 minutos"],
    ["Momento de la decisión", "Hasta 15 minutos después de autorizar"],
  ], [5526, 3500]),

  H1("8. Qué se espera de cada equipo"),
  N("Un prototipo que reciba transacciones del sandbox y devuelva una decisión con puntaje y razones."),
  N("Un reporte de indicadores obtenido del sandbox: fraude detectado, falsos positivos y tiempo de respuesta."),
  N("Un diagrama de la arquitectura propuesta, que puede partir del archivo de draw.io."),
  N("Una explicación de cómo se justifica cada decisión ante el cliente y ante un auditor."),
  N("Una presentación de cinco minutos con una demostración en vivo."),

  H1("9. Restricciones"),
  B("**Tiempo de respuesta:** la decisión debe llegar en menos de 300 milisegundos y soportar picos de 150 transacciones por segundo."),
  B("**Sin información del futuro:** para decidir una operación solo se pueden usar datos anteriores a su fecha y hora."),
  B("**Explicabilidad:** cada decisión debe poder explicarse y auditarse. No puede discriminar por región, edad o nivel de ingresos."),
  B("**Experiencia del cliente:** la meta es bajar los falsos positivos del 92 % a menos del 60 % sin dejar pasar más fraude."),
  B("**Supervisión humana:** un bloqueo definitivo de cuenta siempre requiere la revisión de un analista."),
  B("**Datos:** se trabaja solo con los datos sintéticos entregados, bajo acuerdo de confidencialidad."),
  B("**Marco legal de referencia:** Ley 1581 de 2012, Ley 1266 de 2008 e instrucciones de la Superintendencia Financiera sobre seguridad y ciberseguridad."),

  H1("10. Criterios de evaluación propuestos"),
  tabla(["Criterio", "Qué se mira", "Peso"], [
    ["Efectividad", "Fraude detectado y falsos positivos frente a la línea base, medidos en el sandbox.", "30 %"],
    ["Viabilidad técnica", "Tiempo de respuesta, arquitectura y facilidad de integración por API.", "20 %"],
    ["Explicabilidad", "Razones claras por decisión, registro auditable y control de sesgos.", "15 %"],
    ["Experiencia del cliente", "Fricción para el usuario legítimo y claridad de los mensajes.", "15 %"],
    ["Seguridad y cumplimiento", "Manejo de datos, cifrado y respeto de las restricciones.", "10 %"],
    ["Presentación", "Demostración en vivo y claridad del relato.", "10 %"],
  ], [2300, 5526, 1200]),
  nota("Los pesos son una propuesta del retador. El comité organizador puede ajustarlos."),

  H1("11. Cómo empezar"),
  N("Lee README.md y revisa diccionario_de_datos.csv.", "num2"),
  N("Ejecuta **python 03_Datos/linea_base.py** para reproducir la línea base.", "num2"),
  N("Levanta el sandbox con **python 04_Sandbox_API/mock_api.py** y consulta openapi.yaml.", "num2"),
  N("Abre 06_Sitio_web/index.html para ver la experiencia del cliente y el panel del analista.", "num2"),

  H1("12. Glosario"),
  tabla(["Término", "Significado"], [
    ["Billetera digital", "Aplicación para guardar dinero y hacer pagos desde el celular."],
    ["Llave", "Dato fácil de recordar, como el celular, que identifica la cuenta de destino en una transferencia inmediata."],
    ["OTP", "Código de un solo uso que se envía para confirmar una operación."],
    ["Cuenta mula", "Cuenta usada para recibir y mover dinero de origen ilícito."],
    ["Falso positivo", "Operación legítima que el sistema marcó como sospechosa."],
    ["Desafío", "Verificación adicional que se pide al cliente cuando el riesgo es medio."],
    ["SARLAFT", "Sistema de administración del riesgo de lavado de activos y financiación del terrorismo."],
  ], [2300, 6726]),
];

const estiloTitulo = (size, before, after) => ({ run: { font: F, size, bold: true, color: AZUL }, paragraph: { spacing: { before, after }, keepNext: true } });
const doc = new Document({
  creator: "John Mazo", title: "Caso de estudio: Escudo Yuma",
  styles: { default: { document: { run: { font: F, size: 21 } }, heading1: estiloTitulo(30, 360, 120), heading2: estiloTitulo(24, 220, 80) } },
  numbering: { config: [
    { reference: "vin", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 240 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] },
    { reference: "num2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "Yuma Pay (organización ficticia) · Caso de estudio para hackatón · página ", font: F, size: 16, color: "7F7F7F" }),
      new TextRun({ children: [PageNumber.CURRENT], font: F, size: 16, color: "7F7F7F" })] })] }) },
    children: hijos,
  }],
});
const salida = process.argv[2] || path.join(RAIZ, "Caso_de_estudio_Yuma_Pay.docx");
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(salida, b); console.log("ok", salida); });
