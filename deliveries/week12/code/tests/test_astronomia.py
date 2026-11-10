"""El Sol y la Luna de cada noche (dreemgo/astronomia.py), contra fechas que no dependen del
algoritmo: los eclipses de 2026 y 2027 caen en luna nueva o llena."""

from datetime import UTC, date, datetime, time

import pytest

from dreemgo import astronomia

CUSCO = (-13.5167, -71.9787)
LIMA = (-12.05, -77.04)


@pytest.mark.parametrize(
    "instante",
    [
        datetime(2026, 2, 17, 12, 1, tzinfo=UTC),  # eclipse anular de Sol
        datetime(2026, 8, 12, 17, 46, tzinfo=UTC),  # eclipse total de Sol
        datetime(2027, 8, 2, 10, 7, tzinfo=UTC),  # eclipse total de Sol
    ],
)
def test_en_un_eclipse_de_sol_la_luna_esta_nueva(instante):
    parte, _ = astronomia.iluminada(instante)
    assert parte < 0.002


@pytest.mark.parametrize(
    "instante",
    [
        datetime(2026, 3, 3, 11, 33, tzinfo=UTC),  # eclipse total de Luna
        datetime(2026, 8, 28, 4, 13, tzinfo=UTC),  # eclipse parcial de Luna
    ],
)
def test_en_un_eclipse_de_luna_la_luna_esta_llena(instante):
    parte, _ = astronomia.iluminada(instante)
    assert parte > 0.998


def test_la_luna_nueva_del_mes_es_la_noche_mas_cercana():
    # La de febrero de 2026 es el 17 al mediodía de Greenwich: la noche más cercana es la del 16,
    # cuya medianoche en el Perú son las 05:00 del 17.
    assert astronomia.lunas_nuevas(2026, 2) == [date(2026, 2, 16)]
    assert astronomia.lunas_nuevas(2026, 8) == [date(2026, 8, 12)]
    # Agosto de 2027 tiene dos.
    assert astronomia.lunas_nuevas(2027, 8) == [date(2027, 8, 1), date(2027, 8, 31)]


@pytest.mark.parametrize(
    "fecha, oscurece, aclara",
    [
        (date(2026, 6, 21), time(19, 10), time(5, 10)),  # invierno: oscurece temprano y aclara tarde
        (date(2026, 12, 21), time(19, 50), time(4, 25)),
    ],
)
def test_en_lima_oscurece_y_aclara_cuando_el_sol_baja_de_18_grados(fecha, oscurece, aclara):
    noche = astronomia.noche(fecha, *LIMA)
    assert (noche.oscurece, noche.aclara) == (oscurece, aclara)
    assert noche.oscurece.minute % 5 == 0 and noche.aclara.minute % 5 == 0


def test_en_luna_nueva_toda_la_noche_es_sin_luna():
    noche = astronomia.noche(date(2027, 7, 4), *CUSCO)
    assert noche.luna < astronomia.LUNA_QUE_NO_ESTORBA
    assert noche.horas_sin_luna == noche.horas_oscuras > 9


def test_en_cuarto_creciente_la_luna_se_pone_a_medianoche():
    noche = astronomia.noche(date(2027, 7, 10), *CUSCO)
    assert noche.creciente and 0.4 < noche.luna < 0.6
    assert noche.luna_sale is None
    assert noche.luna_se_pone >= time(23, 30) or noche.luna_se_pone <= time(0, 50)
    assert 4 < noche.horas_sin_luna < 6


def test_en_cuarto_menguante_la_luna_sale_cerca_de_medianoche():
    noche = astronomia.noche(date(2027, 7, 25), *CUSCO)
    assert not noche.creciente and 0.4 < noche.luna < 0.65
    assert noche.luna_se_pone is None and time(22, 30) <= noche.luna_sale <= time(23, 59)


def test_en_luna_llena_no_hay_horas_sin_luna():
    noche = astronomia.noche(date(2027, 7, 18), *CUSCO)
    assert noche.luna > 0.98
    assert noche.horas_sin_luna == 0
    assert noche.luna_sale is None and noche.luna_se_pone is None  # está arriba toda la noche


def test_la_misma_noche_da_lo_mismo():
    assert astronomia.noche(date(2027, 1, 9), *LIMA) == astronomia.noche(date(2027, 1, 9), *LIMA)
