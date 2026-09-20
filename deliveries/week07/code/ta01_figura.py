"""Figura de TA-01 con la comparación controlada (no la primera, que era injusta)."""
import sys, warnings, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, HDBSCAN
warnings.filterwarnings("ignore")

df = pd.read_csv(sys.argv[1], sep=None, engine="python")
V = ["latitud", "longitud", "ALTITUD", "INDICE_COSTO_LOGISTICO"]
geo = df.dropna(subset=V).copy()
X = StandardScaler().fit_transform(geo[V].to_numpy(float))
h = HDBSCAN(min_cluster_size=15).fit(X)
geo["C"] = h.labels_
val = geo[geo.C != -1]

INK, GRID, MUT = "#14181D", "#D5DBE1", "#6B747E"
ROJO, AMB, VERD = "#A81F13", "#7E5200", "#175E38"
fig, ax = plt.subplots(1, 3, figsize=(16, 6.1))

# ── 1 · comparación controlada ──
mod = ["REGIÓN\n25 grupos", "K-Means\n74 grupos", "HDBSCAN\n81 grupos"]
sil = [-0.0287, 0.6260, 0.6573]
b = ax[0].bar(mod, sil, color=[ROJO, AMB, VERD], width=.58)
ax[0].axhline(0, color=INK, lw=1.2)
for r, v in zip(b, sil):
    ax[0].text(r.get_x()+r.get_width()/2, v + (.028 if v > 0 else -.052),
               f"{v:.3f}", ha="center", fontsize=11, weight="bold", color=INK)
ax[0].set_ylabel("Coeficiente de silueta", fontsize=10.5)
ax[0].set_title("Comparación controlada\nmismos 3 760 recursos · nº de grupos comparable",
                fontsize=11.5, weight="bold", loc="left", color=INK)
ax[0].set_ylim(-.14, .78); ax[0].tick_params(labelsize=9.5)
ax[0].grid(axis="y", color=GRID, lw=.7); ax[0].set_axisbelow(True)
ax[0].text(.5, -.11, "la partición administrativa queda por debajo de cero",
           transform=ax[0].transAxes, ha="center", fontsize=9, color=MUT, style="italic")
for s_ in ("top", "right"): ax[0].spines[s_].set_visible(False)

# ── 2 · el radio depende de k ──
ks = [25, 29, 48, 81, 120]; rad = [130.1, 115.5, 78.0, 51.1, 36.1]
ax[1].plot(ks, rad, "-o", color=AMB, lw=2.2, ms=7, label="K-Means (varía con k)")
ax[1].scatter([81], [30.2], s=130, color=VERD, zorder=5, label="HDBSCAN mcs=15")
ax[1].axhline(68.6, color=ROJO, ls="--", lw=1.6, label="Baseline REGIÓN (25 grupos)")
ax[1].annotate("con k=29 parecía\npeor que el baseline", xy=(29, 115.5), xytext=(44, 122),
               fontsize=9, color=MUT,
               arrowprops=dict(arrowstyle="->", color=MUT, lw=1))
ax[1].annotate("30,2 km", xy=(81, 30.2), xytext=(88, 22), fontsize=10,
               weight="bold", color=VERD)
ax[1].set_xlabel("Número de grupos", fontsize=10.5)
ax[1].set_ylabel("Radio medio del conglomerado (km)", fontsize=10.5)
ax[1].set_title("La métrica de recorribilidad cae con el nº de grupos\npor eso solo vale comparándola a igual k",
                fontsize=11.5, weight="bold", loc="left", color=INK)
ax[1].legend(fontsize=9, frameon=False, loc="upper right")
ax[1].set_ylim(0, 148); ax[1].tick_params(labelsize=9.5)
ax[1].grid(color=GRID, lw=.7); ax[1].set_axisbelow(True)
for s_ in ("top", "right"): ax[1].spines[s_].set_visible(False)

# ── 3 · mapa ──
ru = geo[geo.C == -1]
ax[2].scatter(ru.longitud, ru.latitud, s=5, c="#C3CAD2", marker="x", lw=.6,
              label=f"aislados · {len(ru)} (18,8 %)")
rng = np.random.default_rng(7); cmap = plt.get_cmap("turbo")
for c in sorted(val.C.unique()):
    g = val[val.C == c]
    ax[2].scatter(g.longitud, g.latitud, s=7, color=cmap(rng.random()), lw=0)
ax[2].set_title(f"{val.C.nunique()} polos sobre {len(val)} recursos\n"
                "colores arbitrarios · x = no encadenable",
                fontsize=11.5, weight="bold", loc="left", color=INK)
ax[2].set_xlabel("Longitud", fontsize=10); ax[2].set_ylabel("Latitud", fontsize=10)
ax[2].tick_params(labelsize=9.5); ax[2].set_aspect(1.0)
ax[2].grid(color=GRID, lw=.6); ax[2].set_axisbelow(True)
ax[2].legend(loc="lower left", fontsize=9, frameon=False)
for s_ in ("top", "right"): ax[2].spines[s_].set_visible(False)

fig.suptitle("DreemGO · TA-01 — Selección de modelo de agrupamiento",
             fontsize=13.5, weight="bold", x=.007, ha="left", color=INK)
fig.text(.007, .012, "4 915 recursos geolocalizables del Inventario Nacional de Recursos Turísticos "
         "(MINCETUR) · variables: latitud, longitud, altitud, índice de lejanía · "
         "silueta de HDBSCAN calculada solo sobre los recursos que agrupa",
         fontsize=8.8, color=MUT)
fig.tight_layout(rect=[0, .035, 1, .952])
fig.savefig("ta01_seleccion_modelo.png", dpi=170, facecolor="white")
print("ok")
