"""
Las diez propiedades de docs/CONTRATO.md §3, sobre consultas generadas al azar.

Corren contra los artefactos de dreemgo/datos. Por defecto, 100 consultas (las mismas en
cada corrida: hypothesis va en modo determinista). Las mil del plan:

    DREEMGO_PROPIEDADES=1000 pytest tests/test_propiedades.py
"""

from __future__ import annotations

import os
import re
from datetime import date

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from dreemgo.contrato import ALTITUD_MAX_M, DIAS_MAX, DIAS_MIN, PRESUPUESTO_MAX, PRESUPUESTO_MIN, Consulta, Interes
from dreemgo.motor import datos as artefactos
from dreemgo.motor.viaje import resolver, ventana

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
CONSULTAS = int(os.environ.get("DREEMGO_PROPIEDADES", "100"))
FICHA = re.compile(r"^https://consultasenlinea\.mincetur\.gob\.pe/fichaInventario/index\.aspx\?cod_Ficha=\d+$")


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
        # 3. Ninguna jornada pasa de 8 horas.
        assert all(d.horas <= 8.0 for d in ruta.dias)
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
