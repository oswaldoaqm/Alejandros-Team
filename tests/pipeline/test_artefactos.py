"""Lo que los artefactos guardan de los caminos en tren y en bote, y cómo lo lee el motor."""

import numpy as np
import pandas as pd

from dreemgo.motor import datos as motor
from pipeline import artefactos

ORIGENES = pd.DataFrame({"id": ["puno"], "ciudad": ["Puno"], "region": ["Puno"], "lat": [-15.84], "lon": [-70.02]})


def _tablas_de_dos_polos():
    """El polo 1 tiene una isla a la que se llega en bote; en el polo 2 todo va por carretera."""
    maestro = pd.DataFrame(
        {
            "codigo": [10, 11, 20, 21],
            "nombre": ["Isla", "Muelle", "Plaza", "Mirador"],
            "polo": [1, 1, 2, 2],
            "es_parada": True,
            "jerarquia": [3, 2, 2, 1],
            "region": "Puno",
        }
    )
    bases = pd.DataFrame(
        {
            "polo": [1, 2],
            "base": ["Puno", "Juli"],
            "lat": [-15.84, -16.21],
            "lon": [-70.02, -69.46],
            "altitud_m": [3827.0, 3869.0],
            "altitud_fuente": "osm",
            "lugar": ["ciudad", "pueblo"],
            "hospedajes_osm": [50, 3],
            "criterio": "carretera",
        }
    )
    clima = pd.DataFrame(
        {
            "polo": [1, 2],
            "mes": 1,
            "lluvia_mm": 150.0,
            "dias_con_lluvia": 20.0,
            "temp_min_c": 4.0,
            "temp_max_c": 15.0,
            "puesto_lluvia": 1,
            "veredicto": "advertencia",
            "fuente": "open_meteo_polo",
        }
    )
    entre = pd.DataFrame(
        {
            "polo": [1, 1, 2, 2],
            "desde": [10, 11, 20, 21],
            "hasta": [11, 10, 21, 20],
            "minutos": [120.0, 120.0, 10.0, 10.0],
            "km": [31.0, 31.0, 4.0, 4.0],
            "km_tren": 0.0,
            "km_bote": [30.6, 30.6, 0.0, 0.0],
        }
    )
    desde_base = pd.DataFrame(
        {
            "polo": [1, 1, 2, 2],
            "codigo": [10, 11, 20, 21],
            "minutos": [153.2, 8.0, 5.0, 12.0],
            "km": [45.6, 1.0, 0.5, 4.2],
            "km_tren": 0.0,
            "km_bote": [30.6, 0.0, 0.0, 0.0],
        }
    )
    a_base = pd.DataFrame({"origen": "puno", "polo": [1, 2], "minutos": [5.0, 90.0]})
    eventos = pd.DataFrame({"polo": pd.Series(dtype=int), "codigo": pd.Series(dtype=int)})
    return maestro, bases, clima, entre, desde_base, a_base, eventos, ORIGENES


def test_un_polo_guarda_los_km_en_bote_solo_si_algun_camino_va_en_bote():
    con_bote, sin_bote = artefactos.polos(*_tablas_de_dos_polos())
    assert con_bote["base_km_bote"] == [30.6, 0.0]
    assert con_bote["entre_km_bote"] == [[0.0, 30.6], [30.6, 0.0]]
    assert "base_km_tren" not in con_bote and "entre_km_tren" not in con_bote  # ninguno va en tren
    assert not any(clave.endswith(("km_tren", "km_bote")) for clave in sin_bote)
    # El motor lee ceros donde el artefacto no trae la capa.
    polo = motor._polo(con_bote)
    assert polo.base_km_bote.tolist() == [30.6, 0.0] and polo.base_km_tren.tolist() == [0.0, 0.0]
    assert not motor._polo(sin_bote).entre_km_bote.any() and motor._polo(sin_bote).entre_km_bote.shape == (2, 2)


def test_las_tablas_de_antes_del_tren_y_los_botes_tambien_sirven():
    maestro, bases, clima, entre, desde_base, *resto = _tablas_de_dos_polos()
    capas = ["km_tren", "km_bote"]
    polos = artefactos.polos(maestro, bases, clima, entre.drop(columns=capas), desde_base.drop(columns=capas), *resto)
    assert not any(clave.endswith(("km_tren", "km_bote")) for polo in polos for clave in polo)
    assert polos[0]["entre_km"] == [[0.0, 31.0], [31.0, 0.0]] and polos[0]["base_km"] == [45.6, 1.0]


def test_cada_origen_guarda_minutos_km_y_los_km_en_tren_y_en_bote():
    a_base = pd.DataFrame(
        {
            "origen": "puno",
            "polo": [1, 2],
            "minutos": [5.04, np.nan],
            "km": [1.26, np.nan],
            "km_tren": [0.0, np.nan],
            "km_bote": [0.0, np.nan],
        }
    )
    a_parada = pd.DataFrame(
        {
            "origen": "puno",
            "codigo": [10, 11],
            "minutos": [153.2, 300.0],
            "km": [45.6, 90.0],
            "km_tren": 0.0,
            "km_bote": [30.6, 0.0],
        }
    )
    (origen,) = artefactos.origenes_(ORIGENES, a_base, a_parada)
    assert origen["a_base"] == {"1": [5.0, 1.3, 0.0, 0.0], "2": [None, None, None, None]}
    assert origen["a_parada"] == {"10": [153.2, 45.6, 0.0, 30.6]}  # la otra queda a más de 4 horas
    leido = motor._origen(origen)
    assert leido.a_parada_en_capa["10"] == (0.0, 30.6) and leido.a_base_en_capa[2] == (0.0, 0.0)
    assert np.isnan(leido.a_base[2][0])
    # Con las tablas de antes, los km en tren y en bote van en cero.
    (antes,) = artefactos.origenes_(ORIGENES, a_base[["origen", "polo", "minutos", "km"]], a_parada)
    assert antes["a_base"]["1"] == [5.0, 1.3, 0.0, 0.0]
