# -*- coding: utf-8 -*-
"""
pruebas_nucleo.py - Pruebas del nucleo. No necesitan python-chess ni Stockfish.

Uso:  python pruebas_nucleo.py
"""
import unittest

import nucleo as n

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


class PruebasEvaluaciones(unittest.TestCase):
    def test_oportunidad_simetrica_y_acotada(self):
        self.assertAlmostEqual(n.oportunidad(100), -n.oportunidad(-100))
        self.assertAlmostEqual(n.oportunidad(5000), n.oportunidad(1000))
        self.assertEqual(n.oportunidad(0), 0)

    def test_formatos(self):
        self.assertEqual(n.texto_pgn(("cp", -736)), "-7.36")
        self.assertEqual(n.texto_pgn(("cp", 0)), "0.00")
        self.assertEqual(n.texto_pgn(("mate", -3)), "#-3")
        self.assertEqual(n.texto_flecha(("mate", -3)), "Mate in 3")
        for ev in (("cp", 21), ("cp", -736), ("mate", 2), ("mate", -12)):
            self.assertEqual(n.leer_texto_eval(n.texto_pgn(ev)), ev)

    def test_punto_de_vista(self):
        self.assertEqual(n.desde_el_que_mueve(("cp", 50), "B"), ("cp", -50))
        self.assertEqual(n.desde_el_que_mueve(("mate", 3), "W"), ("mate", 3))


class PruebasClasificacion(unittest.TestCase):
    def sev(self, a, d, color="W"):
        v = n.valorar(a, d, color)
        return v["severidad"] if v else None

    def test_umbrales_normales(self):
        self.assertIsNone(self.sev(("cp", 20), ("cp", 10)))
        self.assertEqual(self.sev(("cp", 20), ("cp", -50)), "Inaccuracy")
        self.assertEqual(self.sev(("cp", 20), ("cp", -120)), "Mistake")
        self.assertEqual(self.sev(("cp", 20), ("cp", -300)), "Blunder")

    def test_negras_usan_su_punto_de_vista(self):
        # para las negras, que la evaluacion de las blancas suba es malo
        self.assertEqual(self.sev(("cp", 21), ("cp", 596), "B"), "Blunder")
        self.assertIsNone(self.sev(("cp", 21), ("cp", -200), "B"))

    def test_mejorar_no_penaliza(self):
        self.assertIsNone(self.sev(("cp", -300), ("cp", 100), "W"))

    def test_mate_recibido(self):
        v = n.valorar(("cp", 355), ("mate", 3), "B")
        self.assertEqual((v["severidad"], v["frase"]), ("Blunder", n.FRASE_MATE_RECIBIDO))
        self.assertEqual(self.sev(("cp", 800), ("mate", -2), "W"), "Blunder")
        self.assertEqual(self.sev(("cp", -800), ("mate", -2), "W"), "Mistake")
        self.assertEqual(self.sev(("cp", -1200), ("mate", -2), "W"), "Inaccuracy")
        self.assertIsNone(self.sev(("mate", -5), ("mate", -4), "W"))            # ya estaba perdido por mate

    def test_mate_perdido(self):
        v = n.valorar(("mate", 1), ("cp", 754), "W")
        self.assertEqual(v["frase"], n.FRASE_MATE_PERDIDO)
        self.assertEqual(v["severidad"], "Mistake")
        self.assertEqual(self.sev(("mate", 1), ("cp", 300), "W"), "Blunder")
        self.assertEqual(self.sev(("mate", 1), ("cp", 1200), "W"), "Inaccuracy")
        self.assertIsNone(self.sev(("mate", 3), ("mate", 2), "W"))              # el mate sigue

    def test_sin_datos(self):
        self.assertIsNone(n.valorar(None, ("cp", 0), "W"))
        self.assertIsNone(n.valorar(("cp", 0), None, "W"))


class PruebasLecturaEscritura(unittest.TestCase):
    def test_leer_muestra(self):
        partida = n.separar_partidas(MUESTRA)[0]
        self.assertEqual(partida["resultado"], "0-1")
        self.assertIn(("GameId", "abcd1234"), partida["cabeceras"])
        js = n.leer_jugadas(partida["movimientos"])
        self.assertEqual([j["san"] for j in js], ["d4", "d5", "Bf4", "c5", "e3", "Qb6", "Qh5", "g6"])
        self.assertEqual(js[3]["juicio"]["severidad"], "Blunder")
        self.assertEqual(js[3]["juicio"]["mejor"], "Nf6")
        self.assertEqual(js[3]["variacion"], ["Nf6", "e3", "e6"])
        self.assertEqual(js[5]["juicio"]["frase"], n.FRASE_MATE_RECIBIDO)
        self.assertEqual(js[5]["juicio"]["severidad"], "Blunder")       # sale del glifo ??
        self.assertEqual(js[5]["eval"], ("mate", 3))
        self.assertEqual(js[2]["clk"], "0:15:08")

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
        self.assertEqual(len(js), len(js2))
        for a, b in zip(js, js2):
            for campo in ("san", "clk", "eval", "variacion"):
                self.assertEqual(a[campo], b[campo], campo)
            self.assertEqual(bool(a["juicio"]), bool(b["juicio"]))
            if a["juicio"]:
                for campo in ("severidad", "frase", "mejor"):
                    self.assertEqual(a["juicio"][campo], b["juicio"][campo], campo)
        self.assertEqual(otra["cabeceras"], partida["cabeceras"])
        self.assertTrue(texto.rstrip().endswith("0-1"))

    def test_numeracion_de_variaciones(self):
        self.assertEqual(n.texto_variacion(0, ["e4", "e5", "Nf3"]), "1. e4 e5 2. Nf3")
        self.assertEqual(n.texto_variacion(3, ["Nf6", "e3", "e6"]), "2... Nf6 3. e3 e6")


class PruebasComparacion(unittest.TestCase):
    def test_analisis_identico(self):
        js = [{"eval": ("cp", 20), "juicio": None}, {"eval": ("cp", -200), "juicio": {"severidad": "Blunder"}}]
        matriz, difs = n.comparar_analisis(js, js)
        self.assertEqual(matriz, {("Blunder", "Blunder"): 1})
        self.assertEqual(max(difs), 0)

    def test_analisis_distinto(self):
        ref = [{"eval": ("cp", 20), "juicio": None}, {"eval": ("cp", -200), "juicio": {"severidad": "Blunder"}}]
        loc = [{"eval": ("cp", 30), "juicio": None}, {"eval": ("cp", -100), "juicio": {"severidad": "Mistake"}}]
        matriz, difs = n.comparar_analisis(ref, loc)
        self.assertEqual(matriz, {("Blunder", "Mistake"): 1})
        self.assertGreater(max(difs), 0)

    def test_se_ignoran_posiciones_sin_evaluacion(self):
        ref = [{"eval": ("cp", 0), "juicio": None}, {"eval": None, "juicio": None}]
        loc = [{"eval": ("cp", 0), "juicio": None}, {"eval": ("cp", 0), "juicio": None}]
        matriz, difs = n.comparar_analisis(ref, loc)
        self.assertEqual(len(difs), 1)
        self.assertEqual(sum(matriz.values()), 0)


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


class PruebasOrquestacion(unittest.TestCase):
    def jugadas(self, sans):
        return [{"san": s, "clk": "0:15:00"} for s in sans]

    def test_detecta_el_blunder_y_propone_alternativa(self):
        evals = [("cp", 20), ("cp", 30), ("cp", 25), ("cp", -200), ("cp", -190)]
        pv = {2: ["Nf3", "Nc6", "Bb5"]}
        js = n.analizar_partida(self.jugadas(["e4", "e5", "Qh5", "Nc6"]), AjedrezFalso(99), MotorFalso(evals, pv))
        self.assertEqual([j["eval"] for j in js], evals[1:])
        self.assertIsNone(js[0]["juicio"])
        self.assertEqual(js[2]["juicio"]["severidad"], "Blunder")
        self.assertEqual(js[2]["juicio"]["mejor"], "Nf3")
        self.assertEqual(n.texto_variacion(2, js[2]["variacion"]), "2. Nf3 Nc6 3. Bb5")

    def test_sin_evaluacion_tras_la_ultima_jugada(self):
        evals = [("cp", 20), ("cp", 30), ("cp", 25), ("cp", 25)]
        js = n.analizar_partida(self.jugadas(["e4", "e5", "Nf3"]), AjedrezFalso(3), MotorFalso(evals, {}))
        self.assertIsNone(js[2]["eval"])
        self.assertIsNone(js[2]["juicio"])

    def test_jugada_ilegal(self):
        class Estricto(AjedrezFalso):
            def jugada_desde_san(self, t, san):
                return None if san == "zz" else san
        with self.assertRaises(ValueError):
            n.analizar_partida(self.jugadas(["e4", "zz"]), Estricto(99), MotorFalso([("cp", 0)] * 5, {}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
