"""Fechas de los acontecimientos a partir de su regla."""

from datetime import date

import pytest

from dreemgo.calendario import Regla, pascua


@pytest.mark.parametrize(
    ("anio", "domingo"),
    [
        (2000, date(2000, 4, 23)),
        (2019, date(2019, 4, 21)),
        (2024, date(2024, 3, 31)),
        (2025, date(2025, 4, 20)),
        (2026, date(2026, 4, 5)),
        (2027, date(2027, 3, 28)),
        (2038, date(2038, 4, 25)),  # la Pascua más tardía posible
    ],
)
def test_pascua(anio, domingo):
    assert pascua(anio) == domingo


@pytest.mark.parametrize(
    ("regla", "anio", "inicio", "fin"),
    [
        ("fija 07-25", 2026, date(2026, 7, 25), date(2026, 7, 25)),
        ("fija 07-24..07-30", 2026, date(2026, 7, 24), date(2026, 7, 30)),
        ("fija 12-25..01-06", 2026, date(2026, 12, 25), date(2027, 1, 6)),
        ("fija 02-29", 2027, date(2027, 2, 28), date(2027, 2, 28)),  # año común
        ("pascua -7..0", 2026, date(2026, 3, 29), date(2026, 4, 5)),  # Semana Santa
        ("pascua -6", 2026, date(2026, 3, 30), date(2026, 3, 30)),  # Señor de los Temblores, Lunes Santo
        ("pascua 60..63", 2026, date(2026, 6, 4), date(2026, 6, 7)),  # Corpus Christi
        ("nesimo 04 2 dom", 2026, date(2026, 4, 12), date(2026, 4, 12)),
        ("nesimo 10 -1 dom 3", 2026, date(2026, 10, 25), date(2026, 10, 28)),
        ("mes 07", 2026, date(2026, 7, 1), date(2026, 7, 31)),
        ("mes 11..02", 2026, date(2026, 11, 1), date(2027, 2, 28)),
    ],
)
def test_fechas(regla, anio, inicio, fin):
    assert Regla(regla).fechas(anio) == (inicio, fin)


def test_la_edicion_que_cae_en_el_viaje():
    fin_de_anio = Regla("fija 12-25..01-06")
    assert fin_de_anio.cae_en(date(2027, 1, 2), date(2027, 1, 8)) == (date(2026, 12, 25), date(2027, 1, 6))
    assert Regla("fija 01-01").cae_en(date(2026, 12, 28), date(2027, 1, 3)) == (date(2027, 1, 1), date(2027, 1, 1))
    assert Regla("fija 07-25").cae_en(date(2026, 8, 1), date(2026, 8, 6)) is None


@pytest.mark.parametrize("texto", ["fija 13-01", "pascua", "nesimo 04 6 dom", "mes 7", "cada año"])
def test_regla_invalida(texto):
    with pytest.raises(ValueError, match="regla de fecha"):
        Regla(texto)
