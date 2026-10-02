"""El tren y el bote en el motor: lo que traen los artefactos."""

import numpy as np

from dreemgo.motor import datos as artefactos

POLO = {
    "id": 1,
    "nombre": "Puno",
    "region": "Puno",
    "regiones": ["Puno"],
    "recursos": 2,
    "fuera_del_circuito": True,
    "novedad": 0.5,
    "base": {"nombre": "Puno"},
    "paradas": ["10", "11"],
    "base_minutos": [153.2, 8.0],
    "base_km": [45.6, 1.0],
    "entre_minutos": [[0.0, 120.0], [120.0, 0.0]],
    "entre_km": [[0.0, 31.0], [31.0, 0.0]],
    "clima": [],
    "eventos": [],
}


def test_un_polo_sin_tren_ni_bote_se_lee_con_ceros():
    polo = artefactos._polo(POLO)
    assert polo.base_km_tren.tolist() == [0.0, 0.0] and polo.entre_km_bote.tolist() == [[0.0, 0.0], [0.0, 0.0]]
    con_bote = artefactos._polo(POLO | {"base_km_bote": [30.6, None], "entre_km_bote": [[0.0, 30.6], [30.6, 0.0]]})
    assert con_bote.base_km_bote[0] == 30.6 and np.isnan(con_bote.base_km_bote[1])
    assert con_bote.entre_km_bote[0, 1] == 30.6 and not con_bote.base_km_tren.any()


def test_un_origen_trae_los_km_en_tren_y_en_bote_de_cada_camino():
    origen = artefactos._origen(
        {
            "id": "puno",
            "nombre": "Puno",
            "region": "Puno",
            "lat": -15.84,
            "lon": -70.02,
            "a_base": {"1": [5.0, 1.3, 0.0, 0.0], "2": [None, None, None, None], "3": [90.0, 60.0]},
            "a_parada": {"10": [153.2, 45.6, 0.0, 30.6]},
        }
    )
    assert origen.a_parada["10"] == (153.2, 45.6) and origen.a_parada_en_capa["10"] == (0.0, 30.6)
    # Sin km en tren ni en bote, sin camino, y un artefacto de antes, que solo trae minutos y km.
    assert origen.a_base_en_capa == {1: (0.0, 0.0), 2: (0.0, 0.0), 3: (0.0, 0.0)}
