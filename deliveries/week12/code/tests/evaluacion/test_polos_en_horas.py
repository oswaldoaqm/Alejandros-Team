"""TA-01 v3 (semana 12): el diámetro de cada grupo, el enlace completo con su umbral en minutos y la comparación
de dos particiones. Sin la red vial: la red queda fuera de git y la prueba usa matrices de juguete."""

import numpy as np
import pandas as pd
import pytest

from evaluacion import polos_en_horas as ph

INF = np.inf


def _simetrica(m):
    m = np.array(m, dtype=float)
    return np.maximum(m, m.T)


def test_el_diametro_es_el_viaje_mas_largo_entre_dos_paradas_del_grupo():
    minutos = _simetrica(
        [
            [0, 30, 90, INF],
            [0, 0, 70, 20],
            [0, 0, 0, 50],
            [0, 0, 0, 0],
        ]
    )
    tabla = ph.diametros(minutos, np.array([0, 0, 0, 1]))
    fila = tabla.set_index("grupo").loc[0]
    assert fila["paradas"] == 3 and fila["diametro_min"] == 90 and fila["pares_sin_camino"] == 0
    # Un grupo con un par sin camino: el diámetro es el de los pares con camino, y el par se cuenta aparte.
    tabla = ph.diametros(minutos, np.array([0, 0, 0, 0]))
    assert tabla.iloc[0]["diametro_min"] == 90 and tabla.iloc[0]["pares_sin_camino"] == 1


def test_ningun_grupo_pasa_del_umbral_y_un_par_sin_camino_nunca_queda_junto():
    rng = np.random.default_rng(7)
    puntos = rng.uniform(0, 400, size=(60, 2))
    minutos = np.hypot(*(puntos[:, None, :] - puntos[None, :, :]).transpose(2, 0, 1))
    minutos[3, 4] = minutos[4, 3] = INF  # dos paradas cercanas, pero sin camino entre ellas
    grupo = ph.agrupar(minutos, umbral=120, paradas_min=2)
    assert grupo[3] < 0 or grupo[3] != grupo[4]
    for g in np.unique(grupo[grupo >= 0]):
        i = np.flatnonzero(grupo == g)
        assert len(i) >= 2
        assert minutos[np.ix_(i, i)].max() <= 120
    # Los grupos van del más grande al más chico.
    tamanos = [int((grupo == g).sum()) for g in range(grupo.max() + 1)]
    assert tamanos == sorted(tamanos, reverse=True)


def test_un_grupo_de_menos_paradas_que_el_minimo_no_es_un_grupo():
    minutos = _simetrica([[0, 10, 500], [0, 0, 500], [0, 0, 0]])
    assert list(ph.agrupar(minutos, umbral=60, paradas_min=2)) == [0, 0, -1]
    assert list(ph.agrupar(minutos, umbral=60, paradas_min=3)) == [-1, -1, -1]


def test_dos_particiones_iguales_y_una_que_parte_un_grupo():
    v2 = np.array([0, 0, 0, 1, 1, -1])
    iguales = ph.comparar(v2, np.array([5, 5, 5, 2, 2, -1]))
    assert iguales["ari"] == pytest.approx(1.0)
    assert iguales["grupos_de_la_v2_que_se_parten"] == 0
    parte = ph.comparar(v2, np.array([0, 0, 1, 2, 2, 3]))
    assert parte["grupos_de_la_v2_que_se_parten"] == 1
    assert parte["pares_juntos_en_la_v2_que_siguen_juntos"] == pytest.approx(2 / 4)
    assert parte["sin_grupo_en_la_v2_y_en_la_v3"] == 1


def test_el_diametro_con_los_tiempos_del_motor_cuenta_cada_par_una_vez():
    tiempos = pd.DataFrame(
        {
            "polo": [0] * 6,
            "desde": [1, 2, 1, 3, 2, 3],
            "hasta": [2, 1, 3, 1, 3, 2],
            "minutos": [30.0, 30.0, 250.0, 250.0, np.nan, np.nan],
        }
    )
    grupo_de = pd.Series({1: 7, 2: 7, 3: 7, 4: 8, 5: -1})
    tabla = ph.diametros_del_motor(tiempos, grupo_de).set_index("grupo")
    assert tabla.loc[7, "paradas"] == 3 and tabla.loc[7, "diametro_min"] == 250
    assert tabla.loc[7, "pares_sin_camino"] == 1  # el par 2-3, que el archivo trae dos veces
    # Un grupo de una sola parada mide cero, y lo que no tiene grupo no cuenta.
    assert tabla.loc[8, "paradas"] == 1 and tabla.loc[8, "diametro_min"] == 0
    assert list(tabla.index) == [7, 8]


def test_con_tope_de_desnivel_no_quedan_juntas_dos_paradas_muy_distintas_en_altura():
    minutos = _simetrica([[0, 20, 30], [0, 0, 25], [0, 0, 0]])
    altitud = np.array([100.0, 3800.0, np.nan])
    assert list(ph.agrupar(minutos, umbral=60, paradas_min=2)) == [0, 0, 0]
    con_tope = ph.agrupar(minutos, umbral=60, paradas_min=2, altitud=altitud, desnivel_max=1300)
    # La de 100 m y la de 3 800 m no van juntas; la que no tiene altura puede ir con cualquiera.
    assert con_tope[0] != con_tope[1] or con_tope[0] < 0
    assert (con_tope >= 0).sum() == 2 and con_tope[2] >= 0
