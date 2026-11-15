"""El aviso de seguridad (decisión 0029): si se duerme en una zona con alerta oficial de viaje, como el VRAEM, o
alguna parada está en ella, la ruta lo dice antes que nada; si no, no. Las zonas se marcan aquí a mano sobre los
artefactos, para que la prueba no dependa de la versión de los datos."""

import dataclasses

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from pipeline.artefactos import zonas_de_seguridad

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
A_HUARAZ = Consulta(origen="lima", mes=7, dias=4, solo_por_tierra=True)


@pytest.fixture(scope="module")
def datos():
    return artefactos.cargar()


def _en_el_vraem(datos, codigos=(), bases=()):
    """Los mismos datos, con esos recursos y esas bases en el VRAEM."""
    recursos = {c: {**r, "zona": "vraem"} if c in codigos else r for c, r in datos.recursos.items()}
    polos = {
        i: dataclasses.replace(p, base={**p.base, "zona": "vraem"}) if i in bases else p for i, p in datos.polos.items()
    }
    return dataclasses.replace(datos, recursos=recursos, polos=polos)


def _polo(datos, base: str) -> int:
    return next(p.id for p in datos.polos.values() if p.base["nombre"] == base)


def _huaraz(datos):
    return next(r for r in viaje.resolver(A_HUARAZ, datos).rutas if r.polo.base.nombre == "Huaraz")


def test_si_se_duerme_en_el_vraem_se_avisa_primero_y_nombra_la_base(datos):
    kimbiri = _polo(datos, "Kimbiri")
    consulta = Consulta(origen="ayacucho", mes=7, dias=4, destino=kimbiri)
    (ruta,) = viaje.resolver(consulta, _en_el_vraem(datos, bases={kimbiri})).rutas
    aviso = ruta.avisos[0]
    assert (aviso.tipo, aviso.nivel) == ("seguridad", "advertencia")
    assert aviso.mensaje.startswith("Kimbiri, donde se duerme, está en el VRAEM")
    assert "Canadá y Estados Unidos recomiendan no viajar ahí" in aviso.mensaje


def test_si_solo_una_parada_esta_en_el_vraem_se_nombra_la_parada(datos):
    sin_zona = _huaraz(datos)
    assert not [a for a in sin_zona.avisos if a.tipo == "seguridad"]
    paradas = [p.recurso for d in sin_zona.dias for p in d.paradas]
    ruta = _huaraz(_en_el_vraem(datos, codigos={paradas[0].codigo}))
    assert ruta.avisos[0].mensaje.startswith(f"{paradas[0].nombre} está en el VRAEM")
    assert ruta.avisos[1:] == sin_zona.avisos and ruta.dias == sin_zona.dias  # el aviso no cambia el plan
    muchas = _huaraz(_en_el_vraem(datos, codigos={p.codigo for p in paradas}))
    nombres = viaje.textos.lista([p.nombre for p in paradas[:3]])
    assert muchas.avisos[0].mensaje.startswith(f"{len(paradas)} paradas están en el VRAEM")
    assert f", entre ellas {nombres}." in muchas.avisos[0].mensaje


def test_en_una_excursion_de_un_dia_la_base_no_cuenta(datos):
    """En un día no se duerme en la base: si ninguna parada está en la zona, no hay aviso."""
    urubamba = _polo(datos, "Urubamba")
    consulta = Consulta(origen="cusco", mes=7, dias=1, destino=urubamba)
    (ruta,) = viaje.resolver(consulta, _en_el_vraem(datos, bases={urubamba})).rutas
    assert ruta.dias[0].paradas and not [a for a in ruta.avisos if a.tipo == "seguridad"]


def test_cada_zona_de_la_tabla_tiene_con_que_avisarse():
    assert set(zonas_de_seguridad()["zona"]) <= set(viaje.ZONAS_DE_SEGURIDAD)
