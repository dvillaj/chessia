# Perfil de entrenamiento: peondeloto

**Objetivo:** pasar de ~1600 a 1850 en partidas rápidas 15+10 (cuenta peondeloto).
**Dedicación:** 5-8 h semanales, solo herramientas de Lichess.
**Versión del perfil:** 3 (9 nov 2026). Actualizar cada 20-30 partidas nuevas.

> **Cómo usar este documento:** adjúntalo junto al PGN de las partidas nuevas. Las áreas de mejora tienen un código fijo (A1, A2...) para que la comparativa "SE REPITE, MEJORA o ES NUEVO" sea siempre sobre lo mismo. Los números de verdad los calcula `metricas_pgn.py`, no el modelo.

## 1. Datos de partida y sus límites

- **dvillaj131313** (cuenta antigua): 889 partidas del 4 jul al 9 nov 2026. Se usan las 784 de 10+0 (hasta el 7 nov); no hay ninguna 15+10. **Todas están analizadas:** 81 por Lichess y 703 en local con Stockfish 19 a profundidad 20.
- **peondeloto**: 24 partidas 15+10 del 31 oct al 4 nov, **todas analizadas**: 12 por Lichess y 12 en local con el mismo motor. Se excluye una partida contra la IA de Lichess.
- **Novedad respecto a la versión 2:** antes solo había 10 partidas de peondeloto y 80 de dvillaj con análisis, elegidas por el jugador. Ahora están todas, así que desaparece el sesgo hacia partidas difíciles.
- **Dos métodos mezclados:** el acuerdo entre el análisis local y el de Lichess aún no se ha calibrado (`calibrar_con_lichess.py`). En peondeloto ambos dan 2,33 blunders por partida en sus 12 partidas; en dvillaj, 2,41 con Lichess y 2,76 en local. Son partidas distintas, así que no es una calibración: tómalo como indicio de que no hay una diferencia grande.
- **Etiquetas recalculadas:** las 12 partidas de peondeloto analizadas por Lichess se descargaron con `%eval` pero sin las etiquetas Inaccuracy, Mistake y Blunder. `analizar_local.py` se las ha añadido con la regla de `analisis_local/nucleo.py` sobre las evaluaciones de Lichess, la misma que reproduce sus etiquetas en el 99,8 % de las jugadas. Las 10 que ya estaban en la versión 2 dan exactamente la misma cifra que entonces: 2,50 blunders por partida.
- El rating de peondeloto es de cuenta nueva: subió de 1500 a ~1970, bajó a ~1570 y está en ~1600 tras la última partida. Los rivales tienen una media de ~1680.
- Muestra pequeña en peondeloto. Sus conclusiones son indicios; las de dvillaj, con 784 partidas, son más firmes, pero son de 10+0.

## 2. Puntos fuertes

| Código | Fuerte | Evidencia |
|---|---|---|
| S1 | Resistes y juegas bien las partidas largas | dvillaj: 65 % de puntos en partidas de 50 o más jugadas (132 partidas) y 56 % entre 25 y 34 |
| S2 | No te quedas sin tiempo | dvillaj: 26 victorias por tiempo frente a 10 derrotas por tiempo. peondeloto: 1 y 1 |
| S3 | Rendimiento equilibrado entre colores y un repertorio con negras que ya conoces | dvillaj: 50 % con blancas y 50 % con negras (392 partidas cada uno); Caro-Kann en 230 partidas con un 50 % de puntos |
| S4 | Cuando la partida pasa de la jugada 25, compites con rivales más fuertes | peondeloto: 7 victorias, 1 tablas y 4 derrotas en esas 12 partidas (62 %), contra rivales de ~1680 de media |

## 3. Áreas de mejora (códigos fijos)

| Código | Área | Evidencia | Métrica del script |
|---|---|---|---|
| A1 | **Partidas perdidas antes de la jugada 25** | peondeloto: 10 de 24 partidas (42 %); de las 12 que acabaron antes de la jugada 25 ganaste 2 y perdiste 10. En 12 de las 24 nunca pasaste de +1,0 y sacaste un 8 % de los puntos: el problema empieza pronto. dvillaj: 172 de 784 (22 %) | `derrotas_cortas` |
| A2 | **Ritmo: usas muy poco reloj y el tiempo que usas no se convierte en precisión** | peondeloto: mediana de 3 s por jugada, 15 % del tiempo disponible usado frente a 53 % del rival, 59 % de las jugadas en menos de 5 s. dvillaj: mediana de 2 s, 19 % frente a 37 %. Matiz, ahora medido: a partir de la jugada 11, en peondeloto es blunder el 4,6 % de las jugadas de 3 s o menos, el 8,7 % de las de 4 a 6 s, el 15,4 % de las de 7 a 15 s y el 17,6 % de las de más de 15 s; dvillaj sigue la misma pauta, de 7,1 % a 18,8 %. No demuestra que pensar empeore: piensas más en las posiciones difíciles. Sí muestra que cuando piensas no estás revisando lo que hay que revisar, así que hace falta el chequeo de la sección 5, no solo ir más lento | `mediana_s`, `uso_disponible_pct`, `rapidas_pct` |
| A3 | **Blunders, sobre todo en el medio juego** | peondeloto: 2,41 por partida en la línea base (8,1 % de tus jugadas); 9 en apertura, 32 en medio juego y 15 en final (57 % en el medio juego). dvillaj: 2,72 por partida; 406, 1.138 y 590 (53 % en el medio juego). En ambas cuentas el 12 % de tus jugadas es un error o un blunder | `blunders`, `blunders_medio` |
| A4 | **Convertir ventajas** | dvillaj: llegaste a +3,0 o más en 583 de 784 partidas y no ganaste 218 de ellas (189 derrotas y 29 tablas): se escapa más de 1 de cada 3 ventajas claras. peondeloto: 2 de 10 (26.Rdd6?? con +7,1 y mate después; y unas tablas tras ir +6,9 con 29...Rxh3+?? y 33...Qxa2??). En peondeloto la cifra ya está en el objetivo, pero con 10 casos | `ventaja_tirada` |
| A5 | **Seguridad del rey: enroque tardío y rey en el centro** | Ya no es solo una hipótesis. peondeloto: 5 de las 10 derrotas cortas fueron sin enrocar; en 3 blunders o errores la mejor jugada era enrocar (17.g4? y 13.Qf3?? en lugar de O-O; 14...Qf6?? en lugar de O-O); 2 blunders movieron el rey al centro (18.Ke2?? y 16.Ke2??); y 12.O-O-O salió mal en dos Londres. Con enroque antes de la jugada 11, 60 % de puntos (5 partidas); con enroque posterior o sin enrocar, 34 %. dvillaj: 110 de las 172 derrotas cortas fueron sin enrocar (64 %); avanzar los peones g o h dos filas antes de enrocar y antes de la jugada 16 deja el 44 % de puntos (101 partidas) frente al 51 %. Ojo: una partida corta deja menos tiempo para enrocar, así que parte de la relación es al revés. **No se confirma** que las capturas de peón con la dama sean un problema específico: fallan un 14 % de las veces, como el resto de jugadas de dama (16 %), algo por encima del 12 % general | Cualitativa (comparativa del prompt) |
| A6 | **Rachas y sesiones largas** | peondeloto: 64 % de puntos en las 3 primeras partidas del día (11), 30 % de la 4.ª a la 6.ª (5) y 12 % de la 7.ª en adelante (8). Tras dos derrotas seguidas el mismo día, 28 % (9 partidas). 14 partidas el 1 nov y una racha de 6 derrotas. dvillaj: hasta 47 partidas en un día, 38 de 39 días con más de 5 y 44 % de puntos tras dos derrotas seguidas (162 partidas) | `racha_derrotas`, `max_dia` |
| A7 | **Repertorio con negras sin estructura estable en peondeloto** | peondeloto: 0 puntos en 4 partidas con 1...d5 contra 1.d4, y 5 respuestas distintas a 1.e4 en 5 partidas (1...d5, 1...g6, 1...b6, 1...e5 y 1...c5). Nunca has jugado la Caro-Kann, que en dvillaj es tu defensa más usada: 230 partidas y 50 %. dvillaj: 1...d5 contra 1.d4, 80 partidas y 48 %; Escandinava, 22 partidas y 41 % | Cualitativa: variedad de aperturas por color |

## 4. Línea base (calculada con `metricas_pgn.py`)

| Métrica | peondeloto 15+10 (22 partidas hasta el 3 nov) | dvillaj 10+0 (784 partidas) | Objetivo propuesto |
|---|---|---|---|
| Puntos | 34 % | 50 % | sin objetivo fijo |
| Mediana de segundos por jugada | 3,0 | 2,0 | 8 o más |
| Media de segundos por jugada | 6,3 | 3,6 | |
| % del tiempo disponible usado | 15 % (rival 53 %) | 19 % (rival 37 %) | 40 % o más |
| % de jugadas rápidas (10 o más, 3 s o menos) | 41 % | 59 % | |
| Blunders por partida | 2,41 (22 analizadas) | 2,72 (784 analizadas) | 1,2 o menos |
| Errores (mistakes) por partida | 1,45 | 1,16 | 0,8 o menos |
| Imprecisiones por partida | 2,68 | 2,51 | |
| % de jugadas que son blunders | 8,1 % | 9,0 % | |
| Derrotas en menos de 25 jugadas | 45 % (10 de 22) | 22 % | 15 % o menos |
| Ventajas tiradas (analizadas) | 2 de 22 (9 %) | 218 de 784 (28 %) | 10 % o menos |
| Racha de derrotas más larga | 6 | 9 | 3 o menos |
| Máx. partidas en un día | 14 | 47 | 5 o menos |

**Nota:** los objetivos son propuestas de partida y se pueden ajustar en el script (`OBJETIVOS`); no son referencias externas de lo que hace un jugador de 1850. Las definiciones exactas están al principio del script. El tiempo disponible es el tiempo base más el incremento de cada jugada propia salvo la primera. El script excluye la primera jugada de cada bando, por eso algunas cifras difieren ligeramente de otros cálculos. La línea base de peondeloto incluye ahora la partida del 3 nov, que no estaba en la versión 2, y todas sus partidas analizadas; por eso cambian los blunders (de 2,50 en 10 partidas a 2,41 en 22) y las ventajas tiradas (de 1 de 10 a 2 de 22).

## 5. Reglas de trabajo

**Chequeo antes de cada jugada, a partir de la 10 (salvo jugadas forzadas):**
1. ¿Qué amenaza el rival? Jaques, capturas y amenazas.
2. Tras mi jugada, ¿queda algo sin defender o mal defendido?
3. ¿Mi rey sigue seguro? ¿Ya he enrocado? Si no, ¿por qué no?
4. Si estoy mejor, ¿puedo simplificar en vez de complicar?

**Rey:** enroca antes de la jugada 10 salvo un motivo concreto. Sin enrocar, no muevas el rey al centro ni adelantes los peones g y h. En la Londres, enroque corto por defecto.

**Sesiones:** máximo 3 partidas. Si pierdo 2 seguidas, paro y analizo.

## 6. Aperturas: dónde focalizar el estudio

**Conclusión:** con blancas la apertura rara vez es el problema; con negras en peondeloto, sí. Dedica la mayor parte del tiempo de aperturas (sección 7) a las negras y a unas pocas ramas concretas de las blancas.

**Cómo se ha medido.** Evaluación de Stockfish en la jugada 10, desde tu punto de vista. Hasta +0,5 estás bien; a -1,0 o peor ya juegas una posición difícil antes de salir de la apertura. Esta cifra no la calcula `metricas_pgn.py` (se ha calculado aparte con las mismas partidas).

| Cuenta | Color | Partidas | Mediana en la jugada 10 | Partidas con -1,0 o peor |
|---|---|---|---|---|
| peondeloto | Blancas | 12 | -0,13 | 33 % |
| peondeloto | **Negras** | 12 | **-1,78** | **75 %** |
| dvillaj | Blancas | 376 | +0,21 | 21 % |
| dvillaj | Negras | 375 | -0,12 | 30 % |

En peondeloto jugaste con negras 11 secuencias distintas de las cuatro primeras jugadas en 12 partidas y ninguna fue la Caro-Kann; con blancas, la Londres en 11 de 12. Por eso la diferencia entre colores es tan grande: en dvillaj, donde sí repites repertorio, las negras salen igualadas.

### Negras (prioridad 1)

Idea de conjunto, como propuesta: una sola estructura con peón en c6 y d5 contra todo. Es la que ya dominas con la Caro-Kann y cabe en 15+10 sin memorizar mucho.

| Orden | Qué estudiar | Datos | Por qué |
|---|---|---|---|
| 1 | **Contra 1.d4 d5 2.c4: dejar 2...Bf5 (Baltic)** y elegir otra respuesta, por ejemplo con ...c6 | dvillaj: 25 partidas, 42 % de puntos, evaluación -0,97 en la jugada 10, 8 derrotas cortas (32 %) y 0,96 blunders por partida en la apertura, el máximo de tus líneas con negras | Es tu línea con negras que peor sale de la apertura y es tu única respuesta a 2.c4 (25 de 25 partidas) |
| 2 | **Caro-Kann contra 2.Nf3 d5 3.exd5** | dvillaj: 44 partidas, 39 % de puntos y 16 derrotas cortas (36 %) | Son el 30 % de tus Caro-Kann (68 de 230) y el resultado más bajo de la defensa; con 2.d4 d5 sacas 54 % |
| 3 | **Una sola respuesta contra la Londres (1.d4 d5 2.Bf4)** | dvillaj: 19 partidas, 50 %. peondeloto: 3 partidas, 0 puntos, con 2...Bf5 dos veces (-1,22 en la jugada 10) y 2...g6 una | Es lo que te juegan en 3 de tus 5 partidas con negras contra 1.d4 en peondeloto, y respondes con 2...Bf5 o 2...g6 |
| 4 | **Dejar 1...d5 contra 1.e4 (Escandinava) y 1...e5, y jugar siempre 1...c6** | dvillaj: Escandinava, 23 partidas, 43 % y -1,33 tras 3...Qxd5 4.Nc3 (15 partidas, 40 %); 1...e5, 10 partidas, 45 % y -1,20. peondeloto: 1...d5, 1...g6, 1...b6, 1...e5 y 1...c5 en 5 partidas contra 1.e4 | Quita opciones que te dejan peor y refuerza A7 |

Conservar sin tocar: Caro-Kann contra 2.d4 d5 3.e5 (Avance, 56 partidas, 54 %) y contra 2.Bc4 (28 partidas, 55 %, evaluación +0,62).

### Blancas (prioridad 2)

Mantén la Londres (1.d4 y 2.Bf4). Casi todas las ramas salen bien de la apertura; estas son las que no:

| Orden | Qué estudiar | Datos | Por qué |
|---|---|---|---|
| 1 | **Contra 1...e5 (Gambito Englund)** | dvillaj: 31 partidas, 58 % de puntos pero 1,10 blunders por partida en la apertura y -2,5 de mediana en la jugada 10 tras 3.Nf3. 3.Nf3 Qe7 4.Bf4 Qb4+ pierde el peón b2 y más: 3 partidas, 2 derrotas en 5 y 8 jugadas. 2.Bf4 contra 1...e5: 3 derrotas en 4 partidas; en las dos que siguieron 2...exf4 ya ibas a -6 o -7 hacia la jugada 6 | Ganas el 58 % por la torpeza del rival, no por tu apertura. Contra 1...e5 juega 2.dxe5 y comprueba en el explorador la continuación tras 3.Nf3 Qe7 antes de repetirla |
| 2 | **Contra 1...g6** | dvillaj: 20 partidas, 42 %; con 2.Bf4 (18 partidas) sale 36 % y 0,89 blunders por partida en la apertura; Lichess marca 2.Bf4 como imprecisión en esa línea | Una estructura de piezas distinta de la Londres normal |
| 3 | **Londres contra 1...d5 2.Bf4 Nf6 y 2...c5** | 2...Nf6: 52 partidas, 49 % y 14 derrotas cortas (27 %). 2...c5: 13 partidas, 54 % y -0,60 en la jugada 10. Contra 2...Nc6 tienes 53 %, +0,42 y 7 derrotas cortas de 53 | Son las respuestas con peor evaluación o más derrotas cortas |
| 4 | **Londres contra 1...Nf6 2.Bf4 e6 y 2...d5** | 12 partidas cada una: 33 % y 42 % de puntos, esta última con -0,67 en la jugada 10 | Indicio, con pocas partidas |

Conservar sin tocar: Londres contra 2...Nc6 (53 partidas) y 2...e6 (20 partidas, 52 %), y contra 1...e6 (27 partidas, 61 %).

### Qué no estudiar ahora

Ampliar el repertorio, aprender líneas largas o tocar la Londres contra ...Nc6. El 57 % de tus blunders están en el medio juego (A3) y 5 de tus 10 derrotas cortas fueron sin enrocar (A5): una apertura estudiada hasta la jugada 10 no corrige eso. Si el repertorio sale bien en 20 o 30 partidas, se puede ampliar.

### Cómo estudiar cada línea

- Hasta la jugada 10, con 3 ideas por posición y la trampa en la que has caído: no más.
- Explorador de aperturas de Lichess con la base de Lichess filtrada por tu rango de rating. Un Estudio por línea.
- Tras cada partida perdida, anota en qué jugada saliste de lo que sabías y la evaluación en la jugada 10.

### Cómo comprobar que funciona (propuesta)

Con las mismas partidas, mediana en la jugada 10 de peondeloto con negras de -0,5 o mejor y menos del 40 % de partidas con -1,0 o peor (hoy -1,78 y 75 %). Hace falta repetirlo cada 20-30 partidas; con 12 partidas por color, una sola partida mueve la cifra un 8 %.

**Límites:** dvillaj es 10+0 y de ~1526; sus ramas con menos de 20 partidas son indicios. Las evaluaciones de la jugada 10 mezclan análisis de Lichess y local. Las recomendaciones de líneas concretas (por ejemplo ...c6 contra 2.c4) son propuestas: se deben comprobar en el explorador antes de fijarlas.

## 7. Plan semanal (5-8 h, solo Lichess)

- **Jugar 15+10 (2-3 h):** unas 4 partidas por semana, en sesiones de 2 o 3, con las reglas de arriba.
- **Revisar partidas (1,5-2 h):** analizar todas las partidas, en Lichess o en local, y repasar primero las derrotas cortas con "Aprende de tus errores". En cada una, busca la jugada en que dejaste de estar igualado y si tu rey ya estaba enrocado.
- **Táctica (1,5-2 h):** pocos problemas, resueltos con calma. Temas: pieza colgada, horquilla, clavada, mate en 2 y 3, ataques al rey sin enrocar y jugadas de defensa.
- **Aperturas y finales (0,5-1 h):** seguir el orden de la sección 6 (primero las negras: 2.c4 Bf5, Caro-Kann contra 2.Nf3 y una sola respuesta a la Londres) con el explorador de aperturas; práctica de finales de Lichess y partidas con ventaja contra el ordenador para entrenar la conversión (A4).

## 8. Carpetas y comandos

```
chessia/
  perfil_peondeloto.md        este documento
  metricas_pgn.py             el script de métricas
  prompts/                    versiones del prompt y su changelog
  CONTEXTO_IA.md              contexto del proyecto para un modelo de IA
  partidas/<usuario>/         exportaciones de Lichess (originales, no se tocan)
  partidas_analizadas/<usuario>/   las mismas partidas, analizadas en local o por Lichess
  analisis/                   los PGN enriquecidos que devuelve el prompt
  progreso/                   CSV que genera el script
```

Comando habitual:

```
pipenv run python metricas_pgn.py partidas_analizadas/peondeloto --usuario peondeloto --ritmo 900+10 --base-hasta 2026-11-03 --csv progreso/progreso_peondeloto.csv
```

Si una partida trae `%eval` de Lichess pero no sus etiquetas, el script le cuenta 0 errores. `descargar_lichess.py` ya pide las etiquetas (`literate=true`), y `analizar_local.py` se las añade sin motor a las partidas descargadas antes de ese cambio.

## 9. Registro de progreso (pega aquí la tabla del script cada 20-30 partidas)

| Fecha de corte | Partidas | Mediana s | % tiempo disponible | Blunders por partida | Derrotas cortas | Ventajas tiradas | Notas |
|---|---|---|---|---|---|---|---|
| 2026-11-03 (BASE) | 22 | 3,0 | 15 % | 2,41 | 45 % | 2 de 22 | Línea base, todas analizadas |
| 2026-W45 | 2 | 5,0 | 22 % | 1,50 | 0 % | 0 de 2 | 2 victorias; muestra mínima |

## 10. Historial de versiones

- **v1 (5 nov 2026):** primer diagnóstico con 805 partidas de dvillaj131313 y 21 de peondeloto.
- **v2 (7 nov 2026):** el porcentaje de reloj pasa a medirse sobre el tiempo disponible (base más incrementos). Línea base de peondeloto: 14 % frente a 51 % del rival. En dvillaj no cambia, porque 10+0 no tiene incremento.
- **v3 (9 nov 2026):** todas las partidas analizadas: 24 de peondeloto y 784 de 10+0 de dvillaj131313, con Lichess o en local con Stockfish 19 a profundidad 20. Línea base recalculada con 22 partidas: 2,41 blunders por partida, 15 % del tiempo disponible y 45 % de derrotas cortas. A5 pasa de hipótesis a dato medido y se centra en el enroque y el rey en el centro; se descarta la parte de las capturas de peón con la dama. A2 añade la relación entre tiempo pensado y blunders. A6 añade el rendimiento según el número de partida del día. A7 propone llevar la Caro-Kann a peondeloto. Sesiones de 3 partidas como máximo y regla de enroque. Añade la sección 6, con las aperturas de blancas y negras donde focalizar el estudio, y renumera las secciones 6 a 9 como 7 a 10. En v2 la línea base era de 21 partidas, con 2,50 blunders en 10 analizadas, 14 % del tiempo, 48 % de derrotas cortas y 1 ventaja tirada de 10.
