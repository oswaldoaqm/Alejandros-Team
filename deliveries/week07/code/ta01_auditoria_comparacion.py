"""Auditoría de la comparación de modelos: ¿la gané limpiamente o me hice trampa?"""
import sys, warnings
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, HDBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score
warnings.filterwarnings("ignore")
R = 6371.0

def hav(lat, lon, lat0, lon0):
    la, lo, la0, lo0 = map(np.radians, (lat, lon, lat0, lon0))
    a = np.sin((la-la0)/2)**2 + np.cos(la)*np.cos(la0)*np.sin((lo-lo0)/2)**2
    return 2*R*np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def radio(lat, lon, lab, min_tam=3):
    tot = peso = 0
    for g in np.unique(lab):
        if g == -1: continue
        m = lab == g; n = int(m.sum())
        if n < min_tam: continue
        tot += hav(lat[m], lon[m], lat[m].mean(), lon[m].mean()).mean()*n; peso += n
    return tot/peso

df = pd.read_csv(sys.argv[1], sep=None, engine="python")
VARS = ["latitud","longitud","ALTITUD","INDICE_COSTO_LOGISTICO"]
geo = df.dropna(subset=VARS).copy()
lat = geo.latitud.to_numpy(float); lon = geo.longitud.to_numpy(float)
X = StandardScaler().fit_transform(geo[VARS].to_numpy(float))
reg = geo["REGIÓN"].astype("category").cat.codes.to_numpy()

print("#"*72)
print("1 · ¿El radio medio mejora solo por tener más grupos?")
print("#"*72)
print(f"{'k':>5} {'silueta':>10} {'radio_km':>10}")
for k in (25, 29, 48, 81, 120):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    print(f"{k:>5} {silhouette_score(X, km.labels_):>10.4f} {radio(lat,lon,km.labels_):>10.1f}")

h = HDBSCAN(min_cluster_size=15).fit(X)
lab_h = h.labels_
val = lab_h != -1
print(f"\nHDBSCAN 81 grupos (solo {val.sum()} pts): silueta "
      f"{silhouette_score(X[val], lab_h[val]):.4f}  radio {radio(lat,lon,lab_h):.1f} km")

print("\n" + "#"*72)
print("2 · Comparación justa: mismo subconjunto de puntos, mismo n de grupos")
print("#"*72)
km81 = KMeans(n_clusters=81, n_init=10, random_state=42).fit(X)
print("Sobre los 3 760 puntos que HDBSCAN SÍ agrupó:")
for nom, lb in [("HDBSCAN mcs=15", lab_h), ("K-Means k=81", km81.labels_), ("REGIÓN", reg)]:
    l = lb[val]
    print(f"  {nom:<16} grupos={len(set(l)):>3}  silueta={silhouette_score(X[val], l):>7.4f}  "
          f"DB={davies_bouldin_score(X[val], l):>6.3f}  radio={radio(lat[val],lon[val],l):>6.1f} km")

print("\nSobre los 4 915 puntos (HDBSCAN obligado a incluir el ruido como un grupo más):")
lab_forzado = np.where(lab_h == -1, lab_h.max()+1, lab_h)
for nom, lb in [("HDBSCAN+ruido", lab_forzado), ("K-Means k=81", km81.labels_), ("REGIÓN", reg)]:
    print(f"  {nom:<16} grupos={len(set(lb)):>3}  silueta={silhouette_score(X, lb):>7.4f}  "
          f"DB={davies_bouldin_score(X, lb):>6.3f}")

print("\n" + "#"*72)
print("3 · ¿Las variables que metí son redundantes entre sí?")
print("#"*72)
c = geo[VARS + ["DISTANCIA_CAPITAL_KM"]].corr().round(3)
print(c.to_string())

print("\n" + "#"*72)
print("4 · Dispersión ponderada por recursos, no por grupos")
print("#"*72)
v = geo[val].copy(); v["C"] = lab_h[val]
fuera = ~v["REGIÓN"].str.upper().isin(["LIMA","CUSCO"])
pf = v.groupby("C").apply(lambda g: (~g["REGIÓN"].str.upper().isin(["LIMA","CUSCO"])).mean(),
                          include_groups=False)
tam = v.groupby("C").size()
limpios = pf[pf == 1.0].index
print(f"Polos 100 % fuera del circuito : {len(limpios)} de {len(pf)}  ({len(limpios)/len(pf)*100:.0f} % de los polos)")
print(f"Recursos en esos polos         : {tam[limpios].sum()} de {tam.sum()}  "
      f"({tam[limpios].sum()/tam.sum()*100:.0f} % de los recursos)")
print(f"Tamaño medio polo limpio       : {tam[limpios].mean():.1f} recursos")
print(f"Tamaño medio polo con Lima/Cusco: {tam[~tam.index.isin(limpios)].mean():.1f} recursos")

print("\n" + "#"*72)
print("5 · Cuánto del inventario queda realmente fuera de un itinerario")
print("#"*72)
n_tot = len(df); sin_coord = n_tot - len(geo); ruido = int((~val).sum())
print(f"Inventario total                 : {n_tot}")
print(f"Sin coordenadas (no ruteable)    : {sin_coord}  ({sin_coord/n_tot*100:.1f} %)")
print(f"Aislados por HDBSCAN             : {ruido}  ({ruido/n_tot*100:.1f} %)")
print(f"TOTAL no encadenable en una ruta : {sin_coord+ruido}  ({(sin_coord+ruido)/n_tot*100:.1f} %)")
print(f"Recursos que sí entran a un polo : {int(val.sum())}  ({val.sum()/n_tot*100:.1f} %)")

print("\n" + "#"*72)
print("6 · ¿La altitud es bimodal como afirmé?")
print("#"*72)
a = geo.ALTITUD.to_numpy(float)
hist, edges = np.histogram(a, bins=14)
for i in range(14):
    print(f"  {edges[i]:>6.0f}–{edges[i+1]:>6.0f} m  {'█'*int(hist[i]/18):<40} {hist[i]:>4}")
print(f"\n  bajo 500 m : {(a<500).sum():>4}   entre 500 y 2000 m : {((a>=500)&(a<2000)).sum():>4}   "
      f"sobre 2000 m : {(a>=2000).sum():>4}")

print("\n" + "#"*72)
print("7 · Estabilidad: ¿81 polos es un resultado o una casualidad del parámetro?")
print("#"*72)
for mcs in (10, 12, 15, 18, 20, 22):
    hh = HDBSCAN(min_cluster_size=mcs).fit(X)
    v_ = hh.labels_ != -1
    print(f"  mcs={mcs:>3}  grupos={len(set(hh.labels_[v_])):>3}  ruido={(~v_).sum():>5}  "
          f"silueta={silhouette_score(X[v_], hh.labels_[v_]):>7.4f}  radio={radio(lat,lon,hh.labels_):>6.1f} km")
