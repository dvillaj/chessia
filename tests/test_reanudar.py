# -*- coding: utf-8 -*-
"""Reanudacion del analisis local: no se repite lo ya analizado con el mismo motor y limite. Sin motor."""
from argparse import Namespace

import analizar_local as al

ANOTADOR = "analizar_local.py con Stockfish 19, profundidad 20"
JUGADAS = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"
JUGADAS_ANALIZADAS = ("1. e4 { [%eval 0.30] [%clk 0:15:00] } 1... e5 { [%eval 0.25] [%clk 0:15:00] } "
                      "2. Nf3 { [%eval 0.30] } 2... Nc6 { [%eval 0.28] } 3. Bb5 { [%eval 0.31] } 3... a6 { [%eval 0.35] } 1-0")


def partida(gid, anotador=None, jugadas=JUGADAS, extra=""):
    cab = [("Event", "x"), ("Site", f"https://lichess.org/{gid}"), ("Result", "1-0"), ("GameId", gid)]
    if anotador:
        cab.append(("Annotator", anotador))
    return "".join(f'[{k} "{v}"]\n' for k, v in cab) + f"\n{extra}{jugadas}\n\n"


def preparar(tmp_path, entrada, salida=None):
    (tmp_path / "entrada.pgn").write_text("".join(entrada), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    if salida is not None:
        (out / "entrada_analizado.pgn").write_text("".join(salida), encoding="utf-8")
    return [str(tmp_path / "entrada.pgn")], Namespace(salida=str(out), reanalizar=False, maximo=0)


def acciones(plan):
    return [accion for _, items in plan for _, accion in items]


def test_reutiliza_lo_ya_analizado_con_el_mismo_ajuste(tmp_path):
    ficheros, args = preparar(
        tmp_path,
        [partida("AAAA1111"), partida("BBBB2222"), partida("CCCC3333")],
        [partida("AAAA1111", ANOTADOR, JUGADAS_ANALIZADAS)],
    )
    plan, a_analizar, reanudadas, otro = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["reanudada", "analizar", "analizar"]
    assert reanudadas == 1 and otro == 0
    assert [dict(p["cabeceras"])["GameId"] for p in a_analizar] == ["BBBB2222", "CCCC3333"]
    reutilizada = plan[0][1][0][0]
    assert "%eval" in reutilizada["texto"] and dict(reutilizada["cabeceras"])["Annotator"] == ANOTADOR


def test_una_partida_cortada_por_el_apagado_se_rehace(tmp_path):
    cortada = partida("AAAA1111", ANOTADOR, "1. e4 { [%eval 0.30] } 1... e5 { [%eval 0.25] } 2. Nf3 { [%ev")
    ficheros, args = preparar(tmp_path, [partida("AAAA1111")], [cortada])
    plan, a_analizar, reanudadas, _ = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["analizar"] and reanudadas == 0


def test_sin_resultado_al_final_no_se_reutiliza(tmp_path):
    sin_resultado = partida("AAAA1111", ANOTADOR, JUGADAS_ANALIZADAS.replace(" 1-0", ""))
    ficheros, args = preparar(tmp_path, [partida("AAAA1111")], [sin_resultado])
    plan, _, reanudadas, _ = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["analizar"] and reanudadas == 0


def test_otro_motor_o_limite_se_rehace_y_se_avisa(tmp_path):
    ficheros, args = preparar(
        tmp_path, [partida("AAAA1111")],
        [partida("AAAA1111", "analizar_local.py con Stockfish 19, profundidad 16", JUGADAS_ANALIZADAS)],
    )
    plan, _, reanudadas, otro = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["analizar"] and reanudadas == 0 and otro == 1


def test_mismo_id_con_otras_jugadas_no_se_reutiliza(tmp_path):
    otras = "1. d4 d5 2. c4 e6 1-0"
    ficheros, args = preparar(tmp_path, [partida("AAAA1111")], [partida("AAAA1111", ANOTADOR, otras)])
    plan, _, reanudadas, _ = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["analizar"] and reanudadas == 0


def test_lo_reutilizado_no_cuenta_para_el_maximo(tmp_path):
    ficheros, args = preparar(
        tmp_path,
        [partida("AAAA1111"), partida("BBBB2222"), partida("CCCC3333")],
        [partida("AAAA1111", ANOTADOR, JUGADAS_ANALIZADAS)],
    )
    args.maximo = 1
    plan, a_analizar, reanudadas, _ = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["reanudada", "analizar", "copiar"] and reanudadas == 1 and len(a_analizar) == 1


def test_sin_fichero_previo_se_analiza_todo(tmp_path):
    ficheros, args = preparar(tmp_path, [partida("AAAA1111"), partida("BBBB2222")])
    plan, a_analizar, reanudadas, otro = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["analizar", "analizar"] and reanudadas == 0 and otro == 0 and len(a_analizar) == 2


def test_lo_que_ya_trae_analisis_de_lichess_se_copia_aunque_haya_previa(tmp_path):
    con_eval = partida("AAAA1111", "lichess.org", JUGADAS_ANALIZADAS)
    ficheros, args = preparar(tmp_path, [con_eval], [partida("AAAA1111", ANOTADOR, JUGADAS_ANALIZADAS)])
    plan, _, reanudadas, _ = al.planificar(ficheros, args, ANOTADOR)
    assert acciones(plan) == ["ya_analizada"] and reanudadas == 0
