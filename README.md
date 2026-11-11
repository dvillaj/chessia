# Sistema de entrenamiento de ajedrez con Lichess y Claude

Sistema para mejorar al ajedrez usando solo herramientas de Lichess y midiendo el progreso con datos. Pueden usarlo **varios jugadores**: cada uno tiene su perfil en `perfiles/<usuario>.md`, con su ritmo, su Elo y su objetivo.

| Pieza | Fichero | Qué hace |
|---|---|---|
| El contexto | `perfiles/<usuario>.md` | Cabecera con usuario, ritmo, Elo y objetivo; puntos fuertes, áreas de mejora, línea base y reglas. Se adjunta al prompt en cada chat. |
| El entrenador | `prompts/prompt_analisis_partidas_v6.txt` | Explica cada partida y devuelve un PGN enriquecido para Lichess Study. |
| El medidor | `metricas_pgn.py` | Calcula las métricas de progreso. Los números los saca el script, no el modelo. |
| El verificador | `verificar_pgn.py` | Comprueba que cada PGN enriquecido tiene todas las jugadas del original y cumple el formato. |
| El analizador local | `analisis_local/` | Analiza tus partidas con Stockfish en tu ordenador (opcional; instrucciones en la sección 4). |

> **Idea clave:** el prompt explica, el script mide. No le pidas a un modelo aritmética de relojes ni que recuerde tus cifras anteriores.

Si usas un modelo de IA para mantener el sistema, pásale también `CONTEXTO_IA.md`.

### Preparar el entorno

El entorno de Python se gestiona desde la raíz del proyecto con Pipenv. Necesitas Python 3.12 y Pipenv instalado. Desde la carpeta del proyecto, ejecuta:

```
pipenv install --dev
```

Esto instala las dependencias de ejecución y desarrollo definidas en `Pipfile` y `Pipfile.lock`, incluido `pytest`. Si no vas a ejecutar las pruebas, basta con `pipenv install`. Ejecuta los scripts de Python desde la raíz con `pipenv run python`; no hace falta activar un entorno virtual manualmente. Stockfish se instala aparte y solo es necesario para el análisis local.

El proyecto declara su nombre, versión y versión mínima de Python en `pyproject.toml`; el historial de cambios está en `CHANGELOG.md`. Se sigue versionado semántico: cambios incompatibles aumentan la versión mayor, funciones compatibles la menor y correcciones la versión de parche. Al publicar una versión, actualiza ambos ficheros y crea un tag Git con el mismo número (por ejemplo, `v1.0.0`). El proyecto se ejecuta como un conjunto de scripts y no se instala como paquete.

Las pruebas unitarias se ejecutan con `pytest` y están en `tests/`.

---

## 1. Resumen en 7 pasos

1. Juega tu ritmo habitual siguiendo las reglas del perfil.
2. Consigue evaluaciones: pide el análisis en Lichess o analiza en local (`analisis_local/`).
3. Guarda los PGN, con relojes y evaluaciones, en `partidas/dvillaj131313/` (o en `partidas_analizadas/` si los analizas en local).
4. Ejecuta `metricas_pgn.py` y mira la tabla de progreso.
5. En un chat con Claude, pega el prompt y adjunta tu perfil (`perfiles/<usuario>.md`) y los PGN nuevos.
6. Guarda en `analisis/` los PGN enriquecidos y ejecuta `verificar_pgn.py`.
7. Importa cada PGN verificado en un **Estudio de Lichess** y repásalo.

**Requisitos:** Python 3.12, Pipenv, cuenta de Lichess, acceso a Claude y un editor de texto. El análisis local necesita además Stockfish (sección 4); python-chess se instala con Pipenv.

---

## Varios usuarios

Cada usuario tiene su perfil, sus partidas y su CSV, todo con su nombre de Lichess. `perfiles/`, `partidas/` y `progreso/` están en `.gitignore` por ser datos personales; solo se versiona `perfiles/_plantilla.md`.

### Cómo se crea un perfil nuevo

Sustituye `<usuario>` por el nombre de Lichess. Los ejemplos usan 10+0 y objetivo 1800; cámbialos por los tuyos.

**1. Crea el perfil.**

```
pipenv run python perfiles.py nuevo <usuario> --ritmo 600+0 --objetivo 1800
```

- `--ritmo` es el control de tiempo de Lichess en segundos, `base+incremento`: `600+0` es 10+0, `900+10` es 15+10, `180+2` es 3+2.
- `--objetivo` es el rating que quieres alcanzar.
- Crea `perfiles/<usuario>.md` con la cabecera rellena y el cuerpo de la plantilla vacío, y guarda tu Elo actual de Lichess. No pisa un perfil que ya exista.

**2. Descarga las partidas.**

```
pipenv run python descargar_lichess.py <usuario>
```

Las guarda en `partidas/<usuario>/` y refresca el Elo del perfil. Necesita `LICHESS_TOKEN` en `.env`.

**3. Analízalas en local** (sección 4), con salida en `partidas_analizadas/`. Con Lichess basta si ya las analizó; hacen falta evaluaciones y relojes en todas.

**4. Calcula las métricas.**

```
pipenv run python metricas_pgn.py partidas_analizadas/<usuario> --usuario <usuario> --csv progreso/progreso_<usuario>.csv
```

El ritmo sale de la cabecera del perfil. Genera dos ficheros en `progreso/`: el CSV con una fila por partida y `tabla_<usuario>.md` con la tabla resumen. Si quieres fijar una línea base (todas las partidas hasta una fecha frente a las posteriores por semana), añade `--base-hasta AAAA-MM-DD`, o escribe `base_hasta: AAAA-MM-DD` en la cabecera del perfil. Sin ella, la tabla sale por semanas.

**5. Completa el perfil con Claude.** Abre un chat nuevo en claude.ai y pega el contenido de `prompts/prompt_crear_perfil_v0.txt`. Sube estos tres ficheros con el clip o el **+** (o arrástralos; `@` solo funciona en Claude Code):

- `perfiles/<usuario>.md`, el perfil vacío del paso 1;
- `progreso/tabla_<usuario>.md`;
- `progreso/progreso_<usuario>.csv`.

Claude te preguntará cuántas horas semanales entrenas y después devolverá el perfil completo: áreas de mejora (A1, A2...), puntos fuertes (S1, S2...), línea base, reglas de trabajo y plan semanal. Solo usa cifras de los ficheros; con pocos datos escribe "pendiente de medir" en vez de inventar.

**6. Guarda el resultado** como `perfiles/<usuario>.md`, sustituyendo el vacío. Comprueba que la cabecera entre las líneas `---` sigue intacta. Desde ahí, adjunta ese perfil al prompt de análisis de partidas (sección 6) en cada chat. Actualízalo cada 20 o 30 partidas nuevas, repitiendo los pasos 2 a 5.

Con menos de 30 partidas analizadas el perfil sale incompleto a propósito (aperturas, puntos fuertes y plan pueden quedar pendientes): son indicios, no conclusiones. El prompt de crear perfil se ha probado una vez en un chat nuevo, con 24 partidas: preguntó las horas, respetó la cabecera y sus cifras coincidieron con las del CSV.

**Cabecera del perfil** (entre dos líneas `---`): `usuario`, `ritmo` (por ejemplo `600+0`), `elo`, `elo_fecha`, `objetivo` y `base_hasta` (último día de la línea base). `descargar_lichess.py` y `perfiles.py elo <usuario>` actualizan `elo` y `elo_fecha` con el rating de Lichess para el tipo de partida del ritmo; si no hay red, el perfil no se toca. `metricas_pgn.py` usa `ritmo` y `base_hasta` si no los indicas, y `--perfil RUTA` fuerza otro perfil.

---

## 2. Estructura de carpetas

```
chessia/
├── README.md, CONTEXTO_IA.md
├── perfiles/                    un perfil por usuario (no se versiona, salvo _plantilla.md)
├── perfiles.py                  crea perfiles y actualiza el Elo desde Lichess
├── CHANGELOG.md                 historial de versiones del software
├── pyproject.toml               versión del software y configuración de pytest
├── Pipfile, Pipfile.lock        dependencias y entorno Python compartido
├── metricas_pgn.py              métricas de progreso
├── verificar_pgn.py             comprobación de los PGN enriquecidos
├── analisis_local/               herramientas de análisis local con Stockfish (opcional)
├── tests/                        pruebas unitarias con pytest
├── prompts/
│   ├── CHANGELOG.md             historial de versiones del prompt
│   └── prompt_analisis_partidas_v0.txt ... _v6.txt   (la vigente es v6)
│   └── prompt_crear_perfil_v0.txt   completa el perfil de un usuario nuevo
├── partidas/<usuario>/             exportaciones de Lichess (.pgn), sin tocar
├── partidas_analizadas/         PGN analizados en local (opcional)
├── analisis/                    PGN enriquecidos que entrega Claude, uno por partida
└── progreso/                    CSV que genera el script de métricas
```

Conserva siempre los PGN originales. Claude **no guarda tus ficheros** entre conversaciones.

---

## 3. Conseguir PGN con análisis y relojes

Sin análisis no hay errores que medir y sin relojes no hay gestión del tiempo.

**Opción A: análisis de Lichess**
- En la página de cada partida terminada, pulsa el botón para **solicitar el análisis del ordenador**. Lichess puede limitar los análisis seguidos, así que conviene pedirlos pronto. Pídelo en **todas** las partidas de 10+0, no solo en las perdidas.
- Exporta desde `https://lichess.org/games/export/dvillaj131313` marcando relojes y evaluaciones (los nombres exactos de las opciones pueden cambiar). O con la API:

```bash
source .env
user=dvillaj131313
fecha=$(date +%Y-%m-%d)
mkdir -p "partidas/$user"
curl -H "Accept: application/x-chess-pgn" -H "Authorization: Bearer $LICHESS_TOKEN" \
  "https://lichess.org/api/games/user/$user?perfType=rapid&analysed=true&clocks=true&evals=true&literate=true&opening=true&max=5000000" \
  -o "partidas/$user/lichess_${user}_${fecha}.pgn"
```

**Descarga incremental (recomendada):** `pipenv run python descargar_lichess.py dvillaj131313` baja todas las partidas del usuario a `partidas/dvillaj131313/` con relojes, evaluaciones, comentarios de errores, apertura y precisión, usando `LICHESS_TOKEN` de `.env`. Las siguientes ejecuciones solo traen las partidas posteriores a la última que ya tienes (`--completa` para rehacerlo todo, `--tipo rapid` o `--solo-analizadas` para filtrar). Detalles en la cabecera del script.

Los parámetros están documentados en `https://lichess.org/api`; compruébalos allí. `perfType=rapid` incluye varios ritmos; el filtro exacto se hace luego con `--ritmo 600+0`.

**Opción B: análisis local** con Stockfish, sin límites de Lichess y para todas tus partidas. Consulta la sección 4.

**Comprobación:** abre el PGN y busca `%eval` y `%clk`. Si no aparecen, falta análisis o relojes. Las partidas repetidas entre exportaciones no dan problemas: el script elimina duplicados por `GameId`. Mide siempre sobre **una sola versión** de cada partida.

---

## 4. Analizar partidas localmente con Stockfish (opcional)

El analizador local escribe evaluaciones y relojes en formato compatible con Lichess. El PGN resultante funciona con `metricas_pgn.py`, `verificar_pgn.py` y el prompt.

### Instalación

Ejecuta estos comandos desde la raíz del proyecto. Python 3.12 y Pipenv deben estar instalados; instala las dependencias del proyecto si aún no lo has hecho:

```
pipenv install
```

Stockfish se instala aparte:

- **macOS:** `brew install stockfish`
- **Debian y Ubuntu:** `sudo apt install stockfish` (queda en `/usr/games/stockfish`)
- **Windows:** descarga Stockfish desde su web oficial (stockfishchess.org), descomprímelo y anota la ruta del `.exe`.

El script busca el motor en `--motor`, en la variable de entorno `STOCKFISH_PATH`, en el PATH y en las rutas habituales.
Para no pasar la ruta en cada ejecución, crea un fichero `.env` en la raíz del proyecto con esta línea
(debe apuntar al ejecutable de Stockfish):

```
STOCKFISH_PATH=C:\WinBoard-4.8.0\stockfish\stockfish-windows-x86-64-universal.exe
```

Pipenv carga automáticamente las variables de `.env` al ejecutar con `pipenv run`. El fichero `.env` local
está excluido de Git; `--motor` y las variables de entorno ya definidas tienen prioridad sobre su valor.

Comprueba la instalación y ejecuta el autotest:

```
pipenv run python analisis_local/analizar_local.py --autotest
```

Debe terminar con `AUTOTEST OK`. Las pruebas unitarias del núcleo que no necesitan motor se ejecutan desde la raíz con:

```
pipenv run pytest
```

No requieren Stockfish. Incluyen una comprobación de la regla de etiquetas contra las de Lichess que usa los PGN de `partidas/` y se salta si hay menos de 30 partidas analizadas por Lichess.

### Analizar partidas

```
pipenv run python analisis_local/analizar_local.py partidas/dvillaj131313 --salida partidas_analizadas
```

Escribe un `<nombre>_analizado.pgn` por cada PGN de entrada. Las partidas que ya traen evaluaciones se copian sin cambios, salvo que se indique `--reanalizar`. Si traen `%eval` pero no los comentarios Inaccuracy, Mistake y Blunder (exportadas sin `literate=true`), se les añaden a partir de sus propias evaluaciones, con la misma regla y sin usar el motor. Si se indican varios límites, manda este orden: `--nodos`, `--tiempo`, `--profundidad`. El motor recibe `ucinewgame` al empezar cada partida, así que no arrastra la tabla hash de la anterior.

Si la partida no trae las cabeceras `ECO` y `Opening`, el analizador las añade como hace Lichess, con su base pública de aperturas (`chess-openings`, CC0, guardada en `analisis_local/base_aperturas/`; origen y forma de actualizarla en su `LEEME.md`). La búsqueda es por posición, así que las transposiciones dan el mismo resultado. Las partidas exportadas de Lichess ya las traen y no se tocan. Sobre 865 partidas de Lichess, el resultado coincidió con su etiqueta en el 97,5 %; las diferencias vienen de que la base del repositorio es más reciente que la que usa Lichess (nombres renombrados o líneas más profundas añadidas).

| Opción | Para qué sirve |
|---|---|
| `--profundidad N` | Profundidad por posición (por defecto 20). Más profundidad es más lento y más fiable; con 16 las evaluaciones son más ruidosas y a veces no se ve un mate largo. |
| `--tiempo S` | Segundos por posición; sustituye a la profundidad. |
| `--nodos N` | Límite de nodos por posición; sustituye a la profundidad y al tiempo. |
| `--procesos N` | Analiza N partidas a la vez, cada una con su propio Stockfish de 1 hilo. El resultado de cada partida no depende de N. Es la forma recomendada de acelerar el análisis. |
| `--hilos N` y `--hash MB` | Recursos de cada motor. Con 0 hilos se usa el valor por defecto del motor (1). `--hash` es por proceso, así que la memoria es N veces la de uno. Subir `--hilos` no es reproducible y en las pruebas fue más lento. |
| `--reanalizar` | Rehace también las partidas que ya traen evaluaciones. |
| `--maximo N` | Analiza como mucho N partidas; útil para medir el tiempo antes de procesar todas. |

Mientras analiza, el terminal muestra una barra de progreso con las partidas hechas, el porcentaje, el tiempo transcurrido, una estimación del tiempo restante (ETA) y cuántas partidas hay en curso. Cada partida terminada deja una línea con su contador (`OK [12/774] ...`). Si rediriges la salida a un fichero, no se dibuja la barra y solo quedan esas líneas.

El fichero de salida se escribe partida a partida y en el orden original, así que puedes interrumpir con Ctrl+C: lo analizado hasta ese momento queda guardado. Lo mismo ocurre si el equipo se apaga.

**Reanudar:** para continuar una tanda interrumpida, vuelve a lanzar **el mismo comando**. Las partidas que ya estén en el fichero de salida, completas, con las mismas jugadas y hechas con el mismo motor y el mismo límite, se reutilizan y solo se analiza el resto (la partida que quedó cortada se rehace). Si cambias el motor o el límite (`--profundidad`, `--tiempo` o `--nodos`), no se reutiliza nada, se avisa y el fichero se sobrescribe, porque no conviene mezclar métodos. `--hilos` y `--hash` no cuentan para esa comprobación. La reanudación supone que el PGN de entrada no ha cambiado de orden. Conviene empezar con `--maximo 1` para medir cuánto tarda en tu equipo.

Los PGN originales de Lichess se quedan en `partidas/`; los analizados localmente van a `partidas_analizadas/`. Mide el progreso **solo sobre una de esas carpetas**, nunca mezcles originales y analizados: si hay dos versiones de la misma partida, el script puede quedarse con la que no tiene evaluaciones.

Para medir partidas analizadas localmente:

```
pipenv run python metricas_pgn.py partidas_analizadas --usuario dvillaj131313 --ritmo 600+0 --csv progreso/progreso_dvillaj131313.csv
```

Para comprobar PGN enriquecidos contra los PGN analizados:

```
pipenv run python verificar_pgn.py --originales partidas_analizadas --enriquecidos analisis
```

### Calibrar el análisis

**Validar las reglas sin motor:** el script compara las etiquetas calculadas con las de Lichess:

```
pipenv run python analisis_local/validar_umbrales_offline.py partidas
```

Con las 98 partidas analizadas por Lichess disponibles al construirlo, el acuerdo fue del 99,79 % en 5.657 jugadas con evaluaciones normales y del 97,87 % en 235 casos con mate (reglas aproximadas). Esto valida **la regla**, no el motor.

Solo se usan partidas con `[Annotator "lichess.org"]`. Los PGN analizados en local se ignoran (el script dice cuántos), porque sus etiquetas las genera la propia regla y la validación sería circular, aunque tengan el mismo `GameId` que la partida original.

**Comparar con Stockfish:** vuelve a analizar partidas que Lichess ya evaluó y compara los resultados jugada a jugada:

```
pipenv run python analisis_local/calibrar_con_lichess.py partidas --maximo 10
```

También acepta `--procesos N`, igual que el analizador (misma salida con cualquier N).

Muestra la diferencia de evaluación, el acuerdo de etiquetas y los blunders por partida. Si el acuerdo es bajo, prueba con más profundidad, con `--tiempo` o con `--nodos`. Una vez elegido el ajuste, úsalo siempre igual para las partidas que quieras comparar.

### Limitaciones y problemas frecuentes

- Los resultados pueden diferir de Lichess por el motor y la profundidad. La línea base del perfil se calculó con análisis de Lichess; si cambias al análisis local, conviene reanalizar también las partidas antiguas con `--reanalizar` y recalcularla con el mismo método.
- Las reglas con mate son aproximadas (97,87 % de acuerdo con Lichess en 235 casos).
- Solo se analizan partidas estándar. Las variantes y las partidas con jugadas que `python-chess` no reconoce se copian sin analizar, con un aviso.
- No se añade evaluación a la jugada que da mate, igual que en Lichess. Una partida que acaba por abandono sí lleva evaluación en la última jugada.
- Si la mejor jugada del motor coincide con la jugada hecha pero la evaluación cae, la jugada se marca igual y no lleva variación; con suficiente profundidad es raro.
- El núcleo (18 pruebas), las reglas contra las etiquetas de Lichess en 98 partidas y el flujo con un motor simulado se han probado. Ya se ha generado un primer lote local con Stockfish 19 a profundidad 20 (4 partidas de `dvillaj131313`), pero el acuerdo con Lichess del análisis local aún no está medido: ejecuta `--autotest` y `calibrar_con_lichess.py` en tu equipo antes de fiarte de los resultados.

| Síntoma | Causa probable y solución |
|---|---|
| "Falta python-chess" | Ejecuta `pipenv install` desde la raíz del proyecto. |
| "No encuentro Stockfish" | Indica la ruta con `--motor` o con la variable `STOCKFISH_PATH`. |
| El autotest falla en "Checkmate is now unavoidable" | El motor no ve el mate: prueba con más profundidad o comprueba que es Stockfish. |
| El análisis es muy lento | Baja `--profundidad`, fija `--tiempo` por posición, sube `--hilos` o usa `--maximo` para trabajar por tandas. |
| "Jugada ilegal o no reconocida" | El PGN contiene una variante o está corrupto; la partida se copia sin analizar. |
| Las métricas salen sin análisis | Comprueba que mediste `partidas_analizadas`, no la carpeta de originales. |

---

## 5. Medir tu progreso con `metricas_pgn.py`

Desde la raíz del proyecto:

```
pipenv run python metricas_pgn.py partidas/dvillaj131313 --usuario dvillaj131313 --ritmo 600+0 --base-hasta 2026-11-07 --csv progreso/progreso_dvillaj131313.csv
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

## 6. Analizar partidas con el prompt

1. Abre un chat nuevo, pega `prompts/prompt_analisis_partidas_v6.txt` y adjunta tu perfil y los PGN (cada partida se procesa por separado). Si quieres, pega también la tabla de progreso.
2. Si el chat no tiene entorno de código, pega la fila del CSV de cada partida: así los indicadores coinciden con los del script. Sin código ni fila, el prompt omite esa línea.
3. Recibes **un PGN por partida**: como fichero descargable `AAAA-MM-DD_color_vs_rival_GameId.pgn` si el chat puede crear ficheros, o como bloque de código si no. Guárdalos en `analisis/`.
4. Antes de importar, comprueba que están completos:

```
pipenv run python verificar_pgn.py --originales partidas/dvillaj131313 --enriquecidos analisis
```

Imprime `OK` o `X` con los problemas: jugadas que faltan, cabeceras o relojes cambiados, caracteres prohibidos, límites de palabras. **No comprueba la legalidad** de las variaciones ni de las FEN. Si dice `FALTAN JUGADAS`, descarta ese PGN y pide generarlo de nuevo.

5. En Lichess crea un **Estudio**, añade un capítulo por partida e importa el PGN (sube el fichero o pega su contenido). El título de la partida va en la primera línea del comentario inicial.

Cada PGN lleva un briefing inicial, comentarios en los momentos clave con variaciones de hasta 3 semijugadas, y un debriefing final con lecciones, tabla de tiempos, indicadores de la partida, comparativa de patrones y 2 o 3 posiciones FEN.

**Calidad:** con evaluaciones de Stockfish en el PGN, las evaluaciones y variaciones son fiables. Sin ellas, el prompt aplica el Plan B (evaluaciones estimadas por el modelo): úsalo solo como orientación. Las evaluaciones del PGN original no se conservan en el enriquecido.

Cada chat nuevo parte de cero. Si no quieres repetir el paso 1, crea un **Proyecto** en Claude con el prompt como instrucciones y el perfil como conocimiento. Según la ayuda oficial, los proyectos están disponibles para todos los usuarios y el contexto no pasa de un chat a otro salvo que lo añadas al conocimiento del proyecto; cuando actualices el perfil, súbelo de nuevo.

**Versiones del prompt:** la vigente es la v6 (v0 es el original). El historial, con los motivos de cada cambio y la tabla de equivalencias de los nombres antiguos, está en `prompts/CHANGELOG.md`.

---

## 7. Rutina semanal (5-8 horas)

| Bloque | Horas | Qué hacer |
|---|---|---|
| Jugar 10+0 | 2-3 | Unas 4 partidas con las reglas del perfil. Máximo 3 o 4 por sesión; parar tras 2 derrotas seguidas. |
| Revisar | 1,5-2 | Repasar primero las derrotas cortas con "Aprende de tus errores". |
| Táctica | 1,5-2 | Pocos problemas, con calma: pieza colgada, horquilla, clavada, mate en 2 y 3. |
| Aperturas y finales | 0,5-1 | Explorador de aperturas y práctica de finales. |

**Cada 20-30 partidas:** guarda los PGN nuevos, ejecuta el script con el mismo `--base-hasta`, pega la fila nueva en el registro del perfil y pide a Claude un informe con este mensaje (adjuntando perfil y tabla):

> Te paso mi perfil y la tabla del script. Compara cada periodo con la BASE y el OBJETIVO, dime qué áreas (A1-A7) mejoran y cuáles no, y propón 2 prioridades para las próximas semanas. No uses cifras que no estén en la tabla.

---

## 8. Problemas frecuentes

| Síntoma | Causa probable y solución |
|---|---|
| "No se ha encontrado ninguna partida" | Ruta incorrecta o carpeta sin ficheros `.pgn`. |
| "Ninguna partida cumple los filtros" | El usuario no coincide o el `--ritmo` no existe. Mira `TimeControl` en el PGN (10+0 es `600+0`). |
| Columnas de errores con `-` | Esas partidas no traen análisis. Pídelo en Lichess o analiza en local y vuelve a medir. |
| Pipenv no encuentra Python | Comprueba que Python 3.12 está instalado y disponible para Pipenv. |
| `pipenv` no se reconoce | Instala Pipenv y vuelve a abrir la terminal para actualizar el PATH. |
| El CSV se ve en una sola columna | Importa con separador `;`. |
| Claude dice "evaluaciones estimadas" | El PGN no llevaba `%eval`. |
| `verificar_pgn.py` dice FALTAN JUGADAS | La salida se recortó. Descártala y genera de nuevo esa partida. |
| El PGN no se importa bien en el Estudio | Revisa que no haya texto extra fuera del PGN y que el comentario inicial esté pegado a la primera jugada. |

---

## 9. Limitaciones

- **Muestras pequeñas:** con decenas de partidas, una semana mala no demuestra nada.
- **El rating de una cuenta nueva es provisional** y se mueve mucho al principio.
- **Las partidas analizadas pueden estar sesgadas** si solo analizas las que te interesan. Analiza todas las de 10+0.
- **El modelo puede equivocarse** en explicaciones tácticas, sobre todo sin evaluaciones. Contrasta lo importante en Lichess.
- **Los objetivos son propuestas**, no referencias externas.
