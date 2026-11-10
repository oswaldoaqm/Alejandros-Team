"""Los tres almacenes de eventos publicados guardan y devuelven lo mismo, y avisan igual de
que alguien guardó."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from dreemgo.almacen import EnArchivo, EnDynamo, EnMemoria, del_entorno


def registro(id_: str = "p-000000000001", **cambios) -> dict:
    return {
        "id": id_,
        "nombre": "Festival del Café",
        "tipo": None,
        "fecha_inicio": "2026-11-13",
        "fecha_fin": "2026-11-15",
        "distrito": "Villa Rica",
        "provincia": "Oxapampa",
        "region": "Pasco",
        "lat": -10.7345,
        "lon": -75.2712,
        "descripcion": None,
        "url": "https://www.munivillarica.gob.pe/festival",
        "publicado_por": "Municipalidad Distrital de Villa Rica",
        "publicado": "2026-10-02T09:30:15-05:00",
        **cambios,
    }


class TablaFalsa:
    """Lo que ``EnDynamo`` usa de una tabla de boto3, con las reglas de DynamoDB que importan aquí:
    no acepta ``float``, devuelve los números como ``Decimal`` y entrega el ``scan`` por páginas."""

    def __init__(self, por_pagina: int = 2) -> None:
        self.items: dict[str, dict] = {}
        self.por_pagina = por_pagina
        self.lecturas: list[dict] = []
        self.consultas: list[dict] = []
        self.no_deja_guardar: str | None = None  # el id que la tabla rechaza

    def put_item(self, Item: dict) -> None:  # «Item», con mayúscula: así se llama en boto3
        for campo, valor in Item.items():
            if isinstance(valor, float):
                raise TypeError(f"Float types are not supported. Use Decimal types instead ({campo}).")
        assert isinstance(Item["id"], str) and Item["id"], "la clave de la tabla es «id»"
        if Item["id"] == self.no_deja_guardar:
            raise OSError("ProvisionedThroughputExceededException")
        self.items[Item["id"]] = dict(Item)

    def get_item(self, **opciones) -> dict:
        self.consultas.append(opciones)
        item = self.items.get(opciones["Key"]["id"])
        return {"Item": self._como_lo_devuelve_dynamo(item)} if item else {}

    def scan(self, **opciones) -> dict:
        self.lecturas.append(opciones)
        claves = sorted(self.items)
        inicio = claves.index(opciones["ExclusiveStartKey"]["id"]) + 1 if "ExclusiveStartKey" in opciones else 0
        pagina = claves[inicio : inicio + self.por_pagina]
        respuesta: dict = {"Items": [self._como_lo_devuelve_dynamo(self.items[c]) for c in pagina]}
        if inicio + self.por_pagina < len(claves):
            respuesta["LastEvaluatedKey"] = {"id": pagina[-1]}
        return respuesta

    @staticmethod
    def _como_lo_devuelve_dynamo(item: dict) -> dict:
        return {k: Decimal(v) if isinstance(v, int) and not isinstance(v, bool) else v for k, v in item.items()}


@pytest.fixture(params=["memoria", "archivo", "dynamo"])
def dos_servidores(request, tmp_path):
    """El almacén visto desde dos procesos del API. La memoria no se comparte: es el mismo las dos veces."""
    if request.param == "memoria":
        return (unico := EnMemoria()), unico
    if request.param == "archivo":
        ruta = tmp_path / "datos" / "eventos.jsonl"
        return EnArchivo(ruta), EnArchivo(ruta)
    tabla = TablaFalsa()
    return EnDynamo("eventos", tabla), EnDynamo("eventos", tabla)


@pytest.fixture
def almacen(dos_servidores):
    return dos_servidores[0]


class TestCualquierAlmacen:
    def test_vacio(self, almacen):
        assert almacen.leer() == []

    def test_devuelve_lo_que_se_guardo(self, almacen):
        uno, otro = registro(), registro("p-000000000002", lat=None, lon=None, url=None, tipo="Feria")
        almacen.guardar(uno)
        almacen.guardar(otro)
        assert sorted(almacen.leer(), key=lambda r: r["id"]) == [uno, otro]

    def test_guardar_el_mismo_id_lo_reemplaza(self, almacen):
        almacen.guardar(registro())
        almacen.guardar(registro(lat=-10.74, nombre="Festival del Café de Altura"))
        [guardado] = almacen.leer()
        assert (guardado["lat"], guardado["nombre"]) == (-10.74, "Festival del Café de Altura")

    def test_lo_devuelto_no_es_lo_guardado(self, almacen):
        original = registro()
        almacen.guardar(original)
        original["nombre"] = "cambiado después de guardar"
        almacen.leer()[0]["nombre"] = "cambiado después de leer"
        assert almacen.leer()[0]["nombre"] == "Festival del Café"

    def test_la_marca_cambia_cada_vez_que_alguien_guarda(self, dos_servidores):
        uno, otro = dos_servidores
        vistas = [otro.marca()]
        uno.guardar(registro())
        vistas.append(otro.marca())
        uno.guardar(registro("p-000000000002"))
        vistas.append(otro.marca())
        uno.guardar(registro("p-000000000002", lat=-10.74))  # corregir uno también es guardar
        vistas.append(otro.marca())
        assert len(set(vistas)) == 4

    def test_la_marca_no_cambia_si_nadie_guarda(self, dos_servidores):
        uno, otro = dos_servidores
        vacia = otro.marca()
        assert uno.marca() == vacia == otro.marca()
        uno.guardar(registro())
        con_uno = otro.marca()
        uno.leer()
        otro.leer()
        assert uno.marca() == con_uno == otro.marca()


class TestEnArchivo:
    def test_lo_guardado_sigue_ahi_al_reiniciar(self, tmp_path):
        ruta = tmp_path / "eventos.jsonl"
        EnArchivo(ruta).guardar(registro())
        assert EnArchivo(ruta).leer() == [registro()]

    def test_una_linea_por_evento_con_sus_tildes(self, tmp_path):
        ruta = tmp_path / "eventos.jsonl"
        EnArchivo(ruta).guardar(registro())
        [linea] = ruta.read_text(encoding="utf-8").splitlines()
        assert "Festival del Café" in linea and json.loads(linea) == registro()

    def test_una_linea_rota_no_tumba_a_las_demas(self, tmp_path, caplog):
        ruta = tmp_path / "eventos.jsonl"
        almacen = EnArchivo(ruta)
        almacen.guardar(registro())
        with ruta.open("a", encoding="utf-8") as fh:
            fh.write('{"id": "p-00000000000\n\n[1, 2]\n{"sin": "id"}\n')
        almacen.guardar(registro("p-000000000002"))
        with caplog.at_level(logging.WARNING, logger="dreemgo.almacen"):
            assert [r["id"] for r in almacen.leer()] == ["p-000000000001", "p-000000000002"]
        assert len(caplog.records) == 3


class TestEnDynamo:
    def test_los_numeros_van_como_decimal_y_vuelven_como_numeros(self):
        tabla = TablaFalsa()
        almacen = EnDynamo("eventos", tabla)
        almacen.guardar(registro())
        item = tabla.items["p-000000000001"]
        assert item["lat"] == Decimal("-10.7345") and item["lon"] == Decimal("-75.2712")
        assert item["tipo"] is None
        [leido] = almacen.leer()
        assert leido == registro() and isinstance(leido["lat"], float)

    def test_la_tabla_borra_sola_lo_que_ya_paso(self):
        tabla = TablaFalsa()
        EnDynamo("eventos", tabla).guardar(registro())  # termina el 15 de noviembre
        expira = datetime.fromtimestamp(tabla.items["p-000000000001"]["expira"], tz=UTC)
        assert expira.replace(microsecond=0) == datetime(2026, 11, 16, 23, 59, 59, tzinfo=UTC)
        assert "expira" not in EnDynamo("eventos", tabla).leer()[0]
        assert "expira" not in tabla.items[EnDynamo.MARCA]  # la marca no vence

    def test_la_marca_es_un_item_de_la_tabla_que_no_sale_entre_los_eventos(self):
        tabla = TablaFalsa()
        almacen = EnDynamo("eventos", tabla)
        almacen.guardar(registro())
        assert sorted(tabla.items) == [EnDynamo.MARCA, "p-000000000001"]
        assert almacen.leer() == [registro()]
        assert almacen.marca() == tabla.items[EnDynamo.MARCA]["marca"]
        assert tabla.consultas == [{"Key": {"id": EnDynamo.MARCA}, "ConsistentRead": True}]

    def test_si_no_se_puede_dejar_la_marca_el_evento_igual_queda_guardado(self, caplog):
        tabla = TablaFalsa()
        tabla.no_deja_guardar = EnDynamo.MARCA
        almacen = EnDynamo("eventos", tabla)
        with caplog.at_level(logging.WARNING, logger="dreemgo.almacen"):
            almacen.guardar(registro())
        assert almacen.leer() == [registro()]
        assert "no su marca" in caplog.text

    def test_si_no_se_puede_guardar_el_evento_falla_y_no_mueve_la_marca(self):
        tabla = TablaFalsa()
        tabla.no_deja_guardar = "p-000000000001"
        almacen = EnDynamo("eventos", tabla)
        with pytest.raises(OSError):
            almacen.guardar(registro())
        assert tabla.items == {}

    def test_lee_todas_las_paginas_con_lectura_consistente(self):
        tabla = TablaFalsa(por_pagina=2)
        almacen = EnDynamo("eventos", tabla)
        for n in range(5):
            almacen.guardar(registro(f"p-00000000000{n}"))
        assert sorted(r["id"] for r in almacen.leer()) == [f"p-00000000000{n}" for n in range(5)]
        assert len(tabla.lecturas) == 3
        assert all(lectura["ConsistentRead"] is True for lectura in tabla.lecturas)

    def test_no_necesita_boto3_hasta_que_toca_la_tabla(self):
        EnDynamo("eventos")  # crearlo no importa boto3 ni sale a la red


class TestDelEntorno:
    def test_sin_variables_en_memoria(self):
        assert isinstance(del_entorno({}), EnMemoria)

    def test_con_archivo(self, tmp_path):
        ruta = tmp_path / "eventos.jsonl"
        almacen = del_entorno({"DREEMGO_EVENTOS_ARCHIVO": str(ruta)})
        assert isinstance(almacen, EnArchivo)
        almacen.guardar(registro())
        assert ruta.exists()

    def test_con_tabla_gana_la_tabla(self, tmp_path):
        entorno = {"DREEMGO_TABLA_EVENTOS": "dreemgo-eventos", "DREEMGO_EVENTOS_ARCHIVO": str(tmp_path / "e.jsonl")}
        assert isinstance(del_entorno(entorno), EnDynamo)

    def test_una_variable_vacia_es_como_no_tenerla(self):
        assert isinstance(del_entorno({"DREEMGO_TABLA_EVENTOS": "", "DREEMGO_EVENTOS_ARCHIVO": ""}), EnMemoria)
