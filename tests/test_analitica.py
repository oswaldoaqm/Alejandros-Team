"""La simulación y la actividad real nunca se mezclan."""

from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from dreemgo import analitica
from dreemgo.analitica import EventoUso, leer_reales, registrar, resumir
from dreemgo.api.app import app


def _indicadores(respuesta: dict) -> dict:
    return {indicador["id"]: indicador["valor"] for indicador in respuesta["indicadores"]}


def test_simulacion_tiene_200_sesiones_y_no_escribe_la_base(monkeypatch, tmp_path):
    base = tmp_path / "actividad.sqlite3"
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(base))
    cliente = TestClient(app)

    respuesta = cliente.get("/v1/analitica/resumen")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "simulacion"
    assert "SIMULACIÓN" in cuerpo["fuente"]
    assert _indicadores(cuerpo)["sesiones"] == 200
    assert len(cuerpo["indicadores"]) >= 20
    assert not base.exists()


def test_resumen_real_necesita_clave_y_lee_solo_lo_registrado(monkeypatch, tmp_path):
    base = tmp_path / "actividad.sqlite3"
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(base))
    monkeypatch.delenv("DREEMGO_CLAVE_ANALITICA", raising=False)
    cliente = TestClient(app)

    assert cliente.get("/v1/analitica/resumen?modo=real").status_code == 403
    monkeypatch.setenv("DREEMGO_CLAVE_ANALITICA", "clave-de-prueba")
    assert cliente.get("/v1/analitica/resumen?modo=real").status_code == 401
    cabecera = {"X-Clave-Analitica": "clave-de-prueba"}
    vacio = cliente.get("/v1/analitica/resumen?modo=real", headers=cabecera)
    assert vacio.status_code == 200
    assert _indicadores(vacio.json())["sesiones"] == 0

    sesion = str(uuid4())
    evento = cliente.post("/v1/analitica/eventos", json={"sesion": sesion, "tipo": "sesion_iniciada"})
    assert evento.status_code == 202
    real = cliente.get("/v1/analitica/resumen?modo=real", headers=cabecera)
    assert real.status_code == 200
    assert _indicadores(real.json())["sesiones"] == 1
    assert _indicadores(real.json())["busquedas_iniciadas"] == 0
    assert _indicadores(cliente.get("/v1/analitica/resumen").json())["sesiones"] == 200

    with sqlite3.connect(base) as conexion:
        guardado = json.loads(conexion.execute("SELECT datos FROM actividad").fetchone()[0])
    assert guardado["sesion"] == sesion
    assert guardado["tipo"] == "sesion_iniciada"
    assert guardado["instante"].endswith("Z")


def test_post_rechaza_datos_personales_y_fecha_del_cliente(monkeypatch, tmp_path):
    base = tmp_path / "actividad.sqlite3"
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(base))
    cliente = TestClient(app)
    base_evento = {"sesion": str(uuid4()), "tipo": "busqueda_iniciada"}

    for campo, valor in (("correo", "viajero@ejemplo.pe"), ("instante", "2026-01-01T00:00:00Z")):
        respuesta = cliente.post("/v1/analitica/eventos", json={**base_evento, campo: valor})
        assert respuesta.status_code == 422
    assert not base.exists()


def test_indicadores_calculan_tasas_sin_confundir_eventos_con_sesiones():
    a, b = str(uuid4()), str(uuid4())
    instante = "2026-11-11T10:00:00Z"
    eventos = [
        {"sesion": a, "tipo": "formulario_abierto", "instante": instante},
        {"sesion": a, "tipo": "busqueda_iniciada", "instante": instante, "dias": 4, "presupuesto": 700},
        {"sesion": a, "tipo": "busqueda_resultado", "instante": instante, "resultados": 3, "duracion_ms": 350},
        {"sesion": a, "tipo": "itinerario_abierto", "instante": instante, "polo": 1},
        {"sesion": a, "tipo": "viaje_guardado", "instante": instante, "polo": 1},
        {"sesion": b, "tipo": "formulario_abierto", "instante": instante},
    ]

    indicadores = {i.id: i.valor for i in resumir(eventos, modo="simulacion").indicadores}

    assert indicadores["sesiones"] == 2
    assert indicadores["tasa_abandono_formulario"] == 50
    assert indicadores["tasa_resultados"] == 100
    assert indicadores["tasa_guardado"] == 100
    assert indicadores["latencia_mediana_ms"] == 350
    assert indicadores["presupuesto_mediano_soles"] == 700


def test_reintentar_el_mismo_evento_no_duplica_la_actividad(monkeypatch, tmp_path):
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(tmp_path / "actividad.sqlite3"))
    cliente = TestClient(app)
    evento = {"id_evento": str(uuid4()), "sesion": str(uuid4()), "tipo": "busqueda_iniciada"}

    assert cliente.post("/v1/analitica/eventos", json=evento).json()["estado"] == "registrado"
    repetido = cliente.post("/v1/analitica/eventos", json=evento)
    assert repetido.status_code == 202
    assert repetido.json()["estado"] == "ya_registrado"
    assert len(leer_reales()) == 1


def test_migracion_conserva_la_base_anterior(monkeypatch, tmp_path):
    base = tmp_path / "actividad.sqlite3"
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(base))
    anterior = {"sesion": str(uuid4()), "tipo": "sesion_iniciada", "instante": "2026-11-11T12:00:00Z"}
    with sqlite3.connect(base) as conexion:
        conexion.execute(
            "CREATE TABLE actividad (id INTEGER PRIMARY KEY, instante TEXT, sesion TEXT, tipo TEXT, datos TEXT)"
        )
        conexion.execute(
            "INSERT INTO actividad(instante, sesion, tipo, datos) VALUES (?, ?, ?, ?)",
            (anterior["instante"], anterior["sesion"], anterior["tipo"], json.dumps(anterior)),
        )
    assert leer_reales() == [anterior]
    registrar(EventoUso(sesion=uuid4(), tipo="sesion_iniciada", id_evento=uuid4()))
    assert len(leer_reales()) == 2


def test_escrituras_simultaneas_y_reintentos_no_pierden_ni_duplican_eventos(monkeypatch, tmp_path):
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(tmp_path / "actividad.sqlite3"))
    eventos = [EventoUso(sesion=uuid4(), tipo="sesion_iniciada", id_evento=uuid4()) for _ in range(16)]
    with ThreadPoolExecutor(max_workers=8) as grupo:
        resultados = list(grupo.map(registrar, eventos + eventos))
    assert sum(resultados) == 16
    assert len(leer_reales()) == 16


def test_limite_por_sesion_rechaza_rafagas_pero_permite_reintentar(monkeypatch, tmp_path):
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(tmp_path / "actividad.sqlite3"))
    monkeypatch.setattr(analitica, "MAX_EVENTOS_POR_MINUTO", 2)
    cliente = TestClient(app)
    evento = {"id_evento": str(uuid4()), "sesion": str(uuid4()), "tipo": "formulario_abierto"}
    assert cliente.post("/v1/analitica/eventos", json=evento).status_code == 202
    assert cliente.post("/v1/analitica/eventos", json={**evento, "id_evento": str(uuid4())}).status_code == 202
    assert cliente.post("/v1/analitica/eventos", json=evento).json()["estado"] == "ya_registrado"
    limite = cliente.post("/v1/analitica/eventos", json={**evento, "id_evento": str(uuid4())})
    assert limite.status_code == 429
    assert limite.headers["Retry-After"] == "60"
    assert len(leer_reales()) == 2


def test_fechas_y_serie_respetan_el_dia_de_peru(monkeypatch, tmp_path):
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(tmp_path / "actividad.sqlite3"))
    for hora, microsegundos in ((4, 999999), (5, 0), (5, 1)):
        registrar(
            EventoUso(sesion=uuid4(), tipo="sesion_iniciada"),
            datetime(2026, 11, 11, hora, 0, 0, microsegundos, tzinfo=UTC),
        )
    todos = leer_reales()
    dia = date(2026, 11, 11)
    assert len(leer_reales(dia, dia)) == 2
    resumen = resumir(todos, "real", desde=dia, hasta=dia)
    assert resumen.total_eventos == 2
    assert [(p.fecha, p.sesiones) for p in resumen.serie] == [(dia, 2)]
    assert resumen.zona_horaria == "America/Lima"
    assert resumir(todos, "real").periodo["desde"] == date(2026, 11, 10)


def test_resumen_sin_cache_y_actividad_reciente_no_expone_identificadores(monkeypatch, tmp_path):
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(tmp_path / "actividad.sqlite3"))
    monkeypatch.setenv("DREEMGO_CLAVE_ANALITICA", "clave-de-prueba")
    cliente = TestClient(app)
    sesion = str(uuid4())
    cliente.post("/v1/analitica/eventos", json={"sesion": sesion, "tipo": "formulario_abierto"})
    respuesta = cliente.get("/v1/analitica/resumen?modo=real", headers={"X-Clave-Analitica": "clave-de-prueba"})
    assert respuesta.headers["Cache-Control"] == "no-store"
    cuerpo = respuesta.json()
    assert cuerpo["consultado"] >= cuerpo["actualizado"]
    assert cuerpo["actividad_reciente"][0]["etiqueta"] == "Se abrió el planificador"
    assert sesion not in respuesta.text
    assert set(cuerpo["actividad_reciente"][0]) == {"instante", "tipo", "etiqueta"}


def test_eventos_incompletos_y_preferencias_repetidas_no_sesgan_las_cifras():
    cliente = TestClient(app)
    incompleto = cliente.post("/v1/analitica/eventos", json={"sesion": str(uuid4()), "tipo": "busqueda_resultado"})
    assert incompleto.status_code == 422
    evento = EventoUso(sesion=uuid4(), tipo="busqueda_iniciada", intereses=["naturaleza", "naturaleza"])
    assert len(evento.intereses) == 1
    sin_datos = {i.id: i.valor for i in resumir([], "real").indicadores}
    assert sin_datos["tasa_resultados"] is None
    assert sin_datos["tasa_sesiones_con_error"] is None


def test_ayuda_y_comentario_actualizan_el_panel_sin_guardar_el_texto(monkeypatch, tmp_path):
    base = tmp_path / "actividad.sqlite3"
    monkeypatch.setenv("DREEMGO_ANALITICA_DB", str(base))
    monkeypatch.setenv("DREEMGO_CLAVE_ANALITICA", "clave-de-prueba")
    cliente = TestClient(app)
    sesion = str(uuid4())
    for tipo in ("ayuda_consultada", "ayuda_consultada", "comentario_enviado"):
        respuesta = cliente.post("/v1/analitica/eventos", json={"sesion": sesion, "tipo": tipo})
        assert respuesta.status_code == 202

    # El contrato rechaza texto libre en la analítica, incluso para el chat.
    rechazado = cliente.post(
        "/v1/analitica/eventos",
        json={"sesion": sesion, "tipo": "ayuda_consultada", "pregunta": "¿Puedo llevar mascotas?"},
    )
    assert rechazado.status_code == 422

    real = cliente.get("/v1/analitica/resumen?modo=real", headers={"X-Clave-Analitica": "clave-de-prueba"})
    assert real.status_code == 200
    indicadores = _indicadores(real.json())
    assert indicadores["consultas_ayuda"] == 2
    assert indicadores["comentarios_enviados"] == 1
    assert {item["id"]: item["cantidad"] for item in real.json()["analisis"]["distribucion"]} == {"ayuda": 1}
    assert real.json()["actividad_reciente"][0]["etiqueta"] == "Se envió un comentario al equipo"
    assert "mascotas" not in json.dumps(real.json(), ensure_ascii=False).lower()
    assert "mascotas" not in base.read_bytes().decode("utf-8", errors="ignore").lower()

    demo = _indicadores(cliente.get("/v1/analitica/resumen?modo=simulacion").json())
    assert demo["sesiones"] == 200
    assert demo["consultas_ayuda"] == demo["comentarios_enviados"] == 0
