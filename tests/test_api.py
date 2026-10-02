"""La API expone el contrato y responde lo que promete."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dreemgo import __version__
from dreemgo.api.app import app
from dreemgo.contrato import VERSION_CONTRATO, PoloDetalle, Respuesta
from dreemgo.motor import datos as artefactos

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
ESQUEMA_DE_LA_APP = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"


@pytest.fixture(scope="module")
def cliente():
    return TestClient(app)


def test_salud(cliente):
    r = cliente.get("/v1/salud")
    assert r.status_code == 200
    version_datos = artefactos.cargar().version if artefactos.hay_datos() else None
    assert r.json() == {
        "estado": "ok",
        "version": __version__,
        "version_contrato": VERSION_CONTRATO,
        "version_datos": version_datos,
    }


def test_el_esquema_publica_el_contrato(cliente):
    esquemas = cliente.get("/v1/openapi.json").json()["components"]["schemas"]
    for modelo in ("Respuesta", "Ruta", "Dia", "Parada", "Recurso", "Costo", "Evento", "Opciones", "PoloDetalle"):
        assert modelo in esquemas


def _lo_que_usa_la_app(esquema: dict) -> dict:
    """Rutas con sus parámetros, y modelos con sus campos y enumeraciones: lo que no puede
    cambiar sin regenerar los tipos de la app. No compara textos ni el orden, que dependen
    de la versión de FastAPI y de pydantic."""
    rutas = {
        f"{metodo.upper()} {ruta}": sorted(p["name"] for p in operacion.get("parameters", []))
        for ruta, metodos in esquema["paths"].items()
        for metodo, operacion in metodos.items()
    }
    modelos = {}
    for nombre, modelo in esquema["components"]["schemas"].items():
        campos = modelo.get("properties", {})
        enumeraciones = {campo: sorted(c["enum"]) for campo, c in campos.items() if "enum" in c}
        if "enum" in modelo:
            enumeraciones[""] = sorted(modelo["enum"])
        modelos[nombre] = {
            "campos": sorted(campos),
            "obligatorios": sorted(modelo.get("required", [])),
            "enumeraciones": enumeraciones,
        }
    return {"rutas": rutas, "modelos": modelos}


def test_el_esquema_del_que_salen_los_tipos_de_la_app_esta_al_dia(cliente):
    en_docs = json.loads(ESQUEMA_DE_LA_APP.read_text(encoding="utf-8"))
    del_api = cliente.get("/v1/openapi.json").json()
    assert _lo_que_usa_la_app(en_docs) == _lo_que_usa_la_app(del_api), (
        "docs/openapi.json quedó atrás del contrato. "
        "Corre `python docs/generar_openapi.py` y, en app/, `npm run tipos`."
    )


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


def test_las_opciones_de_un_valor_no_valido_se_listan_en_espanol(cliente):
    r = cliente.get("/v1/viajes", params={"mes": 7, "intereses": "museos"})
    [error] = [e for e in r.json()["detail"] if e["campo"] == "intereses"]
    assert error["mensaje"].endswith("'arquitectura' o 'aventura'.")
    assert " or " not in error["mensaje"]


def test_parametro_desconocido(cliente):
    assert cliente.get("/v1/viajes", params={"mes": 7, "moneda": "USD"}).status_code == 422


def test_intereses_repetidos_en_la_url(cliente):
    r = cliente.get("/v1/viajes", params=[("mes", 7), ("intereses", "playa"), ("intereses", "historia")])
    if artefactos.hay_datos():
        assert r.status_code == 200
        assert r.json()["consulta"]["intereses"] == ["playa", "historia"]
    else:
        assert r.status_code == 503


@con_datos
def test_viaje_cumple_el_contrato(cliente):
    r = cliente.get("/v1/viajes", params={"origen": "lima", "mes": 7, "dias": 4, "intereses": "historia"})
    assert r.status_code == 200
    respuesta = Respuesta.model_validate(r.json())
    assert 1 <= len(respuesta.rutas) <= 3
    assert respuesta.version_datos == artefactos.cargar().version


@con_datos
def test_origen_desconocido(cliente):
    r = cliente.get("/v1/viajes", params={"origen": "marte", "mes": 7})
    assert r.status_code == 422
    assert r.json()["detail"][0]["campo"] == "origen"


@con_datos
def test_opciones(cliente):
    r = cliente.get("/v1/opciones").json()
    assert len(r["origenes"]) == 24 and r["origenes"][0]["id"] == "lima"
    assert [i["id"] for i in r["intereses"]][:2] == ["naturaleza", "historia"]
    assert r["dias"] == {"minimo": 1, "maximo": 14, "defecto": 6}


@con_datos
def test_ficha_de_un_polo(cliente):
    r = cliente.get("/v1/polos/70")
    assert r.status_code == 200
    detalle = PoloDetalle.model_validate(r.json())
    assert [c.mes for c in detalle.clima] == list(range(1, 13))
    jerarquias = [x.jerarquia or 0 for x in detalle.recursos]
    assert jerarquias == sorted(jerarquias, reverse=True)
    assert cliente.get("/v1/polos/99999").status_code == 404


@con_datos
def test_eventos_entre_dos_fechas(cliente):
    r = cliente.get("/v1/eventos", params={"desde": "2027-07-01", "hasta": "2027-07-31"})
    assert r.status_code == 200
    eventos = r.json()["eventos"]
    assert eventos and all(e["fecha_inicio"] <= "2027-07-31" and e["fecha_fin"] >= "2027-07-01" for e in eventos)
    assert cliente.get("/v1/eventos", params={"desde": "2027-07-31", "hasta": "2027-07-01"}).status_code == 422
    assert cliente.get("/v1/eventos", params={"desde": "2027-01-01", "hasta": "2028-06-01"}).status_code == 422


def test_cors_para_la_app(cliente):
    r = cliente.options(
        "/v1/viajes", headers={"Origin": "https://oswaldoaqm.github.io", "Access-Control-Request-Method": "GET"}
    )
    assert r.headers.get("access-control-allow-origin") == "https://oswaldoaqm.github.io"


def test_cors_rechaza_otros_origenes(cliente):
    r = cliente.options("/v1/viajes", headers={"Origin": "https://ejemplo.com", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers
