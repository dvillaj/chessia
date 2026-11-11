# Changelog del prompt de análisis de partidas

**Versión vigente: v6** (`prompt_analisis_partidas_v6.txt`).

| Versión | Fichero | Resumen |
|---|---|---|
| v0 | `prompt_analisis_partidas_v0.txt` | Prompt original, el primero que se pasó al modelo. |
| v1 | `prompt_analisis_partidas_v1.txt` | Siete correcciones surgidas de probarlo con tres partidas. |
| v2 | `prompt_analisis_partidas_v2.txt` | Añade una línea de indicadores por partida y sube el límite del debriefing a 450 palabras. |
| v3 | `prompt_analisis_partidas_v3.txt` | Porcentaje de reloj sobre el tiempo disponible, coma decimal uniforme y menos redundancia. |
| v4 | `prompt_analisis_partidas_v4.txt` | Entrega de cada partida como fichero y reglas de completitud para que no falte ninguna jugada. |
| v5 | `prompt_analisis_partidas_v5.txt` | Pasa a una sola cuenta, dvillaj131313, en 10+0; el incremento se lee de la cabecera en lugar de fijarlo en 10 s. |
| v6 | `prompt_analisis_partidas_v6.txt` | Sin datos del jugador: usuario, ritmo, Elo, objetivo y patrones salen del perfil adjunto en cada chat. |
| crear perfil v0 | `prompt_crear_perfil_v0.txt` | Prompt aparte (numeración propia) que completa el perfil de un usuario nuevo a partir de las métricas. |

**Sobre la numeración:** los prompts se numeran sin huecos, de v0 a v6. Antes de la renumeración se usaron otros nombres: el original se llamó v1 en un changelog antiguo y las versiones posteriores v2, v3 y v4. Si encuentras esas referencias en conversaciones o notas antiguas, usa esta equivalencia:

| Nombre anterior | Nombre actual |
|---|---|
| original (llamado v1) | v0 |
| v2 | v1 |
| v3 | v2 |
| v4 | v3 |

Las versiones antiguas se conservan sin editar, salvo las correcciones menores que se anotan aquí.

---

## v6 (11 nov 2026)

La aplicación pasa a admitir varios usuarios, cada uno con su perfil en `perfiles/<usuario>.md`. Los datos del jugador dejan de estar escritos en el prompt, donde se quedaban obsoletos (rating, patrones).

**Cambiado**
- **Datos del jugador:** se sustituyen por la regla de que todo sale del perfil adjunto (cabecera con usuario, ritmo, Elo y objetivo, más áreas de mejora A y fuertes S). Sin perfil, el prompt pregunta cuál de los dos bandos es el usuario y omite la comparativa de patrones y las referencias de indicadores.
- **Tiempo disponible:** el ejemplo es genérico (10+0 y 15+10).
- Las menciones al usuario pasan a "el jugador".

**Sin cambios:** modo fichero, completitud, formato PGN y umbrales. **No probado** en un chat nuevo.

**Prompt nuevo, `prompt_crear_perfil_v0.txt`:** crea el perfil de un usuario desde la plantilla con la tabla del script y el CSV. Solo usa cifras de los adjuntos y marca como pendiente lo que falte. Tras una primera pasada hecha por quien conocía el proyecto, se corrigieron dos contradicciones: los fuertes mínimos frente a pocos datos, y preguntar las horas semanales antes de escribir.

**Probado una vez en un chat nuevo (11 nov 2026), con 24 partidas y 15+10:** preguntó las horas semanales antes de escribir, no tocó la cabecera, no propuso cambios de repertorio, marcó como pendiente lo que no podía medir y sus cifras coincidieron con las del CSV (se comprobaron las principales). Matiz: la ventaja grande de S1 usa un corte ajustado a los datos y es solo un indicio. Es una sola prueba, con una sola cuenta y pocas partidas; falta probarlo con datos distintos, por ejemplo sin partidas analizadas.

---

## v5 (11 nov 2026)

El proyecto pasa a basarse solo en la cuenta dvillaj131313 (ritmo 10+0), sin la otra cuenta que usaban las versiones anteriores.

**Cambiado**
- **Datos del jugador:** usuario dvillaj131313, rating aproximado 1526 y objetivo 1850 en 10+0. Se eliminan el repertorio y los patrones recurrentes de la cuenta anterior; los patrones remiten al perfil adjunto (`perfil_dvillaj131313.md`, códigos A1 a A7 y S1 a S4).
- **Tiempo usado:** suma el incremento de la cabecera `TimeControl` (0 s en 10+0) en lugar de 10 s fijos. El tiempo disponible del ejemplo pasa a 10+0.
- Todas las menciones al usuario pasan a dvillaj131313.

**Sin cambios:** modo fichero, completitud, formato PGN y umbrales. **No probado** en un chat nuevo.

---

## v4 (7 nov 2026)

Responde a dos peticiones del usuario: que el PGN se entregue como fichero en un directorio de salida, en lugar de como texto en el chat, y que no falte ninguna jugada. Según el usuario, en una salida anterior una de las partidas llegó incompleta.

**Añadido**
- **Modo fichero (preferente).** Si el entorno puede crear y entregar ficheros, cada partida va en su propio `.pgn`, en una carpeta de salida (`analisis`), con el nombre `AAAA-MM-DD_color_vs_rival_GameId.pgn`. El PGN no se pega en el chat; el mensaje se limita a una línea por partida con el nombre del fichero y la comprobación de completitud. Motivo: un PGN con 60 a 130 semijugadas y comentarios es largo, y copiarlo al chat deja margen a recortes y errores de transcripción. Un fichero generado por código y releído no se retranscribe.
- **Modo bloques (alternativa).** Si no puede crear ficheros, se mantiene el comportamiento anterior: solo bloques de código PGN, uno por partida, sin texto fuera.
- **Regla 10, COMPLETITUD:** el PGN lleva todas las jugadas, hasta la última, y el resultado final. Prohíbe abreviar, usar puntos suspensivos o recortar por longitud. Si no puede entregar una partida entera, debe decirlo.
- **Punto (k) del checklist:** comparar número de semijugadas, última jugada y resultado con el original, con código o contando. En modo fichero, releer el fichero entregado y comprobar sobre él, no sobre lo que tenía en memoria.

**Cambiado**
- "Cada bloque debe empezar por las cabeceras" pasa a "Cada PGN, ya sea fichero o bloque".
- La restricción de "solo bloques, sin texto fuera" queda limitada al modo bloques.

**Cambios fuera del prompt**
- Nuevo script `verificar_pgn.py`: comprueba, sin depender del modelo, que cada PGN enriquecido tiene las mismas jugadas, relojes, cabeceras y resultado que el original, y que cumple las reglas de sintaxis y los límites de palabras. Se probó con tres salidas correctas y cuatro estropeadas a propósito (jugadas finales recortadas, jugada alterada, enumeración con paréntesis y cabecera eliminada): detectó las cuatro. No comprueba la legalidad de las jugadas de las variaciones ni de las FEN.
- README y `CONTEXTO_IA.md` actualizados.

**Notas**
- **No se ha probado todavía** con una ejecución real en modo fichero. El modo fichero necesita un entorno que cree y entregue ficheros; si no lo hay, el prompt cae al modo bloques.
- En las pruebas anteriores, las salidas se generaron con scripts y se verificaron antes de enviarlas, pero lo que se pegó en el chat se transcribió a mano. No ha sido posible determinar cuál de las partidas llegó incompleta. Con `verificar_pgn.py` se puede comprobar cualquier PGN, también los antiguos.

---

## v3 (7 nov 2026)

Corrige tres problemas que aparecieron al probar la v2 con una partida sin evaluaciones.

**Corregido**
1. **Porcentaje de reloj sobre el tiempo disponible.** La v2 lo medía sobre el tiempo base, y con incremento eso engaña en partidas largas: en la partida de prueba daba 65 % para peondeloto y 167 % para el rival. Ahora el tiempo disponible es el tiempo base más el incremento de cada jugada propia salvo la primera (en 15+10: 900 más 10 por cada jugada menos la primera). En esa partida el mismo dato pasa a 38 %.
2. **Formato numérico uniforme.** Nueva regla 9: coma decimal en todas las cifras del texto (2,5; 9,8; 38 %), salvo en las evaluaciones del motor, que siguen el formato de Lichess con signo y punto (+1.8, -0.5). En la v2, la línea de indicadores usaba punto y el resto del debriefing, coma. El ejemplo de la línea de indicadores y el punto (j) del checklist se actualizan en consecuencia.
3. **Menos redundancia.** La tabla de gestión del tiempo ya no repite el tiempo usado total, el porcentaje ni la mediana, que figuran en los indicadores, y la comparativa de patrones cita solo la cifra clave de cada veredicto. En la prueba de la v2 la cifra de 587 s aparecía tres veces y el debriefing llegó a 445 de 450 palabras.

**Añadido**
- En REFERENCIAS PARA COMPARAR LOS INDICADORES: cada indicador se compara solo con una referencia definida de la misma forma. Por ejemplo, minutos usados con minutos usados, pero nunca un porcentaje del tiempo disponible con un porcentaje del tiempo base.

**Cambios fuera del prompt (para que todo coincida)**
- `metricas_pgn.py`: la columna `uso_reloj_pct` pasa a `uso_disponible_pct` (y la del rival, a `uso_disponible_rival_pct`), con la nueva definición. La tabla muestra "% tiempo disponible usado" y el objetivo del 40 % se aplica a esa medida.
- `perfil_peondeloto.md` pasa a la versión 2 del perfil, que tiene su propia numeración: línea base de peondeloto 14 % de tiempo disponible usado frente a 51 % del rival (antes, 19 % y 69 % sobre el tiempo base). En dvillaj no cambia: 19 % frente a 37 %, porque 10+0 no tiene incremento.
- Los prompts pasan al subdirectorio `prompts/`, junto con este changelog.
- Se renumeran los prompts sin huecos (de v0 a v3). Esta versión se llamaba v4 antes de la renumeración.
- Se añade `CONTEXTO_IA.md`.

**Notas**
- **No se ha probado todavía** con una ejecución real. Conviene analizar una partida con evaluaciones y comprobar que la línea de indicadores sale con coma decimal y porcentaje sobre el tiempo disponible, y que la tabla de tiempos ya no repite cifras.
- El objetivo del 40 % del tiempo disponible es una propuesta heredada del 40 % anterior. Con la nueva medida conviene revisarlo cuando haya más datos.

---

## v2 (6 nov 2026)

**Añadido**
- **Línea INDICADORES en el debriefing** (apartado c): una sola línea de texto plano con tiempo usado total y porcentaje del tiempo base, mediana de segundos por jugada, blunders, errores e imprecisiones, ventaja máxima, ventaja tirada y derrota corta.
- **Sección DEFINICIÓN DE INDICADORES**, con las mismas definiciones que usa `metricas_pgn.py`.
- **Sección REFERENCIAS PARA COMPARAR LOS INDICADORES:** usa la línea base y los objetivos del perfil si se adjunta; si no, solo las cifras de "Patrones recurrentes recientes"; nunca inventa una referencia.
- **Regla de honestidad:** los indicadores se calculan solo con código o se copian tal cual de la fila del script. Nunca se estiman ni se presentan como aproximados. Si no hay ninguna de las dos fuentes, se escribe una frase de omisión.
- **Punto (j) del checklist** para verificar la línea de indicadores.

**Cambiado**
- Límite del debriefing: de 400 a **450 palabras** sin contar las FEN. Motivo: los debriefings de la prueba ya usaban entre 355 y 384 palabras y la línea nueva añade unas 50.
- Los apartados del debriefing pasan a ser a) a e). La regla 8 y el aviso de no copiar las letras incluyen ahora la e).
- La comparativa de patrones debe apoyarse en las cifras de los indicadores cuando existan.

**Pruebas:** se probó con una partida sin evaluaciones. La línea salió con el formato esperado y con cifras iguales a las del script. Esa prueba destapó los tres problemas que corrige la v3. La parte con evaluaciones (blunders, ventaja máxima, ventaja tirada) no se pudo probar.

---

## v1 (6 nov 2026)

Corrige problemas que aparecieron al probar el prompt original (v0) con tres partidas: una sin evaluaciones y dos con ellas.

**Cambiado**
1. **Regla 8, sin paréntesis en los comentarios:** prohíbe enumeraciones como `1)` o `a)`, que rompen el balance de paréntesis del checklist. Pide usar "Primero:", "Segundo:"... y no copiar las letras de la plantilla.
2. **Cabeceras originales conservadas** (`[White]`, `[Black]`, `[Result]`...), con una línea en blanco antes del briefing. Nuevo punto (i) del checklist y apartado 0 de la estructura.
3. **Tiempo usado definido:** reloj anterior propio menos reloj actual propio más 10 s, en segundos totales. Los umbrales pasan a "menor de 5 s" y "mayor de 120 s" de tiempo usado, en lugar de "incluido incremento".
4. **Variaciones de máximo 3 semijugadas**, con un ejemplo, y comprobación en el punto (h) del checklist.
5. **Plan B para python-chess:** si no está disponible, actúa como si no hubiera código para validar la legalidad de jugadas, variaciones y FEN.
6. **Plantilla de FEN sin corchetes ni barras** para cuando no hay código, porque la anterior chocaba con la regla de caracteres seguros.
7. **Origen de datos sin corchetes ni signo de apertura:** el apartado pide indicar si el PGN trae evaluaciones reales de Stockfish o estimadas, sin escribir la etiqueta técnica.

**Nota:** los cambios 6 y 7 se aplicaron sobre el mismo fichero v1 poco después de crearlo, el mismo día.

---

## v0 (original)

Prompt preparado por el usuario antes de la primera prueba. En disco se llamaba `prompt_analisis_partidas.txt`; se ha renombrado a `prompt_analisis_partidas_v0.txt` y movido a `prompts/`, **sin modificar su contenido**. Incluye:
- Salida exclusiva en bloques PGN, con reglas de sintaxis pensadas para Lichess Study.
- Datos del jugador y patrones recurrentes escritos dentro del prompt.
- Checklist de auto-verificación (a) a (h).
- Umbrales objetivos para momentos clave y gestión del tiempo, y Plan B sin evaluaciones.
- Briefing inicial y debriefing final con tabla de tiempos, comparativa de patrones y posiciones FEN.

**Problemas detectados al probarla** (corregidos en la v1): enumeraciones con paréntesis que rompían el balance, cabeceras no mencionadas, umbral de tiempo ambiguo, sin plan B para python-chess y una plantilla de FEN con corchetes y barras.

---

## Pendiente y limitaciones conocidas

- **El apartado de veredicto honesto** sigue escrito como una pregunta que empieza por el signo de apertura, que el modelo podría copiar y romper la regla de caracteres seguros. Se arregla reescribiéndolo sin signos de interrogación.
- **Los patrones recurrentes están escritos dentro del prompt** y se quedan obsoletos. La alternativa es apoyarse solo en `perfil_dvillaj131313.md`.
- **El PGN enriquecido no conserva las evaluaciones** de la partida original, porque el prompt solo permite la etiqueta del reloj en los comentarios. El script de métricas debe ejecutarse siempre sobre los PGN originales.
- **Las explicaciones tácticas pueden fallar**, sobre todo sin evaluaciones de Stockfish. Contrasta lo importante en Lichess.
- **El modo fichero depende del entorno.** Solo funciona si el chat puede crear y entregar ficheros; en caso contrario el prompt usa el modo bloques, donde sigue existiendo el riesgo de salidas recortadas.
- **Ninguna versión se ha probado en un chat nuevo.** Las pruebas se hicieron en una conversación donde el ejecutor ya conocía los problemas, así que miden que el prompt se puede seguir, no que un modelo lo cumpla a la primera.

---

## Cómo registrar una versión nueva

1. Copia la versión vigente a un fichero nuevo (`prompt_analisis_partidas_v5.txt`) en esta carpeta y haz ahí los cambios.
2. Añade arriba una sección con la fecha y las listas **Añadido**, **Cambiado** y **Corregido**, con el motivo de cada cambio.
3. Anota qué cambios hay fuera del prompt (script, perfil, README) y qué se ha probado y qué no.
4. Actualiza la tabla del principio y la versión vigente.
