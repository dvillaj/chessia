#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analizar_local.py - Analiza tus partidas con Stockfish en local y las escribe en formato Lichess.

Lee PGN exportados de Lichess (con relojes), evalua cada posicion con Stockfish y escribe un PGN con
  - [%eval ...] y [%clk ...] en cada jugada,
  - comentarios Inaccuracy, Mistake y Blunder con los mismos umbrales que Lichess,
  - la mejor alternativa como variacion.
El resultado se puede usar tal cual con metricas_pgn.py, verificar_pgn.py y el prompt.

REQUISITOS  python-chess (pip install -r requirements.txt) y un ejecutable de Stockfish.

USO
  python analizar_local.py partidas/peondeloto --motor /ruta/a/stockfish
  python analizar_local.py partidas/peondeloto --profundidad 18 --salida partidas_analizadas
  python analizar_local.py --autotest --motor /ruta/a/stockfish

El motor se busca, por este orden, en --motor, en la variable de entorno STOCKFISH_PATH, en el PATH y en
las rutas habituales. Las partidas que ya traen evaluaciones se copian sin cambios, salvo con --reanalizar.
Se escribe un fichero <nombre>_analizado.pgn por cada PGN de entrada.
"""
import argparse
import glob
import os
import shutil
import sys
import time

import nucleo as n

RUTAS_HABITUALES = [
    "/opt/homebrew/bin/stockfish", "/usr/local/bin/stockfish", "/usr/games/stockfish", "/usr/bin/stockfish",
    r"C:\Program Files\Stockfish\stockfish.exe",
]


class AjedrezChess:
    """Adaptador de python-chess a la interfaz que usa nucleo.analizar_partida."""

    def __init__(self, chess):
        self.chess = chess

    def nuevo(self):
        return self.chess.Board()

    def jugada_desde_san(self, t, san):
        try:
            return t.parse_san(san)
        except ValueError:
            return None

    def san_de(self, t, mv):
        return t.san(mv)

    def empujar(self, t, mv):
        c = t.copy(stack=False)
        c.push(mv)
        return c

    def color(self, t):
        return "W" if t.turn == self.chess.WHITE else "B"

    def es_final(self, t):
        return t.is_game_over()


class MotorUCI:
    """Envoltorio de un motor UCI (Stockfish) con la interfaz que usa nucleo.analizar_partida."""

    def __init__(self, chess, ruta, limite_txt, depth=None, nodes=None, hilos=0, hash_mb=0):
        import chess.engine
        self.chess = chess
        self.motor = chess.engine.SimpleEngine.popen_uci(ruta)
        cfg = {}
        if hilos:
            cfg["Threads"] = hilos
        if hash_mb:
            cfg["Hash"] = hash_mb
        self.motor.configure({k: v for k, v in cfg.items() if k in self.motor.options})
        self.limite = chess.engine.Limit(depth=depth) if nodes is None else chess.engine.Limit(nodes=nodes)
        self.nombre = self.motor.id.get("name", "motor UCI")
        self.descripcion = f"{self.nombre}, {limite_txt}"

    def evaluar(self, t):
        info = self.motor.analyse(t, self.limite, info=self.chess.engine.INFO_SCORE | self.chess.engine.INFO_PV)
        p = info["score"].white()
        ev = ("mate", p.mate()) if p.is_mate() else ("cp", p.score())
        return {"eval": ev, "pv": list(info.get("pv", []))}

    def cerrar(self):
        try:
            self.motor.quit()
        except Exception:
            pass


def importar_chess():
    try:
        import chess
        import chess.engine  # noqa: F401
        return chess
    except ImportError:
        sys.exit("Falta python-chess. Instalalo con:  pip install -r requirements.txt  (dentro de tu entorno virtual)")


def buscar_motor(explicito):
    candidatos = [explicito, os.environ.get("STOCKFISH_PATH"), shutil.which("stockfish")] + RUTAS_HABITUALES
    for c in candidatos:
        if c and os.path.isfile(c):
            return c
    sys.exit("No encuentro Stockfish. Indica la ruta con --motor o con la variable STOCKFISH_PATH. "
             "Consulta README_ENTORNO.md para instalarlo.")


def crear_motor(args, chess):
    ruta = buscar_motor(args.motor)
    limite_txt = f"{args.nodos} nodos" if args.nodos else f"profundidad {args.profundidad}"
    return MotorUCI(chess, ruta, limite_txt, depth=args.profundidad, nodes=args.nodos,
                    hilos=args.hilos, hash_mb=args.hash_mb)


def ficheros_de(entradas, salida):
    salida_abs = os.path.abspath(salida)
    ficheros = []
    for e in entradas:
        ficheros += sorted(glob.glob(os.path.join(e, "**", "*.pgn"), recursive=True)) if os.path.isdir(e) else [e]
    return [f for f in ficheros if not os.path.abspath(f).startswith(salida_abs + os.sep)]


def resumen_juicios(jugadas):
    c = {"W": {}, "B": {}}
    for i, j in enumerate(jugadas):
        if j.get("juicio"):
            lado = c["W" if i % 2 == 0 else "B"]
            lado[j["juicio"]["severidad"]] = lado.get(j["juicio"]["severidad"], 0) + 1
    f = lambda d: f"{d.get('Blunder', 0)} blunders, {d.get('Mistake', 0)} errores, {d.get('Inaccuracy', 0)} imprecisiones"
    return f"blancas {f(c['W'])}; negras {f(c['B'])}"


def analizar_texto_partida(p, ajedrez, motor):
    jugadas = n.leer_jugadas(p["movimientos"])
    n.analizar_partida(jugadas, ajedrez, motor)
    cab = [(k, v) for k, v in p["cabeceras"] if k != "Annotator"] + [("Annotator", f"analizar_local.py con {motor.descripcion}")]
    return n.escribir_partida(cab, jugadas, p["resultado"]), jugadas


def procesar(args, chess):
    ajedrez = AjedrezChess(chess)
    ficheros = ficheros_de(args.entradas, args.salida)
    if not ficheros:
        sys.exit("No se ha encontrado ningun PGN en las rutas indicadas.")
    os.makedirs(args.salida, exist_ok=True)
    motor = crear_motor(args, chess)
    print(f"Motor: {motor.descripcion}")
    total = analizadas = 0
    t_ini = time.time()
    try:
        for f in ficheros:
            with open(f, encoding="utf-8", errors="replace") as fh:
                partidas = n.separar_partidas(fh.read())
            destino = os.path.join(args.salida, os.path.splitext(os.path.basename(f))[0] + "_analizado.pgn")
            salida = []
            try:
                for p in partidas:
                    cab = dict(p["cabeceras"])
                    gid = cab.get("GameId", "?")
                    total += 1
                    if cab.get("Variant", "Standard") != "Standard":
                        print(f"-  {gid}: variante {cab['Variant']}, se copia sin analizar")
                        salida.append(p["texto"])
                        continue
                    if "%eval" in p["movimientos"] and not args.reanalizar:
                        print(f"=  {gid}: ya trae analisis, se copia sin cambios (usa --reanalizar para rehacerlo)")
                        salida.append(p["texto"])
                        continue
                    if args.maximo and analizadas >= args.maximo:
                        salida.append(p["texto"])
                        continue
                    t0 = time.time()
                    try:
                        texto, js = analizar_texto_partida(p, ajedrez, motor)
                    except ValueError as e:
                        print(f"X  {gid}: {e}; se copia sin analizar")
                        salida.append(p["texto"])
                        continue
                    analizadas += 1
                    salida.append(texto)
                    print(f"OK {gid}: {len(js)} semijugadas en {time.time() - t0:.0f} s | {resumen_juicios(js)}")
            finally:
                with open(destino, "w", encoding="utf-8") as out:
                    out.write("".join(s if s.endswith("\n\n") else s.rstrip("\n") + "\n\n" for s in salida))
                print(f"-> {destino}")
    except KeyboardInterrupt:
        print("\nInterrumpido. Lo analizado hasta ahora se ha guardado.")
    finally:
        motor.cerrar()
    print(f"\n{analizadas} partidas analizadas de {total} en {time.time() - t_ini:.0f} s")


def autotest(args, chess):
    """Analiza una partida corta con mate del pastor y comprueba que todo funciona."""
    ajedrez = AjedrezChess(chess)
    motor = crear_motor(args, chess)
    try:
        print(f"Motor: {motor.descripcion}")
        sans = ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7#"]
        js = [{"san": s, "clk": None} for s in sans]
        t0 = time.time()
        n.analizar_partida(js, ajedrez, motor)
        print(f"Analizada en {time.time() - t0:.1f} s")
        fallos = []
        if js[-1]["eval"] is not None:
            fallos.append("la jugada final (mate) no deberia llevar evaluacion")
        if any(j["eval"] is None for j in js[:-1]):
            fallos.append("faltan evaluaciones en jugadas intermedias")
        j5 = js[5]["juicio"]
        if not j5 or j5["frase"] != n.FRASE_MATE_RECIBIDO:
            fallos.append("3...Nf6 deberia marcarse como 'Checkmate is now unavoidable'")
        texto = n.escribir_partida([("Event", "autotest"), ("Result", "1-0")], js, "1-0")
        js2 = n.leer_jugadas(n.separar_partidas(texto)[0]["movimientos"])
        if [j["san"] for j in js2] != sans or [j["eval"] for j in js2] != [j["eval"] for j in js]:
            fallos.append("la escritura y lectura del PGN no coinciden")
        for i, j in enumerate(js):
            print(f"  {n.escribir_jugada(i, j)}")
        if fallos:
            print("\nAUTOTEST FALLO:")
            for f in fallos:
                print("  -", f)
            sys.exit(1)
        print("\nAUTOTEST OK")
    finally:
        motor.cerrar()


def main():
    ap = argparse.ArgumentParser(description="Analiza PGN con Stockfish en local y escribe PGN en formato Lichess")
    ap.add_argument("entradas", nargs="*", help="ficheros o carpetas con PGN")
    ap.add_argument("--salida", default="partidas_analizadas", help="carpeta de salida")
    ap.add_argument("--motor", help="ruta del ejecutable de Stockfish")
    ap.add_argument("--profundidad", type=int, default=16, help="profundidad de analisis (por defecto 16)")
    ap.add_argument("--nodos", type=int, help="limite de nodos por posicion; sustituye a la profundidad")
    ap.add_argument("--hilos", type=int, default=0, help="hilos del motor (0 = valor por defecto del motor)")
    ap.add_argument("--hash", type=int, default=256, dest="hash_mb", help="memoria hash en MB (por defecto 256)")
    ap.add_argument("--reanalizar", action="store_true", help="rehace tambien las partidas que ya traen evaluaciones")
    ap.add_argument("--maximo", type=int, default=0, help="analiza como maximo N partidas (util para probar)")
    ap.add_argument("--autotest", action="store_true", help="comprueba la instalacion con una partida corta")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    chess = importar_chess()
    if args.autotest:
        autotest(args, chess)
    elif args.entradas:
        procesar(args, chess)
    else:
        ap.error("indica ficheros o carpetas de PGN, o usa --autotest")


if __name__ == "__main__":
    main()
