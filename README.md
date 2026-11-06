# Sistema de entrenamiento de ajedrez con Lichess y Claude

Objetivo: pasar de ~1570 a 1850 en partidas rápidas 15+10 con la cuenta **peondeloto**, usando solo herramientas de Lichess y midiendo el progreso con datos.

El sistema tiene **tres piezas** que se reparten el trabajo:

| Pieza | Fichero | Qué hace |
|---|---|---|
| El contexto | `perfil_peondeloto.md` | Tus puntos fuertes, áreas de mejora (códigos A1-A7), línea base y objetivos. |
| El entrenador | `prompt_analisis_partidas_v3.txt` | Explica cada partida y devuelve un PGN enriquecido para Lichess Study, con una línea de indicadores por partida. |
| El medidor | `metricas_pgn.py` | Calcula las métricas de progreso. Los números los saca el script, no el modelo. |

> **Idea clave:** el prompt explica, el script mide. No le pidas a un modelo que haga aritmética de relojes ni que recuerde tus cifras anteriores: para eso están el script y el perfil. Desde la v3 el prompt también escribe una línea de indicadores por partida, pero solo si los calcula con código o los copia de la fila del script; los agregados semanales salen siempre del script.

---

## 1. Resumen en 7 pasos

1. Juega 15+10 en peondeloto siguiendo las reglas del perfil.
2. En Lichess, **pide el análisis del ordenador** de tus partidas.
3. Exporta las partidas en PGN con **relojes y evaluaciones**.
4. Guarda el PGN en `partidas/peondeloto/`.
5. Ejecuta `metricas_pgn.py` y mira la tabla de progreso.
6. Abre un chat con Claude, pega el prompt, adjunta `perfil_peondeloto.md` y los PGN nuevos.
7. Copia cada bloque PGN que devuelve a un **Estudio de Lichess** y repásalo.

---

## 2. Requisitos

- **Python 3.8 o superior** (el script no necesita instalar nada más). Comprueba con `python --version`. En Windows puede ser `py --version`.
- Cuenta de **Lichess** (peondeloto) para exportar y pedir análisis.
- Acceso a **Claude** para el prompt.
- Un editor de texto cualquiera.

---

## 3. Estructura de carpetas

Crea una carpeta de trabajo, por ejemplo `ajedrez/`:

```
ajedrez/
├── README.md                       este documento
├── perfil_peondeloto.md            contexto: fuertes, áreas de mejora, línea base
├── prompt_analisis_partidas_v3.txt el prompt (versión actual)
├── CHANGELOG_prompt.md             historial de versiones del prompt
├── metricas_pgn.py                 el script de métricas
├── partidas/
│   └── peondeloto/                 tus exportaciones de Lichess (.pgn)
│       ├── lichess_peondeloto_2026-11-03.pgn
│       └── lichess_peondeloto_2026-11-05.pgn
├── analisis/                       los PGN enriquecidos que devuelve Claude
└── progreso/                       los CSV que genera el script
```

Conserva siempre los PGN originales: son tu archivo. Claude **no guarda tus ficheros** entre conversaciones, así que lo que no esté en tu carpeta se pierde.

---

## 4. Conseguir buenos PGN de Lichess

Sin análisis del ordenador no hay errores ni blunders que medir. Sin relojes no hay gestión del tiempo. Por eso importa cómo exportas.

### 4.1 Pedir el análisis

En cada partida terminada, abre su página y pulsa el botón para **solicitar el análisis del ordenador** (hace falta estar con tu sesión iniciada). Lichess puede limitar cuántos análisis se pueden pedir seguidos, así que conviene pedirlos poco después de jugar.

Consejo: pídelo para todas las partidas de 15+10, no solo para las que perdiste. Para medir si mejoras necesitas también las ganadas.

### 4.2 Exportar desde la web

Abre la página de exportación: `https://lichess.org/games/export/peondeloto`. Marca las opciones para incluir **tiempos de reloj** y **evaluaciones o análisis**, y filtra por fechas, ritmo o partidas analizadas si lo necesitas. Los nombres exactos de las opciones pueden cambiar; si dudas, mira la ayuda de esa página.

El fichero se llama algo como `lichess_peondeloto_2026-11-05.pgn`. Guárdalo en `partidas/peondeloto/`.

### 4.2 bis. Exportar con la API (alternativa)

Desde una terminal, con `curl`:

```
curl -H "Accept: application/x-chess-pgn" \
  "https://lichess.org/api/games/user/peondeloto?perfType=rapid&analysed=true&clocks=true&evals=true&opening=true&max=50" \
  -o partidas/peondeloto/lichess_peondeloto_2026-11-10.pgn
```

Los parámetros `analysed`, `clocks`, `evals`, `opening` y `max` están documentados en `https://lichess.org/api`. Compruébalos allí por si cambian.

> `perfType=rapid` incluye tanto 10+0 como 15+10. El filtro por ritmo exacto lo haces después con el script (`--ritmo 900+10`).

### 4.3 Cómo comprobar que el PGN sirve

Abre el fichero con un editor y busca `%eval` y `%clk`. Si no aparecen, el PGN no trae evaluaciones o relojes y hay que exportarlo de nuevo.

Si exportas varias veces con partidas repetidas, no pasa nada: el script elimina duplicados por `GameId`.

---

## 5. Medir tu progreso con `metricas_pgn.py`

### 5.1 Ejecutarlo

Desde la carpeta `ajedrez/`:

```
python metricas_pgn.py partidas/peondeloto --usuario peondeloto --ritmo 900+10 --base-hasta 2026-11-03 --csv progreso/progreso_peondeloto.csv
```

En Windows, si `python` no funciona, usa `py` en su lugar.

| Opción | Para qué sirve |
|---|---|
| `partidas/peondeloto` | Carpeta con PGN (se leen todos los `.pgn`) o uno o varios ficheros. |
| `--usuario` | Tu nombre en Lichess. Si no lo pones, usa el que más aparece. |
| `--ritmo 900+10` | Solo cuenta partidas 15+10. |
| `--base-hasta 2026-11-03` | Las partidas hasta esa fecha forman el grupo **BASE**; las posteriores se agrupan por semana. |
| `--csv` | Dónde guardar el CSV con una fila por partida. |

### 5.2 Leer la tabla

Imprime una tabla en markdown con una fila por periodo (BASE y semanas) y una fila final **OBJETIVO**:

| Columna | Qué mide |
|---|---|
| Puntos % | Resultado (victoria = 1, tablas = 0,5). |
| Mediana s/jugada | Segundos que tardas en una jugada típica. |
| % reloj usado | Tiempo pensado respecto al tiempo base. |
| Blunders/partida y Errores/partida | Solo en partidas con análisis. |
| Analizadas | Cuántas partidas del periodo traen análisis. |
| Derrotas cortas | Derrotas en menos de 25 jugadas. |
| Ventajas tiradas | Partidas analizadas en las que llegaste a +3,0 o más y no ganaste. |
| Racha derrotas | Mayor racha seguida de derrotas. |
| Máx. partidas/día | Mayor número de partidas en un solo día. |

Compara siempre cada fila con **BASE** y con **OBJETIVO**. Las definiciones exactas están al principio del script.

Dos cautelas:
- Con pocas partidas analizadas por periodo (como regla orientativa, menos de 10) las cifras de errores varían mucho de una semana a otra. Usa periodos más largos.
- Los objetivos del script son propuestas de partida, no referencias externas. Cámbialos en el diccionario `OBJETIVOS` si te parecen poco realistas.

### 5.3 Abrir el CSV

El CSV usa `;` como separador y coma decimal para abrirse directamente en Excel en español. Si lo lees con pandas: `pd.read_csv(ruta, sep=";", decimal=",")`.

---

## 6. Analizar partidas con el prompt

### 6.1 Preparar el chat

1. Abre un chat nuevo con Claude.
2. Pega el contenido de `prompt_analisis_partidas_v3.txt`.
3. Adjunta `perfil_peondeloto.md` y los PGN que quieras analizar (uno o varios; cada partida se procesa por separado).
4. Si quieres, pega también la tabla de progreso más reciente.
5. Opcional: si el chat no tiene entorno de código, pega la fila del CSV de cada partida. Así los indicadores de la partida coinciden con los del script; sin código y sin esa fila, el prompt omite la línea de indicadores.

Cada chat nuevo parte de cero. Si no quieres repetir el paso 2 cada vez, puedes crear un **Proyecto** en Claude y guardar ahí el prompt como instrucciones y el perfil como conocimiento. Según la ayuda oficial, los proyectos están disponibles para todos los usuarios y el contexto no pasa de un chat a otro dentro del proyecto salvo que lo añadas al conocimiento del proyecto. Cuando actualices el perfil, vuelve a subir la versión nueva.

### 6.2 Qué devuelve

Un bloque de código PGN **por partida**, sin texto fuera de los bloques. Cada uno incluye:

- Un **briefing** inicial (menos de 250 palabras): origen de los datos, diagnóstico de apertura, veredicto honesto y ajuste semanal.
- Jugadas con comentarios solo en los momentos clave, con NAGs y la mejor alternativa como variación de hasta 3 jugadas.
- Un **debriefing** final: reglas de oro, tabla de tiempos, una línea de indicadores de la partida, comparativa de patrones y 2 o 3 posiciones en FEN para repaso.

### 6.3 Llevarlo a un Estudio de Lichess

1. En Lichess crea un **Estudio** (por ejemplo, "Mis partidas 15+10").
2. Añade un capítulo nuevo e importa el PGN pegando el contenido del bloque.
3. Repite por cada partida. Guarda también el bloque en `analisis/` como copia.

El título de cada partida va como primera línea del comentario inicial, así que puedes usarlo como nombre del capítulo.

### 6.4 Qué esperar de la calidad

- **Con evaluaciones de Stockfish** en el PGN, las evaluaciones y variaciones salen del motor y son fiables.
- **Sin evaluaciones**, el prompt aplica el Plan B: evaluaciones estimadas por el modelo y menos comentarios. Úsalo solo como orientación y contrástalo con el análisis de Lichess.
- Las evaluaciones del PGN original (`%eval`) **no se conservan** en el PGN enriquecido, porque el prompt solo permite `[%clk]` en los comentarios. Lichess Study puede recalcular su propio análisis si lo pides.
- En la prueba que hicimos, el entorno del chat no tenía `python-chess`; la legalidad de jugadas, variaciones y FEN se comprobó con un comprobador propio y así se declara en el briefing. En otro entorno esto puede variar.

---

## 7. Versiones del prompt

El fichero vigente es `prompt_analisis_partidas_v3.txt`. El historial completo de cambios está en `CHANGELOG_prompt.md`. En resumen:

- **v1:** el prompt original.
- **v2:** siete correcciones surgidas de probarlo con tres partidas (paréntesis, cabeceras, tiempo usado, variaciones, plan B de python-chess, plantilla de FEN y origen de datos).
- **v3:** añade una línea de indicadores por partida en el debriefing y sube el límite del debriefing a 450 palabras. Aún no se ha probado con una ejecución real.

**Pendiente, opcional:** sacar los "Patrones recurrentes recientes" del prompt y apoyarse en el perfil, y reescribir el apartado del veredicto honesto sin signos de interrogación. Ambos están anotados en el changelog.

---

## 8. Rutina semanal (5-8 horas)

| Bloque | Horas | Qué hacer |
|---|---|---|
| Jugar 15+10 | 2-3 | Unas 4 partidas con las reglas del perfil. Máximo 3 o 4 por sesión y parar tras 2 derrotas seguidas. |
| Revisar | 1,5-2 | Pedir análisis, repasar primero las derrotas cortas con "Aprende de tus errores". |
| Táctica | 1,5-2 | Pocos problemas, con calma. Temas: pieza colgada, horquilla, clavada, mate en 2 y 3. |
| Aperturas y finales | 0,5-1 | Explorador de aperturas y práctica de finales. |

### Cada 20-30 partidas

1. Exporta y guarda los PGN nuevos.
2. Ejecuta el script con `--base-hasta` fijo (la fecha de tu línea base).
3. Pega la fila nueva en la sección 8 del perfil.
4. Pide a Claude un informe de progreso con este mensaje, adjuntando el perfil y la tabla:

> Te paso mi perfil y la tabla del script. Compara cada periodo con la BASE y el OBJETIVO, dime qué áreas (A1-A7) mejoran y cuáles no, y propón 2 prioridades para las próximas semanas. No uses cifras que no estén en la tabla.

5. Si cambian tus áreas de mejora, actualiza el perfil y anota la versión en su historial.

---

## 9. Problemas frecuentes

| Síntoma | Causa probable y solución |
|---|---|
| "No se ha encontrado ninguna partida" | La ruta es incorrecta o la carpeta no tiene ficheros `.pgn`. |
| "Ninguna partida cumple los filtros" | El nombre de usuario no coincide o el `--ritmo` no existe. Comprueba el campo `TimeControl` del PGN (15+10 es `900+10`). |
| Columnas de errores con `-` | Esas partidas no traen análisis. Pídelo en Lichess y vuelve a exportar. |
| `python` no se reconoce | En Windows usa `py`. En Mac o Linux prueba `python3`. |
| El CSV se ve en una sola columna | Importa con separador `;` o ábrelo con Excel en español. |
| Claude dice "evaluaciones estimadas" | El PGN no llevaba `%eval`. Pide análisis y exporta de nuevo. |
| El PGN enriquecido no se importa bien en el Estudio | Revisa que no hayas copiado texto extra fuera del bloque y que el comentario inicial vaya pegado a la primera jugada. |

---

## 10. Limitaciones que conviene recordar

- **Muestras pequeñas.** Con decenas de partidas, una semana mala no demuestra nada. Mira tendencias de varias semanas.
- **El rating de una cuenta nueva es provisional** y se mueve mucho al principio. No lo uses como medida de nivel durante las primeras partidas.
- **Las partidas analizadas pueden estar sesgadas** si solo analizas las que te interesan. Analiza todas las de 15+10.
- **El modelo puede equivocarse** en explicaciones tácticas, sobre todo sin evaluaciones. Contrasta lo importante con Stockfish en Lichess.
- **Los objetivos son propuestas.** Ajústalos según veas.
