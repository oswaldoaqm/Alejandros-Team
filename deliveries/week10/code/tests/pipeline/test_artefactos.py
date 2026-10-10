"""Lo que los artefactos guardan de los caminos en tren y en bote, cómo lo lee el motor y cómo
cada recurso pasa de su grupo de TA-01 al polo que lo junta."""

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


def test_la_lejania_de_la_novedad_se_mide_en_la_escala_de_la_carretera():
    maestro, bases, clima, entre, desde_base, a_base, eventos, origenes = _tablas_de_dos_polos()
    # Un tercer polo, a dos días de río de la capital de su región.
    maestro = pd.concat([maestro, maestro.iloc[:2].assign(codigo=[30, 31], polo=3)], ignore_index=True)
    bases = pd.concat([bases, bases.iloc[:1].assign(polo=3, base="Contamana")], ignore_index=True)
    clima = pd.concat([clima, clima.iloc[:1].assign(polo=3)], ignore_index=True)
    a_base = a_base.assign(km_tren=0.0, km_bote=0.0)
    lejano = pd.DataFrame({"origen": "puno", "polo": [3], "minutos": [3000.0], "km_tren": 0.0, "km_bote": 900.0})
    polos = artefactos.polos(
        maestro, bases, clima, entre, desde_base, pd.concat([a_base, lejano], ignore_index=True), eventos, origenes
    )
    # A 5 minutos, a 90 por carretera y a 3 000 por río: el más lejano por carretera ya vale 1,
    # y el del río no lo deja en 0,5 + 0,5 · 85 / 2 995.
    assert [polo["novedad"] for polo in polos] == [0.5, 1.0, 1.0]
    # Sin saber qué va en bote (las tablas de antes), la escala es la de todos.
    polos = artefactos.polos(
        maestro,
        bases,
        clima,
        entre,
        desde_base,
        pd.concat([a_base, lejano], ignore_index=True)[["origen", "polo", "minutos"]],
        eventos,
        origenes,
    )
    assert [polo["novedad"] for polo in polos] == [0.5, 0.5142, 1.0]


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


def test_cada_recurso_lleva_el_polo_que_junta_a_su_grupo():
    maestro, bases, clima, entre, desde_base, a_base, _, origenes = _tablas_de_dos_polos()
    # Un grupo más, el 7, que duerme en Puno como el 1: tiempos.py los deja en un solo polo.
    maestro = pd.concat(
        [maestro, pd.DataFrame({"codigo": [70, 71], "nombre": ["Chullpa", "Feria"], "polo": [7, -1]})],
        ignore_index=True,
    ).assign(es_parada=lambda m: m["codigo"] != 71, jerarquia=2, region="Puno")
    bases = bases.assign(grupos=["1|7", "2"])
    eventos = pd.DataFrame({"polo": [7, 2, -1], "codigo": [900, 901, 902]})
    en_polo = artefactos.en_su_polo(maestro, bases)
    assert en_polo.set_index("codigo")["polo"].to_dict() == {10: 1, 11: 1, 20: 2, 21: 2, 70: 1, 71: -1}
    assert artefactos.en_su_polo(eventos, bases)["polo"].tolist() == [1, 2, -1]
    # Las tablas de tiempos ya vienen por polo: la parada del grupo 7 está entre las del 1.
    entre = pd.concat(
        [entre, pd.DataFrame({"polo": 1, "desde": [10, 70, 11, 70], "hasta": [70, 10, 70, 11], "minutos": 30.0})],
        ignore_index=True,
    ).fillna({"km": 9.0, "km_tren": 0.0, "km_bote": 0.0})
    desde_base = pd.concat(
        [desde_base, pd.DataFrame({"polo": [1], "codigo": [70], "minutos": [25.0], "km": [8.0]})], ignore_index=True
    ).fillna(0.0)
    puno, juli = artefactos.polos(
        en_polo, bases, clima, entre, desde_base, a_base, artefactos.en_su_polo(eventos, bases), origenes
    )
    assert (puno["id"], puno["nombre"], puno["paradas"]) == (1, "Puno", ["10", "11", "70"])
    assert puno["entre_minutos"][0] == [0.0, 120.0, 30.0] and puno["base_minutos"] == [153.2, 8.0, 25.0]
    assert puno["eventos"] == ["900"] and juli["eventos"] == ["901"]
    assert puno["recursos"] == 3 and juli["paradas"] == ["20", "21"]


def test_las_tablas_de_antes_de_juntar_no_cambian():
    maestro, bases, *_ = _tablas_de_dos_polos()
    assert artefactos.en_su_polo(maestro, bases)["polo"].tolist() == maestro["polo"].tolist()
