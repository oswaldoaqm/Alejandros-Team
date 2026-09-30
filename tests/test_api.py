"""La API expone el contrato y responde lo que promete."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dreemgo import __version__
from dreemgo.api.app import app


@pytest.fixture(scope="module")
def cliente():
    return TestClient(app)


def test_salud(cliente):
    r = cliente.get("/v1/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "version": __version__, "version_contrato": "1.0", "version_datos": None}


def test_el_esquema_publica_el_contrato(cliente):
    esquemas = cliente.get("/v1/openapi.json").json()["components"]["schemas"]
    for modelo in ("Respuesta", "Ruta", "Dia", "Parada", "Recurso", "Costo", "Evento"):
        assert modelo in esquemas


def test_consulta_sin_mes(cliente):
    r = cliente.get("/v1/viajes", params={"origen": "lima", "dias": 6})
    assert r.status_code == 422
    assert r.json()["detail"] == [
        {"campo": "consulta", "mensaje": "Indica el mes de viaje o la fecha de inicio.", "tipo": "value_error"}
    ]


@pytest.mark.parametrize(
    "params, campo, mensaje",
    [
        ({"mes": 7, "dias": 15}, "dias", "Debe ser menor o igual que 14."),
        ({"mes": 0}, "mes", "Debe ser mayor o igual que 1."),
        ({"mes": "julio"}, "mes", "Debe ser un número entero."),
        ({"mes": 7, "fecha_inicio": "20/07/2026"}, "fecha_inicio", "Fecha no válida: se espera AAAA-MM-DD."),
        ({"mes": 7, "intereses": "museos"}, "intereses", "Valor no válido. Opciones:"),
        ({"mes": 7, "origen": "Lima"}, "origen", "Formato no válido."),
    ],
)
def test_errores_en_espanol_con_su_campo(cliente, params, campo, mensaje):
    r = cliente.get("/v1/viajes", params=params)
    assert r.status_code == 422
    errores = r.json()["detail"]
    assert any(e["campo"] == campo and e["mensaje"].startswith(mensaje) for e in errores), errores


def test_parametro_desconocido(cliente):
    assert cliente.get("/v1/viajes", params={"mes": 7, "moneda": "USD"}).status_code == 422


def test_intereses_repetidos_en_la_url(cliente):
    r = cliente.get("/v1/viajes", params=[("mes", 7), ("intereses", "playa"), ("intereses", "historia")])
    assert r.status_code == 503  # consulta válida; el motor aún no está conectado


def test_cors_para_la_app(cliente):
    r = cliente.options(
        "/v1/viajes", headers={"Origin": "https://oswaldoaqm.github.io", "Access-Control-Request-Method": "GET"}
    )
    assert r.headers.get("access-control-allow-origin") == "https://oswaldoaqm.github.io"


def test_cors_rechaza_otros_origenes(cliente):
    r = cliente.options("/v1/viajes", headers={"Origin": "https://ejemplo.com", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers
