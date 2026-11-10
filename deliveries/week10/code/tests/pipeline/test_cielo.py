"""Desde dónde y en qué meses se ven las estrellas (pipeline/cielo.py): el brillo del cielo con el
modelo de Duriscoe et al. (2018), las noches despejadas de GOES-16 y de los METAR, y lo que queda
para cada polo."""

import csv
import gzip

import numpy as np
import pandas as pd
import pytest

from pipeline import cielo
from pipeline.maestro import PROCESADOS


def test_el_nucleo_baja_con_la_distancia_y_se_corta_a_300_km():
    k = cielo.nucleo(0.9, 0.9)
    centro = (k.shape[0] // 2, k.shape[1] // 2)
    fila = k[centro[0], centro[1] :]
    assert np.all(np.diff(fila[fila > 0]) < 0)
    assert np.allclose(k, k[::-1, ::-1])  # simétrico
    # d^−α con α = 2,3·(d/350)^0,28: a 10 km y a 100 km, por el área de la celda frente a la del modelo.
    area = 0.9 * 0.9 / cielo.CELDA_DEL_MODELO_KM2
    for d in (10, 100):
        i = int(round(d / 0.9))
        dist = i * 0.9
        assert fila[i] == pytest.approx(dist ** -(2.3 * (dist / 350) ** 0.28) * area)
    assert fila[int(299 / 0.9)] > 0 and fila[-1] == 0 and k[0, 0] == 0  # a más de 300 km, nada


def _meses(tmp_path, radiancias):
    rutas = []
    for i, r in enumerate(radiancias):
        ruta = tmp_path / f"m{i}.npz"
        t = np.array([1 / 240, 0.0, -75.0, 0.0, -1 / 240, -10.0])  # 15″, esquina en 75° O y 10° S
        np.savez_compressed(
            ruta, radiancia=r.astype(np.float32), noches=np.full(r.shape, 9, np.uint16), transformacion=t
        )
        rutas.append(ruta)
    return rutas


def test_una_ciudad_ilumina_su_cielo_y_mucho_menos_el_de_lejos(tmp_path):
    forma = (720, 720)  # 3° de lado
    ciudad = np.zeros(forma)
    ciudad[355:365, 355:365] = 60.0  # unos 4,6 km de lado, como una ciudad mediana
    ruido = np.full(forma, 0.4)  # debajo de 0,5: el resplandor del aire, que no cuenta
    alr, t = cielo.brillo_del_cielo(_meses(tmp_path, [ciudad + ruido, ciudad + ruido, ciudad]))
    lat0, lon0 = -10.0 - 360 / 240, -75.0 + 360 / 240
    en_la_ciudad = cielo.brillo_en(alr, t, [lat0], [lon0])[0]
    a_100_km = cielo.brillo_en(alr, t, [lat0], [lon0 + 100 / 110])[0]
    assert cielo.clase(en_la_ciudad) == "con_luz"
    assert en_la_ciudad > 10 * a_100_km > 0
    assert cielo.clase(a_100_km) == "muy_oscuro"
    # Sin la ciudad, el ruido solo no da luz.
    oscuro, _ = cielo.brillo_del_cielo(_meses(tmp_path, [ruido, ruido]))
    assert oscuro.max() < 1e-6


def test_las_clases_son_las_del_servicio_de_parques():
    assert [cielo.clase(x) for x in (0.1, 0.3, 1.9, 2.0, 50)] == [
        "muy_oscuro",
        "oscuro",
        "oscuro",
        "con_luz",
        "con_luz",
    ]


def test_la_rejilla_de_goes_tiene_su_centro_bajo_el_satelite():
    fila, columna = cielo.en_la_rejilla_de_goes(0.0, -75.0)
    assert fila == pytest.approx(2711.5, abs=0.5) and columna == pytest.approx(2711.5, abs=0.5)
    # El Perú cae dentro de la ventana que baja descargar_nubes.py.
    for lat, lon in [(-0.1, -75.2), (-18.3, -70.4), (-4.6, -81.3), (-11.2, -68.7)]:
        f, c = cielo.en_la_rejilla_de_goes(lat, lon)
        assert 2681 < f < 3711 and 2344 < c < 3079


def _metar(tmp_path, filas):
    ruta = tmp_path / "2024" / "84628099999.csv.gz"
    ruta.parent.mkdir(parents=True)
    with gzip.open(ruta, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "STATION", "NAME", "LATITUDE", "LONGITUDE", "ELEVATION", "METAR"])
        for fecha, texto in filas:
            w.writerow([fecha, "84628099999", "JORGE CHAVEZ INTERNATIONAL, PE", "-12.02", "-77.11", "34", texto])
    return tmp_path


def test_un_metar_despejado_es_sin_nubes_o_con_pocas(tmp_path):
    directorio = _metar(
        tmp_path,
        [
            ("2024-07-01T02:00:00", "METAR SPJC 010200Z 16012KT CAVOK 17/14 Q1014"),
            ("2024-07-01T06:00:00", "METAR SPJC 010600Z 17008KT 9999 FEW013 16/14 Q1013"),
            ("2024-07-02T02:00:00", "METAR SPJC 020200Z 17008KT 9999 SCT012 16/14 Q1013"),
            ("2024-07-02T06:00:00", "METAR SPJC 020600Z 17008KT 6000 BKN008 16/14 Q1013"),
            ("2024-07-03T01:52:00", "SPECI SPJC 030152Z 00000KT 0400 FG VV002 15/15 Q1013"),
            ("2024-07-03T02:00:00", "METAR SPJC 030200Z 00000KT 0400 FG OVC002 15/15 Q1013"),
            ("2024-07-03T06:00:00", "METAR SPJC 030600Z 18005KT 9999 15/13 Q1013"),  # sin nubes dichas: no cuenta
            ("2024-07-04T03:00:00", "METAR SPJC 040300Z 18005KT CAVOK 15/13 Q1013"),  # otra hora
        ],
    )
    obs = cielo.leer_metar(directorio).sort_values(["mes", "hora"])
    assert len(obs) == 5
    vistas = {(int(o.hora), bool(o.despejado)) for o in obs.itertuples()}
    assert vistas == {(2, True), (6, True), (2, False), (6, False)}
    # Del 3, a las 02:00 cuenta la de las 02:00 en punto, la más cercana: nublada.
    assert sum(1 for o in obs.itertuples() if o.hora == 2 and not o.despejado) == 2


def test_en_la_costa_las_noches_despejadas_son_las_del_aeropuerto():
    class Satelite:
        def despejadas(self, lat, lon):
            return [0.5] * 12

    en_costa = pd.DataFrame(
        [{"nombre": "Lima", "lat": -12.02, "lon": -77.11, **{f"despejadas_{m}": m / 100 for m in range(1, 13)}}]
    )
    partes, fuente, aeropuerto = cielo.despejadas(-12.12, -77.03, 90.0, 3.0, Satelite(), en_costa)
    assert (fuente, aeropuerto, partes[6]) == ("metar", "Lima", 0.07)
    # En la costa, sin aeropuerto a menos de 150 km: no hay dato.
    assert cielo.despejadas(-14.83, -74.94, 590.0, 48.0, Satelite(), en_costa) == ([None] * 12, "", "")
    # Lejos del mar, o alto, el satélite.
    assert cielo.despejadas(-13.52, -71.98, 3400.0, 340.0, Satelite(), en_costa)[1] == "goes"
    assert cielo.despejadas(-12.4, -76.5, 2600.0, 60.0, Satelite(), en_costa)[1] == "goes"


def test_un_observatorio_que_no_mira_el_cielo_no_es_de_estrellas():
    puntos = pd.DataFrame(
        {
            "clave": ["man_made", "man_made", "amenity", "tourism", "man_made"],
            "valor": ["observatory", "observatory", "planetarium", "viewpoint", "observatory"],
            "nombre": [
                "Observatorio Vulcanológico del Sur",
                "Observatorio Discovery",
                "Planetarium Cusco",
                "",
                "Mirador Moche",
            ],
            "lat": [0.0] * 5,
            "lon": [0.0] * 5,
            "osm": [f"node/{i}" for i in range(5)],
            "horario": [""] * 5,
            "altitud_m": [np.nan] * 5,
        }
    )
    c = cielo.candidatos(puntos)
    assert list(c["nombre"]) == [
        "Observatorio Vulcanológico del Sur",
        "Observatorio Discovery",
        "Planetarium Cusco",
        "Mirador Moche",
    ]
    assert list(c["tipo"]) == ["observatorio", "observatorio", "planetario", "mirador"]
    assert list(c["astronomia"]) == [False, True, True, False]


TABLA = PROCESADOS / "cielo_polos.csv"
VALIDACION = PROCESADOS / "cielo_validacion.csv"


@pytest.mark.skipif(not TABLA.exists(), reason="sin data/procesados/cielo_polos.csv")
def test_la_tabla_publicada():
    tabla = pd.read_csv(TABLA, sep=";", encoding="utf-8-sig")
    bases = pd.read_csv(PROCESADOS / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    assert sorted(tabla["polo"]) == sorted(bases["polo"])
    despejadas = tabla[[f"despejadas_{m}" for m in range(1, 13)]]
    assert ((despejadas >= 0) & (despejadas <= 1) | despejadas.isna()).all().all()
    assert (despejadas.isna().all(axis=1) == tabla["nubes"].isna()).all()
    # Fuera de la base, solo con luz en la base, y más oscuro que ella.
    fuera = tabla[tabla["oscuro_nombre"].notna()]
    assert (fuera["brillo_base"] >= cielo.OSCURO).all()
    assert (fuera["oscuro_brillo"] < cielo.OSCURO).all() and (fuera["oscuro_minutos"] <= cielo.LEJOS_MIN).all()
    assert (tabla["astro_minutos"].dropna() <= cielo.LEJOS_MIN).all()
    cusco = tabla[tabla["polo"] == bases.loc[bases["base"] == "Cuzco", "polo"].item()].iloc[0]
    assert cielo.clase(cusco["brillo_base"]) == "con_luz" and cusco["astro_nombre"] == "Planetarium Cusco"
    assert cusco["despejadas_7"] > 0.8 > 0.2 > cusco["despejadas_2"]  # el invierno seco, el verano de lluvias


@pytest.mark.skipif(not VALIDACION.exists(), reason="sin data/procesados/cielo_validacion.csv")
def test_goes_coincide_con_los_metar_fuera_de_la_costa_y_no_en_ella():
    v = pd.read_csv(VALIDACION, sep=";", encoding="utf-8-sig").set_index("nombre")
    for sierra in ("Cusco", "Arequipa"):
        assert v.at[sierra, "r"] >= 0.95 and not v.at[sierra, "en_la_costa"]
    # En la costa no: por eso ahí se usan los METAR.
    for costa in ("Lima", "Pisco", "Tacna"):
        assert v.at[costa, "en_la_costa"] and v.at[costa, "r"] < 0
