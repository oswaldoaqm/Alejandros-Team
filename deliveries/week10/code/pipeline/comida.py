"""
Dónde comer cerca de cada lugar del inventario y de cada base (decisión 0019).

El plan del día lleva una hora de almuerzo, y el motor elige dónde: si puede, en una parada que
tiene dónde comer cerca; si no, avisa que hay que llevar el almuerzo. Para eso, por cada lugar del
inventario y cada base de polo, cuántos restaurantes, cafés y locales de comida rápida hay a menos
de 1,5 km en línea recta, y a cuántos metros queda el más cercano:

- **OpenStreetMap:** ``amenity`` restaurant, fast_food, cafe o food_court, tengan nombre o no.
- **Overture Maps:** los de categoría básica restaurant, fast_food_restaurant, cafe, food_court o
  food_truck_stand, con una confianza de al menos 0,7 y solo de fuentes con licencia CDLA, como en
  ``pipeline/noche.py``. Sus nombres no se usan: solo dónde están.

Que no haya ninguno no prueba que no haya dónde comer: OSM y Overture no registran todo lo que hay
en un pueblo. Por eso el motor lo dice así: «no tenemos registrado dónde comer cerca».

Escribe data/procesados/comida_cerca.csv. Lo de OSM es obra derivada bajo ODbL; lo de Overture,
bajo CDLA Permissive 2.0.

Uso:  python -m pipeline.comida        (después del maestro, de bases.py y de descargar_overture.py)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.maestro import EXTERNOS, PROCESADOS
from pipeline.red_vial import cercanos, haversine_m

OSM = EXTERNOS / "osm"
OVERTURE = EXTERNOS / "overture"
CACHE = 1  # sube cuando cambia lo que se guarda de OSM
RADIO_M = 1_500
CONFIANZA_MIN = 0.7
ETIQUETAS_OSM = tuple(("amenity", v) for v in ("restaurant", "fast_food", "cafe", "food_court"))
CATEGORIAS_OVERTURE = frozenset({"restaurant", "fast_food_restaurant", "cafe", "food_court", "food_truck_stand"})


def leer_osm(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """Los lugares de comida de OSM: el nodo, o el promedio de los nodos del contorno."""
    import osmium

    filas = []
    procesador = (
        osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations(indice)
        .with_filter(osmium.filter.TagFilter(*ETIQUETAS_OSM))
    )
    for objeto in procesador:
        if objeto.is_node():
            if not objeto.location.valid():
                continue
            filas.append((objeto.location.lat, objeto.location.lon))
            continue
        puntos = [(nd.lat, nd.lon) for nd in objeto.nodes if nd.location.valid()]
        if len(puntos) > 1 and puntos[0] == puntos[-1]:
            puntos = puntos[:-1]
        if puntos:
            filas.append(tuple(float(x) for x in np.mean(puntos, axis=0)))
    return pd.DataFrame(filas, columns=["lat", "lon"])


def osm_en_cache(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """``leer_osm``, guardado junto al extracto: se rehace si cambia su MD5."""
    manifiesto = json.loads((pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    ruta = pbf.parent / f"comida_{manifiesto['md5'][:8]}_v{CACHE}.csv"
    if not ruta.exists():
        leer_osm(pbf, indice).to_csv(ruta, index=False)
    return pd.read_csv(ruta)


def de_overture(ruta: Path) -> pd.DataFrame:
    """Los lugares de comida de Overture: de una categoría de comida, con confianza de al menos
    ``CONFIANZA_MIN`` y solo de fuentes con licencia CDLA."""
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    tabla = pq.read_table(ruta, columns=["confidence", "basic_category", "bbox", "sources"])
    filas = []
    cajas = tabla["bbox"]
    ymin = pc.struct_field(cajas, "ymin").to_pylist()
    xmin = pc.struct_field(cajas, "xmin").to_pylist()
    for categoria, confianza, fuentes, lat, lon in zip(
        tabla["basic_category"].to_pylist(),
        tabla["confidence"].to_pylist(),
        tabla["sources"].to_pylist(),
        ymin,
        xmin,
        strict=True,
    ):
        if categoria not in CATEGORIAS_OVERTURE or confianza is None or confianza < CONFIANZA_MIN:
            continue
        licencias = {f.get("license") for f in fuentes or []}
        if not licencias or any(not (lic or "").startswith("CDLA") for lic in licencias):
            continue
        filas.append((lat, lon))
    return pd.DataFrame(filas, columns=["lat", "lon"])


def cerca(puntos: pd.DataFrame, osm: pd.DataFrame, overture: pd.DataFrame) -> pd.DataFrame:
    """Para cada punto (columnas lat y lon), cuántos lugares de comida de cada fuente hay a menos
    de ``RADIO_M`` y a cuántos metros queda el más cercano (vacío si no hay ninguno)."""
    lat, lon = puntos["lat"].to_numpy(dtype=float), puntos["lon"].to_numpy(dtype=float)
    salida = {}
    distancias = [[] for _ in range(len(puntos))]
    for nombre, fuente in (("osm", osm), ("overture", overture)):
        vecinos = cercanos(lat, lon, fuente["lat"].to_numpy(), fuente["lon"].to_numpy(), RADIO_M)
        salida[f"comida_{nombre}"] = [len(v) for v in vecinos]
        for i, v in enumerate(vecinos):
            if v:
                d = haversine_m(lat[i], lon[i], fuente["lat"].to_numpy()[v], fuente["lon"].to_numpy()[v])
                distancias[i].append(float(np.min(d)))
    salida["mas_cerca_m"] = [int(round(min(d))) if d else None for d in distancias]
    return pd.DataFrame(salida, index=puntos.index)


def main() -> None:
    ap = argparse.ArgumentParser(description="Dónde comer cerca de cada lugar del inventario y de cada base.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--overture", type=Path, help="el parquet de descargar_overture.py; por defecto, el del manifiesto")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem")
    a = ap.parse_args()
    if a.overture is None:
        manifiesto = json.loads((OVERTURE / "manifiesto.json").read_text(encoding="utf-8"))
        a.overture = OVERTURE / manifiesto["archivo"]
    osm, overture = osm_en_cache(a.pbf, a.indice), de_overture(a.overture)

    maestro = pd.read_csv(
        PROCESADOS / "maestro_v3.csv", sep=";", encoding="utf-8-sig", usecols=["codigo", "lat", "lon"]
    )
    maestro = maestro.dropna(subset=["lat", "lon"])
    bases = pd.read_csv(PROCESADOS / "polos_bases.csv", sep=";", encoding="utf-8-sig", usecols=["polo", "lat", "lon"])
    partes = []
    for tipo, tabla, clave in (("recurso", maestro, "codigo"), ("base", bases, "polo")):
        tabla = tabla.reset_index(drop=True)
        partes.append(
            pd.concat([pd.DataFrame({"tipo": tipo, "clave": tabla[clave]}), cerca(tabla, osm, overture)], axis=1)
        )
    comida = pd.concat(partes, ignore_index=True)
    comida["mas_cerca_m"] = comida["mas_cerca_m"].astype("Int64")
    comida.to_csv(a.salida / "comida_cerca.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

    con_comida = comida["mas_cerca_m"].notna()
    resumen = {
        "osm": {"lugares": len(osm), "md5": json.loads((a.pbf.parent / "manifiesto.json").read_text())["md5"]},
        "overture": {"lugares": len(overture), "version": a.overture.stem.removeprefix("lugares_peru_")},
        "radio_m": RADIO_M,
        "recursos": int((comida["tipo"] == "recurso").sum()),
        "recursos_con_comida": int((con_comida & (comida["tipo"] == "recurso")).sum()),
        "bases": int((comida["tipo"] == "base").sum()),
        "bases_con_comida": int((con_comida & (comida["tipo"] == "base")).sum()),
    }
    (a.salida / "comida_resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Comida a menos de {RADIO_M} m: {resumen['recursos_con_comida']} de {resumen['recursos']} lugares y "
        f"{resumen['bases_con_comida']} de {resumen['bases']} bases ({len(osm)} lugares de OSM, {len(overture)} de "
        f"Overture); escrito en {a.salida / 'comida_cerca.csv'}"
    )


if __name__ == "__main__":
    main()
