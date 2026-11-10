"""El bus de noche y el almuerzo en el viaje (decisión 0019): las reglas, sin datos, y un viaje a
Huaraz contra los artefactos de dreemgo/datos."""

from datetime import date

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from dreemgo.motor.planificador import Jornada

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
H = 60


@pytest.mark.parametrize(
    "horas, sale, llega",
    [
        (8 + 7 / 60, "21:45", "05:55"),  # Lima–Huaraz: sale lo más tarde que puede para llegar a las 6:00
        (7, "23:00", "06:00"),
        (11, "19:00", "06:00"),
        (16, "19:00", "11:00"),  # no sale antes de las 19:00, aunque llegue más tarde
    ],
)
def test_a_que_hora_sale_y_llega(horas, sale, llega):
    assert tuple(viaje.textos.hora(m) for m in viaje.bus_de_noche(horas * H)) == (sale, llega)


@pytest.mark.parametrize(
    "dias, horas, tren, bote, va",
    [
        (2, 8, 0, 0, True),
        (2, 9.5, 0, 0, True),  # 19 de las 48 horas del viaje: menos del 40 %
        (2, 9.7, 0, 0, False),  # Arequipa desde el Cusco: dos días son muy poco
        (3, 9.7, 0, 0, True),
        (4, 16, 0, 0, True),
        (1, 8, 0, 0, False),  # en un día no: entre dos noches de bus no hay hotel
        (4, 6.9, 0, 0, False),  # llegaría de madrugada
        (4, 16.1, 0, 0, False),  # más lejos, se vuela o se duerme en el camino
        (4, 8, 120, 0, False),  # en tren, no
        (4, 8, 0, 30, False),  # en bote, tampoco
    ],
)
def test_cuando_va_de_noche(dias, horas, tren, bote, va):
    assert viaje.va_de_noche(dias, horas * H, tren, bote, None) is va


def test_con_vuelo_no_va_de_noche():
    assert not viaje.va_de_noche(4, 8 * H, 0, 0, vuelo=object())


def test_los_dias_son_todos_en_la_base():
    plan = viaje.plan_de_noche(3, (8 + 7 / 60) * H, date(2026, 7, 24))
    assert (plan.llegada, plan.salida, plan.tramos, plan.dia_de_jornada) == (1, 3, {}, [1, 2, 3])
    assert plan.jornadas == [Jornada(8 * H, 8 * H, 4), Jornada(8 * H, 8 * H, 5), Jornada(8 * H, 8 * H, 6)]
    assert viaje.dias_de_solo_viaje(plan) == 0


def test_si_llega_tarde_el_primer_dia_empieza_una_hora_despues_y_termina_a_la_hora():
    plan = viaje.plan_de_noche(2, 16 * H, None)
    # Llega a las 11:00: se visita desde las 12:00 hasta las 16:00, más el almuerzo.
    assert plan.jornadas[0] == Jornada(12 * H, 4 * H, None)


def test_sus_dos_noches_pesan_como_un_dia_mas():
    noche = viaje.plan_de_noche(2, 8 * H, None)
    assert viaje.por_bus_de_noche(noche, 2) == pytest.approx(2 / 3)
    assert viaje.por_bus_de_noche(viaje.plan_de_noche(6, 8 * H, None), 6) == pytest.approx(6 / 7)
    assert viaje.por_bus_de_noche(viaje.plan_de_dias(4, 5 * H, None), 4) == 1.0


@con_datos
def test_a_huaraz_en_bus_de_noche():
    datos = artefactos.cargar()
    [huaraz] = [p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz"]
    consulta = Consulta(origen="lima", fecha_inicio=date(2026, 7, 24), dias=3, destino=huaraz)
    [ruta] = viaje.resolver(consulta, datos).rutas
    t = ruta.traslado
    assert (t.medios, t.dias_de_viaje, t.bus_de_noche.sale, t.bus_de_noche.sale_vuelta) == (
        ["carretera"],
        0,
        "21:45",
        "21:45",
    )
    assert [d.tipo for d in ruta.dias] == ["ida_y_visita", "visita", "visita_y_vuelta"]
    assert ruta.dias[0].fecha == date(2026, 7, 24)  # el día 1 es el día en que se llega
    assert ruta.dias[0].nota.startswith("El bus de noche sale de Lima a las 21:45 de la noche anterior")
    assert ruta.dias[-1].nota.startswith("En la noche, el bus de vuelta")
    # Ningún día lleva las horas del bus; los km del bus van en el total.
    assert all(d.horas <= 8 for d in ruta.dias)
    assert ruta.indicadores.km_total > sum(d.km for d in ruta.dias) + 700
    # Dos noches de hospedaje, y el bus a la misma tarifa por km que de día.
    assert "Hospedaje económico en Huaraz, 2 noches" in ruta.costo.supuestos
    assert any(s.startswith("Bus de noche de ida y vuelta") for s in ruta.costo.supuestos)
    assert any(a.tipo == "acceso" and "bus de noche" in a.mensaje for a in ruta.avisos)
    assert any(m.endswith("de Lima en bus de noche") for m in ruta.motivos)
    # La tarjeta de la app muestra las horas del traslado: la nota del día 1, el aviso y el motivo dicen lo mismo.
    ida = viaje.textos.duracion(t.horas * 60)
    assert ruta.dias[0].nota.endswith(f"a las {t.bus_de_noche.llega}: {ida} por carretera.")
    assert any(
        a.mensaje.startswith(f"La ida y la vuelta van en bus de noche, {ida} por carretera") for a in ruta.avisos
    )
    assert f"A {ida} de Lima en bus de noche" in ruta.motivos


@con_datos
def test_cada_dia_con_visitas_almuerza_a_su_hora():
    datos = artefactos.cargar()
    [huaraz] = [p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz"]
    [ruta] = viaje.resolver(Consulta(origen="lima", mes=7, dias=4, destino=huaraz), datos).rutas
    for d in ruta.dias:
        assert d.almuerzo is not None
        h, m = (int(x) for x in d.almuerzo.hora.split(":"))
        assert 11 * H + 30 <= h * H + m <= 15 * H + 30
