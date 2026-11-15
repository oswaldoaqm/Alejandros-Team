"""El aviso de entradas (decisión 0029): una parada que vende un número fijo de entradas por día, como Machu Picchu,
dice cuántas personas entran y dónde se compran. El cupo se pone aquí sobre los artefactos, para que la prueba no
dependa de la versión de los datos."""

import dataclasses

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from pipeline.artefactos import entradas_con_cupo

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
MACHU_PICCHU = {
    "nombre": "Machu Picchu",
    "por_dia": 4500,
    "por_dia_alta": 5600,
    "en_linea": "tuboleto.cultura.pe",
    "en_persona": "Machu Picchu Pueblo",
    "en_persona_por_dia": 1000,
}


def test_dice_cuantas_personas_entran_y_donde_se_compran():
    aviso = viaje.aviso_de_entradas(MACHU_PICCHU)
    assert (aviso.tipo, aviso.nivel) == ("entradas", "info")
    assert aviso.mensaje == (
        "A Machu Picchu entran 4 500 personas al día como máximo, y 5 600 en temporada alta. Las entradas "
        "se venden en tuboleto.cultura.pe y, solo 1 000 al día, en persona en Machu Picchu Pueblo. Compra la "
        "entrada con anticipación."
    )


@pytest.mark.parametrize(
    "cupo, dice",
    [
        ({"en_linea": "tuboleto.cultura.pe"}, "Las entradas se venden solo en tuboleto.cultura.pe."),
        ({"en_persona": "Machu Picchu Pueblo"}, "Las entradas se venden solo en persona, en Machu Picchu Pueblo."),
        ({}, "como máximo. Compra la entrada con anticipación."),
    ],
)
def test_lo_que_no_se_sabe_no_se_dice(cupo, dice):
    assert dice in viaje.aviso_de_entradas({"nombre": "Machu Picchu", "por_dia": 4500, **cupo}).mensaje


@con_datos
def test_un_viaje_que_visita_machu_picchu_lo_avisa_y_los_demas_no():
    datos = artefactos.cargar()
    con_cupo = dataclasses.replace(
        datos, recursos={c: {**r, "cupo": MACHU_PICCHU if c == "917" else None} for c, r in datos.recursos.items()}
    )
    rutas = viaje.resolver(Consulta(origen="cusco", mes=6, dias=2, intereses=["historia"]), con_cupo).rutas
    for ruta in rutas:
        visita = any(p.recurso.codigo == "917" for d in ruta.dias for p in d.paradas)
        de_entradas = [a.mensaje for a in ruta.avisos if a.tipo == "entradas"]
        assert de_entradas == ([viaje.aviso_de_entradas(MACHU_PICCHU).mensaje] if visita else [])
    assert any(r.polo.base.nombre == "Machupicchu Pueblo" for r in rutas)


@con_datos
def test_cada_entrada_con_cupo_es_una_parada():
    datos = artefactos.cargar()
    assert all(datos.recursos[codigo]["es_parada"] for codigo in entradas_con_cupo())
