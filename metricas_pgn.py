#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metricas_pgn.py - Metricas objetivas de tus partidas de Lichess. Sin dependencias.

USO
  python metricas_pgn.py partidas/ --usuario peondeloto --ritmo 900+10 --base-hasta 2026-11-03
  python metricas_pgn.py export1.pgn export2.pgn --usuario peondeloto

  partidas/      carpeta con tus exportaciones .pgn (se leen todas y se eliminan duplicados por GameId)
  --usuario      tu nombre en Lichess (si se omite, se usa el que mas aparece)
  --ritmo        filtra por TimeControl exacto, por ejemplo 900+10
  --base-hasta   las partidas hasta esa fecha (inclusive) forman el grupo BASE;
                 las posteriores se agrupan por semana ISO
  --csv          fichero de salida (por defecto progreso_<usuario>.csv);
                 separador ; y coma decimal, para abrirlo directamente en Excel en espanol

LAS METRICAS DE ERRORES (imprecisiones, errores, blunders) solo existen en partidas
con analisis del ordenador. Pide el analisis en Lichess antes de exportar.

DEFINICIONES
  tiempo por jugada = reloj propio anterior - reloj propio actual + incremento (la 1.a jugada se excluye)
  % reloj usado     = suma del tiempo por jugada / tiempo base de la partida
  jugadas rapidas   = jugadas posteriores a la 10 con tiempo por jugada de 3 s o menos
  fases             = apertura hasta la jugada 10, medio juego de la 11 a la 25, final desde la 26
  derrota corta     = derrota en menos de 25 jugadas
  ventaja tirada    = partida analizada en la que llegaste a +3,0 o mas y no ganaste
"""
import argparse
import csv
import datetime
import glob
import os
import re
import statistics as st
import sys
from collections import Counter

# Objetivos de partida (propuestas ajustables, no referencias externas)
OBJETIVOS = {
    "mediana_s": ("≥", 8.0),
    "uso_reloj_pct": ("≥", 40.0),
    "blunders_partida": ("≤", 1.2),
    "errores_partida": ("≤", 0.8),
    "derrotas_cortas_pct": ("≤", 15.0),
    "ventajas_tiradas_pct": ("≤", 10.0),
    "racha_derrotas": ("≤", 3),
    "max_dia": ("≤", 5),
}

PLY = re.compile(r"(\d+)(\.{1,3})\s*([^\s{}()]+?)\s*((?:\{[^}]*\}\s*)+)")
CLK = re.compile(r"%clk (\d+):(\d+):(\d+(?:\.\d+)?)")
EVAL = re.compile(r"%eval (#?)(-?\d+(?:\.\d+)?)")
JUDGE = re.compile(r"\)\s*(Inaccuracy|Mistake|Blunder)\b")


def leer_partidas(rutas):
    ficheros = []
    for r in rutas:
        if os.path.isdir(r):
            ficheros += sorted(glob.glob(os.path.join(r, "**", "*.pgn"), recursive=True))
        else:
            ficheros.append(r)
    vistos, salida = set(), []
    for f in ficheros:
        with open(f, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
        for g in re.split(r"(?m)^(?=\[Event )", txt):
            if not g.strip():
                continue
            m = re.search(r"\n[ \t]*\n", g)
            if not m:
                continue
            cab = dict(re.findall(r'\[(\w+) "([^"]*)"\]', g[: m.start()]))
            gid = cab.get("GameId") or cab.get("Site", "").rsplit("/", 1)[-1]
            if not gid or gid in vistos:
                continue
            vistos.add(gid)
            salida.append((gid, cab, g[m.end():]))
    return salida


def procesar(gid, cab, mv, usuario):
    if usuario not in (cab.get("White"), cab.get("Black")):
        return None
    col = "W" if cab.get("White") == usuario else "B"
    r = cab.get("Result", "*")
    if r not in ("1-0", "0-1", "1/2-1/2"):
        return None
    res = "D" if r == "1/2-1/2" else ("W" if (r == "1-0") == (col == "W") else "L")
    tc = cab.get("TimeControl", "")
    m = re.fullmatch(r"(\d+)\+(\d+)", tc)
    base, inc = (int(m.group(1)), int(m.group(2))) if m else (None, 0)

    sin_com = re.sub(r"\{[^}]*\}", "", mv)
    nums = re.findall(r"(\d+)\.(?!\.)", re.sub(r"\([^)]*\)", "", sin_com))
    jugadas = int(nums[-1]) if nums else 0

    sig = 1 if col == "W" else -1
    prev = prev_op = None
    thinks, thinks_op = [], []
    n_eval = imp = err = blu = 0
    blu_f = Counter()
    max_v = None
    for num, dots, _san, coms in PLY.findall(mv):
        n = int(num)
        propio = (("W" if dots == "." else "B") == col)
        c = CLK.search(coms)
        if c and base is not None:
            t = int(c.group(1)) * 3600 + int(c.group(2)) * 60 + float(c.group(3))
            if propio:
                if prev is not None and n > 1:
                    thinks.append((n, max(prev - t + inc, 0)))
                prev = t
            else:
                if prev_op is not None and n > 1:
                    thinks_op.append(max(prev_op - t + inc, 0))
                prev_op = t
        e = EVAL.search(coms)
        if e:
            v = float(e.group(2))
            cp = (10000 if v > 0 else -10000 if v < 0 else 0) if e.group(1) else v * 100
            vp = cp * sig
            max_v = vp if max_v is None else max(max_v, vp)
            if propio:
                n_eval += 1
                j = JUDGE.search(coms)
                if j:
                    fase = "ap" if n <= 10 else ("mj" if n <= 25 else "fn")
                    if j.group(1) == "Inaccuracy":
                        imp += 1
                    elif j.group(1) == "Mistake":
                        err += 1
                    else:
                        blu += 1
                        blu_f[fase] += 1

    tv = [t for _, t in thinks]
    despues10 = [t for n, t in thinks if n > 10]
    analizada = n_eval > 0
    return {
        "fecha": cab.get("UTCDate", cab.get("Date", "")).replace(".", "-"),
        "hora": cab.get("UTCTime", ""),
        "id": gid,
        "ritmo": tc,
        "color": col,
        "apertura": cab.get("Opening", ""),
        "resultado": res,
        "elo_propio": cab.get("WhiteElo" if col == "W" else "BlackElo", ""),
        "elo_rival": cab.get("BlackElo" if col == "W" else "WhiteElo", ""),
        "jugadas": jugadas,
        "terminacion": cab.get("Termination", ""),
        "analizada": int(analizada),
        "mediana_s": round(st.median(tv), 1) if tv else None,
        "media_s": round(st.mean(tv), 1) if tv else None,
        "uso_reloj_pct": round(100 * sum(tv) / base, 1) if tv and base else None,
        "uso_reloj_rival_pct": round(100 * sum(thinks_op) / base, 1) if thinks_op and base else None,
        "rapidas_pct": round(100 * sum(1 for t in despues10 if t <= 3) / len(despues10), 1) if despues10 else None,
        "imprecisiones": imp if analizada else None,
        "errores": err if analizada else None,
        "blunders": blu if analizada else None,
        "blunders_apertura": blu_f["ap"] if analizada else None,
        "blunders_medio": blu_f["mj"] if analizada else None,
        "blunders_final": blu_f["fn"] if analizada else None,
        "blunder_pct": round(100 * blu / n_eval, 1) if analizada else None,
        "max_ventaja_cp": int(min(max_v, 1000)) if analizada and max_v is not None else None,
        "ventaja_tirada": (int(max_v >= 300 and res != "W") if analizada and max_v is not None else None),
        "derrota_corta": int(res == "L" and jugadas < 25),
        "_thinks": tv,
    }


def media(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def f(x, dec=1, suf=""):
    return "-" if x is None else f"{x:.{dec}f}".replace(".", ",") + suf


def racha_max(partidas):
    mejor = actual = 0
    for p in partidas:
        actual = actual + 1 if p["resultado"] == "L" else 0
        mejor = max(mejor, actual)
    return mejor


def semana(fecha):
    y, w, _ = datetime.date.fromisoformat(fecha).isocalendar()
    return f"{y}-W{w:02d}"


def resumen(partidas, base_hasta):
    grupos = {}
    for p in partidas:
        clave = "BASE" if base_hasta and p["fecha"] <= base_hasta else semana(p["fecha"])
        grupos.setdefault(clave, []).append(p)
    orden = sorted(grupos, key=lambda k: ("" if k == "BASE" else k))
    cab = ["Periodo", "Partidas", "Puntos %", "Mediana s/jugada", "% reloj usado",
           "Blunders/partida", "Errores/partida", "Analizadas", "Derrotas cortas",
           "Ventajas tiradas", "Racha derrotas", "Máx. partidas/día"]
    filas = []
    for k in orden:
        ps = grupos[k]
        n = len(ps)
        pts = 100 * (sum(p["resultado"] == "W" for p in ps) + 0.5 * sum(p["resultado"] == "D" for p in ps)) / n
        todos = [t for p in ps for t in p["_thinks"]]
        an = [p for p in ps if p["analizada"]]
        cortas = sum(p["derrota_corta"] for p in ps)
        vt = sum(p["ventaja_tirada"] or 0 for p in an)
        filas.append([
            k, str(n), f(pts, 0, " %"),
            f(st.median(todos)) if todos else "-",
            f(media(p["uso_reloj_pct"] for p in ps), 0, " %"),
            f(media(p["blunders"] for p in an), 2), f(media(p["errores"] for p in an), 2),
            str(len(an)), f"{cortas} ({100 * cortas / n:.0f} %)",
            f"{vt} de {len(an)}", str(racha_max(sorted(ps, key=lambda p: (p["fecha"], p["hora"])))),
            str(max(Counter(p["fecha"] for p in ps).values())),
        ])
    o = OBJETIVOS
    filas.append(["OBJETIVO", "", "", f"{o['mediana_s'][0]} {f(o['mediana_s'][1])}",
                  f"{o['uso_reloj_pct'][0]} {f(o['uso_reloj_pct'][1], 0)} %",
                  f"{o['blunders_partida'][0]} {f(o['blunders_partida'][1], 1)}",
                  f"{o['errores_partida'][0]} {f(o['errores_partida'][1], 1)}", "",
                  f"{o['derrotas_cortas_pct'][0]} {f(o['derrotas_cortas_pct'][1], 0)} %",
                  f"{o['ventajas_tiradas_pct'][0]} {f(o['ventajas_tiradas_pct'][1], 0)} %",
                  f"{o['racha_derrotas'][0]} {o['racha_derrotas'][1]}",
                  f"{o['max_dia'][0]} {o['max_dia'][1]}"])
    linea = lambda xs: "| " + " | ".join(xs) + " |"
    return "\n".join([linea(cab), linea(["---"] * len(cab))] + [linea(x) for x in filas])


def main():
    ap = argparse.ArgumentParser(description="Metricas de progreso a partir de PGN de Lichess")
    ap.add_argument("rutas", nargs="+")
    ap.add_argument("--usuario")
    ap.add_argument("--ritmo")
    ap.add_argument("--base-hasta", dest="base_hasta")
    ap.add_argument("--csv")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    crudas = leer_partidas(a.rutas)
    if not crudas:
        sys.exit("No se ha encontrado ninguna partida en las rutas indicadas.")
    usuario = a.usuario
    if not usuario:
        c = Counter(n for _, cab, _ in crudas for n in (cab.get("White"), cab.get("Black")) if n)
        usuario = c.most_common(1)[0][0]
        print(f"Usuario detectado: {usuario}")
    partidas = []
    for gid, cab, mv in crudas:
        if a.ritmo and cab.get("TimeControl") != a.ritmo:
            continue
        p = procesar(gid, cab, mv, usuario)
        if p:
            partidas.append(p)
    if not partidas:
        sys.exit("Ninguna partida cumple los filtros (usuario, ritmo).")
    partidas.sort(key=lambda p: (p["fecha"], p["hora"]))

    columnas = [k for k in partidas[0] if not k.startswith("_")]
    destino = a.csv or f"progreso_{usuario}.csv"
    with open(destino, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(columnas)
        for p in partidas:
            w.writerow(["" if p[c] is None else str(p[c]).replace(".", ",") if isinstance(p[c], float) else p[c]
                        for c in columnas])
    print(f"{len(partidas)} partidas de {usuario} -> {destino}\n")
    print(resumen(partidas, a.base_hasta))


if __name__ == "__main__":
    main()
