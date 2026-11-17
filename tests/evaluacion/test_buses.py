"""Los tiempos por tierra contra los de Cruz del Sur (semana 12): las rutas, cómo se clasifica cada una, que
los kilómetros del motor sean los de la empresa y que se comparen de terminal a terminal."""

import pytest

from dreemgo.motor import datos as artefactos
from evaluacion import buses


def test_las_rutas_de_la_empresa():
    rutas = buses.leer()
    assert len(rutas) == 29
    assert all(r.fuente.startswith("https://www.cruzdelsur.com.pe/pasajes/") for r in rutas)
    assert all(0 < r.empresa_min <= r.empresa_max for r in rutas)
    assert len({(r.origen, r.destino) for r in rutas}) == len(rutas)
    assert all(-18.5 < r.lat < 0 and -81.5 < r.lon < -68.5 for r in rutas)  # cada pueblo de llegada, en el Perú


@pytest.mark.parametrize(("minutos", "esperado"), [(400, "debajo"), (445, "dentro"), (510, "dentro"), (511, "encima")])
def test_donde_cae_el_motor(minutos, esperado):
    assert buses.donde(minutos, 445, 510) == esperado


@pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
def test_cada_ruta_tiene_camino_y_los_kilometros_son_los_de_la_empresa():
    datos = artefactos.cargar()
    filas = [buses.comparar(r, datos, buses.leer_terminales()) for r in buses.leer()]
    resumen = buses.resumir(filas)
    assert resumen["dentro"] + resumen["debajo"] + resumen["encima"] == resumen["rutas"] == 29
    # La red sigue la carretera: ningún camino se aleja un 10 % de los kilómetros que publica la empresa.
    assert all(0.9 <= f["razon_km"] <= 1.1 for f in filas)
    de_noche = [f for f in filas if f["de_noche"]]
    assert de_noche and all(f["atraso_max"] >= f["atraso_min"] for f in de_noche)
    # Cada ruta llega a una zona que duerme en ese pueblo, aunque las zonas cambien de número entre versiones.
    assert {datos.polos[buses.zona_de(r, datos)].base["nombre"] for r in buses.leer()} >= {"Lima", "Arequipa", "Cuzco"}


def test_los_terminales_son_los_del_pipeline():
    terminales = pytest.importorskip("pipeline.terminales")
    assert buses.EMBARQUE_MIN == terminales.EMBARQUE_MIN
    assert buses.BASE_TAXI_MAX_MIN == terminales.BASE_TAXI_MAX_MIN
    assert buses.IDA_EN_BUS_MIN == terminales.IDA_EN_BUS_MIN


def test_la_ida_larga_se_compara_sin_los_taxis_ni_el_embarque():
    t = buses.Terminales({"lima": (20.0, 4.0)}, {7: (10.0, 2.0)})
    assert t.de_la_ida("lima", 7, 600.0) == (50.0, 10.0, 6.0)  # taxi y embarque; taxi a la base; km de taxi
    assert t.de_la_ida("lima", 7, 150.0) == (0.0, 0.0, 0.0)  # una ida corta no los sumaba
    assert t.de_la_ida("lima", 8, 600.0) == (50.0, 0.0, 4.0)  # una base sin terminal cerca no suma el último taxi
