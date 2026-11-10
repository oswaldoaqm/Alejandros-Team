"""Los tiempos por tierra contra los de Cruz del Sur (semana 12): las rutas, cómo se clasifica cada una y que
los kilómetros del motor sean los de la empresa."""

import pytest

from dreemgo.motor import datos as artefactos
from evaluacion import buses


def test_las_rutas_de_la_empresa():
    rutas = buses.leer()
    assert len(rutas) == 29
    assert all(r.fuente.startswith("https://www.cruzdelsur.com.pe/pasajes/") for r in rutas)
    assert all(0 < r.empresa_min <= r.empresa_max for r in rutas)
    assert len({(r.origen, r.destino) for r in rutas}) == len(rutas)


@pytest.mark.parametrize(("minutos", "esperado"), [(400, "debajo"), (445, "dentro"), (510, "dentro"), (511, "encima")])
def test_donde_cae_el_motor(minutos, esperado):
    assert buses.donde(minutos, 445, 510) == esperado


@pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
def test_cada_ruta_tiene_camino_y_los_kilometros_son_los_de_la_empresa():
    datos = artefactos.cargar()
    filas = [buses.comparar(r, datos) for r in buses.leer()]
    resumen = buses.resumir(filas)
    assert resumen["dentro"] + resumen["debajo"] + resumen["encima"] == resumen["rutas"] == 29
    # La red sigue la carretera: ningún camino se aleja un 10 % de los kilómetros que publica la empresa.
    assert all(0.9 <= f["razon_km"] <= 1.1 for f in filas)
    de_noche = [f for f in filas if f["de_noche"]]
    assert de_noche and all(f["atraso_max"] >= f["atraso_min"] for f in de_noche)
