# Entorno local de análisis con Stockfish

Analiza tus partidas en tu ordenador con Stockfish y escribe el resultado en el mismo formato que usa Lichess. Así todas tus partidas tienen evaluaciones reales, sin depender de pedir el análisis una a una en Lichess.

El PGN que sale funciona sin cambios con `metricas_pgn.py`, `verificar_pgn.py` y el prompt.

## Qué incluye

| Fichero | Para qué sirve | ¿Necesita Stockfish? |
|---|---|---|
| `analizar_local.py` | Analiza PGN y escribe `[%eval]`, `[%clk]`, comentarios Inaccuracy, Mistake y Blunder, y la mejor alternativa como variación. | Sí |
| `calibrar_con_lichess.py` | Compara tu análisis local con el de Lichess en las mismas partidas. | Sí |
| `validar_umbrales_offline.py` | Comprueba que la regla de clasificación reproduce las etiquetas de Lichess, usando solo las evaluaciones de Lichess. | No |
| `pruebas_nucleo.py` | 18 pruebas de la lógica interna. | No |
| `nucleo.py` | Lógica pura: evaluaciones, clasificación, lectura y escritura de PGN. | No |
| `requirements.txt` | Dependencias de Python (`chess`, es decir, python-chess). | No |

## 1. Instalación

**1. Python 3.9 o superior.** Comprueba con `python --version` (en Windows, `py --version`).

**2. Entorno virtual**, desde la carpeta `ajedrez/entorno`:

```
# macOS y Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
py -m venv .venv
.venv\Scripts\activate
```

**3. Dependencias:**

```
pip install -r requirements.txt
```

**4. Stockfish.** Es un programa aparte:

- **macOS:** `brew install stockfish`
- **Debian y Ubuntu:** `sudo apt install stockfish` (queda en `/usr/games/stockfish`)
- **Windows:** descarga Stockfish de su web oficial (stockfishchess.org), descomprime y anota la ruta del `.exe`.

El script lo busca en `--motor`, en la variable de entorno `STOCKFISH_PATH`, en el PATH y en las rutas habituales.

**5. Comprobar la instalación:**

```
python analizar_local.py --autotest --motor /ruta/a/stockfish
```

Debe terminar con `AUTOTEST OK`. Analiza una partida corta con mate y comprueba que las evaluaciones, la detección del error y la escritura del PGN son correctas.

Las pruebas que no necesitan motor se ejecutan con `python pruebas_nucleo.py`.

## 2. Analizar tus partidas

```
python analizar_local.py ../partidas/peondeloto --salida ../partidas_analizadas --motor /ruta/a/stockfish
```

Escribe un `<nombre>_analizado.pgn` por cada PGN de entrada. Las partidas que ya traen evaluaciones se copian sin cambios, salvo con `--reanalizar`.

| Opción | Para qué sirve |
|---|---|
| `--profundidad N` | Profundidad de análisis por posición (por defecto 16). Más profundidad es más lento y más fiable. |
| `--nodos N` | Límite de nodos por posición; sustituye a la profundidad. |
| `--hilos N` y `--hash MB` | Recursos del motor. Con 0 hilos se usa el valor por defecto del motor. |
| `--reanalizar` | Rehace también las partidas que ya traen evaluaciones. |
| `--maximo N` | Analiza como mucho N partidas. Útil para medir el tiempo antes de lanzar todo. |

Puedes interrumpir con Ctrl+C: lo analizado hasta ese momento se guarda.

**Consejo:** prueba primero con `--maximo 1` y mide cuánto tarda. Depende de tu procesador y de la profundidad.

### Cómo encaja con el resto del sistema

1. Los PGN originales de Lichess se quedan en `partidas/`. No se tocan.
2. Los analizados en local van a `partidas_analizadas/`.
3. Para medir el progreso, ejecuta el script de métricas **solo sobre `partidas_analizadas`**:

```
python ../metricas_pgn.py ../partidas_analizadas --usuario peondeloto --ritmo 900+10 --csv ../progreso/progreso_peondeloto.csv
```

4. Para el prompt, adjunta el PGN analizado como si fuera el original, y verifica la salida contra él:

```
python ../verificar_pgn.py --originales ../partidas_analizadas --enriquecidos ../analisis
```

> **No mezcles originales y analizados en la misma carpeta** al medir. Si hay dos versiones de la misma partida, el script de métricas se queda con la primera que encuentra y puede ser la que no tiene evaluaciones.

## 3. Calibrar antes de fiarte de los números

**A. Sin motor.** `validar_umbrales_offline.py` toma tus partidas analizadas por Lichess y comprueba si la regla de clasificación reproduce sus etiquetas:

```
python validar_umbrales_offline.py ../partidas
```

Con las 98 partidas analizadas por Lichess que había disponibles al construirlo:

| Casos | Jugadas | Acuerdo con Lichess |
|---|---|---|
| Evaluaciones normales | 5.657 | 99,79 % |
| Con mate (reglas aproximadas) | 235 | 97,87 % |

Esto valida **la regla**, no el motor.

**B. Con motor.** `calibrar_con_lichess.py` vuelve a analizar en local partidas que Lichess ya analizó y las compara jugada a jugada:

```
python calibrar_con_lichess.py ../partidas --motor /ruta/a/stockfish --maximo 10
```

Muestra la diferencia de evaluación, la matriz de acuerdo de etiquetas y los blunders por partida de cada análisis. Si el acuerdo es bajo, o el local marca bastantes más o menos blunders que Lichess, repite con `--profundidad` mayor o con `--nodos`. Una vez elegido el ajuste, **úsalo siempre igual** en todas las partidas que quieras comparar.

## 4. Qué esperar y limitaciones

- **Los números cambiarán un poco respecto a Lichess:** otro motor, otra profundidad. La línea base del perfil se calculó con análisis de Lichess; si pasas a análisis local, conviene reanalizar también las partidas antiguas con `--reanalizar` y recalcular la línea base con el mismo método.
- **Las reglas con mate son aproximadas** (97,87 % de acuerdo con Lichess en 235 casos).
- **Solo se analizan partidas estándar.** Las variantes se copian sin analizar, y también las partidas con una jugada que python-chess no reconoce, con un aviso.
- **Sin evaluación en la jugada que da mate**, igual que Lichess. Una partida que acaba por abandono sí lleva evaluación en la última jugada.
- **Si la mejor jugada del motor coincide con la jugada hecha** pero la evaluación cae, la jugada se marca igual y no lleva variación. Con profundidad suficiente es raro.

### Qué se ha probado y qué no

- **Probado:** el núcleo (18 pruebas), la regla de clasificación contra las etiquetas de Lichess en 98 partidas, y el flujo completo de `analizar_local.py` con un **motor simulado** (por material) sobre dos partidas reales: conserva jugadas, relojes, resultado y cabeceras, y `metricas_pgn.py` lee la salida.
- **No probado:** la parte que usa **python-chess y Stockfish reales** (`AjedrezChess` y `MotorUCI`). Quien lo construyó no tenía acceso a la red ni al motor. Por eso existen `--autotest` y `calibrar_con_lichess.py`: ejecútalos tú antes de fiarte de los resultados.

## 5. Problemas frecuentes

| Síntoma | Causa probable y solución |
|---|---|
| "Falta python-chess" | No has activado el entorno virtual o no has ejecutado `pip install -r requirements.txt`. |
| "No encuentro Stockfish" | Indica la ruta con `--motor` o con la variable `STOCKFISH_PATH`. |
| El autotest falla en "Checkmate is now unavoidable" | El motor no ve el mate: prueba con más profundidad o comprueba que es Stockfish y no otro motor. |
| Muy lento | Baja `--profundidad`, sube `--hilos` o usa `--maximo` para trabajar por tandas. |
| "jugada ilegal o no reconocida" | El PGN tiene una jugada que python-chess no entiende (variante, PGN corrupto). La partida se copia sin analizar. |
| Las métricas salen sin análisis | El script leyó la versión sin evaluaciones de la partida. Mide solo sobre `partidas_analizadas`. |
