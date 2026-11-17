"""El ejemplo del panel debe ser coherente y seguir marcado como ficticio."""

import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from hashlib import sha256

import pytest

from dreemgo.analitica import EventoUso
from evaluacion.simular_actividad import EMPAQUETADA, HORA_PERU, SALIDA, generar, guardar


def test_archivo_reproducible_y_sin_datos_personales():
    archivo = json.loads(SALIDA.read_text(encoding="utf-8"))
    assert archivo == generar()
    assert archivo["meta"]["tipo"] == "simulacion"
    assert archivo["meta"]["sesiones"] == 200
    assert archivo["meta"]["usuarios_ficticios"] == 200
    assert archivo["meta"]["sesiones_por_usuario"] == 1
    assert sha256(SALIDA.read_bytes()).hexdigest() == sha256(EMPAQUETADA.read_bytes()).hexdigest()
    assert len({e["sesion"] for e in archivo["eventos"]}) == 200
    assert len({u["usuario_ficticio"] for u in archivo["usuarios"]}) == 200
    assert len({u["sesion"] for u in archivo["usuarios"]}) == 200
    prohibidos = {"nombre", "correo", "email", "telefono", "compra", "venta", "pago", "reserva"}
    assert all(not (prohibidos & evento.keys()) for evento in archivo["eventos"])
    assert all(not (prohibidos & usuario.keys()) for usuario in archivo["usuarios"])


def test_acciones_de_cada_sesion_son_posibles_en_la_web():
    por_sesion = defaultdict(list)
    for evento in generar()["eventos"]:
        por_sesion[evento["sesion"]].append(evento)
    for eventos in por_sesion.values():
        eventos.sort(key=lambda e: e["instante"])
        assert eventos[0]["tipo"] == "sesion_iniciada"
        assert all(datetime.fromisoformat(e["instante"]).tzinfo is not None for e in eventos)
        instantes = [datetime.fromisoformat(e["instante"]) for e in eventos]
        assert all(antes < despues for antes, despues in zip(instantes, instantes[1:], strict=False))
        for evento in eventos:
            EventoUso.model_validate({k: v for k, v in evento.items() if k != "instante"})
        tipos = [e["tipo"] for e in eventos]
        if "busqueda_resultado" in tipos:
            assert "busqueda_iniciada" in tipos
            assert tipos.index("busqueda_iniciada") < tipos.index("busqueda_resultado")
        if "itinerario_abierto" in tipos:
            assert "busqueda_resultado" in tipos
            assert tipos.index("busqueda_resultado") < tipos.index("itinerario_abierto")
        for accion in ("viaje_guardado", "viaje_compartido", "viaje_impreso"):
            if accion in tipos:
                assert "itinerario_abierto" in tipos
                assert tipos.index("itinerario_abierto") < tipos.index(accion)
        if "error_consulta" in tipos:
            assert "busqueda_iniciada" in tipos
            assert "busqueda_resultado" not in tipos
        respuestas = [e for e in eventos if e["tipo"] == "busqueda_resultado"]
        if respuestas and respuestas[0]["resultados"] == 0:
            assert "itinerario_abierto" not in tipos
            assert "viaje_guardado" not in tipos


def test_historial_completo_en_hora_de_peru():
    salida = generar()
    fin = date(2026, 11, 10)
    esperadas = {fin - timedelta(days=i) for i in range(28)}
    fechas = {datetime.fromisoformat(e["instante"]).astimezone(HORA_PERU).date() for e in salida["eventos"]}
    assert fechas == esperadas
    assert salida["meta"]["fecha_inicio"] == "2026-10-14"
    assert salida["meta"]["fecha_base"] == "2026-11-10"
    assert salida["meta"]["dias_historia"] == 28
    assert all(datetime.fromisoformat(e["instante"]).utcoffset() == timedelta(hours=-5) for e in salida["eventos"])


def test_usuarios_resumen_corresponden_a_sus_acciones():
    salida = generar()
    por_sesion = defaultdict(list)
    for evento in salida["eventos"]:
        por_sesion[evento["sesion"]].append(evento)
    assert sum(u["acciones"] for u in salida["usuarios"]) == len(salida["eventos"])
    for usuario in salida["usuarios"]:
        eventos = por_sesion[usuario["sesion"]]
        tipos = {e["tipo"] for e in eventos}
        assert usuario["acciones"] == len(eventos)
        assert usuario["ultima_accion"] == eventos[-1]["tipo"]
        assert usuario["guardo"] == ("viaje_guardado" in tipos)
        assert usuario["compartio"] == ("viaje_compartido" in tipos)
        assert usuario["imprimio"] == ("viaje_impreso" in tipos)
        assert usuario["consulta_kit"] in range(1, 41)
        respuestas = [e for e in eventos if e["tipo"] == "busqueda_resultado"]
        if respuestas:
            assert usuario["duracion_ms"] == respuestas[0]["duracion_ms"]
            assert usuario["resultados"] == respuestas[0]["resultados"]
        else:
            assert usuario["duracion_ms"] is None
            assert usuario["resultados"] is None


def test_simulacion_incluye_escenarios_sin_resultados_y_errores():
    salida = generar()
    assert any(e["tipo"] == "error_consulta" for e in salida["eventos"])
    assert any(e["tipo"] == "busqueda_resultado" and e["resultados"] == 0 for e in salida["eventos"])
    assert any(u["guardo"] for u in salida["usuarios"])


def test_exportacion_conserva_eventos_y_una_fila_por_usuario(tmp_path):
    salida = generar()
    ruta = tmp_path / "actividad_200.json"
    empaquetada = tmp_path / "paquete" / "simulacion.json"
    eventos_csv, usuarios_csv = guardar(salida, ruta, empaquetada)
    assert ruta.read_bytes() == empaquetada.read_bytes()
    with eventos_csv.open(encoding="utf-8-sig", newline="") as archivo:
        eventos = list(csv.DictReader(archivo, delimiter=";"))
    with usuarios_csv.open(encoding="utf-8-sig", newline="") as archivo:
        usuarios = list(csv.DictReader(archivo, delimiter=";"))
    assert len(eventos) == len(salida["eventos"])
    assert len(usuarios) == 200
    assert {u["sesion"] for u in usuarios} == {e["sesion"] for e in eventos}


def test_parametros_reproducibles_y_compatibilidad():
    assert generar(42, 9, date(2026, 10, 1), 7) == generar(42, 9, date(2026, 10, 1), 7)
    assert generar(42, 10, date(2026, 10, 1), 7) != generar(42, 9, date(2026, 10, 1), 7)
    assert len(generar(300, 42, date(2026, 11, 11))["usuarios"]) == 300


@pytest.mark.parametrize("sesiones,dias", [(0, 28), (10_001, 28), (200, 0), (200, 366)])
def test_parametros_fuera_de_rango(sesiones, dias):
    with pytest.raises(ValueError):
        generar(sesiones=sesiones, dias_historia=dias)
