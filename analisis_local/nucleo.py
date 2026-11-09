# -*- coding: utf-8 -*-
"""
nucleo.py - Logica pura del analisis local. NO necesita python-chess ni ningun motor.

Contiene:
  - Evaluaciones: probabilidad de ganar, punto de vista, texto en formato Lichess.
  - Clasificacion de jugadas (Inaccuracy, Mistake, Blunder) con los mismos umbrales que Lichess.
  - Lectura de PGN (jugadas, relojes, evaluaciones y comentarios de Lichess) y escritura en formato Lichess.

Una evaluacion es una tupla desde el punto de vista de las BLANCAS:
  ('cp', 35)     35 centipeones a favor de las blancas
  ('mate', 3)    las blancas dan mate en 3
  ('mate', -2)   las negras dan mate en 2

Validacion: con las evaluaciones de Lichess, estas reglas reproducen sus etiquetas en el 99,8 % de las
jugadas con evaluacion normal (ver validar_umbrales_offline.py).
"""
import math
import re

# ----------------------------------------------------------------------------- constantes
K_GANAR = 0.00368208            # pendiente de la curva logistica de Lichess
CP_TOPE = 1000                  # las evaluaciones se recortan a +-1000 centipeones para calcular
UMBRALES = ((0.3, "Blunder"), (0.2, "Mistake"), (0.1, "Inaccuracy"))   # caida de oportunidad de ganar (escala -1 a 1)
UMBRALES_MATE = (700, 1000)     # en centipeones, para los casos con mate
GLIFOS = {"Inaccuracy": "?!", "Mistake": "?", "Blunder": "??"}
RESULTADOS = {"1-0", "0-1", "1/2-1/2", "*"}

FRASE_MATE_RECIBIDO = "Checkmate is now unavoidable"
FRASE_MATE_PERDIDO = "Lost forced checkmate sequence"


# ----------------------------------------------------------------------------- evaluaciones
def oportunidad(cp):
    """Oportunidad de ganar en escala -1 a 1 (formula de Lichess)."""
    cp = max(-CP_TOPE, min(CP_TOPE, cp))
    return 2.0 / (1.0 + math.exp(-K_GANAR * cp)) - 1.0


def desde_el_que_mueve(ev, color):
    """Convierte una evaluacion de las blancas al punto de vista del que mueve ('W' o 'B')."""
    if ev is None or color == "W":
        return ev
    return (ev[0], -ev[1])


def texto_pgn(ev):
    """Texto para la etiqueta %eval: 0.21, -7.36, #3, #-2."""
    if ev[0] == "mate":
        return f"#{ev[1]}"
    pawns = round(ev[1] / 100.0, 2)
    if pawns == 0:
        pawns = 0.0
    return f"{pawns:.2f}"


def texto_flecha(ev):
    """Texto para la flecha del comentario: 0.21 o Mate in 3."""
    if ev is None:
        return "?"
    if ev[0] == "mate":
        return f"Mate in {abs(ev[1])}"
    return texto_pgn(ev)


def leer_texto_eval(txt):
    """Inversa de texto_pgn: '0.21' -> ('cp', 21), '#-3' -> ('mate', -3)."""
    if txt.startswith("#"):
        return ("mate", int(float(txt[1:])))
    return ("cp", int(round(float(txt) * 100)))


# ----------------------------------------------------------------------------- clasificacion
def valorar(antes, despues, color):
    """
    Clasifica la jugada de 'color' ('W' o 'B') segun la evaluacion antes y despues (de las blancas).
    Devuelve None o un dict con 'severidad' (Inaccuracy, Mistake o Blunder) y 'frase' (el texto que
    Lichess pone en el comentario).
    """
    if antes is None or despues is None:
        return None
    a = desde_el_que_mueve(antes, color)
    d = desde_el_que_mueve(despues, color)

    # evaluaciones normales
    if a[0] == "cp" and d[0] == "cp":
        caida = oportunidad(a[1]) - oportunidad(d[1])
        for umbral, sev in UMBRALES:
            if caida >= umbral:
                return {"severidad": sev, "frase": sev}
        return None

    u_mistake, u_inacc = UMBRALES_MATE
    # le dan mate y antes no estaba perdido por mate
    if d[0] == "mate" and d[1] < 0 and not (a[0] == "mate" and a[1] < 0):
        if a[0] == "mate":                          # tenia mate propio y ahora lo reciben
            sev = "Blunder"
        elif a[1] > -u_mistake:
            sev = "Blunder"
        elif a[1] > -u_inacc:
            sev = "Mistake"
        else:
            sev = "Inaccuracy"
        return {"severidad": sev, "frase": FRASE_MATE_RECIBIDO}
    # tenia mate propio y lo pierde
    if a[0] == "mate" and a[1] > 0 and not (d[0] == "mate" and d[1] > 0):
        if d[0] == "mate":
            sev = "Blunder"
        elif d[1] > u_inacc - 1:
            sev = "Inaccuracy"
        elif d[1] > u_mistake:
            sev = "Mistake"
        else:
            sev = "Blunder"
        return {"severidad": sev, "frase": FRASE_MATE_PERDIDO}
    return None


# ----------------------------------------------------------------------------- lectura de PGN
_TOK = re.compile(r"(\{[^}]*\})|(\([^)]*\))|(\d+\.{1,3})|([^\s{}()]+)")
_JUICIO = re.compile(r"\(([^)]*)\)\s*(Inaccuracy|Mistake|Blunder|%s|%s)\.(?:\s*(\S+) was best\.)?"
                     % (re.escape(FRASE_MATE_RECIBIDO), re.escape(FRASE_MATE_PERDIDO)))


def separar_partidas(texto):
    """Divide un fichero PGN en partidas: lista de dict con cabeceras (lista ordenada), jugadas (texto) y resultado."""
    partidas = []
    for g in re.split(r"(?m)^(?=\[Event )", texto):
        if not g.strip():
            continue
        m = re.search(r"\n[ \t]*\n", g)
        cab_txt, mv = (g[: m.start()], g[m.end():]) if m else (g, "")
        cabeceras = re.findall(r'\[(\w+) "([^"]*)"\]', cab_txt)
        res = next((v for k, v in cabeceras if k == "Result"), "*")
        toks = re.sub(r"\{[^}]*\}", " ", mv).split()
        if toks and toks[-1] in RESULTADOS:
            res = toks[-1]
        partidas.append({"cabeceras": cabeceras, "movimientos": mv, "resultado": res, "texto": g})
    return partidas


def leer_jugadas(movimientos):
    """
    Lee el texto de jugadas de un PGN (con o sin analisis de Lichess).
    Devuelve una lista de dict con: san, clk, eval, juicio (o None) y variacion (lista de SAN o None).
    """
    jugadas, cur = [], None
    for com, var, num, tok in _TOK.findall(movimientos):
        if tok:
            if tok in RESULTADOS or tok.startswith("$"):
                continue
            cur = {"san": tok.rstrip("?!"), "clk": None, "eval": None, "juicio": None, "variacion": None}
            jugadas.append(cur)
        elif com and cur is not None:
            m = re.search(r"%clk (\d+:\d\d:\d\d(?:\.\d+)?)", com)
            if m:
                cur["clk"] = m.group(1)
            m = re.search(r"%eval (#?-?[\d.]+)", com)
            if m:
                cur["eval"] = leer_texto_eval(m.group(1))
            m = _JUICIO.search(com)
            if m:
                frase = m.group(2)
                cur["juicio"] = {"frase": frase, "severidad": frase if frase in GLIFOS else None,
                                 "mejor": m.group(3)}
        elif var and cur is not None:
            sans = [t.rstrip("?!") for t in var[1:-1].split() if not re.fullmatch(r"\d+\.{1,3}", t)]
            cur["variacion"] = sans
    # los juicios de mate no dicen su gravedad en el texto: se toma del glifo escrito junto al SAN
    for j, tok in zip(jugadas, _sans_con_glifo(movimientos)):
        if j["juicio"] and j["juicio"]["severidad"] is None:
            j["juicio"]["severidad"] = ("Blunder" if tok.endswith("??") else
                                        "Inaccuracy" if tok.endswith("?!") else "Mistake")
    return jugadas


def _sans_con_glifo(movimientos):
    out = []
    for com, var, num, tok in _TOK.findall(movimientos):
        if tok and tok not in RESULTADOS and not tok.startswith("$"):
            out.append(tok)
    return out


# ----------------------------------------------------------------------------- escritura de PGN
def _prefijo(i):
    return f"{i // 2 + 1}." if i % 2 == 0 else f"{i // 2 + 1}..."


def texto_variacion(i, sans):
    """Variacion que empieza en la semijugada i (0 = primera jugada de las blancas), con numeracion correcta."""
    out, k = [], i
    for n, s in enumerate(sans):
        num = k // 2 + 1
        if k % 2 == 0:
            out.append(f"{num}. {s}")
        else:
            out.append(f"{num}... {s}" if n == 0 else s)
        k += 1
    return " ".join(out)


def escribir_jugada(i, j):
    """Texto de una jugada en el formato de Lichess."""
    ju = j.get("juicio")
    glifo = GLIFOS[ju["severidad"]] if ju else ""
    partes = [f"{_prefijo(i)} {j['san']}{glifo}"]
    if ju:
        txt = f"({texto_flecha(ju['antes'])} → {texto_flecha(ju['despues'])}) {ju['frase']}."
        if ju.get("mejor"):
            txt += f" {ju['mejor']} was best."
        partes.append("{ " + txt + " }")
    tags = []
    if j.get("eval") is not None:
        tags.append(f"[%eval {texto_pgn(j['eval'])}]")
    if j.get("clk"):
        tags.append(f"[%clk {j['clk']}]")
    if tags:
        partes.append("{ " + " ".join(tags) + " }")
    if j.get("variacion"):
        partes.append("( " + texto_variacion(i, j["variacion"]) + " )")
    return " ".join(partes)


def escribir_partida(cabeceras, jugadas, resultado):
    """Texto completo de una partida: cabeceras, linea en blanco, jugadas y resultado."""
    cab = "\n".join(f'[{k} "{v}"]' for k, v in cabeceras)
    mov = " ".join(escribir_jugada(i, j) for i, j in enumerate(jugadas))
    return f"{cab}\n\n{mov} {resultado}\n\n"


# ----------------------------------------------------------------------------- orquestacion
def analizar_partida(jugadas, ajedrez, motor, pv_max=8):
    """
    Anade a cada jugada su evaluacion, su clasificacion y la variacion con la mejor alternativa.

    jugadas: lista de dict (de leer_jugadas) con al menos 'san' y 'clk'.
    ajedrez: objeto con los metodos nuevo(), jugada_desde_san(tablero, san), san_de(tablero, jugada),
             empujar(tablero, jugada), color(tablero) -> 'W' o 'B', es_final(tablero).
    motor:   objeto con evaluar(tablero) -> {'eval': evaluacion de las blancas, 'pv': [jugadas]}.
    Devuelve la lista de jugadas actualizada (la misma lista).
    """
    tablero = ajedrez.nuevo()
    posiciones = [tablero]
    movs = []
    for j in jugadas:
        mv = ajedrez.jugada_desde_san(tablero, j["san"])
        if mv is None:
            raise ValueError(f"jugada ilegal o no reconocida: {j['san']}")
        movs.append(mv)
        tablero = ajedrez.empujar(tablero, mv)
        posiciones.append(tablero)

    infos = [None if ajedrez.es_final(p) else motor.evaluar(p) for p in posiciones]

    for i, j in enumerate(jugadas):
        j["eval"] = infos[i + 1]["eval"] if infos[i + 1] else None      # sin evaluacion tras jugada final, como Lichess
        j["juicio"], j["variacion"] = None, None
        antes = infos[i]["eval"] if infos[i] else None
        v = valorar(antes, j["eval"], ajedrez.color(posiciones[i]))
        if v:
            pv = list(infos[i]["pv"][:pv_max])
            mejor = None
            sans, t = [], posiciones[i]
            for m in pv:
                sans.append(ajedrez.san_de(t, m))
                t = ajedrez.empujar(t, m)
            if sans and sans[0] != j["san"]:
                mejor = sans[0]
                j["variacion"] = sans
            j["juicio"] = {"severidad": v["severidad"], "frase": v["frase"], "antes": antes,
                           "despues": j["eval"], "mejor": mejor}
    return jugadas


def tiene_juicios(jugadas):
    """True si alguna jugada trae un comentario Inaccuracy, Mistake, Blunder o de mate."""
    return any(j.get("juicio") for j in jugadas)


def etiquetar_desde_evals(jugadas):
    """
    Anade la clasificacion a partir de las evaluaciones que ya trae cada jugada, sin motor. Sirve para partidas
    exportadas de Lichess con %eval pero sin sus comentarios (literate=false). No hay mejor jugada ni variacion.
    La primera jugada no se clasifica: falta la evaluacion de la posicion inicial. Supone la posicion inicial
    estandar (empiezan las blancas). Devuelve la lista de jugadas actualizada (la misma lista).
    """
    for i, j in enumerate(jugadas):
        antes = jugadas[i - 1]["eval"] if i > 0 else None
        v = valorar(antes, j["eval"], "W" if i % 2 == 0 else "B")
        j["juicio"] = ({"severidad": v["severidad"], "frase": v["frase"], "antes": antes, "despues": j["eval"],
                        "mejor": None} if v else None)
    return jugadas


# ----------------------------------------------------------------------------- comparacion de analisis
def comparar_analisis(ref, loc):
    """
    Compara jugada a jugada dos analisis de la misma partida (listas de dict con 'eval' y 'juicio').
    Devuelve (matriz, difs): matriz cuenta (etiqueta_ref, etiqueta_loc) y difs es la lista de diferencias de
    oportunidad de ganar (0 a 2) en las posiciones evaluadas por los dos.
    """
    from collections import Counter

    def cp(ev):
        return ev[1] if ev[0] == "cp" else (CP_TOPE if ev[1] > 0 else -CP_TOPE)

    matriz, difs = Counter(), []
    for i, (a, b) in enumerate(zip(ref, loc)):
        if a["eval"] is None or b["eval"] is None:
            continue
        difs.append(abs(oportunidad(cp(a["eval"])) - oportunidad(cp(b["eval"]))))
        if i == 0:
            continue
        et = lambda j: j["juicio"]["severidad"] if j.get("juicio") else "ok"
        matriz[(et(a), et(b))] += 1
    return matriz, difs
