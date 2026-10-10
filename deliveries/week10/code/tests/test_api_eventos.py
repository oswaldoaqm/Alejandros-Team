"""Los eventos publicados en el API: dónde aparecen, cómo cambian la versión de datos y cómo se publican."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from dreemgo.almacen import EnMemoria
from dreemgo.api import publicaciones as modulo
from dreemgo.api.app import app
from dreemgo.api.publicaciones import HORA_DEL_PERU, Publicaciones, ahora, publicaciones
from dreemgo.contrato import Evento, EventoNuevo, Respuesta
from dreemgo.motor import datos as artefactos
from dreemgo.publicados import Publicado

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

AHORA = datetime(2026, 10, 2, 10, 0, tzinfo=HORA_DEL_PERU)
VIAJE = {"origen": "lima", "fecha_inicio": "2026-11-10", "dias": 5}
NOVIEMBRE = {"desde": "2026-11-01", "hasta": "2026-11-30"}
# En la plaza de Huaraz, la base de un polo.
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
        assert duermen_en_huaraz
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


# ══════════════════════════════════ publicar ══════════════════════════════════

CLAVE = "clave-de-prueba-0123456789"
CON_CLAVE = {"X-Clave-Publicador": CLAVE}


@pytest.fixture
def con_clave(monkeypatch):
    """El servidor acepta publicaciones con ``CLAVE``."""
    monkeypatch.setenv("DREEMGO_CLAVE_PUBLICADOR", CLAVE)


def publicar(cliente: TestClient, **cambios):
    return cliente.post("/v1/eventos", json={**FESTIVAL, **cambios}, headers=CON_CLAVE)


# ─────────────────────────────── quién publica ───────────────────────────────


class TestQuienPublica:
    def test_sin_clave_configurada_el_servidor_no_acepta_publicaciones(self, cliente, almacen):
        for cabeceras in ({}, {"X-Clave-Publicador": ""}, CON_CLAVE):
            r = cliente.post("/v1/eventos", json=FESTIVAL, headers=cabeceras)
            assert r.status_code == 403
            assert r.json() == {"detail": "Este servidor no acepta publicaciones."}
        assert almacen.leer() == []

    @pytest.mark.parametrize("cabeceras", [{}, {"X-Clave-Publicador": ""}, {"X-Clave-Publicador": CLAVE + "x"}])
    def test_sin_la_clave_correcta_no_se_publica(self, con_clave, cliente, almacen, cabeceras):
        r = cliente.post("/v1/eventos", json=FESTIVAL, headers=cabeceras)
        assert r.status_code == 401
        assert r.json() == {"detail": "Falta la clave de publicador o no es la correcta."}
        assert r.headers["www-authenticate"] == "APIKey"
        assert almacen.leer() == []

    def test_la_clave_se_pide_antes_de_mirar_el_evento(self, con_clave, cliente):
        r = cliente.post("/v1/eventos", json={"nombre": "x"})
        assert r.status_code == 401

    def test_leer_el_calendario_no_pide_clave(self, con_clave, cliente):
        assert cliente.get("/v1/eventos", params=NOVIEMBRE).status_code in (200, 503)

    def test_la_app_puede_publicar_desde_el_navegador(self, cliente):
        r = cliente.options(
            "/v1/eventos",
            headers={
                "Origin": "https://oswaldoaqm.github.io",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-clave-publicador",
            },
        )
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == "https://oswaldoaqm.github.io"
        assert "POST" in r.headers["access-control-allow-methods"]
        assert "x-clave-publicador" in r.headers["access-control-allow-headers"].lower()

    def test_el_esquema_dice_que_hace_falta_la_clave(self, cliente):
        esquema = cliente.get("/v1/openapi.json").json()
        assert esquema["components"]["securitySchemes"]["ClavePublicador"] == {
            "type": "apiKey",
            "in": "header",
            "name": "X-Clave-Publicador",
            "description": "La clave que el equipo de DreemGO entrega a los municipios y oficinas de destino "
            "que publican.",
        }
        operacion = esquema["paths"]["/v1/eventos"]["post"]
        assert operacion["security"] == [{"ClavePublicador": []}]
        assert set(operacion["responses"]) == {"201", "401", "403", "422", "503"}
        assert "security" not in esquema["paths"]["/v1/eventos"]["get"]


# ─────────────────────────────── qué se acepta ───────────────────────────────


@con_datos
@pytest.mark.usefixtures("con_clave")
class TestQueSeAcepta:
    def test_publicar_devuelve_el_evento_como_lo_vera_el_viajero(self, cliente, almacen):
        r = publicar(cliente)
        assert r.status_code == 201
        evento = Evento.model_validate(r.json())
        assert evento.id.startswith("p-")
        assert (evento.fuente, evento.precision_fecha) == ("publicado", "exacta")
        assert r.json() == {
            "id": evento.id,
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
        [guardado] = almacen.leer()
        assert guardado["id"] == evento.id
        assert guardado["publicado"] == "2026-10-02T10:00:00-05:00"
        assert (guardado["lat"], guardado["lon"]) == (-9.5279, -77.5286)

    def test_los_textos_se_limpian_y_la_region_se_escribe_como_en_el_inventario(self, cliente):
        r = publicar(cliente, nombre="  Festival   del\tCafé ", region="ancash", tipo=" ", url="", descripcion="")
        assert r.status_code == 201
        assert (r.json()["nombre"], r.json()["region"]) == ("Festival del Café", "Áncash")
        assert r.json()["tipo"] is None and r.json()["url"] is None

    def test_basta_con_lo_obligatorio(self, cliente):
        minimo = {c: FESTIVAL[c] for c in ("nombre", "fecha_inicio", "fecha_fin", "distrito", "provincia", "region")}
        r = cliente.post("/v1/eventos", json={**minimo, "publicado_por": "Dircetur Áncash"}, headers=CON_CLAVE)
        assert r.status_code == 201

    def test_el_que_termina_hoy_todavia_se_publica(self, cliente):
        assert publicar(cliente, fecha_inicio="2026-09-28", fecha_fin="2026-10-02").status_code == 201

    def test_se_publican_los_eventos_de_doce_meses(self, cliente):
        # Hoy es 2 de octubre de 2026: hasta setiembre de 2027, que es lo que muestra el calendario.
        assert publicar(cliente, fecha_inicio="2027-09-30", fecha_fin="2027-10-03").status_code == 201

    @pytest.mark.parametrize(
        "cambios, campo, mensaje",
        [
            ({"region": "Narnia"}, "region", "Región desconocida. Opciones: Amazonas, Áncash, Apurímac"),
            ({"fecha_inicio": "2026-09-30", "fecha_fin": "2026-10-01"}, "fecha_fin", "El evento ya terminó."),
            (
                {"fecha_inicio": "2027-10-01", "fecha_fin": "2027-10-02"},
                "fecha_inicio",
                "Falta demasiado: se publican los eventos que empiezan hasta el 30 de setiembre de 2027.",
            ),
            ({"fecha_fin": "2026-11-10"}, "evento", "La fecha de fin no puede ser anterior a la de inicio."),
            ({"fecha_fin": "2027-02-01"}, "evento", "Un evento no puede durar más de 60 días."),
            ({"lon": None}, "evento", "Latitud y longitud van juntas."),
            ({"lat": 40.4, "lon": -3.7}, "lat", "Debe ser menor o igual que 0.1."),
            ({"nombre": " a "}, "nombre", "Debe tener al menos 3 caracteres."),
            ({"nombre": "x" * 121}, "nombre", "Debe tener como máximo 120 caracteres."),
            ({"nombre": 7}, "nombre", "Debe ser un texto."),
            ({"fecha_inicio": "11/11/2026"}, "fecha_inicio", "Fecha no válida: se espera AAAA-MM-DD."),
            ({"lat": "norte"}, "lat", "Debe ser un número."),
            ({"url": "javascript:alert(1)"}, "url", "La dirección tiene que empezar con http:// o https://."),
            ({"url": "munihuaraz.gob.pe"}, "url", "URL no válida."),
            ({"publicado_por": None}, "publicado_por", "Debe ser un texto."),
            ({"precio": 20}, "precio", "Este campo no existe en el contrato."),
        ],
    )
    def test_lo_que_no_vale_se_dice_en_espanol_con_su_campo(self, cliente, almacen, cambios, campo, mensaje):
        r = publicar(cliente, **cambios)
        assert r.status_code == 422, r.text
        errores = r.json()["detail"]
        assert any(e["campo"] == campo and e["mensaje"].startswith(mensaje) for e in errores), errores
        assert almacen.leer() == []

    def test_si_hay_varias_cosas_mal_las_dice_todas(self, cliente):
        r = publicar(cliente, region="Narnia", fecha_inicio="2026-09-30", fecha_fin="2026-10-01")
        assert r.status_code == 422
        assert [e["campo"] for e in r.json()["detail"]] == ["region", "fecha_fin"]

    def test_sin_un_campo_obligatorio(self, cliente):
        incompleto = {c: v for c, v in FESTIVAL.items() if c != "publicado_por"}
        r = cliente.post("/v1/eventos", json=incompleto, headers=CON_CLAVE)
        assert r.status_code == 422
        assert r.json()["detail"] == [{"campo": "publicado_por", "mensaje": "Falta este campo.", "tipo": "missing"}]

    @pytest.mark.parametrize(
        "cuerpo, mensaje",
        [
            ("{esto no es json", "El cuerpo de la petición no es JSON válido."),
            ("[1, 2]", "Se espera un objeto JSON con los campos del contrato."),
        ],
    )
    def test_un_cuerpo_que_no_es_un_evento(self, cliente, cuerpo, mensaje):
        r = cliente.post("/v1/eventos", content=cuerpo, headers={**CON_CLAVE, "Content-Type": "application/json"})
        assert r.status_code == 422
        assert r.json()["detail"][0]["campo"] == "evento"
        assert r.json()["detail"][0]["mensaje"] == mensaje


# ─────────────────────────────── después de publicar ───────────────────────────────


@con_datos
@pytest.mark.usefixtures("con_clave")
class TestDespuesDePublicar:
    def test_se_ve_enseguida_en_el_calendario_y_en_sus_polos(self, cliente):
        datos = artefactos.cargar()
        en_huaraz = next(p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz")
        assert publicados_en(cliente, "/v1/eventos", **NOVIEMBRE) == []  # el API ya leyó el almacén
        id_ = publicar(cliente).json()["id"]
        assert [e["id"] for e in publicados_en(cliente, "/v1/eventos", **NOVIEMBRE)] == [id_]
        assert [e["id"] for e in publicados_en(cliente, f"/v1/polos/{en_huaraz}")] == [id_]

    def test_publicar_cambia_la_version_de_datos_de_todo_el_api(self, cliente):
        base = artefactos.cargar().version
        assert versiones(cliente) == {base}
        publicar(cliente)
        [con_uno] = versiones(cliente)
        assert con_uno.startswith(f"{base}-e")
        publicar(cliente, nombre="Feria del Queso")
        [con_dos] = versiones(cliente)
        assert con_dos.startswith(f"{base}-e") and con_dos != con_uno

    def test_publicar_lo_mismo_no_cambia_nada(self, cliente, almacen):
        primero = publicar(cliente)
        antes = versiones(cliente)
        segundo = publicar(cliente)
        assert segundo.status_code == 201 and segundo.json() == primero.json()
        assert versiones(cliente) == antes
        assert len(almacen.leer()) == 1

    def test_publicar_el_mismo_con_otros_datos_lo_corrige(self, cliente):
        datos = artefactos.cargar()
        en_huaraz = next(p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz")
        primero = publicar(cliente, lat=None, lon=None, url=None)
        assert publicados_en(cliente, "/v1/eventos", **NOVIEMBRE, polo=en_huaraz) == []
        corregido = publicar(cliente, nombre="FESTIVAL DEL CAFE", publicado_por="municipalidad provincial de huaraz")
        assert primero.json()["id"] == corregido.json()["id"]
        [en_calendario] = publicados_en(cliente, "/v1/eventos", **NOVIEMBRE)
        assert en_calendario["nombre"] == "FESTIVAL DEL CAFE"
        assert en_calendario["url"] == "https://www.munihuaraz.gob.pe/festival"
        assert len(publicados_en(cliente, "/v1/eventos", **NOVIEMBRE, polo=en_huaraz)) == 1


# ─────────────────────────────── cuando no se puede guardar ───────────────────────────────


@con_datos
@pytest.mark.usefixtures("con_clave")
class TestCuandoNoSePuedeGuardar:
    def test_si_el_almacen_falla_se_dice_y_no_queda_a_medias(self):
        try:
            cliente = cliente_con(AlmacenQueFalla(al_guardar=True))
            r = publicar(cliente)
            assert r.status_code == 503
            assert r.json() == {"detail": "No pudimos guardar el evento. Vuelve a intentarlo en un momento."}
            assert publicados_en(cliente, "/v1/eventos", **NOVIEMBRE) == []
        finally:
            app.dependency_overrides.clear()

    def test_el_calendario_lleno_no_acepta_uno_nuevo_pero_si_una_correccion(self, cliente, monkeypatch):
        monkeypatch.setattr(modulo, "PUBLICADOS_MAX", 1)
        assert publicar(cliente).status_code == 201
        r = publicar(cliente, nombre="Feria del Queso")
        assert r.status_code == 503
        assert r.json()["detail"].startswith("El calendario de eventos publicados está lleno.")
        assert publicar(cliente, tipo="Feria").status_code == 201
        assert len(publicados_en(cliente, "/v1/eventos", **NOVIEMBRE)) == 1
