import io
import json
import os

import pytest

import perfiles as p

PLANTILLA = "# Perfil: {usuario}\nObjetivo {objetivo} en {ritmo}\n"


def test_separar_y_componer_son_inversos():
    cab = {"usuario": "ana", "ritmo": "600+0", "elo": "1500", "objetivo": "1800", "extra": "x"}
    texto = p.componer(cab, "# Cuerpo\n")
    cab2, cuerpo = p.separar(texto)
    assert cab2 == cab
    assert cuerpo == "# Cuerpo\n"


def test_separar_sin_cabecera():
    assert p.separar("# Solo cuerpo\n") == ({}, "# Solo cuerpo\n")


def test_separar_admite_bom_y_saltos_windows():
    cab, cuerpo = p.separar("﻿---\r\nusuario: ana\r\nelo: 1500\r\n---\r\nhola\r\n")
    assert cab == {"usuario": "ana", "elo": "1500"}
    assert cuerpo == "hola\r\n"


@pytest.mark.parametrize("ritmo,tipo", [("60+0", "bullet"), ("180+0", "blitz"), ("180+2", "blitz"),
                                         ("600+0", "rapid"), ("900+10", "rapid"), ("1800+0", "classical")])
def test_tipo_de_ritmo(ritmo, tipo):
    assert p.tipo_de_ritmo(ritmo) == tipo


@pytest.mark.parametrize("malo", ["", "10", "10+", "diez+0", None])
def test_ritmo_invalido(malo):
    with pytest.raises(ValueError):
        p.tipo_de_ritmo(malo)


@pytest.mark.parametrize("malo", ["", "../x", "a b", "a/b", None])
def test_usuario_invalido_no_sale_de_la_carpeta(malo, tmp_path):
    with pytest.raises(ValueError):
        p.ruta_perfil(malo, str(tmp_path))


def test_rating_de_respuesta():
    assert p.rating_de_respuesta({"perfs": {"rapid": {"rating": 1593.4}}}, "rapid") == 1593
    assert p.rating_de_respuesta({"perfs": {}}, "rapid") is None
    assert p.rating_de_respuesta({}, "rapid") is None


def _plantilla(tmp_path):
    f = tmp_path / "_plantilla.md"
    f.write_text(PLANTILLA, encoding="utf-8")
    return str(f)


def test_crear_rellena_cabecera_y_plantilla(tmp_path):
    ruta = p.crear("ana", "900+10", "1800", carpeta=str(tmp_path), plantilla=_plantilla(tmp_path))
    cab = p.leer("ana", str(tmp_path))
    assert cab == {"usuario": "ana", "ritmo": "900+10", "objetivo": "1800"}
    assert "Objetivo 1800 en 900+10" in open(ruta, encoding="utf-8").read()


def test_crear_no_pisa_un_perfil_existente(tmp_path):
    pl = _plantilla(tmp_path)
    p.crear("ana", "600+0", "1800", carpeta=str(tmp_path), plantilla=pl)
    with pytest.raises(FileExistsError):
        p.crear("ana", "600+0", "1900", carpeta=str(tmp_path), plantilla=pl)


def test_crear_valida_objetivo(tmp_path):
    with pytest.raises(ValueError):
        p.crear("ana", "600+0", "mucho", carpeta=str(tmp_path), plantilla=_plantilla(tmp_path))


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_actualizar_elo_guarda_en_la_cabecera_sin_tocar_el_cuerpo(tmp_path):
    p.crear("ana", "600+0", "1800", carpeta=str(tmp_path), plantilla=_plantilla(tmp_path))
    ruta = p.ruta_perfil("ana", str(tmp_path))
    antes = p.separar(open(ruta, encoding="utf-8").read())[1]
    abrir = lambda req, timeout: _Resp(json.dumps({"perfs": {"rapid": {"rating": 1593.23}}}).encode())
    assert p.actualizar_elo("ana", str(tmp_path), abrir) == 1593
    cab, cuerpo = p.separar(open(ruta, encoding="utf-8").read())
    assert cab["elo"] == "1593" and cab["objetivo"] == "1800" and "elo_fecha" in cab
    assert cuerpo == antes


def test_actualizar_elo_sin_red_no_rompe_ni_cambia_nada(tmp_path):
    import urllib.error
    p.crear("ana", "600+0", "1800", carpeta=str(tmp_path), plantilla=_plantilla(tmp_path))
    ruta = p.ruta_perfil("ana", str(tmp_path))
    antes = open(ruta, encoding="utf-8").read()

    def abrir(req, timeout):
        raise urllib.error.URLError("sin red")

    assert p.actualizar_elo("ana", str(tmp_path), abrir) is None
    assert open(ruta, encoding="utf-8").read() == antes


def test_actualizar_elo_sin_perfil_devuelve_none(tmp_path):
    assert p.actualizar_elo("nadie", str(tmp_path)) is None
