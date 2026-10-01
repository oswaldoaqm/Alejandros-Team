"""
Red vial del Perú desde OpenStreetMap y tiempos de viaje por carretera.

Reemplaza la fórmula de semanas anteriores (línea recta × 1,6 a 32,5 km/h, nunca
calibrada) por rutas sobre las vías reales. Ver docs/decisiones/0007-red-vial-propia.md.

1. ``leer_red`` convierte el extracto de Geofabrik en un grafo: un vértice por cruce o
   extremo de vía, una arista por tramo entre cruces, con su largo, su clase (troncal,
   primaria… trocha), si es sin asfaltar y cuántas curvas tiene por kilómetro. Se guarda
   en data/externos/osm/red_vial.npz (fuera de git: se reconstruye en un minuto).
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
CLASES = ("autopista", "troncal", "primaria", "secundaria", "terciaria", "local", "trocha", "balsa")
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
            fecha_osm=np.array(self.fecha_osm),
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
    """Lee el extracto .osm.pbf y arma el grafo vial simplificado (ver el módulo).

    ``indice`` es donde pyosmium guarda la ubicación de los nodos mientras lee: en memoria
    (~1 GB para el Perú) o, en una máquina con poca, en un archivo:
    ``"sparse_file_array,/tmp/nodos.idx"``.
    """
    from array import array

    import osmium  # solo lo necesita quien construye la red

    refs, lats, lons = array("q"), array("d"), array("d")
    inicios, clases, sin_asf = array("q"), array("b"), array("b")
    procesador = (
        osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations(indice)
        .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
        .with_filter(osmium.filter.KeyFilter("highway", "route"))
    )
    for via in procesador:
        clase = _clase_de_via(via.tags)
        if clase is None:
            continue
        nodos = [(nd.ref, nd.lat, nd.lon) for nd in via.nodes if nd.location.valid()]
        if len(nodos) < 2:
            continue
        r, la, lo = zip(*nodos, strict=True)
        if clase == "balsa":
            largo = haversine_m(np.array(la[:-1]), np.array(lo[:-1]), np.array(la[1:]), np.array(lo[1:])).sum()
            if largo > BALSA_MAX_M:
                continue
        inicios.append(len(refs))
        refs.extend(r)
        lats.extend(la)
        lons.extend(lo)
        clases.append(CODIGO[clase])
        sin_asf.append(via.tags.get("surface", "") in SIN_ASFALTAR)
    del procesador  # libera el índice de nodos antes de armar el grafo
    return _armar(
        np.frombuffer(refs, dtype=np.int64),
        np.frombuffer(lats, dtype=np.float64),
        np.frombuffer(lons, dtype=np.float64),
        np.frombuffer(inicios, dtype=np.int64),
        np.frombuffer(clases, dtype=np.int8),
        np.frombuffer(sin_asf, dtype=np.int8).astype(bool),
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
    asfaltada + recargo por sus curvas). ``ritmos`` sale de pipeline/red_calibracion.py."""
    ritmo = np.array([ritmos[c] for c in CLASES])[red.clase]
    km = red.metros.astype(np.float64) / 1000
    curvas = np.minimum(red.curvas, CURVAS_TOPE) / 100
    return km * (ritmo + ritmos["sin_asfaltar"] * red.sin_asfaltar + ritmos["curvas"] * curvas)


# --- Rutas ------------------------------------------------------------------------------


def _unitarios(lat, lon) -> np.ndarray:
    """Puntos de la esfera como vectores 3D: la distancia euclídea entre ellos crece con la real."""
    p, lam = np.radians(np.asarray(lat, dtype=float)), np.radians(np.asarray(lon, dtype=float))
    return np.column_stack([np.cos(p) * np.cos(lam), np.cos(p) * np.sin(lam), np.sin(p)])


def cercanos(lat, lon, puntos_lat, puntos_lon, radio_m: float) -> list[list[int]]:
    """Para cada (lat, lon), los índices de los ``puntos`` a menos de ``radio_m`` metros."""
    from scipy.spatial import cKDTree

    if len(puntos_lat) == 0:
        return [[] for _ in range(len(lat))]
    arbol = cKDTree(_unitarios(puntos_lat, puntos_lon))
    cuerda = 2 * np.sin(radio_m / (2 * RADIO_TIERRA_M))
    return list(arbol.query_ball_point(_unitarios(lat, lon), cuerda))


class Ruteador:
    """Caminos más rápidos sobre la red con un tiempo por arista (minutos).

    Solo se ubican puntos en la parte conectada grande de la red: un tramo suelto de
    OSM, sin unión con nada, no sirve para llegar a ningún lado.
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
        self._ubicables = np.flatnonzero(self.en_red_grande)
        self._arbol = cKDTree(_unitarios(red.lat[self._ubicables], red.lon[self._ubicables]))

    def ubicar(self, lat, lon) -> tuple[np.ndarray, np.ndarray]:
        """(vértice más cercano, metros en línea recta hasta él) para cada punto."""
        cuerda, i = self._arbol.query(_unitarios(lat, lon))
        metros = 2 * RADIO_TIERRA_M * np.arcsin(np.clip(cuerda / 2, 0.0, 1.0))
        return self._ubicables[i], metros

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

    def entre(self, fuentes, destinos, margen: float | None = 1.0, obligatorios=None) -> tuple[np.ndarray, np.ndarray]:
        """Minutos y km del camino más rápido de cada fuente a cada destino (vértices).

        Con ``margen`` (grados), la búsqueda se hace solo en la parte de la red que cae en
        el rectángulo de los puntos más ese margen: para las paradas de un polo, que están a
        menos de 80 km entre sí, es igual de exacta y cien veces más rápida. Si una fuente
        no llega a algún destino dentro del rectángulo, se repite con toda la red.

        ``obligatorios`` (booleano por destino; por defecto, todos) separa los destinos que
        importan de los que se miden de paso, como los pueblos que podrían ser base: solo
        los obligatorios fijan el rectángulo y obligan a repetir con toda la red. Un destino
        de paso que queda fuera del rectángulo o sin camino dentro de él vale ``inf``.
        """
        fuentes, destinos = np.asarray(fuentes), np.asarray(destinos)
        obligatorios = np.ones(len(destinos), dtype=bool) if obligatorios is None else np.asarray(obligatorios, bool)
        if margen is None:
            return self._entre(np.arange(self.red.vertices), fuentes, destinos)
        todos = np.r_[fuentes, destinos[obligatorios]]
        lat, lon = self.red.lat, self.red.lon
        dentro = np.flatnonzero(
            (lat >= lat[todos].min() - margen)
            & (lat <= lat[todos].max() + margen)
            & (lon >= lon[todos].min() - margen)
            & (lon <= lon[todos].max() + margen)
        )
        minutos, km = self._entre(dentro, fuentes, destinos)
        for i in np.flatnonzero(~np.isfinite(minutos[:, obligatorios]).all(axis=1)):
            minutos[i], km[i] = self._entre(np.arange(self.red.vertices), fuentes[i : i + 1], destinos)
        return minutos, km

    def _entre(self, vertices, fuentes, destinos) -> tuple[np.ndarray, np.ndarray]:
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import dijkstra

        local = np.full(self.red.vertices, -1, dtype=np.int64)
        local[vertices] = np.arange(len(vertices))
        completo = len(vertices) == self.red.vertices
        grafo = self.grafo if completo else self.grafo[vertices][:, vertices]
        metros = self._metros if completo else self._metros[vertices][:, vertices]
        minutos, predecesor = dijkstra(grafo, directed=True, indices=local[fuentes], return_predecessors=True)
        km = np.full(minutos.shape, np.inf)
        for i, fuente in enumerate(local[fuentes]):
            # Los km del camino más rápido: el mismo árbol de caminos, pesado en metros.
            hijos = np.flatnonzero(predecesor[i] >= 0)
            padres = predecesor[i][hijos]
            peso = np.asarray(metros[padres, hijos]).ravel()
            arbol = csr_matrix((np.maximum(peso, 1e-3), (padres, hijos)), shape=grafo.shape)
            km[i] = dijkstra(arbol, directed=True, indices=fuente) / 1000
        j = local[destinos]
        minutos, km = minutos[:, j], km[:, j]
        minutos[:, j < 0] = km[:, j < 0] = np.inf  # destinos fuera de la parte buscada
        return minutos, km
