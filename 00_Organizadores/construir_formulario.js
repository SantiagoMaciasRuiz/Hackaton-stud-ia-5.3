const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, AlignmentType, VerticalAlign,
} = require("docx");

const FONT = "Arial";
const W_LABEL = 2900;
const W_ANSWER = 6126;
const W_TABLE = W_LABEL + W_ANSWER;

// Uso: node construir_formulario.js [salida.docx]
// Each answer is a list of blocks: "texto" (párrafo), {b:[...]} (viñetas), {h:"..."} (subtítulo en negrilla)
const rows = [
  ["Nombre de la organización", ["Yuma Pay S.A. (organización ficticia creada para la hackatón)"]],
  ["Sector económico o industria", ["Servicios financieros – Fintech (billetera digital y pagos electrónicos)"]],
  ["Breve descripción de la organización", [
    "Yuma Pay es una billetera digital colombiana, 100 % móvil, que opera como sociedad especializada en depósitos y pagos electrónicos (SEDPE) vigilada por la Superintendencia Financiera.",
    "Desde 2019 ofrece depósitos de bajo monto, transferencias inmediatas con llaves, pagos con QR, recargas, pago de servicios, tarjeta débito virtual y retiros en corresponsales.",
    "Atiende a 4,2 millones de usuarios, en su mayoría jóvenes, trabajadores independientes y microcomerciantes, y procesa cerca de 1,8 millones de transacciones al día con un equipo de 380 personas.",
  ]],
  ["Página web", ["www.yumapay.online"]],
  ["Nombre completo de la persona que diligencia el reto", ["John Mazo"]],
  ["Cargo o rol que desempeña en la organización", ["CISO (Chief Information Security Officer) – Director de Seguridad de la Información y Prevención de Fraude"]],
  ["Correo electrónico de contacto", ["Jmazo@yumapay.online"]],
  ["Número de teléfono o celular de contacto", ["[Tu número de celular]"]],
  ["Nombre tentativo del reto empresarial", ["Escudo Yuma: sistema antifraude en tiempo real para una billetera digital"]],
  ["¿Qué problema o necesidad concreta enfrenta tu organización?", [
    "Yuma Pay detecta el fraude después de que el dinero ya salió de la cuenta. El motor actual usa unas 140 reglas estáticas y revisa parte de las operaciones por lotes cada 15 minutos. Una transferencia inmediata, en cambio, se completa en segundos y no se puede reversar.",
    "Las modalidades que más golpean a los usuarios son:",
    { b: [
      "Toma de cuenta por phishing, smishing o llamadas de falsos asesores.",
      "Duplicación de SIM (SIM swapping) para interceptar los códigos OTP.",
      "Suplantación de identidad al abrir cuentas, que luego se usan como cuentas mula.",
      "Engaños con códigos QR y comprobantes de pago falsos a comerciantes.",
    ]},
    "Hoy el motor genera cerca de 4.000 alertas diarias y el 92 % son falsos positivos. Los 12 analistas alcanzan a revisar solo un tercio. Cada mes se confirman unos 2.300 casos de fraude, con pérdidas promedio de COP 1.150 millones.",
    "La necesidad concreta es un sistema que califique el riesgo de cada operación antes de autorizarla, en menos de 300 milisegundos. Debe combinar reglas, modelos de aprendizaje automático y análisis de comportamiento, dispositivo y redes de cuentas. También debe explicar cada decisión y reducir los falsos positivos.",
  ]],
  ["¿Por qué es importante resolver este problema para tu organización?", [
    "La confianza es el principal activo de una billetera digital, y cada fraude la erosiona.",
    { b: [
      "**Impacto en el usuario:** la pérdida promedio por caso es de COP 500.000, una suma alta para una población de ingresos bajos y medios.",
      "**Impacto financiero:** las pérdidas por fraude y las devoluciones suman cerca de COP 13.800 millones al año.",
      "**Riesgo regulatorio y reputacional:** las quejas por fraude ante la Superintendencia Financiera pueden derivar en requerimientos y sanciones, y dañan la marca en redes sociales.",
      "**Costo operativo:** los falsos positivos bloquean a clientes legítimos, saturan el servicio al cliente y consumen el tiempo de los analistas.",
      "**Crecimiento:** sin un control en tiempo real, la empresa no puede ampliar topes ni lanzar productos como crédito digital o nuevas funciones de pagos inmediatos.",
    ]},
  ]],
  ["¿Quiénes están involucrados o se ven afectados por este problema?", [
    { b: [
      "**Usuarios:** personas naturales y microcomerciantes, que son las víctimas directas.",
      "**Prevención de Fraude y Ciberseguridad (SOC):** equipos a cargo del CISO que monitorean, investigan y bloquean.",
      "**Servicio al Cliente:** recibe unas 6.500 reclamaciones mensuales relacionadas con fraude.",
      "**Cumplimiento (SARLAFT) y Jurídica:** gestionan reportes, cuentas mula y respuestas a autoridades.",
      "**Producto y Tecnología:** dueños de la app, del núcleo transaccional y de las integraciones.",
      "**Finanzas y Riesgos:** asumen las pérdidas y las provisiones.",
      "**Externos:** otras entidades financieras receptoras del dinero, corresponsales, operadores de telefonía, la Superintendencia Financiera, la Policía y la Fiscalía.",
    ]},
  ]],
  ["¿Dónde se presenta el problema dentro de la organización?", [
    "El problema se concentra en los canales digitales y en la célula de Prevención de Fraude de la Gerencia de Seguridad de la Información.",
    { b: [
      "**App móvil:** inicio de sesión, registro de un dispositivo nuevo, cambio de clave y de número celular.",
      "**Vinculación digital:** apertura de cuentas con documentos o rostros suplantados.",
      "**Transferencias inmediatas salientes y pagos con QR:** el punto donde el dinero sale de la entidad.",
      "**Retiros en corresponsales y cajeros:** el paso final para convertir el fraude en efectivo.",
      "**Centro de monitoreo:** la cola de alertas que los analistas no alcanzan a evacuar.",
    ]},
  ]],
  ["¿Cuándo y con qué frecuencia se presenta el problema?", [
    "El fraude ocurre todos los días, las 24 horas, con unos 75 casos confirmados diarios en promedio.",
    "Los picos se presentan en quincenas, fin de mes, pago de primas (junio y diciembre) y temporadas comerciales como Black Friday y Navidad. También aumentan en noches y fines de semana, cuando hay menos analistas en turno. Las campañas de phishing llegan en oleadas y pueden triplicar los casos en pocas horas.",
  ]],
  ["¿Cómo gestiona actualmente tu organización esta situación?", [
    "La gestión actual es reactiva y depende de revisión manual.",
    { b: [
      "Motor de reglas estáticas (topes, horarios, listas restrictivas) que el equipo ajusta a mano tras cada incidente.",
      "Código OTP por SMS y biometría facial solo en la vinculación.",
      "Analistas que revisan alertas en hojas de cálculo y en la consola del motor, y llaman al cliente para confirmar.",
      "Bloqueo preventivo de cuentas, que a menudo afecta a usuarios legítimos.",
      "Atención de reclamaciones con tiempos de respuesta de hasta 15 días hábiles.",
      "Campañas de educación al usuario en la app y en redes sociales.",
    ]},
    "Las principales limitaciones son tres. No hay calificación de riesgo antes de autorizar la operación. No se analiza el comportamiento del usuario ni del dispositivo. Y la retroalimentación de los casos confirmados no vuelve de forma automática a las reglas.",
  ]],
  ["¿Qué información, datos o materiales podría aportar tu organización para desarrollar el reto?", [
    "Yuma Pay entregaría datos sintéticos y anonimizados, sin información real de clientes.",
    { b: [
      "Conjunto de datos de seis meses de transacciones (monto, canal, hora, tipo de operación, cuenta origen y destino cifradas) con la etiqueta de fraude confirmado.",
      "Eventos de sesión y dispositivo: inicios de sesión, cambios de dispositivo, de clave y de número celular.",
      "Histórico de alertas del motor actual con la decisión final del analista.",
      "Catálogo resumido de las reglas vigentes y sus umbrales.",
      "Fichas de las modalidades de fraude más frecuentes, con casos de ejemplo.",
      "Diccionario de datos e indicadores base: tasa de fraude, falsos positivos y tiempo de detección.",
      "Acompañamiento de mentores de Prevención de Fraude, Ciberseguridad y Analítica.",
    ]},
  ]],
  ["¿Con qué documentos, herramientas o recursos adicionales se podría apoyar el desarrollo del reto?", [
    { b: [
      "Diagrama de arquitectura de alto nivel y flujo de autorización de una transacción.",
      "Flujo del proceso actual de gestión de alertas y reclamaciones.",
      "Entorno de pruebas (sandbox) con una API simulada de transacciones y de eventos.",
      "Conjuntos de datos públicos como PaySim (simulación de dinero móvil) e IEEE-CIS Fraud Detection, disponibles en Kaggle.",
      "Marcos de referencia: NIST Cybersecurity Framework, ISO/IEC 27001, OWASP MASVS y PCI DSS.",
      "Herramientas de código abierto: Python, scikit-learn, XGBoost, Apache Kafka, y Grafana para tableros.",
    ]},
  ]],
  ["¿Qué tipo de información se utilizaría para desarrollar el reto?", [
    { b: [
      "**Datos estructurados:** transacciones, eventos de la app y alertas, todos sintéticos o anonimizados.",
      "**Datos no estructurados:** textos de reclamaciones anonimizados y descripciones de modalidades de fraude.",
      "**Documentación técnica y de procesos:** arquitectura, flujos, reglas y políticas.",
      "**Información pública:** normativa, informes del sector y conjuntos de datos abiertos.",
    ]},
    "No se usarían datos personales reales, credenciales ni información sujeta a reserva bancaria.",
  ]],
  ["¿Existen restricciones de confidencialidad, tecnológicas, legales u operativas que debamos considerar?", [
    "Sí, en los cuatro frentes.",
    { h: "Confidencialidad" },
    { b: [
      "Los participantes firman un acuerdo de confidencialidad antes de recibir los datos.",
      "Solo se entregan datos sintéticos o anonimizados, y no pueden salir del entorno de la hackatón.",
      "Las reglas, los umbrales y las modalidades de fraude no se pueden publicar, porque servirían a los delincuentes.",
    ]},
    { h: "Tecnológicas" },
    { b: [
      "La calificación de riesgo debe responder en menos de 300 milisegundos y soportar picos de 150 transacciones por segundo.",
      "La solución se integra por API REST o por eventos, sin acceso a los sistemas de producción.",
      "Debe poder desplegarse en nube y en contenedores, con cifrado de datos en tránsito y en reposo.",
      "Se prefieren componentes de código abierto o con licencias que permitan uso comercial.",
    ]},
    { h: "Legales y regulatorias" },
    { b: [
      "Protección de datos personales (Ley 1581 de 2012) y hábeas data financiero (Ley 1266 de 2008).",
      "Instrucciones de la Superintendencia Financiera sobre seguridad en canales, ciberseguridad y riesgo operacional, además de SARLAFT.",
      "Reserva bancaria y estándar PCI DSS para los datos de tarjeta.",
      "Las decisiones automáticas deben ser explicables y auditables, y no pueden discriminar por región, edad o nivel de ingresos.",
    ]},
    { h: "Operativas" },
    { b: [
      "El sistema debe operar 24/7 y no puede aumentar la fricción para el usuario legítimo.",
      "La meta es bajar los falsos positivos del 92 % a menos del 60 % sin dejar pasar más fraude.",
      "Un bloqueo definitivo de cuenta siempre requiere la revisión de un analista.",
      "El prototipo debe ser viable en el tiempo de la hackatón y los mentores tienen disponibilidad limitada.",
    ]},
  ]],
];

function runs(text) {
  // soporta **negrilla** al inicio o dentro del texto
  return text.replace(/(\d) %/g, "$1\u00a0%").split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((part) =>
    part.startsWith("**")
      ? new TextRun({ text: part.slice(2, -2), bold: true, font: FONT, size: 20 })
      : new TextRun({ text: part, font: FONT, size: 20 })
  );
}

function answerBlocks(blocks) {
  const out = [];
  for (const blk of blocks) {
    if (typeof blk === "string") {
      out.push(new Paragraph({ children: runs(blk), spacing: { before: 40, after: 80 } }));
    } else if (blk.h) {
      out.push(new Paragraph({
        children: [new TextRun({ text: blk.h, bold: true, font: FONT, size: 20 })],
        spacing: { before: 120, after: 40 }, keepNext: true,
      }));
    } else if (blk.b) {
      for (const item of blk.b) {
        out.push(new Paragraph({
          children: runs(item),
          numbering: { reference: "bullets", level: 0 },
          spacing: { before: 20, after: 40 },
        }));
      }
    }
  }
  return out;
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "B8BEC7" };
const borders = { top: border, bottom: border, left: border, right: border };
const margins = { top: 100, bottom: 100, left: 140, right: 140 };

function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders, margins,
    shading: { type: ShadingType.CLEAR, fill: "1F3A5F", color: "auto" },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", font: FONT, size: 20 })] })],
  });
}

const tableRows = [
  new TableRow({ tableHeader: true, children: [headerCell("Campo", W_LABEL), headerCell("Respuesta", W_ANSWER)] }),
  ...rows.map(([label, blocks]) =>
    new TableRow({
      children: [
        new TableCell({
          width: { size: W_LABEL, type: WidthType.DXA },
          borders, margins, verticalAlign: VerticalAlign.TOP,
          shading: { type: ShadingType.CLEAR, fill: "EEF2F7", color: "auto" },
          children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, font: FONT, size: 20 })], spacing: { before: 40, after: 40 } })],
        }),
        new TableCell({
          width: { size: W_ANSWER, type: WidthType.DXA },
          borders, margins, verticalAlign: VerticalAlign.TOP,
          children: answerBlocks(blocks),
        }),
      ],
    })
  ),
];

const doc = new Document({
  creator: "Yuma Pay (ficticia)",
  title: "Formulario de reto empresarial – Yuma Pay",
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 300, hanging: 200 } } },
      }],
    }],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1200, bottom: 1200, left: 1440, right: 1440 } } },
    children: [
      new Paragraph({
        children: [new TextRun({ text: "Formulario de reto empresarial", bold: true, font: FONT, size: 36, color: "1F3A5F" })],
        spacing: { before: 0, after: 60 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Yuma Pay S.A. – Reto: sistema antifraude en tiempo real", font: FONT, size: 24, color: "44546A" })],
        spacing: { before: 0, after: 120 },
      }),
      new Paragraph({
        children: [new TextRun({
          text: "Yuma Pay es una organización ficticia creada para la hackatón. Su nombre, sus cifras y sus datos son inventados y solo sirven para dar contexto al reto.",
          italics: true, font: FONT, size: 18, color: "595959",
        })],
        spacing: { before: 0, after: 240 },
      }),
      new Table({
        width: { size: W_TABLE, type: WidthType.DXA },
        columnWidths: [W_LABEL, W_ANSWER],
        rows: tableRows,
      }),
    ],
  }],
});

const out = process.argv[2] || "Reto_empresarial_Yuma_Pay.docx";
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("ok", out, rows.length, "campos"); });
