# Escudo Yuma: detectar el fraude antes de que el dinero salga

*Pitch de 5 diapositivas para Yuma Pay. Todas las cifras de la demo salen de pruebas reales hechas con datos
sintéticos de demostración; no hay datos de clientes reales.*

---

## Diapositiva 1: El problema

**El fraude se detecta tarde, y a veces se castiga a inocentes.**

- Dos fraudes que crecen en las billeteras digitales de Colombia:
  - **SIM Swapping:** un delincuente consigue la línea telefónica de la víctima, entra a su cuenta y la vacía.
  - **Cuentas mula:** cuentas prestadas o robadas que reciben el dinero del fraude y lo pasan a otra parte.
- Hoy Yuma Pay revisa **después** de que el dinero sale (en lotes de 15 minutos y con reglas fijas).
- Resultado, según los datos del caso de estudio del reto: **92,1 % de las alertas de octubre eran falsas**.
  Es decir, casi todas las alertas molestaban a un cliente honesto.

> **Mensaje para el jurado:** el fraude actual se descubre tarde, y la mayoría de las alertas son falsas.

*Fuente de las cifras: caso de estudio del reto (datos sintéticos).*

---

## Diapositiva 2: La solución

**Escudo Yuma: una calificación de riesgo de 0 a 1000 para cada operación, explicada en español.**

- Cada operación recibe tres puntajes, uno por tipo de fraude: **SIM Swapping, cuenta mula y phishing (engaño por QR)**.
- Cada puntaje viene con **razones en lenguaje claro**, por ejemplo: "Cambio de SIM en las últimas 48 horas" o
  "El monto es el 90 % del saldo". Un analista entiende por qué se levantó la alerta.
- Si el puntaje llega al umbral, el sistema **abre un caso** para que lo revise una persona en **JUBE**.
- Si la operación es normal, **no hace nada**: el cliente honesto no se entera.

| Puntaje | Nivel |
|---|---|
| 0 a 299 | Bajo (no abre caso) |
| 300 a 599 | Medio |
| 600 a 799 | Alto |
| 800 a 1000 | Crítico |

> **Mensaje para el jurado:** una nota de riesgo que se puede explicar, no una "caja negra".

---

## Diapositiva 3: Cómo está construido

**Dos piezas que ya funcionan juntas.**

1. **JUBE** (software libre de monitoreo de transacciones). Incluye su base de datos (Postgres), su memoria
   rápida (Redis) y su API. Es donde viven las reglas y donde los analistas ven y trabajan los casos.
2. **Nuestro conector en Python** (puerto 8000). Recibe la operación, calcula los tres puntajes con sus razones y
   **envía el resultado a JUBE**.

```
Operación  ->  Conector Escudo Yuma  ->  JUBE  ->  Caso para el analista
 (cliente)     (puntaje 0-1000 y         (4 reglas)   (solo si hay riesgo)
                razones en español)
```

- En las pruebas, el conector calculó cada puntaje en **menos de 1 milisegundo** (medido en el equipo de
  prueba, sin contar el tiempo de JUBE).
- JUBE exige que cada regla sea **aprobada** antes de entrar en funcionamiento: queda registro de quién la
  creó y quién la aprobó.

> **Mensaje para el jurado:** usamos una herramienta abierta y probada, y le sumamos nuestra inteligencia
> antifraude.

---

## Diapositiva 4: Demo real (probada hoy)

**4 operaciones de prueba, de punta a punta: del conector a JUBE.**

| Caso | Puntaje del conector | Resultado en JUBE |
|---|---|---|
| SIM Swapping | **1000** | Abre el **caso n.º 1** |
| Cuenta mula | **900** | Abre el **caso n.º 2** |
| Phishing por QR | **550** | Abre el **caso n.º 3** |
| Operación normal | **0** | **No abre caso** |

**Resultado: 3 fraudes detectados y 0 falsos positivos.**

- Verificamos que la operación normal no abrió caso de tres maneras: la respuesta de JUBE, su base de datos y
  su pantalla de casos (solo muestra los 3 casos de fraude).
- El caso de SIM Swapping activó dos reglas a la vez (SIM Swapping y phishing) y JUBE las reunió en **un solo
  caso**, en lugar de molestar al analista dos veces.

> **Mensaje para el jurado:** en la prueba, los fraudes se detectaron y el cliente honesto pasó sin fricción.

*Nota de honestidad: son 4 operaciones de demostración con datos sintéticos. Sirven para probar que el flujo
funciona de principio a fin; no son una medición estadística de precisión.*

---

## Diapositiva 5: Qué sigue

**Del prototipo a un sistema más fino y más seguro.**

1. **Subir el umbral a 600.** Hoy un puntaje "medio" (por ejemplo, el de 550) ya abre caso. Con 600, solo los
   niveles **alto y crítico** abrirían caso o retendrían la operación, con menos trabajo para los analistas.
   *El bloqueo definitivo de una cuenta seguirá decidiéndolo siempre una persona, como exige el reto.*
2. **Probar la regla `VELOCIDAD_YUMA`** (varias salidas de dinero en una hora). Ya está creada y aprobada,
   pero todavía no se ha probado con una operación.
3. **Usar `AccountId` + fecha como clave del caso.** Hoy hay un caso por cuenta; con la fecha, un mismo cliente
   podría tener casos distintos en días distintos, sin mezclar episodios.

> **Mensaje para el jurado:** la base funciona; los próximos pasos la hacen más precisa y más segura.
