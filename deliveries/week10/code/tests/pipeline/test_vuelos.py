"""Los vuelos del pipeline (decisión 0016): las rutas desde Lima, la banda del pasaje y el viaje
en avión más rápido de puerta a puerta. Con tablas de juguete; las de referencia se revisan
aparte."""

import numpy as np
import pandas as pd
import pytest

from pipeline import vuelos
from pipeline.maestro import REFERENCIA

RUTAS = pd.DataFrame(
    {
        "desde": ["LIM", "LIM", "LIM"],
        "hasta": ["CUZ", "AQP", "IQT"],
        "minutos": [80, 90, 110],
        "tarifa_desde_usd": [45.0, 72.0, None],
        "fuente_tarifa": ["Sky", "Sky", "Sin tarifa publicada"],
    }
)


def test_el_pasaje_es_una_banda_desde_la_tarifa_mas_baja_publicada():
    soles = vuelos.rutas_en_soles(RUTAS).set_index("hasta")
    assert soles.loc["CUZ", "tarifa_minima"] == round(45 * vuelos.TIPO_DE_CAMBIO)
    assert soles.loc["CUZ", "tarifa_central"] == round(45 * vuelos.TIPO_DE_CAMBIO * 1.5)
    assert soles.loc["CUZ", "tarifa_maxima"] == round(45 * vuelos.TIPO_DE_CAMBIO * 2.2)
    # Sin tarifa publicada, la mediana de las demás: (45 + 72) / 2.
    assert soles.loc["IQT", "tarifa_minima"] == round(58.5 * vuelos.TIPO_DE_CAMBIO)
    assert soles["tarifa_publicada"].tolist() == [True, True, False]


def test_entre_dos_aeropuertos_que_no_son_lima_se_vuela_con_escala_en_lima():
    minutos, caminos = vuelos.vuelos_entre(RUTAS, ["LIM", "CUZ", "AQP", "TRU"])
    assert minutos[0, 1] == minutos[1, 0] == 80 and caminos[0][1] == ["LIM", "CUZ"]
    assert minutos[1, 2] == 80 + vuelos.ESCALA_MIN + 90 and caminos[1][2] == ["CUZ", "LIM", "AQP"]
    # Sin ruta (TRU no está en la tabla de juguete) o al mismo aeropuerto, no se vuela.
    assert np.isinf(minutos[0, 3]) and np.isinf(minutos[1, 1]) and caminos[1][1] == []


def test_el_viaje_en_avion_mas_rapido_suma_tierra_aeropuertos_y_vuelo():
    origenes = pd.DataFrame({"id": ["lima"]})
    bases = pd.DataFrame({"polo": [3, 4]})
    aeropuertos = pd.DataFrame({"iata": ["LIM", "CUZ", "AQP"]})
    # Del origen a cada aeropuerto y de cada aeropuerto a cada base: minutos y km por tierra.
    ida = {"minutos": np.array([[25.0, np.nan, np.nan]]), "km": np.array([[12.0, np.nan, np.nan]])}
    llegada = {
        "minutos": np.array([[np.nan, np.nan], [15.0, 600.0], [700.0, 200.0]]),
        "km": np.array([[np.nan, np.nan], [6.0, 300.0], [400.0, 150.0]]),
    }
    for d in (ida, llegada):
        d["km_tren"] = np.zeros_like(d["km"])
        d["km_bote"] = np.zeros_like(d["km"])
    hecho = vuelos.mejores_vuelos(origenes, bases, aeropuertos, RUTAS, ida, llegada).set_index("polo")
    en_aeropuertos = vuelos.LLEGAR_ANTES_MIN + vuelos.SALIR_DEL_AEROPUERTO_MIN
    assert hecho.loc[3, "aeropuertos"] == "LIM-CUZ"
    assert hecho.loc[3, "minutos"] == 25 + en_aeropuertos + 80 + 15
    assert (hecho.loc[3, "km"], hecho.loc[3, "km_hasta_aeropuerto"]) == (18.0, 12.0)
    # A la base 4 conviene Arequipa: 90 de vuelo y 200 por tierra, contra 80 y 600 por el Cusco.
    assert hecho.loc[4, "aeropuertos"] == "LIM-AQP"
    assert hecho.loc[4, "minutos"] == 25 + en_aeropuertos + 90 + 200
    assert (hecho.loc[4, "minutos_vuelo"], hecho.loc[4, "minutos_desde_aeropuerto"]) == (90.0, 200.0)


def test_las_tablas_de_referencia_se_corresponden():
    aeropuertos = vuelos.leer_aeropuertos()
    rutas = pd.read_csv(REFERENCIA / "rutas_aereas.csv", sep=";")
    assert aeropuertos["iata"].is_unique and set(rutas["hasta"]) <= set(aeropuertos["iata"])
    assert (rutas["desde"] == vuelos.HUB).all() and rutas["hasta"].is_unique
    assert rutas["minutos"].between(30, 180).all()
    # Todos en el Perú: entre la frontera con Ecuador y la de Chile.
    assert aeropuertos["lat"].between(-18.5, 0.0).all() and aeropuertos["lon"].between(-81.5, -68.5).all()
    con_tarifa = rutas.dropna(subset=["tarifa_desde_usd"])
    assert con_tarifa["tarifa_desde_usd"].between(20, 300).all()
    assert rutas.loc[rutas["tarifa_desde_usd"].isna(), "fuente_tarifa"].str.startswith("Sin tarifa").all()


@pytest.mark.parametrize("columna", ["minutos", "km", "km_hasta_aeropuerto", "minutos_vuelo"])
def test_los_viajes_procesados_no_traen_negativos(columna):
    ruta = vuelos.PROCESADOS / "vuelos_origen_base.csv"
    if not ruta.exists():
        pytest.skip("sin data/procesados/vuelos_origen_base.csv")
    tabla = pd.read_csv(ruta, sep=";", encoding="utf-8-sig")
    assert (tabla[columna] >= 0).all()
