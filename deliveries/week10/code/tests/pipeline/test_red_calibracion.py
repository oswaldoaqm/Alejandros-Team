"""Calibración de la red vial sobre datos sintéticos y tablas pequeñas."""

import numpy as np
import pandas as pd
import pytest

from pipeline import red_calibracion as calibracion
from pipeline.red_vial import VIALES


def test_clave_de_nombres():
    assert calibracion.clave("Distrito de Cusco") == "cusco"
    assert calibracion.clave("Pariñas") == calibracion.clave("PARINAS") == "parinas"
    assert calibracion.clave("Rupa-Rupa") == "rupa rupa"


def _tabla_sintetica(n=400, semilla=1):
    rng = np.random.default_rng(semilla)
    tabla = pd.DataFrame({f"km_{c}": rng.exponential(8, n) * (rng.random(n) < 0.5) for c in VIALES})
    tabla["km_balsa"] = 0.0
    tabla["km_sin_asfaltar"] = tabla["km_trocha"] * 0.5
    tabla["curvas"] = tabla["km_terciaria"] * 2
    tabla["km_fuera_de_red"] = 0.0
    tabla["traslados"] = 1.0
    return tabla


def test_el_ajuste_recupera_ritmos_conocidos():
    verdad = {**calibracion.INICIALES, "troncal": 0.9, "terciaria": 1.9, "trocha": 3.4, "por_viaje": 8.0}
    tabla = _tabla_sintetica()
    tabla["acceso_min"] = calibracion.predecir(tabla, verdad)
    ajuste = calibracion.ajustar(tabla)
    for p in ("troncal", "terciaria", "trocha", "por_viaje"):
        assert ajuste[p] == pytest.approx(verdad[p], rel=0.05), p


def test_recorridos_de_fichas_solo_por_carretera():
    base = {
        "lat": -12.0,
        "lon": -77.0,
        "acceso_desde": "Lima/Lima/Lima",
        "acceso_km": 20.0,
        "acceso_min": 30.0,
        "caminata_min": 0,
        "acceso_acuatico": False,
        "acceso_aereo": False,
        "coordenada_revisar": False,
        "ultimo_medio": "Taxi",
    }
    maestro = pd.DataFrame(
        [
            {**base, "codigo": 1},
            {**base, "codigo": 2, "caminata_min": 15},
            {**base, "codigo": 3, "acceso_acuatico": True},
            {**base, "codigo": 4, "coordenada_revisar": True},
            {**base, "codigo": 5, "acceso_min": None},
        ]
    )
    r = calibracion.recorridos_de_fichas(maestro)
    assert r["codigo"].tolist() == [1]
    assert (r.loc[0, "region_desde"], r.loc[0, "distrito_desde"]) == ("lima", "lima")


def test_la_partida_es_la_capital_de_osm():
    maestro = pd.DataFrame({"region": ["Piura"], "distrito": ["Pariñas"], "lat": [-4.58], "lon": [-81.27]})
    recorridos = pd.DataFrame({"region_desde": ["piura"], "distrito_desde": ["parinas"]})
    capitales = pd.DataFrame({"distrito": ["Pariñas"], "capital": ["Talara"], "lat": [-4.5797], "lon": [-81.2712]})
    lugares = pd.DataFrame(  # un caserío homónimo más cerca no le gana a la capital
        {"nombre": ["Pariñas", "Pariñas"], "lat": [-4.58, -9.0], "lon": [-81.27, -77.0], "rango": [3, 3]}
    )
    u = calibracion.ubicar_distritos(recorridos, maestro, capitales, lugares)
    assert (u.loc[0, "lat_desde"], u.loc[0, "ubicado_con"]) == (-4.5797, "capital_osm")
    lejos = capitales.assign(lat=-9.0, lon=-77.0)  # a más de 80 km de su distrito: no sirve
    u = calibracion.ubicar_distritos(recorridos, maestro, lejos, lugares.iloc[1:])
    assert u.empty
