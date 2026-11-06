# Perfil de entrenamiento: peondeloto

**Objetivo:** pasar de ~1570 a 1850 en partidas rápidas 15+10 (cuenta peondeloto).
**Dedicación:** 5-8 h semanales, solo herramientas de Lichess.
**Versión del perfil:** 1 (5 nov 2026). Actualizar cada 20-30 partidas nuevas.

> **Cómo usar este documento:** adjúntalo junto al PGN de las partidas nuevas. Las áreas de mejora tienen un código fijo (A1, A2...) para que la comparativa "SE REPITE, MEJORA o ES NUEVO" sea siempre sobre lo mismo. Los números de verdad los calcula `metricas_pgn.py`, no el modelo.

## 1. Datos de partida y sus límites

- **dvillaj131313** (cuenta antigua): 805 partidas del 4 jul al 1 nov 2026. 767 son 10+0 y no hay ninguna 15+10. Solo 80 de las 10+0 traen análisis de Stockfish.
- **peondeloto**: 21 partidas 15+10 del 31 oct al 2 nov. 10 traen análisis; las otras 11 se leyeron a ojo, sin motor.
- El rating de peondeloto es de cuenta nueva y se movió de 1500 a ~1970 y vuelta a ~1570 en tres días. No refleja aún tu nivel real.
- Muestras pequeñas. Las conclusiones sobre peondeloto son indicios, no certezas.
- Las partidas analizadas pueden no ser una muestra aleatoria (las eligió el jugador), así que las cifras de errores pueden estar sesgadas hacia partidas difíciles.

## 2. Puntos fuertes

| Código | Fuerte | Evidencia |
|---|---|---|
| S1 | Resistes y juegas bien las partidas largas | dvillaj: 65 % de puntos en partidas de 50 o más jugadas (130 partidas) y 57 % entre 25 y 35 |
| S2 | No te quedas sin tiempo | dvillaj: 26 victorias por tiempo frente a 10 derrotas por tiempo (las 10 parecen abandonos) |
| S3 | Rendimiento equilibrado entre colores y repertorio con estructura repetida | dvillaj: 49 % con blancas y 50 % con negras; London y Caro-Kann sostenidos en muchas partidas |
| S4 | Cuando la partida pasa de la jugada 25, compites | peondeloto: 5 victorias, 1 tablas y 4 derrotas en esas 10 partidas, contra rivales de ~1600 |

## 3. Áreas de mejora (códigos fijos)

| Código | Área | Evidencia | Métrica del script |
|---|---|---|---|
| A1 | **Partidas perdidas antes de la jugada 25** | peondeloto: 10 de 21 partidas (48 %); solo 1 victoria en las 11 que acabaron antes de la jugada 25. dvillaj: 22 % de las partidas | `derrotas_cortas` |
| A2 | **Ritmo: usas muy poco reloj y el tiempo no se usa en revisar amenazas** | peondeloto: mediana de 3 s por jugada, 19 % del tiempo base usado frente a 69 % del rival, 60 % de las jugadas en menos de 5 s. dvillaj: mediana de 2 s, 19 % frente a 37 %. Matiz: también cometes errores cuando piensas 7 s o más, así que hace falta un chequeo, no solo ir más lento | `mediana_s`, `uso_reloj_pct`, `rapidas_pct` |
| A3 | **Blunders, sobre todo en el medio juego** | peondeloto: 2,5 por partida (8 % de tus jugadas). dvillaj: 2,36 por partida; 36 en apertura, 101 en medio juego y 52 en final (ahí se concentra la mitad). Tienes casi los mismos blunders en las partidas ganadas que en las perdidas | `blunders`, `blunders_medio` |
| A4 | **Convertir ventajas** | dvillaj: en 56 de 80 partidas analizadas llegaste a +3,0 o más y no ganaste 23 de ellas. peondeloto: +7,1 en la jugada 26 (26.Rdd6??) y perdiste por mate | `ventaja_tirada` |
| A5 | **Seguridad del rey, ataques prematuros y capturas de peón con la dama** | Hipótesis por lectura sin motor, a contrastar: h4 y h5 tempranos con sacrificio Rxh5 en la Londres, rey en el centro y dama lejos en derrotas de 14 a 20 jugadas. Con blancas: 3 victorias y 7 derrotas en 10 partidas | Cualitativa (comparativa del prompt) |
| A6 | **Rachas y sesiones largas** | peondeloto: 14 partidas el 1 nov (3 victorias, 1 tablas, 10 derrotas), racha de 6 derrotas seguidas. dvillaj: hasta 47 partidas en un día | `racha_derrotas`, `max_dia` |
| A7 | **Repertorio con negras sin estructura estable** | peondeloto: 5 respuestas distintas a 1.e4 en 5 partidas; 0 victorias con 1...d5 en 4 partidas contra 1.d4. dvillaj: Caro-Kann sin variante identificada, 45 %; Baltic, 46 % | Cualitativa: variedad de aperturas por color |

## 4. Línea base (calculada con `metricas_pgn.py`)

| Métrica | peondeloto 15+10 (21 partidas) | dvillaj 10+0 (767 partidas) | Objetivo propuesto |
|---|---|---|---|
| Puntos | 31 % | 50 % | sin objetivo fijo |
| Mediana de segundos por jugada | 3,0 | 2,0 | 8 o más |
| Media de segundos por jugada | 6,0 | 3,6 | |
| % del tiempo base usado | 19 % (rival 69 %) | 19 % (rival 37 %) | 40 % o más |
| % de jugadas rápidas (10 o más, 3 s o menos) | 41 % | 59 % | |
| Blunders por partida | 2,50 (10 analizadas) | 2,36 (80 analizadas) | 1,2 o menos |
| Errores (mistakes) por partida | 1,50 | 1,12 | 0,8 o menos |
| Imprecisiones por partida | 2,40 | 3,01 | |
| % de jugadas que son blunders | 8,0 % | 8,2 % | |
| Derrotas en menos de 25 jugadas | 48 % | 22 % | 15 % o menos |
| Ventajas tiradas (analizadas) | 1 de 10 | 23 de 80 | 10 % o menos |
| Racha de derrotas más larga | 6 | 9 | 3 o menos |
| Máx. partidas en un día | 14 | 47 | 5 o menos |

**Nota:** los objetivos son propuestas de partida y se pueden ajustar en el script (`OBJETIVOS`); no son referencias externas de lo que hace un jugador de 1850. Las definiciones exactas están al principio del script. Excluye la primera jugada de cada bando, por eso algunas cifras difieren ligeramente de otros cálculos.

## 5. Reglas de trabajo

**Chequeo antes de cada jugada, a partir de la 10 (salvo jugadas forzadas):**
1. ¿Qué amenaza el rival? Jaques, capturas y amenazas.
2. Tras mi jugada, ¿queda algo sin defender o mal defendido?
3. ¿Mi rey sigue seguro? Evito sacrificios y capturas de peón con la dama sin calcular.
4. Si estoy mejor, ¿puedo simplificar en vez de complicar?

**Sesiones:** máximo 3 o 4 partidas. Si pierdo 2 seguidas, paro y analizo.

## 6. Plan semanal (5-8 h, solo Lichess)

- **Jugar 15+10 (2-3 h):** unas 4 partidas por semana, con las reglas de arriba.
- **Revisar partidas (1,5-2 h):** pedir análisis del ordenador a todas las partidas y repasar primero las derrotas cortas con "Aprende de tus errores".
- **Táctica (1,5-2 h):** pocos problemas, resueltos con calma. Temas: pieza colgada, horquilla, clavada, mate en 2 y 3, y jugadas de defensa.
- **Aperturas y finales (0,5-1 h):** explorador de aperturas para fijar el repertorio (A7) y práctica de finales de Lichess.

## 7. Carpetas sugeridas en tu ordenador

```
ajedrez/
  perfil_peondeloto.md        este documento
  metricas_pgn.py             el script
  partidas/                   exportaciones de Lichess con análisis y relojes (.pgn)
  analisis/                   los PGN enriquecidos que devuelve el prompt
  progreso_peondeloto.csv     lo genera el script
```

Comando habitual (desde la carpeta `ajedrez`):

```
python metricas_pgn.py partidas --usuario peondeloto --ritmo 900+10 --base-hasta 2026-11-03
```

## 8. Registro de progreso (pega aquí la tabla del script cada 20-30 partidas)

| Fecha de corte | Partidas | Mediana s | % reloj | Blunders por partida | Derrotas cortas | Ventajas tiradas | Notas |
|---|---|---|---|---|---|---|---|
| 2026-11-03 (BASE) | 21 | 3,0 | 19 % | 2,50 | 48 % | 1 de 10 | Línea base |

## 9. Historial de versiones

- **v1 (5 nov 2026):** primer diagnóstico con 805 partidas de dvillaj131313 y 21 de peondeloto.
