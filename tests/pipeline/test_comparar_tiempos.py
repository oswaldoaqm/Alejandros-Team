"""La comparación de dos corridas de pipeline.tiempos: qué empeora y si tiene explicación."""

import pandas as pd

from pipeline import comparar_tiempos


def _corrida(carpeta, bases, paradas, base_minutos, polo_minutos):
    carpeta.mkdir()

    def escribir(nombre, filas):
        pd.DataFrame(filas).to_csv(carpeta / nombre, sep=";", index=False, encoding="utf-8-sig")

    escribir("polos_bases.csv", bases)
    escribir("red_paradas.csv", paradas)
    escribir(
        "tiempos_base.csv", [{"polo": p, "codigo": c, "minutos": m, "km": 1.0} for (p, c), m in base_minutos.items()]
    )
    escribir(
        "tiempos_polo.csv",
        [{"polo": 1, "desde": d, "hasta": h, "minutos": m, "km": 1.0} for (d, h), m in polo_minutos.items()],
    )
    escribir("tiempos_origen_base.csv", [{"origen": "lima", "polo": 1, "minutos": 100.0, "km": 1.0}])
    escribir("tiempos_origen.csv", [{"origen": "lima", "codigo": 10, "minutos": 100.0, "km": 1.0}])


def test_explica_lo_que_empeora(tmp_path):
    paradas = [{"codigo": c, "polo": 1, "metros_a_la_red": 100} for c in (10, 11, 12)]
    antes, despues = tmp_path / "antes", tmp_path / "despues"
    _corrida(
        antes,
        [{"polo": 1, "base": "Pueblo"}, {"polo": 2, "base": "Otro"}],  # sin capa ni metros: una corrida vieja
        paradas,
        {(1, 10): 10.0, (1, 11): 10.0, (2, 12): 10.0},
        {(10, 11): 5.0, (11, 10): 5.0},
    )
    _corrida(
        despues,
        [
            {"polo": 1, "base": "Pueblo", "metros_a_la_red": 50, "capa": "vial"},
            {"polo": 2, "base": "Nuevo", "metros_a_la_red": 50, "capa": "vial"},
        ],
        [
            {**p, "capa": "bote", "metros_a_la_red": 300} if p["codigo"] == 11 else {**p, "capa": "vial"}
            for p in paradas
        ],
        {(1, 10): 30.0, (1, 11): 40.0, (2, 12): 50.0},
        {(10, 11): 5.0, (11, 10): None},
    )
    r = comparar_tiempos.comparar(antes, despues)
    base = r["tiempos_base.csv"].set_index("codigo")["explicacion"].to_dict()
    # 10 empeora sin que nada cambie de lugar; 11 se ubica ahora en un bote; el polo 2 cambió de base.
    assert base == {10: "", 11: "parada", 12: "base"}
    polo = r["tiempos_polo.csv"]
    assert len(polo) == 1 and polo.iloc[0]["explicacion"] == "parada"  # perdió el camino, con explicación
    resumen = r["resumen"].set_index("tabla")
    assert resumen.loc["tiempos_base.csv", "empeoran"] == 3
    assert resumen.loc["tiempos_polo.csv", "pierden_camino"] == 1
