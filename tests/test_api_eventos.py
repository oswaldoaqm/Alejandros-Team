"""Los eventos publicados en el API: dónde aparecen y cómo cambian la versión de datos."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from dreemgo.almacen import EnMemoria
from dreemgo.api.app import app
from dreemgo.api.publicaciones import HORA_DEL_PERU, Publicaciones, ahora, publicaciones
from dreemgo.contrato import EventoNuevo, Respuesta
from dreemgo.motor import datos as artefactos
from dreemgo.publicados import Publicado

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

AHORA = datetime(2026, 10, 2, 10, 0, tzinfo=HORA_DEL_PERU)
VIAJE = {"origen": "lima", "fecha_inicio": "2026-11-10", "dias": 5}
NOVIEMBRE = {"desde": "2026-11-01", "hasta": "2026-11-30"}
# En la plaza de Huaraz, donde duermen cuatro polos.
FESTIVAL = {
    "nombre": "Festival del Café",
    "tipo": "Feria gastronómica",
    "fecha_inicio": "2026-11-11",
    "fecha_fin": "2026-11-12",
    "distrito": "Huaraz",
    "provincia": "Huaraz",
    "region": "Áncash",
    "lat": -9.5279,
    "lon": -77.5286,
    "url": "https://www.munihuaraz.gob.pe/festival",
    "publicado_por": "Municipalidad Provincial de Huaraz",
}


class AlmacenQueFalla(EnMemoria):
    def __init__(self, al_leer: bool = False, al_guardar: bool = False) -> None:
        super().__init__()
        self.al_leer, self.al_guardar = al_leer, al_guardar

    def leer(self) -> list[dict]:
        if self.al_leer:
            raise OSError("la tabla no responde")
        return super().leer()

    def guardar(self, registro: dict) -> None:
        if self.al_guardar:
            raise OSError("la tabla no responde")
        super().guardar(registro)


def cliente_con(almacen: EnMemoria) -> TestClient:
    """Un cliente del API con su propio almacén y con el reloj en el 2 de octubre de 2026."""
    publicadas = Publicaciones(almacen)
    app.dependency_overrides[publicaciones] = lambda: publicadas
    app.dependency_overrides[ahora] = lambda: AHORA
    return TestClient(app)


@pytest.fixture
def almacen() -> EnMemoria:
    return EnMemoria()


@pytest.fixture
def cliente(almacen):
    yield cliente_con(almacen)
    app.dependency_overrides.clear()


def sembrar(almacen: EnMemoria, **cambios) -> str:
    """Deja en el almacén un evento ya publicado, como si lo hubiera guardado otro servidor. Devuelve su id."""
    publicado = Publicado.nuevo(EventoNuevo(**{**FESTIVAL, **cambios}), AHORA)
    almacen.guardar(publicado.registro())
    return publicado.id


def publicados_en(cliente: TestClient, ruta: str, **parametros) -> list[dict]:
    respuesta = cliente.get(ruta, params=parametros)
    assert respuesta.status_code == 200, respuesta.text
    return [e for e in respuesta.json()["eventos"] if e["fuente"] == "publicado"]


def versiones(cliente: TestClient) -> set[str]:
    """La versión de datos que dice cada parte del API."""
    polo = next(iter(artefactos.cargar().polos))
    return {
        cliente.get("/v1/salud").json()["version_datos"],
        cliente.get("/v1/opciones").json()["version_datos"],
        cliente.get("/v1/eventos", params=NOVIEMBRE).json()["version_datos"],
        cliente.get(f"/v1/polos/{polo}").json()["version_datos"],
        cliente.get("/v1/viajes", params=VIAJE).json()["version_datos"],
    }


# ─────────────────────────────── dónde aparece lo publicado ───────────────────────────────


@con_datos
class TestDondeAparece:
    def test_en_el_calendario(self, cliente, almacen):
        antes = cliente_con(EnMemoria()).get("/v1/eventos", params=NOVIEMBRE).json()
        cliente = cliente_con(almacen)
        id_ = sembrar(almacen)
        despues = cliente.get("/v1/eventos", params=NOVIEMBRE).json()
        [publicado] = [e for e in despues["eventos"] if e["fuente"] == "publicado"]
        assert publicado == {
            "id": id_,
            "nombre": "Festival del Café",
            "tipo": "Feria gastronómica",
            "fecha_inicio": "2026-11-11",
            "fecha_fin": "2026-11-12",
            "precision_fecha": "exacta",
            "distrito": "Huaraz",
            "provincia": "Huaraz",
            "region": "Áncash",
            "fuente": "publicado",
            "publicado_por": "Municipalidad Provincial de Huaraz",
            "url": "https://www.munihuaraz.gob.pe/festival",
        }
        assert [e for e in despues["eventos"] if e["fuente"] == "mincetur"] == antes["eventos"]
        fechas = [(e["fecha_inicio"], e["id"]) for e in despues["eventos"]]
        assert fechas == sorted(fechas)
        assert publicados_en(cliente, "/v1/eventos", desde="2026-12-01", hasta="2026-12-31") == []

    def test_en_los_polos_que_duermen_cerca_y_solo_en_esos(self, cliente, almacen):
        datos = artefactos.cargar()
        duermen_en_huaraz = sorted(p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz")
        lejos = next(p.id for p in datos.polos.values() if p.base["nombre"] == "Iquitos")
        id_ = sembrar(almacen)
        assert len(duermen_en_huaraz) > 1
        for polo in duermen_en_huaraz:
            assert [e["id"] for e in publicados_en(cliente, "/v1/eventos", **NOVIEMBRE, polo=polo)] == [id_]
            assert [e["id"] for e in publicados_en(cliente, f"/v1/polos/{polo}")] == [id_]
        assert publicados_en(cliente, "/v1/eventos", **NOVIEMBRE, polo=lejos) == []
        assert publicados_en(cliente, f"/v1/polos/{lejos}") == []

    def test_sin_coordenadas_sale_en_el_calendario_pero_en_ningun_polo(self, cliente, almacen):
        datos = artefactos.cargar()
        id_ = sembrar(almacen, lat=None, lon=None)
        assert [e["id"] for e in publicados_en(cliente, "/v1/eventos", **NOVIEMBRE)] == [id_]
        for polo in (p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz"):
            assert publicados_en(cliente, "/v1/eventos", **NOVIEMBRE, polo=polo) == []
            assert publicados_en(cliente, f"/v1/polos/{polo}") == []

    def test_en_la_ruta_que_pasa_por_ahi_sin_mover_ninguna(self, almacen):
        try:
            antes = cliente_con(EnMemoria()).get("/v1/viajes", params=VIAJE).json()
            assert antes["rutas"], "la consulta de la prueba tiene que dar rutas"
            base = antes["rutas"][0]["polo"]["base"]
            id_ = sembrar(almacen, lat=base["lat"], lon=base["lon"], distrito=base["nombre"], provincia=base["nombre"])

            cliente = cliente_con(almacen)
            despues = cliente.get("/v1/viajes", params=VIAJE).json()
            Respuesta.model_validate(despues)
            primera = despues["rutas"][0]
            assert [e["id"] for e in primera["eventos"] if e["fuente"] == "publicado"] == [id_]
            fechas = [(e["fecha_inicio"], e["id"]) for e in primera["eventos"]]
            assert fechas == sorted(fechas)

            # Lo publicado no mueve ninguna ruta: los mismos polos, puntajes, motivos, días y costos.
            def sin_lo_publicado(respuesta: dict) -> dict:
                rutas = [
                    {**ruta, "eventos": [e for e in ruta["eventos"] if e["fuente"] != "publicado"]}
                    for ruta in respuesta["rutas"]
                ]
                return {**respuesta, "rutas": rutas, "version_datos": None}

            assert sin_lo_publicado(despues) == sin_lo_publicado(antes)
            assert all("Festival del Café" not in motivo for motivo in primera["motivos"])

            # Fuera de las fechas del viaje no aparece.
            en_diciembre = cliente.get("/v1/viajes", params={**VIAJE, "fecha_inicio": "2026-12-10"}).json()
            assert all(e["fuente"] != "publicado" for ruta in en_diciembre["rutas"] for e in ruta["eventos"])
        finally:
            app.dependency_overrides.clear()


# ─────────────────────────────── la versión de datos ───────────────────────────────


@con_datos
class TestVersionDeDatos:
    def test_sin_nada_publicado_es_la_de_los_artefactos(self, cliente):
        assert versiones(cliente) == {artefactos.cargar().version}

    def test_con_algo_publicado_lleva_su_huella_y_todo_el_api_dice_la_misma(self, cliente, almacen):
        base = artefactos.cargar().version
        sembrar(almacen)
        [con_uno] = versiones(cliente)
        assert con_uno.startswith(f"{base}-e") and len(con_uno) == len(base) + 9

    def test_otro_calendario_otra_version_y_el_mismo_la_misma(self):
        try:
            uno, dos, otra_vez = EnMemoria(), EnMemoria(), EnMemoria()
            sembrar(uno)
            sembrar(dos)
            sembrar(dos, nombre="Feria del Queso")
            sembrar(otra_vez, nombre="Feria del Queso")
            sembrar(otra_vez)  # los mismos dos, guardados en otro orden
            [con_uno] = versiones(cliente_con(uno))
            [con_dos] = versiones(cliente_con(dos))
            assert con_uno != con_dos
            assert versiones(cliente_con(otra_vez)) == {con_dos}
        finally:
            app.dependency_overrides.clear()

    def test_la_misma_version_da_la_misma_respuesta(self, cliente, almacen):
        sembrar(almacen)
        una = cliente.get("/v1/viajes", params=VIAJE).text
        assert cliente.get("/v1/viajes", params=VIAJE).text == una


@con_datos
def test_si_el_almacen_no_responde_las_rutas_siguen():
    try:
        cliente = cliente_con(AlmacenQueFalla(al_leer=True))
        base = artefactos.cargar().version
        assert cliente.get("/v1/salud").json()["version_datos"] == base
        r = cliente.get("/v1/viajes", params=VIAJE)
        assert r.status_code == 200 and r.json()["rutas"] and r.json()["version_datos"] == base
        assert cliente.get("/v1/eventos", params=NOVIEMBRE).status_code == 200
    finally:
        app.dependency_overrides.clear()
