#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
perfiles.py - Lee y actualiza los perfiles de usuario de perfiles/<usuario>.md.

Cada perfil empieza con una cabecera entre dos lineas "---" con datos fijos, una clave por linea:

  ---
  usuario: dvillaj131313
  ritmo: 600+0
  elo: 1593
  elo_fecha: 2026-11-11
  objetivo: 1850
  base_hasta: 2026-11-07
  ---

El resto del fichero es el diagnostico (areas de mejora, fuertes, linea base...). El prompt de analisis y los
scripts leen la cabecera; el diagnostico lo lee el modelo cuando se adjunta el perfil.

USO
  pipenv run python perfiles.py nuevo <usuario> --ritmo 600+0 --objetivo 1850
  pipenv run python perfiles.py elo <usuario>        # consulta el rating en Lichess y lo guarda en el perfil

perfiles/ esta en .gitignore (datos personales); solo se versiona perfiles/_plantilla.md.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date

RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(RAIZ, "perfiles")
PLANTILLA = os.path.join(CARPETA, "_plantilla.md")
CLAVES = ("usuario", "ritmo", "elo", "elo_fecha", "objetivo", "base_hasta")
RE_USUARIO = re.compile(r"^[A-Za-z0-9_-]{2,30}$")
RE_RITMO = re.compile(r"^\d+\+\d+$")
URL_USUARIO = "https://lichess.org/api/user/{usuario}"


def ruta_perfil(usuario, carpeta=CARPETA):
    if not RE_USUARIO.match(usuario or ""):
        raise ValueError(f"Nombre de usuario no valido: {usuario!r}")
    return os.path.join(carpeta, f"{usuario}.md")


def separar(texto):
    """Devuelve (cabecera: dict, cuerpo: str). Sin cabecera, ({}, texto)."""
    texto = texto.lstrip("﻿")
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", texto, re.S)
    if not m:
        return {}, texto
    cab = {}
    for linea in m.group(1).splitlines():
        if ":" in linea and not linea.lstrip().startswith("#"):
            k, v = linea.split(":", 1)
            cab[k.strip()] = v.strip()
    return cab, texto[m.end():]


def componer(cab, cuerpo):
    claves = [k for k in CLAVES if k in cab] + [k for k in cab if k not in CLAVES]
    lineas = [f"{k}: {cab[k]}" for k in claves]
    return "---\n" + "\n".join(lineas) + "\n---\n" + cuerpo


def leer(usuario, carpeta=CARPETA):
    """Cabecera del perfil del usuario, o None si no existe el fichero."""
    ruta = ruta_perfil(usuario, carpeta)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as fh:
        return separar(fh.read())[0]


def leer_ruta(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return separar(fh.read())[0]


def guardar_cabecera(ruta, cambios):
    with open(ruta, encoding="utf-8") as fh:
        cab, cuerpo = separar(fh.read())
    cab.update({k: str(v) for k, v in cambios.items()})
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        fh.write(componer(cab, cuerpo))


def tipo_de_ritmo(ritmo):
    """perfType de Lichess para un ritmo 'base+incremento' (segundos), con su regla de tiempo estimado."""
    if not RE_RITMO.match(ritmo or ""):
        raise ValueError(f"Ritmo no valido: {ritmo!r} (formato base+incremento en segundos, por ejemplo 600+0)")
    base, inc = (int(x) for x in ritmo.split("+"))
    t = base + 40 * inc
    if t < 30:
        return "ultraBullet"
    if t < 180:
        return "bullet"
    if t < 480:
        return "blitz"
    if t < 1500:
        return "rapid"
    return "classical"


def rating_de_respuesta(datos, tipo):
    """Rating entero del perfType en el JSON de /api/user, o None si no hay."""
    p = (datos.get("perfs") or {}).get(tipo) or {}
    r = p.get("rating")
    return int(round(r)) if isinstance(r, (int, float)) else None


def consultar_elo(usuario, ritmo, abrir=urllib.request.urlopen):
    url = URL_USUARIO.format(usuario=usuario)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "chessia"})
    with abrir(req, timeout=30) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
    return rating_de_respuesta(datos, tipo_de_ritmo(ritmo))


def actualizar_elo(usuario, carpeta=CARPETA, abrir=urllib.request.urlopen):
    """Guarda el rating actual en el perfil. Devuelve el rating, o None si no se pudo (sin lanzar)."""
    ruta = ruta_perfil(usuario, carpeta)
    if not os.path.exists(ruta):
        return None
    cab = leer_ruta(ruta)
    if not cab.get("ritmo"):
        print(f"El perfil de {usuario} no tiene 'ritmo' en la cabecera; no se actualiza el Elo.")
        return None
    try:
        elo = consultar_elo(usuario, cab["ritmo"], abrir)
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, json.JSONDecodeError) as e:
        print(f"No se pudo consultar el Elo en Lichess ({e}); el perfil queda como estaba.")
        return None
    if elo is None:
        print(f"Lichess no devuelve rating de {tipo_de_ritmo(cab['ritmo'])} para {usuario}; el perfil queda como estaba.")
        return None
    guardar_cabecera(ruta, {"elo": elo, "elo_fecha": date.today().isoformat()})
    return elo


def crear(usuario, ritmo, objetivo, carpeta=CARPETA, plantilla=PLANTILLA):
    ruta = ruta_perfil(usuario, carpeta)
    if os.path.exists(ruta):
        raise FileExistsError(f"Ya existe {ruta}")
    tipo_de_ritmo(ritmo)  # valida
    if not str(objetivo).isdigit():
        raise ValueError(f"Objetivo no valido: {objetivo!r} (un numero, por ejemplo 1850)")
    with open(plantilla, encoding="utf-8") as fh:
        _, cuerpo = separar(fh.read())
    cuerpo = cuerpo.replace("{usuario}", usuario).replace("{ritmo}", ritmo).replace("{objetivo}", str(objetivo))
    os.makedirs(carpeta, exist_ok=True)
    cab = {"usuario": usuario, "ritmo": ritmo, "objetivo": objetivo}
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        fh.write(componer(cab, cuerpo))
    return ruta


def main():
    ap = argparse.ArgumentParser(description="Gestiona los perfiles de usuario (perfiles/<usuario>.md)")
    sub = ap.add_subparsers(dest="orden", required=True)
    n = sub.add_parser("nuevo", help="crea un perfil desde la plantilla")
    n.add_argument("usuario")
    n.add_argument("--ritmo", required=True, help="TimeControl de Lichess, por ejemplo 600+0 o 900+10")
    n.add_argument("--objetivo", required=True, help="rating objetivo, por ejemplo 1850")
    e = sub.add_parser("elo", help="consulta el rating en Lichess y lo guarda en el perfil")
    e.add_argument("usuario")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if a.orden == "nuevo":
            ruta = crear(a.usuario, a.ritmo, a.objetivo)
            print(f"Perfil creado: {ruta}")
            elo = actualizar_elo(a.usuario)
            if elo:
                print(f"Elo actual en Lichess: {elo}")
            print("Siguiente paso: descarga las partidas, calcula la linea base y completa el perfil con prompts/prompt_crear_perfil_v0.txt.")
        else:
            elo = actualizar_elo(a.usuario)
            if elo is None:
                sys.exit(1)
            print(f"Elo de {a.usuario}: {elo}")
    except (ValueError, FileExistsError, FileNotFoundError) as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
