# -*- coding: utf-8 -*-
"""Pruebas de la busqueda de aperturas. Necesitan python-chess pero no Stockfish."""
import pytest

chess = pytest.importorskip("chess")

from analisis_local import aperturas  # noqa: E402


@pytest.fixture(scope="module")
def libro():
    return aperturas.LibroAperturas(chess)


def test_reconoce_una_apertura_conocida(libro):
    assert libro.buscar(["e4", "e5", "Nf3", "Nc6", "Bb5"]) == ("C60", "Ruy Lopez")


def test_gana_la_coincidencia_mas_profunda(libro):
    eco, nombre = libro.buscar(["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"])
    assert nombre.startswith("Ruy Lopez: Morphy Defense")


def test_las_transposiciones_dan_el_mismo_resultado(libro):
    assert libro.buscar(["e4", "c5", "Nf3"]) == libro.buscar(["Nf3", "c5", "e4"])


def test_sin_jugadas_o_ilegales_no_hay_apertura(libro):
    assert libro.buscar([]) is None
    assert libro.buscar(["e5"]) is None


def test_con_apertura_inserta_tras_timecontrol(libro):
    cab = [("Event", "x"), ("TimeControl", "900+10"), ("Termination", "Normal")]
    nuevas = libro.con_apertura(cab, ["e4", "e5", "Nf3", "Nc6", "Bb5"])
    assert [k for k, _ in nuevas] == ["Event", "TimeControl", "ECO", "Opening", "Termination"]
    assert dict(nuevas)["ECO"] == "C60"


def test_con_apertura_sin_timecontrol_va_al_final(libro):
    nuevas = libro.con_apertura([("Event", "x")], ["e4", "e5"])
    assert [k for k, _ in nuevas] == ["Event", "ECO", "Opening"]


def test_con_apertura_no_pisa_lo_que_ya_trae(libro):
    cab = [("Event", "x"), ("ECO", "A00"), ("Opening", "Mi apertura")]
    assert libro.con_apertura(cab, ["e4", "e5", "Nf3"]) == cab


def test_con_apertura_sin_coincidencia_no_cambia_nada(libro):
    cab = [("Event", "x")]
    assert libro.con_apertura(cab, []) == cab
