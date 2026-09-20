"""DreemGO · TA-01 — modelo seleccionado (HDBSCAN) y figuras de la Semana 6."""
import sys, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, HDBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score

warnings.filterwarnings("ignore")
R = 6371.0
RUTA = sys.argv[1]

def hav(lat, lon, lat0, lon0):
    la, lo, la0, lo0 = map(np.radians, (lat, lon, lat0, lon0))
    a = np.sin((la-la0)/2)**2 + np.cos(la)*np.cos(la0)*np.sin((lo-lo0)/2)**2
    return 2*R*np.arcsin(np.sqrt(np.clip(a, 0, 1)))

df = pd.read_csv(RUTA, sep=None, engine="python")
VARS = ["latitud", "longitud", "ALTITUD", "INDICE_COSTO_LOGISTICO"]
geo = df.dropna(subset=VARS).copy()
lat = geo["latitud"].to_numpy(float); lon = geo["longitud"].to_numpy(float)
X = StandardScaler().fit_transform(geo[VARS].to_numpy(float))

h = HDBSCAN(min_cluster_size=15).fit(X)
geo["CLUSTER"] = h.labels_
km = KMeans(n_clusters=29, n_init=10, random_state=42).fit(X)
geo["CLUSTER_KM"] = km.labels_

val = geo[geo.CLUSTER != -1]
print("="*70); print("MODELO SELECCIONADO · HDBSCAN(min_cluster_size=15)"); print("="*70)
print(f"Conglomerados        : {val.CLUSTER.nunique()}")
print(f"Recursos agrupados   : {len(val)} ({len(val)/len(geo)*100:.1f} %)")
print(f"Marcados como aislados: {(geo.CLUSTER==-1).sum()} ({(geo.CLUSTER==-1).mean()*100:.1f} %)")

perfil = val.groupby("CLUSTER").agg(
    n=("CLUSTER","size"), alt=("ALTITUD","mean"),
    la=("latitud","mean"), lo=("longitud","mean"),
    regs=("REGIÓN", "nunique"), top=("REGIÓN", lambda s: s.mode().iat[0])).reset_index()
perfil["radio_km"] = [hav(val.loc[val.CLUSTER==c,"latitud"].to_numpy(float),
                          val.loc[val.CLUSTER==c,"longitud"].to_numpy(float),
                          perfil.loc[perfil.CLUSTER==c,"la"].iat[0],
                          perfil.loc[perfil.CLUSTER==c,"lo"].iat[0]).mean()
                      for c in perfil.CLUSTER]

print(f"\nRadio medio ponderado : {np.average(perfil.radio_km, weights=perfil.n):.1f} km")
print(f"Radio mediano         : {perfil.radio_km.median():.1f} km")
for u in (30, 50, 80):
    k_ = (perfil.radio_km <= u).sum()
    print(f"Conglomerados con radio <= {u:>2} km : {k_:>3} de {len(perfil)} "
          f"({k_/len(perfil)*100:.0f} %)  ·  {int(perfil.loc[perfil.radio_km<=u,'n'].sum())} recursos")

sat = val["REGIÓN"].str.upper().isin(["LIMA","CUSCO"])
pf = val.groupby("CLUSTER").apply(
    lambda g: (~g["REGIÓN"].str.upper().isin(["LIMA","CUSCO"])).mean(), include_groups=False)
print(f"\nCOBERTURA")
print(f"Recursos fuera de Lima/Cusco        : {(~sat).sum()} ({(~sat).mean()*100:.1f} %)")
print(f"Conglomerados 100 % fuera del circuito: {(pf==1.0).sum()} de {len(pf)} "
      f"({(pf==1.0).mean()*100:.0f} %)")
print(f"Conglomerados multirregionales       : {(perfil.regs>1).sum()} de {len(perfil)} "
      f"({(perfil.regs>1).mean()*100:.0f} %)  ← invisibles para la partición por departamento")

print(f"\n{'─'*70}\nLOS 12 CONGLOMERADOS MÁS COMPACTOS\n{'─'*70}")
print(perfil.nsmallest(12,"radio_km")[["CLUSTER","n","alt","radio_km","regs","top"]]
      .to_string(index=False, float_format=lambda v: f"{v:.1f}"))

# ── figura ──
fig, ax = plt.subplots(1, 3, figsize=(15.5, 6.2))
INK, GRID = "#14181D", "#D5DBE1"

# 1 · comparativa de métricas
modelos = ["REGIÓN\n(baseline)", "REGIÓN×CAT\n(baseline)", "K-Means\nk=29", "HDBSCAN\nmcs=15"]
sil = [-0.0446, -0.3734, 0.4736, 0.6573]
cols = ["#A81F13", "#A81F13", "#7E5200", "#175E38"]
b = ax[0].bar(modelos, sil, color=cols, width=.62)
ax[0].axhline(0, color=INK, lw=1.2)
ax[0].set_ylabel("Coeficiente de silueta", fontsize=10.5)
ax[0].set_title("Cohesión: los baselines administrativos\nquedan por debajo de cero",
                fontsize=11.5, weight="bold", loc="left", color=INK)
for r, v in zip(b, sil):
    ax[0].text(r.get_x()+r.get_width()/2, v + (.035 if v > 0 else -.055),
               f"{v:.3f}", ha="center", fontsize=10, weight="bold", color=INK)
ax[0].set_ylim(-.52, .78); ax[0].tick_params(labelsize=9.5)
ax[0].grid(axis="y", color=GRID, lw=.7); ax[0].set_axisbelow(True)
for s in ("top","right"): ax[0].spines[s].set_visible(False)

# 2 · radio medio (métrica de producto)
mod2 = ["REGIÓN\n(baseline)", "K-Means\nk=29", "HDBSCAN\nmcs=15"]
rad = [72.8, 115.5, 30.2]
b = ax[1].bar(mod2, rad, color=["#A81F13", "#7E5200", "#175E38"], width=.55)
ax[1].set_ylabel("Radio medio del conglomerado (km)", fontsize=10.5)
ax[1].set_title("Recorribilidad: qué tan lejos está cada\nrecurso del centro de su polo",
                fontsize=11.5, weight="bold", loc="left", color=INK)
for r, v in zip(b, rad):
    ax[1].text(r.get_x()+r.get_width()/2, v+3, f"{v:.1f} km",
               ha="center", fontsize=10, weight="bold", color=INK)
ax[1].set_ylim(0, 132); ax[1].tick_params(labelsize=9.5)
ax[1].grid(axis="y", color=GRID, lw=.7); ax[1].set_axisbelow(True)
for s in ("top","right"): ax[1].spines[s].set_visible(False)

# 3 · mapa
ru = geo[geo.CLUSTER == -1]
ax[2].scatter(ru.longitud, ru.latitud, s=5, c="#C3CAD2", marker="x",
              lw=.6, label=f"aislados ({len(ru)})")
rng = np.random.default_rng(7)
cmap = plt.get_cmap("turbo")
for i, c in enumerate(sorted(val.CLUSTER.unique())):
    g = val[val.CLUSTER == c]
    ax[2].scatter(g.longitud, g.latitud, s=7, color=cmap(rng.random()), lw=0)
ax[2].set_title(f"{val.CLUSTER.nunique()} polos turísticos latentes\n"
                "(colores arbitrarios · x = recurso aislado)",
                fontsize=11.5, weight="bold", loc="left", color=INK)
ax[2].set_xlabel("Longitud", fontsize=10); ax[2].set_ylabel("Latitud", fontsize=10)
ax[2].tick_params(labelsize=9.5); ax[2].set_aspect(1.0)
ax[2].grid(color=GRID, lw=.6); ax[2].set_axisbelow(True)
ax[2].legend(loc="lower left", fontsize=9, frameon=False)
for s in ("top","right"): ax[2].spines[s].set_visible(False)

fig.suptitle("DreemGO · TA-01 — Selección de modelo de agrupamiento espacio-temporal",
             fontsize=13.5, weight="bold", x=.008, ha="left", color=INK)
fig.text(.008, .012, "4 915 recursos geolocalizables del Inventario Nacional de Recursos "
         "Turísticos (MINCETUR) · variables: latitud, longitud, altitud, índice de lejanía",
         fontsize=9, color="#6B747E")
fig.tight_layout(rect=[0, .035, 1, .955])
fig.savefig("ta01_seleccion_modelo.png", dpi=170, facecolor="white")
print("\nFigura: ta01_seleccion_modelo.png")

geo[["CODIGO DEL RECURSO","NOMBRE DEL RECURSO","REGIÓN","latitud","longitud",
     "ALTITUD","ZONA_CLIMATICA","CLUSTER","CLUSTER_KM"]].to_csv(
    "clusters_asignados.csv", sep=";", index=False)
perfil.to_csv("perfil_clusters_hdbscan.csv", sep=";", index=False)
print("CSV: clusters_asignados.csv · perfil_clusters_hdbscan.csv")
