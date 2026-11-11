#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_lichess.py - Descarga las partidas de un usuario de Lichess en partidas/<usuario>/, de forma incremental.

Pide a la API de Lichess todas las partidas con relojes, evaluaciones (si la partida esta analizada), apertura,
precision y el resto de cabeceras. Con literate=true, las partidas analizadas traen ademas los comentarios
Inaccuracy, Mistake y Blunder, que necesita metricas_pgn.py para contar errores. La primera vez baja todo el historial; las siguientes solo las partidas
posteriores a la ultima que ya tienes en la carpeta (se deduce de UTCDate/UTCTime de los PGN existentes).
Cada ejecucion crea un fichero nuevo lichess_<usuario>_<AAAA-MM-DD>.pgn, sin tocar los anteriores.

Si existe perfiles/<usuario>.md, al terminar se consulta el rating actual en Lichess y se guarda en su cabecera.

El token se lee de LICHESS_TOKEN (variable de entorno o fichero .env en la raiz del proyecto).

USO
  pipenv run python descargar_lichess.py dvillaj131313
  pipenv run python descargar_lichess.py dvillaj131313 --tipo rapid --tipo classical
  pipenv run python descargar_lichess.py dvillaj131313 --solo-analizadas
  pipenv run python descargar_lichess.py dvillaj131313 --completa          # ignora lo ya descargado
  pipenv run python descargar_lichess.py dvillaj131313 --desde 2026-01-01  # fuerza la fecha de inicio (UTC)

Las partidas se piden en orden cronologico y se guardan segun llegan: si se interrumpe, lo descargado queda
guardado y la siguiente ejecucion continua desde ahi. Las partidas que ya existen (mismo GameId) se omiten.
Una partida descargada sin analisis no se actualiza sola si Lichess la analiza despues: usa --completa en una
carpeta aparte, o analiza en local con analisis_local/analizar_local.py.
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import perfiles

RAIZ = os.path.dirname(os.path.abspath(__file__))
URL = "https://lichess.org/api/games/user/{usuario}"
PARAMS_FIJOS = {
    "tags": "true", "clocks": "true", "evals": "true", "opening": "true",
    "accuracy": "true", "division": "true", "literate": "true", "sort": "dateAsc",
}
ESPERA_LIMITE = 65
MAX_REINTENTOS = 5
RE_CAB = re.compile(r'^\[(\w+) "([^"]*)"\]', re.M)


def leer_token(ruta_env=None):
    token = os.environ.get("LICHESS_TOKEN")
    if token:
        return token.strip()
    ruta_env = ruta_env or os.path.join(RAIZ, ".env")
    if os.path.isfile(ruta_env):
        with open(ruta_env, encoding="utf-8") as fh:
            for linea in fh:
                m = re.match(r"\s*(?:export\s+)?LICHESS_TOKEN\s*=\s*(.*?)\s*$", linea)
                if m:
                    return m.group(1).strip("'\"")
    return None


def marca_tiempo(cabeceras):
    """Milisegundos Unix (UTC) de una partida a partir de UTCDate y UTCTime, o None."""
    fecha, hora = cabeceras.get("UTCDate"), cabeceras.get("UTCTime")
    if not fecha or not hora:
        return None
    try:
        dt = datetime.strptime(f"{fecha} {hora}", "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return int(dt.timestamp() * 1000)


def partidas_en_texto(texto):
    """Divide un PGN en partidas (texto completo de cada una)."""
    return [g for g in re.split(r"(?m)^(?=\[Event )", texto) if g.strip()]


def estado_previo(carpeta):
    """(ids ya descargados, ultima marca de tiempo en ms o None) segun los PGN de la carpeta."""
    ids, ultima = set(), None
    for f in glob.glob(os.path.join(carpeta, "*.pgn")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for g in partidas_en_texto(fh.read()):
                cab = dict(RE_CAB.findall(g))
                if cab.get("GameId"):
                    ids.add(cab["GameId"])
                ts = marca_tiempo(cab)
                if ts is not None and (ultima is None or ts > ultima):
                    ultima = ts
    return ids, ultima


def construir_url(usuario, desde_ms, tipos, solo_analizadas):
    params = dict(PARAMS_FIJOS)
    if desde_ms is not None:
        params["since"] = str(desde_ms)
    if tipos:
        params["perfType"] = ",".join(tipos)
    if solo_analizadas:
        params["analysed"] = "true"
    return URL.format(usuario=urllib.parse.quote(usuario)) + "?" + urllib.parse.urlencode(params)


def lineas_stream(respuesta):
    for linea in respuesta:
        yield linea.decode("utf-8", errors="replace")


def partidas_del_stream(lineas):
    """Genera cada partida completa del stream en cuanto se sabe que ha terminado (aparece la siguiente)."""
    actual = []
    for linea in lineas:
        if linea.startswith("[Event ") and actual:
            yield "".join(actual)
            actual = []
        actual.append(linea)
    if actual and "".join(actual).strip():
        yield "".join(actual)


def partida_completa(texto):
    toks = re.sub(r"\{[^}]*\}", " ", texto.split("\n\n", 1)[-1]).split()
    return bool(toks) and toks[-1] in ("1-0", "0-1", "1/2-1/2", "*")


def abrir(url, token):
    req = urllib.request.Request(url, headers={
        "Accept": "application/x-chess-pgn",
        "Authorization": f"Bearer {token}",
        "User-Agent": "chessia-descargar-lichess",
    })
    return urllib.request.urlopen(req, timeout=120)


def ruta_salida(carpeta, usuario):
    base = os.path.join(carpeta, f"lichess_{usuario}_{datetime.now().strftime('%Y-%m-%d')}")
    ruta, k = base + ".pgn", 2
    while os.path.exists(ruta):
        ruta, k = f"{base}_{k}.pgn", k + 1
    return ruta


def descargar(args, token):
    carpeta = os.path.join(args.salida, args.usuario)
    os.makedirs(carpeta, exist_ok=True)
    ids, ultima = estado_previo(carpeta)
    if args.desde:
        desde = int(datetime.strptime(args.desde, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    elif args.completa:
        desde = None
    else:
        desde = ultima
    if desde is None:
        print(f"Descargando todo el historial de {args.usuario}")
    else:
        print(f"Descargando partidas de {args.usuario} desde {datetime.fromtimestamp(desde / 1000, timezone.utc):%Y-%m-%d %H:%M:%S} UTC")
    print(f"Ya hay {len(ids)} partidas en {carpeta}")

    destino = ruta_salida(carpeta, args.usuario)
    nuevas = omitidas = 0
    fallos = 0
    out = None
    try:
        while True:
            url = construir_url(args.usuario, desde, args.tipo, args.solo_analizadas)
            try:
                with abrir(url, token) as resp:
                    for g in partidas_del_stream(lineas_stream(resp)):
                        cab = dict(RE_CAB.findall(g))
                        gid = cab.get("GameId")
                        ts = marca_tiempo(cab)
                        if not partida_completa(g):
                            continue
                        en_el_borde = ts is not None and ts == desde
                        if ts is not None:
                            desde = ts
                        if gid in ids:
                            if not en_el_borde:
                                omitidas += 1
                            continue
                        if out is None:
                            out = open(destino, "w", encoding="utf-8")
                        out.write(g.rstrip("\n") + "\n\n")
                        out.flush()
                        ids.add(gid)
                        nuevas += 1
                        if nuevas % 50 == 0:
                            print(f"  {nuevas} partidas nuevas (ultima: {cab.get('UTCDate')} {cab.get('UTCTime')})", flush=True)
                break
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    sys.exit("Lichess rechaza el token (401). Revisa LICHESS_TOKEN en .env.")
                if e.code == 404:
                    sys.exit(f"El usuario '{args.usuario}' no existe en Lichess.")
                fallos += 1
                espera = ESPERA_LIMITE if e.code == 429 else 5 * fallos
                if fallos > MAX_REINTENTOS:
                    sys.exit(f"Error HTTP {e.code} repetido; se guardo lo descargado ({nuevas} partidas nuevas).")
                print(f"Error HTTP {e.code}; reintento en {espera} s", flush=True)
                time.sleep(espera)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                fallos += 1
                if fallos > MAX_REINTENTOS:
                    sys.exit(f"Error de red repetido ({e}); se guardo lo descargado ({nuevas} partidas nuevas).")
                print(f"Error de red ({e}); reintento en {5 * fallos} s", flush=True)
                time.sleep(5 * fallos)
    except KeyboardInterrupt:
        print("\nInterrumpido. Lo descargado hasta ahora se ha guardado.")
    finally:
        if out:
            out.close()
    if nuevas:
        print(f"{nuevas} partidas nuevas -> {destino}")
    else:
        print("No hay partidas nuevas.")
    if omitidas:
        print(f"{omitidas} partidas omitidas por estar ya descargadas")
    if perfiles.leer(args.usuario) is not None:
        elo = perfiles.actualizar_elo(args.usuario)
        if elo:
            print(f"Elo actual de {args.usuario}: {elo} (guardado en perfiles/{args.usuario}.md)")


def main():
    ap = argparse.ArgumentParser(description="Descarga de forma incremental las partidas de un usuario de Lichess")
    ap.add_argument("usuario", help="nombre de usuario de Lichess")
    ap.add_argument("--salida", default=os.path.join(RAIZ, "partidas"), help="carpeta base (por defecto partidas/)")
    ap.add_argument("--tipo", action="append", help="perfType a descargar (rapid, blitz, classical...); repetible")
    ap.add_argument("--solo-analizadas", action="store_true", help="solo partidas con analisis de Lichess")
    ap.add_argument("--completa", action="store_true", help="ignora lo ya descargado y baja todo el historial")
    ap.add_argument("--desde", help="fecha de inicio AAAA-MM-DD (UTC); sustituye a la deduccion automatica")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    token = leer_token()
    if not token:
        sys.exit("Falta LICHESS_TOKEN: ponlo en el fichero .env de la raiz (LICHESS_TOKEN=...) o como variable de entorno.")
    descargar(args, token)


if __name__ == "__main__":
    main()
