"""Las métricas de los tres viajes de cada sistema (decisión 0021), con cuentas hechas a mano."""

import pytest

from evaluacion import metricas


def test_las_metricas_de_tres_viajes():
    todas = [2, 1.5, 1, 0, 0]
    assert metricas.ndcg([2, 1.5, 1], todas) == pytest.approx(1)
    assert metricas.ndcg([0, 0, 2], todas) == pytest.approx((2 / 2) / (2 + 1.5 / 1.585 + 1 / 2), abs=1e-3)
    assert metricas.ndcg([0, 0, 0], [0, 0, 0]) == 0
    assert metricas.precision([2, 1.5, 1.25]) == pytest.approx(2 / 3)
    assert metricas.rango_reciproco([1, 0, 1.75]) == pytest.approx(1 / 3)
    assert metricas.no_encajan([0.25, 0.5, 2]) == pytest.approx(1 / 3)


def test_el_intervalo_de_una_diferencia_constante_es_esa_diferencia():
    assert metricas.intervalo([0.2] * 10, veces=200) == pytest.approx((0.2, 0.2))


def test_la_comparacion_cuenta_cuantas_gana_y_cuantas_pierde():
    a = [1.0, 0.5, 0.8, 0.9, 0.7, 0.6, 1.0, 0.4]
    b = [0.5, 0.5, 0.6, 0.8, 0.2, 0.6, 0.9, 0.1]
    c = metricas.comparar(a, b)
    assert (c["gana"], c["pierde"], c["empata"]) == (6, 0, 2)
    assert c["media"] == pytest.approx(0.2125) and c["ic95"][0] > 0 and c["wilcoxon_p"] < 0.05
