"""Clima por polo y mes, y el veredicto de temporada (TA-05 v2)."""

import json

import numpy as np
import pandas as pd
import pytest

from pipeline import clima


def _diario(lluvia_mm: float = 2.0, minima: float = 10.0, maxima: float = 20.0) -> pd.DataFrame:
    dias = pd.date_range(clima.INICIO, clima.FIN, freq="D")
    return pd.DataFrame(
        {
            "time": dias.strftime("%Y-%m-%d"),
            "precipitation_sum": np.where(dias.day % 2 == 0, lluvia_mm, 0.0),  # llueve los días pares
            "temperature_2m_min": minima,
            "temperature_2m_max": maxima,
        }
    )


def _crudo(tmp_path, polo: int, diario: pd.DataFrame, elevacion: float = 3000.0):
    ruta = tmp_path / f"polo_{polo}.json"
    datos = {"polo": polo, "open_meteo": {"elevation": elevacion, "daily": diario.to_dict("list")}}
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


def test_la_regla_de_dos_ejes():
    lluvia = pd.Series([300, 250, 200, 100, 40, 10, 5, 5, 20, 60, 120, 180], dtype=float)
    puesto, veredicto = clima.veredictos(lluvia)
    assert puesto.tolist() == [1, 2, 3, 6, 8, 10, 11, 11, 9, 7, 5, 4]
    assert veredicto[:3].tolist() == ["desaconsejado"] * 3  # los dos ejes
    assert veredicto[11] == "advertencia"  # 180 mm, pero no está entre los tres más lluviosos
    assert set(veredicto[3:11]) == {"viable"}


def test_la_selva_queda_con_advertencia_y_el_desierto_viable():
    _, selva = clima.veredictos(pd.Series([400, 380, 350] + [200] * 9, dtype=float))
    assert selva.tolist() == ["desaconsejado"] * 3 + ["advertencia"] * 9
    _, desierto = clima.veredictos(pd.Series([12, 10, 8] + [1] * 9, dtype=float))
    assert set(desierto) == {"viable"}  # sus meses "más lluviosos" no pasan de 50 mm


def test_promedios_del_mes_y_temperatura_a_la_altura_de_la_base():
    m = clima.clima_de_polo(7, _diario(), altitud_clima=3000.0, altitud_base=2000.0)
    enero = m.set_index("mes").loc[1]
    assert enero["lluvia_mm"] == pytest.approx(15 * 2.0)  # 15 días pares en enero
    assert enero["dias_con_lluvia"] == 15
    # 1 000 m más abajo: 6,5 °C más cálido.
    assert (enero["temp_min_c"], enero["temp_max_c"]) == pytest.approx((16.5, 26.5))
    assert (m["fuente"] == "open_meteo_polo").all() and len(m) == 12


def test_sin_altitud_de_la_base_no_se_ajusta():
    m = clima.clima_de_polo(7, _diario(), altitud_clima=3000.0, altitud_base=None)
    assert m["temp_min_c"].tolist() == pytest.approx([10.0] * 12)


def test_un_archivo_incompleto_no_se_usa(tmp_path):
    assert clima.leer_crudo(tmp_path / "polo_1.json") is None
    assert clima.leer_crudo(_crudo(tmp_path, 1, _diario().iloc[:-1])) is None
    diario, elevacion = clima.leer_crudo(_crudo(tmp_path, 2, _diario(), elevacion=812.0))
    assert len(diario) == clima.DIAS and elevacion == 812.0


def test_sin_descarga_usa_la_capa_regional(tmp_path):
    _crudo(tmp_path, 1, _diario())
    semana6 = pd.DataFrame(
        {
            "POLO": [2] * 12,
            "MES": [float(m) for m in range(1, 13)],
            "precip_mm": [160.0] + [10.0] * 11,
            "veredicto": ["desaconsejado"] + ["viable"] * 11,
        }
    )
    bases = pd.DataFrame({"polo": [1, 2], "altitud_m": [2000.0, np.nan]})
    tabla = clima.construir(bases, tmp_path, semana6)
    assert list(tabla.columns) == clima.COLUMNAS
    regional = tabla[tabla["polo"] == 2]
    assert (regional["fuente"] == "region_semana6").all()
    assert regional["veredicto"].iloc[0] == "desaconsejado"
    assert regional[["dias_con_lluvia", "temp_min_c", "temp_max_c"]].isna().all().all()  # la capa no los tenía
    assert (tabla.loc[tabla["polo"] == 1, "fuente"] == "open_meteo_polo").all()


def test_un_polo_que_junta_grupos_toma_el_clima_del_mas_grande_que_lo_tenga(tmp_path):
    _crudo(tmp_path, 9, _diario(lluvia_mm=8.0))
    _crudo(tmp_path, 3, _diario(lluvia_mm=1.0))
    semana6 = pd.DataFrame(
        {
            "POLO": [6] * 12 + [5] * 12,
            "MES": [float(m) for m in range(1, 13)] * 2,
            "precip_mm": [160.0] + [10.0] * 11 + [20.0] * 12,
            "veredicto": ["desaconsejado"] + ["viable"] * 23,
        }
    )
    # El polo 3 junta los grupos 7, 9 y 3, en ese orden de tamaño; el 5 junta el 6 y el 5.
    bases = pd.DataFrame({"polo": [3, 5], "altitud_m": [2000.0, 500.0], "grupos": ["7|9|3", "6|5"]})
    tabla = clima.construir(bases, tmp_path, semana6)
    assert sorted(tabla["polo"].unique()) == [3, 5] and len(tabla) == 24
    con_archivo = tabla[tabla["polo"] == 3].set_index("mes")
    # El grupo 7 es el más grande, pero no tiene archivo: vale el del 9, no el del 3.
    assert (con_archivo["fuente"] == "open_meteo_polo").all()
    assert con_archivo.loc[1, "lluvia_mm"] == pytest.approx(15 * 8.0)
    assert con_archivo.loc[1, "altitud_base_m"] == 2000.0
    # Ninguno de sus grupos tiene archivo: la capa regional del más grande, el 6, con el número del polo.
    regional = tabla[tabla["polo"] == 5].set_index("mes")
    assert (regional["fuente"] == "region_semana6").all()
    assert (regional.loc[1, "lluvia_mm"], regional.loc[1, "veredicto"]) == (160.0, "desaconsejado")


def test_los_grupos_de_un_polo():
    con, sin = pd.DataFrame({"polo": [3, 4], "grupos": ["5|9|3", "4"]}), pd.DataFrame({"polo": [7]})
    assert [clima.grupos_de(b) for b in con.itertuples()] == [[5, 9, 3], [4]]
    assert [clima.grupos_de(b) for b in sin.itertuples()] == [[7]]
