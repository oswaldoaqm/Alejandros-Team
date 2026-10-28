"""Filas reales del inventario de MINCETUR (tests/fixtures/inventario_muestra.csv).

La muestra tiene siete filas del corte 20260929 tal cual, la 257 con LATITUD y LONGITUD
puestas en su lugar (para probar el caso sin intercambio) y la 11287 del corte
20260831, cuando los acontecimientos aún no tenían coordenadas.
"""

from pathlib import Path

import pandas as pd
import pytest

from pipeline.inventario import leer_coordenada, leer_inventario

MUESTRA = Path(__file__).parents[1] / "fixtures" / "inventario_muestra.csv"


@pytest.fixture(scope="module")
def inventario():
    return leer_inventario(MUESTRA).set_index("codigo")


def test_lee_windows_1252(inventario):
    assert inventario.loc[935, "nombre"] == "Puente Colgante De Q’Eswachaka"  # apóstrofo ’ y espacios de más
    assert inventario.loc[364, "nombre"] == "Complejo Arqueológico Monumental “Narihualá”"


def test_corrige_latitud_y_longitud_intercambiadas(inventario):
    caral = inventario.loc[1237]
    assert (caral.lat, caral.lon, caral.coordenada) == (
        pytest.approx(-10.892818, abs=1e-6),
        pytest.approx(-77.523228, abs=1e-6),
        "intercambiada",
    )


def test_respeta_la_fila_que_viene_bien(inventario):
    paracas = inventario.loc[257]
    assert (paracas.lat, paracas.lon, paracas.coordenada) == (
        pytest.approx(-13.855618, abs=1e-6),
        pytest.approx(-76.337225, abs=1e-6),
        "correcta",
    )


def test_repara_el_punto_decimal_corrido(inventario):
    tauca = inventario.loc[14707]  # LATITUD = -780558.0373798
    assert (tauca.lat, tauca.lon, tauca.coordenada) == (
        pytest.approx(-8.470112, abs=1e-6),
        pytest.approx(-78.0558037, abs=1e-6),
        "reparada",
    )
    assert tauca.latitud_original == "-780558.0373798"  # el valor original se conserva


def test_fila_sin_coordenadas(inventario):
    fila = inventario.loc[11287]
    assert fila.coordenada == "sin_coordenada"
    assert pd.isna(fila.lat) and pd.isna(fila.lon)


def test_categoria_y_tipo(inventario):
    laguna = inventario.loc[22]
    assert (laguna.categoria_num, laguna.categoria, laguna.tipo) == (1, "Sitios naturales", "Cuerpo de Agua")
    assert pd.isna(inventario.loc[14342, "subtipo"])  # la única fila sin subtipo


@pytest.mark.parametrize(
    ("latitud", "longitud", "estado"),
    [
        ("-200", "-300", "invalida"),
        ("", "-77.5", "sin_coordenada"),
        ("abc", "-77.5", "sin_coordenada"),
        ("-12.05", "-77.04", "correcta"),
        ("-77.04", "-12.05", "intercambiada"),
    ],
)
def test_leer_coordenada(latitud, longitud, estado):
    assert leer_coordenada(latitud, longitud).estado == estado
