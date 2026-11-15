"""El kit corto para calificadores de fuera y la comparación con el equipo (decisión 0033)."""

import csv

from evaluacion import externos, kit_externo
from evaluacion.informe import CARPETA, leer_clave


def test_el_kit_corto_son_siempre_las_mismas_10_consultas():
    assert kit_externo.elegidas() == [3, 14, 15, 18, 21, 24, 29, 31, 33, 39]


def test_el_cuadernillo_corto_deja_solo_esas_consultas_y_guarda_aparte():
    html = kit_externo.recortar((CARPETA / "cuadernillo.html").read_text(encoding="utf-8"), [3, 14])
    assert html.count("<section class='consulta'") == 2 and "id='c3'" in html and "id='c1'" not in html
    assert "dreemgo-externos-" in html and '"externo_" + quien()' in html


def test_si_los_de_fuera_ponen_2_a_todo_el_equipo_queda_por_debajo(tmp_path):
    viajes, _ = leer_clave(CARPETA / "clave.csv")
    consultas = set(kit_externo.elegidas())
    for quien in ("AA", "BB"):
        with open(tmp_path / f"externo_{quien}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["consulta", "opcion", "zona", "calificacion", "comentario"])
            for v in viajes:
                if v.consulta in consultas:
                    w.writerow([v.consulta, v.opcion, v.zona, 2, ""])
    r = externos.calcular(CARPETA / "clave.csv", CARPETA / "calificaciones", tmp_path)
    assert r["de_fuera"] == 2 and r["viajes"] == 50
    assert r["equipo_menos_fuera"]["media"] < 0 and r["equipo_menos_fuera"]["ic95"][1] < 0
    assert r["ndcg3_con_las_notas_de_fuera"]["motor"] == 1.0
