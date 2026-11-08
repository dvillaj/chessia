#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calibrar_con_lichess.py - Compara tu analisis local (Stockfish) con el analisis de Lichess en las mismas partidas.

Toma PGN que Lichess ya ha analizado, vuelve a analizar cada partida en local y compara jugada a jugada:
  - diferencia de evaluacion (en probabilidad de ganar, de 0 a 2),
  - acuerdo en las etiquetas Inaccuracy, Mistake y Blunder (matriz de confusion),
  - blunders por partida segun cada analisis.

Sirve para decidir con datos que profundidad usar y cuanto se parece tu analisis local al de Lichess.
Requiere python-chess y Stockfish (ver README.md, sección 4).

Uso:
  pipenv run python analisis_local/calibrar_con_lichess.py partidas/peondeloto --motor /ruta/a/stockfish --maximo 10
  pipenv run python analisis_local/calibrar_con_lichess.py partidas/peondeloto --profundidad 20 --maximo 10
"""
import argparse
import collections
import statistics as st
import sys
import time

import analizar_local as al
import nucleo as n


def main():
    ap = argparse.ArgumentParser(description="Compara el analisis local con el de Lichess")
    ap.add_argument("entradas", nargs="+", help="PGN analizados por Lichess (ficheros o carpetas)")
    ap.add_argument("--motor")
    ap.add_argument("--profundidad", type=int, default=16)
    ap.add_argument("--nodos", type=int)
    ap.add_argument("--hilos", type=int, default=0)
    ap.add_argument("--hash", type=int, default=256, dest="hash_mb")
    ap.add_argument("--maximo", type=int, default=10, help="numero maximo de partidas a comparar (por defecto 10)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    chess = al.importar_chess()
    ajedrez = al.AjedrezChess(chess)
    motor = al.crear_motor(a, chess)
    etiquetas = ("ok", "Inaccuracy", "Mistake", "Blunder")
    matriz = collections.Counter()
    difs = []
    por_partida = []
    t0 = time.time()
    try:
        print(f"Motor: {motor.descripcion}")
        hechas = 0
        for f in al.ficheros_de(a.entradas, "__sin_salida__"):
            with open(f, encoding="utf-8", errors="replace") as fh:
                partidas = n.separar_partidas(fh.read())
            for p in partidas:
                if "%eval" not in p["movimientos"] or hechas >= a.maximo:
                    continue
                gid = dict(p["cabeceras"]).get("GameId", "?")
                ref = n.leer_jugadas(p["movimientos"])
                loc = [{"san": j["san"], "clk": j["clk"]} for j in ref]
                try:
                    n.analizar_partida(loc, ajedrez, motor)
                except ValueError as e:
                    print(f"X  {gid}: {e}")
                    continue
                m, d = n.comparar_analisis(ref, loc)
                matriz.update(m)
                difs += d
                b_ref = sum(1 for j in ref if j["juicio"] and j["juicio"]["severidad"] == "Blunder")
                b_loc = sum(1 for j in loc if j["juicio"] and j["juicio"]["severidad"] == "Blunder")
                por_partida.append((gid, b_ref, b_loc))
                hechas += 1
                print(f"OK {gid}: {len(ref)} semijugadas | blunders Lichess {b_ref}, local {b_loc}")
    except KeyboardInterrupt:
        print("\nInterrumpido; se muestran los resultados parciales.")
    finally:
        motor.cerrar()

    if not por_partida:
        sys.exit("No se ha comparado ninguna partida (hacen falta PGN con evaluaciones de Lichess).")
    total = sum(matriz.values())
    acuerdo = sum(v for (r, l), v in matriz.items() if r == l)
    print(f"\n=== Resultado: {len(por_partida)} partidas, {total} jugadas, {time.time() - t0:.0f} s ===")
    print(f"Diferencia de evaluacion (probabilidad de ganar, 0 a 2): mediana {st.median(difs):.3f}, "
          f"media {st.mean(difs):.3f}, percentil 90 {sorted(difs)[int(len(difs) * 0.9)]:.3f}")
    print(f"Acuerdo de etiquetas: {100 * acuerdo / total:.1f} %")
    print("\n   Lichess \\ local    " + "  ".join(f"{e:>10}" for e in etiquetas))
    for r in etiquetas:
        print(f"   {r:<16}  " + "  ".join(f"{matriz.get((r, l), 0):>10}" for l in etiquetas))
    sb_ref = sum(x[1] for x in por_partida)
    sb_loc = sum(x[2] for x in por_partida)
    print(f"\nBlunders por partida: Lichess {sb_ref / len(por_partida):.2f}, local {sb_loc / len(por_partida):.2f}")
    print("\nLectura: si el local marca bastantes menos o mas blunders que Lichess, o el acuerdo es bajo, prueba con mas "
          "profundidad (--profundidad) o con un limite de nodos (--nodos) y repite. Una vez elegido el ajuste, "
          "usa SIEMPRE el mismo para todas las partidas que quieras comparar entre si.")


if __name__ == "__main__":
    main()
