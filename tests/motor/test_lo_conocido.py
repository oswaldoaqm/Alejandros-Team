"""Lo que cualquiera espera del motor: que proponga Machu Picchu y la Cordillera Blanca desde
donde y cuando se puede ir, que desde Lima se vuele al Cusco, que a Huaraz se vaya en bus de
noche, y que no mande a nadie más días en el bus que de visita. Corre contra los artefactos de
dreemgo/datos: si un cambio en los datos o en el puntaje los saca de las tres rutas, aquí se nota
(decisiones 0013 a 0016, 0019, 0027 y 0028)."""

import re

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


def _duermen_en(**consulta) -> list[str]:
    return [r.polo.base.nombre for r in viaje.resolver(Consulta(**consulta), artefactos.cargar()).rutas]


def test_desde_el_cusco_un_fin_de_semana_de_temporada_seca_se_queda_en_el_valle_sagrado():
    """En dos días, las 7 horas y media hasta Puno se llevan más del 30 % del viaje con las noches del bus:
    el fin de semana se queda cerca (decisión 0027). Con tres días, Puno sí va en bus de noche (0019)."""
    dos = viaje.resolver(Consulta(origen="cusco", mes=6, dias=2), artefactos.cargar()).rutas
    assert "Urubamba" in {r.polo.base.nombre for r in dos}
    assert all(r.traslado.bus_de_noche is None for r in dos)
    tres = viaje.resolver(Consulta(origen="cusco", mes=6, dias=3), artefactos.cargar()).rutas
    assert {r.polo.base.nombre: r for r in tres}["Puno"].traslado.bus_de_noche is not None


def test_un_viaje_a_puno_con_tiempo_lleva_a_los_uros():
    """Los Uros se visitan en lugar de la Reserva Nacional del Titicaca, que no tiene camino, y valen como ella
    (decisión 0028). En dos días desde Arequipa no caben: el primero es tranquilo, por la altura, y el segundo
    termina con la vuelta. Y desde que la ida en bus cuenta los terminales (decisión 0030), en tres días se pasa
    más tiempo en el camino que en Puno."""
    datos = artefactos.cargar()
    [puno] = [p.id for p in datos.polos.values() if p.base["nombre"] == "Puno"]
    for origen, dias in (("cusco", 3), ("arequipa", 4), ("lima", 4), ("tacna", 3)):
        [ruta] = viaje.resolver(Consulta(origen=origen, mes=7, dias=dias, destino=puno), datos).rutas
        assert "960" in {p.recurso.codigo for d in ruta.dias for p in d.paradas}, origen


def test_desde_el_cusco_un_fin_de_semana_de_historia_lleva_a_machu_picchu():
    assert "Machupicchu Pueblo" in _duermen_en(origen="cusco", mes=6, dias=2, intereses=["historia"])


def test_desde_lima_seis_dias_de_julio_se_vuela_al_cusco():
    rutas = viaje.resolver(Consulta(origen="lima", mes=7, dias=6), artefactos.cargar()).rutas
    [cusco] = [r for r in rutas if r.polo.base.nombre == "Cuzco"]
    assert cusco.traslado.medios[0] == "avion" and [d.tipo for d in cusco.dias][1:5] == ["visita"] * 4


def test_por_tierra_desde_lima_seis_dias_de_julio_llevan_a_huaraz():
    assert "Huaraz" in _duermen_en(origen="lima", mes=7, dias=6, solo_por_tierra=True)


def test_por_tierra_desde_lima_cuatro_dias_de_julio_tambien_llevan_a_huaraz():
    """Son 8 horas de viaje, en bus de noche: los cuatro días son allá (decisión 0019)."""
    rutas = viaje.resolver(Consulta(origen="lima", mes=7, dias=4, solo_por_tierra=True), artefactos.cargar()).rutas
    [huaraz] = [r for r in rutas if r.polo.base.nombre == "Huaraz"]
    assert [d.tipo for d in huaraz.dias] == ["ida_y_visita", "visita", "visita", "visita_y_vuelta"]
    assert huaraz.traslado.dias_de_viaje == 0 and huaraz.traslado.bus_de_noche is not None
    assert all(d.paradas and d.horas <= 8.0 for d in huaraz.dias)


def test_desde_lima_un_fin_de_semana_se_queda_cerca_y_con_tres_dias_va_a_huaraz_en_bus_de_noche():
    """En dos días, las 8 horas y media hasta Huaraz se llevan más del 30 % del viaje con las noches del bus,
    y el fin de semana se queda a pocas horas de Lima (decisión 0027). Con tres días, Huaraz va en bus de
    noche (0019)."""
    dos = viaje.resolver(Consulta(origen="lima", mes=7, dias=2), artefactos.cargar()).rutas
    assert len(dos) == 3 and all(r.traslado.bus_de_noche is None for r in dos)
    tres = viaje.resolver(Consulta(origen="lima", mes=7, dias=3), artefactos.cargar()).rutas
    assert {r.polo.base.nombre: r for r in tres}["Huaraz"].traslado.bus_de_noche is not None


# El ejemplo de la guía del avance del 9 de octubre: desde Lima, cuatro días, para alguien a quien le
# gustan la naturaleza y las caminatas, con hasta S/ 1 000. Si deja de cumplirse, la guía miente.
NATURALEZA = {"origen": "lima", "dias": 4, "intereses": ["naturaleza", "caminatas"], "presupuesto": 1000}


def test_con_naturaleza_y_caminatas_julio_lleva_a_huaraz():
    assert "Huaraz" in _duermen_en(mes=7, **NATURALEZA)


def test_con_presupuesto_los_vuelos_que_lo_pasan_no_desplazan_a_los_que_entran():
    """Sin presupuesto, desde Lima con cuatro días se vuela a Arequipa y al Cusco; con S/ 1 000,
    que esos vuelos pasan, los tres viajes van en bus y entran (decisión 0016)."""
    rutas = viaje.resolver(Consulta(mes=7, **NATURALEZA), artefactos.cargar()).rutas
    assert len(rutas) == 3 and not any(r.traslado.vuelos for r in rutas)
    assert all(r.costo.dentro_del_presupuesto for r in rutas)
    sin_tope = viaje.resolver(Consulta(mes=7, **(NATURALEZA | {"presupuesto": None})), artefactos.cargar()).rutas
    assert any(r.traslado.vuelos for r in sin_tope)


def test_en_febrero_la_lluvia_de_la_sierra_saca_a_huaraz():
    rutas = viaje.resolver(Consulta(mes=2, **NATURALEZA), artefactos.cargar()).rutas
    assert rutas and "Huaraz" not in [r.polo.base.nombre for r in rutas]
    assert all(r.estacionalidad.veredicto != "desaconsejado" for r in rutas)


def test_con_mas_de_tres_imperdibles_el_motivo_nombra_algunos():
    """Urubamba, desde el Cusco, tiene cuatro: el motivo nombra tres y dice que son algunos."""
    rutas = viaje.resolver(Consulta(origen="cusco", mes=6, dias=2), artefactos.cargar()).rutas
    [urubamba] = [r for r in rutas if r.polo.base.nombre == "Urubamba"]
    assert any(m.startswith("4 lugares de jerarquía 3 o 4, entre ellos ") for m in urubamba.motivos)
    for ruta in rutas:
        for motivo in ruta.motivos:
            cuantos = re.match(r"(\d+) lugares de jerarquía 3 o 4", motivo)
            if cuantos:
                assert (", entre ellos " in motivo) == (int(cuantos.group(1)) > 3), motivo


def test_ningun_viaje_pasa_mas_dias_en_el_camino_que_alla():
    """Por tierra, el Cusco desde Lima con nueve días eran seis en el bus y tres allá; y Tarapoto
    desde Iquitos, ocho días de río y uno allá. En avión sí caben."""
    for origen, mes, fuera in (("lima", 7, "Cuzco"), ("iquitos", 6, "Tarapoto")):
        for solo_por_tierra in (True, False):
            consulta = Consulta(origen=origen, mes=mes, dias=9, solo_por_tierra=solo_por_tierra)
            rutas = viaje.resolver(consulta, artefactos.cargar()).rutas
            assert rutas and (fuera not in [r.polo.base.nombre for r in rutas] or not solo_por_tierra)
            for ruta in rutas:
                de_camino = sum(1 for d in ruta.dias if d.tipo in ("ida", "vuelta") and not d.paradas)
                assert de_camino <= len(ruta.dias) - de_camino, ruta.polo.nombre
