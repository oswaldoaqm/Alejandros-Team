"""Los vuelos en el motor (decisión 0016): cuándo se vuela, cómo se parten los días, qué dice
cada día y cuánto cuesta. Las reglas van con vuelos de mentira; lo demás corre contra los
artefactos de dreemgo/datos."""

import dataclasses
import math

import numpy as np
import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import costo, viaje
from dreemgo.motor import datos as artefactos
from dreemgo.motor.datos import Origen, Vuelo

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

POLO = 7


class _Polo:
    id = POLO


def _vuelo(antes: float, aire: float, despues: float, aeropuertos=("LIM", "CUZ"), km_antes=12.0, km_despues=6.0):
    return Vuelo(
        minutos=antes + aire + despues,
        km=km_antes + km_despues,
        km_tren=0.0,
        km_bote=0.0,
        minutos_vuelo=aire - 150,
        minutos_hasta_aeropuerto=antes,
        km_hasta_aeropuerto=km_antes,
        minutos_desde_aeropuerto=despues,
        aeropuertos=aeropuertos,
    )


def _origen(minutos_por_tierra: float, vuelo: Vuelo | None) -> Origen:
    return Origen(
        id="origen",
        nombre="Origen",
        region="Región",
        lat=0.0,
        lon=0.0,
        a_base={POLO: (minutos_por_tierra, 100.0)},
        a_parada={},
        a_base_en_capa={POLO: (0.0, 0.0)},
        a_parada_en_capa={},
        a_base_en_avion={} if vuelo is None else {POLO: vuelo},
    )


def _vuela(minutos_por_tierra: float, vuelo: Vuelo, **consulta) -> bool:
    *_, elegido = viaje.ida(_Polo(), Consulta(mes=7, **consulta), _origen(minutos_por_tierra, vuelo))
    return elegido is not None


# ─────────────────────────────── cuándo se vuela ───────────────────────────────


def test_se_vuela_solo_a_lo_lejano():
    a_cusco = _vuelo(23, 230, 15)  # 4 h 28 de puerta a puerta
    assert _vuela(1348, a_cusco)  # por tierra, 22 h 28
    # Hasta 16 horas por tierra se va en bus, que se puede tomar de noche: Huaraz (8 h 07) y
    # Trujillo (11 h 06) desde Lima, aunque el avión llegue mucho antes.
    assert not _vuela(488, _vuelo(23, 210, 34))
    assert not _vuela(666, _vuelo(23, 225, 19))
    assert not _vuela(viaje.LEJOS_PARA_VOLAR_MIN, a_cusco)
    assert _vuela(viaje.LEJOS_PARA_VOLAR_MIN + 1, a_cusco)


def test_y_solo_si_en_avion_se_llega_media_jornada_antes_con_las_noches_contadas():
    # De Ica a Iquitos en avión se duerme en Lima antes de volar y se llega al día siguiente a
    # las 11:41; un bus de 16 h 40, partido en dos días, llega ese día a las 15:20. No alcanza.
    ica_iquitos = _vuelo(368, 260, 21)
    assert viaje.llegada(viaje.tramos_de_la_ida(ica_iquitos.minutos, ica_iquitos)) == 24 * 60 + 281
    assert viaje.llegada(viaje.tramos_de_la_ida(1000)) == 24 * 60 + 500
    assert not _vuela(1000, ica_iquitos)
    assert _vuela(52 * 60, ica_iquitos, dias=9)  # por río, más de dos días


def test_en_un_viaje_corto_no_se_vuela():
    # Ida y vuelta al Cusco en avión son 8 h 56: el 56 % de un viaje de dos días, el 37 % de uno
    # de tres. A Machupicchu Pueblo, 15 h 08: el 47 % de uno de cuatro días, el 38 % de uno de cinco.
    a_cusco, a_machu_picchu = _vuelo(23, 230, 15), _vuelo(23, 230, 201)
    assert not _vuela(1348, a_cusco, dias=2) and _vuela(1348, a_cusco, dias=3)
    assert not _vuela(1476, a_machu_picchu, dias=4) and _vuela(1476, a_machu_picchu, dias=5)
    assert viaje.CAMINO_QUE_PESA == 0.4


def test_sin_camino_por_tierra_se_vuela_y_con_solo_por_tierra_nunca():
    assert _vuela(np.nan, _vuelo(23, 230, 15))
    assert not _vuela(1348, _vuelo(23, 230, 15), solo_por_tierra=True)
    minutos, km, _, _, vuelo = viaje.ida(_Polo(), Consulta(mes=7), _origen(1348, None))
    assert (minutos, km, vuelo) == (1348, 100.0, None)


def test_con_un_vuelo_los_km_son_los_de_tierra():
    minutos, km, km_tren, km_bote, vuelo = viaje.ida(_Polo(), Consulta(mes=7), _origen(1348, _vuelo(23, 230, 15)))
    assert (minutos, km, km_tren, km_bote) == (268, 18.0, 0.0, 0.0) and vuelo.aeropuertos == ("LIM", "CUZ")


# ─────────────────────────────── los días de la ida ───────────────────────────────


@pytest.mark.parametrize(
    "antes, aire, despues, dias",
    [
        # Cabe en un día: de puerta a puerta.
        (23, 230, 15, [[("antes", 23), ("aire", 230), ("despues", 15)]]),
        # Se duerme junto al aeropuerto de llegada, y lo demás se parte en días iguales.
        (23, 230, 573, [[("antes", 23), ("aire", 230)], [("despues", 287)], [("despues", 286)]]),
        # Llegar al aeropuerto ya se lleva el día: se duerme junto a él y se vuela al otro.
        (368, 260, 21, [[("antes", 368)], [("aire", 260), ("despues", 21)]]),
        # Y si después del vuelo todavía falta mucho, otra noche junto al aeropuerto de llegada.
        (368, 260, 600, [[("antes", 368)], [("aire", 260)], [("despues", 300)], [("despues", 300)]]),
    ],
)
def test_los_dias_de_una_ida_en_avion(antes, aire, despues, dias):
    vuelo = _vuelo(antes, aire, despues)
    assert viaje.dias_en_avion(vuelo) == dias
    tramos = viaje.tramos_de_la_ida(vuelo.minutos, vuelo)
    assert sum(tramos) == math.ceil(vuelo.minutos) and max(tramos) <= viaje.SOLO_VIAJE_MAX_MIN


def test_por_tierra_los_dias_siguen_siendo_partes_iguales():
    assert viaje.tramos_de_la_ida(541) == [271, 270]
    assert viaje.tramos_de_la_ida(488) == [488]
    assert viaje.llegada([271, 270]) == 24 * 60 + 270


def test_la_vuelta_en_avion_hace_los_mismos_dias_al_reves():
    vuelo = _vuelo(368, 260, 21)
    plan = viaje.plan_de_dias(dias=6, minutos_ida=vuelo.minutos, fecha_inicio=None, vuelo=vuelo)
    assert plan.tramos == {1: 368, 2: 281, 5: 281, 6: 368}
    assert (plan.llegada, plan.salida) == (2, 5)
    assert viaje.plan_de_dias(dias=3, minutos_ida=vuelo.minutos, fecha_inicio=None, vuelo=vuelo) is None


# ─────────────────────────────── con los artefactos ───────────────────────────────


def _itinerario(origen: str, base: str, dias: int, mes: int = 7):
    """El viaje de un origen a una base, armado como lo arma el motor."""
    datos = artefactos.cargar()
    consulta = Consulta(origen=origen, mes=mes, dias=dias)
    [polo] = [p for p in datos.polos.values() if p.base["nombre"] == base]
    p = viaje.preparar(polo, consulta, datos.origenes[origen], datos)
    recorridos = viaje.mejor_plan(p.candidatas, p.plan.jornadas, p.tiempos)
    it = viaje.Itinerario(
        p.polo,
        p.plan,
        recorridos,
        p.candidatas,
        viaje.valor_visitado(recorridos),
        p.minutos_ida,
        p.km_ida,
        p.km_tren_ida,
        p.km_bote_ida,
        p.desde_en_capa,
        p.vuelo,
    )
    return it, consulta, datos


@con_datos
def test_desde_lima_al_cusco_se_vuela_y_la_respuesta_lo_dice():
    rutas = viaje.resolver(Consulta(origen="lima", mes=7, dias=6), artefactos.cargar()).rutas
    [cusco] = [r for r in rutas if r.polo.base.nombre == "Cuzco"]
    t = cusco.traslado
    assert t.medios == ["avion", "carretera"] and t.fuente == "red_vial_y_vuelos"
    assert [(v.desde, v.hasta, v.codigo_desde, v.codigo_hasta, v.horas) for v in t.vuelos] == [
        ("Lima", "Cusco", "LIM", "CUZ", 1.33)
    ]
    assert 4 < t.horas < 5 and t.dias_de_viaje == 2 and t.acceso == "terrestre"
    assert cusco.dias[0].nota.startswith(
        "Salida de Lima a las 07:00; 4 h 28 de puerta a puerta hasta Cuzco: con el vuelo Lima–Cusco de 1 h 20"
    )
    assert cusco.dias[-1].nota.endswith("Vuelta a Lima: 4 h 28 de puerta a puerta, con el vuelo Cusco–Lima de 1 h 20.")
    assert list(cusco.costo.desglose)[:2] == ["transporte", "vuelos"]
    assert any(s.startswith("Vuelo Lima–Cusco, de ida y de vuelta: entre S/") for s in cusco.costo.supuestos)
    avisos = [a.mensaje for a in cusco.avisos]
    assert any(m.startswith("La ida y la vuelta van en avión.") for m in avisos)
    assert any("acostumbrarse, y en avión se nota más: conviene" in m for m in avisos)


@con_datos
def test_solo_por_tierra_nunca_vuela():
    datos = artefactos.cargar()
    for consulta in (Consulta(origen="lima", mes=7, dias=6), Consulta(origen="trujillo", mes=7, dias=7)):
        for ruta in viaje.resolver(consulta.model_copy(update={"solo_por_tierra": True}), datos).rutas:
            assert "avion" not in ruta.traslado.medios and not ruta.traslado.vuelos
            assert ruta.traslado.fuente == "red_vial" and "vuelos" not in ruta.costo.desglose


@con_datos
def test_a_iquitos_se_vuela_pero_por_tierra_sigue_sin_acceso():
    it, _, datos = _itinerario("lima", "Iquitos", 5)
    assert it.vuelo is not None and it.vuelo.aeropuertos == ("LIM", "IQT")
    traslado = viaje._traslado(it, datos.origenes["lima"], datos)
    assert traslado.medios == ["avion", "carretera"] and traslado.acceso == "sin_acceso_terrestre"


@con_datos
def test_si_hay_que_dormir_junto_a_un_aeropuerto_las_notas_lo_dicen():
    it, consulta, datos = _itinerario("ica", "Iquitos", 9)
    assert viaje.dias_en_avion(it.vuelo)[0] == [("antes", 368)]
    dias = viaje.dias_del_viaje(it, consulta, datos.origenes["ica"], datos)
    notas = {d.numero: d.nota for d in dias}
    assert notas[1] == (
        "Salida de Ica a las 07:00: 6 h 08 por tierra hacia Lima, de donde sale el vuelo; se duerme en Lima."
    )
    assert notas[2].startswith("Del aeropuerto de Lima hasta Iquitos: 4 h 41, con el vuelo Lima–Iquitos de 1 h 50")
    assert notas[8].startswith("Se deja Iquitos: 4 h 41 hasta Lima, con el vuelo Iquitos–Lima de 1 h 50; se duerme")
    assert notas[9] == "Vuelta a Ica: 6 h 08 por tierra desde Lima."
    # El día que se va al aeropuerto lleva sus km, y el del vuelo, solo los de tierra al llegar.
    assert dias[0].km == pytest.approx(it.vuelo.km_hasta_aeropuerto, abs=0.1)
    assert dias[1].km < 50


@con_datos
def test_el_pasaje_es_una_banda_por_tramo_y_no_toca_el_costo_de_lo_que_va_por_tierra():
    datos = artefactos.cargar()
    v = datos.costos["vuelo_LIM_CUZ"]
    assert v["minimo"] < v["valor"] < v["maximo"] and v["unidad"] == "S/ por persona y tramo"
    gastos = costo.Gastos(
        dias=4, noches=3, km_interprovincial=18.0, km_locales=40.0, tarifas=(), combinados=(), sin_tarifa=0, base="X"
    )
    sin_vuelos = {n: p for n, p in datos.costos.items() if not n.startswith("vuelo_")}
    assert costo.estimar(datos.costos, gastos, None) == costo.estimar(sin_vuelos, gastos, None)
    con_vuelo = costo.estimar(
        datos.costos,
        dataclasses.replace(gastos, vuelos=("vuelo_LIM_CUZ",), tramos_aereos=("Lima–Cusco",)),
        None,
    )
    assert 2 * v["minimo"] < con_vuelo.desglose["vuelos"] < 2 * v["maximo"]
    assert con_vuelo.p20 < con_vuelo.p50 < con_vuelo.p80
    assert "Por tierra, hasta y desde los aeropuertos: 36 km de ida y vuelta" in con_vuelo.supuestos
