"""La altura del terreno alrededor de cada base (decisión 0020): cómo se nombra y se lee una tesela, y la
ventana que se guarda alrededor de cada base."""

import gzip
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

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
