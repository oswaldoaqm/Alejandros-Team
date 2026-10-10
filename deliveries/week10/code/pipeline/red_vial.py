"""
Red vial del Perú desde OpenStreetMap, con el tren y los botes encima, y tiempos de viaje.

Reemplaza la fórmula de semanas anteriores (línea recta × 1,6 a 32,5 km/h, nunca
calibrada) por rutas sobre las vías reales. Ver docs/decisiones/0007-red-vial-propia.md.

1. ``leer_red`` convierte el extracto de Geofabrik en un grafo: un vértice por cruce o
   extremo de vía, una arista por tramo entre cruces, con su largo, su clase (troncal,
   primaria… trocha), si es sin asfaltar y cuántas curvas tiene por kilómetro. Se guarda
   en data/externos/osm/red_vial.npz (fuera de git: se reconstruye en un minuto).
   Encima de las vías van dos capas que no se cruzan con ellas: los trenes de pasajeros
   (las rutas ``route=train`` sin sus ramales mineros, y los rieles de uso turístico
   aunque OSM no les haya puesto ruta, como el tramo de Machu Picchu a la Hidroeléctrica)
   y los botes (los ferris de más de 3 km: el Titicaca, las Ballestas, los ríos de la
   Amazonía). Del tren se sube y se baja en una estación, y de un bote en cualquier punto de
   su ruta; los que quedan cerca de una vía se unen a ella por un trasbordo que cuesta
   minutos fijos.
2. Las velocidades por clase se calibran con los recorridos de acceso que publican las
   fichas oficiales (``pipeline/red_calibracion.py``).
3. Con la red calibrada se calculan los tiempos que usa el motor: de cada ciudad de
   origen a cada parada y a la base de cada polo, y entre las paradas de cada polo y su
   base (``pipeline/tiempos.py``).

La red y las tablas que salen de ella son obra derivada de OpenStreetMap (ODbL 1.0,
© colaboradores de OpenStreetMap).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Clases de vía que puede recorrer un bus o un auto. Las de enlace ("_link") van con su
# vía madre. "track" es la trocha carrozable; "service" son accesos a fundos, minas y
# recursos, sin los pasillos de estacionamiento.
CLASES = (
    "autopista",
    "troncal",
    "primaria",
    "secundaria",
    "terciaria",
    "local",
    "trocha",
    "balsa",
    "tren",
    "bote",
    "transbordo",
)
VIALES = CLASES[: CLASES.index("balsa") + 1]  # lo que recorre un auto o un bus
CAPAS = ("vial", "tren", "bote")  # cada vértice es de una
_CLASE_DE = {
    "motorway": "autopista",
    "motorway_link": "autopista",
    "trunk": "troncal",
    "trunk_link": "troncal",
    "primary": "primaria",
    "primary_link": "primaria",
    "secondary": "secundaria",
    "secondary_link": "secundaria",
    "tertiary": "terciaria",
    "tertiary_link": "terciaria",
    "unclassified": "local",
    "residential": "local",
    "living_street": "local",
    "road": "local",
    "service": "local",
    "track": "trocha",
}
CODIGO = {nombre: i for i, nombre in enumerate(CLASES)}
_SERVICIO_EXCLUIDO = {"parking_aisle", "drive-through", "emergency_access"}
_SIN_ACCESO = {"no", "private"}
SIN_ASFALTAR = {
    "unpaved",
    "ground",
    "compacted",
    "dirt",
    "gravel",
    "fine_gravel",
    "earth",
    "mud",
    "sand",
    "grass",
    "rock",
    "pebblestone",
    "gravel;ground",
    "salt",
}
BALSA_MAX_M = 3_000  # un ferry más largo que esto no es parte de la red vial: es un viaje en bote
TRAMO_MAX_M = 1_000  # las vías largas se parten cada kilómetro (ver _armar)
CONEXION_MAX_M = 1_000  # una estación o un muelle se une a la vía más cercana si está a menos de esto
_RIELES = {"rail", "narrow_gauge"}
_RIEL_TURISTICO = "tourism"  # usage: lleva pasajeros aunque no esté en una ruta de tren de OSM
_RIEL_EXCLUIDO = {"industrial", "military", "test"}  # usage: el tren minero no lleva pasajeros
_SERVICIO_RIEL_EXCLUIDO = {"yard", "siding", "spur", "crossover"}
_DESPLAZAMIENTO = {"tren": 10**12, "bote": 2 * 10**12}  # nodos de una capa: nunca coinciden con los de las vías
_NO_ES_TREN = {"subway", "light_rail", "monorail", "funicular", "tram"}  # station=…: el metro de Lima no es el tren
ESTACION_AL_LADO_M = 300  # una estación dibujada junto al riel se toma en el nodo del riel más cercano

RADIO_TIERRA_M = 6_371_008.8


@dataclass
class Red:
    """El grafo vial. Vértices y aristas en arreglos de numpy, en el mismo orden."""

    lat: np.ndarray  # float64, por vértice
    lon: np.ndarray
    desde: np.ndarray  # int32, por arista
    hasta: np.ndarray
    metros: np.ndarray  # float32
    clase: np.ndarray  # int8, índice en CLASES
    sin_asfaltar: np.ndarray  # bool
    curvas: np.ndarray  # float32, grados de giro por kilómetro
    capa: np.ndarray | None = None  # int8 por vértice, índice en CAPAS; None si todo es vial
    embarque: np.ndarray | None = None  # bool por vértice: estación o muelle; None si todo es vial
    fecha_osm: str = ""

    @property
    def vertices(self) -> int:
        return len(self.lat)

    @property
    def aristas(self) -> int:
        return len(self.desde)

    def guardar(self, ruta: Path) -> None:
        np.savez_compressed(
            ruta,
            lat=self.lat,
            lon=self.lon,
            desde=self.desde,
            hasta=self.hasta,
            metros=self.metros,
            clase=self.clase,
            sin_asfaltar=self.sin_asfaltar,
            curvas=self.curvas,
            capa=np.zeros(self.vertices, dtype=np.int8) if self.capa is None else self.capa,
            embarque=np.zeros(self.vertices, dtype=bool) if self.embarque is None else self.embarque,
            fecha_osm=np.array(self.fecha_osm),
        )

    def vial(self) -> Red:
        """Solo las vías, sin el tren, los botes ni sus trasbordos (para calibrar)."""
        if self.capa is None or not (self.capa > 0).any():
            return self
        n = int((self.capa == 0).sum())  # los vértices de las vías van primero (ver _unir)
        e = self.clase < len(VIALES)
        return Red(
            lat=self.lat[:n],
            lon=self.lon[:n],
            desde=self.desde[e],
            hasta=self.hasta[e],
            metros=self.metros[e],
            clase=self.clase[e],
            sin_asfaltar=self.sin_asfaltar[e],
            curvas=self.curvas[e],
            fecha_osm=self.fecha_osm,
        )

    @classmethod
    def cargar(cls, ruta: Path) -> Red:
        with np.load(ruta) as z:
            return cls(**{k: (str(z[k]) if k == "fecha_osm" else z[k]) for k in z.files})


def haversine_m(lat1, lon1, lat2, lon2):
    """Distancia en metros sobre la esfera; acepta arreglos."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * RADIO_TIERRA_M * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def _clase_de_via(tags) -> str | None:
    """La clase de una vía de OSM, o None si un auto no puede recorrerla."""
    if tags.get("route") == "ferry":
        return "balsa"
    clase = _CLASE_DE.get(tags.get("highway", ""))
    if clase is None:
        return None
    if tags.get("highway") == "service" and tags.get("service") in _SERVICIO_EXCLUIDO:
        return None
    for clave in ("access", "motor_vehicle", "motorcar", "vehicle"):
        if tags.get(clave) in _SIN_ACCESO:
            return None
    return clase


def leer_red(pbf: Path, indice: str = "flex_mem") -> Red:
    """Lee el extracto .osm.pbf y arma el grafo: las vías, y encima el tren y los botes
    (ver el módulo).

    ``indice`` es donde pyosmium guarda la ubicación de los nodos mientras lee: en memoria
    (~1 GB para el Perú) o, en una máquina con poca, en un archivo:
    ``"sparse_file_array,/tmp/nodos.idx"``.
    """
    import osmium  # solo lo necesita quien construye la red

    vias_de_tren, paradas = _rutas_de_tren(pbf)
    vial, capas = _Vias(), _Vias()
    rieles: list[list[tuple[int, float, float]]] = []
    procesador = (
        osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations(indice)
        .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
        .with_filter(osmium.filter.KeyFilter("highway", "route", "railway"))
    )
    for via in procesador:
        tags = via.tags
        turistico = tags.get("usage") == _RIEL_TURISTICO and tags.get("railway") in _RIELES
        if (via.id in vias_de_tren or turistico) and "highway" not in tags:
            if (
                tags.get("railway") in _RIELES
                and tags.get("usage") not in _RIEL_EXCLUIDO
                and tags.get("service") not in _SERVICIO_RIEL_EXCLUIDO
            ):
                rieles.append([(nd.ref, nd.lat, nd.lon) for nd in via.nodes if nd.location.valid()])
            continue
        clase = _clase_de_via(tags)
        if clase is None:
            continue
        nodos = [(nd.ref, nd.lat, nd.lon) for nd in via.nodes if nd.location.valid()]
        if len(nodos) < 2:
            continue
        if clase == "balsa":
            _, la, lo = zip(*nodos, strict=True)
            largo = haversine_m(np.array(la[:-1]), np.array(lo[:-1]), np.array(la[1:]), np.array(lo[1:])).sum()
            if largo > BALSA_MAX_M:
                capas.agregar(nodos, "bote", False, _DESPLAZAMIENTO["bote"])
                continue
        vial.agregar(nodos, clase, tags.get("surface", "") in SIN_ASFALTAR)
    del procesador  # libera el índice de nodos antes de armar el grafo

    # Las estaciones parten el riel: así cada una es un vértice donde se sube y se baja.
    refs_de_riel = {r for riel in rieles for r, _, _ in riel}
    estaciones = _estaciones(pbf, refs_de_riel, paradas) | _estaciones_al_lado(pbf, rieles, refs_de_riel)
    for riel in rieles:
        tramo = []
        for nodo in riel:
            tramo.append(nodo)
            if nodo[0] in estaciones and len(tramo) > 1:
                capas.agregar(tramo, "tren", False, _DESPLAZAMIENTO["tren"])
                tramo = [nodo]
        if len(tramo) > 1:
            capas.agregar(tramo, "tren", False, _DESPLAZAMIENTO["tren"])
    return _unir(vial.armar(), capas.armar(), list(estaciones.values()))


class _Vias:
    """Las vías que se van leyendo, en arreglos planos para ``_armar``."""

    def __init__(self):
        from array import array

        self.refs, self.lats, self.lons = array("q"), array("d"), array("d")
        self.inicios, self.clases, self.sin_asf = array("q"), array("b"), array("b")

    def agregar(self, nodos, clase: str, sin_asfaltar: bool, desplazamiento: int = 0) -> None:
        if len(nodos) < 2:
            return
        r, la, lo = zip(*nodos, strict=True)
        self.inicios.append(len(self.refs))
        self.refs.extend(x + desplazamiento for x in r)
        self.lats.extend(la)
        self.lons.extend(lo)
        self.clases.append(CODIGO[clase])
        self.sin_asf.append(sin_asfaltar)

    def armar(self) -> Red | None:
        if not self.inicios:
            return None
        return _armar(
            np.frombuffer(self.refs, dtype=np.int64),
            np.frombuffer(self.lats, dtype=np.float64),
            np.frombuffer(self.lons, dtype=np.float64),
            np.frombuffer(self.inicios, dtype=np.int64),
            np.frombuffer(self.clases, dtype=np.int8),
            np.frombuffer(self.sin_asf, dtype=np.int8).astype(bool),
        )


def _rutas_de_tren(pbf: Path) -> tuple[set[int], set[int]]:
    """(vías, nodos de parada) de las rutas de tren (``route=train``) del extracto."""
    import osmium

    vias, paradas = set(), set()
    relaciones = osmium.FileProcessor(str(pbf), osmium.osm.RELATION).with_filter(
        osmium.filter.TagFilter(("route", "train"))
    )
    for rel in relaciones:
        for m in rel.members:
            if m.type == "w":
                vias.add(m.ref)
            elif m.type == "n":
                paradas.add(m.ref)
    return vias, paradas


def _estaciones(pbf: Path, refs_de_riel: set[int], paradas: set[int]) -> dict[int, tuple[float, float]]:
    """Nodo → (lat, lon) de cada estación, paradero o parada de ruta que está sobre el riel."""
    import osmium

    salida = {}
    for nodo in osmium.FileProcessor(str(pbf), osmium.osm.NODE).with_filter(osmium.filter.IdFilter(refs_de_riel)):
        t = nodo.tags
        es_estacion = t.get("railway") in ("station", "halt") or t.get("public_transport") in (
            "stop_position",
            "station",
        )
        if (es_estacion or nodo.id in paradas) and nodo.location.valid():
            salida[nodo.id] = (nodo.location.lat, nodo.location.lon)
    return salida


def _estaciones_al_lado(pbf: Path, rieles: list, refs_de_riel: set[int]) -> dict[int, tuple[float, float]]:
    """Las estaciones de tren que OSM dibuja al lado del riel y no sobre él, como la de la
    Hidroeléctrica: nodo del riel más cercano → (lat, lon), si está a menos de
    ESTACION_AL_LADO_M. Sin esto, ahí no se podría subir ni bajar."""
    import osmium
    from scipy.spatial import cKDTree

    puntos = []
    for nodo in osmium.FileProcessor(str(pbf), osmium.osm.NODE).with_filter(
        osmium.filter.KeyFilter("railway", "public_transport")
    ):
        t = nodo.tags
        if nodo.id in refs_de_riel or not nodo.location.valid():
            continue
        de_tren = (t.get("railway") in ("station", "halt") and t.get("station") not in _NO_ES_TREN) or (
            t.get("public_transport") == "station" and t.get("train") == "yes"
        )
        if de_tren:
            puntos.append((nodo.location.lat, nodo.location.lon))
    nodos = {r: (la, lo) for riel in rieles for r, la, lo in riel}
    if not puntos or not nodos:
        return {}
    refs = list(nodos)
    lat, lon = np.array([nodos[r] for r in refs]).T
    cuerda, i = cKDTree(_unitarios(lat, lon)).query(_unitarios(*np.array(puntos).T))
    return {refs[j]: nodos[refs[j]] for j in i[_cuerda_a_metros(cuerda) <= ESTACION_AL_LADO_M]}


def _unir(vial: Red, capas: Red | None, puntos: list[tuple[float, float]]) -> Red:
    """La red vial con las capas encima, unidas por un trasbordo entre cada punto de embarque
    y el vértice vial más cercano, si está a menos de CONEXION_MAX_M. Del tren se sube en sus
    estaciones; de un bote, en cualquier punto de su ruta, como las lanchas que paran en cada
    pueblo de la orilla. Los puntos de embarque quedan marcados en ``embarque``, aunque ninguna
    vía llegue a ellos (el muelle de una isla)."""
    if capas is None:
        return vial
    from scipy.spatial import cKDTree

    n = vial.vertices
    capa = np.zeros(n + capas.vertices, dtype=np.int8)
    for nombre in ("tren", "bote"):
        de_la_capa = capas.clase == CODIGO[nombre]
        capa[n + capas.desde[de_la_capa]] = CAPAS.index(nombre)
        capa[n + capas.hasta[de_la_capa]] = CAPAS.index(nombre)
    vertice_de = {(la, lo): i for i, (la, lo) in enumerate(zip(capas.lat.tolist(), capas.lon.tolist(), strict=True))}
    de_bote = np.flatnonzero(capa[n:] == CAPAS.index("bote")).tolist()
    en_capa = sorted({vertice_de[p] for p in puntos if p in vertice_de} | set(de_bote))
    embarque = np.zeros(n + capas.vertices, dtype=bool)
    embarque[n + np.asarray(en_capa, dtype=np.int64)] = True
    arbol = cKDTree(_unitarios(vial.lat, vial.lon))
    cuerda, cercano = arbol.query(_unitarios(capas.lat[en_capa], capas.lon[en_capa]))
    metros = 2 * RADIO_TIERRA_M * np.arcsin(np.clip(cuerda / 2, 0.0, 1.0))
    une = metros <= CONEXION_MAX_M
    desde = cercano[une].astype(np.int32)
    hasta = (n + np.asarray(en_capa)[une]).astype(np.int32)
    k = int(une.sum())
    return Red(
        lat=np.r_[vial.lat, capas.lat],
        lon=np.r_[vial.lon, capas.lon],
        desde=np.r_[vial.desde, capas.desde + n, desde].astype(np.int32),
        hasta=np.r_[vial.hasta, capas.hasta + n, hasta].astype(np.int32),
        metros=np.r_[vial.metros, capas.metros, np.maximum(metros[une], 1.0)].astype(np.float32),
        clase=np.r_[vial.clase, capas.clase, np.full(k, CODIGO["transbordo"])].astype(np.int8),
        sin_asfaltar=np.r_[vial.sin_asfaltar, capas.sin_asfaltar, np.zeros(k, dtype=bool)],
        curvas=np.r_[vial.curvas, capas.curvas, np.zeros(k)].astype(np.float32),
        capa=capa,
        embarque=embarque,
    )


def _armar(refs, lat, lon, inicios, clase_via, sin_asf_via) -> Red:
    """Parte cada vía en sus cruces y cada kilómetro. Vectorizado: 15 millones de nodos en
    segundos; los intermedios se sueltan apenas dejan de servir para caber en poca memoria."""
    n = len(refs)
    por_via = np.diff(np.r_[inicios, n])
    via = np.repeat(np.arange(len(inicios), dtype=np.int32), por_via)
    primero = np.zeros(n, dtype=bool)
    primero[inicios] = True
    ultimo = np.zeros(n, dtype=bool)
    ultimo[np.r_[inicios[1:] - 1, n - 1]] = True

    # Largo de cada paso entre nodos seguidos de una misma vía.
    paso = haversine_m(lat[:-1], lon[:-1], lat[1:], lon[1:])
    paso[ultimo[:-1]] = 0.0  # entre el último nodo de una vía y el primero de la siguiente
    acumulado = np.r_[0.0, np.cumsum(paso)]

    # Un nodo es vértice si lo usan dos vías (o dos veces la misma), si es un extremo o si
    # cierra un kilómetro de la vía: así una parada nunca queda a más de medio kilómetro de
    # carretera de su vértice más cercano, aunque el próximo cruce esté a 30 km.
    _, inverso, usos = np.unique(refs, return_inverse=True, return_counts=True)
    es_vertice = (usos[inverso] > 1) | primero | ultimo
    del usos
    km_de_via = np.floor((acumulado - np.repeat(acumulado[inicios], por_via)) / TRAMO_MAX_M)
    es_vertice[1:] |= km_de_via[1:] != km_de_via[:-1]
    del km_de_via

    # Cuánto gira la vía en cada nodo, para medir las curvas de cada arista.
    giro = np.abs((np.diff(_rumbo(lat[:-1], lon[:-1], lat[1:], lon[1:])) + 180.0) % 360.0 - 180.0)  # nodo i+1
    giro[ultimo[1:-1] | primero[1:-1]] = 0.0
    giro[(paso[:-1] < 1.0) | (paso[1:] < 1.0)] = 0.0  # nodos repetidos
    del paso, primero, ultimo
    giro_acumulado = np.r_[0.0, 0.0, np.cumsum(giro)]  # [i]: suma de los giros en los nodos anteriores al i
    del giro

    posiciones = np.flatnonzero(es_vertice)
    del es_vertice
    ini, fin = posiciones[:-1], posiciones[1:]
    misma_via = via[ini] == via[fin]
    ini, fin = ini[misma_via], fin[misma_via]
    metros = acumulado[fin] - acumulado[ini]
    giros = np.maximum(giro_acumulado[fin] - giro_acumulado[np.minimum(ini + 1, n - 1)], 0.0)
    del acumulado, giro_acumulado

    # Vértices compactos: solo los nodos que son extremo de alguna arista.
    usados, id_vertice = np.unique(inverso[np.r_[ini, fin]], return_inverse=True)
    desde, hasta = id_vertice[: len(ini)], id_vertice[len(ini) :]
    posicion_de = np.empty(int(inverso.max()) + 1, dtype=np.int64)
    posicion_de[inverso[posiciones]] = posiciones
    pos = posicion_de[usados]
    valida = (desde != hasta) & (metros > 0)
    km = np.maximum(metros[valida], 1.0) / 1000.0
    return Red(
        lat=lat[pos],
        lon=lon[pos],
        desde=desde[valida].astype(np.int32),
        hasta=hasta[valida].astype(np.int32),
        metros=metros[valida].astype(np.float32),
        clase=clase_via[via[ini[valida]]],
        sin_asfaltar=sin_asf_via[via[ini[valida]]],
        curvas=(giros[valida] / km).astype(np.float32),
    )


def _rumbo(lat1, lon1, lat2, lon2):
    """Rumbo inicial en grados de cada paso."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2 - lon1)
    x = np.sin(dl) * np.cos(p2)
    y = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return np.degrees(np.arctan2(x, y))


# --- Capitales, pueblos y hospedajes ----------------------------------------------------

RANGO_LUGAR = {"city": 0, "town": 1, "suburb": 2, "village": 3, "hamlet": 4, "neighbourhood": 5, "locality": 6}


def leer_capitales(pbf: Path):
    """La capital de cada distrito según OSM: el nodo que el límite distrital (nivel 8)
    marca como ``admin_centre``. Con eso "Pariñas" cae en Talara y "Tambopata" en Puerto
    Maldonado, aunque el pueblo no se llame como el distrito. Si un distrito no lo marca,
    se usa el pueblo con su mismo nombre (``leer_lugares``).

    DataFrame con nombre del distrito, lat, lon y el nombre del pueblo capital."""
    import osmium
    import pandas as pd

    centro_de = {}
    relaciones = osmium.FileProcessor(str(pbf), osmium.osm.RELATION).with_filter(
        osmium.filter.TagFilter(("boundary", "administrative"))
    )
    for rel in relaciones:
        if rel.tags.get("admin_level") != "8" or not rel.tags.get("name"):
            continue
        for miembro in rel.members:
            if miembro.type == "n" and miembro.role == "admin_centre":
                centro_de[miembro.ref] = rel.tags.get("name")
                break
    filas = []
    nodos = osmium.FileProcessor(str(pbf), osmium.osm.NODE).with_filter(osmium.filter.IdFilter(centro_de))
    for nodo in nodos:
        if nodo.location.valid():
            filas.append((centro_de[nodo.id], nodo.tags.get("name"), nodo.location.lat, nodo.location.lon))
    return pd.DataFrame(filas, columns=["distrito", "capital", "lat", "lon"])


def leer_lugares(pbf: Path):
    """Nodos ``place`` de OSM con nombre: ciudades, pueblos, caseríos. DataFrame con
    nombre, lat, lon, rango (0 = ciudad… 6 = paraje) y la altitud que declara el nodo
    (``ele``: la tienen todas las ciudades y el 84 % de los pueblos)."""
    import osmium
    import pandas as pd

    from pipeline.texto import leer_altitud

    filas = []
    for nodo in osmium.FileProcessor(str(pbf), osmium.osm.NODE).with_filter(osmium.filter.KeyFilter("place")):
        rango = RANGO_LUGAR.get(nodo.tags.get("place", ""))
        nombre = nodo.tags.get("name")
        if rango is not None and nombre and nodo.location.valid():
            altitud = leer_altitud(nodo.tags.get("ele"))[0]
            filas.append((nombre, nodo.location.lat, nodo.location.lon, rango, altitud))
    return pd.DataFrame(filas, columns=["nombre", "lat", "lon", "rango", "altitud_m"])


HOSPEDAJE = ("hotel", "hostel", "guest_house", "motel", "apartment", "chalet")


def leer_hospedajes(pbf: Path, indice: str = "flex_mem"):
    """Hoteles, hostales, casas de huéspedes, moteles y alojamientos turísticos que
    registra OSM (``tourism``): un punto por establecimiento, el nodo o el promedio de
    los nodos de su contorno. Sirve para saber en qué pueblos hay dónde dormir.

    DataFrame con tipo, lat y lon."""
    import osmium
    import pandas as pd

    filas = []
    procesador = (
        osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations(indice)
        .with_filter(osmium.filter.TagFilter(*(("tourism", tipo) for tipo in HOSPEDAJE)))
    )
    for objeto in procesador:
        if objeto.is_node():
            if objeto.location.valid():
                filas.append((objeto.tags.get("tourism"), objeto.location.lat, objeto.location.lon))
            continue
        puntos = [(nd.lat, nd.lon) for nd in objeto.nodes if nd.location.valid()]
        if len(puntos) > 1 and puntos[0] == puntos[-1]:
            puntos = puntos[:-1]  # un contorno cerrado repite su primer nodo al final
        if puntos:
            lat, lon = np.mean(puntos, axis=0)
            filas.append((objeto.tags.get("tourism"), float(lat), float(lon)))
    return pd.DataFrame(filas, columns=["tipo", "lat", "lon"])


# --- Tiempo de cada arista ------------------------------------------------------------

CURVAS_TOPE = 1_000.0  # grados de giro por km; más que eso es ruido del trazado


def minutos_por_arista(red: Red, ritmos: dict[str, float]) -> np.ndarray:
    """Minutos para recorrer cada arista: km × (ritmo de su clase + recargo si no está
    asfaltada + recargo por sus curvas). Los recargos son de las vías; el tren y el bote
    van a su ritmo, y cada trasbordo suma además ``ritmos["transbordo_min"]``. Los ritmos de
    las vías salen de pipeline/red_calibracion.py; los demás, de pipeline/referencia/ritmos_fijos.csv."""
    ritmo = np.array([ritmos.get(c, np.inf) for c in CLASES])[red.clase]
    km = red.metros.astype(np.float64) / 1000
    curvas = np.minimum(red.curvas, CURVAS_TOPE) / 100
    vial = (red.clase < len(VIALES)).astype(np.float64)  # multiplicar por 1 no cambia ni un bit
    minutos = km * (ritmo + ritmos["sin_asfaltar"] * red.sin_asfaltar * vial + ritmos["curvas"] * curvas * vial)
    return minutos + ritmos.get("transbordo_min", 0.0) * (red.clase == CODIGO["transbordo"])


# --- Rutas ------------------------------------------------------------------------------


def _unitarios(lat, lon) -> np.ndarray:
    """Puntos de la esfera como vectores 3D: la distancia euclídea entre ellos crece con la real."""
    p, lam = np.radians(np.asarray(lat, dtype=float)), np.radians(np.asarray(lon, dtype=float))
    return np.column_stack([np.cos(p) * np.cos(lam), np.cos(p) * np.sin(lam), np.sin(p)])


def _cuerda_a_metros(cuerda) -> np.ndarray:
    return 2 * RADIO_TIERRA_M * np.arcsin(np.clip(cuerda / 2, 0.0, 1.0))


def cercanos(lat, lon, puntos_lat, puntos_lon, radio_m: float) -> list[list[int]]:
    """Para cada (lat, lon), los índices de los ``puntos`` a menos de ``radio_m`` metros."""
    from scipy.spatial import cKDTree

    if len(puntos_lat) == 0:
        return [[] for _ in range(len(lat))]
    arbol = cKDTree(_unitarios(puntos_lat, puntos_lon))
    cuerda = 2 * np.sin(radio_m / (2 * RADIO_TIERRA_M))
    return list(arbol.query_ball_point(_unitarios(lat, lon), cuerda))


MEDIOS = ("vial", "tren", "bote")  # por dónde se llega a un punto (ver Ruteador.ubicar)
_EN_CAPA = ("tren", "bote")  # los km de un camino que van en cada una (Ruteador.entre con por_medio)
CAPA_MAX_M = 5_000  # un punto que se llega en bote o en tren se ubica en su capa si está a menos de esto


class Ruteador:
    """Caminos más rápidos sobre la red con un tiempo por arista (minutos).

    Solo se ubican puntos en la parte conectada de la red. En las vías, en cualquier tramo
    de al menos ``vertices_minimos`` vértices: un tramo suelto de OSM, sin unión con nada,
    no sirve para llegar a ningún lado. En el tren y en los botes, solo en la parte que se
    une con el resto del país: un río mapeado a trozos no lleva a ninguna parte. Del tren
    se baja en una estación; de un bote, en cualquier punto de su ruta, como hacen las
    lanchas de la Amazonía y los botes del Titicaca. Cómo se elige dónde se ubica cada
    punto está en ``ubicar``.
    """

    def __init__(self, red: Red, minutos: np.ndarray, vertices_minimos: int = 200):
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import connected_components
        from scipy.spatial import cKDTree

        n = red.vertices
        indice = np.arange(red.aristas, dtype=np.int64)
        u = np.r_[red.desde, red.hasta]
        v = np.r_[red.hasta, red.desde]
        w = np.r_[minutos, minutos].astype(np.float64)
        e = np.r_[indice, indice]
        # Entre dos vértices puede haber dos aristas (dos vías paralelas): queda la más rápida.
        orden = np.lexsort((w, v, u))
        u, v, w, e = u[orden], v[orden], w[orden], e[orden]
        primera = np.r_[True, (u[1:] != u[:-1]) | (v[1:] != v[:-1])]
        u, v, w, e = u[primera], v[primera], np.maximum(w[primera], 1e-6), e[primera]
        self.red = red
        self.grafo = csr_matrix((w, (u, v)), shape=(n, n))
        self._arista = csr_matrix((e + 1, (u, v)), shape=(n, n))  # +1: un cero no se guarda
        self._metros = csr_matrix((np.maximum(red.metros[e].astype(np.float64), 1e-3), (u, v)), shape=(n, n))
        self.componentes, etiqueta = connected_components(self.grafo, directed=False)
        tamanio = np.bincount(etiqueta)
        self.componente = etiqueta
        self.en_red_grande = tamanio[etiqueta] >= vertices_minimos
        unida = etiqueta == int(np.argmax(tamanio))  # la parte que une el país
        capa = np.zeros(n, dtype=np.int8) if red.capa is None else red.capa
        embarque = np.zeros(n, dtype=bool) if red.embarque is None else red.embarque
        self._capa = capa
        self._ubicables = {
            "vial": np.flatnonzero(self.en_red_grande & (capa == CAPAS.index("vial"))),
            "tren": np.flatnonzero(unida & (capa == CAPAS.index("tren")) & embarque),
            "bote": np.flatnonzero(unida & (capa == CAPAS.index("bote"))),
        }
        self._arboles = {
            medio: cKDTree(_unitarios(red.lat[v], red.lon[v])) for medio, v in self._ubicables.items() if len(v)
        }

    def _mas_cercano(self, medio: str, puntos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if medio not in self._arboles:
            return np.full(len(puntos), -1, dtype=np.int64), np.full(len(puntos), np.inf)
        cuerda, i = self._arboles[medio].query(puntos)
        return self._ubicables[medio][i], _cuerda_a_metros(cuerda)

    def ubicar(self, lat, lon, medios=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(vértice, metros en línea recta hasta él, capa del vértice) para cada punto.

        ``medios`` dice, por punto, cómo se llega a él:
        - ``"vial"``: por la vía más cercana, como un pueblo o una parada a la que se llega
          en auto o a pie;
        - ``"bote"`` o ``"tren"``: por la ruta de bote o la estación más cercanas, si quedan a
          menos de CAPA_MAX_M y no hay una vía igual de cerca a menos de CONEXION_MAX_M;
          si no, por la vía;
        - ``None`` (todos, por defecto): por la vía, salvo que no haya ninguna a menos de
          CONEXION_MAX_M y una estación o la ruta de un bote queden más cerca (una isla, un
          pueblo al que solo llega el tren).
        """
        puntos = _unitarios(lat, lon)
        cercano = {medio: self._mas_cercano(medio, puntos) for medio in MEDIOS}
        vertice, metros = cercano["vial"]
        junto_a_la_via = metros <= CONEXION_MAX_M
        if medios is None:
            (vt, mt), (vb, mb) = cercano["tren"], cercano["bote"]
            v, m = np.where(mb < mt, vb, vt), np.minimum(mb, mt)
            usa = ~junto_a_la_via & (m < metros)
        else:
            medios = np.asarray(medios, dtype=object)
            en_bote = medios == "bote"
            v = np.where(en_bote, cercano["bote"][0], cercano["tren"][0])
            m = np.where(en_bote, cercano["bote"][1], cercano["tren"][1])
            usa = np.isin(medios, ["tren", "bote"]) & (m <= CAPA_MAX_M) & ~(junto_a_la_via & (metros <= m))
        vertice, metros = np.where(usa, v, vertice), np.where(usa, m, metros)
        return vertice, metros, self._capa[vertice]

    def minutos_desde(self, fuentes, limite: float = np.inf, predecesores: bool = False):
        """Minutos de viaje desde cada fuente a todos los vértices (inf si no se llega)."""
        from scipy.sparse.csgraph import dijkstra

        return dijkstra(self.grafo, directed=True, indices=fuentes, limit=limite, return_predecessors=predecesores)

    def aristas_del_camino(self, predecesores: np.ndarray, destino: int) -> np.ndarray:
        """Índices de las aristas del camino que termina en ``destino``."""
        vertices = [destino]
        while (anterior := predecesores[vertices[-1]]) >= 0:
            vertices.append(anterior)
        if len(vertices) < 2:
            return np.empty(0, dtype=np.int64)
        camino = np.array(vertices[::-1])
        a, b = camino[:-1], camino[1:]
        return np.asarray(self._arista[a, b]).ravel().astype(np.int64) - 1

    def entre(
        self, fuentes, destinos, margen: float | None = 1.0, obligatorios=None, por_medio: bool = False
    ) -> tuple[np.ndarray, ...]:
        """Minutos y km del camino más rápido de cada fuente a cada destino (vértices).

        Con ``margen`` (grados), la búsqueda se hace solo en la parte de la red que cae en
        el rectángulo de los puntos más ese margen: para las paradas de un polo, que están a
        menos de 80 km entre sí, es igual de exacta y cien veces más rápida. Si una fuente
        no llega a algún destino dentro del rectángulo, se repite con toda la red.

        ``obligatorios`` (booleano por destino; por defecto, todos) separa los destinos que
        importan de los que se miden de paso, como los pueblos que podrían ser base: solo
        los obligatorios fijan el rectángulo y obligan a repetir con toda la red. Un destino
        de paso que queda fuera del rectángulo o sin camino dentro de él vale ``inf``.

        Con ``por_medio`` devuelve además cuántos de esos km van en tren y cuántos en bote:
        (minutos, km, km_tren, km_bote).
        """
        fuentes, destinos = np.asarray(fuentes), np.asarray(destinos)
        obligatorios = np.ones(len(destinos), dtype=bool) if obligatorios is None else np.asarray(obligatorios, bool)
        if margen is None:
            return self._entre(np.arange(self.red.vertices), fuentes, destinos, por_medio)
        todos = np.r_[fuentes, destinos[obligatorios]]
        lat, lon = self.red.lat, self.red.lon
        dentro = np.flatnonzero(
            (lat >= lat[todos].min() - margen)
            & (lat <= lat[todos].max() + margen)
            & (lon >= lon[todos].min() - margen)
            & (lon <= lon[todos].max() + margen)
        )
        salida = self._entre(dentro, fuentes, destinos, por_medio)
        for i in np.flatnonzero(~np.isfinite(salida[0][:, obligatorios]).all(axis=1)):
            otra = self._entre(np.arange(self.red.vertices), fuentes[i : i + 1], destinos, por_medio)
            for tabla, fila in zip(salida, otra, strict=True):
                tabla[i] = fila[0]
        return salida

    def _entre(self, vertices, fuentes, destinos, por_medio: bool = False) -> tuple[np.ndarray, ...]:
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import dijkstra

        local = np.full(self.red.vertices, -1, dtype=np.int64)
        local[vertices] = np.arange(len(vertices))
        completo = len(vertices) == self.red.vertices
        grafo = self.grafo if completo else self.grafo[vertices][:, vertices]
        metros = self._metros if completo else self._metros[vertices][:, vertices]
        aristas = None
        if por_medio:
            aristas = self._arista if completo else self._arista[vertices][:, vertices]
        j = local[destinos]
        fuera = j < 0  # destinos fuera de la parte buscada
        j = np.where(fuera, 0, j)
        minutos, predecesor = dijkstra(grafo, directed=True, indices=local[fuentes], return_predecessors=True)
        forma = (len(fuentes), len(destinos))
        km, km_medio = np.full(forma, np.inf), np.full((len(_EN_CAPA),) + forma, np.inf)
        for i, fuente in enumerate(local[fuentes]):
            # Los km del camino más rápido: el mismo árbol de caminos, pesado en metros.
            hijos = np.flatnonzero(predecesor[i] >= 0)
            if not len(hijos):  # no llega a ningún otro vértice
                km[i] = km_medio[:, i] = np.where(j == fuente, 0.0, np.inf)
                continue
            padres = predecesor[i][hijos]
            peso = np.asarray(metros[padres, hijos]).ravel()
            arbol = csr_matrix((np.maximum(peso, 1e-3), (padres, hijos)), shape=grafo.shape)
            km[i] = dijkstra(arbol, directed=True, indices=fuente)[j] / 1000
            if por_medio:
                # Y en el mismo árbol, solo los metros de las aristas de cada capa.
                clase = self.red.clase[np.asarray(aristas[padres, hijos]).ravel() - 1]
                for k, medio in enumerate(_EN_CAPA):
                    en_medio = clase == CODIGO[medio]
                    if not en_medio.any():
                        km_medio[k, i] = np.where(np.isfinite(km[i]), 0.0, np.inf)
                        continue
                    peso_medio = np.maximum(np.where(en_medio, peso, 0.0), 1e-6)
                    arbol = csr_matrix((peso_medio, (padres, hijos)), shape=grafo.shape)
                    km_medio[k, i] = dijkstra(arbol, directed=True, indices=fuente)[j] / 1000
        minutos = minutos[:, j]
        minutos[:, fuera] = km[:, fuera] = np.inf
        km_medio[:, :, fuera] = np.inf
        if por_medio:
            return minutos, km, km_medio[0], km_medio[1]
        return minutos, km
