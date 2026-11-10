"""La lista de zonas que la app busca en «Quiero ir a…» (pipeline/destinos.py)."""

import json

import pytest

from dreemgo.motor import datos as artefactos
from pipeline import destinos

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


@con_datos
def test_la_lista_publicada_es_la_de_estos_datos():
    # Si falla: correr «python -m pipeline.destinos» después de rehacer los artefactos.
    publicada = json.loads(destinos.SALIDA.read_text(encoding="utf-8"))
    assert publicada == destinos.destinos(artefactos.cargar())


@con_datos
def test_entran_las_zonas_con_algo_que_visitar_en_una_jornada():
    datos = artefactos.cargar()
    zonas = {z["id"]: z for z in destinos.destinos(datos)["zonas"]}
    fuera = {p.nombre for p in datos.polos.values() if p.id not in zonas}
    assert fuera == {"Queropalca"}  # solo caminatas de más de un día
    for polo in datos.polos.values():
        assert (polo.id in zonas) == bool(destinos.lugares_de_un_dia(polo, datos))
    cusco = next(z for z in zonas.values() if z["nombre"] == "Cuzco")
    assert (cusco["region"], cusco["regiones"], cusco["misma_ciudad"]) == ("Cusco", ["Cusco", "Apurímac"], ["cusco"])
    # Cada origen tiene la suya, y Lima, dos: también Miraflores.
    en_casa = sorted(o for z in zonas.values() for o in z["misma_ciudad"])
    assert en_casa == sorted([*datos.origenes, "lima"])


@con_datos
def test_los_lugares_van_de_mayor_a_menor_jerarquia_y_sin_repetir():
    for zona in destinos.destinos(artefactos.cargar())["zonas"]:
        nombres = [nombre for nombre, _ in zona["lugares"]]
        jerarquias = [jerarquia or 0 for _, jerarquia in zona["lugares"]]
        assert len(nombres) == len(set(nombres))
        assert jerarquias == sorted(jerarquias, reverse=True)


@con_datos
def test_el_peso_es_lo_que_valen_sus_doce_lugares_mas_importantes_y_ordena_la_lista():
    datos = artefactos.cargar()
    zonas = destinos.destinos(datos)["zonas"]
    assert [z["peso"] for z in zonas] == sorted((z["peso"] for z in zonas), reverse=True)
    machu_picchu = next(z for z in zonas if z["nombre"] == "Machupicchu Pueblo")
    assert machu_picchu["lugares"][0] == ["Parque Arqueológico Nacional de Machu Picchu", 4]
    valores = sorted(({1: 1, 2: 2, 3: 6, 4: 24, None: 2}[j] for _, j in machu_picchu["lugares"]), reverse=True)
    assert machu_picchu["peso"] == sum(valores[:12]) == 46
    # En el Cusco, primero lo que más se visita, y no el pueblo con más lugares corrientes.
    del_cusco = [z["nombre"] for z in zonas if "Cusco" in z["regiones"]]
    assert del_cusco[:3] == ["Cuzco", "Urubamba", "Machupicchu Pueblo"]
