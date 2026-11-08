# Changelog

Historial de cambios del software. El historial de versiones del prompt de análisis
se mantiene por separado en [`prompts/CHANGELOG.md`](prompts/CHANGELOG.md).

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
- Pruebas unitarias con `unittest` para el núcleo del análisis local.

### Requisitos

- Python 3.12 y Pipenv para instalar las dependencias del proyecto.
- `python-chess` y un ejecutable de Stockfish solo para el análisis local.
