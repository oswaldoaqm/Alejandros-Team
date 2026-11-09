"""La auditoría del motor (semana 13): lo que se ve de noche, la cota del mejor orden y las cifras sobre una
corrida armada a mano, con dos ciudades de juguete."""

import numpy as np
import pytest

from dreemgo.motor import datos as artefactos
from evaluacion import auditoria


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("Parque de la Reserva - Circuito Mágico del Agua", True),
        ("Peña Don Porfirio", True),
        ("Observatorio Astronómico de Moquegua", True),
        ("Paseo Sáenz Peña", False),  # una calle con nombre de persona
        ("Plaza Mayor de Lima", False),
    ],
)
def test_lo_que_se_ve_de_noche(nombre, esperado):
    assert auditoria.de_noche(nombre) is esperado


def test_el_mejor_orden_es_una_cota_del_camino():
    base = np.array([10.0, 1.0, 10.0])
    entre = np.array([[0.0, 5.0, 1.0], [5.0, 0.0, 1.0], [1.0, 1.0, 0.0]])
    dado, mejor = auditoria.camino_y_mejor(base, entre, [0, 1, 2])
    assert dado == 10 + 5 + 1 + 10
    assert mejor == 1 + 1 + 1 + 10  # 1 → 2 → 0, o al revés
    assert auditoria.camino_y_mejor(base, np.full((3, 3), np.inf), [0, 1, 2]) is None


def _parada(lat, km, traslado, visita=60, jerarquia=3, nombre="Lugar"):
    return {
        "nombre": nombre,
        "jerarquia": jerarquia,
        "lat": lat,
        "lon": 0.0,
        "llegada": "10:00",
        "traslado": traslado,
        "km": km,
        "visita": visita,
    }


def test_las_cifras_de_una_corrida_a_mano():
    # Dos «ciudades» de juguete: la latitud 1 es Lima y la 2 una ciudad grande; la 0, el campo.
    def banda_de(lat, lon):
        return {0: (0, "fuera"), 1: (1, "metropoli"), 2: (2, "grande")}[round(lat)]

    lima = {
        "nombre": "Lima",
        "base": [1.0, 0.0],
        "dias": [
            {
                "tipo": "visita",
                "horas": 7.5,
                "orden": [11.0, 10.0],
                "paradas": [_parada(1, 10, 20), _parada(1, 4, 20), _parada(1, 0.5, 5)],  # 30 y 12 km/h; corta
            }
        ],
    }
    campo = {
        "nombre": "Campo",
        "base": [0.0, 0.0],
        "dias": [{"tipo": "visita", "horas": 5.0, "orden": [10.0, 10.0], "paradas": [_parada(2, 10, 30)]}],
    }
    corrida = [{"rutas": [lima, campo]}, {"rutas": [lima]}]
    c = auditoria.cifras(corrida, banda_de, {"metropoli": 16.0, "grande": 17.0})
    assert c["viajes"] == 3
    # El tramo de menos de 1 km no cuenta, ni el que sale del campo a la ciudad grande.
    assert c["tramos_en_ciudad"] == {
        "metropoli": {
            "tramos": 4,
            "km_mediana": 7.0,
            "minutos_mediana": 20.0,
            "kmh_mediana": 21.0,
            "tomtom_kmh": 16.0,
            "mas_rapidos_que_tomtom": 0.5,
        }
    }
    assert c["dias"]["en_lima"]["dias"] == 2
    assert c["dias"]["con_7_5_horas_o_mas"] == round(2 / 3, 3)
    assert c["orden"] == {"dias": 3, "el_mejor": round(1 / 3, 3), "a_mas_de_5_por_ciento": round(2 / 3, 3)}
    assert c["concentracion"]["las_5_mas_propuestas"][0] == ["Lima", round(2 / 3, 3)]
    assert c["concentracion"]["con_base_en_ciudad_grande_o_lima"] == round(2 / 3, 3)


@pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
def test_la_rejilla_y_una_consulta():
    datos = artefactos.cargar()
    consultas = auditoria.rejilla(datos)
    assert len(consultas) == len(datos.origenes) * 4 * 12
    auditoria._iniciar(None)
    salida = auditoria.correr(("lima", 7, 2))
    assert salida["rutas"]
    for ruta in salida["rutas"]:
        for dia in ruta["dias"]:
            if dia["orden"]:
                dado, mejor = dia["orden"]
                assert mejor <= dado + 1e-9
