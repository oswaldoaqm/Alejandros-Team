"""Qué zonas propone cada sistema (semana 12): la cuenta de las coincidencias y la cobertura con el kit del
repositorio."""

import pytest

from dreemgo.motor import datos as artefactos
from evaluacion import zonas
from evaluacion.informe import CARPETA, Viaje, leer_clave


def _viaje(consulta, opcion, polo, **puestos):
    return Viaje(consulta, opcion, polo, f"zona {polo}", puestos)


def test_las_coincidencias_se_cuentan_por_consulta_y_sin_mirar_el_puesto():
    viajes = [
        _viaje(1, "A", 10, motor=1, guia=3),
        _viaje(1, "B", 11, motor=2),
        _viaje(1, "C", 12, guia=1),
        _viaje(2, "A", 10, motor=1),
        _viaje(2, "B", 13, guia=1),
    ]
    de_cada = zonas.propuestas(viajes, ["motor", "guia"])
    assert de_cada["motor"] == {1: {10, 11}, 2: {10}}
    c = zonas.coinciden(de_cada)["motor_y_guia"]
    # La zona 10 de la consulta 2 la propone solo el motor: no cuenta, aunque la guía la proponga en la 1.
    assert c == {"propuestas_en_comun": 1, "de": 3, "consultas_con_las_mismas_zonas": 0, "consultas": 2}


@pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
def test_la_cobertura_de_los_tres_sistemas_con_el_kit():
    viajes, sistemas = leer_clave(CARPETA / "clave.csv")
    datos = artefactos.cargar()
    de_cada = zonas.propuestas(viajes, sistemas)
    cobertura = zonas.cobertura(de_cada, datos)
    assert set(cobertura) == {"motor", "guia", "variante"}
    for c in cobertura.values():
        assert c["viajes"] == 120  # tres por cada una de las 40 consultas
        assert 0 < c["zonas_distintas"] <= c["de"] == len(datos.polos)
        assert 0 <= c["fuera_del_circuito"] <= 1
    for c in zonas.coinciden(de_cada).values():
        assert 0 <= c["propuestas_en_comun"] <= c["de"] == 120
