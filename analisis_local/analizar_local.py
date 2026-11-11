#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analizar_local.py - Analiza tus partidas con Stockfish en local y las escribe en formato Lichess.

Lee PGN exportados de Lichess (con relojes), evalua cada posicion con Stockfish y escribe un PGN con
  - [%eval ...] y [%clk ...] en cada jugada,
  - comentarios Inaccuracy, Mistake y Blunder con los mismos umbrales que Lichess,
  - la mejor alternativa como variacion,
  - las cabeceras ECO y Opening, si la partida no las trae (base de aperturas de Lichess, ver aperturas.py).
El resultado se puede usar tal cual con metricas_pgn.py, verificar_pgn.py y el prompt.

REQUISITOS  python-chess (pipenv install desde la raíz) y un ejecutable de Stockfish.

USO
  pipenv run python analisis_local/analizar_local.py partidas/dvillaj131313 --motor /ruta/a/stockfish
  pipenv run python analisis_local/analizar_local.py partidas/dvillaj131313 --profundidad 22 --salida partidas_analizadas
  pipenv run python analisis_local/analizar_local.py partidas/dvillaj131313 --tiempo 2 --hilos 4
  pipenv run python analisis_local/analizar_local.py partidas/dvillaj131313 --nodos 2000000
  pipenv run python analisis_local/analizar_local.py partidas/dvillaj131313 --procesos 6
  pipenv run python analisis_local/analizar_local.py --autotest --motor /ruta/a/stockfish

LIMITE DE ANALISIS (por posicion). Si se dan varios, manda este orden: --nodos, --tiempo, --profundidad.
Por defecto: profundidad 20. A profundidad 16 las evaluaciones son mas ruidosas y a veces no se ve un mate
largo, lo que provoca diferencias con el analisis de Lichess.

El motor se busca, por este orden, en --motor, en la variable de entorno STOCKFISH_PATH, en el PATH y en
las rutas habituales. Las partidas que ya traen evaluaciones se copian sin cambios, salvo con --reanalizar.
Si traen %eval pero no los comentarios Inaccuracy, Mistake y Blunder (exportadas con literate=false), se
anaden esos comentarios a partir de sus propias evaluaciones, con la misma regla y sin usar el motor.
Se escribe un fichero <salida>/<carpeta del PGN>/<nombre>_analizado.pgn por cada PGN de entrada, partida a partida y en el orden original:
si se interrumpe, queda guardado todo lo hecho hasta ese momento.

--procesos N analiza N partidas a la vez, cada una con su propio Stockfish (--hilos, por defecto 1, y --hash MB
por proceso, asi que la memoria es N veces la de un proceso). El resultado de cada partida no depende de N.
"""
import argparse
import glob
import multiprocessing.util
import os
import re
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, wait

import aperturas
import nucleo as n

RUTAS_HABITUALES = [
    "/opt/homebrew/bin/stockfish", "/usr/local/bin/stockfish", "/usr/games/stockfish", "/usr/bin/stockfish",
    r"C:\Program Files\Stockfish\stockfish.exe",
]

PROFUNDIDAD_POR_DEFECTO = 20


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

    def __init__(self, chess, ruta, limite_txt, depth=None, nodes=None, tiempo=None, hilos=0, hash_mb=0):
        import chess.engine
        self.chess = chess
        self.motor = chess.engine.SimpleEngine.popen_uci(ruta)
        cfg = {}
        if hilos:
            cfg["Threads"] = hilos
        if hash_mb:
            cfg["Hash"] = hash_mb
        self.motor.configure({k: v for k, v in cfg.items() if k in self.motor.options})
        if nodes:
            self.limite = chess.engine.Limit(nodes=nodes)
        elif tiempo:
            self.limite = chess.engine.Limit(time=tiempo)
        else:
            self.limite = chess.engine.Limit(depth=depth or PROFUNDIDAD_POR_DEFECTO)
        self.nombre = self.motor.id.get("name", "motor UCI")
        self.descripcion = f"{self.nombre}, {limite_txt}"
        self._juego = object()

    def nueva_partida(self):
        """Marca el inicio de una partida: python-chess envia ucinewgame y Stockfish limpia su hash."""
        self._juego = object()

    def evaluar(self, t):
        info = self.motor.analyse(t, self.limite, game=self._juego,
                                  info=self.chess.engine.INFO_SCORE | self.chess.engine.INFO_PV)
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
        sys.exit("Falta python-chess. Instalalo con:  pipenv install  (desde la raíz del proyecto)")


def buscar_motor(explicito):
    candidatos = [explicito, os.environ.get("STOCKFISH_PATH"), shutil.which("stockfish")] + RUTAS_HABITUALES
    for c in candidatos:
        if c and os.path.isfile(c):
            return c
    sys.exit("No encuentro Stockfish. Indica la ruta con --motor o con la variable STOCKFISH_PATH. "
             "Consulta la sección 4 de README.md para instalarlo.")


def texto_limite(args):
    if args.nodos:
        return f"{args.nodos} nodos"
    if args.tiempo:
        return f"{args.tiempo:g} s por posicion"
    return f"profundidad {args.profundidad}"


def crear_motor(args, chess):
    ruta = buscar_motor(args.motor)
    return MotorUCI(chess, ruta, texto_limite(args), depth=args.profundidad, nodes=args.nodos, tiempo=args.tiempo,
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


def analizar_texto_partida(p, ajedrez, motor, libro=None):
    jugadas = n.leer_jugadas(p["movimientos"])
    motor.nueva_partida()
    n.analizar_partida(jugadas, ajedrez, motor)
    cab = [(k, v) for k, v in p["cabeceras"] if k != "Annotator"]
    if libro:
        cab = libro.con_apertura(cab, [j["san"] for j in jugadas])
    cab.append(("Annotator", f"analizar_local.py con {motor.descripcion}"))
    return n.escribir_partida(cab, jugadas, p["resultado"]), jugadas


def etiquetar_texto_partida(p):
    """Partida con %eval pero sin comentarios de Lichess: anade Inaccuracy, Mistake y Blunder sin usar el motor."""
    jugadas = n.etiquetar_desde_evals(n.leer_jugadas(p["movimientos"]))
    return n.escribir_partida(p["cabeceras"], jugadas, p["resultado"]), jugadas


def base_aperturas_disponible():
    return all(os.path.isfile(os.path.join(aperturas.DIRECTORIO, f"{letra}.tsv")) for letra in "abcde")


_motor = None
_ajedrez = None
_libro = None


def _iniciar_proceso(args):
    global _motor, _ajedrez, _libro
    chess = importar_chess()
    _ajedrez = AjedrezChess(chess)
    _libro = aperturas.LibroAperturas(chess) if base_aperturas_disponible() else None
    _motor = crear_motor(args, chess)
    multiprocessing.util.Finalize(None, _motor.cerrar, exitpriority=10)


def _analizar_en_proceso(p):
    """Analiza una partida en este proceso. Devuelve (texto, semijugadas, resumen, error, segundos)."""
    t0 = time.time()
    try:
        texto, js = analizar_texto_partida(p, _ajedrez, _motor, _libro)
    except ValueError as e:
        return None, 0, None, str(e), time.time() - t0
    return texto, len(js), resumen_juicios(js), None, time.time() - t0


def clave_partida(cab):
    return cab.get("GameId") or cab.get("Site")


def jugadas_san(p):
    return [j["san"] for j in n.leer_jugadas(p["movimientos"])]


def termina_con_resultado(p):
    toks = re.sub(r"\{[^}]*\}", " ", p["movimientos"]).split()
    return bool(toks) and toks[-1] in n.RESULTADOS


def partidas_previas(salida, anotador):
    """
    Partidas de cualquier PGN de la carpeta de salida (con independencia de su nombre) hechas con este mismo
    ajuste: ({clave: partida}, cuantas usan otro ajuste).
    """
    validas, otro_ajuste = {}, 0
    for f in sorted(glob.glob(os.path.join(salida, "**", "*.pgn"), recursive=True)):
        with open(f, encoding="utf-8", errors="replace") as fh:
            partidas = n.separar_partidas(fh.read())
        for p in partidas:
            cab = dict(p["cabeceras"])
            anot = cab.get("Annotator", "")
            if not anot.startswith("analizar_local.py"):
                continue
            if anot != anotador:
                otro_ajuste += 1
            elif clave_partida(cab):
                validas[clave_partida(cab)] = p
    return validas, otro_ajuste


def destino_de(fichero, salida):
    """<salida>/<carpeta del PGN>/<nombre>_analizado.pgn: un subdirectorio por usuario (carpeta de origen)."""
    carpeta = os.path.basename(os.path.dirname(os.path.abspath(fichero)))
    return os.path.join(salida, carpeta, os.path.splitext(os.path.basename(fichero))[0] + "_analizado.pgn")


def planificar(ficheros, args, anotador):
    """
    Devuelve (plan, a_analizar, reanudadas, otro_ajuste).
    plan: por fichero, su destino y sus (partida, accion); a_analizar: las partidas a analizar, en orden.
    Una partida ya presente en cualquier PGN de la carpeta de salida, completa, con las mismas jugadas y hecha con el mismo
    motor y limite, se reutiliza (accion "reanudada") en lugar de analizarla otra vez.
    """
    plan, a_analizar = [], []
    reanudadas = 0
    previas, otro_ajuste = partidas_previas(args.salida, anotador)
    for f in ficheros:
        with open(f, encoding="utf-8", errors="replace") as fh:
            partidas = n.separar_partidas(fh.read())
        destino = destino_de(f, args.salida)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        items = []
        for p in partidas:
            cab = dict(p["cabeceras"])
            previa = previas.get(clave_partida(cab))
            if cab.get("Variant", "Standard") != "Standard":
                accion = "variante"
            elif "%eval" in p["movimientos"] and not args.reanalizar:
                accion = "ya_analizada" if n.tiene_juicios(n.leer_jugadas(p["movimientos"])) else "etiquetar"
            elif previa and termina_con_resultado(previa) and jugadas_san(previa) == jugadas_san(p):
                accion = "reanudada"
                p = previa
                reanudadas += 1
            elif args.maximo and len(a_analizar) >= args.maximo:
                accion = "copiar"
            else:
                accion = "analizar"
                a_analizar.append(p)
            items.append((p, accion))
        plan.append((destino, items))
    return plan, a_analizar, reanudadas, otro_ajuste


def descripcion_motor(args, chess):
    motor = crear_motor(args, chess)
    try:
        return motor.descripcion
    finally:
        motor.cerrar()


def formatear_tiempo(segundos):
    s = int(round(segundos))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


class Progreso:
    """Barra de progreso en una sola linea. Si la salida no es un terminal, no dibuja nada."""

    ANCHO = 28

    def __init__(self, total, procesos, terminal=None):
        self.total = total
        self.procesos = procesos
        self.t0 = time.time()
        self.terminal = sys.stdout.isatty() if terminal is None else terminal
        self._largo = 0

    def texto(self, hechas):
        fraccion = hechas / self.total if self.total else 1.0
        lleno = int(self.ANCHO * fraccion)
        transcurrido = time.time() - self.t0
        eta = formatear_tiempo((self.total - hechas) * transcurrido / hechas) if hechas else "--:--:--"
        en_curso = min(self.procesos, self.total - hechas)
        return (f"[{'#' * lleno}{'-' * (self.ANCHO - lleno)}] {hechas}/{self.total} {100 * fraccion:.1f}%"
                f"  transcurrido {formatear_tiempo(transcurrido)}  ETA {eta}  en curso {en_curso}")

    def actualizar(self, hechas):
        if not self.terminal or not self.total:
            return
        txt = self.texto(hechas)
        sys.stdout.write("\r" + txt.ljust(self._largo))
        sys.stdout.flush()
        self._largo = len(txt)

    def linea(self, texto, hechas):
        """Imprime una linea de registro sin romper la barra, y la vuelve a dibujar debajo."""
        if self.terminal and self._largo:
            sys.stdout.write("\r" + " " * self._largo + "\r")
        print(texto, flush=True)
        self.actualizar(hechas)

    def cerrar(self):
        if self.terminal and self._largo:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._largo = 0


def esperar(futuro, futuros, progreso):
    """Espera el resultado de un futuro y mientras tanto refresca la barra cada segundo."""
    while True:
        progreso.actualizar(sum(f.done() for f in futuros))
        if futuro.done():
            return futuro.result()
        wait([futuro], timeout=1)


def escribir_partida(out, texto):
    out.write(texto if texto.endswith("\n\n") else texto.rstrip("\n") + "\n\n")
    out.flush()


def procesar(args):
    ficheros = ficheros_de(args.entradas, args.salida)
    if not ficheros:
        sys.exit("No se ha encontrado ningun PGN en las rutas indicadas.")
    ruta_motor = buscar_motor(args.motor)
    os.makedirs(args.salida, exist_ok=True)
    if not base_aperturas_disponible():
        print("Aviso: no se encuentra la base de aperturas (analisis_local/base_aperturas); no se anadiran ECO ni Opening")
    anotador = f"analizar_local.py con {descripcion_motor(args, importar_chess())}"
    plan, a_analizar, reanudadas, otro_ajuste = planificar(ficheros, args, anotador)
    procesos = max(1, min(args.procesos, len(a_analizar)))
    ya_analizadas = sum(1 for _, items in plan for _, accion in items if accion == "ya_analizada")
    print(f"Motor: {ruta_motor} | limite: {texto_limite(args)}")
    print(f"{len(a_analizar)} partidas a analizar con {procesos} proceso(s)")
    if reanudadas:
        print(f"{reanudadas} partidas ya estaban analizadas con este mismo motor y limite en una ejecucion anterior: se reutilizan")
    if otro_ajuste:
        print(f"AVISO: {otro_ajuste} partidas de la salida anterior se hicieron con otro motor o limite y no se "
              f"reutilizan; los ficheros de salida con el mismo nombre se sobrescriben")
    a_etiquetar = sum(1 for _, items in plan for _, accion in items if accion == "etiquetar")
    if ya_analizadas:
        print(f"{ya_analizadas} partidas ya traen analisis y se copian sin cambios (usa --reanalizar para rehacerlas)")
    if a_etiquetar:
        print(f"{a_etiquetar} partidas traen %eval pero no los comentarios de Lichess: se anaden Inaccuracy, Mistake y "
              f"Blunder con sus evaluaciones, sin motor (usa --reanalizar para analizarlas con Stockfish)")
    ex = None
    futuros = []
    if a_analizar:
        ex = ProcessPoolExecutor(max_workers=procesos, initializer=_iniciar_proceso, initargs=(args,))
        futuros = [ex.submit(_analizar_en_proceso, p) for p in a_analizar]
    siguiente = iter(futuros)
    progreso = Progreso(len(a_analizar), procesos)
    total = analizadas = consumidas = 0
    interrumpido = False
    t_ini = time.time()
    hechas = lambda: sum(f.done() for f in futuros)
    try:
        progreso.actualizar(0)
        for destino, items in plan:
            with open(destino, "w", encoding="utf-8") as out:
                for p, accion in items:
                    cab = dict(p["cabeceras"])
                    gid = cab.get("GameId", "?")
                    total += 1
                    if accion == "variante":
                        progreso.linea(f"-  {gid}: variante {cab['Variant']}, se copia sin analizar", hechas())
                        escribir_partida(out, p["texto"])
                    elif accion in ("ya_analizada", "copiar", "reanudada"):
                        escribir_partida(out, p["texto"])
                    elif accion == "etiquetar":
                        escribir_partida(out, etiquetar_texto_partida(p)[0])
                    else:
                        texto, semijugadas, resumen, error, segundos = esperar(next(siguiente), futuros, progreso)
                        consumidas += 1
                        marca = f"[{consumidas}/{len(a_analizar)}]"
                        if error:
                            progreso.linea(f"X  {marca} {gid}: {error}; se copia sin analizar", hechas())
                            escribir_partida(out, p["texto"])
                            continue
                        analizadas += 1
                        escribir_partida(out, texto)
                        progreso.linea(f"OK {marca} {gid}: {semijugadas} semijugadas en {segundos:.0f} s | {resumen}", hechas())
            progreso.linea(f"-> {destino}", hechas())
    except KeyboardInterrupt:
        interrumpido = True
        progreso.cerrar()
        print("\nInterrumpido. Lo analizado hasta ahora se ha guardado.")
    finally:
        progreso.cerrar()
        if ex:
            ex.shutdown(wait=not interrumpido, cancel_futures=True)
    transcurrido = time.time() - t_ini
    media = f", {transcurrido / analizadas:.0f} s por partida de media" if analizadas else ""
    reutilizadas = f" ({reanudadas} reutilizadas de una ejecucion anterior)" if reanudadas else ""
    print(f"\n{analizadas} partidas analizadas de {total} en {formatear_tiempo(transcurrido)}{media}{reutilizadas}")


def autotest(args, chess):
    """Analiza una partida corta con mate del pastor y comprueba que todo funciona."""
    ajedrez = AjedrezChess(chess)
    motor = crear_motor(args, chess)
    try:
        print(f"Motor: {motor.descripcion}")
        sans = ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7#"]
        js = [{"san": s, "clk": None} for s in sans]
        t0 = time.time()
        motor.nueva_partida()
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
    ap.add_argument("--profundidad", type=int, default=PROFUNDIDAD_POR_DEFECTO,
                    help=f"profundidad de analisis (por defecto {PROFUNDIDAD_POR_DEFECTO})")
    ap.add_argument("--nodos", type=int, help="limite de nodos por posicion; sustituye a la profundidad y al tiempo")
    ap.add_argument("--tiempo", type=float, help="segundos por posicion; sustituye a la profundidad")
    ap.add_argument("--hilos", type=int, default=0, help="hilos de cada motor (0 = valor por defecto del motor, 1)")
    ap.add_argument("--hash", type=int, default=256, dest="hash_mb", help="memoria hash en MB por proceso (por defecto 256)")
    ap.add_argument("--procesos", type=int, default=1, help="partidas analizadas a la vez (por defecto 1)")
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
        procesar(args)
    else:
        ap.error("indica ficheros o carpetas de PGN, o usa --autotest")


if __name__ == "__main__":
    main()