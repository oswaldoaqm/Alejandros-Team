"""
Las diez propiedades de docs/CONTRATO.md §3, sobre consultas generadas al azar, y lo que
esas propiedades piden cuando además hay eventos publicados por los municipios.

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
    origenes = sorted(artefactos.cargar().origenes)
    con_fecha = draw(st.booleans())
    fecha = draw(st.dates(date(2026, 10, 1), date(2027, 12, 31))) if con_fecha else None
    return Consulta(
        origen=draw(st.sampled_from(origenes)),
        mes=None if con_fecha else draw(st.integers(1, 12)),
        fecha_inicio=fecha,
        dias=draw(st.integers(DIAS_MIN, DIAS_MAX)),
        intereses=draw(st.lists(st.sampled_from(list(Interes)), max_size=3, unique=True)),
        presupuesto=draw(st.one_of(st.none(), st.integers(PRESUPUESTO_MIN, PRESUPUESTO_MAX))),
        altitud_max=draw(st.one_of(st.none(), st.integers(0, ALTITUD_MAX_M))),
        sorpresa=draw(st.booleans()),
    )


def _hhmm(texto: str) -> int:
    h, m = texto.split(":")
    return int(h) * 60 + int(m)


@settings(
    max_examples=CONSULTAS,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(consultas())
def test_las_diez_propiedades(consulta):
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
        # 3. Ninguna jornada con visitas pasa de 8 horas, ni un día de solo viaje de 9.
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
    if respuesta.sin_resultado is not None:
        assert not POLO.search(respuesta.sin_resultado.motivo)
        assert not any("ruta" in s.efecto for s in respuesta.sin_resultado.sugerencias)

    # 9. Las rutas son de polos distintos.
    polos = [r.polo.id for r in respuesta.rutas]
    assert len(polos) == len(set(polos))

    # 8. La misma consulta con los mismos datos da exactamente la misma respuesta.
    assert resolver(consulta, datos).model_dump_json() == respuesta.model_dump_json()

    # 7. El presupuesto ordena y advierte, pero nunca esconde una ruta.
    if consulta.presupuesto is not None:
        sin_presupuesto = resolver(consulta.model_copy(update={"presupuesto": None}), datos)
        assert sorted(polos) == sorted(r.polo.id for r in sin_presupuesto.rutas)
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
