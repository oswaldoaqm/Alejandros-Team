"""La comparación de dos corridas de pipeline.tiempos: qué empeora y si tiene explicación."""

import pandas as pd

from pipeline import comparar_tiempos


def _corrida(carpeta, bases, paradas, base_minutos, polo_minutos, origen_base=None):
    """``polo_minutos``: (desde, hasta) → minutos, en el polo 1, o (polo, desde, hasta) → minutos."""
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
        [
            {"polo": par[-3] if len(par) == 3 else 1, "desde": par[-2], "hasta": par[-1], "minutos": m, "km": 1.0}
            for par, m in polo_minutos.items()
        ],
    )
    escribir(
        "tiempos_origen_base.csv",
        [{"origen": "lima", "polo": p, "minutos": m, "km": 1.0} for p, m in (origen_base or {1: 100.0}).items()],
    )
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


def test_compara_aunque_dos_grupos_pasen_a_ser_un_polo(tmp_path):
    """Los grupos 1 y 2 dormían en Pueblo; en la corrida nueva son el polo 1, y el 3 duerme en otro lugar."""
    paradas = [{"codigo": c, "polo": p, "metros_a_la_red": 100, "capa": "vial"} for c, p in ((10, 1), (12, 2), (13, 3))]
    en = {"metros_a_la_red": 50, "capa": "vial"}
    antes, despues = tmp_path / "antes", tmp_path / "despues"
    _corrida(
        antes,
        [{"polo": 1, "base": "Pueblo", **en}, {"polo": 2, "base": "Pueblo", **en}, {"polo": 3, "base": "Villa", **en}],
        paradas,
        {(1, 10): 10.0, (2, 12): 20.0, (3, 13): 30.0},
        {(1, 10, 11): 5.0, (2, 12, 14): 6.0},
        origen_base={1: 100.0, 2: 100.0, 3: 200.0},
    )
    _corrida(
        despues,
        [{"polo": 1, "base": "Pueblo", **en, "grupos": "1|2"}, {"polo": 3, "base": "Aldea", **en, "grupos": "3"}],
        [{**p, "polo": 1} if p["polo"] == 2 else p for p in paradas],
        {(1, 10): 10.0, (1, 12): 25.0, (3, 13): 45.0},
        {(1, 10, 11): 5.0, (1, 12, 14): 6.0, (1, 10, 12): 40.0, (1, 12, 10): 40.0},
        origen_base={1: 100.0, 3: 230.0},
    )
    r = comparar_tiempos.comparar(antes, despues)
    resumen = r["resumen"].set_index("tabla")
    # Entre paradas: los dos pares de antes siguen igual y los dos entre los grupos son nuevos, no «ganan camino».
    assert r["tiempos_polo.csv"].empty
    assert resumen.loc["tiempos_polo.csv", ["pares", "nuevos", "ganan_camino", "pierden_camino"]].tolist() == [
        2,
        2,
        0,
        0,
    ]
    # Desde la base: la parada del grupo 2 se compara aunque su polo ahora sea el 1, y empeora sin explicación
    # (la base es la misma); la del 3 empeora porque su base es otro pueblo.
    base = r["tiempos_base.csv"].set_index("codigo")
    assert base["explicacion"].to_dict() == {12: "", 13: "base"}
    assert (base.loc[12, "polo_antes"], base.loc[12, "polo_despues"], base.loc[12, "diferencia"]) == (2, 1, 5.0)
    assert resumen.loc["tiempos_base.csv", ["pares", "empeoran", "pierden_camino", "nuevos"]].tolist() == [3, 2, 0, 0]
    # Del origen a la base, por grupo: tres antes y tres después, aunque después haya dos polos.
    origen = r["tiempos_origen_base.csv"]
    assert resumen.loc["tiempos_origen_base.csv", ["pares", "empeoran", "nuevos"]].tolist() == [3, 1, 0]
    assert origen[["grupo", "polo_antes", "polo_despues", "explicacion"]].values.tolist() == [[3, 3, 3, "base"]]


def test_un_par_que_ya_no_esta_cuenta_como_que_pierde_su_camino(tmp_path):
    paradas = [{"codigo": c, "polo": 1, "metros_a_la_red": 100, "capa": "vial"} for c in (10, 11)]
    bases = [{"polo": 1, "base": "Pueblo", "metros_a_la_red": 50, "capa": "vial"}]
    antes, despues = tmp_path / "antes", tmp_path / "despues"
    _corrida(antes, bases, paradas, {(1, 10): 10.0, (1, 11): 10.0}, {(10, 11): 5.0})
    _corrida(despues, bases, paradas[:1], {(1, 10): 10.0}, {(10, 13): 7.0})
    r = comparar_tiempos.comparar(antes, despues)
    assert r["tiempos_base.csv"]["codigo"].tolist() == [11] and r["tiempos_base.csv"]["explicacion"].tolist() == [""]
    polo = r["resumen"].set_index("tabla").loc["tiempos_polo.csv"]
    assert polo[["pares", "pierden_camino", "nuevos", "ganan_camino"]].tolist() == [1, 1, 1, 0]
    assert r["tiempos_polo.csv"][["desde", "hasta"]].values.tolist() == [[10, 11]]
