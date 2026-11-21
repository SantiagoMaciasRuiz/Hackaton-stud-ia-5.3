# Resultados de la demo: conector Escudo Yuma -> Jube

Prueba local de extremo a extremo: el conector (`app.py`, `POST /evaluar`) califica cada operación con un
puntaje de 0 a 1000 por modalidad y `conectar_jube.py` envía el resultado a Jube, donde cuatro reglas
(`SIM_SWAPPING_YUMA`, `MULA_YUMA`, `PHISHING_QR_YUMA`, `VELOCIDAD_YUMA`) deciden si se abre un caso.

> Todos los datos son **sintéticos y de demostración** (cuentas `C-DEMO-*`). No hay datos reales,
> credenciales ni direcciones IP en este repositorio.

## Tabla final de 4 casos

| Caso | Evento / cuenta | Scores del conector (sim / mula / phishing) | Regla de Jube que disparó | ¿Debe crear caso? | ¿Creó caso en Jube? | ¿Pasó? |
|---|---|---|---|---|---|---|
| SIM Swapping | `T-SIM-0001` / `C-DEMO-SIM` | **1000** / 100 / 600 | `SIM_SWAPPING_YUMA` y `PHISHING_QR_YUMA` | Sí | Sí, caso nº 1 | Sí |
| Mula | `T-MULA-0001` / `C-DEMO-MULA` | 0 / **900** / 150 | `MULA_YUMA` | Sí | Sí, caso nº 2 | Sí |
| Phishing (QR) | `T-QR-0001` / `C-DEMO-QR` | 0 / 0 / **550** | `PHISHING_QR_YUMA` | Sí | Sí, caso nº 3 | Sí |
| Normal | `T-OK-0001` / `C-DEMO-OK` | **0 / 0 / 0** | Ninguna | **No** | **No** | Sí |

Resultado: 3 de 3 operaciones de riesgo abrieron caso y la operación normal **no** abrió ninguno.

## Cómo se verificó que el caso normal no abrió caso

- La respuesta de la API de Jube no incluye el bloque `CreateCase`.
- El evento sí llegó a Jube (HTTP 200) y quedó archivado con scores 0 y ninguna regla `*_YUMA` activada.
- En la base de datos de Jube hay 0 casos para `C-DEMO-OK`; el total de casos es 3.
- La cola de casos abiertos de la interfaz muestra exactamente 3 filas (1 `C-DEMO-SIM`, 2 `C-DEMO-MULA`,
  3 `C-DEMO-QR`).

## Capturas

| Archivo | Qué muestra |
|---|---|
| `capturas/01_reglas_creadas_en_jube.jpg` | Las 4 reglas `*_YUMA` en el modelo de Jube |
| `capturas/02_caso_1_creado_en_jube.jpg` | Caso 1 (`C-DEMO-SIM`), estado Open |
| `capturas/03_caso_1_activaciones.jpg` | Panel de activaciones del caso 1 |
| `capturas/04_caso_2_mula_creado_en_jube.jpg` | Caso 2 (`C-DEMO-MULA`), estado Open |
| `capturas/05_caso_3_phishing_creado_en_jube.jpg` | Caso 3 (`C-DEMO-QR`), estado Open |
| `capturas/evidencia_sim_swapping.json` | Reglas activadas, scores y datos del caso 1 leídos de la base de datos |

## Cómo reproducirlo

```powershell
# 1) Conector
python -m uvicorn app:app --port 8000

# 2) La API Key de Jube se pasa solo por variable de entorno (nunca en archivos)
$env:JUBE_API_KEY = "<tu clave>"

# 3) Un caso a la vez
python conectar_jube.py --caso sim_swapping
python conectar_jube.py --caso mula
python conectar_jube.py --caso phishing
python conectar_jube.py --caso normal
```

## Configuración usada

- Modelo de Jube: "Detailed Account Financial Transactions", con 4 campos de entrada nuevos
  (`ScoreSimSwapping`, `ScoreCuentaMula`, `ScorePhishing`, `NSalidas60min`).
- Las 3 reglas de puntaje disparan con `score >= 300`; `VELOCIDAD_YUMA` con `NSalidas60min >= 3`.
- Los casos se agrupan por `AccountId`: dos reglas sobre la misma cuenta producen **un solo caso**
  con varias activaciones (como en el caso 1).
- Jube exige maker-checker: cada campo y regla se aprobó antes de entrar al motor.

## Limitaciones conocidas

- Los puntajes y umbrales son una primera propuesta basada en reglas, sin calibrar con datos reales.
- Con el umbral en 300, un puntaje "medio" (p. ej. 550 en el caso de phishing) ya abre caso. Para que solo
  los niveles "alto" (600) y "crítico" (800) abran caso habría que subir el umbral de las reglas.
- `VELOCIDAD_YUMA` está creada y aprobada, pero **no se probó con un evento**: en las cuatro pruebas
  `NSalidas60min` fue 0.
- Solo se ejecutó un evento por caso; no se midió rendimiento ni carga.
