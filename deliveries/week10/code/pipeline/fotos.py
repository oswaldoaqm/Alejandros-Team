"""
Qué foto va con cada lugar del inventario y con cada pueblo donde se duerme.

Las fotos son de Wikimedia Commons y se encuentran a través de Wikidata: un lugar del
inventario de MINCETUR y un elemento de Wikidata son el mismo si están cerca y se llaman
parecido. Lo baja ``pipeline/adquisicion/descargar_fotos.py``; este módulo solo decide, así
que se prueba sin la red.

Cómo se decide
--------------
- Los nombres se comparan en una forma canónica que junta las grafías del quechua y del
  castellano: «Huarihuilca» y «Wariwillka», «Qorikancha» y «Coricancha», «Cuélap» y
  «Kuélap» quedan iguales.
- Cuenta lo que distingue al lugar, no su clase: en «Santuario Arqueológico de Wariwillka»
  cuenta «Wariwillka». Las palabras de clase (iglesia, plaza, museo, laguna…) solo impiden
  mezclar: si los dos nombres tienen clase, tiene que ser de la misma familia. Una iglesia
  no es la foto de una plaza; templo, capilla y catedral sí son de la misma familia.
- Un lugar acepta un elemento a menos de 2,5 km si todo lo que lo distingue aparece en el
  nombre del elemento, o a menos de 1 km si aparece la mitad o más; y el elemento no puede ser
  sobre otra cosa: más de la mitad de lo que distingue al elemento tiene que estar en el lugar
  («Mercado Viejo de Huánuco» no es la «Plaza de Armas de Huánuco»). Un nombre hecho solo de
  clase («Plaza de Armas») exige que el elemento se llame igual, o igual y algo más («Plaza de
  Armas de Concepción»), a menos de 400 m. Una reserva, un lago o una cordillera con el mismo
  nombre pueden estar a 30 km: su punto en el mapa es uno de tantos.
- Una batalla o una pintura tienen coordenadas, pero no son la foto de un lugar.
- Un pueblo, un distrito o una provincia no es la foto de un lugar: la foto de Huancayo no
  sirve para la Catedral de Huancayo. Sí lo es de la base del polo que se llama igual, a
  menos de 10 km.
- De las fotos que pasan gana la del elemento que más se parece y está más cerca; de sus
  fotos, la apaisada más grande. Solo JPEG con licencia libre, y con autor salvo que sea de
  dominio público.
- El autor se publica como se va a leer junto a la foto: sin los restos de la wiki con que
  Commons lo guarda («User:», «No machine-readable author provided…»). «Trabajo propio» o
  «Unknown author» no nombran a nadie: una foto así solo sirve si es de dominio público.
- Si Wikidata no da ninguna, a una base o a un imperdible le sirve una foto de Commons con
  coordenadas a menos de 2 km de la base o de 2,5 km del imperdible, cuyo nombre trae todo lo
  que distingue al lugar: «Catarata El León - panoramio.jpg» para la Catarata El León. Si el
  imperdible tiene clase, el nombre de la foto tiene que traer una de la misma familia: el
  «Restaurante El León» de al lado no es la catarata. De esas gana la apaisada, la más cercana.
- ``pipeline/referencia/fotos_revisadas.csv`` corrige a mano lo que la regla no ve: quita la
  foto que eligió, o pone otra.

Las cifras (2,5 km, 1 km, 400 m, 10 km) son supuestos del producto, no mediciones.

Uso:     python -m pipeline.fotos        (después de pipeline/adquisicion/descargar_fotos.py)
Salida:  app/public/fotos.json, que la app pide cuando muestra un viaje
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXTERNOS = RAIZ / "data" / "externos" / "fotos"
DATOS = RAIZ / "dreemgo" / "datos"
REVISADAS = RAIZ / "pipeline" / "referencia" / "fotos_revisadas.csv"
CERCA = EXTERNOS / "cerca_en_commons.json"
CAMPOS_REVISADAS = ["tipo", "clave", "archivo", "motivo"]
SALIDA = RAIZ / "app" / "public" / "fotos.json"

RADIO_TODO_KM = 2.5  # todo lo que distingue al lugar aparece en el elemento
RADIO_MITAD_KM = 1.0  # aparece la mitad o más
RADIO_SOLO_CLASE_KM = 0.4  # «Plaza de Armas»: el mismo nombre, casi en el mismo punto
RADIO_BASE_KM = 10.0
RADIO_NATURAL_KM = 30.0  # una reserva, un valle o una cordillera: su punto puede caer lejos del otro
ANCHO_MINIMO = 640  # una foto más chica se ve borrosa en la portada de un viaje

VACIAS = {"de", "del", "la", "las", "el", "los", "y", "e", "en", "a", "al", "o", "u", "con", "por"}
VACIAS |= {"the", "of", "and"}

# Palabras de clase, por familia. Una palabra puede estar en dos familias (un templo puede ser
# una iglesia o un sitio arqueológico); las que no tienen familia no impiden nada.
FAMILIAS_EN_CLARO = {
    "religioso": "iglesia templo capilla catedral basilica santuario convento monasterio parroquia ermita",
    "plaza": "plaza plazuela parque alameda paseo malecon ovalo jardin bulevar boulevard",
    "museo": "museo casa casona palacio hacienda galeria sala",
    "arqueologico": "sitio complejo zona arqueologico arqueologica ruinas restos fortaleza ciudadela huaca templo",
    "agua": "laguna lago rio catarata cascada caida aguas termales banos fuente pozas cocha manantial oasis",
    "montana": "cerro nevado montana volcan cordillera abra apu pico cumbre",
    "naturaleza": "bosque valle canon cueva gruta caverna bahia isla peninsula desierto dunas lomas mirador",
    "playa": "playa balneario caleta bahia",
    "protegida": "reserva santuario parque nacional area",
    "puente": "puente",
    "monumento": "monumento estatua escultura obelisco",
    "cementerio": "cementerio mausoleo camposanto",
    "puerto": "muelle puerto embarcadero",
    "calle": "calle jiron avenida pasaje",
    "ciudad": "centrohistorico ciudad pueblo barrio",
    "edificio": (
        "municipalidad edificio inmueble hotel hostal colegio escuela universidad hospital teatro biblioteca "
        "banco club casino estadio coliseo cine aeropuerto"
    ),
}
# El centro histórico de una ciudad se puede mostrar con su plaza principal.
AFINES = {frozenset({"ciudad", "plaza"})}
# Las familias de los lugares grandes, cuyo punto en un mapa es solo uno de tantos.
NATURALES = {"protegida", "montana", "naturaleza", "agua"}
SIN_FAMILIA_EN_CLARO = (
    "nacional regional municipal natural historico historica monumental colonial antiguo antigua tradicional "
    "turistico turistica centro san santa santo senor senora nuestra virgen mercado estacion torre faro armas "
    "comercial hotelero sagrada sagrado real gran grande"
)
# Frases que son una sola clase: «centro histórico» no es un museo histórico.
FRASES = {"centro historico": "centrohistorico", "casco historico": "centrohistorico", "campo santo": "camposanto"}
# Tipos de Wikidata que no son un lugar que se visita: una batalla, una pintura.
NO_ES_LUGAR = re.compile(r"\b(battle|siege|war|conflict|massacre|earthquake|event|election|human|painting|film)\b")

# Los tipos de Wikidata que son lugares poblados o divisiones administrativas.
POBLADO_EXACTO = {
    "city",
    "town",
    "village",
    "human settlement",
    "big city",
    "capital city",
    "national capital",
    "provincial capital",
    "regional capital",
    "municipality",
    "neighborhood",
    "neighbourhood",
    "hamlet",
    "populated place",
    "locality",
    "urban area",
    "rural area",
    "census-designated place",
    "metropolis",
    "megacity",
    "million city",
}
POBLADO_PREFIJO = re.compile(r"^(district|province|region|department|municipality|commune|capital) of ")

# Lo que no es una foto del lugar aunque esté en su ficha de Wikidata: un collage, un mapa, un escudo.
NO_ES_FOTO = re.compile(
    r"collage|mosaico|montage|montaje|\bmapa?\b|locator|ubicaci|escudo|coat of arms|bandera|flag|logo", re.IGNORECASE
)
# Una región entera no es la foto del pueblo donde se duerme.
REGION = re.compile(r"^(department|region|state) of ")

LICENCIA_LIBRE = re.compile(
    r"^(cc0( 1\.0)?|cc by(-sa)?( \d\.\d)?( [a-z]{2,3})?|public domain|pd.*|attribution)$", re.IGNORECASE
)
DOMINIO_PUBLICO = re.compile(r"^(cc0|public domain|pd)", re.IGNORECASE)

# Lo que Commons pone de autor cuando quien subió la foto no dijo quién la hizo.
SIN_AUTOR = re.compile(
    r"^(own work|self(-made)?|trabajo propio|obra propia|foto propia|elaboraci[oó]n propia"
    r"|(unknown( author)?\s*)+|autor desconocido|desconocido|an[oó]nimo|anonymous)\.?$",
    re.IGNORECASE,
)
SUPUESTO = re.compile(r"No machine-readable author provided\.\s*(.+?)\s+assumed \(based on copyright claims\)")


# ───────────────────────────── nombres ─────────────────────────────


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def canonico(palabra: str) -> str:
    """Una palabra (en minúsculas y sin tildes) en la grafía común a quechua y castellano."""
    p = palabra.replace("x", "j")  # Xauxa → Jauja: la x antigua sonaba como j
    p = re.sub(r"(?<!c)hu(?=[aeio])", "w", p)  # Huarihuilca → Wariwilca; «chua» no cambia
    p = re.sub(r"gu(?=a)", "w", p)
    p = re.sub(r"qu(?=[ei])", "k", p)
    p = p.replace("q", "k")  # Qorikancha → Korikancha
    p = re.sub(r"c(?![eih])", "k", p)  # ca, co, cu y c antes de consonante → k; «ch» no cambia
    p = re.sub(r"c(?=[ei])", "s", p)
    p = p.replace("z", "s").replace("v", "b")
    p = re.sub(r"(?<!c)h", "", p)  # la h muda; la de «ch» se queda
    p = p.replace("ll", "l").replace("y", "i")
    return re.sub(r"(.)\1+", r"\1", p)  # letras dobles


def palabras(nombre: str) -> list[str]:
    """Las palabras de un nombre, canónicas y sin las vacías («de», «la», «y»…)."""
    texto = re.sub(r"[^a-z0-9]+", " ", sin_tildes(nombre.lower()))
    for frase, junta in FRASES.items():
        texto = re.sub(rf"\b{frase}\b", junta, texto)
    return [canonico(p) for p in texto.split() if p not in VACIAS]


FAMILIAS: dict[str, set[str]] = {}
for _familia, _lista in FAMILIAS_EN_CLARO.items():
    for _palabra in _lista.split():
        FAMILIAS.setdefault(canonico(_palabra), set()).add(_familia)
CLASES = set(FAMILIAS) | {canonico(p) for p in SIN_FAMILIA_EN_CLARO.split()}


def singular(palabra: str) -> str:
    """La palabra de clase en singular («huacas» → «huaca», «lagunas» → «laguna»), si lo es."""
    for corte in ("", "s", "es"):
        if palabra.endswith(corte) and palabra[: len(palabra) - len(corte)] in CLASES:
            return palabra[: len(palabra) - len(corte)]
    return palabra


@dataclass(frozen=True)
class Nombre:
    """Un nombre partido en lo que distingue al lugar y su clase."""

    propias: tuple[str, ...]
    familias: frozenset[str]
    completo: str

    @classmethod
    def de(cls, nombre: str) -> Nombre:
        todas = [singular(p) for p in palabras(nombre)]
        propias = tuple(p for p in todas if p not in CLASES and (len(p) >= 3 or p.isdigit()))
        familias = frozenset(f for p in todas for f in FAMILIAS.get(p, ()))
        return cls(propias, familias, " ".join(todas))


def coincide(a: str, b: str) -> bool:
    """Dos palabras iguales, o casi iguales si son largas (una letra de diferencia)."""
    return a == b or (min(len(a), len(b)) >= 5 and SequenceMatcher(None, a, b).ratio() >= 0.86)


def cobertura(lugar: Nombre, otro: Nombre) -> float:
    """Qué parte de lo que distingue a `lugar` aparece en `otro`."""
    if not lugar.propias:
        return 0.0
    return sum(any(coincide(p, q) for q in otro.propias) for p in lugar.propias) / len(lugar.propias)


def compatibles(a: Nombre, b: Nombre) -> bool:
    """Si los dos tienen clase, comparten familia (o son afines: un centro histórico y su plaza)."""
    if not a.familias or not b.familias or a.familias & b.familias:
        return True
    return any(frozenset({x, y}) in AFINES for x in a.familias for y in b.familias)


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rad = math.pi / 180
    dlat, dlon = (lat2 - lat1) * rad, (lon2 - lon1) * rad
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(min(1.0, math.sqrt(h)))


# ───────────────────────────── qué elemento es cuál ─────────────────────────────


def no_es_lugar(elemento: dict, tipos: dict[str, dict]) -> bool:
    """Una batalla o una pintura tienen coordenadas, pero no son un lugar que se visita."""
    return any(NO_ES_LUGAR.search((tipos.get(q) or {}).get("en", "").lower()) for q in elemento.get("tipos", []))


def es_poblado(elemento: dict, tipos: dict[str, dict]) -> bool:
    """Si el elemento es un lugar poblado o una división administrativa, por su tipo."""
    for qid in elemento.get("tipos", []):
        nombre = (tipos.get(qid) or {}).get("en", "").lower()
        if nombre in POBLADO_EXACTO or POBLADO_PREFIJO.match(nombre):
            return True
    return False


def es_region(elemento: dict, tipos: dict[str, dict]) -> bool:
    return any(REGION.match((tipos.get(q) or {}).get("en", "").lower()) for q in elemento.get("tipos", []))


def nombres_de(elemento: dict) -> list[Nombre]:
    return [Nombre.de(n) for n in [elemento.get("nombre", ""), elemento.get("nombre_en", ""), *elemento["otros"]] if n]


def parecido(lugar: Nombre, elemento: dict, distancia: float) -> float | None:
    """Qué tanto se parece el elemento al lugar (0 a 1), o None si no puede ser él."""
    mejor = None
    for otro in nombres_de(elemento):
        if not compatibles(lugar, otro):
            continue
        if not lugar.propias:
            # «Plaza de Armas» es la «Plaza de Armas de Concepción» que está ahí mismo.
            mismo = otro.completo == lugar.completo or otro.completo.startswith(lugar.completo + " ")
            if mismo and distancia <= RADIO_SOLO_CLASE_KM:
                mejor = 1.0
            continue
        c = cobertura(lugar, otro)
        # El elemento tampoco puede ser sobre otra cosa: «Mercado Viejo de Huánuco» no es la
        # «Plaza de Armas de Huánuco», aunque compartan «Huánuco».
        if otro.propias and cobertura(otro, lugar) <= 0.5:
            continue
        larga = any(len(p) >= 4 and any(coincide(p, q) for q in otro.propias) for p in lugar.propias)
        natural = bool(lugar.familias & NATURALES and otro.familias & NATURALES)
        radio = RADIO_NATURAL_KM if natural and c == 1 and cobertura(otro, lugar) == 1 else RADIO_TODO_KM
        if (c == 1 and distancia <= radio) or (c >= 0.5 and larga and distancia <= RADIO_MITAD_KM):
            mejor = max(mejor or 0.0, c)
    return mejor


def es_pueblo(recurso: dict) -> bool:
    """Los recursos que son un pueblo entero sí pueden llevar la foto del pueblo."""
    clase = sin_tildes(f"{recurso.get('tipo', '')} {recurso.get('subtipo', '')}".lower())
    nombre = sin_tildes(recurso.get("nombre", "").lower())
    return "pueblo" in clase or "ciudad" in clase or nombre.startswith(("pueblo ", "ciudad "))


def candidatos_del_lugar(recurso: dict, elementos: list[dict], tipos: dict[str, dict]) -> list[tuple]:
    """Los elementos que pueden ser el recurso, del más parecido y cercano al menos."""
    lugar = Nombre.de(recurso["nombre"])
    salida = []
    for e in elementos:
        d = km(recurso["lat"], recurso["lon"], e["lat"], e["lon"])
        if d > RADIO_NATURAL_KM or no_es_lugar(e, tipos) or (es_poblado(e, tipos) and not es_pueblo(recurso)):
            continue
        p = parecido(lugar, e, d)
        if p is not None:
            salida.append((-p, round(d, 2), -e.get("enlaces", 0), e["qid"], e))
    return [fila[-1] for fila in sorted(salida, key=lambda f: f[:4])]


def candidatos_de_la_base(base: dict, elementos: list[dict], tipos: dict[str, dict]) -> list[dict]:
    """Los pueblos que se llaman como la base, del mismo nombre exacto y más conocido primero."""
    nombre = Nombre.de(base["nombre"])
    salida = []
    for e in elementos:
        d = km(base["lat"], base["lon"], e["lat"], e["lon"])
        if d > RADIO_BASE_KM or not es_poblado(e, tipos) or es_region(e, tipos):
            continue
        otros = nombres_de(e)
        if not any(cobertura(nombre, o) == 1 for o in otros):
            continue
        exacto = any(o.completo == nombre.completo for o in otros)
        salida.append((not exacto, -e.get("enlaces", 0), round(d, 2), e["qid"], e))
    return [fila[-1] for fila in sorted(salida, key=lambda f: f[:4])]


# ───────────────────────────── qué foto ─────────────────────────────


def autor_legible(texto: str | None) -> str:
    """El autor como se lee junto a la foto. Commons lo guarda tal como lo escribió quien la
    subió, con restos de su wiki: «No machine-readable author provided. Xauxa assumed (based on
    copyright claims).» es Xauxa; «User:Pedro Felipe» es Pedro Felipe. Lo que no nombra a nadie
    («Trabajo propio», «Unknown author») queda vacío: esa foto no tiene a quién atribuirse."""
    autor = texto or ""
    supuesto = SUPUESTO.search(autor)
    if supuesto:
        autor = supuesto.group(1)
    autor = re.sub(r"\[\[[^\]]*\]\]", "", autor)  # «Y. Hooker[[User:|Hookery]]»
    autor = re.sub(r"^credit:\s*", "", autor, flags=re.IGNORECASE)
    autor = re.sub(r"^photo courtesy of\s+", "", autor, flags=re.IGNORECASE)
    autor = re.sub(r"\s+-\s+uploaded\b.*$", "", autor, flags=re.IGNORECASE)  # «… - uploaded with permission by…»
    autor = re.sub(r"^(the\s+)?original uploader was\s+", "", autor, flags=re.IGNORECASE)
    # «Ericbronder at English Wikipedia», «Acatenazzi at en.wikipedia ( Original text: … )»
    autor = re.sub(r"\s+at\s+(\w+\s+wikipedia|[a-z-]{2,12}\.wikipedia)\b.*$", "", autor, flags=re.IGNORECASE)
    autor = re.sub(r"\b(?:[a-z]{2,3}:)?(?:user|usuario)\s*:\s*", "", autor, flags=re.IGNORECASE)
    autor = re.sub(r"\(\s+", "(", autor)
    autor = re.sub(r"\s+\)", ")", autor)
    autor = re.sub(r"\s+", " ", autor).strip()
    return "" if SIN_AUTOR.match(autor) else autor


def libre(meta: dict | None, archivo: str = "") -> bool:
    """Una foto (no un mapa ni un collage) en JPEG, con licencia libre, y con autor salvo que
    sea de dominio público."""
    if not meta or meta.get("tipo") != "image/jpeg" or (meta.get("ancho") or 0) < ANCHO_MINIMO:
        return False
    if NO_ES_FOTO.search(archivo):
        return False
    licencia = meta.get("licencia", "").strip()
    if not LICENCIA_LIBRE.match(licencia):
        return False
    return bool(autor_legible(meta.get("autor"))) or bool(DOMINIO_PUBLICO.match(licencia))


def ruta_en_commons(archivo: str) -> str:
    """La carpeta de un archivo en upload.wikimedia.org: «b/bb», de la huella MD5 de su nombre."""
    h = hashlib.md5(archivo.replace(" ", "_").encode("utf-8")).hexdigest()
    return f"{h[0]}/{h[:2]}"


def foto(archivo: str, meta: dict, qid: str) -> dict:
    return {
        "archivo": archivo,
        "ruta": ruta_en_commons(archivo),
        "ancho": meta["ancho"],
        "alto": meta["alto"],
        "autor": autor_legible(meta.get("autor")),
        "licencia": meta["licencia"],
        "url_licencia": meta.get("url_licencia", ""),
        "wikidata": qid,
    }


def mejor_foto(elementos: list[dict], metadatos: dict) -> dict | None:
    """La primera foto libre de los elementos, en su orden; de un mismo elemento, la apaisada
    más grande."""
    for e in elementos:
        libres = [a for a in e["imagenes"] if libre(metadatos.get(a), a)]
        if libres:
            elegido = max(
                libres,
                key=lambda a: (
                    metadatos[a]["ancho"] >= metadatos[a]["alto"],
                    metadatos[a]["ancho"] * metadatos[a]["alto"],
                    a,
                ),
            )
            return foto(elegido, metadatos[elegido], e["qid"])
    return None


def titulo_de(archivo: str) -> str:
    """Lo que dice el nombre de un archivo de Commons, sin la extensión ni lo que agregan la
    cámara o la plataforma de donde vino: «IMG_1234», «DSC01234», « - panoramio (2)»."""
    t = re.sub(r"\.jpe?g$", "", archivo, flags=re.IGNORECASE).replace("_", " ")
    t = re.sub(r"\s*-\s*panoramio(\s*\(\d+\))?$", "", t, flags=re.IGNORECASE)
    return re.sub(r"\b(img|dsc|dscn|cimg|pict|p)\s*\d{3,}\b", " ", t, flags=re.IGNORECASE)


def de_commons(lugar: Nombre, archivos: list[dict], metadatos: dict, base: bool) -> dict | None:
    """La foto con coordenadas que muestra el lugar, cuando Wikidata no dio ninguna: su nombre
    trae todo lo que distingue al lugar y, si es un imperdible con clase, una clase de la misma
    familia. De esas, la apaisada más cercana."""
    if not lugar.propias:
        return None  # «Plaza de Armas»: cualquier plaza de la zona se llama así
    buenas = []
    for f in archivos:
        archivo, meta = f["archivo"], metadatos.get(f["archivo"])
        if not libre(meta, archivo):
            continue
        otro = Nombre.de(titulo_de(archivo))
        if cobertura(lugar, otro) < 1:
            continue
        if not base and lugar.familias and not (lugar.familias & otro.familias):
            continue
        buenas.append((meta["ancho"] < meta["alto"], f["m"], -meta["ancho"] * meta["alto"], archivo))
    if not buenas:
        return None
    elegido = min(buenas)[-1]
    return foto(elegido, metadatos[elegido], "")


def leer_revisadas(ruta: Path = REVISADAS) -> dict[tuple[str, str], str]:
    """Lo corregido a mano: (lugar|base, clave) → archivo, o "" si no lleva foto.

    Una fila mal escrita no se pasa por alto: un punto y coma de más en el motivo correría los
    campos, y una clave repetida dejaría valer solo la última."""
    if not ruta.exists():
        return {}
    revisadas: dict[tuple[str, str], str] = {}
    with open(ruta, encoding="utf-8", newline="") as fh:
        filas = csv.reader(fh, delimiter=";")
        if next(filas, None) != CAMPOS_REVISADAS:
            raise ValueError(f"{ruta.name}: la primera línea tiene que ser «{';'.join(CAMPOS_REVISADAS)}»")
        for linea, fila in enumerate(filas, 2):
            if not fila:
                continue
            campos = [c.strip() for c in fila]
            if len(campos) != 4 or campos[0] not in ("lugar", "base") or not campos[1] or not campos[3]:
                raise ValueError(f"{ruta.name}, línea {linea}: se esperaba «tipo;clave;archivo;motivo» y dice {fila}")
            if (campos[0], campos[1]) in revisadas:
                raise ValueError(f"{ruta.name}, línea {linea}: {campos[0]} {campos[1]} ya estaba más arriba")
            revisadas[(campos[0], campos[1])] = campos[2]
    return revisadas


def sin_efecto(revisadas: dict[tuple[str, str], str], metadatos: dict) -> list[tuple[str, str, str]]:
    """Las correcciones que ponen una foto que no se puede usar: sus datos no se descargaron, o
    no es libre. Ese lugar se queda sin foto, así que hay que decirlo."""
    return sorted((tipo, clave, a) for (tipo, clave), a in revisadas.items() if a and not libre(metadatos.get(a)))


def elegir(
    recursos: list[dict],
    polos: list[dict],
    elementos: list[dict],
    tipos: dict[str, dict],
    metadatos: dict,
    revisadas: dict[tuple[str, str], str],
    cerca: dict[str, list[dict]] | None = None,
) -> dict:
    """Las fotos de los lugares que pueden ser parada y de las bases. `cerca` son las fotos de
    Commons con coordenadas cerca de cada base e imperdible («base:<polo>», «lugar:<código>»)."""
    cerca = cerca or {}
    lugares, bases = {}, {}
    for r in recursos:
        if not r.get("es_parada"):
            continue
        clave = ("lugar", r["codigo"])
        if clave in revisadas:
            archivo = revisadas[clave]
            if archivo and libre(metadatos.get(archivo)):
                lugares[r["codigo"]] = foto(archivo, metadatos[archivo], "")
            continue
        elegida = mejor_foto(candidatos_del_lugar(r, elementos, tipos), metadatos)
        if not elegida:
            elegida = de_commons(Nombre.de(r["nombre"]), cerca.get(f"lugar:{r['codigo']}", []), metadatos, False)
        if elegida:
            lugares[r["codigo"]] = elegida
    for p in polos:
        clave = ("base", str(p["id"]))
        if clave in revisadas:
            archivo = revisadas[clave]
            if archivo and libre(metadatos.get(archivo)):
                bases[str(p["id"])] = foto(archivo, metadatos[archivo], "")
            continue
        elegida = mejor_foto(candidatos_de_la_base(p["base"], elementos, tipos), metadatos)
        if not elegida:
            elegida = de_commons(Nombre.de(p["base"]["nombre"]), cerca.get(f"base:{p['id']}", []), metadatos, True)
        if elegida:
            bases[str(p["id"])] = elegida
    return {"lugares": lugares, "bases": bases}


# ───────────────────────────── archivos ─────────────────────────────


def leer_gz(ruta: Path):
    return json.loads(gzip.decompress(ruta.read_bytes()))


def leer_elementos() -> list[dict]:
    vistos: dict[str, dict] = {}
    for archivo in sorted((EXTERNOS / "wikidata").glob("*.json")):
        for e in json.loads(archivo.read_text(encoding="utf-8"))["elementos"]:
            vistos[e["qid"]] = e
    return list(vistos.values())


def main() -> None:
    ap = argparse.ArgumentParser(description="Elige la foto de cada lugar y de cada base.")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()

    recursos = leer_gz(DATOS / "recursos.json.gz")
    polos = leer_gz(DATOS / "polos.json.gz")
    manifiesto = json.loads((DATOS / "manifiesto.json").read_text(encoding="utf-8"))
    elementos = leer_elementos()
    tipos = json.loads((EXTERNOS / "tipos.json").read_text(encoding="utf-8"))
    metadatos = json.loads((EXTERNOS / "commons.json").read_text(encoding="utf-8"))
    cerca = json.loads(CERCA.read_text(encoding="utf-8")) if CERCA.exists() else {}

    revisadas = leer_revisadas()
    elegidas = elegir(recursos, polos, elementos, tipos, metadatos, revisadas, cerca)
    salida = {
        "version_datos": manifiesto.get("version_datos", ""),
        "fuente": "Wikimedia Commons, a través de Wikidata o de las coordenadas de cada foto",
        **elegidas,
    }
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(salida, ensure_ascii=False, sort_keys=True, separators=(",", ":")), "utf-8")

    paradas = [r for r in recursos if r.get("es_parada")]
    altas = [r for r in paradas if (r.get("jerarquia") or 0) >= 3]
    con_foto = elegidas["lugares"]
    print(f"Paradas con foto: {len(con_foto)} de {len(paradas)}")
    print(f"  de jerarquía 3 o 4: {sum(r['codigo'] in con_foto for r in altas)} de {len(altas)}")
    print(f"Bases con foto: {len(elegidas['bases'])} de {len(polos)}")
    puestas = sum(1 for archivo in revisadas.values() if archivo)
    print(f"Corregidas a mano: {len(revisadas)} ({puestas} con otra foto, {len(revisadas) - puestas} sin foto)")
    print(f"{a.salida.relative_to(RAIZ)}: {a.salida.stat().st_size / 1024:.0f} KB")
    faltan = sin_efecto(revisadas, metadatos)
    if faltan:
        print(f"\nOjo: {len(faltan)} correcciones ponen una foto cuyos datos no están o que no es libre.")
        print("Esos lugares quedan sin foto. Si falta descargar: python pipeline/adquisicion/descargar_fotos.py")
        for tipo, clave, archivo in faltan:
            print(f"  {tipo} {clave}: {archivo}")


if __name__ == "__main__":
    main()
