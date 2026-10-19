"""
Artefactos del motor: lo que ``dreemgo/motor`` carga al arrancar (decisión 0003).

Junta las tablas de data/procesados en pocos archivos compactos dentro de dreemgo/datos/,
que entran a la imagen del API:

  manifiesto.json     versión de los datos, de dónde sale cada cosa y la huella de cada archivo
  recursos.json.gz    los recursos de cada polo: lo que la respuesta muestra de ellos y lo que
                      el motor necesita para programarlos
  polos.json.gz       cada polo: base, novedad, clima mes a mes, sus paradas y los tiempos
                      entre ellas y desde la base; si algún camino va en tren o en bote, cuántos
                      de sus km van en cada uno; y su noche: dónde salir cerca de la base y su
                      cielo para mirar las estrellas (pipeline/noche.py y pipeline/cielo.py)
  origenes.json.gz    las 24 ciudades de partida, con sus tiempos a cada base y a las paradas a
                      menos de 4 horas, que son las que caben en un viaje de un día: minutos, km,
                      km en tren y km en bote; y el viaje en avión a cada base (pipeline/vuelos.py)
  eventos.json.gz     los acontecimientos programados con la regla de su fecha
  costos.json         los parámetros del costo (pipeline/referencia/costos.csv) y el pasaje de
                      cada ruta aérea, por tramo (data/procesados/vuelos_rutas.csv)

Los archivos son deterministas: con las mismas tablas salen los mismos bytes (JSON con las
claves ordenadas y gzip sin fecha), así que su huella sirve para comprobar que dos máquinas
construyeron lo mismo.

Un polo es lo que se visita desde una base. El maestro y los eventos traen el grupo de TA-01
de cada recurso; los grupos que duermen en el mismo pueblo son un solo polo, y aquí cada
recurso y cada evento pasa a llevar el número de su polo (``grupos`` de polos_bases.csv).

Uso:  python -m pipeline.artefactos --version 2026.10.6
      (después de maestro, eventos, tiempos, vuelos, clima, noche y cielo)
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from dreemgo.contrato import ETIQUETAS_INTERES, Interes
from pipeline.bases import polo_de_cada_grupo
from pipeline.maestro import PROCESADOS, RAIZ, REFERENCIA
from pipeline.texto import sin_tildes

DESTINO = RAIZ / "dreemgo" / "datos"
VERSION_DATOS = "2026.10.6"
SATURADAS = ("Lima", "Cusco")  # el circuito habitual: decide `fuera_del_circuito` y la novedad
EXCURSION_MAX_MIN = 240  # una parada más lejos que esto del origen no cabe en un viaje de un día
MEDIOS_KM = ("km", "km_tren", "km_bote")  # los km de cada camino, y cuántos van en tren y en bote

ATRIBUCION = [
    "Inventario Nacional de Recursos Turísticos y fichas oficiales · MINCETUR",
    "Clima: Open-Meteo.com, sobre ERA5 y ERA5-Land de Copernicus · CC BY 4.0",
    "Red de vías, trenes y botes, pueblos, hospedajes y lugares de noche: © colaboradores de OpenStreetMap · ODbL 1.0",
]
ATRIBUCION_NOCHE = [
    "Lugares de noche: Overture Maps Foundation, con datos de Meta y Microsoft · CDLA Permissive 2.0",
    "Luces nocturnas: VIIRS, Earth Observation Group, Colorado School of Mines · dominio público; copia «Light Every"
    " Night» del Banco Mundial",
    "Nubes de noche: GOES-16 y METAR de los aeropuertos, NOAA",
]


def _limpio(v):
    """Un valor listo para JSON: NaN es null, los enteros de numpy son int."""
    if v is None:
        return None
    if isinstance(v, float | np.floating):
        return None if math.isnan(v) else float(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def _redondo(x, decimales: int = 1):
    v = _limpio(x)
    return None if v is None else round(float(v), decimales)


def _entero(x):
    v = _limpio(x)
    return None if v is None else int(round(float(v)))


def _lista(texto) -> list[str]:
    return [] if pd.isna(texto) or texto == "" else str(texto).split("|")


def _ingreso(fila) -> str:
    """El tipo de ingreso del contrato: libre, pagado o desconocido."""
    if fila["ingreso"] == "libre":
        return "libre"
    if fila["ingreso"] == "boleto" or (fila["ingreso"] in ("permiso", "otro") and fila["tarifa_soles"] > 0):
        return "pagado"
    return "desconocido"


def en_su_polo(tabla: pd.DataFrame, bases: pd.DataFrame) -> pd.DataFrame:
    """La tabla con el polo de cada fila en vez de su grupo de TA-01; lo que no está en ningún
    grupo sigue en −1."""
    a_polo = polo_de_cada_grupo(bases)
    return tabla.assign(polo=tabla["polo"].map(lambda grupo: a_polo.get(grupo, grupo)).astype(int))


def recursos(maestro: pd.DataFrame) -> list[dict]:
    """Los recursos que están en un polo, ordenados por código."""
    filas = []
    for f in maestro[maestro["polo"] >= 0].sort_values("codigo").to_dict("records"):
        filas.append(
            {
                "codigo": str(f["codigo"]),
                "nombre": f["nombre"],
                "categoria": f["categoria"],
                "tipo": f["tipo"],
                "subtipo": _limpio(f["subtipo"]),
                "jerarquia": _entero(f["jerarquia"]),
                "lat": round(float(f["lat"]), 6),
                "lon": round(float(f["lon"]), 6),
                "altitud_m": _entero(f["altitud_m"]),
                "url_ficha": f["url_ficha"],
                "descripcion": _limpio(f["descripcion_corta"]),
                "foto_url": _limpio(f["foto_url"]),
                "ingreso": _ingreso(f),
                "tarifa_soles": _redondo(f["tarifa_soles"], 2),
                "boleto_combinado": bool(f["boleto_combinado"]),
                "polo": int(f["polo"]),
                "es_parada": bool(f["es_parada"]),
                "intereses": _lista(f["intereses"]),
                "visita_min": _entero(f["visita_min"]),
                "caminata_min": _entero(f["caminata_min"]),
                "abre": _limpio(f["abre"]),
                "cierra": _limpio(f["cierra"]),
                "dias": _lista(f["dias"]) or None,
            }
        )
    return filas


def _nombre_corto(nombre: str, largo: int = 40) -> str:
    return nombre if len(nombre) <= largo else nombre[: largo - 1].rsplit(" ", 1)[0] + "…"


def _region_origen(origenes: pd.DataFrame) -> dict[str, str]:
    """Región → ciudad de origen de esa región (Callao sale de Lima)."""
    clave = {sin_tildes(r).lower(): o for r, o in zip(origenes["region"], origenes["id"], strict=True)}
    clave["callao"] = "lima"
    return clave


def polos(
    maestro: pd.DataFrame,
    bases: pd.DataFrame,
    clima: pd.DataFrame,
    tiempos_polo: pd.DataFrame,
    tiempos_base: pd.DataFrame,
    tiempos_origen_base: pd.DataFrame,
    eventos: pd.DataFrame,
    origenes: pd.DataFrame,
    noche: dict[int, dict] | None = None,
) -> list[dict]:
    """Cada polo con lo que el motor necesita para resolver una consulta sin otra tabla."""
    en_polo = maestro[maestro["polo"] >= 0]
    paradas = en_polo[en_polo["es_parada"].astype(bool)]

    # Nombre: el de la base. Dos polos ya no duermen en el mismo pueblo, pero dos pueblos pueden
    # llamarse igual: ahí se agrega el recurso principal de cada polo.
    principal = (
        paradas.assign(_j=paradas["jerarquia"].fillna(0))
        .sort_values(["polo", "_j", "codigo"], ascending=[True, False, True])
        .groupby("polo")["nombre"]
        .first()
    )
    repetida = bases["base"].duplicated(keep=False)
    nombre = {
        int(p): f"{b} · {_nombre_corto(principal.get(p, ''))}" if r and p in principal.index else str(b)
        for p, b, r in zip(bases["polo"], bases["base"], repetida, strict=True)
    }

    # Novedad (semana 6, §6.4): 0,5 · (1 − saturación) + 0,5 · lejanía. La lejanía es el
    # tiempo desde la ciudad de origen de la región del polo hasta su base, en la escala de la
    # carretera: va de 0 a 1, y el 1 es el polo más lejano al que se llega sin tren ni bote.
    # Los que quedan más lejos que ese (a días de río) o sin camino también valen 1, como
    # cuando la red solo tenía carreteras: un río muy largo no achica la lejanía de los demás.
    region_origen = _region_origen(origenes)
    a_base = tiempos_origen_base.set_index(["origen", "polo"])
    capas = [c for c in MEDIOS_KM[1:] if c in a_base]
    region = en_polo.groupby("polo")["region"].agg(lambda s: s.value_counts().sort_index().idxmax())
    lejos, por_carretera = {}, {}
    for p, r in region.items():
        clave = (region_origen.get(sin_tildes(r).lower()), p)
        hay = clave in a_base.index
        lejos[p] = a_base.at[clave, "minutos"] if hay else np.nan
        por_carretera[p] = not (hay and a_base.loc[clave, capas].sum() > 0)
    lejos = pd.Series(lejos, dtype=float)
    tope = lejos[pd.Series(por_carretera)].max()
    tope = lejos.max() if pd.isna(tope) else tope  # ninguno por carretera: la escala es la de todos
    lejos = lejos.fillna(tope).clip(upper=tope)
    lejania = (lejos - lejos.min()) / (tope - lejos.min())
    saturacion = en_polo.groupby("polo")["region"].agg(lambda s: s.isin(SATURADAS).mean())
    novedad = 0.5 * (1 - saturacion) + 0.5 * lejania

    salida = []
    clima_de = {p: g.sort_values("mes") for p, g in clima.groupby("polo")}
    eventos_de = eventos[eventos["polo"] >= 0].groupby("polo")["codigo"].agg(lambda s: sorted(str(c) for c in s))
    for b in bases.sort_values("polo").itertuples():
        p = int(b.polo)
        mios = en_polo[en_polo["polo"] == p]
        codigos = sorted(paradas.loc[paradas["polo"] == p, "codigo"].astype(int))
        posicion = {c: i for i, c in enumerate(codigos)}
        n = len(codigos)
        pares = tiempos_polo[tiempos_polo["polo"] == p]
        i = pares["desde"].map(posicion).to_numpy()
        j = pares["hasta"].map(posicion).to_numpy()
        entre = {}
        for columna in ("minutos", *MEDIOS_KM):
            matriz = np.full((n, n), np.nan)
            np.fill_diagonal(matriz, 0.0)
            if columna in pares:
                matriz[i, j] = pares[columna].to_numpy()
            entre[columna] = matriz
        desde_base = tiempos_base[tiempos_base["polo"] == p].set_index("codigo")
        # Cuántos km de cada camino van en tren y en bote: solo en los polos donde alguno va.
        en_capa = {}
        for columna in MEDIOS_KM[1:]:
            base_km = [_redondo(desde_base[columna].get(c)) if columna in desde_base else None for c in codigos]
            if any((x or 0) > 0 for x in base_km) or np.nansum(entre[columna]) > 0:
                en_capa[f"base_{columna}"] = base_km
                en_capa[f"entre_{columna}"] = [[_redondo(x) for x in fila] for fila in entre[columna]]
        regiones = mios["region"].value_counts()
        salida.append(
            {
                "id": p,
                "nombre": nombre[p],
                "region": region[p],
                "regiones": sorted(regiones.index, key=lambda r: (-regiones[r], r)),
                "recursos": len(mios),
                "fuera_del_circuito": not mios["region"].isin(SATURADAS).any(),
                "novedad": round(float(novedad[p]), 4),
                "base": {
                    "nombre": b.base,
                    "lat": round(float(b.lat), 6),
                    "lon": round(float(b.lon), 6),
                    "altitud_m": _entero(b.altitud_m),
                    "altitud_fuente": _limpio(b.altitud_fuente) or None,
                    "lugar": b.lugar,
                    "hospedajes_osm": int(b.hospedajes_osm),
                    "criterio": b.criterio,
                },
                "paradas": [str(c) for c in codigos],
                "base_minutos": [_redondo(desde_base["minutos"].get(c)) for c in codigos],
                "base_km": [_redondo(desde_base["km"].get(c)) for c in codigos],
                "entre_minutos": [[_redondo(x) for x in fila] for fila in entre["minutos"]],
                "entre_km": [[_redondo(x) for x in fila] for fila in entre["km"]],
                **en_capa,
                "clima": [
                    {
                        "mes": int(c.mes),
                        "lluvia_mm": _redondo(c.lluvia_mm),
                        "dias_con_lluvia": _redondo(c.dias_con_lluvia),
                        "temp_min_c": _redondo(c.temp_min_c),
                        "temp_max_c": _redondo(c.temp_max_c),
                        "puesto_lluvia": int(c.puesto_lluvia),
                        "veredicto": c.veredicto,
                        "fuente": c.fuente,
                    }
                    for c in clima_de[p].itertuples()
                ],
                "eventos": list(eventos_de.get(p, [])),
                **({"noche": noche[p]} if noche and p in noche else {}),
            }
        )
    return salida


def _texto(x) -> str | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) or x == "" else str(x)


def _de_estrellas(fila: dict, prefijo: str) -> dict | None:
    """Un lugar de cielo_polos.csv (``oscuro_*`` o ``astro_*``), o None si no hay."""
    nombre = _texto(fila.get(f"{prefijo}_nombre"))
    if nombre is None:
        return None
    return {
        "nombre": nombre,
        "tipo": fila[f"{prefijo}_tipo"],
        "osm": fila[f"{prefijo}_osm"],
        "lat": round(float(fila[f"{prefijo}_lat"]), 6),
        "lon": round(float(fila[f"{prefijo}_lon"]), 6),
        "minutos": int(fila[f"{prefijo}_minutos"]),
        "brillo": round(float(fila[f"{prefijo}_brillo"]), 3),
    }


def noches(lugares: pd.DataFrame, cielo: pd.DataFrame) -> dict[int, dict]:
    """La noche de cada polo: los lugares para salir, en el orden de pipeline/noche.py, y su cielo,
    de pipeline/cielo.py."""
    salida = {}
    por_polo = {int(p): g for p, g in lugares.groupby("polo")}
    for fila in cielo.to_dict("records"):
        p = int(fila["polo"])
        aqui = por_polo.get(p, lugares.iloc[0:0])
        salida[p] = {
            "lugares": [
                {
                    "nombre": f["nombre"],
                    "tipo": f["tipo"],
                    "lat": round(float(f["lat"]), 6),
                    "lon": round(float(f["lon"]), 6),
                    "minutos_a_pie": int(f["minutos_a_pie"]),
                    "fuente": f["fuente"],
                    "osm": _texto(f["osm"]),
                    "horario": _texto(f["horario"]),
                }
                for f in aqui.to_dict("records")
            ],
            "cielo": {
                "brillo": round(float(fila["brillo_base"]), 3),
                "oscuro": _de_estrellas(fila, "oscuro"),
                "astro": _de_estrellas(fila, "astro"),
                "despejadas": [_redondo(fila[f"despejadas_{m}"], 3) for m in range(1, 13)],
                "nubes": _texto(fila["nubes"]),
                "aeropuerto": _texto(fila["nubes_aeropuerto"]),
            },
        }
    return salida


def _tiempos(fila) -> list:
    """[minutos, km, km en tren, km en bote] de un camino; los dos últimos en 0 si la tabla no
    los trae (las de antes del tren y los botes)."""
    return [_redondo(getattr(fila, c, 0.0)) for c in ("minutos", *MEDIOS_KM)]


def _en_avion(fila) -> list:
    """[minutos de puerta a puerta, km por tierra, km en tren, km en bote, minutos de vuelo,
    minutos y km por tierra hasta el aeropuerto, minutos desde el de llegada, aeropuertos]."""
    numeros = (
        "minutos",
        *MEDIOS_KM,
        "minutos_vuelo",
        "minutos_hasta_aeropuerto",
        "km_hasta_aeropuerto",
        "minutos_desde_aeropuerto",
    )
    return [*(_redondo(getattr(fila, c)) for c in numeros), fila.aeropuertos]


def origenes_(
    origenes: pd.DataFrame,
    tiempos_origen_base: pd.DataFrame,
    tiempos_origen: pd.DataFrame,
    vuelos_origen_base: pd.DataFrame | None = None,
) -> list[dict]:
    salida = []
    for o in origenes.itertuples():
        a_base = tiempos_origen_base[tiempos_origen_base["origen"] == o.id].sort_values("polo")
        cerca = tiempos_origen[(tiempos_origen["origen"] == o.id) & (tiempos_origen["minutos"] <= EXCURSION_MAX_MIN)]
        cerca = cerca.sort_values("codigo")
        fila = {
            "id": o.id,
            "nombre": o.ciudad,
            "region": o.region,
            "lat": o.lat,
            "lon": o.lon,
            "a_base": {str(p): _tiempos(f) for p, f in zip(a_base["polo"], a_base.itertuples(), strict=True)},
            "a_parada": {str(c): _tiempos(f) for c, f in zip(cerca["codigo"], cerca.itertuples(), strict=True)},
        }
        if vuelos_origen_base is not None:
            avion = vuelos_origen_base[vuelos_origen_base["origen"] == o.id].sort_values("polo")
            fila["a_base_en_avion"] = {
                str(p): _en_avion(f) for p, f in zip(avion["polo"], avion.itertuples(), strict=True)
            }
        salida.append(fila)
    return salida


def eventos_(eventos: pd.DataFrame) -> list[dict]:
    salida = []
    for e in eventos.sort_values("codigo").to_dict("records"):
        salida.append(
            {
                "id": str(e["codigo"]),
                "nombre": e["nombre"],
                "tipo": _limpio(e["subtipo"]) or _limpio(e["tipo"]),
                "polo": int(e["polo"]),
                "regla": _limpio(e["regla"]),
                "dia_central": _limpio(e["dia_central"]),
                "precision_fecha": e["precision_fecha"],
                "distrito": e["distrito"],
                "provincia": e["provincia"],
                "region": e["region"],
                "url": e["url_ficha"],
            }
        )
    return salida


def costos_(vuelos_rutas: pd.DataFrame | None = None) -> dict:
    t = pd.read_csv(REFERENCIA / "costos.csv", sep=";")
    salida = {
        f.parametro: {"valor": f.valor, "minimo": f.minimo, "maximo": f.maximo, "unidad": f.unidad, "fuente": f.fuente}
        for f in t.itertuples()
    }
    for r in [] if vuelos_rutas is None else vuelos_rutas.itertuples():
        fuente = (
            f"{r.fuente}, recogida el 15 de octubre de 2026 y pasada a soles: el mínimo"
            if r.tarifa_publicada
            else f"{r.fuente}: la mediana de las demás rutas como mínimo"
        )
        salida[f"vuelo_{r.desde}_{r.hasta}"] = {
            "valor": float(r.tarifa_central),
            "minimo": float(r.tarifa_minima),
            "maximo": float(r.tarifa_maxima),
            "unidad": "S/ por persona y tramo",
            "fuente": f"{fuente}. Central y máximo: 1,5 y 2,2 veces el mínimo (pipeline/vuelos.py). Sin calibrar",
        }
    return salida


def aeropuertos_(vuelos_rutas: pd.DataFrame) -> dict:
    """Cada aeropuerto con su ciudad y los minutos de su vuelo a Lima, para los textos del motor."""
    aeropuertos = pd.read_csv(REFERENCIA / "aeropuertos.csv", sep=";")
    minutos = dict(zip(vuelos_rutas["hasta"], vuelos_rutas["minutos"].astype(int), strict=True))
    return {a.iata: {"ciudad": a.ciudad, "minutos_a_lima": minutos.get(a.iata, 0)} for a in aeropuertos.itertuples()}


def _fecha(aaaammdd) -> str:
    t = str(int(aaaammdd))
    return f"{t[:4]}-{t[4:6]}-{t[6:]}"


def _bytes_json(datos) -> bytes:
    return json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _escribir_gz(datos, ruta: Path) -> str:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0, compresslevel=9) as gz:
        gz.write(_bytes_json(datos))
    ruta.write_bytes(buffer.getvalue())
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def construir(entrada: Path, destino: Path, version: str) -> dict:
    def leer(nombre: str, **kw) -> pd.DataFrame:
        return pd.read_csv(entrada / nombre, sep=";", encoding="utf-8-sig", **kw)

    bases = leer("polos_bases.csv")
    maestro = en_su_polo(leer("maestro_v3.csv", dtype={"dias": str}), bases)
    eventos = en_su_polo(leer("eventos_v3.csv"), bases)
    clima = leer("clima_polo_mes.csv")
    tiempos_polo = leer("tiempos_polo.csv")
    tiempos_base = leer("tiempos_base.csv")
    tiempos_origen_base = leer("tiempos_origen_base.csv")
    tiempos_origen = leer("tiempos_origen.csv")
    origenes = pd.read_csv(REFERENCIA / "origenes.csv", sep=";")
    calibracion = json.loads((entrada / "red_calibracion.json").read_text(encoding="utf-8"))
    hay_vuelos = (entrada / "vuelos_origen_base.csv").exists()
    vuelos_origen_base = leer("vuelos_origen_base.csv") if hay_vuelos else None
    vuelos_rutas = leer("vuelos_rutas.csv") if hay_vuelos else None
    hay_noche = (entrada / "noche_lugares.csv").exists() and (entrada / "cielo_polos.csv").exists()
    noche = None
    if hay_noche:
        lugares_de_noche = leer("noche_lugares.csv", keep_default_na=False, dtype={"osm": str, "horario": str})
        noche = noches(lugares_de_noche, leer("cielo_polos.csv", dtype={"oscuro_osm": str, "astro_osm": str}))

    destino.mkdir(parents=True, exist_ok=True)
    huellas = {
        "recursos.json.gz": _escribir_gz(recursos(maestro), destino / "recursos.json.gz"),
        "polos.json.gz": _escribir_gz(
            polos(maestro, bases, clima, tiempos_polo, tiempos_base, tiempos_origen_base, eventos, origenes, noche),
            destino / "polos.json.gz",
        ),
        "origenes.json.gz": _escribir_gz(
            origenes_(origenes, tiempos_origen_base, tiempos_origen, vuelos_origen_base), destino / "origenes.json.gz"
        ),
        "eventos.json.gz": _escribir_gz(eventos_(eventos), destino / "eventos.json.gz"),
    }
    costos = _bytes_json(costos_(vuelos_rutas))
    (destino / "costos.json").write_bytes(costos)
    huellas["costos.json"] = hashlib.sha256(costos).hexdigest()

    propios = clima.loc[clima["fuente"] == "open_meteo_polo", "polo"].nunique()
    usables = maestro[(maestro["polo"] >= 0) & maestro["es_parada"].astype(bool)]
    intereses_de = usables["intereses"].fillna("").str.split("|")
    manifiesto = {
        "version_datos": version,
        "fuentes": {
            "inventario": {"fecha_corte": _fecha(maestro["fecha_corte"].dropna().max())},
            "osm": calibracion["osm"],
            "clima": {
                "polos_con_su_clima": int(propios),
                "polos_con_clima_regional": int(clima["polo"].nunique() - propios),
            },
        },
        "intereses": {
            i.value: {
                "etiqueta": ETIQUETAS_INTERES[i],
                "paradas": int(intereses_de.apply(lambda xs, i=i: i.value in xs).sum()),
            }
            for i in Interes
        },
        "atribucion": ATRIBUCION + (ATRIBUCION_NOCHE if hay_noche else []),
        "archivos": huellas,
    }
    if hay_noche:
        for nombre in ("noche", "cielo"):
            resumen = entrada / f"{nombre}_resumen.json"
            if resumen.exists():
                manifiesto["fuentes"][nombre] = json.loads(resumen.read_text(encoding="utf-8"))
    if vuelos_rutas is not None:
        manifiesto["aeropuertos"] = aeropuertos_(vuelos_rutas)
        manifiesto["fuentes"]["vuelos"] = {"rutas": len(vuelos_rutas), "consultadas": "2026-10-15"}
    (destino / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifiesto


def main() -> None:
    ap = argparse.ArgumentParser(description="Arma los artefactos que carga el motor.")
    ap.add_argument("--version", default=VERSION_DATOS, help="version_datos: AAAA.MM.n")
    ap.add_argument("--entrada", type=Path, default=PROCESADOS)
    ap.add_argument("--destino", type=Path, default=DESTINO)
    a = ap.parse_args()
    manifiesto = construir(a.entrada, a.destino, a.version)
    tamanio = sum((a.destino / f).stat().st_size for f in manifiesto["archivos"])
    print(f"Artefactos {manifiesto['version_datos']} en {a.destino}: {tamanio / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
