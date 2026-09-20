"""
DreemGO · Estimación de costo del itinerario

El producto pide presupuesto como entrada. Para que ese input sirva hay que
devolver un número, no una etiqueta. Este módulo descompone el costo en cinco
componentes, cada uno con su fuente, y entrega una banda P20–P80 en lugar de
una cifra puntual — porque la cifra puntual promete una precisión que no
tenemos y la banda es honesta y sigue siendo accionable.

    costo = transporte_interprovincial (ida y vuelta)
          + movilidad_dentro_del_polo
          + noches × alojamiento
          + días  × alimentación
          + entradas de las paradas pagadas

Parámetros en parametros_costo.csv. Mientras una fila esté marcada
`calibrado = no`, su rango entra completo al Monte Carlo y ensancha la banda.
Esa es la propiedad útil: **el ancho de la banda mide cuánto no sabemos.**

Uso:
    python costo_itinerario.py parametros_costo.csv            # caso base
    python costo_itinerario.py parametros_costo.csv --sensibilidad
"""
import sys
import numpy as np
import pandas as pd

RUTA = sys.argv[1] if len(sys.argv) > 1 else "parametros_costo.csv"
N_MC = 20000
SINUOSIDAD = 1.6


def cargar(ruta):
    p = pd.read_csv(ruta, sep=";", comment="#")
    p["calibrado"] = p.calibrado.astype(str).str.strip().str.lower().eq("si")
    return p.set_index("parametro")


def costo(p, itin):
    """p: dict parámetro → valor. itin: dict con el itinerario."""
    transporte = 2 * (p["bus_intercepto"] + p["bus_soles_km"] * itin["dist_origen_km"])
    interno = (p["movilidad_soles_km"] * itin["diametro_polo_km"] * SINUOSIDAD
               * max(itin["paradas"] - 1, 0))
    alojamiento = max(itin["dias"] - 1, 0) * p["alojamiento_noche"]
    alimentacion = itin["dias"] * p["alimentacion_dia"]
    entradas = itin["paradas"] * itin["frac_paradas_pagadas"] * p["entrada_pagada"]
    return {
        "transporte interprovincial": transporte,
        "movilidad en el polo": interno,
        "alojamiento": alojamiento,
        "alimentación": alimentacion,
        "entradas": entradas,
        "total": transporte + interno + alojamiento + alimentacion + entradas,
    }


def banda(p, itin, n=N_MC, semilla=42):
    """Monte Carlo sobre los parámetros no calibrados. Devuelve P20, P50, P80."""
    rng = np.random.default_rng(semilla)
    tot = np.empty(n)
    for i in range(n):
        muestra = {}
        for k, f in p.iterrows():
            if f.calibrado:
                muestra[k] = rng.uniform(f.valor * 0.95, f.valor * 1.05)
            else:
                muestra[k] = rng.uniform(f.rango_min, f.rango_max)
        tot[i] = costo(muestra, itin)["total"]
    return np.percentile(tot, [20, 50, 80]), tot


def main():
    p = cargar(RUTA)
    itin = dict(dist_origen_km=450, diametro_polo_km=55, dias=6, paradas=5,
                frac_paradas_pagadas=0.23)

    print("=" * 76)
    print("COSTO ESTIMADO DEL ITINERARIO")
    print("=" * 76)
    print(f"Itinerario: {itin['dias']} días · {itin['paradas']} paradas · "
          f"polo a {itin['dist_origen_km']} km del origen · "
          f"diámetro {itin['diametro_polo_km']} km\n")

    c = costo(dict(p.valor), itin)
    for k, v in c.items():
        if k == "total":
            continue
        print(f"  {k:<28} S/ {v:>7.0f}   {v / c['total'] * 100:>5.1f} %")
    print(f"  {'-' * 28} {'-' * 10}")
    print(f"  {'valor central':<28} S/ {c['total']:>7.0f}")

    (p20, p50, p80), tot = banda(p, itin)
    print(f"\n  BANDA P20–P80              S/ {p20:.0f} – {p80:.0f}"
          f"   (P50 S/ {p50:.0f}, ±{(p80 - p20) / 2 / p50 * 100:.1f} %)")

    sin = (~p.calibrado).sum()
    print(f"\n  Parámetros sin calibrar: {sin} de {len(p)}")
    if sin:
        print("  La banda se estrechará al calibrarlos. Prioridad:")
        for k, f in p[~p.calibrado].iterrows():
            lo = dict(p.valor); lo[k] = f.rango_min
            hi = dict(p.valor); hi[k] = f.rango_max
            amp = costo(hi, itin)["total"] - costo(lo, itin)["total"]
            print(f"    ±S/ {amp:>4.0f}  {k:<20} {f.fuente}")

    if "--sensibilidad" in sys.argv:
        print("\n" + "=" * 76)
        print("EFECTO DE CALIBRAR POR ETAPAS")
        print("=" * 76)
        orden = (p[~p.calibrado]
                 .assign(amp=[abs(costo({**dict(p.valor), k: f.rango_max}, itin)["total"]
                                  - costo({**dict(p.valor), k: f.rango_min}, itin)["total"])
                              for k, f in p[~p.calibrado].iterrows()])
                 .sort_values("amp", ascending=False).index.tolist())
        acum = []
        for k in [None] + orden:
            if k: acum.append(k)
            q = p.copy(); q.loc[q.index.isin(acum), "calibrado"] = True
            (a, b, cc), _ = banda(q, itin, n=6000)
            etiq = "nada calibrado" if not acum else f"+ {k}"
            print(f"  {etiq:<26} S/ {a:>5.0f} – {cc:<5.0f}  ±{(cc - a) / 2 / b * 100:>4.1f} %")


if __name__ == "__main__":
    main()
