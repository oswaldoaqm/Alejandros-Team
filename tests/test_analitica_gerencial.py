"""Comprobaciones de denominadores, fechas y separación temporal del panel."""

from datetime import date, timedelta
from math import sqrt

import pytest

from dreemgo.analitica import resumir
from dreemgo.analitica_gerencial import analizar, proyectar, resumen_latencia


def evento(sesion, tipo, instante="2026-11-10T15:00:00Z", **datos):
    return {"sesion": str(sesion), "tipo": tipo, "instante": instante, **datos}


def serie(valores):
    inicio = date(2026, 10, 1)
    return [{"fecha": inicio + timedelta(days=i), "sesiones": valor} for i, valor in enumerate(valores)]


def test_vacio_no_inventa_estadisticas_ni_proyeccion():
    datos = analizar([], [], "real")
    assert datos.distribucion == []
    assert datos.pareto == []
    assert len(datos.mapa_calor) == 168
    assert sum(c.acciones for c in datos.mapa_calor) == 0
    assert datos.latencia.n == 0
    assert datos.latencia.media is None
    assert all(p.r is None and p.n == 0 for p in datos.correlacion.pares)
    assert all(e.porcentaje is None for e in datos.embudo)
    assert datos.proyeccion.estado == "insuficiente"
    assert datos.proyeccion.futuro == []


def test_distribucion_exclusiva_y_pareto_usan_sesiones_no_acciones():
    datos = analizar(
        [
            evento("a", "busqueda_resultado", resultados=3),
            evento("a", "itinerario_abierto"),
            evento("a", "viaje_guardado"),
            evento("a", "viaje_guardado"),
            evento("b", "itinerario_abierto"),
            evento("b", "itinerario_abierto"),
            evento("c", "formulario_abierto"),
            evento("d", "formulario_abierto"),
            evento("e", "error_consulta"),
        ],
        [],
        "simulacion",
    )
    assert sum(d.cantidad for d in datos.distribucion) == 5
    assert {d.id: d.cantidad for d in datos.distribucion} == {
        "guardado": 1,
        "abierto": 1,
        "formulario": 2,
        "error": 1,
    }
    assert sum(p.cantidad for p in datos.pareto) == 4
    assert [p.cantidad for p in datos.pareto] == [2, 1, 1]
    assert [p.acumulado for p in datos.pareto] == [50, 75, 100]


def test_guardado_priorizado_no_atribuye_fracaso_por_error_anterior():
    datos = analizar([evento(1, "error_consulta"), evento(1, "viaje_guardado")], [], "real")
    assert datos.distribucion[0].id == "guardado"
    assert datos.pareto == []


def test_embudo_requiere_secuencia_y_no_cuenta_dos_veces():
    pasos = ["formulario_abierto", "busqueda_iniciada", "busqueda_resultado", "itinerario_abierto", "viaje_guardado"]
    eventos = [evento(1, tipo, resultados=3) for tipo in pasos]
    eventos += [evento(1, tipo, resultados=3) for tipo in pasos]
    eventos += [evento(2, "viaje_guardado")]
    eventos += [evento(3, tipo, resultados=3) for tipo in reversed(pasos)]
    etapas = analizar(eventos, [], "simulacion").embudo
    assert [e.sesiones for e in etapas] == [3, 2, 1, 1, 1, 1]
    assert etapas[-1].porcentaje == 33.3


def test_embudo_no_considera_respuesta_vacia_como_viajes_recibidos():
    eventos = [
        evento(1, "formulario_abierto"),
        evento(1, "busqueda_iniciada"),
        evento(1, "busqueda_resultado", resultados=0),
        evento(1, "itinerario_abierto"),
    ]
    datos = analizar(eventos, [], "real")
    assert [e.sesiones for e in datos.embudo] == [1, 1, 1, 0, 0, 0]


def test_calor_convierte_a_lunes_y_hora_local_peru():
    datos = analizar([evento(1, "sesion_iniciada", "2026-11-10T04:30:00Z")], [], "real")
    activas = [c for c in datos.mapa_calor if c.acciones]
    assert [(c.dia, c.hora, c.acciones) for c in activas] == [(0, 23, 1)]


def test_latencia_cuenta_respuestas_percentiles_y_desviacion_muestral():
    eventos = [evento(i, "busqueda_resultado", resultados=3, duracion_ms=v) for i, v in enumerate([100, 200, 300, 400])]
    eventos.append(evento(5, "busqueda_iniciada", duracion_ms=10_000))
    datos = resumen_latencia(eventos)
    assert datos.n == 4
    assert datos.media == datos.mediana == 250
    assert datos.p25 == 175 and datos.p75 == 325 and datos.p95 == 385
    assert datos.desviacion == pytest.approx(sqrt(50_000 / 3), abs=0.01)
    assert sum(b.cantidad for b in datos.histograma) == datos.n
    assert datos.histograma[-1].cantidad == 1  # incluye el máximo


def test_latencia_un_solo_valor_no_inventa_desviacion():
    datos = resumen_latencia([evento(1, "busqueda_resultado", resultados=3, duracion_ms=400)])
    assert datos.media == datos.mediana == 400
    assert datos.desviacion is None
    assert len(datos.histograma) == 1 and datos.histograma[0].cantidad == 1


def test_pearson_pares_completos_y_constantes():
    eventos = [evento(i, "busqueda_iniciada", dias=i + 1, presupuesto=1000 - 100 * i) for i in range(5)]
    eventos.append(evento(8, "busqueda_iniciada", dias=9))  # sin presupuesto
    datos = analizar(eventos, [], "real")
    pares = {(p.x, p.y): p for p in datos.correlacion.pares}
    assert pares["dias", "presupuesto"].n == 5
    assert pares["dias", "presupuesto"].r == -1
    assert pares["presupuesto", "dias"].r == -1
    assert pares["interacciones", "interacciones"].r is None  # constantes en cero
    assert pares["latencia", "dias"].r is None
    assert len(datos.dispersion) == 5


def test_pearson_menos_de_cinco_no_muestra_coeficiente():
    datos = analizar(
        [evento(i, "busqueda_iniciada", dias=i + 1, presupuesto=100 * (i + 1)) for i in range(4)], [], "real"
    )
    par = next(p for p in datos.correlacion.pares if p.x == "dias" and p.y == "presupuesto")
    assert par.n == 4 and par.r is None


def test_ultima_consulta_define_dispersion_y_no_expone_sesion():
    datos = analizar(
        [
            evento("identificador-privado", "busqueda_iniciada", dias=3, presupuesto=500),
            evento("identificador-privado", "busqueda_iniciada", "2026-11-10T16:00:00Z", dias=6, presupuesto=1000),
        ],
        [],
        "real",
    )
    assert [(p.dias, p.presupuesto) for p in datos.dispersion] == [(6, 1000)]
    assert "identificador-privado" not in datos.model_dump_json()


def test_serie_completa_huecos_sin_extender_rango_observado():
    datos = resumir(
        [
            evento(1, "sesion_iniciada", "2026-11-01T12:00:00Z"),
            evento(2, "sesion_iniciada", "2026-11-03T12:00:00Z"),
        ],
        "real",
        desde=date(2000, 1, 1),
        hasta=date(2099, 1, 1),
    )
    assert [p.sesiones for p in datos.serie] == [1, 0, 1]


@pytest.mark.parametrize("cantidad", [0, 1, 7, 20])
def test_proyeccion_exige_21_dias(cantidad):
    datos = proyectar(serie([2] * cantidad), "simulacion")
    assert datos.estado == "insuficiente"
    assert datos.futuro == []


def test_tendencia_perfecta_elige_lineal_y_valida_sin_fuga():
    datos = proyectar(serie([3 + 2 * i for i in range(28)]), "simulacion")
    assert datos.metodo == "Tendencia lineal"
    assert datos.mae_validacion == 0
    assert datos.n_validacion == 7 and datos.dias_historia == 28
    assert [p.valor for p in datos.futuro] == [59, 61, 63, 65, 67, 69, 71]
    assert datos.futuro[0].fecha == date(2026, 10, 29)


def test_validacion_no_usa_la_semana_reservada_para_entrenar():
    datos = proyectar(serie([1] * 21 + [200] * 7), "simulacion")
    assert all(c.mae == 199 for c in datos.candidatos)
    assert datos.metodo == "Promedio de los últimos 7 días"  # empate: modelo sencillo
    assert [p.valor for p in datos.futuro] == [200] * 7  # reajuste posterior con historia completa


def test_real_excluye_dia_actual_y_futuro_de_validacion_y_proyeccion():
    datos = proyectar(serie([2] * 28), "real", hoy=date(2026, 10, 22))
    assert datos.dias_historia == 21
    assert datos.historico[-1].fecha == date(2026, 10, 21)
    assert datos.futuro[0].fecha == date(2026, 10, 22)


def test_tendencia_descendente_no_genera_sesiones_negativas():
    datos = proyectar(serie(list(range(28, 0, -1))), "simulacion")
    assert datos.metodo == "Tendencia lineal"
    assert all(p.valor == 0 for p in datos.futuro)
