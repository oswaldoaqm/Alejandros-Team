"""La altura de las bases según el modelo de elevación (decisión 0020): cómo se lee una tesela, la
ventana alrededor de cada base, su altura y cuál manda en los artefactos."""

import gzip
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline import elevacion

ADQUISICION = Path(__file__).resolve().parents[2] / "pipeline" / "adquisicion"


@pytest.fixture(scope="module")
def descarga():
    """descargar_elevacion.py, que se corre como script (importa _comun desde su carpeta)."""
    sys.path.insert(0, str(ADQUISICION))
    try:
        spec = importlib.util.spec_from_file_location("descargar_elevacion", ADQUISICION / "descargar_elevacion.py")
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        yield modulo
    finally:
        sys.path.remove(str(ADQUISICION))


def test_la_tesela_se_nombra_por_su_esquina_suroeste(descarga):
    assert descarga.tesela(-15.838, -71.091) == "S16/S16W072"  # Imata
    assert descarga.tesela(-3.5, -80.4) == "S04/S04W081"
    assert descarga.tesela(0.2, -75.5) == "N00/N00W076"


def test_una_tesela_se_lee_de_norte_a_sur_y_de_oeste_a_este(descarga):
    n = 5  # una tesela de juguete: la fila 0 es el borde norte
    m = np.arange(n * n, dtype=">i2").reshape(n, n)
    leida = descarga.grilla(gzip.compress(m.tobytes()))
    assert leida.shape == (n, n) and leida[0, 0] == 0 and leida[4, 4] == 24
    # La esquina noroeste de S16W072 es (-15, -72); la sureste, (-16, -71). Justo en el borde, el punto es
    # de la tesela de al lado, donde también está: el borde se repite.
    assert descarga.posicion(-15.0001, -71.9999, 3601) == (0, 0)
    assert descarga.posicion(-15.9999, -71.0001, 3601) == (3600, 3600)
    assert descarga.posicion(-15.5, -71.5, 3601) == (1800, 1800)
    assert descarga.posicion(-15.0, -71.5, 3601) == (3600, 1800)  # en S15W072, su borde sur


def test_lo_que_cae_fuera_de_la_tesela_va_sin_dato(descarga):
    m = np.full((7, 7), 100, dtype=np.int16)
    v = descarga.ventana(m, 0, 0, radio=2)
    assert v.shape == (5, 5)
    assert (v[:2, :] == descarga.SIN_DATO).all() and (v[:, :2] == descarga.SIN_DATO).all()
    assert (v[2:, 2:] == 100).all()


def test_la_altura_es_la_mediana_de_los_puntos_con_dato_cerca_de_la_base():
    v = np.full((21, 21), 9999, dtype=np.int16)  # lo lejano no cuenta
    v[8:13, 8:13] = 3000
    v[10, 10] = 3500  # un techo o una torre en el centro no la mueve
    v[8, 8] = elevacion.SIN_DATO
    assert elevacion.altura(v) == 3000
    assert elevacion.altura(np.full((21, 21), elevacion.SIN_DATO, dtype=np.int16)) is None


def _bases():
    return pd.DataFrame(
        {
            "polo": [1, 2, 3, 4],
            "base": ["Puno", "Picoy", "Imata", "Sin modelo"],
            "lat": [-15.84, -10.92, -15.838, -12.0],
            "lon": [-70.02, -76.73, -71.091, -75.0],
            "altitud_m": [3830.0, 2856.0, np.nan, np.nan],
            "altitud_fuente": ["osm", "recursos_a_2_km", np.nan, np.nan],
            "grupos": ["1", "2", "3", "4"],
        }
    )


def _dem():
    b = _bases()
    return pd.DataFrame(
        {"polo": b["polo"], "lat_dem": b["lat"], "lon_dem": b["lon"], "altitud_dem_m": [3849.0, 2993.0, 4449.0, None]}
    )


def test_la_tabla_dice_cuanto_difiere_cada_base_del_modelo():
    t = elevacion.tabla(_bases(), _dem())
    assert list(t["diferencia_m"].iloc[:2]) == [-19.0, -137.0]
    r = elevacion.resumen(t)
    assert (r["completadas"], r["reemplazadas"], r["sin_altura"]) == (1, 1, 1)
    assert r["diferencia_m"]["osm"]["max"] == 19.0


def test_se_niega_si_una_base_se_movio_desde_la_descarga():
    dem = _dem()
    dem.loc[0, "lat_dem"] -= 0.01
    with pytest.raises(ValueError, match=r"\[1\]"):
        elevacion.tabla(_bases(), dem)


def test_en_los_artefactos_la_de_osm_se_queda_y_en_las_demas_manda_el_modelo():
    b = elevacion.completar(_bases(), elevacion.tabla(_bases(), _dem()))
    assert list(b["altitud_m"].iloc[:3]) == [3830.0, 2993.0, 4449.0]
    assert list(b["altitud_fuente"].iloc[:3]) == ["osm", "terrain_tiles", "terrain_tiles"]
    assert pd.isna(b["altitud_m"].iloc[3])  # sin modelo, queda como estaba
    assert list(b["grupos"]) == ["1", "2", "3", "4"]  # lo demás de la tabla no cambia
