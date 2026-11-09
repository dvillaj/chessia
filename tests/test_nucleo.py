# -*- coding: utf-8 -*-
"""Pruebas del núcleo que no necesitan python-chess ni Stockfish."""
import re

import pytest

from analisis_local import nucleo as n

MUESTRA = (
    '[Event "rated rapid game"]\n[Site "https://lichess.org/abcd1234"]\n[White "yo"]\n[Black "rival"]\n'
    '[Result "0-1"]\n[GameId "abcd1234"]\n[TimeControl "900+10"]\n\n'
    '1. d4 { [%eval 0.20] [%clk 0:15:00] } 1... d5 { [%eval 0.18] [%clk 0:15:00] } '
    '2. Bf4 { [%eval 0.22] [%clk 0:15:08] } 2... c5?? { (0.22 → 2.40) Blunder. Nf6 was best. } '
    '{ [%eval 2.40] [%clk 0:15:05] } ( 2... Nf6 3. e3 e6 ) '
    '3. e3 { [%eval 2.31] [%clk 0:15:15] } 3... Qb6?? { (2.31 → Mate in 3) Checkmate is now unavoidable. Nc6 was best. } '
    '{ [%eval #3] [%clk 0:14:50] } ( 3... Nc6 4. c3 e6 ) '
    '4. Qh5 { [%eval #2] [%clk 0:15:20] } 4... g6 { [%eval #2] [%clk 0:14:40] } 0-1\n'
)


class TestEvaluaciones:
    def test_oportunidad_simetrica_y_acotada(self):
        assert n.oportunidad(100) == pytest.approx(-n.oportunidad(-100))
        assert n.oportunidad(5000) == pytest.approx(n.oportunidad(1000))
        assert n.oportunidad(0) == 0

    def test_formatos(self):
        assert n.texto_pgn(("cp", -736)) == "-7.36"
        assert n.texto_pgn(("cp", 0)) == "0.00"
        assert n.texto_pgn(("mate", -3)) == "#-3"
        assert n.texto_flecha(("mate", -3)) == "Mate in 3"
        for ev in (("cp", 21), ("cp", -736), ("mate", 2), ("mate", -12)):
            assert n.leer_texto_eval(n.texto_pgn(ev)) == ev

    def test_punto_de_vista(self):
        assert n.desde_el_que_mueve(("cp", 50), "B") == ("cp", -50)
        assert n.desde_el_que_mueve(("mate", 3), "W") == ("mate", 3)


class TestClasificacion:
    def sev(self, a, d, color="W"):
        v = n.valorar(a, d, color)
        return v["severidad"] if v else None

    def test_umbrales_normales(self):
        assert self.sev(("cp", 20), ("cp", 10)) is None
        assert self.sev(("cp", 20), ("cp", -50)) == "Inaccuracy"
        assert self.sev(("cp", 20), ("cp", -120)) == "Mistake"
        assert self.sev(("cp", 20), ("cp", -300)) == "Blunder"

    def test_negras_usan_su_punto_de_vista(self):
        # para las negras, que la evaluacion de las blancas suba es malo
        assert self.sev(("cp", 21), ("cp", 596), "B") == "Blunder"
        assert self.sev(("cp", 21), ("cp", -200), "B") is None

    def test_mejorar_no_penaliza(self):
        assert self.sev(("cp", -300), ("cp", 100), "W") is None

    def test_mate_recibido(self):
        v = n.valorar(("cp", 355), ("mate", 3), "B")
        assert (v["severidad"], v["frase"]) == ("Blunder", n.FRASE_MATE_RECIBIDO)
        assert self.sev(("cp", 800), ("mate", -2), "W") == "Blunder"
        assert self.sev(("cp", -800), ("mate", -2), "W") == "Mistake"
        assert self.sev(("cp", -1200), ("mate", -2), "W") == "Inaccuracy"
        assert self.sev(("mate", -5), ("mate", -4), "W") is None  # ya estaba perdido por mate

    def test_mate_perdido(self):
        v = n.valorar(("mate", 1), ("cp", 754), "W")
        assert v["frase"] == n.FRASE_MATE_PERDIDO
        assert v["severidad"] == "Mistake"
        assert self.sev(("mate", 1), ("cp", 300), "W") == "Blunder"
        assert self.sev(("mate", 1), ("cp", 1200), "W") == "Inaccuracy"
        assert self.sev(("mate", 3), ("mate", 2), "W") is None  # el mate sigue

    def test_sin_datos(self):
        assert n.valorar(None, ("cp", 0), "W") is None
        assert n.valorar(("cp", 0), None, "W") is None


class TestLecturaEscritura:
    def test_leer_muestra(self):
        partida = n.separar_partidas(MUESTRA)[0]
        assert partida["resultado"] == "0-1"
        assert ("GameId", "abcd1234") in partida["cabeceras"]
        js = n.leer_jugadas(partida["movimientos"])
        assert [j["san"] for j in js] == ["d4", "d5", "Bf4", "c5", "e3", "Qb6", "Qh5", "g6"]
        assert js[3]["juicio"]["severidad"] == "Blunder"
        assert js[3]["juicio"]["mejor"] == "Nf6"
        assert js[3]["variacion"] == ["Nf6", "e3", "e6"]
        assert js[5]["juicio"]["frase"] == n.FRASE_MATE_RECIBIDO
        assert js[5]["juicio"]["severidad"] == "Blunder"  # sale del glifo ??
        assert js[5]["eval"] == ("mate", 3)
        assert js[2]["clk"] == "0:15:08"

    def test_etiquetar_desde_evals_reproduce_la_muestra(self):
        mv = n.separar_partidas(MUESTRA)[0]["movimientos"]
        originales = n.leer_jugadas(mv)
        sin_comentarios = re.sub(r"\{ \([^}]*\} |\( [^)]*\) |\?\?", "", mv)
        js = n.leer_jugadas(sin_comentarios)
        assert not n.tiene_juicios(js) and n.tiene_juicios(originales)
        n.etiquetar_desde_evals(js)
        clave = lambda j: (j["juicio"]["severidad"], j["juicio"]["frase"]) if j["juicio"] else None
        assert [clave(j) for j in js] == [clave(j) for j in originales]
        assert all(j["juicio"]["mejor"] is None for j in js if j["juicio"])

    def test_ida_y_vuelta(self):
        partida = n.separar_partidas(MUESTRA)[0]
        js = n.leer_jugadas(partida["movimientos"])
        for i, j in enumerate(js):                       # reconstruir la flecha con las evaluaciones vecinas
            if j["juicio"]:
                j["juicio"]["antes"] = js[i - 1]["eval"]
                j["juicio"]["despues"] = j["eval"]
        texto = n.escribir_partida(partida["cabeceras"], js, partida["resultado"])
        otra = n.separar_partidas(texto)[0]
        js2 = n.leer_jugadas(otra["movimientos"])
        assert len(js) == len(js2)
        for a, b in zip(js, js2):
            for campo in ("san", "clk", "eval", "variacion"):
                assert a[campo] == b[campo], campo
            assert bool(a["juicio"]) == bool(b["juicio"])
            if a["juicio"]:
                for campo in ("severidad", "frase", "mejor"):
                    assert a["juicio"][campo] == b["juicio"][campo], campo
        assert otra["cabeceras"] == partida["cabeceras"]
        assert texto.rstrip().endswith("0-1")

    def test_numeracion_de_variaciones(self):
        assert n.texto_variacion(0, ["e4", "e5", "Nf3"]) == "1. e4 e5 2. Nf3"
        assert n.texto_variacion(3, ["Nf6", "e3", "e6"]) == "2... Nf6 3. e3 e6"


class TestComparacion:
    def test_analisis_identico(self):
        js = [{"eval": ("cp", 20), "juicio": None}, {"eval": ("cp", -200), "juicio": {"severidad": "Blunder"}}]
        matriz, difs = n.comparar_analisis(js, js)
        assert matriz == {("Blunder", "Blunder"): 1}
        assert max(difs) == 0

    def test_analisis_distinto(self):
        ref = [{"eval": ("cp", 20), "juicio": None}, {"eval": ("cp", -200), "juicio": {"severidad": "Blunder"}}]
        loc = [{"eval": ("cp", 30), "juicio": None}, {"eval": ("cp", -100), "juicio": {"severidad": "Mistake"}}]
        matriz, difs = n.comparar_analisis(ref, loc)
        assert matriz == {("Blunder", "Mistake"): 1}
        assert max(difs) > 0

    def test_se_ignoran_posiciones_sin_evaluacion(self):
        ref = [{"eval": ("cp", 0), "juicio": None}, {"eval": None, "juicio": None}]
        loc = [{"eval": ("cp", 0), "juicio": None}, {"eval": ("cp", 0), "juicio": None}]
        matriz, difs = n.comparar_analisis(ref, loc)
        assert len(difs) == 1
        assert sum(matriz.values()) == 0


class AjedrezFalso:
    """Juego de juguete: un tablero es la tupla de jugadas hechas; la partida acaba al llegar a 'largo' jugadas."""

    def __init__(self, largo):
        self.largo = largo

    def nuevo(self):
        return ()

    def jugada_desde_san(self, t, san):
        return san

    def san_de(self, t, mv):
        return mv

    def empujar(self, t, mv):
        return t + (mv,)

    def color(self, t):
        return "W" if len(t) % 2 == 0 else "B"

    def es_final(self, t):
        return len(t) >= self.largo


class MotorFalso:
    """Devuelve evaluaciones guionizadas segun cuantas jugadas se han hecho."""

    def __init__(self, evals, pv):
        self.evals, self.pv = evals, pv

    def evaluar(self, t):
        return {"eval": self.evals[len(t)], "pv": self.pv.get(len(t), [])}


class TestOrquestacion:
    def jugadas(self, sans):
        return [{"san": s, "clk": "0:15:00"} for s in sans]

    def test_detecta_el_blunder_y_propone_alternativa(self):
        evals = [("cp", 20), ("cp", 30), ("cp", 25), ("cp", -200), ("cp", -190)]
        pv = {2: ["Nf3", "Nc6", "Bb5"]}
        js = n.analizar_partida(self.jugadas(["e4", "e5", "Qh5", "Nc6"]), AjedrezFalso(99), MotorFalso(evals, pv))
        assert [j["eval"] for j in js] == evals[1:]
        assert js[0]["juicio"] is None
        assert js[2]["juicio"]["severidad"] == "Blunder"
        assert js[2]["juicio"]["mejor"] == "Nf3"
        assert n.texto_variacion(2, js[2]["variacion"]) == "2. Nf3 Nc6 3. Bb5"

    def test_sin_evaluacion_tras_la_ultima_jugada(self):
        evals = [("cp", 20), ("cp", 30), ("cp", 25), ("cp", 25)]
        js = n.analizar_partida(self.jugadas(["e4", "e5", "Nf3"]), AjedrezFalso(3), MotorFalso(evals, {}))
        assert js[2]["eval"] is None
        assert js[2]["juicio"] is None

    def test_jugada_ilegal(self):
        class Estricto(AjedrezFalso):
            def jugada_desde_san(self, t, san):
                return None if san == "zz" else san
        with pytest.raises(ValueError):
            n.analizar_partida(self.jugadas(["e4", "zz"]), Estricto(99), MotorFalso([("cp", 0)] * 5, {}))
