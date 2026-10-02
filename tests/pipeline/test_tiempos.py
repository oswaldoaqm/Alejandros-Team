"""Tiempos por polo sobre la red de juguete (tests/fixtures/red_mini.osm): una sola búsqueda
por polo da los tiempos entre paradas, la base y los tiempos de la base a cada parada."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline import bases, tiempos
from pipeline.red_vial import (
    CAPAS,
    Ruteador,
    leer_capitales,
    leer_hospedajes,
    leer_lugares,
    leer_red,
    minutos_por_arista,
)

MINI = Path(__file__).parents[1] / "fixtures" / "red_mini.osm"
PARAMETROS = {
    "autopista": 0.8,
    "troncal": 1.0,
    "primaria": 1.2,
    "secundaria": 1.5,
    "terciaria": 1.7,
    "local": 2.0,
    "trocha": 2.5,
    "balsa": 6.0,
    "sin_asfaltar": 0.5,
    "curvas": 0.1,
    "por_viaje": 5.0,
    "tren": 2.0,
    "bote": 3.0,
    "transbordo": 12.0,
    "transbordo_min": 30.0,
}
PARADAS = pd.DataFrame(
    {
        "codigo": [1, 2, 3, 4, 5],
        "polo": [1, 1, 1, 2, -1],
        # 1 y 2 junto a la red; 3 a más de 5 km de ella; 4 solo en su polo; 5 sin polo.
        "lat": [-12.0005, -11.9915, -12.2, -12.0, -12.0],
        "lon": [-77.0, -76.973, -77.3, -76.9555, -76.98],
        "jerarquia": [3, None, 2, 1, 4],
    }
)


@pytest.fixture(scope="module")
def mundo():
    red = leer_red(MINI)
    ruteador = Ruteador(red, minutos_por_arista(red, PARAMETROS), vertices_minimos=4)
    candidatos = bases.candidatos(leer_lugares(MINI), leer_capitales(MINI), leer_hospedajes(MINI))
    pares, elegidas, desde_base = tiempos.recorrer_polos(ruteador, PARAMETROS, PARADAS, candidatos)
    return ruteador, candidatos, pares, elegidas, desde_base


def _directo(ruteador, desde, hasta, medio_hasta=None):
    """Minutos y km de puerta a puerta buscando en toda la red, sin atajos."""
    (vd,), (md,), (cd,) = ruteador.ubicar([desde[0]], [desde[1]])
    (vh,), (mh,), (ch,) = ruteador.ubicar([hasta[0]], [hasta[1]], None if medio_hasta is None else [medio_hasta])
    minutos, km = ruteador.entre([vd], [vh], margen=None)
    en_capa = int(cd > 0) + int(ch > 0)
    m, k = tiempos._puerta_a_puerta(minutos[0, 0], km[0, 0], md + mh, PARAMETROS, en_capa)
    return float(m), float(k)


def test_pares_de_paradas(mundo):
    ruteador, _, pares, _, _ = mundo
    assert set(pares["polo"]) == {1}  # el polo 2 tiene una sola parada; la 5 no tiene polo
    ida = pares.query("desde == 1 and hasta == 2").iloc[0]
    vuelta = pares.query("desde == 2 and hasta == 1").iloc[0]
    esperado = _directo(ruteador, (-12.0005, -77.0), (-11.9915, -76.973))
    assert (ida["minutos"], ida["km"]) == pytest.approx(esperado)
    assert vuelta["minutos"] == pytest.approx(ida["minutos"])  # cada tramo cuesta lo mismo en los dos sentidos
    lejos = pares[(pares["desde"] == 3) | (pares["hasta"] == 3)]
    assert len(lejos) == 4 and lejos[["minutos", "km"]].isna().all().all()


def test_la_base_es_la_de_menor_costo(mundo):
    ruteador, candidatos, _, elegidas, _ = mundo
    assert elegidas["polo"].tolist() == [1, 2]
    assert (elegidas["criterio"] == "carretera").all()
    base = elegidas.set_index("polo").loc[1]
    # El costo de cada candidato con las paradas 1 y 2 (la 3 no cuenta: está lejos de la red).
    puntos = [(-12.0005, -77.0), (-11.9915, -76.973)]
    minutos = np.array([[_directo(ruteador, p, (c.lat, c.lon))[0] for c in candidatos.itertuples()] for p in puntos])
    costo = bases.costos(minutos, bases.pesos(pd.Series([3, None])), candidatos["ajuste_min"].to_numpy())
    assert base["base"] == candidatos["nombre"].iloc[int(np.argmin(costo))]
    assert (base["paradas"], base["paradas_con_camino"]) == (3, 2)
    assert base["capa"] == "vial" and base["metros_a_la_red"] == round(
        ruteador.ubicar([base["lat"]], [base["lon"]])[1][0]
    )


def test_tiempos_de_la_base_a_sus_paradas(mundo):
    ruteador, _, _, elegidas, desde_base = mundo
    base = elegidas.set_index("polo").loc[1]
    fila = desde_base.query("codigo == 2").iloc[0]
    assert (fila["minutos"], fila["km"]) == pytest.approx(
        _directo(ruteador, (base["lat"], base["lon"]), (-11.9915, -76.973))
    )
    assert desde_base.query("codigo == 3")[["minutos", "km"]].isna().all().all()
    assert set(desde_base["codigo"]) == {1, 2, 3, 4}


def test_desde_los_origenes(mundo):
    ruteador, _, _, elegidas, _ = mundo
    origenes = pd.DataFrame({"id": ["prueba"], "lat": [-12.0], "lon": [-76.99]})
    a_paradas, a_bases = tiempos.tiempos_desde_origenes(ruteador, PARAMETROS, origenes, PARADAS, elegidas)
    assert len(a_paradas) == len(PARADAS) and len(a_bases) == len(elegidas)
    fila = a_paradas.query("codigo == 4").iloc[0]
    assert (fila["minutos"], fila["km"]) == pytest.approx(_directo(ruteador, (-12.0, -76.99), (-12.0, -76.9555)))
    assert a_paradas.query("codigo == 3")[["minutos", "km"]].isna().all().all()
    base = elegidas.set_index("polo").loc[2]
    fila = a_bases.query("polo == 2").iloc[0]
    assert (fila["minutos"], fila["km"]) == pytest.approx(
        _directo(ruteador, (-12.0, -76.99), (base["lat"], base["lon"]))
    )


def test_por_donde_se_llega_segun_la_ficha():
    recursos = pd.DataFrame(
        {
            "ultimo_medio": ["Lancha", "A pie", "A pie", "Mototaxi", "Ferrocarril", None],
            "acceso_acuatico": [True, True, False, True, False, None],
        }
    )
    # En bote; en bote y luego a pie; a pie; el bote fue antes de la mototaxi; en tren; sin ficha.
    assert list(tiempos.acceso_de(recursos)) == ["bote", "bote", "vial", "vial", "tren", "vial"]


def test_a_una_isla_se_llega_en_bote_y_bajarse_cuesta_un_trasbordo(mundo):
    ruteador, _, _, elegidas, _ = mundo
    isla = pd.DataFrame(
        {"codigo": [9], "polo": [2], "lat": [-12.0015], "lon": [-76.921], "jerarquia": [1], "acceso": ["bote"]}
    )
    origenes = pd.DataFrame({"id": ["prueba"], "lat": [-12.0], "lon": [-76.99]})
    a_paradas, _ = tiempos.tiempos_desde_origenes(ruteador, PARAMETROS, origenes, isla, elegidas)
    fila = a_paradas.iloc[0]
    assert (fila["minutos"], fila["km"]) == pytest.approx(
        _directo(ruteador, (-12.0, -76.99), (-12.0015, -76.921), "bote")
    )
    # Dos trasbordos: subir al bote en el muelle y bajarse en la isla.
    (vo,), (mo,), _ = ruteador.ubicar([-12.0], [-76.99])
    (vi,), (mi,), (ci,) = ruteador.ubicar([-12.0015], [-76.921], ["bote"])
    minutos, _ = ruteador.entre([vo], [vi], margen=None)
    sin_bajarse = minutos[0, 0] + PARAMETROS["por_viaje"] + 1.3 * (mo + mi) / 1000 * PARAMETROS["trocha"]
    assert CAPAS[ci] == "bote" and fila["minutos"] == pytest.approx(sin_bajarse + PARAMETROS["transbordo_min"])


def test_las_coordenadas_se_escriben_con_seis_decimales(tmp_path):
    tabla = pd.DataFrame({"polo": [1], "lat": [-9.2954321], "lon": [-75.9981234], "minutos": [12.345]})
    tiempos._escribir(tabla, tmp_path / "t.csv")
    leida = pd.read_csv(tmp_path / "t.csv", sep=";", encoding="utf-8-sig")
    assert (leida.at[0, "lat"], leida.at[0, "lon"]) == (-9.295432, -75.998123)
    assert leida.at[0, "minutos"] == 12.3
