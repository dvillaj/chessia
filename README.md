# Sistema de entrenamiento de ajedrez con Lichess y Claude

Objetivo: pasar de ~1570 a 1850 en partidas rápidas 15+10 con la cuenta **peondeloto**, usando solo herramientas de Lichess y midiendo el progreso con datos.

| Pieza | Fichero | Qué hace |
|---|---|---|
| El contexto | `perfil_peondeloto.md` | Puntos fuertes, áreas de mejora (A1-A7), línea base y objetivos. |
| El entrenador | `prompts/prompt_analisis_partidas_v4.txt` | Explica cada partida y devuelve un PGN enriquecido para Lichess Study. |
| El medidor | `metricas_pgn.py` | Calcula las métricas de progreso. Los números los saca el script, no el modelo. |
| El verificador | `verificar_pgn.py` | Comprueba que cada PGN enriquecido tiene todas las jugadas del original y cumple el formato. |
| El analizador local | `entorno/` | Analiza tus partidas con Stockfish en tu ordenador (opcional). Ver `entorno/README_ENTORNO.md`. |

> **Idea clave:** el prompt explica, el script mide. No le pidas a un modelo aritmética de relojes ni que recuerde tus cifras anteriores.

Si usas un modelo de IA para mantener el sistema, pásale también `CONTEXTO_IA.md`.

### Preparar el entorno

El entorno de Python se gestiona desde la raíz del proyecto con Pipenv. Necesitas Python 3.12 y Pipenv instalado. Desde la carpeta del proyecto, ejecuta:

```
pipenv install
```

Esto instala las dependencias definidas en `Pipfile` y `Pipfile.lock`. Ejecuta los scripts de Python desde la raíz con `pipenv run python`; no hace falta activar un entorno virtual manualmente. Stockfish se instala aparte y solo es necesario para el análisis local.

---

## 1. Resumen en 7 pasos

1. Juega 15+10 en peondeloto siguiendo las reglas del perfil.
2. Consigue evaluaciones: pide el análisis en Lichess o analiza en local (`entorno/`).
3. Guarda los PGN, con relojes y evaluaciones, en `partidas/peondeloto/` (o en `partidas_analizadas/` si los analizas en local).
4. Ejecuta `metricas_pgn.py` y mira la tabla de progreso.
5. En un chat con Claude, pega el prompt y adjunta `perfil_peondeloto.md` y los PGN nuevos.
6. Guarda en `analisis/` los PGN enriquecidos y ejecuta `verificar_pgn.py`.
7. Importa cada PGN verificado en un **Estudio de Lichess** y repásalo.

**Requisitos:** Python 3.12, Pipenv, cuenta de Lichess, acceso a Claude y un editor de texto. El análisis local necesita además Stockfish (ver su guía); python-chess se instala con Pipenv.

---

## 2. Estructura de carpetas

```
ajedrez/
├── README.md, CONTEXTO_IA.md, perfil_peondeloto.md
├── Pipfile, Pipfile.lock          entorno Python compartido del proyecto
├── metricas_pgn.py              métricas de progreso
├── verificar_pgn.py             comprobación de los PGN enriquecidos
├── entorno/                     análisis local con Stockfish (opcional)
├── prompts/
│   ├── CHANGELOG.md             historial de versiones
│   └── prompt_analisis_partidas_v0.txt ... _v4.txt   (la vigente es v4)
├── partidas/peondeloto/         exportaciones de Lichess (.pgn), sin tocar
├── partidas_analizadas/         PGN analizados en local (opcional)
├── analisis/                    PGN enriquecidos que entrega Claude, uno por partida
└── progreso/                    CSV que genera el script de métricas
```

Conserva siempre los PGN originales. Claude **no guarda tus ficheros** entre conversaciones.

---

## 3. Conseguir PGN con análisis y relojes

Sin análisis no hay errores que medir y sin relojes no hay gestión del tiempo.

**Opción A: análisis de Lichess**
- En la página de cada partida terminada, pulsa el botón para **solicitar el análisis del ordenador**. Lichess puede limitar los análisis seguidos, así que conviene pedirlos pronto. Pídelo en **todas** las partidas de 15+10, no solo en las perdidas.
- Exporta desde `https://lichess.org/games/export/peondeloto` marcando relojes y evaluaciones (los nombres exactos de las opciones pueden cambiar). O con la API:

```
curl -H "Accept: application/x-chess-pgn" \
  "https://lichess.org/api/games/user/peondeloto?perfType=rapid&analysed=true&clocks=true&evals=true&opening=true&max=50" \
  -o partidas/peondeloto/lichess_peondeloto_2026-11-10.pgn
```

Los parámetros están documentados en `https://lichess.org/api`; compruébalos allí. `perfType=rapid` incluye 10+0 y 15+10; el filtro exacto se hace luego con `--ritmo 900+10`.

**Opción B: análisis local** con Stockfish, sin límites de Lichess y para todas tus partidas. Está en `entorno/`.

**Comprobación:** abre el PGN y busca `%eval` y `%clk`. Si no aparecen, falta análisis o relojes. Las partidas repetidas entre exportaciones no dan problemas: el script elimina duplicados por `GameId`. Mide siempre sobre **una sola versión** de cada partida.

---

## 4. Medir tu progreso con `metricas_pgn.py`

Desde la raíz del proyecto:

```
pipenv run python metricas_pgn.py partidas/peondeloto --usuario peondeloto --ritmo 900+10 --base-hasta 2026-11-03 --csv progreso/progreso_peondeloto.csv
```

`--base-hasta` marca la fecha hasta la que las partidas forman el grupo **BASE**; las posteriores se agrupan por semana. Sin `--usuario` usa el nombre que más aparece.

Imprime una tabla con una fila por periodo y una fila final **OBJETIVO**. Compara siempre con BASE y con OBJETIVO:

| Columna | Qué mide |
|---|---|
| Puntos % | Resultado (victoria = 1, tablas = 0,5). |
| Mediana s/jugada | Segundos en una jugada típica. |
| % tiempo disponible usado | Tiempo pensado sobre el tiempo base más los incrementos. |
| Blunders y Errores por partida | Solo en partidas analizadas (columna Analizadas). |
| Derrotas cortas | Derrotas en menos de 25 jugadas. |
| Ventajas tiradas | Partidas analizadas en las que llegaste a +3,0 y no ganaste. |
| Racha derrotas, Máx. partidas/día | Mayor racha de derrotas y mayor número de partidas en un día. |

Cautelas: con menos de unas 10 partidas analizadas por periodo, las cifras de errores varían mucho; usa periodos más largos. Los objetivos son propuestas y se cambian en el diccionario `OBJETIVOS` del script.

El CSV usa `;` y coma decimal para abrirse en Excel en español (en pandas: `sep=";", decimal=","`).

---

## 5. Analizar partidas con el prompt

1. Abre un chat nuevo, pega `prompts/prompt_analisis_partidas_v4.txt` y adjunta `perfil_peondeloto.md` y los PGN (cada partida se procesa por separado). Si quieres, pega también la tabla de progreso.
2. Si el chat no tiene entorno de código, pega la fila del CSV de cada partida: así los indicadores coinciden con los del script. Sin código ni fila, el prompt omite esa línea.
3. Recibes **un PGN por partida**: como fichero descargable `AAAA-MM-DD_color_vs_rival_GameId.pgn` si el chat puede crear ficheros, o como bloque de código si no. Guárdalos en `analisis/`.
4. Antes de importar, comprueba que están completos:

```
pipenv run python verificar_pgn.py --originales partidas/peondeloto --enriquecidos analisis
```

Imprime `OK` o `X` con los problemas: jugadas que faltan, cabeceras o relojes cambiados, caracteres prohibidos, límites de palabras. **No comprueba la legalidad** de las variaciones ni de las FEN. Si dice `FALTAN JUGADAS`, descarta ese PGN y pide generarlo de nuevo.

5. En Lichess crea un **Estudio**, añade un capítulo por partida e importa el PGN (sube el fichero o pega su contenido). El título de la partida va en la primera línea del comentario inicial.

Cada PGN lleva un briefing inicial, comentarios en los momentos clave con variaciones de hasta 3 semijugadas, y un debriefing final con lecciones, tabla de tiempos, indicadores de la partida, comparativa de patrones y 2 o 3 posiciones FEN.

**Calidad:** con evaluaciones de Stockfish en el PGN, las evaluaciones y variaciones son fiables. Sin ellas, el prompt aplica el Plan B (evaluaciones estimadas por el modelo): úsalo solo como orientación. Las evaluaciones del PGN original no se conservan en el enriquecido.

Cada chat nuevo parte de cero. Si no quieres repetir el paso 1, crea un **Proyecto** en Claude con el prompt como instrucciones y el perfil como conocimiento. Según la ayuda oficial, los proyectos están disponibles para todos los usuarios y el contexto no pasa de un chat a otro salvo que lo añadas al conocimiento del proyecto; cuando actualices el perfil, súbelo de nuevo.

**Versiones del prompt:** la vigente es la v4 (v0 es el original). El historial, con los motivos de cada cambio y la tabla de equivalencias de los nombres antiguos, está en `prompts/CHANGELOG.md`.

---

## 6. Rutina semanal (5-8 horas)

| Bloque | Horas | Qué hacer |
|---|---|---|
| Jugar 15+10 | 2-3 | Unas 4 partidas con las reglas del perfil. Máximo 3 o 4 por sesión; parar tras 2 derrotas seguidas. |
| Revisar | 1,5-2 | Repasar primero las derrotas cortas con "Aprende de tus errores". |
| Táctica | 1,5-2 | Pocos problemas, con calma: pieza colgada, horquilla, clavada, mate en 2 y 3. |
| Aperturas y finales | 0,5-1 | Explorador de aperturas y práctica de finales. |

**Cada 20-30 partidas:** guarda los PGN nuevos, ejecuta el script con el mismo `--base-hasta`, pega la fila nueva en el registro del perfil y pide a Claude un informe con este mensaje (adjuntando perfil y tabla):

> Te paso mi perfil y la tabla del script. Compara cada periodo con la BASE y el OBJETIVO, dime qué áreas (A1-A7) mejoran y cuáles no, y propón 2 prioridades para las próximas semanas. No uses cifras que no estén en la tabla.

---

## 7. Problemas frecuentes

| Síntoma | Causa probable y solución |
|---|---|
| "No se ha encontrado ninguna partida" | Ruta incorrecta o carpeta sin ficheros `.pgn`. |
| "Ninguna partida cumple los filtros" | El usuario no coincide o el `--ritmo` no existe. Mira `TimeControl` en el PGN (15+10 es `900+10`). |
| Columnas de errores con `-` | Esas partidas no traen análisis. Pídelo en Lichess o analiza en local y vuelve a medir. |
| Pipenv no encuentra Python | Comprueba que Python 3.12 está instalado y disponible para Pipenv. |
| `pipenv` no se reconoce | Instala Pipenv y vuelve a abrir la terminal para actualizar el PATH. |
| El CSV se ve en una sola columna | Importa con separador `;`. |
| Claude dice "evaluaciones estimadas" | El PGN no llevaba `%eval`. |
| `verificar_pgn.py` dice FALTAN JUGADAS | La salida se recortó. Descártala y genera de nuevo esa partida. |
| El PGN no se importa bien en el Estudio | Revisa que no haya texto extra fuera del PGN y que el comentario inicial esté pegado a la primera jugada. |

---

## 8. Limitaciones

- **Muestras pequeñas:** con decenas de partidas, una semana mala no demuestra nada.
- **El rating de una cuenta nueva es provisional** y se mueve mucho al principio.
- **Las partidas analizadas pueden estar sesgadas** si solo analizas las que te interesan. Analiza todas las de 15+10.
- **El modelo puede equivocarse** en explicaciones tácticas, sobre todo sin evaluaciones. Contrasta lo importante en Lichess.
- **Los objetivos son propuestas**, no referencias externas.
