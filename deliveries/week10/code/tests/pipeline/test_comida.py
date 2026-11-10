"""Dónde comer cerca de cada lugar y de cada base (pipeline/comida.py, decisión 0019)."""

from pathlib import Path

import pandas as pd
import pytest

from pipeline import comida
from pipeline.maestro import PROCESADOS


def _overture(tmp_path: Path, filas) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    tabla = pa.table(
        {
            "confidence": [f[0] for f in filas],
            "basic_category": [f[1] for f in filas],
            "bbox": [{"xmin": f[3], "xmax": f[3], "ymin": f[2], "ymax": f[2]} for f in filas],
            "sources": [[{"dataset": "meta", "license": f[4]}] for f in filas],
        }
    )
    ruta = tmp_path / "lugares.parquet"
    pq.write_table(tabla, ruta)
    return ruta


def test_de_overture_solo_comida_confiable_y_con_licencia_cdla(tmp_path):
    cdla, apache = "CDLA-Permissive-2.0", "Apache-2.0"
    ruta = _overture(
        tmp_path,
        [
            (0.95, "restaurant", -13.51, -71.97, cdla),
            (0.80, "cafe", -13.52, -71.98, cdla),
            (0.75, "food_truck_stand", -13.53, -71.99, cdla),
            (0.65, "restaurant", -13.54, -71.97, cdla),  # poca confianza
            (0.95, "fast_food_restaurant", -13.55, -71.97, apache),  # otra licencia
            (0.95, "bar", -13.56, -71.97, cdla),  # de noche, no de comer
            (0.95, None, -13.57, -71.97, cdla),
        ],
    )
    lugares = comida.de_overture(ruta)
    assert list(lugares["lat"]) == [-13.51, -13.52, -13.53]


def test_cerca_cuenta_cada_fuente_y_mide_el_mas_cercano():
    puntos = pd.DataFrame({"lat": [-13.5, -13.6], "lon": [-71.9, -71.9]})
    osm = pd.DataFrame({"lat": [-13.5, -13.505, -13.6 + 0.02], "lon": [-71.9 + 0.003, -71.9, -71.9]})
    overture = pd.DataFrame({"lat": [-13.5 + 0.009], "lon": [-71.9]})
    cerca = comida.cerca(puntos, osm, overture)
    # El primero: dos de OSM (a ~325 m y ~555 m) y uno de Overture (a ~1 km). El segundo, a 2,2 km: nada.
    assert list(cerca["comida_osm"]) == [2, 0] and list(cerca["comida_overture"]) == [1, 0]
    assert 300 < cerca["mas_cerca_m"].iloc[0] < 350 and pd.isna(cerca["mas_cerca_m"].iloc[1])


TABLA = PROCESADOS / "comida_cerca.csv"


@pytest.mark.skipif(not TABLA.exists(), reason="sin data/procesados/comida_cerca.csv")
def test_la_tabla_publicada():
    tabla = pd.read_csv(TABLA, sep=";", encoding="utf-8-sig", dtype={"clave": str})
    assert set(tabla["tipo"]) == {"recurso", "base"}
    assert not tabla.duplicated(["tipo", "clave"]).any()
    con_comida = tabla["mas_cerca_m"].notna()
    # Hay una distancia si y solo si hay alguno cerca, y nunca pasa del radio.
    assert (con_comida == (tabla["comida_osm"] + tabla["comida_overture"] > 0)).all()
    assert (tabla.loc[con_comida, "mas_cerca_m"] <= comida.RADIO_M).all()
    bases = pd.read_csv(PROCESADOS / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    assert set(tabla.loc[tabla["tipo"] == "base", "clave"].astype(int)) == set(bases["polo"])
    # Las bases son pueblos: casi todas tienen dónde comer registrado.
    assert con_comida[tabla["tipo"] == "base"].mean() > 0.7
