"""Las reglas del motor que no dependen de los artefactos."""

from datetime import date

import pytest

from dreemgo.motor import viaje


def test_valor_de_una_parada():
    r = {"jerarquia": 4, "intereses": ["historia"]}
    assert [viaje.valor({"jerarquia": j, "intereses": []}, set()) for j in (1, 2, 3, 4)] == [1, 2, 6, 24]
    assert viaje.valor({"jerarquia": None, "intereses": []}, set()) == viaje.VALOR_SIN_JERARQUIA == 2
    assert viaje.valor(r, {"historia", "playa"}) == 24
    assert viaje.valor(r, {"playa"}) == 24 * viaje.FACTOR_SIN_INTERES


def test_visita_con_caminata_de_ida_y_vuelta():
    assert viaje.minutos_de_visita({"visita_min": 90, "caminata_min": 30}) == 150
    assert viaje.minutos_de_visita({"visita_min": None, "caminata_min": None}) == viaje.VISITA_POR_DEFECTO_MIN


def test_un_viaje_corto_usa_el_dia_de_llegada_y_el_de_salida():
    plan = viaje.plan_de_dias(dias=4, minutos_ida=150, fecha_inicio=None)
    assert (plan.llegada, plan.salida) == (1, 4)
    assert plan.tramos == {1: 150, 4: 150}
    assert plan.dia_de_jornada == [1, 2, 3, 4]
    llegada, *_, salida = plan.jornadas
    assert (llegada.inicio, llegada.tope) == (viaje.SALIDA_DEL_ORIGEN + 150, 330)
    assert (salida.inicio, salida.tope) == (viaje.INICIO_DE_VISITAS, 330)


def test_mas_de_nueve_horas_se_parten_en_partes_iguales():
    plan = viaje.plan_de_dias(dias=6, minutos_ida=600, fecha_inicio=None)
    assert plan.tramos == {1: 300, 2: 300, 5: 300, 6: 300}
    assert (plan.llegada, plan.salida) == (2, 5)
    assert plan.dia_de_jornada == [2, 3, 4, 5]  # con 5 horas de viaje, el día de llegada y el de salida se visita
    # Un minuto más de nueve horas ya son dos días de ida.
    assert viaje.plan_de_dias(dias=6, minutos_ida=541, fecha_inicio=None).tramos == {1: 271, 2: 270, 5: 270, 6: 271}


def test_un_dia_de_solo_viaje_puede_durar_hasta_nueve_horas():
    for ida in (481, 488, 540):  # 488: de Lima a Huaraz
        plan = viaje.plan_de_dias(dias=4, minutos_ida=ida, fecha_inicio=None)
        assert plan.tramos == {1: ida, 4: ida} and (plan.llegada, plan.salida) == (1, 4)
        assert plan.dia_de_jornada == [2, 3]  # los dos días de viaje no tienen visitas
        assert [(j.inicio, j.tope) for j in plan.jornadas] == [(viaje.INICIO_DE_VISITAS, viaje.JORNADA_MIN)] * 2
    # Y un viaje de ida y vuelta en dos días sigue sin caber: no quedaría ningún día allá.
    assert viaje.plan_de_dias(dias=2, minutos_ida=488, fecha_inicio=None).jornadas == []


def test_un_dia_con_visitas_no_pasa_de_ocho_horas_con_el_viaje():
    for ida in range(30, 2000, 7):
        plan = viaje.plan_de_dias(dias=14, minutos_ida=ida, fecha_inicio=None)
        tope = dict(zip(plan.dia_de_jornada, (j.tope for j in plan.jornadas), strict=True))
        for dia, viaje_min in plan.tramos.items():
            assert viaje_min <= viaje.SOLO_VIAJE_MAX_MIN
            if dia in tope:  # ese día, además de viajar, se visita
                assert viaje_min + tope[dia] <= viaje.JORNADA_MIN
        assert all(t <= viaje.JORNADA_MIN for t in tope.values())


def test_sin_dias_para_ir_y_volver_no_hay_plan():
    assert viaje.plan_de_dias(dias=3, minutos_ida=600, fecha_inicio=None) is None


def test_si_casi_todo_el_dia_es_carretera_ese_dia_no_se_visita():
    plan = viaje.plan_de_dias(dias=3, minutos_ida=420, fecha_inicio=None)
    assert plan.dia_de_jornada == [2]  # 60 minutos libres no alcanzan para visitar


def test_con_fecha_cada_jornada_sabe_su_dia_de_la_semana():
    plan = viaje.plan_de_dias(dias=3, minutos_ida=60, fecha_inicio=date(2027, 7, 26))  # lunes
    assert [j.dia_semana for j in plan.jornadas] == [0, 1, 2]


@pytest.mark.parametrize("mes, anio", [(10, 2026), (12, 2026), (1, 2027), (9, 2027)])
def test_anio_de_referencia(mes, anio):
    assert viaje.anio_de_referencia("2026.10.1", mes) == anio


def test_ventana_del_viaje():
    from dreemgo.contrato import Consulta

    assert viaje.ventana(Consulta(mes=2, dias=4), "2026.10.1") == (date(2027, 2, 1), date(2027, 2, 28))
    con_fecha = Consulta(fecha_inicio=date(2027, 7, 30), dias=4)
    assert viaje.ventana(con_fecha, "2026.10.1") == (date(2027, 7, 30), date(2027, 8, 2))


def test_mejores_meses_de_menos_a_mas_lluvia():
    clima = [
        {"mes": m, "veredicto": "viable" if m in (6, 7, 8) else "advertencia", "lluvia_mm": 30 - m}
        for m in range(1, 13)
    ]
    assert viaje.mejores_meses(tuple(clima)) == [8, 7, 6]
    selva = [{"mes": m, "veredicto": "advertencia", "lluvia_mm": 200 + m} for m in range(1, 13)]
    assert viaje.mejores_meses(tuple(selva))[0] == 1  # sin meses viables, los de advertencia
