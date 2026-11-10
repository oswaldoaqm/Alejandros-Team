"""El acuerdo entre quienes califican (decisión 0021), contra los ejemplos publicados de Fleiss (1971) y de
Krippendorff (2011)."""

import pytest

from evaluacion import acuerdo


def test_el_kappa_de_fleiss_da_el_del_ejemplo_de_fleiss_1971():
    """Diez sujetos, catorce calificadores y cinco categorías: κ = 0,210."""
    conteos = [
        [0, 0, 0, 0, 14],
        [0, 2, 6, 4, 2],
        [0, 0, 3, 5, 6],
        [0, 3, 9, 2, 0],
        [2, 2, 8, 1, 1],
        [7, 7, 0, 0, 0],
        [3, 2, 6, 3, 0],
        [2, 5, 3, 2, 2],
        [6, 5, 2, 1, 0],
        [0, 2, 2, 3, 7],
    ]
    notas = [[k for k, c in enumerate(fila) for _ in range(c)] for fila in conteos]
    assert acuerdo.kappa_de_fleiss(notas, categorias=range(5)) == pytest.approx(0.2099, abs=1e-4)


def test_el_alfa_de_krippendorff_da_el_del_ejemplo_de_krippendorff_2011():
    """Cuatro codificadores, doce unidades y notas que faltan: 0,743 nominal y 0,815 ordinal."""
    a = [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None]
    b = [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3]
    c = [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None]
    d = [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None]
    filas = [list(t) for t in zip(a, b, c, d, strict=True)]
    assert acuerdo.alfa_de_krippendorff(filas, "nominal") == pytest.approx(0.743, abs=1e-3)
    assert acuerdo.alfa_de_krippendorff(filas, "ordinal") == pytest.approx(0.815, abs=1e-3)


def test_si_todos_coinciden_los_dos_dan_uno():
    notas = [[2, 2, 2, 2], [0, 0, 0, 0], [1, 1, 1, 1]]
    assert acuerdo.kappa_de_fleiss(notas) == pytest.approx(1)
    assert acuerdo.alfa_de_krippendorff(notas) == pytest.approx(1)


def test_el_kappa_pide_las_mismas_notas_en_cada_viaje():
    with pytest.raises(ValueError, match="las mismas en todos"):
        acuerdo.kappa_de_fleiss([[2, 2, 1], [1, 1]])
