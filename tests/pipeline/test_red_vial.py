"""Red vial sobre un extracto de juguete: tests/fixtures/red_mini.osm."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline.red_vial import (
    CAPAS,
    CLASES,
    CODIGO,
    Red,
    Ruteador,
    _estaciones_al_lado,
    haversine_m,
    leer_capitales,
    leer_hospedajes,
    leer_lugares,
    leer_red,
    minutos_por_arista,
)

MINI = Path(__file__).parents[1] / "fixtures" / "red_mini.osm"
# Minutos por km de cada clase, y recargos por km sin asfaltar y por cada 100° de giro por km.
RITMOS = {
    "autopista": 0.75,
    "troncal": 1.0,
    "primaria": 1.2,
    "secundaria": 1.5,
    "terciaria": 1.7,
    "local": 2.4,
    "trocha": 3.0,
    "balsa": 6.0,
    "sin_asfaltar": 0.5,
    "curvas": 0.1,
}
CON_CAPAS = {**RITMOS, "tren": 2.0, "bote": 3.0, "transbordo": 12.0, "transbordo_min": 30.0}


@pytest.fixture(scope="module")
def red() -> Red:
    return leer_red(MINI)


def _arista(red, lat1, lon1, lat2, lon2):
    """Índice de la arista entre esos dos puntos, en cualquier sentido."""
    for i in range(red.aristas):
        a = (red.lat[red.desde[i]], red.lon[red.desde[i]])
        b = (red.lat[red.hasta[i]], red.lon[red.hasta[i]])
        if {a, b} == {(lat1, lon1), (lat2, lon2)}:
            return i
    raise AssertionError(f"no hay arista entre {(lat1, lon1)} y {(lat2, lon2)}")


def test_la_red_se_parte_en_los_cruces_y_cada_kilometro(red):
    assert (red.vial().vertices, red.vial().aristas) == (11, 9)
    # La primaria 1-2-3-4 se corta en el cruce con la trocha (nodo 3), no en el nodo 2.
    i = _arista(red, -12.0, -77.0, -12.0, -76.982)
    assert red.metros[i] == pytest.approx(haversine_m(-12.0, -77.0, -12.0, -76.982), rel=1e-6)
    assert CLASES[red.clase[i]] == "primaria"
    # La trocha pasa el kilómetro en el nodo 5: queda partida ahí.
    assert CLASES[red.clase[_arista(red, -12.0, -76.982, -11.991, -76.982)]] == "trocha"


def test_lo_que_un_auto_no_puede_recorrer_queda_fuera(red):
    vial = red.vial()
    puntos = set(zip(vial.lat.tolist(), vial.lon.tolist(), strict=True))
    assert (-12.009, -76.973) not in puntos  # residencial privada
    assert (-12.009, -77.0) not in puntos  # vereda
    assert (-12.001, -76.991) not in puntos  # pasillo de estacionamiento
    assert (-12.0, -76.92) not in puntos  # ferry de 3,8 km: es un viaje en bote


def test_la_balsa_corta_es_parte_de_la_red(red):
    assert CLASES[red.clase[_arista(red, -12.0, -76.973, -12.0, -76.964)]] == "balsa"


def test_sin_asfaltar_y_curvas(red):
    assert red.sin_asfaltar[_arista(red, -12.0, -76.982, -11.991, -76.982)]
    assert not red.sin_asfaltar[_arista(red, -12.0, -77.0, -12.0, -76.982)]
    zigzag = _arista(red, -12.05, -77.05, -12.047, -77.047)  # gira 90° en el nodo 51
    km = red.metros[zigzag] / 1000
    assert red.curvas[zigzag] == pytest.approx(90 / km, rel=0.01)


def test_guardar_y_cargar(red, tmp_path):
    red.guardar(tmp_path / "red.npz")
    otra = Red.cargar(tmp_path / "red.npz")
    assert np.array_equal(otra.metros, red.metros) and np.array_equal(otra.desde, red.desde)
    assert np.array_equal(otra.capa, red.capa)


def test_el_tren_y_el_bote_van_en_su_capa(red):
    capa = {nombre: set() for nombre in CAPAS}
    for i in range(red.vertices):
        capa[CAPAS[red.capa[i]]].add((red.lat[i], red.lon[i]))
    assert capa["bote"] == {(-12.0, -76.955), (-12.0, -76.92)}  # el ferry de 3,8 km
    # La ruta de tren y el riel turístico que sigue desde el paradero, sin relación de ruta; sin el ramal minero.
    assert capa["tren"] == {
        (-12.0005, -76.982),
        (-12.01, -76.982),
        (-12.03, -76.982),
        (-12.03, -76.96),
        (-12.03, -76.95),
    }
    # Solo se sube en una estación o un muelle a menos de 1 km de una vía.
    trasbordos = np.flatnonzero(red.clase == CODIGO["transbordo"])
    puntas = {
        frozenset({(red.lat[red.desde[e]], red.lon[red.desde[e]]), (red.lat[red.hasta[e]], red.lon[red.hasta[e]])})
        for e in trasbordos
    }
    assert puntas == {
        frozenset({(-12.0, -76.982), (-12.0005, -76.982)}),  # la estación, junto al cruce
        frozenset({(-12.0, -76.955)}),  # el muelle, en el mismo punto que la vía
    }


def test_una_estacion_dibujada_al_lado_del_riel_se_toma_en_el_riel():
    # El riel turístico 82-85-86 y la estación 87, dibujada a 25 m del nodo 85 y no sobre el riel.
    riel = [(82, -12.03, -76.982), (85, -12.03, -76.96), (86, -12.03, -76.95)]
    assert _estaciones_al_lado(MINI, [riel], {82, 85, 86}) == {85: (-12.03, -76.96)}


def test_al_paradero_lejano_se_llega_en_tren(red):
    ruteador = Ruteador(red, minutos_por_arista(red, CON_CAPAS), vertices_minimos=4)
    (inicio,), _ = ruteador.ubicar([-12.0], [-76.982])
    (lejano,), metros = ruteador.ubicar([-12.0302], [-76.982])  # a más de 1 km de cualquier vía
    assert (red.lat[lejano], red.lon[lejano]) == (-12.03, -76.982) and metros[0] < 50
    minutos, km = ruteador.entre([inicio], [lejano], margen=None)
    trasbordo = haversine_m(-12.0, -76.982, -12.0005, -76.982) / 1000
    riel = haversine_m(-12.0005, -76.982, -12.03, -76.982) / 1000
    assert minutos[0, 0] == pytest.approx(trasbordo * 12.0 + 30.0 + riel * 2.0, rel=1e-4)
    assert km[0, 0] == pytest.approx(trasbordo + riel, rel=1e-4)


def test_junto_a_una_via_se_ubica_en_la_via_aunque_el_riel_este_mas_cerca(red):
    ruteador = Ruteador(red, minutos_por_arista(red, CON_CAPAS), vertices_minimos=4)
    (vertice,), _ = ruteador.ubicar([-12.0004], [-76.982])  # a 11 m de la estación y 44 m del cruce
    assert red.capa[vertice] == CAPAS.index("vial")


def test_sin_capas_la_red_vial_es_la_misma(red):
    vial = red.vial()
    assert vial.capa is None and set(vial.clase.tolist()) <= {CODIGO[c] for c in CLASES[:8]}
    assert np.array_equal(red.lat[: vial.vertices], vial.lat)


def test_minutos_por_arista(red):
    minutos = minutos_por_arista(red, RITMOS)
    i = _arista(red, -12.0, -76.982, -11.991, -76.982)  # trocha sin asfaltar, recta
    assert minutos[i] == pytest.approx(red.metros[i] / 1000 * (RITMOS["trocha"] + RITMOS["sin_asfaltar"]))


def test_el_camino_mas_rapido_y_sus_km(red):
    ruteador = Ruteador(red, minutos_por_arista(red, RITMOS), vertices_minimos=4)
    inicio, _ = ruteador.ubicar([-12.0], [-77.0])
    fin, _ = ruteador.ubicar([-12.0], [-76.973])
    minutos, km = ruteador.entre(inicio, fin, margen=None)
    recto = haversine_m(-12.0, -77.0, -12.0, -76.973) / 1000
    assert km[0, 0] == pytest.approx(recto, rel=1e-4)  # por la primaria, no por la trocha
    assert minutos[0, 0] == pytest.approx(recto * RITMOS["primaria"], rel=1e-4)
    con_margen = ruteador.entre(inicio, fin, margen=0.05)
    assert np.allclose(con_margen[0], minutos) and np.allclose(con_margen[1], km)


def test_solo_se_ubica_en_la_red_conectada(red):
    ruteador = Ruteador(red, minutos_por_arista(red, RITMOS), vertices_minimos=4)
    vertice, metros = ruteador.ubicar([-12.1], [-77.1])  # junto a un tramo suelto de dos vértices
    assert ruteador.en_red_grande[vertice[0]]
    assert metros[0] > 10_000


def test_capitales_y_pueblos():
    capitales = leer_capitales(MINI)
    assert capitales.to_dict("records") == [
        {"distrito": "Distrito de Prueba", "capital": "Pueblo Prueba", "lat": -12.005, "lon": -76.985}
    ]
    lugares = leer_lugares(MINI).set_index("nombre")
    assert sorted(lugares.index) == ["Otro Pueblo", "Pueblo Prueba"]  # sin el caserío sin nombre
    assert lugares.at["Pueblo Prueba", "altitud_m"] == 3399
    assert pd.isna(lugares.at["Otro Pueblo", "altitud_m"])


def test_hospedajes():
    hospedajes = leer_hospedajes(MINI)
    assert sorted(hospedajes["tipo"]) == ["hostel", "hotel"]  # el mirador no es hospedaje
    hostal = hospedajes[hospedajes["tipo"] == "hostel"].iloc[0]
    # El centro de su contorno, sin contar dos veces el nodo que lo cierra.
    assert (hostal["lat"], hostal["lon"]) == pytest.approx((-12.0205, -77.0115))


def test_los_destinos_de_paso_no_agrandan_ni_repiten_la_busqueda(red, monkeypatch):
    ruteador = Ruteador(red, minutos_por_arista(red, RITMOS), vertices_minimos=4)
    (inicio,), _ = ruteador.ubicar([-12.0], [-77.0])
    (cerca,), _ = ruteador.ubicar([-12.0], [-76.982])
    (pasando_la_balsa,), _ = ruteador.ubicar([-12.0], [-76.964])  # fuera del rectángulo de 0,01°
    en_toda_la_red = ruteador.entre([inicio], [cerca, pasando_la_balsa], margen=None)
    busquedas = []
    original = ruteador._entre
    monkeypatch.setattr(ruteador, "_entre", lambda *a: busquedas.append(len(a[0])) or original(*a))

    minutos, km = ruteador.entre([inicio], [cerca, pasando_la_balsa], margen=0.01, obligatorios=[True, False])
    assert minutos[0, 0] == pytest.approx(en_toda_la_red[0][0, 0])
    assert np.isinf(minutos[0, 1]) and np.isinf(km[0, 1])  # fuera de lo buscado: sin camino, no otro vértice
    assert len(busquedas) == 1 and busquedas[0] < red.vertices

    # Si es obligatorio, el rectángulo lo incluye y el resultado es el de toda la red.
    minutos, km = ruteador.entre([inicio], [cerca, pasando_la_balsa], margen=0.01)
    assert np.allclose(minutos, en_toda_la_red[0]) and np.allclose(km, en_toda_la_red[1])
