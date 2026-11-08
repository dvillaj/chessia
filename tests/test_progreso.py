# -*- coding: utf-8 -*-
"""Pruebas de la barra de progreso de analizar_local. No necesitan python-chess ni Stockfish."""
import analizar_local as al


def test_formatear_tiempo():
    assert al.formatear_tiempo(0) == "0:00:00"
    assert al.formatear_tiempo(65) == "0:01:05"
    assert al.formatear_tiempo(3 * 3600 + 7 * 60 + 9) == "3:07:09"


def test_texto_al_empezar_no_tiene_eta():
    p = al.Progreso(10, 4, terminal=False)
    txt = p.texto(0)
    assert "0/10" in txt and "0.0%" in txt and "ETA --:--:--" in txt and "en curso 4" in txt
    assert "#" not in txt


def test_texto_a_la_mitad_y_al_final():
    p = al.Progreso(10, 4, terminal=False)
    p.t0 -= 100
    mitad = p.texto(5)
    assert "5/10" in mitad and "50.0%" in mitad and "ETA 0:01:40" in mitad
    assert mitad.count("#") == al.Progreso.ANCHO // 2
    final = p.texto(10)
    assert "100.0%" in final and "en curso 0" in final and final.count("#") == al.Progreso.ANCHO


def test_en_curso_no_supera_lo_que_queda():
    assert "en curso 2" in al.Progreso(10, 6, terminal=False).texto(8)


def test_sin_terminal_no_dibuja_la_barra(capsys):
    p = al.Progreso(5, 2, terminal=False)
    p.actualizar(1)
    p.cerrar()
    assert capsys.readouterr().out == ""
    p.linea("OK algo", 1)
    assert capsys.readouterr().out == "OK algo\n"


def test_con_terminal_la_linea_no_deja_restos(capsys):
    p = al.Progreso(5, 2, terminal=True)
    p.actualizar(1)
    p.linea("OK algo", 1)
    p.cerrar()
    out = capsys.readouterr().out
    assert out.startswith("\r[")
    antes, despues = out.split("OK algo\n")
    assert antes.endswith("\r")
    assert despues.startswith("\r[") and despues.endswith("\n")
    assert " " * 20 in antes
