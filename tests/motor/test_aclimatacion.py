"""El primer día en la altura (decisión 0020): cuándo pesa la altura, qué cansa, cómo es la jornada
tranquila en el planificador y en el plan, y viajes de verdad contra los artefactos de dreemgo/datos."""

import numpy as np
import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import aclimatacion, viaje
from dreemgo.motor import datos as artefactos
from dreemgo.motor.planificador import Candidata, Jornada, Tiempos, admite, mejor_plan

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
H = 60


@pytest.mark.parametrize(
    "base, origen, pesa",
    [
        (3061, 161, True),  # Huaraz desde Lima
        (3830, 3400, False),  # Puno desde el Cusco: ya se vive en la altura
        (4421, 3400, True),  # Marcapomacocha desde el Cusco: 1 021 m más arriba
        (2499, 0, False),  # bajo los 2 500 m no pesa, aunque se suba desde el mar
        (2722, 1899, False),  # Cajamarca desde Huánuco: menos de 1 000 m
        (None, 161, False),  # sin la altura de la base no se sabe
        (3061, None, False),
    ],
)
def test_pesa_la_altura_si_se_duerme_alto_y_se_llega_de_mil_metros_mas_abajo(base, origen, pesa):
    assert aclimatacion.pesa(base, origen) is pesa
    assert aclimatacion.altura_max_del_primer_dia(base, origen) == (base + 500 if pesa else None)


@pytest.mark.parametrize(
    "caminata, visita, cansa",
    [(0, 60, False), (30, 120, False), (31, 60, True), (0, 180, True), (None, None, False)],
)
def test_cansa_una_caminata_de_mas_de_media_hora_o_una_visita_de_mas_de_dos(caminata, visita, cansa):
    assert aclimatacion.exigente({"caminata_min": caminata, "visita_min": visita}) is cansa


def test_una_jornada_tranquila_no_admite_lo_exigente_ni_lo_alto():
    tranquila = Jornada(9 * H, 4 * H, altura_max=3561, tranquila=True)
    assert admite(tranquila, Candidata(0, 1.0, 60, altura=3300))
    assert not admite(tranquila, Candidata(0, 1.0, 60, altura=4453))
    assert not admite(tranquila, Candidata(0, 1.0, 60, altura=3300, exigente=True))
    assert not admite(tranquila, Candidata(0, 1.0, 60, altura=None))  # sin altura no se sabe si sube
    assert admite(Jornada(8 * H, 8 * H), Candidata(0, 1.0, 180, altura=4453, exigente=True))


def test_lo_alto_y_lo_exigente_van_despues_del_dia_tranquilo():
    """Un parque a 4 453 m vale más que todo lo demás junto: igual no va el primer día. El segundo día solo
    le alcanza para el parque, así que lo demás va el primero."""
    t = Tiempos(np.array([20.0, 15.0, 10.0]), np.array([[0, 20, 25], [20, 0, 10], [25, 10, 0.0]]))
    parque = Candidata(0, valor=24.0, visita=180, altura=4453, exigente=True)
    mirador = Candidata(1, valor=2.0, visita=20, altura=3200)
    museo = Candidata(2, valor=2.0, visita=60, altura=3060)
    jornadas = [Jornada(9 * H, 4 * H, altura_max=3561, tranquila=True), Jornada(8 * H, 230)]
    primero, segundo = mejor_plan([parque, mirador, museo], jornadas, t)
    assert {v.candidata.i for v in primero.visitas} <= {1, 2} and primero.visitas
    assert [v.candidata.i for v in segundo.visitas] == [0]


def test_despues_de_un_bus_de_noche_el_dia_tranquilo_empieza_a_las_9():
    plan = viaje.plan_de_noche(3, 8 * H, None, altura_max_del_primer_dia=3561)
    uno, dos, tres = plan.jornadas
    assert (uno.inicio, uno.tope, uno.altura_max, uno.tranquila) == (9 * H, 4 * H, 3561, True)
    assert (dos.tope, dos.altura_max, dos.tranquila) == (8 * H, None, False) and not tres.tranquila
    assert plan.tranquilo == 1
    # Sin altura que pese, como antes: desde una hora después de llegar, y el día entero.
    sin = viaje.plan_de_noche(3, 8 * H, None)
    assert (sin.jornadas[0].inicio, sin.jornadas[0].tope, sin.tranquilo) == (8 * H, 8 * H, None)


def test_por_tierra_de_dia_es_tranquila_la_primera_jornada_en_la_base():
    # Cinco horas de camino: el día de llegada quedan tres para visitar, y esas son las tranquilas.
    plan = viaje.plan_de_dias(4, 5 * H, None, altura_max_del_primer_dia=3561)
    assert plan.dia_de_jornada[0] == 1 and plan.tranquilo == 1
    assert (plan.jornadas[0].tope, plan.jornadas[0].tranquila) == (3 * H, True)
    assert not any(j.tranquila for j in plan.jornadas[1:])
    # Siete horas: el día de llegada no tiene visitas, así que el tranquilo es el siguiente, de 9 a 13.
    plan = viaje.plan_de_dias(5, 7 * H, None, altura_max_del_primer_dia=3561)
    assert plan.dia_de_jornada[0] == 2 and plan.tranquilo == 2
    assert (plan.jornadas[0].inicio, plan.jornadas[0].tope) == (8 * H, 4 * H)


def _zona(datos, nombre: str) -> int:
    [p] = [p.id for p in datos.polos.values() if p.nombre == nombre]
    return p


@con_datos
def test_cada_origen_sabe_a_que_altura_esta():
    """Sin la altura del origen la regla no aplicaría sin que nadie lo note: cada una de las 24 ciudades
    tiene la base de su zona a menos de media hora."""
    datos = artefactos.cargar()
    alturas = {o: aclimatacion.del_origen(origen, datos) for o, origen in datos.origenes.items()}
    assert len(alturas) == 24 and None not in alturas.values()
    assert alturas["lima"] < 300 and alturas["cusco"] == datos.polos[_zona(datos, "Cuzco")].base["altitud_m"]


@con_datos
def test_de_lima_a_huaraz_el_dia_1_es_tranquilo():
    datos = artefactos.cargar()
    huaraz = datos.polos[_zona(datos, "Huaraz")]
    consulta = Consulta(origen="lima", mes=7, dias=3, destino=huaraz.id, intereses=["vida_nocturna"])
    [ruta] = viaje.resolver(consulta, datos).rutas
    assert ruta.traslado.bus_de_noche is not None
    uno, *demas = ruta.dias
    assert uno.tranquilo and not any(d.tranquilo for d in demas)
    assert uno.paradas and uno.horas <= 4
    assert int(uno.paradas[0].llegada[:2]) * 60 + int(uno.paradas[0].llegada[3:]) >= 9 * H
    for p in uno.paradas:
        r = datos.recursos[p.recurso.codigo]
        assert r["altitud_m"] <= huaraz.base["altitud_m"] + 500 and not aclimatacion.exigente(r)
    # El Huascarán, a 4 453 m y con tres horas de visita, va otro día.
    assert "Parque Nacional Huascarán" in {p.recurso.nombre for d in demas for p in d.paradas}
    # Y la primera noche, con vida nocturna, es de descanso: la misma regla.
    assert uno.noche is not None and uno.noche.tipo == "descanso"


@con_datos
def test_desde_el_cusco_a_puno_no_hay_dia_tranquilo():
    datos = artefactos.cargar()
    consulta = Consulta(origen="cusco", mes=7, dias=4, destino=_zona(datos, "Puno"))
    [ruta] = viaje.resolver(consulta, datos).rutas
    assert not any(d.tranquilo for d in ruta.dias)
    [aviso] = [a.mensaje for a in ruta.avisos if a.tipo == "aclimatacion"]
    assert aviso.endswith("conviene un primer día tranquilo.")
