"""
DreemGO · TA-04 — evaluación sobre los 222 polos

Tres anécdotas no son una evaluación. Esto corre el ordenamiento sobre todos
los polos y reporta la distribución de la mejora contra el baseline.

Métrica principal: PARADAS VISITADAS en los días disponibles. Los kilómetros
son un medio; lo que el viajero nota es cuántos lugares alcanza a ver.

Uso:  python ta04_evaluacion.py [DIAS]
"""
import sys, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
spec = importlib.util.spec_from_file_location("t4", "ta04_ordenar_ruta.py")

R, K, VEL, SIN, JOR = 6371.0, 0.06, 32.5, 1.6, 8.0
VISITA = {"1": 2.5, "2": 1.5, "3": 2.0, "4": 1.5, "5": 3.0}
B = "../data/processed/"
L = lambda p, **k: pd.read_csv(B + p, sep=";", encoding="utf-8-sig", **k)

po, ma = L("polos_asignados_v2.csv"), L("dreemgo_master_dataset.csv")
fi = L("fichas_mincetur.csv", dtype=str)
for d, c in ((po, "CODIGO DEL RECURSO"), (ma, "CODIGO DEL RECURSO"), (fi, "CODIGO")):
    d["C"] = d[c].astype(str).str.strip()
dat = po[po.POLO != -1].merge(ma[["C", "CATEGORÍA"]], on="C", how="left") \
                       .merge(fi[["C", "ACCESO_MIN", "FICHA_JERARQUIA_NUM"]], on="C", how="left")

def mats(lat, lon, alt):
    la, lo = np.radians(lat)[:, None], np.radians(lon)[:, None]
    a = np.sin((la-la.T)/2)**2 + np.cos(la)*np.cos(la.T)*np.sin((lo-lo.T)/2)**2
    g = 2*R*np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    return g, np.sqrt(g**2 + (np.abs(alt[:,None]-alt[None,:])*K)**2)

def h(D, i, j): return D[i, j]*SIN/VEL
def ct(D, t, b):
    if not t: return 0.0
    return h(D,b,t[0]) + h(D,t[-1],b) + sum(h(D,t[k],t[k+1]) for k in range(len(t)-1))
def kt(G, t, b):
    if not t: return 0.0
    return G[b,t[0]] + G[t[-1],b] + sum(G[t[k],t[k+1]] for k in range(len(t)-1))

def opt2(D, t, b):
    m, go = t[:], True
    while go:
        go = False
        for i in range(len(m)-1):
            for j in range(i+1, len(m)):
                c = m[:i] + m[i:j+1][::-1] + m[j+1:]
                if ct(D,c,b) + 1e-9 < ct(D,m,b): m, go = c, True
    return m

def vecino(D, pend, b, vis, dias, con2):
    pend, rut = list(pend), []
    for _ in range(dias):
        if not pend: break
        t, act = [], b
        while pend:
            s = min(pend, key=lambda x: D[act, x]); pr = t+[s]
            if ct(D,pr,b) + sum(vis[x] for x in pr) > JOR: break
            t, act = pr, s; pend.remove(s)
        if not t: break
        if con2: t = opt2(D, t, b)
        rut.append(t)
    return rut, pend

def porjer(D, orden, b, vis, dias):
    pend, rut = list(orden), []
    for _ in range(dias):
        if not pend: break
        t = []
        for x in list(pend):
            if ct(D,t+[x],b) + sum(vis[y] for y in t+[x]) > JOR: break
            t.append(x); pend.remove(x)
        if not t: break
        rut.append(t)
    return rut, pend

filas = []
for polo, g in dat.groupby("POLO"):
    g = g.reset_index(drop=True); n = len(g)
    if n < 3: continue
    lat, lon = g.latitud.to_numpy(float), g.longitud.to_numpy(float)
    G, D = mats(lat, lon, g.ALTITUD.to_numpy(float))
    vis = np.array([VISITA.get(c, 1.5) for c in g["CATEGORÍA"].fillna("").str[:1]])
    am = pd.to_numeric(g.ACCESO_MIN, errors="coerce")
    b = int(am.idxmin()) if am.notna().any() else int(
        np.argmin((lat-lat.mean())**2 + (lon-lon.mean())**2))
    jer = pd.to_numeric(g.FICHA_JERARQUIA_NUM, errors="coerce").fillna(0)
    oj = [i for i in jer.sort_values(ascending=False).index if i != b]
    resto = [i for i in range(n) if i != b]
    r0,_ = porjer(D, oj, b, vis, DIAS)
    r1,_ = vecino(D, resto, b, vis, DIAS, False)
    r2,_ = vecino(D, resto, b, vis, DIAS, True)
    f = lambda r: (sum(len(t) for t in r), sum(kt(G,t,b) for t in r))
    p0,k0 = f(r0); p1,k1 = f(r1); p2,k2 = f(r2)
    filas.append(dict(POLO=polo, n=n, base=b, par_jer=p0, par_vec=p1, par_2opt=p2,
                      km_jer=k0, km_vec=k1, km_2opt=k2))

d = pd.DataFrame(filas)
d.to_csv(B + "evaluacion_ta04.csv", sep=";", index=False)
print("="*78); print(f"TA-04 · EVALUACIÓN SOBRE {len(d)} POLOS · {DIAS} días"); print("="*78)
print(f"\nParadas visitadas en {DIAS} días (suma sobre todos los polos):")
print(f"  0 · orden por jerarquía : {d.par_jer.sum():>6}")
print(f"  1 · vecino más cercano  : {d.par_vec.sum():>6}  ({d.par_vec.sum()/d.par_jer.sum()-1:+.1%})")
print(f"  2 · vecino + 2-opt      : {d.par_2opt.sum():>6}  ({d.par_2opt.sum()/d.par_jer.sum()-1:+.1%})")
print(f"\nKilómetros recorridos (suma):")
print(f"  0 · orden por jerarquía : {d.km_jer.sum():>8.0f} km")
print(f"  1 · vecino más cercano  : {d.km_vec.sum():>8.0f} km  ({d.km_vec.sum()/d.km_jer.sum()-1:+.1%})")
print(f"  2 · vecino + 2-opt      : {d.km_2opt.sum():>8.0f} km  ({d.km_2opt.sum()/d.km_jer.sum()-1:+.1%})")
g = d[d.par_jer > 0]
r = (g.par_2opt / g.par_jer - 1) * 100
print(f"\nMejora en paradas, por polo (n={len(g)}):")
for q in (10, 25, 50, 75, 90):
    print(f"  P{q:<3}: {np.percentile(r,q):>+6.1f} %")
print(f"  polos donde 2-opt visita MÁS   : {(r>0).sum()} ({(r>0).mean():.0%})")
print(f"  polos donde empata             : {(r==0).sum()} ({(r==0).mean():.0%})")
print(f"  polos donde visita MENOS       : {(r<0).sum()} ({(r<0).mean():.0%})")
ap = d.par_2opt - d.par_vec
print(f"\nAporte propio del 2-opt sobre el vecino más cercano:")
print(f"  paradas extra : {ap.sum()} · km ahorrados: {d.km_vec.sum()-d.km_2opt.sum():.0f} "
      f"({1-d.km_2opt.sum()/d.km_vec.sum():.1%})")
print(f"\nCobertura del polo en {DIAS} días: mediana {(d.par_2opt/(d.n-1)).median():.0%}")
print("\nEscrito: ../data/processed/evaluacion_ta04.csv")
