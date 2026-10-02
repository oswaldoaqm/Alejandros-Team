"""
Compara dos corridas de ``python -m pipeline.tiempos``: qué pares empeoran, mejoran, ganan o
pierden camino, y por qué.

Sirve para revisar un cambio en la red antes de publicarlo. Sumar caminos (el tren, los
botes) nunca debería alargar un viaje si cada punto se ubica en el mismo lugar, así que todo
lo que empeora tiene que tener una explicación. Las que reconoce:

  base       la base del polo es otro pueblo, o el mismo ubicado en otro lugar de la red;
  parada     la parada se ubica en otro lugar de la red: otra capa (la vía, una estación, la
             ruta de un bote) u otra distancia hasta ella.

Dónde se ubica cada base y cada parada sale de polos_bases.csv y red_paradas.csv; si la
corrida de antes no lo trae (las de antes del tren y los botes), cuenta como la vía.

Lo demás sale como «sin explicación» y hay que mirarlo a mano antes de publicar.

Uso:  python -m pipeline.comparar_tiempos ANTES DESPUES [--umbral 1]
      (dos carpetas con las salidas de pipeline.tiempos, por ejemplo data/procesados y una
      corrida nueva con --salida)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TABLAS = {
    "tiempos_origen_base.csv": ["origen", "polo"],
    "tiempos_base.csv": ["polo", "codigo"],
    "tiempos_origen.csv": ["origen", "codigo"],
    "tiempos_polo.csv": ["polo", "desde", "hasta"],
}


def _leer(carpeta: Path, nombre: str) -> pd.DataFrame:
    return pd.read_csv(carpeta / nombre, sep=";", encoding="utf-8-sig")


def _ubicacion(tabla: pd.DataFrame, clave: str) -> pd.DataFrame:
    """Dónde se ubica cada punto: capa y metros hasta la red (vacío si la tabla no lo trae)."""
    t = tabla.set_index(clave)
    for columna, defecto in (("capa", "vial"), ("metros_a_la_red", -1)):
        if columna not in t:
            t[columna] = defecto
    return t[["capa", "metros_a_la_red"]]


def _movidos(antes: pd.DataFrame, despues: pd.DataFrame) -> set:
    """Los puntos que cambian de lugar en la red, entre los que están en las dos corridas."""
    comun = antes.index.intersection(despues.index)
    a, d = antes.loc[comun], despues.loc[comun]
    sabe = (a["metros_a_la_red"] >= 0) & (d["metros_a_la_red"] >= 0)
    return set(comun[(a["capa"] != d["capa"]) | (sabe & (a["metros_a_la_red"] != d["metros_a_la_red"]))])


def comparar(antes: Path, despues: Path, umbral: float = 1.0) -> dict[str, pd.DataFrame]:
    """Por tabla, los pares que empeoran más de ``umbral`` minutos o pierden su camino, con
    su explicación (vacía si no la hay), y un resumen de cuántos pares cambian."""
    bases_a, bases_d = _leer(antes, "polos_bases.csv"), _leer(despues, "polos_bases.csv")
    nombre_a = bases_a.set_index("polo")["base"].to_dict()
    nombre_d = bases_d.set_index("polo")["base"].to_dict()
    otra_base = {p for p in nombre_a.keys() | nombre_d.keys() if nombre_a.get(p) != nombre_d.get(p)}
    otra_base |= _movidos(_ubicacion(bases_a, "polo"), _ubicacion(bases_d, "polo"))
    movida = _movidos(
        _ubicacion(_leer(antes, "red_paradas.csv"), "codigo"), _ubicacion(_leer(despues, "red_paradas.csv"), "codigo")
    )

    salida, resumen = {}, []
    for nombre, claves in TABLAS.items():
        t = _leer(antes, nombre).merge(_leer(despues, nombre), on=claves, suffixes=("_antes", "_despues"), how="outer")
        dif = t["minutos_despues"] - t["minutos_antes"]
        peor = (dif > umbral) | (t["minutos_antes"].notna() & t["minutos_despues"].isna())
        resumen.append(
            {
                "tabla": nombre,
                "pares": len(t),
                "empeoran": int((dif > umbral).sum()),
                "pierden_camino": int((t["minutos_antes"].notna() & t["minutos_despues"].isna()).sum()),
                "mejoran": int((dif < -umbral).sum()),
                "ganan_camino": int((t["minutos_antes"].isna() & t["minutos_despues"].notna()).sum()),
            }
        )
        p = t[peor].assign(diferencia=dif[peor].round(1))
        motivo = pd.Series("", index=p.index)
        if "polo" in p:
            motivo = motivo.mask(p["polo"].isin(otra_base), "base")
        for columna in ("codigo", "desde", "hasta"):
            if columna in p:
                motivo = motivo.mask((motivo == "") & p[columna].isin(movida), "parada")
        salida[nombre] = p.assign(explicacion=motivo).sort_values("diferencia", ascending=False, na_position="first")
    salida["resumen"] = pd.DataFrame(resumen)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="Compara dos corridas de pipeline.tiempos.")
    ap.add_argument("antes", type=Path)
    ap.add_argument("despues", type=Path)
    ap.add_argument("--umbral", type=float, default=1.0, help="minutos desde los que un par cuenta como peor")
    a = ap.parse_args()
    resultado = comparar(a.antes, a.despues, a.umbral)
    print(resultado.pop("resumen").to_string(index=False))
    sin_explicar = 0
    for nombre, p in resultado.items():
        if p.empty:
            continue
        print(f"\n{nombre}: {len(p)} empeoran o pierden camino")
        print(p["explicacion"].replace("", "sin explicación").value_counts().to_string())
        resto = p[p["explicacion"] == ""]
        sin_explicar += len(resto)
        if len(resto):
            print(resto.head(30).to_string(index=False))
    print(f"\nSin explicación: {sin_explicar}")


if __name__ == "__main__":
    main()
