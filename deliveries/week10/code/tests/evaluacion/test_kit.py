"""El kit para calificar (decisión 0021): cada zona una vez, con el puesto que le da cada sistema, en un
orden fijo; el cuadernillo con un formulario por viaje; y las tablas como las lee Excel."""

import csv
import json
import re

import pytest

from dreemgo.motor import datos as artefactos
from evaluacion import consultas, kit

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


@pytest.fixture(scope="module")
def datos():
    return artefactos.cargar()


@pytest.fixture(scope="module")
def filas(datos):
    """Dos consultas: la playa de un fin de semana desde Lima y el montañista de Huaraz."""
    por_id = {c.id: c for c in consultas.leer()}
    return [(por_id[n], kit.opciones(n, por_id[n].consulta, datos)) for n in (15, 38)]


def test_cada_zona_sale_una_vez_con_el_puesto_que_le_da_cada_sistema(filas, datos):
    for anotada, ops in filas:
        assert [op.letra for op in ops] == list(kit.LETRAS[: len(ops)])
        assert len({op.ruta.polo.id for op in ops}) == len(ops)
        for nombre, proponer in kit.SISTEMAS.items():
            propuestas = proponer(anotada.consulta, datos)
            puestos = sorted(op.puestos[nombre] for op in ops if nombre in op.puestos)
            assert puestos == list(range(1, len(propuestas) + 1))
            assert {op.ruta.polo.id for op in ops if nombre in op.puestos} == set(propuestas)


def test_el_orden_es_siempre_el_mismo(filas, datos):
    anotada, ops = filas[0]
    otra_vez = kit.opciones(anotada.id, anotada.consulta, datos)
    assert [(op.letra, op.ruta.polo.id) for op in otra_vez] == [(op.letra, op.ruta.polo.id) for op in ops]


def test_el_cuadernillo_tiene_un_formulario_por_viaje(filas, datos):
    pagina = kit.cuadernillo(filas, datos)
    formularios = re.findall(r"<fieldset data-consulta='(\d+)' data-opcion='(\w)' data-zona='([^']*)'>", pagina)
    esperados = [(str(c.id), op.letra, op.ruta.polo.nombre) for c, ops in filas for op in ops]
    assert formularios == esperados
    assert pagina.count("type='radio'") == 3 * len(esperados)
    datos_kit = json.loads(re.search(r"<script type='application/json' id='kit'>(.*?)</script>", pagina).group(1))
    assert datos_kit == {"huella": kit.huella(filas, datos.version), "columnas": kit.COLUMNAS}


def test_la_huella_cambia_si_cambia_un_viaje(filas, datos):
    (anotada, ops), segunda = filas
    cambiada = [(anotada, ops[::-1]), segunda]
    assert kit.huella(cambiada, datos.version) != kit.huella(filas, datos.version)
    assert kit.huella(filas, "otra") != kit.huella(filas, datos.version)


def test_la_tarjeta_dice_lo_que_hace_falta_para_calificar(filas):
    _, ops = filas[0]
    for op in ops:
        tarjeta = "".join(kit._tarjeta(15, op))
        assert op.ruta.polo.nombre in tarjeta and "Se duerme en" in tarjeta and "por persona" in tarjeta
        assert tarjeta.count("<li><b>Día") == len(op.ruta.dias)


def test_las_tablas_van_con_punto_y_coma_y_con_bom(tmp_path):
    ruta = tmp_path / "t.csv"
    kit.escribir_csv(ruta, kit.COLUMNAS, [[1, "A", "Huacho", "", 'con "comillas"; y punto y coma']])
    assert ruta.read_bytes().startswith(b"\xef\xbb\xbf")
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        [fila] = list(csv.DictReader(fh, delimiter=";"))
    assert fila["comentario"] == 'con "comillas"; y punto y coma' and fila["calificacion"] == ""
