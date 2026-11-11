# Perfil de entrenamiento: {usuario}

**Objetivo:** llegar a {objetivo} en partidas {ritmo} (los datos fijos están en la cabecera de este fichero).
**Dedicación:** (horas semanales) h, solo herramientas de Lichess.
**Versión del perfil:** 1. Actualizar cada 20-30 partidas nuevas.

> **Cómo usar este documento:** adjúntalo junto al PGN de las partidas nuevas y el prompt de análisis. Las áreas de mejora tienen un código fijo (A1, A2...) para que la comparativa "SE REPITE, MEJORA o ES NUEVO" sea siempre sobre lo mismo. Los números de verdad los calcula `metricas_pgn.py`, no el modelo.

## 1. Datos de partida y sus límites

(Número de partidas, fechas, cuántas están analizadas y con qué método. Indica las limitaciones de la muestra.)

## 2. Puntos fuertes

| Código | Fuerte | Evidencia |
|---|---|---|
| S1 | (pendiente) | (cifra del script) |

## 3. Áreas de mejora (códigos fijos)

| Código | Área | Evidencia | Métrica del script |
|---|---|---|---|
| A1 | (pendiente) | (cifra del script) | |

## 4. Línea base (calculada con `metricas_pgn.py`)

| Métrica | Valor | Objetivo propuesto |
|---|---|---|
| Puntos | | sin objetivo fijo |
| Mediana de segundos por jugada | | 8 o más |
| % del tiempo disponible usado | | 40 % o más |
| Blunders por partida | | 1,2 o menos |
| Errores (mistakes) por partida | | 0,8 o menos |
| Derrotas en menos de 25 jugadas | | 15 % o menos |
| Ventajas tiradas | | 10 % o menos |
| Racha de derrotas más larga | | 3 o menos |
| Máx. partidas en un día | | 5 o menos |

Los objetivos son propuestas de partida, no referencias externas de lo que hace un jugador de ese nivel.

## 5. Reglas de trabajo

(Pocas reglas concretas, derivadas de las áreas de mejora.)

## 6. Aperturas: dónde focalizar el estudio

(Evaluación en la jugada 10 por color y las ramas que peor salen, con su número de partidas.)

## 7. Plan semanal

(Reparto de horas entre jugar, revisar partidas, táctica y aperturas/finales.)

## 8. Registro de progreso (pega aquí la tabla del script cada 20-30 partidas)

| Fecha de corte | Partidas | Mediana s | % tiempo disponible | Blunders por partida | Derrotas cortas | Ventajas tiradas | Notas |
|---|---|---|---|---|---|---|---|

## 9. Historial de versiones

- **v1:** perfil creado con la línea base.
