"""El buzón guarda mensajes aparte y solo los muestra al equipo autorizado."""

from __future__ import annotations

import sqlite3
from uuid import uuid4

from fastapi.testclient import TestClient

from dreemgo.api.app import app


def test_recibe_mensaje_y_protege_la_lectura(monkeypatch, tmp_path):
    base = tmp_path / "comentarios.sqlite3"
    monkeypatch.setenv("DREEMGO_COMENTARIOS_DB", str(base))
    monkeypatch.delenv("DREEMGO_CLAVE_COMENTARIOS", raising=False)
    cliente = TestClient(app)

    assert cliente.get("/v1/comentarios").status_code == 403
    assert not base.exists()

    sesion = str(uuid4())
    respuesta = cliente.post(
        "/v1/comentarios",
        json={"sesion": sesion, "categoria": "duda", "mensaje": "  ¿Cómo se calcula el costo?  "},
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "recibido"

    monkeypatch.setenv("DREEMGO_CLAVE_COMENTARIOS", "solo-equipo-prueba")
    assert cliente.get("/v1/comentarios").status_code == 401
    assert cliente.get("/v1/comentarios", headers={"X-Clave-Comentarios": "incorrecta"}).status_code == 401
    listado = cliente.get("/v1/comentarios", headers={"X-Clave-Comentarios": "solo-equipo-prueba"})
    assert listado.status_code == 200
    assert listado.headers["cache-control"] == "no-store"
    assert listado.json()["total"] == 1
    assert listado.json()["comentarios"][0]["mensaje"] == "¿Cómo se calcula el costo?"
    assert "sesion" not in listado.json()["comentarios"][0]
    with sqlite3.connect(base) as conexion:
        columnas = {fila[1] for fila in conexion.execute("PRAGMA table_info(comentarios)")}
    assert columnas == {"id", "instante", "sesion", "categoria", "mensaje"}


def test_rechaza_mensajes_invalidos_y_limita_envios(monkeypatch, tmp_path):
    base = tmp_path / "comentarios.sqlite3"
    monkeypatch.setenv("DREEMGO_COMENTARIOS_DB", str(base))
    cliente = TestClient(app)
    sesion = str(uuid4())
    comun = {"sesion": sesion, "categoria": "sugerencia", "mensaje": "Me gustaría ver más destinos."}

    for cambio in (
        {"mensaje": "         "},
        {"mensaje": "a" * 1001},
        {"categoria": "venta"},
        {"correo": "viajero@ejemplo.pe"},
    ):
        assert cliente.post("/v1/comentarios", json={**comun, **cambio}).status_code == 422
    assert not base.exists()

    for _ in range(3):
        assert cliente.post("/v1/comentarios", json=comun).status_code == 201
    exceso = cliente.post("/v1/comentarios", json=comun)
    assert exceso.status_code == 429
    assert exceso.headers["retry-after"] == "3600"
    assert cliente.post("/v1/comentarios", json={**comun, "sesion": str(uuid4())}).status_code == 201


def test_lectura_limita_filas_y_no_muestra_la_analitica(monkeypatch, tmp_path):
    base = tmp_path / "comentarios.sqlite3"
    monkeypatch.setenv("DREEMGO_COMENTARIOS_DB", str(base))
    monkeypatch.setenv("DREEMGO_CLAVE_COMENTARIOS", "equipo")
    cliente = TestClient(app)
    for categoria in ("duda", "problema"):
        assert (
            cliente.post(
                "/v1/comentarios",
                json={"sesion": str(uuid4()), "categoria": categoria, "mensaje": "Este es un mensaje de prueba."},
            ).status_code
            == 201
        )

    respuesta = cliente.get("/v1/comentarios?limite=1", headers={"X-Clave-Comentarios": "equipo"})
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 2
    assert len(respuesta.json()["comentarios"]) == 1
    assert cliente.get("/v1/comentarios?limite=101", headers={"X-Clave-Comentarios": "equipo"}).status_code == 422
