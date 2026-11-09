# -*- coding: utf-8 -*-
"""Pruebas de la parte pura de descargar_lichess.py (sin red)."""
import descargar_lichess as d

PLANTILLA = (
    '[Event "rated blitz game"]\n[GameId "GID"]\n[UTCDate "FECHA"]\n[UTCTime "HORA"]\n[Result "1-0"]\n\n'
    '1. e4 { [%clk 0:05:00] } 1... e5 { [%clk 0:05:00] } 1-0\n\n'
)


def partida(gid, fecha, hora):
    return PLANTILLA.replace("GID", gid).replace("FECHA", fecha).replace("HORA", hora)


def test_marca_tiempo_en_utc():
    assert d.marca_tiempo({"UTCDate": "1970.01.01", "UTCTime": "00:00:01"}) == 1000
    assert d.marca_tiempo({}) is None
    assert d.marca_tiempo({"UTCDate": "x", "UTCTime": "y"}) is None


def test_token_desde_env(tmp_path, monkeypatch):
    monkeypatch.delenv("LICHESS_TOKEN", raising=False)
    env = tmp_path / ".env"
    env.write_text('OTRA=1\nexport LICHESS_TOKEN="lip_abc"\n', encoding="utf-8")
    assert d.leer_token(str(env)) == "lip_abc"
    monkeypatch.setenv("LICHESS_TOKEN", "desde_entorno")
    assert d.leer_token(str(env)) == "desde_entorno"


def test_estado_previo_toma_la_ultima_partida(tmp_path):
    (tmp_path / "a.pgn").write_text(
        partida("aaaaaaaa", "2026.11.08", "10:00:00")
        + partida("bbbbbbbb", "2026.11.09", "05:55:51"), encoding="utf-8")
    ids, ultima = d.estado_previo(str(tmp_path))
    assert ids == {"aaaaaaaa", "bbbbbbbb"}
    assert ultima == d.marca_tiempo({"UTCDate": "2026.11.09", "UTCTime": "05:55:51"})


def test_estado_previo_carpeta_vacia(tmp_path):
    assert d.estado_previo(str(tmp_path)) == (set(), None)


def test_stream_separa_partidas_y_detecta_truncadas():
    texto = partida("aaaaaaaa", "2026.11.08", "10:00:00") + \
        '[Event "rated blitz game"]\n[GameId "cortada1"]\n\n1. e4 { [%clk 0:05:00] } 1... e5'
    partidas = list(d.partidas_del_stream(texto.splitlines(keepends=True)))
    assert len(partidas) == 2
    assert d.partida_completa(partidas[0])
    assert not d.partida_completa(partidas[1])


def test_url_incluye_parametros():
    url = d.construir_url("peondeloto", 123, ["rapid", "blitz"], True)
    assert "since=123" in url and "perfType=rapid%2Cblitz" in url and "analysed=true" in url
    assert "clocks=true" in url and "evals=true" in url and "sort=dateAsc" in url
    assert "literate=true" in url
