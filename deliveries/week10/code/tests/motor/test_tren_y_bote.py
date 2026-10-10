"""El tren y el bote en el motor: lo que traen los artefactos, con qué se viaja (contrato 1.2) y cuánto cuesta."""

import numpy as np
import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import costo, textos, viaje
from dreemgo.motor import datos as artefactos

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

POLO = {
    "id": 1,
    "nombre": "Puno",
    "region": "Puno",
    "regiones": ["Puno"],
    "recursos": 2,
    "fuera_del_circuito": True,
    "novedad": 0.5,
    "base": {"nombre": "Puno"},
    "paradas": ["10", "11"],
    "base_minutos": [153.2, 8.0],
    "base_km": [45.6, 1.0],
    "entre_minutos": [[0.0, 120.0], [120.0, 0.0]],
    "entre_km": [[0.0, 31.0], [31.0, 0.0]],
    "clima": [],
    "eventos": [],
}


def test_un_polo_sin_tren_ni_bote_se_lee_con_ceros():
    polo = artefactos._polo(POLO)
    assert polo.base_km_tren.tolist() == [0.0, 0.0] and polo.entre_km_bote.tolist() == [[0.0, 0.0], [0.0, 0.0]]
    con_bote = artefactos._polo(POLO | {"base_km_bote": [30.6, None], "entre_km_bote": [[0.0, 30.6], [30.6, 0.0]]})
    assert con_bote.base_km_bote[0] == 30.6 and np.isnan(con_bote.base_km_bote[1])
    assert con_bote.entre_km_bote[0, 1] == 30.6 and not con_bote.base_km_tren.any()


def test_un_origen_trae_los_km_en_tren_y_en_bote_de_cada_camino():
    origen = artefactos._origen(
        {
            "id": "puno",
            "nombre": "Puno",
            "region": "Puno",
            "lat": -15.84,
            "lon": -70.02,
            "a_base": {"1": [5.0, 1.3, 0.0, 0.0], "2": [None, None, None, None], "3": [90.0, 60.0]},
            "a_parada": {"10": [153.2, 45.6, 0.0, 30.6]},
        }
    )
    assert origen.a_parada["10"] == (153.2, 45.6) and origen.a_parada_en_capa["10"] == (0.0, 30.6)
    # Sin km en tren ni en bote, sin camino, y un artefacto de antes, que solo trae minutos y km.
    assert origen.a_base_en_capa == {1: (0.0, 0.0), 2: (0.0, 0.0), 3: (0.0, 0.0)}


@pytest.mark.parametrize(
    "km, km_tren, km_bote, medios",
    [
        (103.7, 28.8, 0.0, ["carretera", "tren"]),  # Cusco → Machupicchu Pueblo
        (45.6, 0.0, 39.1, ["carretera", "bote"]),  # Puno → Amantaní
        (250.0, 0.0, 0.0, ["carretera"]),
        (5.2, 0.0, 4.6, ["bote"]),  # menos de un km fuera del bote: ir al muelle
        (12.0, float("nan"), float("nan"), ["carretera"]),
    ],
)
def test_medios_de_un_camino(km, km_tren, km_bote, medios):
    assert viaje.medios(km, km_tren, km_bote) == medios


def test_como_se_escriben_los_medios():
    assert textos.por_medios(["carretera"]) == "por carretera"
    assert textos.por_medios(["carretera", "tren"]) == "por carretera y en tren"
    assert textos.por_medios(["carretera", "tren", "bote"]) == "por carretera, en tren y en bote"
    assert textos.por_medios(["bote"]) == "en bote"


PARAMETROS = {
    "bus_intercepto": {"valor": 12, "minimo": 5, "maximo": 25},
    "bus_soles_km": {"valor": 0.085, "minimo": 0.055, "maximo": 0.125},
    "movilidad_soles_km": {"valor": 0.55, "minimo": 0.30, "maximo": 0.95},
    "alojamiento_noche": {"valor": 70, "minimo": 35, "maximo": 140},
    "alimentacion_dia": {"valor": 50, "minimo": 25, "maximo": 95},
    "entrada_sin_tarifa": {"valor": 17.63, "minimo": 5, "maximo": 20},
    "tren_tramo": {"valor": 80, "minimo": 18, "maximo": 206},
    "bote_soles_km": {"valor": 1.0, "minimo": 0.33, "maximo": 1.81},
}


def _gastos(**cambios) -> costo.Gastos:
    base = dict(
        dias=3,
        noches=2,
        km_interprovincial=75.0,
        km_locales=20.0,
        tarifas=(152.0,),
        combinados=(),
        sin_tarifa=0,
        base="Machupicchu Pueblo",
    )
    return costo.Gastos(**(base | cambios))


def test_el_tren_y_el_bote_se_pagan_aparte():
    sin = costo.estimar(PARAMETROS, _gastos(), None)
    tren = costo.estimar(PARAMETROS, _gastos(tramos_tren=2), None)
    bote = costo.estimar(PARAMETROS, _gastos(km_bote=60.0), None)
    assert tren.desglose["transporte"] > sin.desglose["transporte"] and tren.p20 > sin.p20
    assert bote.desglose["transporte"] > sin.desglose["transporte"]
    assert any(s.startswith("Tren: 2 tramos, entre S/\u00a018 y S/\u00a0206") for s in tren.supuestos)
    assert any(s.startswith("Bote: 60 km, entre S/\u00a00,33 y S/\u00a01,81 por km") for s in bote.supuestos)
    assert not any(s.startswith(("Tren", "Bote")) for s in sin.supuestos)


@con_datos
def test_a_machu_picchu_se_llega_en_tren():
    datos = artefactos.cargar()
    consulta = Consulta(origen="cusco", mes=6, dias=4)
    p = viaje.preparar(datos.polos[4], consulta, datos.origenes["cusco"], datos)
    assert p is not None and p.km_tren_ida > 0
    it = viaje.Itinerario(
        p.polo, p.plan, [], p.candidatas, 0.0, p.minutos_ida, p.km_ida, p.km_tren_ida, p.km_bote_ida, p.desde_en_capa
    )
    assert viaje.medios_del_traslado(it) == ["carretera", "tren"]


@con_datos
def test_a_las_islas_del_titicaca_se_llega_en_bote():
    datos = artefactos.cargar()
    polo = datos.polos[datos.recursos["959"]["polo"]]  # Isla Taquile, desde Puno
    i = polo.indice()["959"]
    assert np.isfinite(polo.base_minutos[i]) and polo.base_km_bote[i] > 20


@con_datos
def test_la_respuesta_dice_con_que_se_viaja_y_avisa_del_tren():
    datos = artefactos.cargar()
    for consulta in (Consulta(origen="cusco", mes=6, dias=2, intereses=["naturaleza"]), Consulta(origen="lima", mes=7)):
        for ruta in viaje.resolver(consulta, datos).rutas:
            medios = ruta.traslado.medios
            assert medios and medios == sorted(medios, key=["carretera", "tren", "bote"].index)
            assert (ruta.traslado.acceso == "sin_acceso_terrestre") == ("bote" in medios)
            con_tren = "tren" in medios or any(d.nota and "En tren hasta" in d.nota for d in ruta.dias)
            aviso = any(a.tipo == "acceso" and "tren" in a.mensaje for a in ruta.avisos)
            assert aviso == con_tren
            if medios != ["carretera"]:
                assert not any("carretera" in a.mensaje for a in ruta.avisos)
            if "tren" in medios:
                assert any(s.startswith("Tren:") for s in ruta.costo.supuestos)


@con_datos
def test_el_dia_de_salida_cuenta_primero_la_visita_y_despues_la_vuelta():
    consulta = Consulta(origen="ica", mes=2, dias=2, intereses=["naturaleza", "playa"])
    notas = [
        dia.nota
        for ruta in viaje.resolver(consulta, artefactos.cargar()).rutas
        for dia in ruta.dias
        if dia.tipo == "visita_y_vuelta" and "En bote hasta" in (dia.nota or "")
    ]
    # A El Candelabro se va en bote desde Paracas, y de ahí se vuelve a Ica.
    assert notas and all(nota.startswith("En bote hasta") and "Vuelta a Ica" in nota for nota in notas)
