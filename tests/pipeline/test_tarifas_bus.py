"""La banda del bus cubre la tarifa más baja de Cruz del Sur en sus 18 rutas desde Lima (decisión 0032)."""

import pandas as pd

from pipeline.maestro import REFERENCIA


def test_cada_tarifa_de_cruz_del_sur_cae_dentro_de_la_banda_del_bus():
    costos = pd.read_csv(REFERENCIA / "costos.csv", sep=";").set_index("parametro")
    tarifas = pd.read_csv(REFERENCIA / "tarifas_bus.csv", sep=";")
    assert len(tarifas) == 18 and tarifas["fuente"].str.startswith("https://www.cruzdelsur.com.pe/").all()
    i, k = costos.loc["bus_intercepto"], costos.loc["bus_soles_km"]
    minimo = i["minimo"] + k["minimo"] * tarifas["km"]
    maximo = i["maximo"] + k["maximo"] * tarifas["km"]
    assert ((tarifas["desde_soles"] >= minimo) & (tarifas["desde_soles"] <= maximo)).all()
    # Cruz del Sur es la empresa cara: su tarifa más baja queda siempre sobre el valor central.
    central = i["valor"] + k["valor"] * tarifas["km"]
    assert (tarifas["desde_soles"] > central).all()
