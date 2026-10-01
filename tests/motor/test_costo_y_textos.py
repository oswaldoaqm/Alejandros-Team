"""Costo por persona y la forma de escribir horas, montos y fechas."""

from datetime import date

import pytest

from dreemgo.motor import costo, textos

PARAMETROS = {
    "bus_intercepto": {"valor": 12, "minimo": 5, "maximo": 25},
    "bus_soles_km": {"valor": 0.085, "minimo": 0.055, "maximo": 0.125},
    "movilidad_soles_km": {"valor": 0.55, "minimo": 0.30, "maximo": 0.95},
    "alojamiento_noche": {"valor": 70, "minimo": 35, "maximo": 140},
    "alimentacion_dia": {"valor": 50, "minimo": 25, "maximo": 95},
    "entrada_sin_tarifa": {"valor": 17.63, "minimo": 5, "maximo": 20},
}


def _gastos(**cambios) -> costo.Gastos:
    base = dict(
        dias=4,
        noches=3,
        km_interprovincial=300.0,
        km_locales=150.0,
        tarifas=(10.0, 20.0),
        combinados=(),
        sin_tarifa=0,
        base="Huacho",
    )
    return costo.Gastos(**(base | cambios))


def test_banda_ordenada_y_desglose_que_suma_el_p50():
    c = costo.estimar(PARAMETROS, _gastos(), presupuesto=None)
    assert c.p20 < c.p50 < c.p80
    assert sum(c.desglose.values()) == c.p50
    assert set(c.desglose) == {"transporte", "alojamiento", "alimentacion", "entradas"}
    assert c.dentro_del_presupuesto is None and c.exceso is None


def test_la_misma_entrada_da_el_mismo_costo():
    assert costo.estimar(PARAMETROS, _gastos(), 900) == costo.estimar(PARAMETROS, _gastos(), 900)


def test_presupuesto():
    c = costo.estimar(PARAMETROS, _gastos(), presupuesto=200)
    assert c.dentro_del_presupuesto is False and c.exceso == c.p50 - 200
    assert costo.estimar(PARAMETROS, _gastos(), presupuesto=50_000).dentro_del_presupuesto is True


def test_el_boleto_combinado_se_paga_una_vez():
    uno = costo.estimar(PARAMETROS, _gastos(tarifas=(), combinados=(130.0,)), None)
    tres = costo.estimar(PARAMETROS, _gastos(tarifas=(), combinados=(130.0, 130.0, 70.0)), None)
    assert uno.p50 == tres.p50


def test_las_tarifas_desconocidas_suben_la_banda():
    sin = costo.estimar(PARAMETROS, _gastos(), None)
    con = costo.estimar(PARAMETROS, _gastos(sin_tarifa=3), None)
    assert con.p50 > sin.p50
    assert any("no publican su tarifa" in s for s in con.supuestos)


def test_un_viaje_de_un_dia_no_paga_bus_ni_hospedaje():
    c = costo.estimar(PARAMETROS, _gastos(dias=1, noches=0, km_interprovincial=0.0), None)
    assert c.desglose["alojamiento"] == 0
    assert not any("Hospedaje" in s or "interprovincial" in s for s in c.supuestos)


@pytest.mark.parametrize(
    "minutos, texto",
    [(45, "45 min"), (60, "1 h"), (160, "2 h 40"), (125, "2 h 05"), (59.6, "1 h")],
)
def test_duracion(minutos, texto):
    assert textos.duracion(minutos) == texto


def test_hora_lista_y_montos():
    assert textos.hora(425) == "07:05"
    assert textos.hora(24 * 60 + 30) == "00:30"
    assert textos.lista(["a"]) == "a"
    assert textos.lista(["a", "b", "c"]) == "a, b y c"
    assert textos.lista(["a", "b"], "o") == "a o b"
    assert textos.soles(1250) == "S/ 1 250"
    assert textos.a_minutos("08:30", 0) == 510
    assert textos.a_minutos(None, 99) == 99
    assert textos.a_minutos("todo el día", 7) == 7


def test_fechas():
    assert textos.fechas(date(2027, 7, 16), date(2027, 7, 16)) == "16 de julio"
    assert textos.fechas(date(2027, 7, 24), date(2027, 7, 30)) == "del 24 al 30 de julio"
    assert textos.fechas(date(2026, 12, 28), date(2027, 1, 6)) == "del 28 de diciembre al 6 de enero"
