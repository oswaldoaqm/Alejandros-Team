"""
Las propiedades de docs/CONTRATO.md §3, sobre consultas generadas al azar, y lo que esas
propiedades piden cuando además hay eventos publicados por los municipios.

Corren contra los artefactos de dreemgo/datos. Por defecto, 100 consultas (las mismas en
cada corrida: hypothesis va en modo determinista). Las mil del plan:

    DREEMGO_PROPIEDADES=1000 pytest tests/test_propiedades.py
"""

from __future__ import annotations

import math
import os
import re
from datetime import date, datetime, timedelta, timezone

import pytest
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from dreemgo.contrato import (
    ALTITUD_MAX_M,
    DIAS_MAX,
    DIAS_MIN,
    PRESUPUESTO_MAX,
    PRESUPUESTO_MIN,
    Consulta,
    EventoNuevo,
    Interes,
)
from dreemgo.motor import datos as artefactos
from dreemgo.motor.viaje import resolver, ventana
from dreemgo.publicados import RADIO_KM, Instantanea, Publicado

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
CONSULTAS = int(os.environ.get("DREEMGO_PROPIEDADES", "100"))
FICHA = re.compile(r"^https://consultasenlinea\.mincetur\.gob\.pe/fichaInventario/index\.aspx\?cod_Ficha=\d+$")
POLO = re.compile(r"\bpolos?\b", re.IGNORECASE)


@st.composite
def consultas(draw) -> Consulta:
    datos = artefactos.cargar()
    origenes = sorted(datos.origenes)
    con_fecha = draw(st.booleans())
    # Una de cada tres, más o menos, con un destino elegido: no va con «Sorpréndeme».
    destino = draw(st.one_of(st.none(), st.none(), st.sampled_from(sorted(datos.polos))))
    fecha = draw(st.dates(date(2026, 10, 1), date(2027, 12, 31))) if con_fecha else None
    return Consulta(
        origen=draw(st.sampled_from(origenes)),
        mes=None if con_fecha else draw(st.integers(1, 12)),
        fecha_inicio=fecha,
        dias=draw(st.integers(DIAS_MIN, DIAS_MAX)),
        intereses=draw(st.lists(st.sampled_from(list(Interes)), max_size=3, unique=True)),
        presupuesto=draw(st.one_of(st.none(), st.integers(PRESUPUESTO_MIN, PRESUPUESTO_MAX))),
        altitud_max=draw(st.one_of(st.none(), st.integers(0, ALTITUD_MAX_M))),
        sorpresa=destino is None and draw(st.booleans()),
        solo_por_tierra=draw(st.booleans()),
        destino=destino,
    )


def _hhmm(texto: str) -> int:
    h, m = texto.split(":")
    return int(h) * 60 + int(m)


def _la_noche(consulta: Consulta, ruta) -> None:
    """La noche (desde 1.5): solo las que se duermen en la base, solo lo que la consulta pide, a lo más
    una de estrellas, y cada lugar para salir a pie de la base."""
    noches = [d for d in ruta.dias if d.noche is not None]
    pide_salir = Interes.vida_nocturna in consulta.intereses
    pide_estrellas = Interes.naturaleza in consulta.intereses or not consulta.intereses
    for d in noches:
        # Se duerme en la base: no es un viaje de un día ni el día en que se deja, y si es de ida,
        # es el último tramo.
        assert d.tipo not in ("ida_visita_y_vuelta", "vuelta", "visita_y_vuelta")
        if d.tipo == "ida":
            assert all(otro.tipo != "ida" for otro in ruta.dias if otro.numero > d.numero)
        assert d.noche.tipo != "salir" or pide_salir
        assert d.noche.tipo != "descanso" or pide_salir
        assert d.noche.tipo != "estrellas" or pide_estrellas
        assert len(d.noche.lugares) <= 3 and all(lugar.minutos_a_pie <= 30 for lugar in d.noche.lugares)
        assert (d.noche.cielo is not None) == (d.noche.tipo == "estrellas")
    assert sum(1 for d in noches if d.noche.tipo == "estrellas") <= 1


def _el_almuerzo(consulta: Consulta, ruta) -> None:
    """12. El almuerzo (desde 1.6): solo en un día con paradas, desde las 11:30, en su lugar entre las
    paradas; y si un día con paradas no lo trae, es porque sus visitas terminan antes de las 12:30."""
    deposito = ruta.traslado.desde if consulta.dias == 1 else ruta.polo.base.nombre
    for d in ruta.dias:
        a = d.almuerzo
        if a is None:
            if d.paradas:
                ultima = d.paradas[-1]
                assert _hhmm(ultima.llegada) + ultima.minutos_visita < 12 * 60 + 30
            continue
        assert d.paradas and _hhmm(a.hora) >= 11 * 60 + 30
        assert 0 <= a.despues_de <= len(d.paradas)
        if a.despues_de:
            assert _hhmm(a.hora) >= _hhmm(d.paradas[a.despues_de - 1].llegada)
        if a.despues_de < len(d.paradas):
            assert _hhmm(a.hora) + 60 <= _hhmm(d.paradas[a.despues_de].llegada)
        assert a.en_la_base == (a.lugar == deposito)
        assert a.hay_donde_comer is not False or not a.en_la_base
        if a.hay_donde_comer is False:
            event("algún almuerzo donde no hay registrado dónde comer")


def _el_bus_de_noche(consulta: Consulta, ruta) -> None:
    """13. El bus de noche (desde 1.6): solo por carretera, de 7 a 16 horas, en un viaje de dos días o
    más y si ida y vuelta no se llevan el 40 % de las horas del viaje, con sus noches. Sus noches van
    fuera de los días: sale a las 19:00 o después, ningún día lleva horas de camino y el día 1 se visita
    desde una hora después de llegar. Y lo que cumple todo eso va en bus de noche."""
    t = ruta.traslado
    solo_carretera = t.medios == ["carretera"] and t.horas is not None and consulta.dias >= 2
    if t.bus_de_noche is None:
        # Las horas vienen redondeadas a la décima: en los bordes manda la cuenta del motor.
        adentro = solo_carretera and 7.1 <= t.horas <= 15.9
        assert not (adentro and 2 * t.horas < 0.4 * 24 * consulta.dias - 0.2)
        return
    assert solo_carretera and 7.0 <= t.horas <= 16.0 and 2 * t.horas < 0.4 * 24 * consulta.dias + 0.2
    assert t.dias_de_viaje == 0
    event("alguna ruta en bus de noche")
    assert _hhmm(t.bus_de_noche.sale) >= 19 * 60 and _hhmm(t.bus_de_noche.llega) < 12 * 60
    assert [d.tipo for d in ruta.dias][:: len(ruta.dias) - 1] in (
        ["ida_y_visita", "visita_y_vuelta"],
        ["ida", "visita_y_vuelta"],
        ["ida_y_visita", "vuelta"],
        ["ida", "vuelta"],
    )
    assert all(d.tipo == "visita" for d in ruta.dias[1:-1])
    if ruta.dias[0].paradas:
        assert _hhmm(ruta.dias[0].paradas[0].llegada) >= _hhmm(t.bus_de_noche.llega) + 60


@settings(
    max_examples=CONSULTAS,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(consultas())
def test_las_propiedades(consulta):
    datos = artefactos.cargar()
    respuesta = resolver(consulta, datos)
    desde, hasta = ventana(consulta, datos.version)
    assert bool(respuesta.rutas) != (respuesta.sin_resultado is not None)

    for ruta in respuesta.rutas:
        paradas = [p for d in ruta.dias for p in d.paradas]
        # 1. Ninguna parada supera la altitud máxima.
        if consulta.altitud_max is not None:
            assert all(p.recurso.altitud_m is not None and p.recurso.altitud_m <= consulta.altitud_max for p in paradas)
        # 2. Los días suman exactamente los pedidos, con la ida y la vuelta.
        assert [d.numero for d in ruta.dias] == list(range(1, consulta.dias + 1))
        # 3. Ninguna jornada con visitas pasa de 8 horas, sin el almuerzo, ni un día de solo viaje de 9.
        assert all(d.horas <= (8.0 if d.paradas else 9.0) for d in ruta.dias)
        # 4. Toda parada enlaza a su ficha oficial.
        assert all(FICHA.match(str(p.recurso.url_ficha)) for p in paradas)
        # 5. Un mes desaconsejado nunca aparece sin aviso, y hay una alternativa.
        if ruta.estacionalidad.veredicto == "desaconsejado":
            assert any(a.tipo == "estacionalidad" for a in ruta.avisos)
            assert ruta.estacionalidad.mejores_meses
        # 6. Un evento solo aparece si cae dentro de las fechas o del mes del viaje.
        assert all(e.fecha_inicio <= hasta and e.fecha_fin >= desde for e in ruta.eventos)
        # 10. Lo que la fuente no trae viaja como null.
        for p in paradas:
            fuente = datos.recursos[p.recurso.codigo]
            assert (p.recurso.jerarquia, p.recurso.tarifa_soles, p.recurso.altitud_m) == (
                fuente["jerarquia"],
                fuente["tarifa_soles"],
                fuente["altitud_m"],
            )
        assert ruta.estacionalidad.horas_sol is None
        # Y lo que el itinerario dice de sí mismo es coherente.
        for d in ruta.dias:
            llegadas = [_hhmm(p.llegada) for p in d.paradas]
            assert llegadas == sorted(llegadas)
            assert [p.orden for p in d.paradas] == list(range(1, len(d.paradas) + 1))
        assert ruta.indicadores.paradas == len(paradas)
        # Y lo que el viajero lee del clima habla de la zona, como la app, no del polo.
        del_clima = [a.mensaje for a in ruta.avisos if a.tipo in ("datos", "estacionalidad")]
        assert not any(POLO.search(frase) for frase in [ruta.estacionalidad.explicacion, *del_clima])
        _la_noche(consulta, ruta)
        _el_almuerzo(consulta, ruta)
        _el_bus_de_noche(consulta, ruta)
    if respuesta.sin_resultado is not None:
        assert not POLO.search(respuesta.sin_resultado.motivo)
        assert not any("ruta" in s.efecto for s in respuesta.sin_resultado.sugerencias)
        # Y cada sugerencia, aceptada sola, hace salir algún viaje.
        for s in respuesta.sin_resultado.sugerencias:
            assert resolver(consulta.model_copy(update={s.campo: s.valor}), datos, sugerir=False).rutas

    # 9. Las rutas son de polos distintos; con destino, una como mucho, y es la de esa zona.
    polos = [r.polo.id for r in respuesta.rutas]
    assert len(polos) == len(set(polos))
    if consulta.destino is not None:
        assert polos in ([], [consulta.destino])
    # Y el viaje a una zona es el mismo cuando la elige el motor que cuando la elige el viajero:
    # solo cambia el puntaje, que la compara con las demás.
    if consulta.destino is None and respuesta.rutas:
        ruta = respuesta.rutas[-1]
        [elegida] = resolver(consulta.model_copy(update={"destino": ruta.polo.id, "sorpresa": False}), datos).rutas
        assert elegida.model_dump(exclude={"puntaje"}) == ruta.model_dump(exclude={"puntaje"})

    # 8. La misma consulta con los mismos datos da exactamente la misma respuesta.
    assert resolver(consulta, datos).model_dump_json() == respuesta.model_dump_json()

    # Y la vida nocturna no cambia el día: en la misma zona, sin ella, las paradas, sus horas, el
    # traslado y el costo son los mismos (desde 1.5).
    if Interes.vida_nocturna in consulta.intereses and respuesta.rutas:
        ruta = respuesta.rutas[0]
        sin_noche = consulta.model_copy(
            update={
                "intereses": [i for i in consulta.intereses if i != Interes.vida_nocturna],
                "destino": ruta.polo.id,
                "sorpresa": False,
            }
        )
        [del_dia] = resolver(sin_noche, datos).rutas
        assert [d.model_dump(exclude={"noche"}) for d in ruta.dias] == [
            d.model_dump(exclude={"noche"}) for d in del_dia.dias
        ]
        assert (ruta.costo, ruta.traslado) == (del_dia.costo, del_dia.traslado)

    # 7. El presupuesto ordena, elige y avisa. Con él salen tantas rutas como sin él; una que
    #    entra en el presupuesto y salía sin él sigue saliendo; y la que lo pasa lleva su aviso.
    if consulta.presupuesto is not None:
        sin_presupuesto = resolver(consulta.model_copy(update={"presupuesto": None}), datos)
        assert len(polos) == len(sin_presupuesto.rutas)
        for ruta in sin_presupuesto.rutas:
            if ruta.costo.p50 <= consulta.presupuesto:
                assert ruta.polo.id in polos
        for ruta in respuesta.rutas:
            if ruta.costo.exceso:
                assert any(a.tipo == "presupuesto" for a in ruta.avisos)


# ─────────────────────────────── con eventos publicados ───────────────────────────────

PUBLICADO_EL = datetime(2026, 10, 2, 9, 0, tzinfo=timezone(timedelta(hours=-5)))


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine, punto a punto: otra cuenta que la del motor, para comprobarla."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _le_toca(publicado: Publicado, polo: int, datos) -> bool:
    """Si el evento queda a RADIO_KM o menos de donde se duerme en el polo o de alguno de sus lugares."""
    if publicado.lat is None or publicado.lon is None:
        return False
    base = datos.polos[polo].base
    lugares = [(base["lat"], base["lon"])]
    lugares += [(r["lat"], r["lon"]) for r in datos.recursos.values() if r["polo"] == polo]
    return any(_km(publicado.lat, publicado.lon, lat, lon) <= RADIO_KM for lat, lon in lugares)


@st.composite
def publicados(draw, desde: date, hasta: date, bases: list[dict]) -> list[Publicado]:
    """Eventos alrededor de las fechas del viaje: unos donde se duerme en las rutas propuestas
    (para que caigan en ellas), otros junto a cualquier lugar del inventario y otros sin lugar."""
    datos = artefactos.cargar()
    codigos = sorted(datos.recursos)
    lista = []
    for n in range(draw(st.integers(1, 6))):
        donde = draw(st.sampled_from(["base", "lugar", "sin lugar"] if bases else ["lugar", "sin lugar"]))
        if donde == "base":
            punto = draw(st.sampled_from(bases))
        elif donde == "lugar":
            punto = datos.recursos[draw(st.sampled_from(codigos))]
        else:
            punto = {"lat": None, "lon": None}
        corrido = draw(st.floats(-0.12, 0.12)) if punto["lat"] is not None else 0.0  # hasta unos 13 km
        inicio = desde + timedelta(days=draw(st.integers(-5, (hasta - desde).days + 5)))
        lista.append(
            Publicado.nuevo(
                EventoNuevo(
                    nombre=f"Evento de prueba {n}",
                    fecha_inicio=inicio,
                    fecha_fin=inicio + timedelta(days=draw(st.integers(0, 6))),
                    distrito="Distrito",
                    provincia="Provincia",
                    region="Lima",
                    lat=None if punto["lat"] is None else max(-18.4, min(0.1, punto["lat"] + corrido)),
                    lon=punto["lon"],
                    publicado_por="Municipalidad de prueba",
                ),
                PUBLICADO_EL,
            )
        )
    return lista


def _sin_lo_publicado(respuesta) -> dict:
    """La respuesta sin los eventos publicados y sin la versión de datos, que es lo único que
    publicar puede cambiar."""
    contenido = respuesta.model_dump(mode="json")
    for ruta in contenido["rutas"]:
        ruta["eventos"] = [e for e in ruta["eventos"] if e["fuente"] != "publicado"]
    del contenido["version_datos"]
    return contenido


@settings(
    max_examples=max(10, CONSULTAS // 4),
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(consultas(), st.data())
def test_lo_publicado_se_suma_sin_mover_las_rutas(consulta, data):
    datos = artefactos.cargar()
    sin_publicar = resolver(consulta, datos)
    desde, hasta = ventana(consulta, datos.version)
    bases = [r.polo.base.model_dump() for r in sin_publicar.rutas]
    lista = data.draw(publicados(desde, hasta, bases))
    instantanea = Instantanea.de(lista, datos)

    respuesta = resolver(consulta, datos, instantanea)

    # Publicar no cambia qué polos se proponen, ni su orden, ni sus motivos, días o costos.
    assert _sin_lo_publicado(respuesta) == _sin_lo_publicado(sin_publicar)
    assert sin_publicar.version_datos == datos.version
    assert respuesta.version_datos == instantanea.version(datos.version) != datos.version

    for ruta in respuesta.rutas:
        en_la_ruta = {e.id for e in ruta.eventos if e.fuente == "publicado"}
        # 6. Solo los que caen en las fechas del viaje; y de esos, los que quedan cerca de este polo y nada más.
        esperados = {
            p.id
            for p in instantanea.eventos
            if p.fecha_inicio <= hasta and p.fecha_fin >= desde and _le_toca(p, ruta.polo.id, datos)
        }
        assert en_la_ruta == esperados
        assert all(e.publicado_por and e.precision_fecha == "exacta" for e in ruta.eventos if e.fuente == "publicado")
        orden = [(e.fecha_inicio, e.id) for e in ruta.eventos]
        assert orden == sorted(orden) and len(set(orden)) == len(orden)

    # Para ver con `pytest --hypothesis-show-statistics` que la prueba no pasa en vacío.
    en_rutas = sum(1 for ruta in respuesta.rutas for e in ruta.eventos if e.fuente == "publicado")
    event(f"eventos publicados que salen en alguna ruta: {'ninguno' if en_rutas == 0 else 'alguno'}")

    # 8. La misma consulta con la misma versión de datos da exactamente la misma respuesta,
    # lleguen los eventos del almacén en el orden en que lleguen.
    otra_vez = resolver(consulta, datos, Instantanea.de(reversed(lista), datos))
    assert otra_vez.model_dump_json() == respuesta.model_dump_json()
