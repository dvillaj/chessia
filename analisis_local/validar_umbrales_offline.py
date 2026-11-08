# -*- coding: utf-8 -*-
"""
validar_umbrales_offline.py - Comprueba que nucleo.valorar reproduce las etiquetas de Lichess.

Toma PGN que Lichess ya ha analizado (con %eval y comentarios Inaccuracy, Mistake y Blunder), aplica
nucleo.valorar a las evaluaciones de Lichess y compara con las etiquetas que Lichess puso. NO necesita
motor ni python-chess: valida solo la regla de clasificacion, no el motor.

Solo se usan partidas con [Annotator "lichess.org"]. Asi se ignoran los PGN analizados en local
(analizar_local.py), cuyas etiquetas las genera nucleo.valorar y harian la validacion circular, aunque
tengan el mismo GameId que la partida original.

Uso:  python validar_umbrales_offline.py partidas/peondeloto partidas/dvillaj
"""
import argparse
import collections
import glob
import os
import sys

import nucleo as n

ANOTADOR_LICHESS = "lichess.org"


def leer(rutas):
    ficheros = []
    for r in rutas:
        ficheros += sorted(glob.glob(os.path.join(r, "**", "*.pgn"), recursive=True)) if os.path.isdir(r) else [r]
    partidas = {}
    ignoradas = 0
    for f in ficheros:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for p in n.separar_partidas(fh.read()):
                cab = dict(p["cabeceras"])
                if "%eval" not in p["movimientos"]:
                    continue
                if cab.get("Annotator") != ANOTADOR_LICHESS:
                    ignoradas += 1
                    continue
                # clave que no se pisa: GameId, si no Site, si no fichero + posicion
                clave = cab.get("GameId") or cab.get("Site") or f"{f}#{len(partidas)}"
                partidas[clave] = p
    return partidas, ignoradas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rutas", nargs="+")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    partidas, ignoradas = leer(a.rutas)
    if not partidas:
        sys.exit("No se ha encontrado ninguna partida analizada por Lichess ([Annotator \"lichess.org\"]).")
    etiquetas = ("ok", "Inaccuracy", "Mistake", "Blunder")
    normal = collections.Counter()
    mate = collections.Counter()
    for gid, p in partidas.items():
        js = n.leer_jugadas(p["movimientos"])
        for i in range(1, len(js)):
            antes, despues = js[i - 1]["eval"], js[i]["eval"]
            if antes is None or despues is None:
                continue
            real = js[i]["juicio"]["severidad"] if js[i]["juicio"] else "ok"
            v = n.valorar(antes, despues, "W" if i % 2 == 0 else "B")
            nuestro = v["severidad"] if v else "ok"
            con_mate = antes[0] == "mate" or despues[0] == "mate"
            (mate if con_mate else normal)[(real, nuestro)] += 1

    def informe(titulo, c):
        total = sum(c.values())
        if not total:
            print(f"{titulo}: sin casos")
            return
        bien = sum(v for (r, o), v in c.items() if r == o)
        print(f"\n{titulo}: {total} jugadas, acuerdo {100 * bien / total:.2f} %")
        print("   Lichess \\ calculo   " + "  ".join(f"{e:>10}" for e in etiquetas))
        for r in etiquetas:
            print(f"   {r:<18}  " + "  ".join(f"{c.get((r, o), 0):>10}" for o in etiquetas))

    print(f"Partidas con evaluaciones de Lichess: {len(partidas)}")
    if ignoradas:
        print(f"Partidas con evaluaciones pero no analizadas por Lichess (ignoradas): {ignoradas}")
    informe("Evaluaciones normales", normal)
    informe("Casos con mate (reglas aproximadas)", mate)


if __name__ == "__main__":
    main()