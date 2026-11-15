"""Dónde dormir: hasta tres hospedajes con nombre cerca de la base (decisión 0032), sin leer el extracto."""

import pandas as pd

from pipeline.hospedajes import cerca, sin_contacto


def test_van_los_tres_mas_cercanos_sin_repetir_nombre_y_dentro_del_radio():
    bases = pd.DataFrame({"polo": [7], "lat": [-8.1116], "lon": [-79.0287]})
    hospedajes = pd.DataFrame(
        {
            "osm": ["node/1", "node/2", "way/3", "node/4", "node/5"],
            "nombre": ["Casa Andina", "casa andina", "Los Corregidores", "Yaqta Hostel", "Lejano"],
            "tipo": ["hotel", "hotel", "hotel", "albergue", "hotel"],
            "lat": [-8.1117, -8.1118, -8.1125, -8.1130, -8.2000],
            "lon": [-79.0287, -79.0288, -79.0290, -79.0300, -79.0287],
        }
    )
    salida = cerca(bases, hospedajes)
    assert salida["nombre"].tolist() == ["Casa Andina", "Los Corregidores", "Yaqta Hostel"]
    assert salida["km"].is_monotonic_increasing and (salida["km"] <= 2).all()
    assert cerca(bases, hospedajes.iloc[[4]]).empty  # a casi 10 km no cuenta


def test_el_nombre_se_corta_donde_empieza_un_contacto():
    assert sin_contacto("Hostal Sol N 120 Cel 987654321, 912345678") == "Hostal Sol N 120"
    assert sin_contacto("Casa Inti - Telf. 01 4567890") == "Casa Inti"
    assert sin_contacto("Posada reservas@posada.pe") == "Posada"
    assert sin_contacto("Hotel La Reserva") == "Hotel La Reserva"
    assert sin_contacto("Hostal 2000") == "Hostal 2000"  # un año o un número corto se queda
    assert sin_contacto("987654321") == ""
    bases = pd.DataFrame({"polo": [7], "lat": [-8.1116], "lon": [-79.0287]})
    hospedajes = pd.DataFrame(
        {"osm": ["node/1"], "nombre": ["999888777"], "tipo": ["hotel"], "lat": [-8.1117], "lon": [-79.0287]}
    )
    assert cerca(bases, hospedajes).empty  # sin nombre, después de cortar, no va
