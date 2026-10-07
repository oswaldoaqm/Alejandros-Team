"""
Fotos de los lugares y de los pueblos donde se duerme, desde Wikidata y Wikimedia Commons.

Qué baja
--------
1. De Wikidata, todo lo que tiene coordenadas y foto (la propiedad P18, «imagen») cerca de
   donde el motor puede llevar al viajero: en cada celda de 1° × 1° con una parada o una
   base. Con su nombre en español y en inglés, sus otros nombres en español, de qué tipo es
   (P31) y en cuántas Wikipedias aparece. Con eso, ``pipeline/fotos.py`` decide qué foto va
   con qué lugar.
2. De Wikidata, el nombre de cada tipo (P31) que aparece: con él se reconoce un pueblo, un
   distrito o una provincia, que no son la foto de un lugar.
3. De Wikimedia Commons, el autor, la licencia y el tamaño de cada foto de lo que quedó a
   menos de 3 km de una parada o a menos de 10 km de una base: lo que la licencia exige para
   mostrarla, y lo que hace falta para pedir una miniatura del tamaño justo. También los de
   las fotos que la revisión a mano puso en ``pipeline/referencia/fotos_revisadas.csv``,
   vengan de donde vengan en Commons.

No baja las fotos: la app las pide a Wikimedia, del tamaño que necesita cada pantalla.

Buenas prácticas
----------------
Wikimedia corta a quien le pide rápido (responde 429). El script pide de a uno, con una
pausa entre pedidos y un agente que identifica al proyecto, y respeta el ``Retry-After``
cuando lo hay. A Commons le pide los archivos de a 50.

Salida (fuera de git; lo que entra al repositorio lo arma ``python -m pipeline.fotos``)
  data/externos/fotos/wikidata/<celda>.json   lo de Wikidata en cada celda
  data/externos/fotos/tipos.json              el nombre en inglés y en español de cada tipo
  data/externos/fotos/commons.json            autor, licencia y tamaño de cada archivo

Licencias: los datos de Wikidata son CC0. Cada foto de Commons tiene la suya (CC BY, CC
BY-SA, dominio público…) y su autor; la app muestra ambos junto a la foto.

Uso
  python pipeline/adquisicion/descargar_fotos.py            # baja lo que falta; si se corta, retoma
  python pipeline/adquisicion/descargar_fotos.py --rehacer  # vuelve a pedir todo
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import math
import re
import time
from pathlib import Path
from urllib.parse import unquote

import requests

from _comun import AGENTE, EXTERNOS, RAIZ, ahora_utc, escribir_json, miles, utf8_consola

SPARQL = "https://query.wikidata.org/sparql"
COMMONS = "https://commons.wikimedia.org/w/api.php"
DIR = EXTERNOS / "fotos"
CELDAS = DIR / "wikidata"
METADATOS = DIR / "commons.json"
TIPOS = DIR / "tipos.json"

DATOS = RAIZ / "dreemgo" / "datos"
REVISADAS = RAIZ / "pipeline" / "referencia" / "fotos_revisadas.csv"
CERCA_DE_PARADA_KM = 3.0
CERCA_DE_BASE_KM = 10.0
PAUSA_S = 1.5  # entre pedidos a Wikidata
PAUSA_COMMONS_S = 3.0  # Commons corta antes que Wikidata
LOTE = 50  # archivos por pedido a Commons: el máximo que acepta sin cuenta

CONSULTA = """
SELECT ?item (SAMPLE(?es) AS ?nombre) (SAMPLE(?en) AS ?nombre_en) (SAMPLE(?coord) AS ?coord)
       (GROUP_CONCAT(DISTINCT ?imagen; separator="|") AS ?imagenes)
       (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?otros)
       (GROUP_CONCAT(DISTINCT ?tipo; separator=" ") AS ?tipos)
       (SAMPLE(?enlaces) AS ?enlaces) WHERE {
  SERVICE wikibase:box {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerSouthWest "Point(%(oeste)s %(sur)s)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerNorthEast "Point(%(este)s %(norte)s)"^^geo:wktLiteral .
  }
  ?item wdt:P18 ?imagen .
  OPTIONAL { ?item rdfs:label ?es . FILTER(LANG(?es) = "es") }
  OPTIONAL { ?item rdfs:label ?en . FILTER(LANG(?en) = "en") }
  OPTIONAL { ?item skos:altLabel ?alt . FILTER(LANG(?alt) = "es") }
  OPTIONAL { ?item wdt:P31 ?tipo . }
  OPTIONAL { ?item wikibase:sitelinks ?enlaces . }
} GROUP BY ?item
"""


# ───────────────────────────── dónde buscar ─────────────────────────────


def leer_puntos() -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Las paradas y las bases de los artefactos del motor: (lat, lon)."""
    recursos = json.loads(gzip.decompress((DATOS / "recursos.json.gz").read_bytes()))
    polos = json.loads(gzip.decompress((DATOS / "polos.json.gz").read_bytes()))
    paradas = [(r["lat"], r["lon"]) for r in recursos if r.get("es_parada")]
    bases = [(p["base"]["lat"], p["base"]["lon"]) for p in polos]
    return paradas, bases


def celdas(puntos: list[tuple[float, float]], margen: float = 0.1) -> list[tuple[int, int]]:
    """Las celdas de 1° que tocan los puntos. Un punto a menos de `margen` grados del borde
    también trae la celda vecina: lo que está al otro lado del borde puede ser lo suyo."""
    salida = set()
    for lat, lon in puntos:
        for dlat in (-margen, 0, margen):
            for dlon in (-margen, 0, margen):
                salida.add((math.floor(lat + dlat), math.floor(lon + dlon)))
    return sorted(salida)


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    rad = math.pi / 180
    dlat, dlon = (b[0] - a[0]) * rad, (b[1] - a[1]) * rad
    h = math.sin(dlat / 2) ** 2 + math.cos(a[0] * rad) * math.cos(b[0] * rad) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(min(1.0, math.sqrt(h)))


# ───────────────────────────── pedidos ─────────────────────────────


def pedir(sesion: requests.Session, metodo: str, url: str, **kw) -> requests.Response:
    """Un pedido con paciencia: ante 429 o un error del servidor espera (lo que diga
    `Retry-After`, o cada vez más) y vuelve a intentar, hasta cinco veces."""
    espera = 10.0
    for intento in range(1, 6):
        try:
            r = sesion.request(metodo, url, timeout=(20, 120), **kw)
        except (requests.ConnectionError, requests.Timeout) as e:
            print(f"  la red falló ({type(e).__name__}); espero {espera:.0f} s", flush=True)
        else:
            if r.status_code == 200 and not r.text.lstrip().startswith("You are making too many"):
                return r
            pide = r.headers.get("Retry-After", "")
            if pide.isdigit():
                espera = max(espera, float(pide))
            print(f"  respuesta {r.status_code} (intento {intento}); espero {espera:.0f} s", flush=True)
        time.sleep(espera)
        espera = min(espera * 2, 300)
    raise RuntimeError(f"{url} no respondió después de cinco intentos")


def leer_celda(fila: dict) -> dict | None:
    """Una fila de la respuesta de Wikidata, en limpio."""
    valor = {k: v.get("value", "") for k, v in fila.items()}
    coord = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", valor.get("coord", ""))
    if not coord:
        return None
    imagenes = [
        unquote(i.rsplit("/", 1)[-1]).replace("_", " ") for i in valor.get("imagenes", "").split("|") if i.strip()
    ]
    return {
        "qid": valor["item"].rsplit("/", 1)[-1],
        "nombre": valor.get("nombre", ""),
        "nombre_en": valor.get("nombre_en", ""),
        "otros": [o for o in valor.get("otros", "").split("|") if o],
        "lat": float(coord.group(2)),
        "lon": float(coord.group(1)),
        "imagenes": imagenes,
        "tipos": [t.rsplit("/", 1)[-1] for t in valor.get("tipos", "").split() if t],
        "enlaces": int(valor.get("enlaces") or 0),
    }


def bajar_wikidata(sesion: requests.Session, lista: list[tuple[int, int]], rehacer: bool) -> list[dict]:
    CELDAS.mkdir(parents=True, exist_ok=True)
    elementos: dict[str, dict] = {}
    pendientes = [c for c in lista if rehacer or not (CELDAS / f"{c[0]}_{c[1]}.json").exists()]
    print(f"Wikidata: {len(lista)} celdas de 1°, {len(pendientes)} por pedir.", flush=True)
    for n, (lat, lon) in enumerate(lista, 1):
        archivo = CELDAS / f"{lat}_{lon}.json"
        if (lat, lon) in pendientes:
            consulta = CONSULTA % {"sur": lat, "oeste": lon, "norte": lat + 1, "este": lon + 1}
            filas = [f for f in (leer_celda(b) for b in consultar(sesion, consulta)) if f]
            escribir_json(archivo, {"celda": [lat, lon], "pedido": ahora_utc(), "elementos": filas})
            print(f"  [{n}/{len(lista)}] {lat}°, {lon}°: {len(filas)} con foto", flush=True)
            time.sleep(PAUSA_S)
        for e in json.loads(archivo.read_text(encoding="utf-8"))["elementos"]:
            elementos[e["qid"]] = e  # una celda vecina puede repetirlo
    return list(elementos.values())


def cerca(elementos: list[dict], paradas, bases) -> list[dict]:
    """Lo que queda a menos de 3 km de una parada o de 10 km de una base. Una grilla de
    0,1° evita medir contra cada punto."""
    grilla: dict[tuple[int, int], list[tuple[tuple[float, float], float]]] = {}
    for punto, radio in [(p, CERCA_DE_PARADA_KM) for p in paradas] + [(b, CERCA_DE_BASE_KM) for b in bases]:
        grilla.setdefault((math.floor(punto[0] * 10), math.floor(punto[1] * 10)), []).append((punto, radio))
    salida = []
    for e in elementos:
        celda = (math.floor(e["lat"] * 10), math.floor(e["lon"] * 10))
        vecinos = (
            g
            for dlat in range(-1, 2)
            for dlon in range(-1, 2)
            for g in grilla.get((celda[0] + dlat, celda[1] + dlon), [])
        )
        if any(km((e["lat"], e["lon"]), punto) <= radio for punto, radio in vecinos):
            salida.append(e)
    return salida


CONSULTA_TIPOS = """
SELECT ?t ?en ?es WHERE {
  VALUES ?t { VALORES }
  OPTIONAL { ?t rdfs:label ?en . FILTER(LANG(?en) = "en") }
  OPTIONAL { ?t rdfs:label ?es . FILTER(LANG(?es) = "es") }
}
"""


def consultar(sesion: requests.Session, consulta: str) -> list[dict]:
    """Una consulta SPARQL a Wikidata: las filas de la respuesta."""
    r = pedir(sesion, "POST", SPARQL, data={"query": consulta}, headers={"Accept": "application/sparql-results+json"})
    return r.json()["results"]["bindings"]


def bajar_tipos(sesion: requests.Session, qids: list[str], rehacer: bool) -> dict:
    """El nombre de cada tipo, de a 300 por consulta."""
    tipos: dict = {} if rehacer or not TIPOS.exists() else json.loads(TIPOS.read_text(encoding="utf-8"))
    faltan = [q for q in qids if q not in tipos]
    print(f"Tipos: {len(qids)}, {len(faltan)} por pedir.", flush=True)
    for i in range(0, len(faltan), 300):
        lote = faltan[i : i + 300]
        for b in consultar(sesion, CONSULTA_TIPOS.replace("VALORES", " ".join(f"wd:{q}" for q in lote))):
            tipos[b["t"]["value"].rsplit("/", 1)[-1]] = {
                "en": b.get("en", {}).get("value", ""),
                "es": b.get("es", {}).get("value", ""),
            }
        for q in lote:
            tipos.setdefault(q, {"en": "", "es": ""})
        escribir_json(TIPOS, tipos)
        time.sleep(PAUSA_S)
    return tipos


def texto_plano(fragmento: str) -> str:
    """El autor en Commons viene en HTML (un enlace a su página): queda el texto."""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", fragmento or "")
    return re.sub(r"\s+", " ", html.unescape(sin_etiquetas)).strip()


def puestas_a_mano(ruta: Path = REVISADAS) -> set[str]:
    """Los archivos que la revisión a mano puso en vez del que eligió la regla. Pueden no venir
    de ningún elemento de Wikidata cercano, y sin sus datos ``pipeline/fotos.py`` no los usa."""
    if not ruta.exists():
        return set()
    with open(ruta, encoding="utf-8", newline="") as fh:
        return {(f.get("archivo") or "").strip() for f in csv.DictReader(fh, delimiter=";")} - {""}


def bajar_commons(sesion: requests.Session, archivos: list[str], rehacer: bool) -> dict:
    metadatos: dict = {} if rehacer or not METADATOS.exists() else json.loads(METADATOS.read_text(encoding="utf-8"))
    faltan = [a for a in archivos if a not in metadatos]
    print(f"Commons: {miles(len(archivos))} archivos, {miles(len(faltan))} por pedir.", flush=True)
    for i in range(0, len(faltan), LOTE):
        lote = faltan[i : i + LOTE]
        r = pedir(
            sesion,
            "GET",
            COMMONS,
            params={
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "maxlag": "5",
                "prop": "imageinfo",
                "iiprop": "size|mime|extmetadata",
                "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|AttributionRequired|Copyrighted",
                "titles": "|".join(f"File:{a}" for a in lote),
            },
        )
        datos = r.json().get("query", {})
        # Commons normaliza los títulos (mayúscula inicial, espacios): se vuelve al nombre pedido.
        normal = {n["to"]: n["from"] for n in datos.get("normalized", [])}
        for pagina in datos.get("pages", []):
            pedido = normal.get(pagina["title"], pagina["title"]).removeprefix("File:")
            info = (pagina.get("imageinfo") or [None])[0]
            if pagina.get("missing") or not info:
                metadatos[pedido] = None  # borrado o renombrado en Commons
                continue
            meta = {k: (v or {}).get("value", "") for k, v in info.get("extmetadata", {}).items()}
            metadatos[pedido] = {
                "ancho": info.get("width"),
                "alto": info.get("height"),
                "tipo": info.get("mime", ""),
                "autor": texto_plano(meta.get("Artist", ""))[:120],
                "licencia": meta.get("LicenseShortName", ""),
                "url_licencia": meta.get("LicenseUrl", ""),
                "atribucion": meta.get("AttributionRequired", ""),
            }
        for a in lote:
            metadatos.setdefault(a, None)  # lo que Commons no devolvió cuenta como faltante
        escribir_json(METADATOS, metadatos)
        print(f"  {min(i + LOTE, len(faltan))}/{len(faltan)}", flush=True)
        time.sleep(PAUSA_COMMONS_S)
    return metadatos


def main() -> None:
    utf8_consola()
    ap = argparse.ArgumentParser()
    ap.add_argument("--rehacer", action="store_true", help="vuelve a pedir todo, aunque ya esté")
    a = ap.parse_args()

    paradas, bases = leer_puntos()
    sesion = requests.Session()
    sesion.headers["User-Agent"] = AGENTE
    elementos = bajar_wikidata(sesion, celdas(paradas + bases), a.rehacer)
    utiles = cerca(elementos, paradas, bases)
    a_mano = puestas_a_mano()
    archivos = sorted({i for e in utiles for i in e["imagenes"]} | a_mano)
    print(f"{miles(len(elementos))} elementos con foto; {miles(len(utiles))} cerca de una parada o una base.")
    print(f"{len(a_mano)} fotos puestas a mano en {REVISADAS.relative_to(RAIZ)}.")
    bajar_tipos(sesion, sorted({t for e in utiles for t in e["tipos"]}), a.rehacer)
    metadatos = bajar_commons(sesion, archivos, a.rehacer)
    libres = sum(1 for m in metadatos.values() if m and m["licencia"])
    print(f"Listo: {miles(libres)} fotos con autor y licencia en {Path(METADATOS).relative_to(RAIZ)}.")


if __name__ == "__main__":
    main()
