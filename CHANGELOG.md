# Changelog

Historial de cambios del software. El historial de versiones del prompt de análisis
se mantiene por separado en [`prompts/CHANGELOG.md`](prompts/CHANGELOG.md).

## [Sin publicar]

### Añadido

- `analizar_local.py` añade las cabeceras `ECO` y `Opening` a las partidas que no las traen, con la base
  de aperturas de Lichess (`analisis_local/base_aperturas/`, copia de `lichess-org/chess-openings`, CC0).
  Nuevo módulo `analisis_local/aperturas.py`: búsqueda por posición, hasta 40 semijugadas, como scalachess.
- `analizar_local.py` acepta `--procesos N` para analizar N partidas a la vez, cada una con su propio Stockfish.
  La salida no depende de N. El fichero de salida se escribe partida a partida, así que una interrupción
  no pierde lo ya analizado.
- `analizar_local.py` reanuda: al relanzar el mismo comando reutiliza las partidas de la salida anterior que estén
  completas, tengan las mismas jugadas y se hicieran con el mismo motor y límite, y solo analiza el resto. Con otro
  motor o límite avisa y lo rehace todo. Antes, relanzar vaciaba el fichero y empezaba de cero.
  Pruebas en `tests/test_reanudar.py`.
- `analizar_local.py` muestra una barra de progreso (hechas, porcentaje, tiempo transcurrido, ETA y partidas en
  curso) y un contador en la línea de cada partida. Las partidas que ya traen análisis se resumen en una
  sola línea al empezar. Pruebas en `tests/test_progreso.py`.
- `calibrar_con_lichess.py` acepta `--procesos N` para comparar N partidas a la vez, cada una con su propio
  Stockfish, y `--tiempo`.
- Pruebas en `tests/test_aperturas.py`.
- Pruebas en `tests/test_umbrales_lichess.py`: la regla de etiquetas debe coincidir con las de Lichess
  (al menos 99,5 % en jugadas normales y 95 % con mate); se saltan si faltan partidas en `partidas/`.

### Corregido

- `descargar_lichess.py` pedía `literate=false`, así que las partidas analizadas por Lichess llegaban con `%eval`
  pero sin los comentarios Inaccuracy, Mistake y Blunder, y `metricas_pgn.py` les contaba 0 errores (en
  peondeloto, 1,27 blunders por partida en la línea base en lugar de 2,41). Ahora pide `literate=true`.
- `analizar_local.py` copiaba sin cambios esas partidas por traer `%eval`. Ahora les añade los comentarios a partir
  de sus propias evaluaciones, con `nucleo.valorar` y sin motor (nuevas `nucleo.etiquetar_desde_evals` y
  `nucleo.tiene_juicios`). La primera jugada no se clasifica y no hay mejor jugada ni variación. Pruebas en
  `tests/test_nucleo.py` y `tests/test_reanudar.py`.
- `calibrar_con_lichess.py` fallaba con `AttributeError` desde la 1.1.0 por no definir `--tiempo`. Ahora usa
  la profundidad por defecto de `analizar_local.py` (20) y envía `ucinewgame` antes de cada partida.

### Cambiado

- `validar_umbrales_offline.py` expone `comparar` y `acuerdo` para reutilizarlos desde las pruebas; su salida
  no cambia. `pytest` añade `analisis_local` al `pythonpath`.

## [1.1.0] - 2026-11-08

### Añadido

- Opción `--tiempo` en `analizar_local.py` para limitar el análisis por segundos por posición.

### Cambiado

- La profundidad por defecto del análisis local pasa de 16 a 20, que da evaluaciones menos ruidosas.
- Orden de los límites de análisis: `--nodos`, `--tiempo`, `--profundidad`.
- `validar_umbrales_offline.py` solo usa partidas con `[Annotator "lichess.org"]` e informa de cuántas ignora.
- `calibrar_con_lichess.py` simplifica el ejemplo de uso de su cabecera.
- Ruta de ejemplo de `STOCKFISH_PATH` en el README apunta al ejecutable.

### Corregido

- El motor recibe `ucinewgame` al empezar cada partida y ya no arrastra la tabla hash de la anterior.
- La validación sin motor ya no es circular: antes podía contar como Lichess un PGN analizado en local con el mismo `GameId`.

## [1.0.1] - 2026-11-08

### Añadido

- Pruebas unitarias con `pytest` en el directorio `tests/`.
- Metadatos de versión y configuración de `pytest` en `pyproject.toml`.

### Cambiado

- `pytest` añadido a las dependencias de desarrollo de Pipenv.

## [1.0.0] - 2026-11-08

Primera versión documentada del sistema de entrenamiento y análisis de partidas.

### Añadido

- `metricas_pgn.py` para calcular métricas de progreso a partir de PGN y exportarlas
  a CSV.
- `verificar_pgn.py` para comprobar la integridad y el formato de los PGN enriquecidos.
- Herramientas opcionales en `analisis_local/` para analizar partidas con Stockfish,
  calibrar resultados frente a Lichess y validar los umbrales sin motor.
- Prompts de análisis de partidas, perfil de entrenamiento e instrucciones de contexto
  para el flujo de trabajo.
- Pruebas unitarias para el núcleo del análisis local.

### Requisitos

- Python 3.12 y Pipenv para instalar las dependencias del proyecto.
- `python-chess` y un ejecutable de Stockfish solo para el análisis local.
