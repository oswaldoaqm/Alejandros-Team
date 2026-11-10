"""Calibración de la red vial sobre datos sintéticos y tablas pequeñas."""

import numpy as np
import pandas as pd
import pytest

from pipeline import red_calibracion as calibracion
from pipeline.red_vial import BANDAS, VIALES


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


# --- Las ciudades (decisión 0025) ---------------------------------------------------------


def test_el_ajuste_recupera_el_recargo_de_las_ciudades_medianas():
    verdad = {**calibracion.INICIALES, "troncal": 0.9, "por_viaje": 8.0, "recargo_mediana": 1.2}
    tabla = _tabla_sintetica()
    tabla["km_mediana"] = np.random.default_rng(2).exponential(3, len(tabla))
    tabla["min_ciudad"] = np.random.default_rng(3).exponential(10, len(tabla))  # fijos: no se ajustan
    tabla["acceso_min"] = calibracion.predecir(tabla, verdad)
    ajuste = calibracion.ajustar(tabla)
    assert ajuste["recargo_mediana"] == pytest.approx(1.2, rel=0.05)
    assert ajuste["troncal"] == pytest.approx(0.9, rel=0.05)


def _ciudad_grande():
    """Una cuadrícula de 11 × 11 km con una calle cada 100 m (unos 118 km² de mancha): con las bandas de verdad,
    una ciudad grande. La carretera sale de su esquina noreste hacia el norte."""
    from tests.pipeline.test_red_vial import _grilla_con_ruta

    red = _grilla_con_ruta(n=111, paso_km=0.1, ruta_km=30)
    assert BANDAS[red.bandas[0]] == "grande"
    return red


def test_los_pisos_de_la_ciudad_llegan_a_lo_que_mide_tomtom(monkeypatch):
    red = _ciudad_grande()
    tomtom = pd.DataFrame(
        [
            {
                "ciudad": "Prueba",
                "banda": "grande",
                "uso": "ajuste",
                "lat": -11.95,
                "lon": -76.95,
                "autopista_kmh": 30.0,
                "meta_min_10km": 40.0,
            }
        ]
    )
    monkeypatch.setattr(calibracion, "trafico", lambda: tomtom)
    monkeypatch.setattr(calibracion, "PARES_POR_CIUDAD", 40)
    ritmos = {**calibracion.INICIALES, "local": 2.0}
    pisos = calibracion.pisos_de_ciudad(red, ritmos)
    assert pisos["piso_grande_rapidas"] == pytest.approx(2.0)
    medido = calibracion.ritmos_en_ciudades(red, {**ritmos, **pisos}, tomtom)
    assert medido.loc[0, "banda"] == "grande" and medido.loc[0, "pares"] >= 20
    assert medido.loc[0, "min_10km"] == pytest.approx(40.0, rel=calibracion.TOLERANCIA_CIUDAD)
    # Una ciudad de ajuste que la red no reconoce en su banda es un error, no un piso inventado.
    otra = tomtom.assign(banda="metropoli")
    monkeypatch.setattr(calibracion, "trafico", lambda: otra)
    with pytest.raises(ValueError, match="no cae en su banda"):
        calibracion.pisos_de_ciudad(red, ritmos)


def test_lo_que_se_ajusta_explica_lo_que_rutea_la_red():
    """Con las columnas de componer, predecir da los mismos minutos que el camino más rápido por la red."""
    from pipeline.red_vial import Ruteador, minutos_por_arista

    red = _ciudad_grande()
    ritmos = {**calibracion.INICIALES, "local": 2.0, "piso_grande_calles": 4.0, "piso_grande_rapidas": 2.0}
    pares = pd.DataFrame(
        {
            "lat_desde": [-11.95, -11.99],
            "lon_desde": [-76.95, -76.99],
            "lat": [-11.70, -11.80],
            "lon": [-76.9012, -76.9012],
            "acceso_min": [100.0, 100.0],
        }
    )
    tabla = calibracion.componer(red, ritmos, pares)
    assert (tabla["min_ciudad"] > 0).all() and (tabla["km_ciudad"] > 0).all()
    assert (tabla["km_primaria"] > 0).all()  # la carretera, fuera de la ciudad, sigue en sus km por clase
    ruteador = Ruteador(red, minutos_por_arista(red, ritmos), vertices_minimos=4)
    inicio, m_ini, _ = ruteador.ubicar(pares["lat_desde"].to_numpy(), pares["lon_desde"].to_numpy())
    fin, m_fin, _ = ruteador.ubicar(pares["lat"].to_numpy(), pares["lon"].to_numpy())
    en_red = [ruteador.minutos_desde([int(a)])[0][int(b)] for a, b in zip(inicio, fin, strict=True)]
    fuera = 1.3 * (m_ini + m_fin) / 1000 * ritmos["trocha"]
    esperado = np.array(en_red) + ritmos["por_viaje"] + fuera
    assert calibracion.predecir(tabla, ritmos) == pytest.approx(esperado, rel=1e-6)
