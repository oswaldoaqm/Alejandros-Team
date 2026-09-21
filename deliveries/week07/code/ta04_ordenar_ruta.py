"""
DreemGO · TA-04 — ordenamiento de la ruta dentro del polo

TA-01 entrega un polo: un conjunto de recursos que caben en un viaje. Eso no es
todavía un itinerario. Este módulo convierte el conjunto en una secuencia con
días asignados, que es lo que el producto promete.

MODELO
------
El viajero duerme en un punto base del polo y sale cada día a recorrer y volver.
No es un camino abierto: es una tanda de tours diarios desde un depósito, que es
como se viaja de verdad en el Perú — no se cambia de hospedaje cada noche en una
zona de 40 km.

    día = base → r1 → r2 → ... → rk → base,   con  suma(traslado + visita) ≤ JORNADA_H

El punto base es el recurso con menor ACCESO_MIN de la ficha oficial: el más
accesible desde el pueblo más cercano es el que tiene el pueblo al lado, y por
tanto donde hay dónde dormir. Si ningún recurso del polo declara acceso, se usa
el más cercano al centroide.

TIEMPO DE TRASLADO
------------------
    horas = distancia_geodésica × SINUOSIDAD / VELOCIDAD_KMH

VELOCIDAD_KMH = 32,5 sale de 3 094 tramos de acceso reales de la ficha, que dan
kilómetros y minutos por separado (mediana; P25 19,5 y P75 49,7 — la dispersión
es enorme y el número es una mediana, no una promesa).

SINUOSIDAD = 1,6 sigue siendo un supuesto: convierte línea recta en carretera y
no tenemos con qué calibrarlo hasta traer la red vial de OpenStreetMap.

Efectivo sobre distancia geodésica: 32,5 / 1,6 = 20,3 km/h, contra los 25 km/h
que suponía la versión anterior. Es decir, cruzar un polo cuesta un 23 % MÁS
tiempo del que documentamos en ModelSelection §5.7.

BASELINES
---------
  0 · orden por jerarquía   — el orden que entrega TA-03 hoy, partido en días
  1 · vecino más cercano    — heurístico clásico desde la base
  2 · vecino + 2-opt        — mejora local sobre cada día

Uso:  python ta04_ordenar_ruta.py [POLO] [DIAS]
"""
import sys
import numpy as np
import pandas as pd

R_TIERRA = 6371.0
K_DESNIVEL = 0.06
VELOCIDAD_KMH = 32.5        # calibrada · 3 094 tramos de la ficha
SINUOSIDAD = 1.6            # supuesto · pendiente de OSM
JORNADA_H = 8.0

# Duración de visita por categoría. Supuesto declarado: no hay ninguna fuente
# en el inventario que diga cuánto se tarda uno en ver un recurso.
VISITA_H = {"1": 2.5, "2": 1.5, "3": 2.0, "4": 1.5, "5": 3.0}
VISITA_DEF = 1.5

BASE = "../data/processed/"


def leer(p, **kw):
    return pd.read_csv(BASE + p, sep=";", encoding="utf-8-sig", **kw)


def matriz(lat, lon, alt):
    la = np.radians(lat)[:, None]; lo = np.radians(lon)[:, None]
    a = np.sin((la - la.T) / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2
    geo = 2 * R_TIERRA * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    dz = np.abs(alt[:, None] - alt[None, :]) * K_DESNIVEL
    return geo, np.sqrt(geo ** 2 + dz ** 2)


def horas(D, i, j):
    return D[i, j] * SINUOSIDAD / VELOCIDAD_KMH


def costo_tour(D, tour, base):
    """Horas de traslado de base → tour → base."""
    if not tour:
        return 0.0
    h = horas(D, base, tour[0]) + horas(D, tour[-1], base)
    return h + sum(horas(D, tour[k], tour[k + 1]) for k in range(len(tour) - 1))


def km_tour(G, tour, base):
    if not tour:
        return 0.0
    k = G[base, tour[0]] + G[tour[-1], base]
    return k + sum(G[tour[k2], tour[k2 + 1]] for k2 in range(len(tour) - 1))


def dos_opt(D, tour, base):
    """Mejora local: invierte segmentos mientras baje el tiempo del tour."""
    mejor = tour[:]
    mejora = True
    while mejora:
        mejora = False
        for i in range(len(mejor) - 1):
            for j in range(i + 1, len(mejor)):
                cand = mejor[:i] + mejor[i:j + 1][::-1] + mejor[j + 1:]
                if costo_tour(D, cand, base) + 1e-9 < costo_tour(D, mejor, base):
                    mejor, mejora = cand, True
    return mejor


def dias_vecino(D, pend, base, vis, dias, con_2opt):
    """Arma cada día tomando el vecino más cercano mientras quepa la jornada."""
    pend = list(pend)
    rutas = []
    for _ in range(dias):
        if not pend:
            break
        tour, act, h = [], base, 0.0
        while pend:
            sig = min(pend, key=lambda x: D[act, x])
            prueba = tour + [sig]
            t = costo_tour(D, prueba, base) + sum(vis[x] for x in prueba)
            if t > JORNADA_H:
                break
            tour, act = prueba, sig
            h = t
            pend.remove(sig)
        if not tour:
            break
        if con_2opt:
            tour = dos_opt(D, tour, base)
            h = costo_tour(D, tour, base) + sum(vis[x] for x in tour)
        rutas.append((tour, h))
    return rutas, pend


def dias_jerarquia(D, orden, base, vis, dias):
    """Baseline 0: el orden que entrega TA-03, partido por jornada."""
    pend = list(orden)
    rutas = []
    for _ in range(dias):
        if not pend:
            break
        tour = []
        for x in list(pend):
            prueba = tour + [x]
            if costo_tour(D, prueba, base) + sum(vis[y] for y in prueba) > JORNADA_H:
                break
            tour.append(x); pend.remove(x)
        if not tour:
            break
        rutas.append((tour, costo_tour(D, tour, base) + sum(vis[y] for y in tour)))
    return rutas, pend


def resumen(nombre, rutas, pend, G, base, n):
    km = sum(km_tour(G, t, base) for t, _ in rutas)
    vis = sum(len(t) for t, _ in rutas)
    tras = sum(h - sum(0 for _ in t) for t, h in rutas)
    return {"metodo": nombre, "dias": len(rutas), "paradas": vis,
            "cobertura_%": round(vis / n * 100, 1),
            "km_recorridos": round(km, 1),
            "h_por_dia": round(np.mean([h for _, h in rutas]), 2) if rutas else 0.0,
            "sin_visitar": len(pend)}


def main():
    # Se leen aquí y no al importar el módulo: consulta.py lo importa para
    # reusar las funciones de ruteo y tiene sus propios argumentos.
    POLO = int(sys.argv[1]) if len(sys.argv) > 1 else 201
    DIAS = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    # ───────────────────────────── datos ─────────────────────────────
    po = leer("polos_asignados_v2.csv")
    ma = leer("dreemgo_master_dataset.csv")
    fi = leer("fichas_mincetur.csv", dtype=str)
    ma["C"] = ma["CODIGO DEL RECURSO"].astype(str).str.strip()
    fi["C"] = fi["CODIGO"].astype(str).str.strip()
    po["C"] = po["CODIGO DEL RECURSO"].astype(str).str.strip()

    g = po[po.POLO == POLO].merge(ma[["C", "CATEGORÍA"]], on="C", how="left") \
                           .merge(fi[["C", "ACCESO_MIN", "FICHA_JERARQUIA_NUM"]], on="C", how="left")
    if g.empty:
        print(f"El polo {POLO} no existe o no tiene recursos."); return

    g = g.reset_index(drop=True)
    lat = g.latitud.to_numpy(float); lon = g.longitud.to_numpy(float)
    alt = g.ALTITUD.to_numpy(float)
    G, D = matriz(lat, lon, alt)
    n = len(g)

    cat = g["CATEGORÍA"].fillna("").str[:1]
    vis = np.array([VISITA_H.get(c, VISITA_DEF) for c in cat])

    am = pd.to_numeric(g.ACCESO_MIN, errors="coerce")
    if am.notna().any():
        base = int(am.idxmin()); motivo = f"menor tiempo de acceso ({am.min():.0f} min)"
    else:
        c = np.array([lat.mean(), lon.mean()])
        base = int(np.argmin((lat - c[0]) ** 2 + (lon - c[1]) ** 2)); motivo = "más cercano al centroide"

    jer = pd.to_numeric(g.FICHA_JERARQUIA_NUM, errors="coerce").fillna(0)
    orden_jer = [i for i in jer.sort_values(ascending=False).index if i != base]
    resto = [i for i in range(n) if i != base]

    print("=" * 78)
    print(f"TA-04 · ordenamiento de la ruta · POLO {POLO} · {DIAS} días")
    print("=" * 78)
    print(f"Recursos            : {n}")
    print(f"Base del itinerario : {g.loc[base, 'NOMBRE DEL RECURSO'][:48]}")
    print(f"                      elegida por {motivo}")
    print(f"Velocidad           : {VELOCIDAD_KMH} km/h sobre carretera · sinuosidad {SINUOSIDAD}")
    print(f"                      efectivo {VELOCIDAD_KMH/SINUOSIDAD:.1f} km/h en línea recta")
    print(f"Jornada             : {JORNADA_H} h · visita {VISITA_H} h según categoría\n")

    filas = []
    r0, p0 = dias_jerarquia(D, orden_jer, base, vis, DIAS)
    filas.append(resumen("0 · orden por jerarquía", r0, p0, G, base, n - 1))
    r1, p1 = dias_vecino(D, resto, base, vis, DIAS, False)
    filas.append(resumen("1 · vecino más cercano", r1, p1, G, base, n - 1))
    r2, p2 = dias_vecino(D, resto, base, vis, DIAS, True)
    filas.append(resumen("2 · vecino + 2-opt", r2, p2, G, base, n - 1))

    print("-" * 78)
    print("COMPARATIVA CONTRA BASELINE")
    print("-" * 78)
    print(pd.DataFrame(filas).to_string(index=False))

    b, m = filas[0]["km_recorridos"], filas[2]["km_recorridos"]
    if b:
        print(f"\n2-opt contra el orden por jerarquía: {(m/b-1)*100:+.1f} % de kilómetros")

    print("\n" + "=" * 78)
    print(f"ITINERARIO · vecino + 2-opt")
    print("=" * 78)
    print(f"Base: {g.loc[base, 'NOMBRE DEL RECURSO'][:56]}\n")
    for d, (tour, h) in enumerate(r2, 1):
        print(f"  DÍA {d}  ·  {h:.1f} h  ·  {km_tour(G, tour, base):.0f} km")
        ant = base
        for x in tour:
            t = horas(D, ant, x) * 60
            j = g.loc[x, "FICHA_JERARQUIA_NUM"]
            j = "-" if pd.isna(j) else str(j)
            print(f"     {t:>4.0f} min →  {g.loc[x,'NOMBRE DEL RECURSO'][:44]:<44} "
                  f"({vis[x]:.1f} h · jer {j})")
            ant = x
        print(f"     {horas(D, ant, base)*60:>4.0f} min →  regreso a la base\n")
    if p2:
        print(f"  Sin visitar en {DIAS} días: {len(p2)} recursos")
        for x in p2[:6]:
            print(f"     · {g.loc[x,'NOMBRE DEL RECURSO'][:52]}")

if __name__ == "__main__":
    main()
