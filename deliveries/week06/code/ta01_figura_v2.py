"""Figura de selección de modelo TA-01 v2."""
import sys, warnings, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from sklearn.cluster import AgglomerativeClustering, HDBSCAN
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings("ignore")

R = 6371.0; K = 0.06; UMBRAL = 80; MIN = 5
V1, V2, INK, MUTE, GRID, SURF = "#C2410C", "#0D9488", "#1A1D21", "#6B7280", "#E4E7EB", "#FCFCFB"
HORA = 1.6 / 40

df = pd.read_csv(sys.argv[1], sep=None, engine="python")
VARS = ["latitud", "longitud", "ALTITUD", "INDICE_COSTO_LOGISTICO"]
g = df.dropna(subset=VARS).copy()
lat, lon, alt = (g[c].to_numpy(float) for c in ("latitud", "longitud", "ALTITUD"))
la = np.radians(lat)[:, None].astype(np.float32); lo = np.radians(lon)[:, None].astype(np.float32)
a = np.sin((la - la.T) / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2
DG = (2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))).astype(np.float32); del a, la, lo
DV = np.sqrt(DG ** 2 + (np.abs(alt[:, None] - alt[None, :]).astype(np.float32) * K) ** 2)

X = StandardScaler().fit_transform(g[VARS].to_numpy(float))
l1 = HDBSCAN(min_cluster_size=15).fit(X).labels_
l2 = AgglomerativeClustering(n_clusters=None, distance_threshold=UMBRAL,
                             metric="precomputed", linkage="complete").fit_predict(DV)

def diam(lab):
    out = []
    for gr in np.unique(lab):
        if gr == -1: continue
        m = lab == gr
        if m.sum() < MIN: continue
        out.append((int(gr), int(m.sum()), float(DG[np.ix_(m, m)].max())))
    return pd.DataFrame(out, columns=["g", "n", "d"])

d1, d2 = diam(l1), diam(l2)
g["POLO"] = [x if x in set(d2.g) else -1 for x in l2]

fig, ax = plt.subplots(1, 3, figsize=(16.2, 6.1), facecolor=SURF)
for a_ in ax: a_.set_facecolor(SURF)

# ── 1 · distribución de diámetros ──
rng = np.random.default_rng(3)
for i, (dd, col, nom) in enumerate([(d1, V1, "v1 · HDBSCAN"), (d2, V2, "v2 · enlace completo")]):
    x = i + rng.uniform(-.17, .17, len(dd))
    ax[0].scatter(x, dd.d, s=13, color=col, alpha=.55, lw=0, zorder=3)
    bp = ax[0].boxplot([dd.d], positions=[i], widths=.46, showfliers=False,
                       patch_artist=True, zorder=4,
                       medianprops=dict(color=INK, lw=2.2),
                       boxprops=dict(facecolor="none", edgecolor=col, lw=2),
                       whiskerprops=dict(color=col, lw=1.6),
                       capprops=dict(color=col, lw=1.6))
    ypos = dd.d.max() if i == 0 else 190
    ax[0].annotate(f"max {dd.d.max():.0f} km · {dd.d.max()*HORA:.1f} h", (i, dd.d.max()),
                   xytext=(i + .30, ypos), fontsize=10.5, weight="bold", color=col,
                   va="center", ha="left",
                   arrowprops=None if i == 0 else dict(arrowstyle="-", color=col, lw=1.1,
                                                       shrinkA=2, shrinkB=6))
ax[0].axhline(UMBRAL, color=V2, ls="--", lw=1.6, zorder=2)
ax[0].text(1.73, UMBRAL + 8, "techo de 80 km garantizado por el enlace completo",
           fontsize=9, color=V2, ha="right", va="bottom", style="italic")
ax[0].set_xticks([0, 1]); ax[0].set_xticklabels(["v1 · HDBSCAN\n81 polos", "v2 · enlace completo\n222 polos"], fontsize=10)
ax[0].set_ylabel("Diámetro del polo (km geodésicos)", fontsize=10.5, color=INK)
ax[0].set_title("Recorribilidad: el radio medio escondía la cola\n"
                "cada punto es un polo", fontsize=11.8, weight="bold", loc="left", color=INK, pad=12)
ax[0].set_xlim(-.55, 1.75); ax[0].set_ylim(0, 470)

# ── 2 · la paradoja de la silueta ──
from sklearn.metrics import silhouette_score
o1, o2 = l1 != -1, g.POLO.to_numpy() != -1
sil = {
    "En el espacio\nestandarizado\n(lo que optimiza v1)": (
        silhouette_score(X[o1], l1[o1]),
        silhouette_score(X[o2], g.POLO.to_numpy()[o2])),
    "En la métrica\nde viaje\n(lo que importa al producto)": (
        silhouette_score(DV[np.ix_(o1, o1)], l1[o1], metric="precomputed"),
        silhouette_score(DV[np.ix_(o2, o2)], g.POLO.to_numpy()[o2], metric="precomputed")),
}
x = np.arange(2); w = .34
for j, (col, nom) in enumerate([(V1, "v1 · HDBSCAN"), (V2, "v2 · enlace completo")]):
    vals = [v[j] for v in sil.values()]
    b = ax[1].bar(x + (j - .5) * (w + .02), vals, w, color=col, label=nom, zorder=3)
    for r, v in zip(b, vals):
        ax[1].text(r.get_x() + r.get_width() / 2, v + .015, f"{v:.3f}",
                   ha="center", fontsize=10.5, weight="bold", color=INK)
ax[1].set_xticks(x); ax[1].set_xticklabels(sil.keys(), fontsize=9.5)
ax[1].set_ylabel("Coeficiente de silueta", fontsize=10.5, color=INK)
ax[1].set_title("La silueta no es neutral:\ncada modelo gana en el espacio que optimiza",
                fontsize=11.8, weight="bold", loc="left", color=INK, pad=12)
ax[1].set_ylim(0, .78); ax[1].legend(fontsize=9.5, frameon=False, loc="upper center", ncol=1)

for a_ in ax[:2]:
    a_.grid(axis="y", color=GRID, lw=.8, zorder=0); a_.set_axisbelow(True)
    a_.tick_params(labelsize=9.5, colors=MUTE)
    for s in ("top", "right"): a_.spines[s].set_visible(False)
    for s in ("left", "bottom"): a_.spines[s].set_color(GRID)

# ── 3 · mapa, color secuencial por diámetro ──
val = g[g.POLO != -1]; iso = g[g.POLO == -1]
dmap = dict(zip(d2.g, d2.d))
ax[2].scatter(iso.longitud, iso.latitud, s=7, c="#C9CFD6", marker="x", lw=.6, zorder=2,
              label=f"no encadenables · {len(iso)}")
sc = ax[2].scatter(val.longitud, val.latitud, s=7, lw=0, zorder=3,
                   c=[dmap[p] for p in val.POLO], cmap="YlGnBu", vmin=0, vmax=80)
cb = fig.colorbar(sc, ax=ax[2], fraction=.036, pad=.02)
cb.set_label("Diámetro del polo (km)", fontsize=9.5, color=MUTE)
cb.ax.tick_params(labelsize=9, colors=MUTE); cb.outline.set_edgecolor(GRID)
ax[2].set_title(f"222 polos sobre {len(val)} recursos\ntodos por debajo de 80 km",
                fontsize=11.8, weight="bold", loc="left", color=INK, pad=12)
ax[2].set_xlabel("Longitud", fontsize=10, color=MUTE); ax[2].set_ylabel("Latitud", fontsize=10, color=MUTE)
ax[2].set_aspect(1.0); ax[2].grid(color=GRID, lw=.7, zorder=0); ax[2].set_axisbelow(True)
ax[2].tick_params(labelsize=9.5, colors=MUTE)
ax[2].legend(fontsize=9, frameon=False, loc="lower left")
for s in ("top", "right"): ax[2].spines[s].set_visible(False)
for s in ("left", "bottom"): ax[2].spines[s].set_color(GRID)

fig.suptitle("DreemGO · TA-01 v2 — polos con diámetro acotado por construcción",
             fontsize=13.6, weight="bold", x=.007, ha="left", color=INK)
fig.text(.007, .012,
         "4 915 recursos geolocalizables del Inventario Nacional de Recursos Turísticos (MINCETUR) · "
         "distancia de viaje = haversine ⊕ desnivel × 0,06 km/m · horas a 40 km/h con factor de sinuosidad 1,6",
         fontsize=8.8, color=MUTE)
fig.tight_layout(rect=[0, .035, 1, .948])
fig.savefig("ta01_seleccion_modelo_v2.png", dpi=170, facecolor=SURF)
print("ok")
