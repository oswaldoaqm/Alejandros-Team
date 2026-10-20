"""Cuándo pesa la altura (decisión 0018): la regla, en un solo lugar, y la altura de cada origen
contra los artefactos de dreemgo/datos."""

import pytest

from dreemgo.motor import aclimatacion
from dreemgo.motor import datos as artefactos

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


@pytest.mark.parametrize(
    "base, origen, pesa",
    [
        (3061, 161, True),  # Huaraz desde Lima
        (3830, 3400, False),  # Puno desde el Cusco: ya se vive en la altura
        (4421, 3400, True),  # Marcapomacocha desde el Cusco: 1 021 m más arriba
        (2499, 0, False),  # bajo los 2 500 m no pesa, aunque se suba desde el mar
        (2722, 1899, False),  # Cajamarca desde Huánuco: menos de 1 000 m
        (None, 161, False),  # sin la altura de la base no se sabe
        (3061, None, False),
    ],
)
def test_pesa_la_altura_si_se_duerme_alto_y_se_llega_de_mil_metros_mas_abajo(base, origen, pesa):
    assert aclimatacion.pesa(base, origen) is pesa


def _zona(datos, nombre: str) -> int:
    [p] = [p.id for p in datos.polos.values() if p.nombre == nombre]
    return p


@con_datos
def test_cada_origen_sabe_a_que_altura_esta():
    """Sin la altura del origen la regla no aplicaría sin que nadie lo note: cada una de las 24 ciudades
    tiene la base de su zona a menos de media hora."""
    datos = artefactos.cargar()
    alturas = {o: aclimatacion.del_origen(origen, datos) for o, origen in datos.origenes.items()}
    assert len(alturas) == 24 and None not in alturas.values()
    assert alturas["lima"] < 300 and alturas["cusco"] == datos.polos[_zona(datos, "Cuzco")].base["altitud_m"]
