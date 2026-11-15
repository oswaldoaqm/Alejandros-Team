"""El terminal de bus en cada punta de la ida (decisión 0030), sin la red: lo que se elige y lo que se suma."""

import pandas as pd

from pipeline.terminales import EMBARQUE_MIN, es_terminal, mas_cercano, sumar_terminales


def test_el_transporte_urbano_no_es_un_terminal():
    assert es_terminal("Terminal Terrestre de Arequipa") and es_terminal("Cruz del Sur")
    assert not es_terminal("Estación Jirón de la Unión hacia el Norte")
    assert not es_terminal("Colectivos a Campo Verde")
    assert not es_terminal("Estación Naranjal") and not es_terminal("")


def test_un_terminal_terrestre_gana_aunque_otro_quede_mas_cerca():
    puntos = pd.DataFrame({"id": ["arequipa"], "lat": [-16.3988], "lon": [-71.5369]})
    terminales = pd.DataFrame(
        {
            "osm": ["node/1", "node/2", "node/3"],
            "nombre": ["Flores", "Terminal Terrestre de Arequipa", "Estación de buses urbanos hacia el Norte"],
            "lat": [-16.3990, -16.4230, -16.3989],
            "lon": [-71.5370, -71.5450, -71.5369],
        }
    )
    [fila] = mas_cercano(puntos, terminales, 15).to_dict("records")
    assert fila["terminal"] == "Terminal Terrestre de Arequipa"
    assert mas_cercano(puntos, terminales.iloc[[1]], 1).empty  # a más de 1 km no hay terminal


def test_la_ida_larga_suma_los_dos_taxis_y_el_embarque_y_la_corta_no():
    tiempos = pd.DataFrame(
        {
            "origen": ["lima", "lima", "lima"],
            "polo": [1, 2, 3],
            "minutos": [600.0, 60.0, 400.0],
            "km": [500.0, 40.0, 300.0],
        }
    )
    terminales = pd.DataFrame(
        {
            "punta": ["origen", "base", "base"],
            "id": ["lima", "1", "3"],
            "minutos": [20.0, 6.0, 45.0],
            "km": [8.0, 1.5, 20.0],
        }
    )
    t = sumar_terminales(tiempos, terminales).set_index("polo")
    assert t.loc[1, "minutos"] == 600 + 20 + EMBARQUE_MIN + 6 and t.loc[1, "km"] == 509.5
    assert t.loc[2, "minutos"] == 60  # en una ida corta se va en colectivo o en auto
    assert t.loc[3, "minutos"] == 400 + 20 + EMBARQUE_MIN  # a más de media hora en taxi, el bus deja en el pueblo
