"""Dónde salir de noche cerca de cada base (pipeline/noche.py): qué entra de OpenStreetMap y de
Overture Maps, cómo se juntan y qué queda cerca."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline import noche
from pipeline.maestro import PROCESADOS


@pytest.mark.parametrize(
    "nombre, de_comer, es",
    [
        ("Peña Don Porfirio", False, True),
        ("La Peña", True, True),
        ("Sukay Peña Vip", False, True),
        ("Casa Zambrano Restaurante Peña Criolla", True, True),
        ("Recreo Peña turística el cangrejo", True, True),
        ("Restaurante - Cafeteria La Peña", True, False),  # un nombre y nada más
        ("Restaurante Merito de Peña", True, False),  # un apellido
        ("Alameda Sáenz Peña", False, False),
        ("Peña Blanca", False, True),  # sin categoría de noche no llega aquí: lo filtra quien llama
    ],
)
def test_una_pena_se_reconoce_por_su_nombre(nombre, de_comer, es):
    assert noche.es_pena(nombre, de_comer=de_comer) is es


@pytest.mark.parametrize(
    "nombre, no_es",
    [
        ("COAR Ica", True),  # un colegio
        ("Senati Jaen", True),
        ("Sauna El Edén", True),
        ("La 12 tu canchita sintetica", True),
        ("Techos Fibraforte", True),
        ("Catarata de santa carmen", True),
        ("Jr Alfonso Ugarte N 501 Tiendas Crown", True),
        ("𝘾𝙤𝙡𝙚𝙜𝙞𝙤 San José", True),  # letras de adorno: es «Colegio»
        ("Bar", True),  # solo dice qué es
        ("Resto Bar", True),
        ("Disco Teca", True),
        ("Señor de", True),  # cortado
        ("Bar Lima", False),
        ("Discoteca Bar Alcoholegio", False),  # «colegio» dentro de otra palabra
        ("Cafe Soprano's", False),
        ("Black Cat", False),
    ],
)
def test_lo_que_el_nombre_dice_que_no_es_de_noche(nombre, no_es):
    assert noche.no_es_de_noche(nombre) is no_es


@pytest.mark.parametrize(
    "nombre, dudoso",
    [
        ("Restaurante Valentino", True),
        ("Mamaica Grill Restaurante", True),
        ("𝙆𝙊𝙍𝙔'𝙨 𝙋𝘼𝙎𝘾𝙊 𝙋𝙤𝙡𝙡𝙤𝙨 𝙮 𝙋𝙖𝙧𝙧𝙞𝙡𝙡𝙖𝙨", True),
        ("Playa Barlovento", True),
        ("Santa Teresita", True),
        ("Jr Los Rosales 311 Tarapoto", True),
        ("Urb. Obando", True),
        ("Llahuar City", True),
        ("Lolita Restaurante - Bar", False),  # dice que es bar
        ("Pig Grill and Bar", False),
        ("Santo Bar", False),
        ("Cafe Tequila Chapas Corchos y Alitas", False),
        ("La Tarima Cafe Concert", False),
        ("VÉNIU Disco - Convenciones", False),
        ("Taj Mahal", False),  # no dice nada, pero tampoco es de otra cosa
    ],
)
def test_en_overture_un_nombre_de_restaurante_de_sitio_o_de_direccion_no_basta(nombre, dudoso):
    assert noche.dudoso_en_overture(nombre) is dudoso


def test_el_nombre_dice_si_es_de_noche():
    de_noche = (
        "ChimeneaBar",
        "Bunker_discotek_Tarma",
        "Palacekaraoke",
        "Edelmann Craftbeer Tasting Room",
        "Mar de Copas",
    )
    assert all(noche.dice_que_es_de_noche(n) for n in de_noche)
    assert not any(noche.dice_que_es_de_noche(n) for n in ("Barrio Urubamba", "Barlovento", "Taj Mahal", "Kibosh"))


def test_el_nombre_se_limpia_sin_cambiarlo():
    assert noche.limpio('RESTO-Bar chosita"') == "RESTO-Bar chosita"
    assert noche.limpio("BLU BAR") == "Blu Bar"
    assert noche.limpio("  Km.0   cusco ") == "Km.0 cusco"
    assert noche.limpio("PUB") == "PUB"  # las siglas cortas quedan


def test_dos_nombres_son_el_mismo_lugar_si_dicen_lo_mismo_y_estan_cerca():
    assert noche.mismo_lugar("Paddy's Irish Pub", "Paddys Irish Pub", 40)
    assert noche.mismo_lugar("Bar El Tambo", "El Tambo", 120)  # las palabras genéricas no cuentan
    assert not noche.mismo_lugar("Bar El Tambo", "El Tambo", 400)
    assert noche.mismo_lugar("Bonustrack Cocktails Music", "Bonustrack", 50)
    assert not noche.mismo_lugar("Bonustrack Cocktails Music", "Bonustrack", 100)
    assert not noche.mismo_lugar("La Chupitería", "La Fábrica", 10)


def _puntos(filas):
    return pd.DataFrame(filas, columns=["clave", "valor", "nombre", "lat", "lon", "osm", "horario", "altitud_m"])


def test_de_osm_toma_lo_de_la_noche_con_su_tipo():
    puntos = _puntos(
        [
            ("amenity", "bar", "Black Cat", -13.5, -71.9, "node/1", "Mo-Su 16:00-01:00", np.nan),
            ("amenity", "pub", "Paddy's", -13.5, -71.9, "way/2", "", np.nan),
            ("amenity", "nightclub", "Mama Africa", -13.5, -71.9, "node/3", "", np.nan),
            ("leisure", "dance", "Academia de Baile Sol", -13.5, -71.9, "node/4", "", np.nan),
            ("amenity", "restaurant", "Peña La Jarana", -12.1, -77.0, "node/5", "", np.nan),
            ("amenity", "restaurant", "Cafetería La Peña", -12.1, -77.0, "node/6", "", np.nan),
            ("amenity", "bar", "Licorería La Reina", -6.2, -77.8, "node/7", "", np.nan),
            ("amenity", "bar", "", -6.2, -77.8, "node/8", "", np.nan),
            ("tourism", "viewpoint", "Mirador", -6.2, -77.8, "node/9", "", np.nan),
            ("amenity", "bar", "La 12 tu canchita sintetica", -6.5, -76.4, "node/10", "", np.nan),
            ("amenity", "bar", "Bar", -6.5, -76.4, "node/11", "", np.nan),
            # Una persona lo marcó como bar: en OSM, «café» no basta para sacarlo.
            ("amenity", "bar", "Cafe Soprano's", -9.5, -77.5, "node/12", "", np.nan),
        ]
    )
    lugares = noche.de_osm(puntos)
    assert dict(zip(lugares["nombre"], lugares["tipo"], strict=True)) == {
        "Black Cat": "bar",
        "Paddy's": "pub",
        "Mama Africa": "discoteca",
        "Peña La Jarana": "pena",
        "Cafe Soprano's": "bar",
    }
    assert set(lugares["fuente"]) == {"osm"} and lugares["confianza"].isna().all()
    assert lugares.loc[lugares["nombre"] == "Black Cat", "horario"].item() == "Mo-Su 16:00-01:00"


def _overture(tmp_path: Path, filas) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    tabla = pa.table(
        {
            "id": [f[0] for f in filas],
            "confidence": [f[1] for f in filas],
            "names": [{"primary": f[2]} for f in filas],
            "taxonomy": [{"primary": f[3]} for f in filas],
            "bbox": [{"xmin": f[5], "xmax": f[5], "ymin": f[4], "ymax": f[4]} for f in filas],
            "sources": [[{"dataset": "meta", "license": f[6]}] for f in filas],
        }
    )
    ruta = tmp_path / "lugares.parquet"
    pq.write_table(tabla, ruta)
    return ruta


def test_de_overture_solo_lo_confiable_de_noche_y_con_licencia_cdla(tmp_path):
    cdla, apache = "CDLA-Permissive-2.0", "Apache-2.0"
    ruta = _overture(
        tmp_path,
        [
            ("a", 0.95, "Ukukus", "dance_club", -13.5, -71.9, cdla),
            ("b", 0.65, "Poco Confiable Bar", "bar", -13.5, -71.9, cdla),
            ("c", 0.90, "De Foursquare", "bar", -13.5, -71.9, apache),
            ("d", 0.90, "Lotengo Rent a Car", "karaoke_venue", -13.5, -71.9, cdla),
            ("e", 0.90, "Salón Princess Eventos", "music_venue", -13.5, -71.9, cdla),
            ("f", 0.90, "Peña Don Porfirio", "music_venue", -12.1, -77.0, cdla),
            ("g", 0.80, "Hanz", "beer_bar", -13.5, -71.9, cdla),
            ("h", 0.75, "Hanz", "beer_bar", -13.5001, -71.9, cdla),  # el mismo, a 11 m
        ],
    )
    lugares = noche.de_overture(ruta)
    assert dict(zip(lugares["nombre"], lugares["tipo"], strict=True)) == {
        "Ukukus": "discoteca",
        "Peña Don Porfirio": "pena",
        "Hanz": "pub",
    }
    assert len(lugares) == 4  # los dos Hanz se juntan después, con OSM: juntar() deja uno
    juntos = noche.juntar(noche.de_osm(_puntos([])), lugares)
    assert sorted(juntos["overture"]) == ["a", "f", "g"]


def test_juntar_deja_el_de_osm_con_la_confianza_de_overture():
    osm = noche.de_osm(_puntos([("amenity", "pub", "Paddy's Irish Pub", -13.51676, -71.97755, "way/2", "", np.nan)]))
    osm = pd.concat(
        [osm, noche.de_osm(_puntos([("amenity", "bar", "Sach'a restaurante", -16.4, -71.53, "node/3", "", np.nan)]))],
        ignore_index=True,
    )
    nombres = ["Paddy's Irish Pub", "Mama Africa", "Sach'a restaurante", "Restaurante Valentino"]
    overture = pd.DataFrame(
        {
            "nombre": nombres,
            "tipo": ["pub", "discoteca", "bar", "bar"],
            "lat": [-13.51680, -13.51700, -16.40002, -12.05],
            "lon": [-71.97760, -71.97800, -71.53, -77.03],
            "fuente": "overture",
            "osm": "",
            "overture": ["x1", "x2", "x3", "x4"],
            "confianza": [0.99, 0.9, 0.8, 0.9],
            "horario": "",
            "dudoso": [noche.dudoso_en_overture(n) for n in nombres],
        }
    )
    juntos = noche.juntar(osm, overture)
    # El restaurante de Overture solo no queda; el que confirma un bar de OSM le da su confianza.
    assert sorted(juntos["nombre"]) == ["Mama Africa", "Paddy's Irish Pub", "Sach'a restaurante"]
    assert "dudoso" not in juntos
    paddys = juntos[juntos["nombre"] == "Paddy's Irish Pub"].iloc[0]
    assert (paddys["fuente"], paddys["osm"], paddys["overture"], paddys["confianza"]) == ("osm", "way/2", "x1", 0.99)
    assert juntos.loc[juntos["nombre"] == "Sach'a restaurante", "overture"].item() == "x3"
    # En las dos fuentes va primero.
    assert list(juntos["nombre"])[:2] == ["Paddy's Irish Pub", "Sach'a restaurante"]


def test_cerca_de_cada_base_a_pie():
    lugares = pd.DataFrame(
        {
            "nombre": ["Bar Cerca", "Bar Lejos", "Al lado", "Taj Mahal"],
            "tipo": ["bar", "bar", "pub", "discoteca"],
            "lat": [-13.5100, -13.5300, -13.5000, -13.5010],
            "lon": [-72.0, -72.0, -72.0005, -72.0],
            "fuente": ["overture", "overture", "osm", "overture"],
            "osm": ["", "", "node/1", ""],
            "overture": ["a", "b", "", "c"],
            "confianza": [0.9, 0.95, np.nan, 0.95],
            "horario": "",
        }
    )
    bases = pd.DataFrame({"polo": [7], "lat": [-13.5], "lon": [-72.0]})
    cerca = noche.cerca_de_cada_base(lugares, bases)
    # 0,9 de confianza antes que 0,8 de OSM solo; y al final, el que no dice que sea de noche.
    assert list(cerca["nombre"]) == ["Bar Cerca", "Al lado", "Taj Mahal"]
    assert list(cerca["metros"]) == [1112, 54, 111]
    assert list(cerca["minutos_a_pie"]) == [20, 1, 2]
    assert set(cerca["polo"]) == {7}


TABLA = PROCESADOS / "noche_lugares.csv"


@pytest.mark.skipif(not TABLA.exists(), reason="sin data/procesados/noche_lugares.csv")
def test_la_tabla_publicada():
    tabla = pd.read_csv(TABLA, sep=";", encoding="utf-8-sig", keep_default_na=False)
    bases = pd.read_csv(PROCESADOS / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    assert set(tabla["polo"]) <= set(bases["polo"])
    assert set(tabla["tipo"]) <= set(noche.TIPO_OSM.values()) | set(noche.TIPO_OVERTURE.values()) | {"pena"}
    assert (tabla["metros"] <= noche.RADIO_M).all() and (tabla["minutos_a_pie"] <= 26).all()
    assert set(tabla["fuente"]) == {"osm", "overture"}
    assert (tabla.loc[tabla["fuente"] == "osm", "osm"] != "").all()
    # Ningún nombre trae un teléfono ni un correo.
    assert not tabla["nombre"].str.contains(r"\d{6,}|@", regex=True).any()
    # Nada de lo que no es de noche, ni de Overture solo con nombre de restaurante o de sitio.
    assert not tabla["nombre"].map(noche.no_es_de_noche).any()
    assert not tabla.loc[tabla["osm"] == "", "nombre"].map(noche.dudoso_en_overture).any()
    # Un lugar por nombre y polo, cerca.
    repetidos = tabla.assign(clave=tabla["nombre"].map(noche.palabras)).duplicated(["polo", "clave"], keep=False)
    assert repetidos.sum() <= 0.05 * len(tabla)  # sucursales con el mismo nombre a más de 300 m
