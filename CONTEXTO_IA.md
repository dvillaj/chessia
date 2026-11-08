# Contexto del proyecto para un modelo de IA

Documento escrito para que un asistente de IA entienda este proyecto antes de ayudar. Léelo entero al empezar una sesión. Si algo de aquí contradice lo que dice el usuario en el chat, manda el usuario, pero avísale de la diferencia.

Última actualización: 8 nov 2026. Versión vigente del prompt: **v4**.

---

## 1. Qué es el proyecto

Un sistema para que una persona mejore su nivel de ajedrez midiendo su progreso con datos.

- **Usuario:** habla español. Juega en Lichess y quiere usar **exclusivamente herramientas de Lichess** para entrenar.
- **Cuentas:**
  - `peondeloto`: la cuenta donde quiere mejorar. Es nueva, con rating provisional de unos 1570 en 15+10.
  - `dvillaj131313`: la cuenta antigua, de la que sale el diagnóstico inicial (805 partidas del 4 jul al 1 nov 2026; 767 son 10+0 y solo 80 traen análisis de Stockfish).
- **Objetivo:** llegar a **1850 en partidas rápidas 15+10**.
- **Dedicación:** 5 a 8 horas semanales, incluyendo jugar, revisar, táctica, aperturas y finales.

Ejemplos de lo que se espera de ti: analizar partidas con el prompt, interpretar la tabla de progreso, proponer una versión nueva del prompt, actualizar el perfil o explicar el sistema.

---

## 2. Mapa de ficheros

```
ajedrez/
├── README.md                  guía de uso para el usuario, incluido el análisis local
├── CONTEXTO_IA.md             este documento
├── perfil_peondeloto.md       diagnóstico, áreas de mejora, línea base y objetivos
├── metricas_pgn.py            script que calcula las métricas, sin dependencias
├── verificar_pgn.py           comprueba que los PGN enriquecidos están completos y bien formados
├── pyproject.toml              versión del software y configuración de pytest
├── tests/                       pruebas unitarias del núcleo con pytest
├── analisis_local/            herramientas de análisis local con Stockfish (opcional; instrucciones en README.md, sección 4)
│   ├── analizar_local.py      analiza PGN con Stockfish y escribe el resultado en formato Lichess
│   ├── calibrar_con_lichess.py   compara el análisis local con el de Lichess
│   ├── nucleo.py              lógica pura: evaluaciones, clasificación, lectura y escritura de PGN
│   ├── validar_umbrales_offline.py   validación que no necesita motor
├── prompts/
│   ├── CHANGELOG.md           historial de versiones del prompt
│   └── prompt_analisis_partidas_v0.txt ... _v4.txt   (vigente: v4)
├── partidas/                  exportaciones de Lichess en PGN (originales, no se tocan)
├── partidas_analizadas/       PGN analizados en local (opcional)
├── analisis/                  PGN enriquecidos que entrega el prompt, un .pgn por partida
└── progreso/                  CSV que genera el script
```

**Fuente de verdad de cada cosa:**

| Qué | Dónde |
|---|---|
| Métricas y agregados | `metricas_pgn.py`. Nunca los recalcules de memoria. |
| Que un PGN enriquecido está completo y bien formado | `verificar_pgn.py`. Lo que diga el modelo sobre su propia salida no sustituye a esta comprobación. |
| Diagnóstico, áreas de mejora (A1-A7), fuertes (S1-S4), línea base y objetivos | `perfil_peondeloto.md` |
| Evaluaciones y etiquetas de error cuando se analiza en local | `analisis_local/analizar_local.py` y la regla de `analisis_local/nucleo.py` |
| Cómo se explica cada partida | el prompt vigente |
| Qué cambió entre versiones del prompt | `prompts/CHANGELOG.md` |

**Numeración de prompts:** v0 (el original), v1, v2 y v3, sin huecos. Antes se llamaban v1 (el original), v2, v3 y v4; la tabla de equivalencias está en `prompts/CHANGELOG.md`. Si el usuario usa un nombre antiguo, tradúcelo con esa tabla.

---

## 3. Principios de diseño

1. **El prompt explica, el script mide.** Un modelo falla en aritmética de relojes y no recuerda cifras anteriores; el script sí. El prompt solo escribe cifras si las calcula con código o las copia de la fila del script.
2. **No inventes datos.** Distingue siempre entre evaluaciones reales de Stockfish (el PGN trae `%eval`) y estimaciones propias, y etiqueta las estimaciones como tales.
3. **Sé honesto sobre cómo has validado.** No afirmes haber usado python-chess ni Stockfish si no lo has hecho. Si validas con un comprobador propio, dilo.
4. **Las definiciones deben coincidir** entre script, prompt, perfil y README. Si cambias una, cámbiala en los cuatro sitios y anótalo en el changelog.
5. **No edites versiones antiguas del prompt.** Crea una nueva y regístrala en el changelog.
6. **Muestras pequeñas, conclusiones prudentes.** Con decenas de partidas, una semana mala no demuestra nada.

---

## 4. Flujo de trabajo

1. El usuario juega 15+10 en peondeloto.
2. Consigue evaluaciones: pide el análisis del ordenador en Lichess y exporta los PGN con relojes y evaluaciones, o analiza las partidas en local con `analisis_local/analizar_local.py` (Stockfish). Mide siempre sobre una sola versión de cada partida.
3. Guarda los originales en `partidas/` y ejecuta `metricas_pgn.py` para ver el progreso.
4. En un chat, pega el prompt y adjunta `perfil_peondeloto.md` y los PGN. Recibe un PGN enriquecido por partida, como fichero si el chat puede crearlos o como bloque de código si no.
5. Guarda los PGN enriquecidos en `analisis/` y ejecuta `verificar_pgn.py` para comprobar que no falta ninguna jugada.
6. Importa cada PGN verificado en un Estudio de Lichess para repasarlo.
7. Cada 20-30 partidas, compara la tabla del script con la línea base y los objetivos, y actualiza el perfil.

Comando habitual del script:

```
python metricas_pgn.py partidas/peondeloto --usuario peondeloto --ritmo 900+10 --base-hasta 2026-11-03 --csv progreso/progreso_peondeloto.csv
```

Comprobación de la salida del prompt:

```
python verificar_pgn.py --originales partidas/peondeloto --enriquecidos analisis
```

---

## 5. Indicadores y sus definiciones

Son las del script y las del prompt vigente. Si los usas, usa estas.

- **Tiempo usado por jugada** = reloj propio anterior − reloj propio actual + incremento, en segundos totales. La primera jugada se excluye.
- **% del tiempo disponible usado** = suma del tiempo usado / (tiempo base + incremento por cada jugada propia salvo la primera). Se usa el tiempo disponible y no solo el base porque con incremento el porcentaje sobre el base engaña en partidas largas.
- **Mediana de segundos por jugada.**
- **Blunders, errores, imprecisiones:** jugadas propias que el PGN original marca como Blunder, Mistake e Inaccuracy, sobre toda la partida.
- **Ventaja máxima:** mayor evaluación a favor del jugador en la partida. **Ventaja tirada:** llegó a +3,0 o más y no ganó.
- **Derrota corta:** derrota en menos de 25 jugadas.
- **Fases del script:** apertura hasta la jugada 10, medio juego de la 11 a la 25, final desde la 26.

**Etiquetas de error (Inaccuracy, Mistake, Blunder).** Son las de Lichess, y el análisis local las reproduce con su misma regla: oportunidad de ganar = 2 / (1 + e^(−0,00368208 · cp)) − 1, con cp recortado a ±1000, y se marca la jugada según cuánto cae esa oportunidad para quien mueve: 0,1 o más es Inaccuracy, 0,2 o más Mistake y 0,3 o más Blunder. Con las evaluaciones de Lichess, esta regla reproduce sus etiquetas en el 99,79 % de 5.657 jugadas con evaluación normal y en el 97,87 % de 235 jugadas con mate (98 partidas del usuario). Un análisis local con otro motor o profundidad dará cifras algo distintas: no mezcles ambos métodos en una misma comparación sin calibrarlos.

Los objetivos del perfil (por ejemplo, 1,2 blunders por partida o mediana de 8 s) son **propuestas de partida**, no referencias externas de lo que hace un jugador de 1850.

---

## 6. Reglas del PGN enriquecido (resumen del prompt v4)

El formato está pensado para importarse en un Estudio de Lichess sin fallos. Resumen, no sustituye al prompt:

- **Modo fichero (preferente):** un fichero `.pgn` por partida, con el nombre `AAAA-MM-DD_color_vs_rival_GameId.pgn`, entregado como archivo. El PGN no se pega en el chat; el mensaje lleva solo una línea por partida con la comprobación de completitud.
- **Modo bloques** (si no se pueden crear ficheros): solo bloques de código PGN, uno por partida, sin texto fuera.
- **Completitud:** el PGN contiene todas las jugadas y el resultado final; no se abrevia ni se recorta. Se comprueba con código y, en modo fichero, releyendo el fichero entregado (regla 10 y punto k).
- Se conservan **todas las cabeceras originales**, seguidas de una línea en blanco.
- Comentario inicial pegado a la primera jugada: título del chat (`Color vs Rival — resumen de 3 a 5 palabras`), briefing de hasta 250 palabras.
- Cada jugada lleva su reloj en un bloque propio `{ [%clk h:mm:ss] }` y el comentario en un segundo bloque.
- Las negras repiten siempre el prefijo `N...` tras un comentario o variación.
- NAGs estándar (`$1`, `$2`, `$4`, `$6`...), nunca símbolos pegados al SAN.
- En cada jugada marcada con `$2`, `$4` o `$6`, una variación de **máximo 3 semijugadas**, con alternativa del mismo bando.
- **En los comentarios no se permiten** corchetes (salvo `[%clk]` y `[MOMENTO CLAVE ★]`), paréntesis, barras ni signos de apertura. Tampoco enumeraciones tipo `1)`: se usa "Primero:", "Segundo:".
- Las evaluaciones originales (`%eval`) **no se conservan** en la salida.
- Comas decimales en el texto; evaluaciones con signo y punto (+1.8).
- Debriefing final de hasta 450 palabras, con lecciones, tabla de tiempos, indicadores, comparativa de patrones y 2 o 3 posiciones FEN con la pregunta "Que juegas aqui?".
- Máximo 15 a 20 jugadas comentadas; sin evaluaciones, 8 a 12.

---

## 7. Estado actual

**Resultados del diagnóstico** (detalle en el perfil):
- peondeloto (21 partidas 15+10): 31 % de puntos, mediana de 3 s por jugada, 14 % del tiempo disponible usado frente a 51 % del rival, 2,5 blunders por partida en las 10 analizadas, 48 % de partidas perdidas en menos de 25 jugadas.
- dvillaj131313 (767 partidas 10+0): 50 % de puntos, 2,36 blunders por partida en las 80 analizadas, 23 de 80 partidas analizadas con ventaja de +3,0 o más que no se ganaron.

**Pruebas del prompt realizadas:**
- v0 con tres partidas de peondeloto (una sin evaluaciones, dos con ellas). Destapó los problemas corregidos en v1.
- v2 con una partida sin evaluaciones. Destapó los problemas corregidos en v3.
- **v3 y v4 no se han probado todavía.** Tampoco se ha probado ninguna versión en un chat nuevo: las pruebas se hicieron en una conversación donde el ejecutor ya conocía los fallos, así que no miden que un modelo la cumpla a la primera.

**Análisis local** (`analisis_local/`):
- Probado: la lógica pura (18 pruebas), la regla de clasificación contra Lichess (99,79 % y 97,87 %) y el flujo completo con un motor simulado sobre dos partidas reales.
- **No probado:** la integración con python-chess y Stockfish reales, porque el entorno donde se construyó no tenía red ni motor. El usuario debe ejecutar `analizar_local.py --autotest` y `calibrar_con_lichess.py`.

**Pendiente:**
- Ejecutar el autotest y la calibración con Stockfish real. Si el usuario pasa a análisis local, reanalizar las partidas antiguas y recalcular la línea base con el mismo método.
- Probar la v4 con una partida analizada: modo fichero, línea de indicadores y verificación con `verificar_pgn.py`.
- Reescribir el apartado "veredicto honesto" del prompt sin signos de interrogación, que el modelo podría copiar y romper la regla de caracteres seguros.
- Decidir si los "Patrones recurrentes" salen del prompt y se apoyan solo en el perfil.
- Revisar el objetivo del 40 % del tiempo disponible cuando haya más datos.

---

## 8. Cómo comportarte

**Idioma y tono:** responde en español, con cercanía y sin rodeos. Celebra lo que funciona, señala los errores como oportunidades concretas y no suavices los problemas reales.

**Antes de analizar un fichero**, comprueba que es lo que parece:
- Busca `%eval` y `%clk`. Si el usuario dice que está analizado y no hay `%eval`, díselo.
- Compara con ficheros anteriores (por ejemplo, con un hash) por si es el mismo.
- Comprueba quién es el jugador y el ritmo (`TimeControl 900+10` es 15+10).
- Si faltan evaluaciones, ofrece las dos vías: análisis de Lichess o análisis local. No digas que el análisis local está validado con Stockfish real mientras no lo haya probado el usuario.

**Al crear una versión nueva del prompt:**
1. Copia la vigente a `prompts/prompt_analisis_partidas_vN.txt`.
2. Aplica solo los cambios pedidos. Si ves otros problemas, avisa y no los incluyas sin permiso.
3. Si cambias una definición, actualiza script, perfil y README.
4. Registra en `prompts/CHANGELOG.md` qué cambió, por qué y qué se ha probado.

**Al generar un PGN enriquecido:** valida legalidad de jugadas, variaciones y FEN con python-chess si está disponible. Si no lo está, di cómo has validado. Comprueba que la línea principal es idéntica a la original y que se cumplen los límites de palabras. Si puedes crear ficheros, entrégalos y no pegues el PGN en el chat. Antes de entregar, comprueba la completitud y recuerda al usuario que puede ejecutar `verificar_pgn.py`.

**Qué no hacer:**
- No inventes evaluaciones, motivos tácticos ni cifras que no se desprendan de las jugadas.
- No presentes como aproximadas las cifras que el prompt exige exactas.
- No cambies el alcance de una petición sin preguntar.
- No afirmes que algo funciona sin haberlo probado.

---

## 9. Lecciones aprendidas

- Las enumeraciones con paréntesis (`1)`, `a)`) rompen la regla de balance de paréntesis. Lo mismo ocurre con plantillas que contienen corchetes o barras y que el modelo copia literalmente.
- Los porcentajes sobre el tiempo base engañan con incremento en partidas largas (65 % frente a 38 % sobre el tiempo disponible en una partida de 67 jugadas).
- Cifras repetidas en varias secciones gastan el límite de palabras y no aportan.
- Un ejecutor que conoce los fallos de un prompt no demuestra que el prompt funcione. Para validarlo, hay que probarlo en un chat nuevo.
- Un fichero que "parece nuevo" puede ser idéntico a uno anterior.
- Sin red ni motor, separar la lógica pura y probarla con un motor simulado permite validar casi todo, pero no sustituye a una prueba con el motor real.
- Un PGN pegado en el chat puede llegar incompleto, recortado o mal transcrito. Entregarlo como fichero generado por código y verificarlo con `verificar_pgn.py` lo evita; la comprobación debe hacerse sobre el fichero, no sobre lo que el modelo cree haber escrito.

---

## 10. Glosario

- **PGN:** formato de texto estándar para partidas de ajedrez.
- **SAN:** notación algebraica estándar de las jugadas (`Nf3`, `O-O`, `exd5`).
- **NAG:** código numérico de anotación (`$1` buena, `$2` error, `$4` error grave, `$6` imprecisión).
- **FEN:** cadena de texto que describe una posición concreta.
- **Semijugada:** movimiento de un solo bando. Una jugada completa tiene dos.
- **`%clk` y `%eval`:** etiquetas de reloj y de evaluación de Stockfish que Lichess puede incluir en los comentarios del PGN.
- **Estudio de Lichess:** herramienta de Lichess donde se importan y repasan partidas anotadas.
- **15+10:** 15 minutos más 10 segundos de incremento por jugada (`900+10`).
