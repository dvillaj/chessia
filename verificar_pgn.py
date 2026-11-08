#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_pgn.py - Comprueba que un PGN enriquecido esta COMPLETO y bien formado respecto al original.
No necesita instalar nada. No depende del modelo que genero el PGN.

USO
  python verificar_pgn.py --originales partidas/peondeloto --enriquecidos analisis
  python verificar_pgn.py --originales lichess_peondeloto_2026-11-05.pgn --enriquecidos analisis/2026-11-04_blancas_vs_worsemd_AhkTMz6R.pgn

  Las partidas se emparejan por GameId. Si una partida original no tiene su version enriquecida, se avisa.
  Devuelve codigo de salida 1 si algun PGN tiene errores.

QUE COMPRUEBA
  Completitud   la linea principal tiene las mismas semijugadas, en el mismo orden y con la misma ultima
                jugada que el original; el resultado final coincide.
  Cabeceras     todas las cabeceras del original estan presentes y sin cambios.
  Relojes       la secuencia de relojes de cada jugada coincide con la original.
  Sintaxis      llaves y parentesis balanceados; sin corchetes, parentesis, barras ni signos invertidos en el
                texto libre de los comentarios (salvo las etiquetas autorizadas y las cadenas FEN).
  Estructura    comentario inicial con el briefing y comentario final con el debriefing; limites de palabras;
                variaciones con numero de jugada y maximo 3 semijugadas.

QUE NO COMPRUEBA
  La legalidad de las jugadas de las variaciones ni de las FEN (hace falta un motor de reglas como python-chess).
"""
import argparse
import glob
import os
import re
import sys

LIMITE_BRIEFING = 250      # palabras
LIMITE_DEBRIEFING = 450    # palabras, sin contar las FEN
RESULTADOS = {"1-0", "0-1", "1/2-1/2", "*"}
FEN = re.compile(r"[1-8pnbrqkPNBRQK]+(?:/[1-8pnbrqkPNBRQK]+){7} [wb] (?:-|[KQkq]+) (?:-|[a-h][36]) \d+ \d+")


def leer_partidas(rutas):
    ficheros = []
    for r in rutas:
        if os.path.isdir(r):
            ficheros += sorted(glob.glob(os.path.join(r, "**", "*.pgn"), recursive=True))
        else:
            ficheros.append(r)
    partidas = {}
    for f in ficheros:
        with open(f, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
        for g in re.split(r"(?m)^(?=\[Event )", txt):
            if not g.strip():
                continue
            m = re.search(r"\n[ \t]*\n", g)
            cab_txt, mv = (g[: m.start()], g[m.end():]) if m else (g, "")
            cab = dict(re.findall(r'\[(\w+) "([^"]*)"\]', cab_txt))
            gid = cab.get("GameId") or cab.get("Site", "").rsplit("/", 1)[-1] or f"sin_id_{os.path.basename(f)}"
            partidas[gid] = (f, cab, mv)
    return partidas


def comentarios(mv):
    return re.findall(r"\{([^}]*)\}", mv)


def jugadas_principales(mv):
    """Lista de SAN de la linea principal, sin comentarios, variaciones, NAGs ni numeros."""
    t = re.sub(r"\{[^}]*\}", " ", mv)
    t = re.sub(r"\([^)]*\)", " ", t)
    sans = []
    for tok in t.split():
        if tok in RESULTADOS or tok.startswith("$"):
            continue
        tok = re.sub(r"^\d+\.+", "", tok)
        tok = tok.rstrip("?!")
        if tok:
            sans.append(tok)
    return sans


def resultado_final(mv):
    t = re.sub(r"\{[^}]*\}", " ", mv).split()
    return t[-1] if t and t[-1] in RESULTADOS else None


def relojes(mv):
    return re.findall(r"%clk (\d+:\d\d:\d\d(?:\.\d+)?)", mv)


def verificar(gid, orig, enr):
    errores, avisos = [], []
    f_o, cab_o, mv_o = orig
    f_e, cab_e, mv_e = enr

    # --- completitud ---
    so, se = jugadas_principales(mv_o), jugadas_principales(mv_e)
    if so != se:
        n = min(len(so), len(se))
        dif = next((i for i in range(n) if so[i] != se[i]), None)
        if dif is not None:
            errores.append(f"la linea principal difiere en la semijugada {dif + 1}: original {so[dif]} y enriquecido {se[dif]}")
        if len(se) < len(so):
            errores.append(f"FALTAN JUGADAS: el enriquecido tiene {len(se)} semijugadas y el original {len(so)}; "
                           f"la ultima del enriquecido es {se[-1] if se else 'ninguna'} y la del original {so[-1]}")
        elif len(se) > len(so):
            errores.append(f"SOBRAN JUGADAS: el enriquecido tiene {len(se)} semijugadas y el original {len(so)}")
    ro, re_ = resultado_final(mv_o), resultado_final(mv_e)
    if ro != re_:
        errores.append(f"el resultado final no coincide: original {ro} y enriquecido {re_}")

    # --- cabeceras ---
    faltan = [k for k in cab_o if k not in cab_e]
    cambian = [k for k in cab_o if k in cab_e and cab_o[k] != cab_e[k]]
    if faltan:
        errores.append("faltan cabeceras: " + ", ".join(faltan))
    if cambian:
        errores.append("cabeceras modificadas: " + ", ".join(cambian))

    # --- relojes ---
    if relojes(mv_o) != relojes(mv_e):
        errores.append(f"la secuencia de relojes no coincide: original {len(relojes(mv_o))} valores y enriquecido {len(relojes(mv_e))}")

    # --- sintaxis ---
    if mv_e.count("{") != mv_e.count("}"):
        errores.append("llaves desbalanceadas")
    if mv_e.count("(") != mv_e.count(")"):
        errores.append("parentesis desbalanceados")
    coms = comentarios(mv_e)
    for c in coms:
        t = re.sub(r"\[%clk \d+:\d\d:\d\d(?:\.\d+)?\]", "", c).replace("[MOMENTO CLAVE ★]", "")
        t = FEN.sub("", t)
        malos = sorted({ch for ch in "[]()/¿¡" if ch in t})
        if malos:
            errores.append(f"caracteres prohibidos {malos} en el comentario que empieza por: {t.strip()[:50]!r}")
            break
    sin = re.sub(r"\{[^}]*\}", " ", mv_e)
    if "/" in sin.replace("1/2-1/2", ""):
        errores.append("hay una barra fuera de los comentarios")

    # --- estructura ---
    texto_coms = [c for c in coms if "%clk" not in c or len(c.split()) > 5]
    if not coms or "=== BRIEFING INICIAL Y DIAGNÓSTICO ===" not in coms[0]:
        errores.append("el primer comentario no es el briefing inicial")
    else:
        pal = len(coms[0].split())
        if pal > LIMITE_BRIEFING:
            errores.append(f"el briefing tiene {pal} palabras (maximo {LIMITE_BRIEFING})")
        if not re.match(r"\s*(Blancas|Negras) vs \S+ — .+", coms[0]):
            errores.append("la primera linea del briefing no tiene el formato 'Color vs Rival — resumen'")
    if not coms or "=== DEBRIEFING Y REGLAS DE ORO ===" not in coms[-1]:
        errores.append("el ultimo comentario no es el debriefing final")
    else:
        pal = len(FEN.sub("", coms[-1]).split())
        if pal > LIMITE_DEBRIEFING:
            errores.append(f"el debriefing tiene {pal} palabras sin contar las FEN (maximo {LIMITE_DEBRIEFING})")
        nfen = len(FEN.findall(coms[-1]))
        if not 2 <= nfen <= 3:
            avisos.append(f"el debriefing incluye {nfen} FEN (se esperan 2 o 3)")
    if not re.match(r"\s*\{[^}]*\}\s*\n1\. ", mv_e.lstrip() if mv_e.lstrip().startswith("{") else "x"):
        avisos.append("el briefing no esta pegado a la primera jugada (revisa que no haya linea en blanco)")
    for m in re.finditer(r"\(([^)]*)\)", sin):
        v = m.group(1).split()
        if not v or not re.fullmatch(r"\d+\.(?:\.\.)?", v[0]):
            errores.append(f"una variacion no empieza por su numero de jugada: {' '.join(v[:3])}")
            continue
        n = len([t for t in v if not re.fullmatch(r"\d+\.+", t)])
        if n > 3:
            errores.append(f"una variacion tiene {n} semijugadas (maximo 3): {' '.join(v[:4])}...")
    return errores, avisos, len(so), len(se)


def main():
    ap = argparse.ArgumentParser(description="Verifica que los PGN enriquecidos estan completos respecto a los originales")
    ap.add_argument("--originales", nargs="+", required=True)
    ap.add_argument("--enriquecidos", nargs="+", required=True)
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    orig, enr = leer_partidas(a.originales), leer_partidas(a.enriquecidos)
    if not enr:
        sys.exit("No se ha encontrado ningun PGN enriquecido.")
    mal = 0
    for gid, e in sorted(enr.items()):
        if gid not in orig:
            print(f"?  {gid}: no hay original con ese GameId ({os.path.basename(e[0])})")
            mal += 1
            continue
        errs, avs, no, ne = verificar(gid, orig[gid], e)
        nombre = os.path.basename(e[0])
        if errs:
            mal += 1
            print(f"X  {gid} ({nombre}): {len(errs)} error(es)")
            for x in errs:
                print(f"     - {x}")
        else:
            print(f"OK {gid} ({nombre}): completa, {ne} de {no} semijugadas, resultado {resultado_final(e[2])}")
        for x in avs:
            print(f"     aviso: {x}")
    for gid in sorted(set(orig) - set(enr)):
        print(f"-  {gid}: hay original pero no PGN enriquecido")
    sys.exit(1 if mal else 0)


if __name__ == "__main__":
    main()
