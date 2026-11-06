# Changelog del prompt de análisis de partidas

**Versión vigente: v3** (`prompt_analisis_partidas_v3.txt`).

| Versión | Fichero | Resumen |
|---|---|---|
| v1 | `prompt_analisis_partidas_V1.txt` | Prompt original, preparado antes de la primera prueba. |
| v2 | `prompt_analisis_partidas_v2.txt` | Siete correcciones surgidas de probarlo con tres partidas. |
| v3 | `prompt_analisis_partidas_v3.txt` | Añade una línea de indicadores por partida y sube el límite del debriefing a 450 palabras. |

Las versiones antiguas se conservan sin editar, salvo las correcciones menores que se anotan aquí.

---

## v3 (6 nov 2026)

**Añadido**
- **Línea INDICADORES en el debriefing** (apartado c): una sola línea de texto plano con tiempo usado total y porcentaje del tiempo base, mediana de segundos por jugada, blunders, errores e imprecisiones, ventaja máxima, ventaja tirada y derrota corta.
- **Sección DEFINICIÓN DE INDICADORES**, con las mismas definiciones que usa `metricas_pgn.py`, para que las cifras de la partida y las del script coincidan.
- **Sección REFERENCIAS PARA COMPARAR LOS INDICADORES:** usa la línea base y los objetivos del perfil si se adjunta; si no, solo las cifras de "Patrones recurrentes recientes"; nunca inventa una referencia.
- **Regla de honestidad:** los indicadores se calculan solo con código o se copian tal cual de la fila del script. Nunca se estiman ni se presentan como aproximados. Si no hay ninguna de las dos fuentes, se escribe una frase de omisión en lugar de cifras.
- **Punto (j) del checklist** para verificar la línea de indicadores.

**Cambiado**
- Límite del debriefing: de 400 a **450 palabras** sin contar las FEN. Motivo: los debriefings de la prueba ya usaban entre 355 y 384 palabras y la línea nueva añade unas 50.
- Los apartados del debriefing pasan a ser a) a e). La regla 8 (sin enumeraciones con paréntesis) y el aviso de no copiar las letras incluyen ahora la e).
- La comparativa de patrones debe apoyarse en las cifras de los indicadores cuando existan.

**Notas**
- Funciona sin perfil y sin script: en ese caso compara con los patrones del propio prompt, o no compara.
- **No se ha probado todavía** con una ejecución real. Conviene analizar una o dos partidas y comprobar que la línea de indicadores sale con el formato esperado y con cifras iguales a las del script.

---

## v2 (6 nov 2026)

Corrige problemas que aparecieron al probar la v1 con tres partidas (una sin evaluaciones y dos con ellas).

**Cambiado**
1. **Regla 8, sin paréntesis en los comentarios:** prohíbe enumeraciones como `1)` o `a)`, que rompen el balance de paréntesis del checklist. Pide usar "Primero:", "Segundo:"... y no copiar las letras de la plantilla.
2. **Cabeceras originales conservadas** (`[White]`, `[Black]`, `[Result]`...), con una línea en blanco antes del briefing. Nuevo punto (i) del checklist y apartado 0 de la estructura.
3. **Tiempo usado definido:** reloj anterior propio menos reloj actual propio más 10 s, en segundos totales. Los umbrales pasan a "menor de 5 s" y "mayor de 120 s" de tiempo usado, en lugar de "incluido incremento".
4. **Variaciones de máximo 3 semijugadas**, con un ejemplo, y comprobación en el punto (h) del checklist.
5. **Plan B para python-chess:** si no está disponible, actúa como si no hubiera código para validar la legalidad de jugadas, variaciones y FEN.
6. **Plantilla de FEN sin corchetes ni barras** para cuando no hay código, porque la anterior chocaba con la regla de caracteres seguros.
7. **Origen de datos sin corchetes ni signo de apertura:** el apartado pide indicar si el PGN trae evaluaciones reales de Stockfish o estimadas, sin escribir la etiqueta técnica.

**Nota:** los cambios 6 y 7 se aplicaron sobre el mismo fichero v2 poco después de crearlo, el mismo día.

---

## v1 (original)

Prompt preparado por el usuario antes de la primera prueba. Incluye:
- Salida exclusiva en bloques PGN, con reglas de sintaxis pensadas para Lichess Study.
- Datos del jugador y patrones recurrentes escritos dentro del prompt.
- Checklist de auto-verificación (a) a (h).
- Umbrales objetivos para momentos clave y gestión del tiempo, y Plan B sin evaluaciones.
- Briefing inicial y debriefing final con tabla de tiempos, comparativa de patrones y posiciones FEN.

**Problemas detectados al probarla** (corregidos en v2): enumeraciones con paréntesis que rompían el balance, cabeceras no mencionadas, umbral de tiempo ambiguo, sin plan B para python-chess y una plantilla de FEN con corchetes y barras.

---

## Pendiente y limitaciones conocidas

- **El apartado de veredicto honesto** sigue escrito como una pregunta que empieza por el signo de apertura, que el modelo podría copiar y romper la regla de caracteres seguros. Se arregla reescribiéndolo sin signos de interrogación.
- **Los patrones recurrentes están escritos dentro del prompt** y se quedan obsoletos. La alternativa es apoyarse solo en `perfil_peondeloto.md`.
- **El PGN enriquecido no conserva las evaluaciones** de la partida original, porque el prompt solo permite la etiqueta del reloj en los comentarios. El script de métricas debe ejecutarse siempre sobre los PGN originales.
- **Las explicaciones tácticas pueden fallar**, sobre todo sin evaluaciones de Stockfish. Contrasta lo importante en Lichess.

---

## Cómo registrar una versión nueva

1. Copia la versión vigente a un fichero nuevo (`prompt_analisis_partidas_v4.txt`) y haz ahí los cambios.
2. Añade arriba una sección con la fecha y las listas **Añadido**, **Cambiado** y **Corregido**, con el motivo de cada cambio.
3. Anota qué se ha probado y qué no.
4. Actualiza la tabla del principio y la versión vigente.
