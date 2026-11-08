# Base de aperturas

Copia de los ficheros `a.tsv` a `e.tsv` de https://github.com/lichess-org/chess-openings
(licencia CC0, dominio público), la misma base que usa Lichess para nombrar las aperturas.

- Origen: rama `master`, último commit `3ba6b20` (5 nov 2026).
- Columnas: `eco`, `name` (con la forma `Familia: Variante, Subvariante`) y `pgn` (la línea de jugadas).
- No hay que editar estos ficheros a mano.

Para actualizarlos, vuelve a descargar los cinco ficheros y anota aquí el nuevo commit:

```
for f in a b c d e; do curl -fsSL "https://raw.githubusercontent.com/lichess-org/chess-openings/master/$f.tsv" -o analisis_local/base_aperturas/$f.tsv; done
```
