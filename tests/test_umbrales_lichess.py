# -*- coding: utf-8 -*-
"""La regla de clasificacion reproduce las etiquetas de Lichess. No necesita motor ni python-chess."""
from pathlib import Path

import pytest

import validar_umbrales_offline as val

PARTIDAS = Path(__file__).resolve().parent.parent / "partidas"
MIN_PARTIDAS = 30


@pytest.fixture(scope="module")
def comparacion():
    if not PARTIDAS.is_dir():
        pytest.skip("no existe la carpeta partidas/")
    partidas, _ = val.leer([str(PARTIDAS)])
    if len(partidas) < MIN_PARTIDAS:
        pytest.skip(f"hacen falta al menos {MIN_PARTIDAS} partidas analizadas por Lichess en partidas/")
    return val.comparar(partidas)


def test_acuerdo_en_evaluaciones_normales(comparacion):
    normal, _ = comparacion
    assert sum(normal.values()) >= 1000
    assert val.acuerdo(normal) >= 0.995


def test_acuerdo_en_casos_con_mate(comparacion):
    _, mate = comparacion
    if sum(mate.values()) < 100:
        pytest.skip("pocos casos con mate para medir el acuerdo")
    assert val.acuerdo(mate) >= 0.95


def test_ignora_partidas_analizadas_en_local(tmp_path):
    pgn = ('[Event "x"]\n[GameId "abc"]\n[Annotator "analizar_local.py con Stockfish 19, profundidad 20"]\n\n'
           '1. e4 { [%eval 0.30] } 1... e5 { [%eval 0.25] } 1-0\n')
    (tmp_path / "local.pgn").write_text(pgn, encoding="utf-8")
    partidas, ignoradas = val.leer([str(tmp_path)])
    assert partidas == {}
    assert ignoradas == 1


def test_acepta_partidas_de_lichess(tmp_path):
    pgn = ('[Event "x"]\n[GameId "abc"]\n[Annotator "lichess.org"]\n\n'
           '1. e4 { [%eval 0.30] } 1... e5 { [%eval 0.25] } 1-0\n')
    (tmp_path / "lichess.pgn").write_text(pgn, encoding="utf-8")
    partidas, ignoradas = val.leer([str(tmp_path)])
    assert list(partidas) == ["abc"]
    assert ignoradas == 0
