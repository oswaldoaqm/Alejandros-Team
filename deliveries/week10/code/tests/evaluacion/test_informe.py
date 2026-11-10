"""El informe de la evaluación (decisión 0021), con un kit y calificaciones de juguete: como las descarga el
cuadernillo o como las deja Excel, y uno que no es del kit."""

import csv

import pytest

from dreemgo.motor import datos as artefactos
from evaluacion import informe

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

CLAVE = [
    # consulta, opción, polo, zona, puesto del sistema a, del b
    (1, "A", 70, "Huacho", 1, ""),
    (1, "B", 33, "Huancayo", 2, 1),
    (1, "C", 14, "Huaraz", "", 2),
    (2, "A", 85, "Los Órganos", 1, 1),
]


def _kit(tmp_path, notas: dict[str, list], separador=";", codificacion="utf-8-sig"):
    clave = tmp_path / "clave.csv"
    with open(clave, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";", lineterminator="\n")
        w.writerow(["consulta", "opcion", "polo", "zona", "puesto_a", "puesto_b", "version_datos", "kit"])
        w.writerows([[*fila, "2026.10.8", "x"] for fila in CLAVE])
    carpeta = tmp_path / "calificaciones"
    carpeta.mkdir()
    for quien, valores in notas.items():
        with open(carpeta / f"{quien}.csv", "w", encoding=codificacion, newline="") as fh:
            w = csv.writer(fh, delimiter=separador, lineterminator="\r\n")
            w.writerow(["consulta", "opcion", "zona", "calificacion", "comentario"])
            w.writerows([[c, o, z, v, ""] for (c, o, _, z, *_), v in zip(CLAVE, valores, strict=True)])
    return clave, carpeta


def test_si_todos_coinciden_el_acuerdo_es_total_y_gana_quien_propone_lo_mejor(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 0, 2, 1], "CD": [2, 0, 2, 1], "EF": [2, 0, 2, 1]})
    notas, filas, resumen = informe.calcular(clave, carpeta)
    assert resumen["acuerdo"]["kappa_fleiss"] == pytest.approx(1)
    assert resumen["acuerdo"]["alfa_krippendorff_ordinal"] == pytest.approx(1)
    assert [n["media"] for n in notas] == [2, 0, 2, 1]
    por = {(f["consulta"], f["sistema"]): f for f in filas}
    assert por[(1, "a")]["ndcg3"] == pytest.approx(1 / (1 + 1 / 1.585), abs=1e-3)  # el 2.º era el peor
    assert por[(1, "b")]["ndcg3"] < por[(1, "a")]["ndcg3"] and por[(2, "a")]["ndcg3"] == 1
    assert resumen["cobertura"]["a"]["zonas_distintas"] == 3


def test_lee_lo_que_deja_excel_con_comas_y_en_windows_1252(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 1, 0, 2], "CD": [1, 1, 0, ""]}, separador=",", codificacion="cp1252")
    notas, _, resumen = informe.calcular(clave, carpeta)
    assert notas[3]["zona"] == "Los Órganos" and notas[3]["media"] == 2
    assert resumen["acuerdo"]["viajes_con_todas_las_notas"] == 3


def test_se_niega_si_unas_calificaciones_son_de_otro_kit(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 1, 0, 2], "CD": [1, 1, 0, 2]})
    ruta = carpeta / "CD.csv"
    ruta.write_text(ruta.read_text(encoding="utf-8-sig").replace("Huaraz", "Caraz"), encoding="utf-8-sig")
    with pytest.raises(ValueError, match="CD.csv no es de este kit"):
        informe.calcular(clave, carpeta)
