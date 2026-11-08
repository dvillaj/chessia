# Changelog

Historial de cambios del software. El historial de versiones del prompt de análisis
se mantiene por separado en [`prompts/CHANGELOG.md`](prompts/CHANGELOG.md).

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
