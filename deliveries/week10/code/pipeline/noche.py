"""
Dónde salir de noche cerca de donde se duerme en cada polo: bares, pubs, discotecas, karaokes y
peñas (decisión 0018).

1. **OpenStreetMap.** Del extracto del Perú, los bares, pubs, discotecas, karaokes y salones de
   baile con nombre (``amenity`` bar, pub, nightclub, biergarten, karaoke_box, music_venue;
   ``leisure`` dance), y las peñas, que OSM marca como bar o restaurante: se reconocen por el
   nombre. De paso guarda los miradores, los observatorios y los planetarios, que usa
   ``pipeline/cielo.py``.
2. **Overture Maps.** Tiene diez veces más: casi todo viene de las páginas de Meta. Se toman los
   de una categoría de la noche, con nombre y una confianza de al menos 0,7, y solo de fuentes
   con licencia CDLA: lo de Foursquare (Apache 2.0) queda fuera. Las «salas de música» de
   Overture no entran: son sobre todo locales de eventos, salas de ensayo y tiendas.
3. **Lo que no es de noche** aunque su categoría lo diga, por su nombre. Nunca lo es una
   agencia de turismo, un hotel, una pollería, un colegio, un casino, una cancha, una tienda ni
   una catarata (``NO_ES_DE_NOCHE``); ni un nombre que solo dice qué es («Bar», «Resto Bar») o
   que quedó cortado («Señor de»). Y lo que solo está en Overture, que casi siempre es la
   página que alguien abrió en Meta y le puso la categoría que quiso, tampoco si su nombre es de
   un restaurante, un sitio o una dirección («Restaurante Valentino», «Playa Barlovento», «Jr Los
   Rosales 311») y no dice nada de la noche (``DUDOSO_EN_OVERTURE``, ``DE_NOCHE``). Lo de OSM,
   que una persona marcó como bar, sí queda: «Cafe Soprano's» es un bar.
4. **Uno solo por lugar.** Uno de Overture con el mismo nombre que uno de OSM a menos de 150 m,
   o con casi el mismo a menos de 60 m, es el mismo: queda el de OSM, que tiene una página
   pública para verificarlo, con la confianza de Overture. Después, dos con el mismo nombre a
   menos de 300 m son uno.
5. **Cerca.** Para cada polo, los que quedan a menos de 1,5 km en línea recta de su base: a pie,
   con un 30 % más de camino que la línea recta y a 4,5 km/h, unos 25 minutos.

El orden, que la app y el motor usan para elegir qué nombrar, es por confianza: un lugar que
está en las dos fuentes va primero, y uno que solo está en OSM vale como uno de Overture de 0,8.
Uno que solo está en Overture y cuyo nombre no dice nada de la noche («Taj Mahal», pero también
«Huaytapallana», que es un nevado) va al final: se cuenta, pero se nombra solo si no hay otro.

Escribe data/procesados/noche_lugares.csv. Lo de OSM es obra derivada bajo ODbL; lo de
Overture, bajo CDLA Permissive 2.0.

Uso:  python -m pipeline.noche        (después de pipeline/tiempos.py y de descargar_overture.py)
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.maestro import EXTERNOS, PROCESADOS
from pipeline.red_vial import cercanos, haversine_m
from pipeline.texto import sin_tildes

OSM = EXTERNOS / "osm"
OVERTURE = EXTERNOS / "overture"
CACHE = 2  # sube cuando cambia lo que se guarda de los puntos de OSM
RADIO_M = 1_500
DESVIO = 1.3  # el camino a pie es un 30 % más largo que la línea recta
A_PIE_M_POR_MIN = 75  # 4,5 km/h
CONFIANZA_MIN = 0.7
CONFIANZA_SOLO_OSM = 0.8
MISMO_NOMBRE_M = 150
CASI_EL_MISMO_M = 60
DUPLICADO_M = 300
SIN_PISTA = 0.5  # lo que baja en el orden uno de Overture cuyo nombre no dice que sea de noche

# Qué tipo de lugar es cada etiqueta de OSM y cada categoría de Overture.
TIPO_OSM = {
    ("amenity", "bar"): "bar",
    ("amenity", "biergarten"): "pub",
    ("amenity", "pub"): "pub",
    ("amenity", "nightclub"): "discoteca",
    ("leisure", "dance"): "discoteca",
    ("amenity", "karaoke_box"): "karaoke",
    ("amenity", "music_venue"): "musica",
}
TIPO_OVERTURE = {
    **dict.fromkeys(
        (
            "bar",
            "cocktail_bar",
            "wine_bar",
            "whiskey_bar",
            "sports_bar",
            "tapas_bar",
            "hookah_bar",
            "tiki_bar",
            "dive_bar",
            "beach_bar",
            "sake_bar",
            "hotel_bar",
            "gay_bar",
            "lounge",
        ),
        "bar",
    ),
    **dict.fromkeys(("pub", "irish_pub", "gastropub", "beer_bar", "beer_garden"), "pub"),
    **dict.fromkeys(("dance_club", "salsa_club", "nightlife_venue"), "discoteca"),
    "karaoke_venue": "karaoke",
    "jazz_and_blues_venue": "musica",
    "comedy_club": "comedia",
}
# Una peña puede estar en cualquiera de estas: en OSM, como bar o restaurante; en Overture, como
# sala de música, bar o restaurante.
PENA_OSM = {"bar", "pub", "restaurant", "nightclub", "events_venue", "music_venue", "arts_centre"}
PENA_OVERTURE = {
    "music_venue",
    "bar",
    "restaurant",
    "peruvian_restaurant",
    "latin_american_restaurant",
    "dance_club",
    "gastropub",
    "karaoke_venue",
}
PENA = re.compile(r"\bpe[ñn]a\b")
PENA_AL_COMIENZO = re.compile(r"^(la\s+)?pe[ñn]a\b")
PENA_CON_TODO = re.compile(r"\bpe[ñn]as?\s+(turistica|criolla|show|folk|folc|cultural|recreo)")
NO_PENA = re.compile(r"\b(saenz|roque|trebejo|de)\s+pe[ñn]a\b")  # apellidos y calles: «Mérito de Peña»
# Lo que dice el nombre. Se lee con ``plano``: sin tildes, en minúsculas y en la forma compatible
# de Unicode, así que «𝙋𝙤𝙡𝙡𝙤𝙨» es «pollos». Salen de revisar a mano los 1 367 lugares de la
# primera vuelta (decisión 0018).
DE_NOCHE = re.compile(
    r"\bbar\b|\w+bar\b|\bbar(es|ra)\b|pub\b|\bdisco|karaoke|\bpe[ñn]as?\b|lounge|club|\bcantina|\bta[bv]e+rna"
    r"|\btavern|\bresto\b|cervec|brew|beer|\bbier|\bchela|\bchopp|\btap\s?room|cocktail|coctel|\bdrinks?\b"
    r"|tragos?\b|\bpisco\b|\bpisqu|\bmezcal|\bwhisk|\bvinos?\b|\bwine|\brock\b|\bsalsa\b|\brooftop|\bsnack"
    r"|\bvideo|\bmusic|\bshow\b|\bvip\b|\bdance|\brumba|\bjazz|\bchicher|\bbillar|\bboxes\b|\bnight|\bnoche\b"
    r"|\btequila|\bconcert|\bcopas\b|\btapas\b"
)
NO_ES_DE_NOCHE = re.compile(
    r"rent a car|\bruinas?\b|\bhotel\b|\bhostal\b|\bhostel\b|\bhospedaje\b|\bcorporativ|\be\.?i\.?r\.?l\b"
    r"|\bs\.?a\.?c\b|\bs\.?r\.?l\b|\btours?\b|\btravel\b|\bagencia\b|\btrek\w*|\bcooking\b|\bhealthy\b"
    r"|\bburgers?\b|\bpizzeria\b|\bchifas?\b|\bpolleria\b|\bcevicher\w*|\bcebicher\w*|\balmuerzo|\bpanaderia\b"
    r"|\bminimarket\b|\bferreteria\b|\bfarmacia\b|\bbotica\b|\bstore\b|\btiendas?\b|\bcentro comercial\b"
    r"|^c\.? ?c\.? |\binmobiliaria\b|\binversiones\b|\bdistribu\w+|\bbackus\b|\bfibraforte\b|\bdeposito\b"
    r"|\bcolegio\b|\bcoar\b|\bsenati\b|\bsencico\b|\bcetpro\b|\binstituto\b|\buniversidad\b|\bacademia\b"
    r"|\bescuela\b|\bdistrito\b|\bmunicipalidad\b|\bministerio\b|\bcofopri\b|\bcapitania\b|\benace\b"
    r"|\bcentro civico\b|\biglesia\b|\bcasino\b|\btragamonedas\b|\bapuestas\b|\bsportbet\b|\btinbet\b"
    r"|\bkarts?\b|\bcanchas?\b|\bcanchita\b|\bgimnasio\b|\bgym\b|\bsauna\b|\bspa\b|\bestetica\b|\bpeluqueria\b"
    r"|\bbarberia\b|\bcatarata\b|\bcascada\b|\bcañon\b|\bpuente\b|\bmalecon\b|\bmuelle\b|\bobelisco\b"
    r"|\blaguna\b|\borquesta\b|\bclub (arabe|deportivo|de leones|de tiro|de regatas)\b|\blicor|\bliquor"
)
# En Overture, un nombre de restaurante, de sitio o de dirección, si no dice nada de la noche.
DUDOSO_EN_OVERTURE = re.compile(
    r"\brestaurant\w*|\brestaurat\b|\bchicharroner\w*|\bsanguch\w*|\bpollos?\b|\bparrillas?\b|\bbrasas\b"
    r"|\banticuch\w*|\bmenu\b|\bcomida\b|\btea room\b|\bemolient\w*|\bcafe\b|\bkaffe\b|\bcoffee\b|\bcafeter\w*"
    r"|\bgrill\b|\bpizza\w*|\bgourmet\b|\bstreet food\b|\beventos?\b|\bconvenciones\b|\bproducciones\b"
    r"|\bgrupo\b|\bgaleria\b|\bmarket\b|\bbodega\b|\bcampestre\b|\brecreo\b|\bplaya\b|\bcaleta\b|\bpuerto\b"
    r"|\bcerro\b|\bmirador\b|\brio\b|\bbarrio\b|\bcity\b|\bparroquia\b|\btemplo\b|^(san|santa|santo) "
    r"|^nuev[oa]s? |^punta |^villa |^fiesta "
    r"|^(jr|jiron|av|avenida|calle|psje|pasaje|urb|urbanizacion|mz|manzana|prolongacion|carretera|km)\b"
)
# Las palabras que dicen qué es un lugar y no cuál es: no cuentan al comparar nombres, y un nombre
# hecho solo de ellas («Bar», «Resto Bar», «Disco Teca») no es un nombre. «Bar Lima» sí lo es.
GENERICAS = {
    "bar",
    "pub",
    "resto",
    "restobar",
    "restaurante",
    "restaurant",
    "club",
    "disco",
    "discoteca",
    "karaoke",
    "lounge",
    "the",
    "la",
    "el",
    "los",
    "las",
    "de",
    "del",
    "y",
    "and",
    "cafe",
    "cusco",
    "cuzco",
    "lima",
}
SOLO_DICEN_QUE_ES = (GENERICAS - {"cusco", "cuzco", "lima"}) | {"teca", "discotek", "discoteck", "discoteka", "snack"}
# Los puntos de OSM que se guardan: los de la noche y los del cielo (pipeline/cielo.py).
ETIQUETAS_OSM = (
    *(("amenity", v) for v in ("bar", "pub", "nightclub", "biergarten", "karaoke_box", "music_venue")),
    *(("amenity", v) for v in ("restaurant", "events_venue", "arts_centre", "planetarium")),
    ("leisure", "dance"),
    ("tourism", "viewpoint"),
    ("man_made", "observatory"),
    ("man_made", "telescope"),
)


def _etiqueta(tags) -> tuple[str, str] | None:
    for clave, valor in ETIQUETAS_OSM:
        if tags.get(clave) == valor:
            return clave, valor
    return None


def leer_puntos(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """Los puntos de OSM de ``ETIQUETAS_OSM``: el nodo, o el promedio de los nodos del contorno.

    Columnas: clave, valor, nombre, lat, lon, osm (``node/123`` o ``way/456``), horario
    (``opening_hours`` tal cual) y altitud_m (``ele``, si la tiene). Los restaurantes, los locales
    de eventos y los centros culturales, solo si su nombre dice peña."""
    import osmium

    from pipeline.texto import leer_altitud

    filas = []
    procesador = (
        osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations(indice)
        .with_filter(osmium.filter.TagFilter(*ETIQUETAS_OSM))
    )
    for objeto in procesador:
        etiqueta = _etiqueta(objeto.tags)
        nombre = (objeto.tags.get("name") or "").strip()
        if etiqueta is None or (etiqueta[1] in ("restaurant", "events_venue", "arts_centre") and not es_pena(nombre)):
            continue
        if objeto.is_node():
            if not objeto.location.valid():
                continue
            lat, lon, osm = objeto.location.lat, objeto.location.lon, f"node/{objeto.id}"
        else:
            puntos = [(nd.lat, nd.lon) for nd in objeto.nodes if nd.location.valid()]
            if len(puntos) > 1 and puntos[0] == puntos[-1]:
                puntos = puntos[:-1]
            if not puntos:
                continue
            lat, lon = (float(x) for x in np.mean(puntos, axis=0))
            osm = f"way/{objeto.id}"
        altitud = leer_altitud(objeto.tags.get("ele"))[0]
        filas.append((*etiqueta, nombre, lat, lon, osm, objeto.tags.get("opening_hours") or "", altitud))
    return pd.DataFrame(filas, columns=["clave", "valor", "nombre", "lat", "lon", "osm", "horario", "altitud_m"])


def puntos_en_cache(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """``leer_puntos``, guardados junto al extracto: se rehacen si cambia su MD5."""
    manifiesto = json.loads((pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    ruta = pbf.parent / f"puntos_de_noche_{manifiesto['md5'][:8]}_v{CACHE}.csv"
    if not ruta.exists():
        leer_puntos(pbf, indice).to_csv(ruta, index=False)
    puntos = pd.read_csv(ruta, keep_default_na=False, dtype={"horario": str, "nombre": str})
    return puntos.assign(altitud_m=pd.to_numeric(puntos["altitud_m"], errors="coerce"))


def es_pena(nombre: str, de_comer: bool = False) -> bool:
    """Si el nombre dice que es una peña, donde se come con música criolla o andina en vivo. En un
    restaurante o una cafetería, solo si empieza por «Peña» o lo dice con todas sus letras («peña
    turística», «peña criolla»): «Cafetería La Peña» puede ser solo un nombre."""
    n = plano(nombre).strip()
    al_comienzo = bool(PENA_AL_COMIENZO.search(n))
    if not PENA.search(n) or (NO_PENA.search(n) and not al_comienzo):
        return False
    return not de_comer or al_comienzo or bool(PENA_CON_TODO.search(n))


def plano(nombre: str) -> str:
    """El nombre para leerlo: sin tildes, en minúsculas, en la forma compatible de Unicode y sin
    guiones bajos. «𝙋𝙤𝙡𝙡𝙤𝙨_y» es «pollos y»."""
    return sin_tildes(unicodedata.normalize("NFKC", nombre)).replace("_", " ")


def no_es_de_noche(nombre: str) -> bool:
    """Si el nombre dice que no es un lugar para salir de noche, sea de la fuente que sea: por lo
    que es (``NO_ES_DE_NOCHE``), porque solo dice qué es o porque quedó cortado."""
    n = plano(nombre).strip()
    palabras_ = re.findall(r"[a-z0-9ñ]+", n)
    return (
        not palabras_
        or bool(NO_ES_DE_NOCHE.search(n))
        or all(p in SOLO_DICEN_QUE_ES for p in palabras_)
        or palabras_[-1] in ("de", "del", "la", "el", "los", "las", "y", "en")
    )


def dice_que_es_de_noche(nombre: str) -> bool:
    return bool(DE_NOCHE.search(plano(nombre)))


def dudoso_en_overture(nombre: str) -> bool:
    """Si un lugar que solo está en Overture tiene nombre de restaurante, de sitio o de dirección
    y no dice nada de la noche."""
    n = plano(nombre).strip()
    return bool(DUDOSO_EN_OVERTURE.search(n)) and not DE_NOCHE.search(n)


def limpio(nombre: str) -> str:
    """En la forma compatible de Unicode, sin comillas ni espacios de más; un nombre todo en
    mayúsculas pasa a mayúscula inicial."""
    n = unicodedata.normalize("NFKC", nombre)
    n = " ".join(n.replace('"', " ").replace("“", " ").replace("”", " ").split()).strip(" -|·,")
    if len(n) > 3 and n.isupper():
        n = " ".join(p.capitalize() for p in n.split())
    return n


def palabras(nombre: str) -> frozenset[str]:
    """Las palabras de un nombre que dicen cuál es el lugar: sin tildes, apóstrofos ni signos, y sin
    las genéricas («bar», «la», «club»), salvo que no quede otra. «Paddy's» es «paddys»."""
    todas = re.findall(r"[a-z0-9ñ]+", plano(nombre).replace("'", "").replace("’", ""))
    return frozenset(p for p in todas if p not in GENERICAS) or frozenset(todas)


def de_osm(puntos: pd.DataFrame) -> pd.DataFrame:
    """Los lugares de la noche de OSM, con su tipo."""
    tipos = []
    for clave, valor, nombre in zip(puntos["clave"], puntos["valor"], puntos["nombre"], strict=True):
        if not nombre or no_es_de_noche(nombre):
            tipos.append(None)
        elif valor in PENA_OSM and es_pena(nombre, de_comer=valor == "restaurant"):
            tipos.append("pena")
        elif clave == "leisure" and re.search(r"\b(escuela|academia|ballet|danzas?)\b", sin_tildes(nombre)):
            tipos.append(None)  # en OSM, leisure=dance también marca academias de baile
        else:
            tipos.append(TIPO_OSM.get((clave, valor)))
    lugares = puntos.assign(tipo=tipos).dropna(subset=["tipo"])
    return pd.DataFrame(
        {
            "nombre": lugares["nombre"].map(limpio),
            "tipo": lugares["tipo"],
            "lat": lugares["lat"],
            "lon": lugares["lon"],
            "fuente": "osm",
            "osm": lugares["osm"],
            "overture": "",
            "confianza": np.nan,
            "horario": lugares["horario"],
            "dudoso": False,
        }
    ).reset_index(drop=True)


def de_overture(ruta: Path) -> pd.DataFrame:
    """Los lugares de la noche de Overture: con nombre, una categoría de la noche, confianza de al
    menos ``CONFIANZA_MIN`` y solo de fuentes con licencia CDLA. Los ``dudoso`` (con nombre de
    restaurante, de sitio o de dirección) sirven para confirmar uno de OSM, pero solos no quedan."""
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    tabla = pq.read_table(ruta, columns=["id", "confidence", "names", "taxonomy", "bbox", "sources"])
    categoria = pc.struct_field(tabla["taxonomy"], "primary").to_pylist()
    filas = []
    for i, (cat, nombres, confianza, fuentes) in enumerate(
        zip(
            categoria,
            tabla["names"].to_pylist(),
            tabla["confidence"].to_pylist(),
            tabla["sources"].to_pylist(),
            strict=True,
        )
    ):
        nombre = ((nombres or {}).get("primary") or "").strip()
        if not nombre or confianza is None or confianza < CONFIANZA_MIN:
            continue
        licencias = {f.get("license") for f in fuentes or []}
        if not licencias or any(not (lic or "").startswith("CDLA") for lic in licencias):
            continue
        if no_es_de_noche(nombre):
            continue
        if cat in PENA_OVERTURE and es_pena(nombre, de_comer=cat.endswith("restaurant")):
            tipo = "pena"
        else:
            tipo = TIPO_OVERTURE.get(cat)
        if tipo is not None:
            filas.append((i, limpio(nombre), tipo, float(confianza)))
    if not filas:
        return pd.DataFrame(
            columns=["nombre", "tipo", "lat", "lon", "fuente", "osm", "overture", "confianza", "horario", "dudoso"]
        )
    idx = [f[0] for f in filas]
    caja = tabla["bbox"].take(idx)
    ids = tabla["id"].take(idx).to_pylist()
    lugares = pd.DataFrame(
        {
            "nombre": [f[1] for f in filas],
            "tipo": [f[2] for f in filas],
            "lat": pc.struct_field(caja, "ymin").to_pylist(),
            "lon": pc.struct_field(caja, "xmin").to_pylist(),
            "fuente": "overture",
            "osm": "",
            "overture": ids,
            "confianza": [f[3] for f in filas],
            "horario": "",
        }
    )
    return lugares.assign(dudoso=lugares["nombre"].map(dudoso_en_overture))


def orden(lugares: pd.DataFrame) -> np.ndarray:
    """Cuánto se confía en cada lugar: uno que está en las dos fuentes, 1 más su confianza en
    Overture; uno que solo está en OSM, ``CONFIANZA_SOLO_OSM``; uno de Overture, su confianza, y
    ``SIN_PISTA`` menos si su nombre no dice nada de la noche."""
    con_osm = lugares["osm"].astype(bool).to_numpy()
    con_overture = lugares["overture"].astype(bool).to_numpy()
    confianza = lugares["confianza"].astype(float).fillna(0).to_numpy()
    sin_pista = ~lugares["nombre"].map(dice_que_es_de_noche).to_numpy(dtype=bool)
    return np.select(
        [con_osm & con_overture, con_osm], [1.0 + confianza, CONFIANZA_SOLO_OSM], confianza - SIN_PISTA * sin_pista
    )


def _sin_repetidos(lugares: pd.DataFrame) -> pd.DataFrame:
    """Dos con las mismas palabras a menos de ``DUPLICADO_M`` son uno: queda el más confiable."""
    lugares = (
        lugares.assign(_orden=orden(lugares))
        .sort_values(["_orden", "osm", "overture"], ascending=[False, True, True])
        .drop(columns="_orden")
        .reset_index(drop=True)
    )
    clave = [palabras(n) for n in lugares["nombre"]]
    vecinos = cercanos(
        lugares["lat"].to_numpy(),
        lugares["lon"].to_numpy(),
        lugares["lat"].to_numpy(),
        lugares["lon"].to_numpy(),
        DUPLICADO_M,
    )
    fuera = set()
    for i, cerca in enumerate(vecinos):
        if i in fuera:
            continue
        fuera.update(j for j in cerca if j > i and clave[j] == clave[i])
    return lugares.drop(index=sorted(fuera)).reset_index(drop=True)


def mismo_lugar(a: str, b: str, metros: float) -> bool:
    """Si dos nombres a ``metros`` uno del otro son el mismo lugar: con las mismas palabras, a menos de
    ``MISMO_NOMBRE_M``; con casi las mismas (la mitad en común, o las de uno dentro de las del otro,
    como «Bonustrack» y «Bonustrack Cocktails Music»), a menos de ``CASI_EL_MISMO_M``."""
    pa, pb = palabras(a), palabras(b)
    if pa == pb:
        return metros <= MISMO_NOMBRE_M
    if metros > CASI_EL_MISMO_M or not (pa and pb):
        return False
    return pa <= pb or pb <= pa or len(pa & pb) / len(pa | pb) >= 0.5


def juntar(osm: pd.DataFrame, overture: pd.DataFrame) -> pd.DataFrame:
    """Los de OSM más los de Overture que no son uno de OSM y no son dudosos. Cuando lo son, el de
    OSM se queda con la confianza y el identificador de Overture."""
    osm = osm.copy()
    if len(osm) and len(overture):
        vecinos = cercanos(
            overture["lat"].to_numpy(),
            overture["lon"].to_numpy(),
            osm["lat"].to_numpy(),
            osm["lon"].to_numpy(),
            MISMO_NOMBRE_M,
        )
        repetidos = []
        for i, cerca in enumerate(vecinos):
            fila = overture.iloc[i]
            for j in sorted(cerca):
                m = haversine_m(fila["lat"], fila["lon"], osm.at[j, "lat"], osm.at[j, "lon"])
                if mismo_lugar(fila["nombre"], osm.at[j, "nombre"], float(m)):
                    if not osm.at[j, "overture"] or fila["confianza"] > osm.at[j, "confianza"]:
                        osm.at[j, "overture"] = fila["overture"]
                        osm.at[j, "confianza"] = fila["confianza"]
                    repetidos.append(i)
                    break
        overture = overture.drop(index=repetidos)
    if "dudoso" in overture:
        overture = overture[~overture["dudoso"].astype(bool)]
    juntos = pd.concat([osm, overture], ignore_index=True).drop(columns="dudoso", errors="ignore")
    return _sin_repetidos(juntos)


def cerca_de_cada_base(lugares: pd.DataFrame, bases: pd.DataFrame) -> pd.DataFrame:
    """Para cada polo, los lugares a menos de ``RADIO_M`` de su base, del más confiable al menos;
    entre iguales, del más cerca al más lejos."""
    vecinos = cercanos(
        bases["lat"].to_numpy(), bases["lon"].to_numpy(), lugares["lat"].to_numpy(), lugares["lon"].to_numpy(), RADIO_M
    )
    partes = []
    for (_, base), cerca in zip(bases.iterrows(), vecinos, strict=True):
        if not cerca:
            continue
        aqui = lugares.iloc[sorted(cerca)].copy()
        metros = haversine_m(base["lat"], base["lon"], aqui["lat"].to_numpy(), aqui["lon"].to_numpy())
        aqui = aqui.assign(
            polo=int(base["polo"]),
            metros=np.round(metros).astype(int),
            minutos_a_pie=np.maximum(1, np.ceil(metros * DESVIO / A_PIE_M_POR_MIN)).astype(int),
            _orden=orden(aqui),
        )
        partes.append(aqui.sort_values(["_orden", "metros", "nombre"], ascending=[False, True, True]))
    columnas = [
        "polo",
        "nombre",
        "tipo",
        "lat",
        "lon",
        "metros",
        "minutos_a_pie",
        "fuente",
        "osm",
        "overture",
        "confianza",
        "horario",
    ]
    if not partes:
        return pd.DataFrame(columns=columnas)
    return pd.concat(partes, ignore_index=True)[columnas]


def escribir(tabla: pd.DataFrame, ruta: Path) -> None:
    coordenadas = {c: tabla[c].map(lambda x: f"{x:.6f}") for c in ("lat", "lon")}
    confianza = tabla["confianza"].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
    tabla.assign(**coordenadas, confianza=confianza).to_csv(
        ruta, sep=";", index=False, encoding="utf-8-sig", lineterminator="\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Los lugares para salir de noche cerca de la base de cada polo.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--overture", type=Path, help="el parquet de descargar_overture.py; por defecto, el del manifiesto")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem")
    a = ap.parse_args()
    if a.overture is None:
        manifiesto = json.loads((OVERTURE / "manifiesto.json").read_text(encoding="utf-8"))
        a.overture = OVERTURE / manifiesto["archivo"]
    bases = pd.read_csv(PROCESADOS / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    osm = de_osm(puntos_en_cache(a.pbf, a.indice))
    overture = de_overture(a.overture)
    lugares = cerca_de_cada_base(juntar(osm, overture), bases)
    escribir(lugares, a.salida / "noche_lugares.csv")
    por_polo = lugares.groupby("polo").size()
    osm_manifiesto = json.loads((a.pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    resumen = {
        "osm": {"datos": osm_manifiesto["datos_last_modified"], "md5": osm_manifiesto["md5"]},
        "overture": a.overture.stem.removeprefix("lugares_peru_"),
        "confianza_minima": CONFIANZA_MIN,
        "radio_m": RADIO_M,
        "lugares": len(lugares),
        "de_osm": int((lugares["fuente"] == "osm").sum()),
        "de_overture": int((lugares["fuente"] == "overture").sum()),
        "por_tipo": {t: int(n) for t, n in lugares["tipo"].value_counts().sort_index().items()},
        "polos_con_lugares": len(por_polo),
        "polos_con_5_o_mas": int((por_polo >= 5).sum()),
    }
    (a.salida / "noche_resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"{len(lugares)} lugares en {len(por_polo)} polos ({int((por_polo >= 5).sum())} con 5 o más): "
        f"{int((lugares['fuente'] == 'osm').sum())} de OSM, {int((lugares['fuente'] == 'overture').sum())} de "
        f"Overture; escrito en {a.salida / 'noche_lugares.csv'}"
    )
    print(lugares["tipo"].value_counts().to_string())


if __name__ == "__main__":
    main()
