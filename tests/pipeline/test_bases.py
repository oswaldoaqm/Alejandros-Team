"""La base de cada polo: decisiones puras, sin la red."""

import numpy as np
import pandas as pd
import pytest

from pipeline import bases

SIN_CAPITALES = pd.DataFrame(columns=["distrito", "capital", "lat", "lon"]).astype({"lat": float, "lon": float})
SIN_HOSPEDAJES = pd.DataFrame(columns=["tipo", "lat", "lon"]).astype({"lat": float, "lon": float})


def _lugares() -> pd.DataFrame:
    # Separados por 0,1° (11 km): ninguno queda dentro de otro.
    return pd.DataFrame(
        {
            "nombre": ["Paraje", "Caserío con capital", "Caserío", "Barrio", "Pueblo", "Ciudad"],
            "lat": [-12.5, -12.4, -12.3, -12.2, -12.1, -12.0],
            "lon": [-77.0] * 6,
            "rango": [4, 3, 3, 2, 1, 0],
            "altitud_m": [np.nan, np.nan, 3000.0, np.nan, np.nan, 100.0],
        }
    )


def test_candidatos_y_lo_que_suma_o_resta_su_hospedaje():
    capitales = pd.DataFrame({"distrito": ["X"], "capital": ["Caserío con capital"], "lat": [-12.4], "lon": [-77.0]})
    hospedajes = pd.DataFrame({"tipo": ["hotel"] * 3, "lat": [-12.301] * 3, "lon": [-77.0] * 3})  # a 110 m del caserío
    c = bases.candidatos(_lugares(), capitales, hospedajes)
    # Sin el paraje, y en orden estable: más grande primero; con hospedaje antes que sin él.
    assert c["nombre"].tolist() == ["Ciudad", "Pueblo", "Barrio", "Caserío", "Caserío con capital"]
    assert c["hospedajes_osm"].tolist() == [0, 0, 0, 3, 0]
    assert c["capital_de_distrito"].tolist() == [False, False, False, False, True]
    # Sin hospedaje: nada la ciudad, 15 el pueblo, el barrio y la capital; con 3, dos duplicaciones de bono.
    assert c["ajuste_min"].tolist() == pytest.approx([0, 15, 15, -10, 15])
    assert c["altitud_osm_m"].iloc[3] == 3000


def test_sin_hospedaje_un_caserio_paga_mas():
    c = bases.candidatos(_lugares(), SIN_CAPITALES, SIN_HOSPEDAJES).set_index("nombre")
    assert c.at["Caserío", "ajuste_min"] == bases.RECARGO_SIN_HOSPEDAJE_MIN[3]


def test_el_bono_por_hospedaje_tiene_tope():
    muchos = pd.DataFrame({"tipo": ["hotel"] * 500, "lat": [-12.0] * 500, "lon": [-77.0] * 500})
    c = bases.candidatos(_lugares(), SIN_CAPITALES, muchos).set_index("nombre")
    assert c.at["Ciudad", "ajuste_min"] == -bases.BONO_MAX_MIN


def test_un_barrio_junto_a_la_ciudad_es_la_ciudad():
    lugares = pd.concat(
        [
            _lugares(),
            pd.DataFrame(  # a 6,7 km de la ciudad y a 5,6 km del pueblo
                {"nombre": ["Barrio céntrico", "Caserío vecino"], "lat": [-12.06, -12.15], "lon": [-77.0, -77.0]}
            ).assign(rango=[2, 3], altitud_m=np.nan),
        ]
    )
    nombres = set(bases.candidatos(lugares, SIN_CAPITALES, SIN_HOSPEDAJES)["nombre"])
    assert "Barrio céntrico" not in nombres  # dentro de los 8 km de la ciudad
    assert "Caserío vecino" in nombres  # fuera de los 4 km del pueblo


def test_gana_la_que_deja_cerca_lo_que_mas_vale():
    peso = bases.pesos(pd.Series([4, None]))  # 1 + jerarquía; sin jerarquía pesa como 2,5
    assert peso.tolist() == [5.0, 2.5]
    minutos = np.array(
        [
            [10.0, 60.0],  # la parada de jerarquía 4 queda cerca del candidato 0
            [60.0, 10.0],  # la que no tiene jerarquía, del candidato 1
        ]
    )
    assert bases.elegir(minutos, peso, np.zeros(2)) == 0
    # Medias de 26,7 y 43,3 minutos: un recargo de 20 al primero da vuelta la elección.
    assert bases.costos(minutos, peso, np.zeros(2)) == pytest.approx([200 / 7.5, 325 / 7.5])
    assert bases.elegir(minutos, peso, np.array([20.0, 0.0])) == 1


def test_el_hospedaje_compensa_unos_minutos_y_no_mas():
    minutos, peso = np.array([[30.0, 45.0]]), np.ones(1)
    un_hostal, treinta = -bases.BONO_POR_DUPLICAR_MIN * 1, -bases.BONO_POR_DUPLICAR_MIN * np.log2(32)
    assert bases.elegir(minutos, peso, np.array([un_hostal, treinta])) == 1  # 15 minutos más, 31 hospedajes
    assert bases.elegir(np.array([[30.0, 55.0]]), peso, np.array([un_hostal, treinta])) == 0  # 25 más: no


def test_sin_camino_cuenta_como_diez_horas_y_sin_ninguno_no_hay_base():
    peso = np.ones(2)
    minutos = np.array([[30.0, np.inf], [np.inf, np.inf]])
    c = bases.costos(minutos, peso, np.zeros(2))
    assert c[0] == pytest.approx((30 + bases.SIN_CAMINO_MIN) / 2)
    assert np.isinf(c[1])
    assert bases.elegir(minutos, peso, np.zeros(2)) == 0
    assert bases.elegir(np.full((2, 2), np.inf), peso, np.zeros(2)) is None


def test_entre_iguales_gana_el_primero():
    assert bases.elegir(np.array([[10.0, 10.0]]), np.ones(1), np.zeros(2)) == 0


def test_en_linea_recta_si_no_hay_red():
    lat, lon = np.array([-13.0, -12.01]), np.array([-77.0, -77.0])
    assert bases.elegir_en_linea_recta([-12.0], [-77.0], np.ones(1), lat, lon, np.zeros(2)) == 1


def test_altitud_de_osm_o_de_los_recursos_del_pueblo():
    b = pd.DataFrame({"lat": [-12.0, -13.0, -14.0], "lon": [-77.0] * 3, "altitud_osm_m": [150.0, np.nan, np.nan]})
    recursos = pd.DataFrame(
        {"lat": [-13.001, -13.002, -13.003, -13.5], "lon": [-77.0] * 4, "altitud_m": [3000, 3100, 3500, 4000]}
    )
    altitud, fuente = bases.altitud(b, recursos)
    assert altitud.tolist()[:2] == [150, 3100]  # la mediana de los tres a menos de 2 km
    assert np.isnan(altitud.iloc[2])
    assert fuente.tolist() == ["osm", "recursos_a_2_km", ""]
