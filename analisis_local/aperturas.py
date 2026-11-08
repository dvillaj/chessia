# -*- coding: utf-8 -*-
"""
aperturas.py - Busca el codigo ECO y el nombre de la apertura de una partida, como hace Lichess.

Usa la base publica lichess-org/chess-openings (licencia CC0), guardada en analisis_local/base_aperturas/
(a.tsv a e.tsv, columnas eco, name y pgn). Ver base_aperturas/LEEME.md para su origen y como actualizarla.

La busqueda replica la de scalachess (OpeningDb.search): se identifica cada posicion por su EPD, asi
que las transposiciones dan el mismo resultado; se miran como mucho las 40 primeras semijugadas, se
para en la primera posicion con menos de 20 piezas y gana la coincidencia mas profunda.
"""
import csv
import os
import re

DIRECTORIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_aperturas")
MAX_SEMIJUGADAS = 40
MIN_PIEZAS = 20

_NUMERO_JUGADA = re.compile(r"\d+\.+")


class LibroAperturas:
    def __init__(self, chess, directorio=DIRECTORIO):
        self.chess = chess
        self.indice = {}
        for letra in "abcde":
            ruta = os.path.join(directorio, f"{letra}.tsv")
            with open(ruta, encoding="utf-8", newline="") as fh:
                for fila in csv.DictReader(fh, delimiter="\t"):
                    tablero = chess.Board()
                    for tok in fila["pgn"].split():
                        if not _NUMERO_JUGADA.fullmatch(tok):
                            tablero.push_san(tok)
                    self.indice[tablero.epd()] = (fila["eco"], fila["name"])

    def buscar(self, sans):
        """Devuelve (eco, nombre) de la apertura mas profunda reconocida, o None."""
        tablero = self.chess.Board()
        encontrada = None
        for san in sans[:MAX_SEMIJUGADAS]:
            try:
                tablero.push_san(san)
            except ValueError:
                break
            if len(tablero.piece_map()) < MIN_PIEZAS:
                break
            encontrada = self.indice.get(tablero.epd(), encontrada)
        return encontrada

    def con_apertura(self, cabeceras, sans):
        """
        Devuelve las cabeceras con ECO y Opening anadidos, justo despues de TimeControl como en Lichess.
        Si la partida ya trae alguna de las dos, o no se reconoce la apertura, no se cambia nada.
        """
        if any(k in ("ECO", "Opening") for k, _ in cabeceras):
            return cabeceras
        encontrada = self.buscar(sans)
        if not encontrada:
            return cabeceras
        nuevas = [("ECO", encontrada[0]), ("Opening", encontrada[1])]
        pos = next((i + 1 for i, (k, _) in enumerate(cabeceras) if k == "TimeControl"), len(cabeceras))
        return cabeceras[:pos] + nuevas + cabeceras[pos:]
