"""Una ruta aérea sin un vuelo cada día lo avisa (decisión 0030): el motor supone que hay uno cuando se llega al
aeropuerto, y con pocos por semana no es así."""

from dreemgo.motor import viaje
from dreemgo.motor.datos import Vuelo


def _vuelo(*aeropuertos: str) -> Vuelo:
    return Vuelo(600, 80, 0, 0, 65, 30, 15, 60, aeropuertos=aeropuertos)


class _Falso:
    """Lo único que el aviso mira de los datos: los aeropuertos."""

    def __init__(self, aeropuertos):
        self.aeropuertos = aeropuertos


AEROPUERTOS = {
    "LIM": {"ciudad": "Lima", "minutos_a_lima": 0},
    "MZA": {"ciudad": "Mazamari", "minutos_a_lima": 65, "vuelos_al_mes": 9},
    "CUZ": {"ciudad": "Cusco", "minutos_a_lima": 80, "vuelos_al_mes": 1006},
    "AQP": {"ciudad": "Arequipa", "minutos_a_lima": 90},
}


def test_con_pocos_vuelos_dice_cuantos_hay_por_semana():
    aviso = viaje.aviso_de_pocos_vuelos(_vuelo("LIM", "MZA"), _Falso(AEROPUERTOS))
    assert (aviso.tipo, aviso.nivel) == ("acceso", "advertencia")
    assert aviso.mensaje == (
        "No hay un vuelo cada día: a Mazamari, unos 2 por semana. Fija las fechas del viaje según el vuelo, y no al "
        "revés."
    )


def test_con_un_vuelo_cada_dia_o_sin_la_cifra_no_avisa():
    assert viaje.aviso_de_pocos_vuelos(_vuelo("LIM", "CUZ"), _Falso(AEROPUERTOS)) is None
    assert viaje.aviso_de_pocos_vuelos(_vuelo("AQP", "LIM", "CUZ"), _Falso(AEROPUERTOS)) is None
