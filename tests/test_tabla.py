import os

import metricas_pgn as m


def test_ruta_tabla_por_defecto_junto_al_csv():
    csv = os.path.join("progreso", "progreso_ana.csv")
    assert m.ruta_tabla(None, csv, "ana") == os.path.join("progreso", "tabla_ana.md")


def test_ruta_tabla_explicita_manda():
    assert m.ruta_tabla("otra/t.md", "progreso/progreso_ana.csv", "ana") == "otra/t.md"


def test_ruta_tabla_sin_carpeta_en_el_csv():
    assert m.ruta_tabla(None, "progreso_ana.csv", "ana") == "tabla_ana.md"
