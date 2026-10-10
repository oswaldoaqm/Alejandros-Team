"""La foto de cada lugar y de cada base: decisiones puras, sin la red."""

import csv
import json

import pytest

from pipeline import fotos
from pipeline.fotos import Nombre

TIPOS = {
    "Q515": {"en": "city", "es": "ciudad"},
    "Q2179958": {"en": "district of Peru", "es": "distrito del Perú"},
    "Q16970": {"en": "church building", "es": "iglesia"},
    "Q839954": {"en": "archaeological site", "es": "yacimiento arqueológico"},
    "Q174782": {"en": "square", "es": "plaza"},
}


def elemento(qid, nombre, lat, lon, tipos=(), imagenes=("Foto.jpg",), otros=(), enlaces=0):
    return {
        "qid": qid,
        "nombre": nombre,
        "nombre_en": "",
        "otros": list(otros),
        "lat": lat,
        "lon": lon,
        "imagenes": list(imagenes),
        "tipos": list(tipos),
        "enlaces": enlaces,
    }


def recurso(codigo, nombre, lat=-12.0, lon=-75.0, tipo="Sitios Arqueológicos", subtipo=""):
    return {"codigo": codigo, "nombre": nombre, "lat": lat, "lon": lon, "tipo": tipo, "subtipo": subtipo}


def meta(ancho=2000, alto=1500, licencia="CC BY-SA 4.0", autor="Autora", tipo="image/jpeg"):
    return {"ancho": ancho, "alto": alto, "licencia": licencia, "autor": autor, "tipo": tipo, "url_licencia": "u"}


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Wariwillka", "Huarihuilca"),
        ("Qorikancha", "Coricancha"),
        ("Kuélap", "Cuélap"),
        ("Sacsayhuamán", "Saqsaywaman"),
        ("Jauja", "Xauxa"),
        ("Ollantaytambo", "Ollantaitambo"),
    ],
)
def test_las_grafias_del_quechua_y_del_castellano_quedan_iguales(a, b):
    assert fotos.palabras(a) == fotos.palabras(b)


def test_la_ch_no_se_pierde():
    assert fotos.palabras("Quechua") == ["kechua"]
    assert fotos.palabras("Huanchaco") == ["wanchako"]


def test_lo_que_distingue_y_la_clase():
    n = Nombre.de("Santuario Arqueológico de Wariwillka")
    assert n.propias == ("wariwilka",)
    assert "religioso" in n.familias and "arqueologico" in n.familias
    assert Nombre.de("Plaza de Armas").propias == ()
    # El plural de una palabra de clase también es clase.
    assert Nombre.de("Huacas del Sol y la Luna").propias == ("sol", "luna")


def test_cobertura_y_familias():
    assert fotos.cobertura(Nombre.de("Convento de Santa Rosa de Ocopa"), Nombre.de("Convento de Ocopa")) == 0.5
    assert not fotos.compatibles(Nombre.de("Plaza de Armas de Huancayo"), Nombre.de("Catedral de Huancayo"))
    assert fotos.compatibles(Nombre.de("Capilla de la Merced"), Nombre.de("Iglesia de la Merced"))
    assert fotos.compatibles(Nombre.de("Wariwillka"), Nombre.de("Templo de Huarivilca"))


def test_un_lugar_toma_al_elemento_que_se_llama_como_el_y_esta_cerca():
    r = recurso("1", "Santuario Arqueológico de Wariwillka")
    cerca = elemento("Q1", "Huarihuilca", -12.01, -75.0, tipos=["Q839954"])  # a 1,1 km
    lejos = elemento("Q2", "Huarihuilca", -12.05, -75.0)  # a 5,6 km
    otro = elemento("Q3", "Iglesia de Huancán", -12.0, -75.0)
    assert [e["qid"] for e in fotos.candidatos_del_lugar(r, [lejos, otro, cerca], TIPOS)] == ["Q1"]


def test_con_la_mitad_del_nombre_tiene_que_estar_mas_cerca():
    r = recurso("1", "Convento de Santa Rosa de Ocopa")
    a_800_m = elemento("Q1", "Convento de Ocopa", -12.0072, -75.0)
    a_2_km = elemento("Q2", "Convento de Ocopa", -12.018, -75.0)
    assert [e["qid"] for e in fotos.candidatos_del_lugar(r, [a_800_m, a_2_km], TIPOS)] == ["Q1"]


def test_un_nombre_de_pura_clase_exige_estar_ahi_mismo():
    r = recurso("1", "Plaza de Armas", tipo="Arquitectura y Espacios Urbanos", subtipo="Plazas")
    ahi = elemento("Q1", "Plaza de Armas de Concepción", -12.002, -75.0, tipos=["Q174782"])  # 220 m
    a_un_km = elemento("Q2", "Plaza de Armas de Matahuasi", -12.009, -75.0, tipos=["Q174782"])
    iglesia = elemento("Q3", "Iglesia de Concepción", -12.0, -75.0, tipos=["Q16970"])
    assert [e["qid"] for e in fotos.candidatos_del_lugar(r, [a_un_km, iglesia, ahi], TIPOS)] == ["Q1"]


def test_un_pueblo_no_es_la_foto_de_un_lugar_salvo_que_el_lugar_sea_el_pueblo():
    ciudad = elemento("Q1", "Huancayo", -12.0, -75.0, tipos=["Q515"])
    distrito = elemento("Q2", "Distrito de Huancayo", -12.0, -75.0, tipos=["Q2179958"])
    catedral = recurso("1", "Catedral de Huancayo", tipo="Arquitectura y Espacios Urbanos", subtipo="Iglesias")
    assert fotos.candidatos_del_lugar(catedral, [ciudad, distrito], TIPOS) == []
    pueblo = recurso("2", "Huancayo", tipo="Pueblos", subtipo="Pueblos tradicionales")
    assert [e["qid"] for e in fotos.candidatos_del_lugar(pueblo, [ciudad], TIPOS)] == ["Q1"]


def test_la_base_toma_el_pueblo_de_su_nombre_y_prefiere_el_mas_conocido():
    base = {"nombre": "Huancayo", "lat": -12.0, "lon": -75.0}
    ciudad = elemento("Q1", "Huancayo", -12.02, -75.0, tipos=["Q515"], enlaces=60)
    distrito = elemento("Q2", "Distrito de Huancayo", -12.0, -75.0, tipos=["Q2179958"], enlaces=12)
    sitio = elemento("Q3", "Huancayo", -12.0, -75.0, tipos=["Q839954"])  # no es un pueblo
    lejano = elemento("Q4", "Huancayo", -12.2, -75.0, tipos=["Q515"])  # a 22 km
    assert [e["qid"] for e in fotos.candidatos_de_la_base(base, [lejano, sitio, distrito, ciudad], TIPOS)] == [
        "Q1",
        "Q2",
    ]


def test_solo_fotos_libres_grandes_en_jpeg_y_con_autor():
    assert fotos.libre(meta())
    assert fotos.libre(meta(licencia="CC BY 2.0"))
    assert fotos.libre(meta(licencia="CC BY-SA 2.5 pe"))
    assert fotos.libre(meta(licencia="Public domain", autor=""))
    assert not fotos.libre(meta(autor=""))  # CC BY sin a quién atribuir
    assert not fotos.libre(meta(licencia="GFDL"))
    assert not fotos.libre(meta(tipo="image/png"))
    assert not fotos.libre(meta(ancho=480))
    assert not fotos.libre(None)  # borrada de Commons


@pytest.mark.parametrize(
    ("en_commons", "se_lee"),
    [
        ("Jose Carlos de la Puente", "Jose Carlos de la Puente"),
        ("No machine-readable author provided. Xauxa assumed (based on copyright claims).", "Xauxa"),
        ("User:Pedro Felipe", "Pedro Felipe"),
        ("en:User:Dynamax", "Dynamax"),
        ("Y. Hooker[[User:|Hookery]]", "Y. Hooker"),
        ("Ericbronder at English Wikipedia", "Ericbronder"),
        ("The original uploader was Steve Pastor at English Wikipedia .", "Steve Pastor"),
        ("AgainErick at English Wikipedia ( Original text: AgainErick )", "AgainErick"),
        ("Martin St-Amant ( S23678 )", "Martin St-Amant (S23678)"),
        (
            "CREDIT: Photo courtesy of Rutahsa Adventures www.rutahsa.com - uploaded with permission by User:Leo",
            "Rutahsa Adventures www.rutahsa.com",
        ),
        # Un nombre con su cuenta o su ciudad se queda como está.
        (
            "Bryan Dougherty (bryand_nyc) from New York City, USA",
            "Bryan Dougherty (bryand_nyc) from New York City, USA",
        ),
        ("Mediaperu~commonswiki", "Mediaperu~commonswiki"),
        # Lo que no nombra a nadie.
        ("Trabajo propio", ""),
        ("self", ""),
        ("Unknown author Unknown author", ""),
        ("", ""),
        (None, ""),
    ],
)
def test_el_autor_se_lee_sin_los_restos_de_la_wiki(en_commons, se_lee):
    assert fotos.autor_legible(en_commons) == se_lee
    assert fotos.autor_legible(se_lee) == se_lee  # limpiar dos veces no cambia nada


def test_una_foto_cuyo_autor_no_nombra_a_nadie_solo_sirve_si_es_de_dominio_publico():
    assert not fotos.libre(meta(autor="Trabajo propio"))
    assert not fotos.libre(meta(autor="Unknown author Unknown author", licencia="CC BY 2.0"))
    assert fotos.libre(meta(autor="Trabajo propio", licencia="CC0"))
    assert fotos.libre(meta(autor="self", licencia="Public domain"))
    # Lo que se publica es el autor ya limpio.
    sucio = meta(autor="No machine-readable author provided. Xauxa assumed (based on copyright claims).")
    assert fotos.foto("Jauja.jpg", sucio, "Q1")["autor"] == "Xauxa"


def test_de_un_elemento_gana_la_foto_apaisada_mas_grande():
    e = elemento("Q1", "X", 0, 0, imagenes=["Vertical.jpg", "Chica.jpg", "Grande.jpg", "Plano.png"])
    metadatos = {
        "Vertical.jpg": meta(ancho=3000, alto=4000),
        "Chica.jpg": meta(ancho=1200, alto=800),
        "Grande.jpg": meta(ancho=4000, alto=3000),
        "Plano.png": meta(ancho=9000, alto=6000, tipo="image/png"),
    }
    elegida = fotos.mejor_foto([e], metadatos)
    assert elegida["archivo"] == "Grande.jpg"
    assert elegida["wikidata"] == "Q1"


def test_la_carpeta_en_commons_sale_de_la_huella_del_nombre():
    # La misma que usa upload.wikimedia.org: .../commons/b/bb/WillkawainTempel2.jpg
    assert fotos.ruta_en_commons("WillkawainTempel2.jpg") == "b/bb"
    assert fotos.ruta_en_commons("Templo de Huarivilca.jpg") == fotos.ruta_en_commons("Templo_de_Huarivilca.jpg")


def test_lo_revisado_a_mano_manda():
    r = recurso("7", "Wariwillka") | {"es_parada": True}
    polo = {"id": 5, "base": {"nombre": "Huancayo", "lat": -12.0, "lon": -75.0}}
    elementos = [
        elemento("Q1", "Huarihuilca", -12.0, -75.0, imagenes=["Mala.jpg"]),
        elemento("Q2", "Huancayo", -12.0, -75.0, tipos=["Q515"], imagenes=["Ciudad.jpg"]),
    ]
    metadatos = {"Mala.jpg": meta(), "Buena.jpg": meta(), "Ciudad.jpg": meta()}
    sin_revisar = fotos.elegir([r], [polo], elementos, TIPOS, metadatos, {})
    assert sin_revisar["lugares"]["7"]["archivo"] == "Mala.jpg"
    assert sin_revisar["bases"]["5"]["archivo"] == "Ciudad.jpg"
    revisadas = {("lugar", "7"): "Buena.jpg", ("base", "5"): ""}
    corregido = fotos.elegir([r], [polo], elementos, TIPOS, metadatos, revisadas)
    assert corregido["lugares"]["7"]["archivo"] == "Buena.jpg"
    assert "5" not in corregido["bases"]


def con_coordenadas(archivo, m=100):
    return {"archivo": archivo, "lat": -12.0, "lon": -75.0, "m": m}


def test_el_nombre_de_un_archivo_sin_lo_que_agregan_la_camara_y_panoramio():
    assert fotos.titulo_de("Catarata El León - panoramio (2).jpg") == "Catarata El León"
    assert fotos.titulo_de("IMG_4521 Laguna Churup.JPG").strip() == "Laguna Churup"
    assert fotos.titulo_de("Plaza_de_Armas_DSC01234.jpeg").strip() == "Plaza de Armas"


def test_sin_foto_en_wikidata_sirve_una_de_commons_que_nombra_al_lugar_y_su_clase():
    catarata = Nombre.de("Catarata El León")
    archivos = [
        con_coordenadas("Restaurante El León.jpg", m=50),  # otra cosa: no dice que es una catarata
        con_coordenadas("Vista del valle.jpg", m=80),  # no nombra al lugar
        con_coordenadas("Catarata El León - panoramio.jpg", m=900),
        con_coordenadas("Cascada El León vertical.jpg", m=300),  # la misma familia, pero vertical
    ]
    metadatos = {a["archivo"]: meta() for a in archivos} | {"Cascada El León vertical.jpg": meta(1000, 1500)}
    elegida = fotos.de_commons(catarata, archivos, metadatos, base=False)
    assert elegida["archivo"] == "Catarata El León - panoramio.jpg"
    assert elegida["wikidata"] == ""


def test_de_commons_solo_fotos_libres_y_nunca_para_un_nombre_de_pura_clase():
    archivos = [con_coordenadas("Plaza de Armas de Tarma.jpg")]
    assert (
        fotos.de_commons(Nombre.de("Plaza de Armas"), archivos, {"Plaza de Armas de Tarma.jpg": meta()}, False) is None
    )
    tarma = Nombre.de("Tarma")
    assert (
        fotos.de_commons(tarma, archivos, {"Plaza de Armas de Tarma.jpg": meta(licencia="All rights reserved")}, True)
        is None
    )
    assert (
        fotos.de_commons(tarma, archivos, {"Plaza de Armas de Tarma.jpg": meta()}, True)["archivo"]
        == archivos[0]["archivo"]
    )


def test_commons_por_coordenadas_solo_cuando_wikidata_no_da_nada_y_lo_revisado_manda():
    r = recurso("7", "Wariwillka") | {"es_parada": True}
    sin_foto = recurso("8", "Catarata El León", tipo="Caídas de agua") | {"es_parada": True}
    polo = {"id": 5, "base": {"nombre": "La Merced", "lat": -12.0, "lon": -75.0}}
    elementos = [elemento("Q1", "Huarihuilca", -12.0, -75.0, imagenes=["De Wikidata.jpg"])]
    cerca = {
        "lugar:7": [con_coordenadas("Wariwillka.jpg")],
        "lugar:8": [con_coordenadas("Catarata El León.jpg")],
        "base:5": [con_coordenadas("La Merced 001 - panoramio.jpg")],
    }
    nombres = ["De Wikidata.jpg", "Wariwillka.jpg", "Catarata El León.jpg", "La Merced 001 - panoramio.jpg"]
    metadatos = {a: meta() for a in nombres}
    elegidas = fotos.elegir([r, sin_foto], [polo], elementos, TIPOS, metadatos, {}, cerca)
    assert elegidas["lugares"]["7"]["archivo"] == "De Wikidata.jpg"
    assert elegidas["lugares"]["8"]["archivo"] == "Catarata El León.jpg"
    assert elegidas["bases"]["5"]["archivo"] == "La Merced 001 - panoramio.jpg"
    revisadas = {("lugar", "8"): "", ("base", "5"): ""}
    corregidas = fotos.elegir([r, sin_foto], [polo], elementos, TIPOS, metadatos, revisadas, cerca)
    assert "8" not in corregidas["lugares"] and "5" not in corregidas["bases"]


def test_el_elemento_no_puede_ser_sobre_otra_cosa():
    plaza = recurso("1", "Plaza de Armas de Huánuco", tipo="Arquitectura y Espacios Urbanos", subtipo="Plazas")
    mercado = elemento("Q1", "Mercado Viejo de Huánuco", -12.0, -75.0)
    assert fotos.candidatos_del_lugar(plaza, [mercado], TIPOS) == []


def test_un_centro_historico_se_muestra_con_su_plaza_y_no_con_una_iglesia():
    centro = recurso("1", "Centro Histórico de Trujillo", tipo="Arquitectura y Espacios Urbanos")
    plaza = elemento("Q1", "Plaza de Armas de Trujillo", -12.0, -75.0)
    iglesia = elemento("Q2", "Iglesia de la Compañía de Trujillo", -12.0, -75.0)
    assert [e["qid"] for e in fotos.candidatos_del_lugar(centro, [iglesia, plaza], TIPOS)] == ["Q1"]


def test_una_reserva_con_el_mismo_nombre_puede_estar_lejos():
    reserva = recurso("1", "Reserva Nacional de Junín", tipo="Áreas Protegidas")
    a_20_km = elemento("Q1", "Reserva nacional de Junín", -12.18, -75.0)
    assert [e["qid"] for e in fotos.candidatos_del_lugar(reserva, [a_20_km], TIPOS)] == ["Q1"]
    iglesia = recurso("2", "Iglesia de Junín", tipo="Arquitectura y Espacios Urbanos")
    lejana = elemento("Q2", "Iglesia de Junín", -12.18, -75.0)
    assert fotos.candidatos_del_lugar(iglesia, [lejana], TIPOS) == []


def test_una_batalla_tiene_coordenadas_pero_no_es_un_lugar():
    tipos = TIPOS | {"Q178561": {"en": "battle", "es": "batalla"}}
    sitio = recurso("1", "Parque Arqueológico de Ollantaytambo")
    batalla = elemento("Q1", "Batalla de Ollantaytambo", -12.0, -75.0, tipos=["Q178561"])
    assert fotos.candidatos_del_lugar(sitio, [batalla], tipos) == []


def test_la_base_no_toma_la_foto_de_toda_la_region():
    tipos = TIPOS | {"Q9": {"en": "department of Peru", "es": "departamento del Perú"}}
    base = {"nombre": "Ayacucho", "lat": -12.0, "lon": -75.0}
    region = elemento("Q1", "Departamento de Ayacucho", -12.0, -75.0, tipos=["Q9"], enlaces=80)
    assert fotos.candidatos_de_la_base(base, [region], tipos) == []


def test_un_collage_o_un_mapa_no_son_una_foto():
    assert not fotos.libre(meta(), "Collage de Iquitos, 2024.jpg")
    assert not fotos.libre(meta(), "Mapa de Huancayo.jpg")
    assert fotos.libre(meta(), "Mapacho al atardecer.jpg")


def test_una_correccion_mal_escrita_no_se_pasa_por_alto(tmp_path):
    ruta = tmp_path / "fotos_revisadas.csv"
    cabecera = "tipo;clave;archivo;motivo\n"
    ruta.write_text(cabecera + "lugar;7;;Wariwillka: es otro sitio\nbase;5;Plaza.jpg;Huancayo: va la plaza\n", "utf-8")
    assert fotos.leer_revisadas(ruta) == {("lugar", "7"): "", ("base", "5"): "Plaza.jpg"}
    # Un punto y coma en el motivo correría los campos.
    ruta.write_text(cabecera + "base;5;Plaza.jpg;Huancayo: era un óvalo; va la plaza\n", "utf-8")
    with pytest.raises(ValueError, match="línea 2"):
        fotos.leer_revisadas(ruta)
    ruta.write_text(cabecera + "lugar;7;;Wariwillka: una\nlugar;7;Otra.jpg;Wariwillka: otra\n", "utf-8")
    with pytest.raises(ValueError, match="línea 3"):
        fotos.leer_revisadas(ruta)
    ruta.write_text(cabecera + "pueblo;7;;No es ni un lugar ni una base\n", "utf-8")
    with pytest.raises(ValueError, match="línea 2"):
        fotos.leer_revisadas(ruta)


def test_se_avisa_de_la_correccion_que_pone_una_foto_que_no_se_puede_usar():
    revisadas = {
        ("lugar", "1"): "Buena.jpg",
        ("lugar", "2"): "Sin descargar.jpg",
        ("base", "3"): "Sin licencia libre.jpg",
        ("base", "4"): "",
    }
    metadatos = {"Buena.jpg": meta(), "Sin licencia libre.jpg": meta(licencia="GFDL")}
    assert fotos.sin_efecto(revisadas, metadatos) == [
        ("base", "3", "Sin licencia libre.jpg"),
        ("lugar", "2", "Sin descargar.jpg"),
    ]


# ───────────── lo que está en el repositorio: las correcciones y la lista que lee la app ─────────────


def paradas_y_bases():
    recursos = fotos.leer_gz(fotos.DATOS / "recursos.json.gz")
    polos = fotos.leer_gz(fotos.DATOS / "polos.json.gz")
    return {r["codigo"] for r in recursos if r.get("es_parada")}, {str(p["id"]): p["base"]["nombre"] for p in polos}


def test_las_correcciones_nombran_paradas_y_bases_que_existen():
    paradas, bases = paradas_y_bases()
    revisadas = fotos.leer_revisadas()  # si una fila está mal escrita, falla aquí
    assert len(revisadas) > 100
    assert [c for t, c in revisadas if t == "lugar" and c not in paradas] == []
    assert [c for t, c in revisadas if t == "base" and c not in bases] == []
    # El número de un polo puede cambiar al rehacer los artefactos: el motivo de cada base
    # empieza con su nombre, y así una fila que quedó apuntando a otro pueblo se nota.
    with open(fotos.REVISADAS, encoding="utf-8", newline="") as fh:
        de_bases = [f for f in csv.DictReader(fh, delimiter=";") if f["tipo"] == "base"]
    assert [f["clave"] for f in de_bases if not f["motivo"].startswith(bases[f["clave"]])] == []


def test_la_lista_publicada_es_de_estos_datos_y_respeta_las_correcciones():
    paradas, bases = paradas_y_bases()
    publicada = json.loads(fotos.SALIDA.read_text(encoding="utf-8"))
    manifiesto = json.loads((fotos.DATOS / "manifiesto.json").read_text(encoding="utf-8"))
    # Si falla: correr «python -m pipeline.fotos» después de rehacer los artefactos o de corregir.
    assert publicada["version_datos"] == manifiesto["version_datos"]
    assert set(publicada["lugares"]) <= paradas
    assert set(publicada["bases"]) <= set(bases)
    for (tipo, clave), archivo in fotos.leer_revisadas().items():
        puesta = publicada["lugares" if tipo == "lugar" else "bases"].get(clave, {})
        assert puesta.get("archivo", "") == archivo, f"{tipo} {clave}"
    for foto in [*publicada["lugares"].values(), *publicada["bases"].values()]:
        assert foto["ruta"] == fotos.ruta_en_commons(foto["archivo"])
        assert foto["ancho"] >= fotos.ANCHO_MINIMO and foto["alto"] > 0
        assert fotos.LICENCIA_LIBRE.match(foto["licencia"])
        assert foto["autor"] or fotos.DOMINIO_PUBLICO.match(foto["licencia"])
        # El crédito se muestra tal cual: va limpio y es un nombre, no una explicación.
        assert foto["autor"] == fotos.autor_legible(foto["autor"]), foto["archivo"]
        assert len(foto["autor"]) <= 60, foto["archivo"]
