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

--procesos N analiza N partidas a la vez, cada una con su propio Stockfish. Cada proceso usa --hilos
(por defecto 1) y --hash MB de memoria, asi que el consumo de memoria es N veces el de un proceso.
El resultado no depende de N: cada partida se analiza igual con un proceso que con varios.

Uso:
  pipenv run python analisis_local/calibrar_con_lichess.py partidas/dvillaj131313 [--motor /ruta/a/stockfish] --maximo 10
  pipenv run python analisis_local/calibrar_con_lichess.py partidas/dvillaj131313 --maximo 10 --procesos 4
"""
import argparse
import collections
import multiprocessing.util
import statistics as st
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import analizar_local as al
import nucleo as n

_motor = None
_ajedrez = None


def _iniciar_proceso(args):
    global _motor, _ajedrez
    chess = al.importar_chess()
    _ajedrez = al.AjedrezChess(chess)
    _motor = al.crear_motor(args, chess)
    multiprocessing.util.Finalize(None, _motor.cerrar, exitpriority=10)


def _comparar_partida(p):
    """Reanaliza una partida en este proceso. Devuelve (id, descripcion del motor, resultado o None, error o None)."""
    gid = dict(p["cabeceras"]).get("GameId", "?")
    ref = n.leer_jugadas(p["movimientos"])
    loc = [{"san": j["san"], "clk": j["clk"]} for j in ref]
    _motor.nueva_partida()
    try:
        n.analizar_partida(loc, _ajedrez, _motor)
    except ValueError as e:
        return gid, _motor.descripcion, None, str(e)
    m, d = n.comparar_analisis(ref, loc)
    b_ref = sum(1 for j in ref if j["juicio"] and j["juicio"]["severidad"] == "Blunder")
    b_loc = sum(1 for j in loc if j["juicio"] and j["juicio"]["severidad"] == "Blunder")
    return gid, _motor.descripcion, (len(ref), m, d, b_ref, b_loc), None


def seleccionar_partidas(entradas, maximo):
    """Las primeras 'maximo' partidas con evaluaciones, en el orden de los ficheros."""
    elegidas = []
    for f in al.ficheros_de(entradas, "__sin_salida__"):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for p in n.separar_partidas(fh.read()):
                if "%eval" in p["movimientos"] and len(elegidas) < maximo:
                    elegidas.append(p)
    return elegidas


def main():
    ap = argparse.ArgumentParser(description="Compara el analisis local con el de Lichess")
    ap.add_argument("entradas", nargs="+", help="PGN analizados por Lichess (ficheros o carpetas)")
    ap.add_argument("--motor")
    ap.add_argument("--profundidad", type=int, default=al.PROFUNDIDAD_POR_DEFECTO)
    ap.add_argument("--tiempo", type=float, help="segundos por posicion; sustituye a la profundidad")
    ap.add_argument("--nodos", type=int, help="limite de nodos por posicion; sustituye a la profundidad y al tiempo")
    ap.add_argument("--hilos", type=int, default=0, help="hilos de cada motor (0 = valor por defecto, 1)")
    ap.add_argument("--hash", type=int, default=256, dest="hash_mb", help="memoria hash en MB por proceso")
    ap.add_argument("--procesos", type=int, default=1, help="partidas analizadas a la vez (por defecto 1)")
    ap.add_argument("--maximo", type=int, default=10, help="numero maximo de partidas a comparar (por defecto 10)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    al.buscar_motor(a.motor)
    partidas = seleccionar_partidas(a.entradas, a.maximo)
    if not partidas:
        sys.exit("No se ha comparado ninguna partida (hacen falta PGN con evaluaciones de Lichess).")
    procesos = max(1, min(a.procesos, len(partidas)))

    etiquetas = ("ok", "Inaccuracy", "Mistake", "Blunder")
    matriz = collections.Counter()
    difs = []
    por_partida = []
    t0 = time.time()
    descripcion_mostrada = False
    with ProcessPoolExecutor(max_workers=procesos, initializer=_iniciar_proceso, initargs=(a,)) as ex:
        try:
            for gid, descripcion, res, error in ex.map(_comparar_partida, partidas):
                if not descripcion_mostrada:
                    print(f"Motor: {descripcion} | {procesos} proceso(s)")
                    descripcion_mostrada = True
                if error:
                    print(f"X  {gid}: {error}")
                    continue
                semijugadas, m, d, b_ref, b_loc = res
                matriz.update(m)
                difs += d
                por_partida.append((gid, b_ref, b_loc))
                print(f"OK {gid}: {semijugadas} semijugadas | blunders Lichess {b_ref}, local {b_loc}", flush=True)
        except KeyboardInterrupt:
            print("\nInterrumpido; se muestran los resultados parciales.")
            ex.shutdown(wait=False, cancel_futures=True)

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
