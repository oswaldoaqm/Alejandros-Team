"""
DreemGO · TA-01 — Agrupamiento espacio-temporal de destinos
Semana 6 · Selección de modelo

Compara K-Means y HDBSCAN contra el baseline de partición administrativa
(REGIÓN) usando métricas internas de cohesión y una métrica de producto:
la distancia real recorrible dentro de cada conglomerado.

Uso:  python run_clustering.py <ruta_master_dataset.csv>
"""
import sys, json, warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, HDBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

warnings.filterwarnings("ignore")
RNG = 42
R_TIERRA_KM = 6371.0

RUTA = sys.argv[1] if len(sys.argv) > 1 else "dreemgo_master_dataset.csv"


# ───────────────────────── utilidades ─────────────────────────
def haversine_matriz(lat, lon):
    """Matriz de distancias en km entre todos los pares (vectorizada)."""
    la = np.radians(lat)[:, None]
    lo = np.radians(lon)[:, None]
    dla = la - la.T
    dlo = lo - lo.T
    a = np.sin(dla / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin(dlo / 2) ** 2
    return 2 * R_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def radio_medio_km(lat, lon, etiquetas, min_tam=3):
    """
    Métrica de producto: distancia media al centroide geográfico dentro de
    cada grupo, ponderada por tamaño. Responde a '¿es recorrible este polo?'.
    Ignora ruido (-1) y grupos de menos de `min_tam` recursos.
    """
    total, peso = 0.0, 0
    for g in np.unique(etiquetas):
        if g == -1:
            continue
        m = etiquetas == g
        n = int(m.sum())
        if n < min_tam:
            continue
        cla, clo = lat[m].mean(), lon[m].mean()
        d = haversine_km_vector(lat[m], lon[m], cla, clo)
        total += d.mean() * n
        peso += n
    return total / peso if peso else float("nan")


def haversine_km_vector(lat, lon, lat0, lon0):
    la, lo = np.radians(lat), np.radians(lon)
    la0, lo0 = np.radians(lat0), np.radians(lon0)
    a = np.sin((la - la0) / 2) ** 2 + np.cos(la) * np.cos(la0) * np.sin((lo - lo0) / 2) ** 2
    return 2 * R_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def evaluar(nombre, X, etiquetas, lat, lon):
    """Métricas internas + métrica de producto para una partición dada."""
    mask = etiquetas != -1
    n_grupos = len(set(etiquetas[mask]))
    ruido = int((~mask).sum())
    fila = {
        "modelo": nombre,
        "n_grupos": n_grupos,
        "ruido": ruido,
        "silueta": np.nan,
        "davies_bouldin": np.nan,
        "calinski": np.nan,
        "radio_medio_km": radio_medio_km(lat, lon, etiquetas),
    }
    if n_grupos >= 2 and mask.sum() > n_grupos:
        fila["silueta"] = float(silhouette_score(X[mask], etiquetas[mask]))
        fila["davies_bouldin"] = float(davies_bouldin_score(X[mask], etiquetas[mask]))
        fila["calinski"] = float(calinski_harabasz_score(X[mask], etiquetas[mask]))
    return fila


# ───────────────────────── carga ─────────────────────────
print("=" * 74)
print("TA-01 · Agrupamiento espacio-temporal de destinos")
print("=" * 74)

df = pd.read_csv(RUTA, sep=None, engine="python")
print(f"\nDataset maestro: {df.shape[0]} registros · {df.shape[1]} columnas")

VARS = ["latitud", "longitud", "ALTITUD", "INDICE_COSTO_LOGISTICO"]
geo = df.dropna(subset=VARS).copy()
print(f"Geolocalizables y completos: {len(geo)} "
      f"({len(geo)/len(df)*100:.1f} %)  ·  descartados: {len(df)-len(geo)}")
print(f"Variables del modelo: {', '.join(VARS)}")

lat = geo["latitud"].to_numpy(float)
lon = geo["longitud"].to_numpy(float)
X = StandardScaler().fit_transform(geo[VARS].to_numpy(float))

resultados = []

# ───────────────── baseline: partición administrativa ─────────────────
print("\n" + "-" * 74)
print("BASELINE · partición por REGIÓN (división política)")
print("-" * 74)
base = geo["REGIÓN"].astype("category").cat.codes.to_numpy()
r = evaluar("Baseline · REGIÓN", X, base, lat, lon)
resultados.append(r)
print(f"  grupos={r['n_grupos']}  silueta={r['silueta']:.4f}  "
      f"DB={r['davies_bouldin']:.4f}  radio medio={r['radio_medio_km']:.1f} km")

# baseline 2: región x categoría (taxonomía MINCETUR)
base2 = (geo["REGIÓN"].astype(str) + "|" + geo["CATEGORÍA"].astype(str)) \
    .astype("category").cat.codes.to_numpy()
r = evaluar("Baseline · REGIÓN × CATEGORÍA", X, base2, lat, lon)
resultados.append(r)
print(f"  grupos={r['n_grupos']}  silueta={r['silueta']:.4f}  "
      f"DB={r['davies_bouldin']:.4f}  radio medio={r['radio_medio_km']:.1f} km")

# ───────────────── barrido de k para K-Means ─────────────────
print("\n" + "-" * 74)
print("K-MEANS · barrido de k")
print("-" * 74)
print(f"{'k':>4} {'silueta':>10} {'davies_b':>10} {'calinski':>11} {'radio_km':>10}")
barrido = []
for k in range(4, 31):
    km = KMeans(n_clusters=k, n_init=10, random_state=RNG).fit(X)
    e = evaluar(f"K-Means k={k}", X, km.labels_, lat, lon)
    barrido.append(e)
    if k <= 12 or k % 5 == 0:
        print(f"{k:>4} {e['silueta']:>10.4f} {e['davies_bouldin']:>10.4f} "
              f"{e['calinski']:>11.1f} {e['radio_medio_km']:>10.1f}")

mejor_sil = max(barrido, key=lambda e: e["silueta"])
mejor_db = min(barrido, key=lambda e: e["davies_bouldin"])
print(f"\n  mejor silueta      → {mejor_sil['modelo']}  ({mejor_sil['silueta']:.4f})")
print(f"  mejor Davies-Bouldin → {mejor_db['modelo']}  ({mejor_db['davies_bouldin']:.4f})")

k_elegido = int(mejor_sil["modelo"].split("=")[1])
km_final = KMeans(n_clusters=k_elegido, n_init=10, random_state=RNG).fit(X)
resultados.append(evaluar(f"K-Means k={k_elegido} (elegido)", X, km_final.labels_, lat, lon))

# ───────────────── HDBSCAN ─────────────────
print("\n" + "-" * 74)
print("HDBSCAN · barrido de min_cluster_size")
print("-" * 74)
print(f"{'min_size':>9} {'grupos':>8} {'ruido':>8} {'silueta':>10} {'davies_b':>10} {'radio_km':>10}")
mejor_h, mejor_h_lab = None, None
for mcs in (15, 25, 40, 60, 90):
    h = HDBSCAN(min_cluster_size=mcs).fit(X)
    e = evaluar(f"HDBSCAN mcs={mcs}", X, h.labels_, lat, lon)
    print(f"{mcs:>9} {e['n_grupos']:>8} {e['ruido']:>8} {e['silueta']:>10.4f} "
          f"{e['davies_bouldin']:>10.4f} {e['radio_medio_km']:>10.1f}")
    if mejor_h is None or (e["silueta"] == e["silueta"] and e["silueta"] > mejor_h["silueta"]):
        mejor_h, mejor_h_lab = e, h.labels_
resultados.append(mejor_h)

# ───────────────── tabla comparativa ─────────────────
print("\n" + "=" * 74)
print("COMPARATIVA FINAL")
print("=" * 74)
comp = pd.DataFrame(resultados)[
    ["modelo", "n_grupos", "ruido", "silueta", "davies_bouldin", "radio_medio_km"]]
print(comp.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

base_sil = comp.loc[0, "silueta"]
base_rad = comp.loc[0, "radio_medio_km"]
fin_sil = float(mejor_sil["silueta"])
fin_rad = float(mejor_sil["radio_medio_km"])
print(f"\nGanancia sobre el baseline administrativo:")
print(f"  silueta        {base_sil:.4f} → {fin_sil:.4f}   ({(fin_sil-base_sil)/abs(base_sil)*100:+.1f} %)")
print(f"  radio medio    {base_rad:.1f} km → {fin_rad:.1f} km   "
      f"({(fin_rad-base_rad)/base_rad*100:+.1f} %)")

# ───────────────── perfil de los conglomerados ─────────────────
geo["CLUSTER"] = km_final.labels_
print("\n" + "=" * 74)
print(f"PERFIL DE LOS {k_elegido} CONGLOMERADOS (K-Means)")
print("=" * 74)
perfil = (geo.groupby("CLUSTER")
          .agg(recursos=("CLUSTER", "size"),
               alt_media=("ALTITUD", "mean"),
               lat=("latitud", "mean"),
               lon=("longitud", "mean"),
               regiones=("REGIÓN", lambda s: s.nunique()),
               region_top=("REGIÓN", lambda s: s.mode().iat[0]),
               zona_top=("ZONA_CLIMATICA", lambda s: s.mode().iat[0] if s.notna().any() else "—"))
          .reset_index())
perfil["radio_km"] = [
    haversine_km_vector(geo.loc[geo.CLUSTER == c, "latitud"].to_numpy(float),
                        geo.loc[geo.CLUSTER == c, "longitud"].to_numpy(float),
                        perfil.loc[perfil.CLUSTER == c, "lat"].iat[0],
                        perfil.loc[perfil.CLUSTER == c, "lon"].iat[0]).mean()
    for c in perfil["CLUSTER"]]
print(perfil[["CLUSTER", "recursos", "alt_media", "radio_km", "regiones",
              "region_top", "zona_top"]]
      .to_string(index=False, float_format=lambda v: f"{v:.1f}"))

# ───────────────── dispersión: cobertura fuera del circuito ─────────────────
print("\n" + "=" * 74)
print("COBERTURA DE CATÁLOGO")
print("=" * 74)
saturado = geo["REGIÓN"].str.upper().isin(["LIMA", "CUSCO"])
print(f"Recursos en Lima o Cusco:            {saturado.sum():>5}  ({saturado.mean()*100:.1f} %)")
print(f"Recursos fuera del circuito:         {(~saturado).sum():>5}  ({(~saturado).mean()*100:.1f} %)")
sin_sat = perfil.merge(
    geo.groupby("CLUSTER").apply(
        lambda g: (~g["REGIÓN"].str.upper().isin(["LIMA", "CUSCO"])).mean(),
        include_groups=False).rename("pct_fuera").reset_index(), on="CLUSTER")
n_limpios = int((sin_sat["pct_fuera"] == 1.0).sum())
print(f"Conglomerados 100 % fuera del circuito: {n_limpios} de {k_elegido}")
print("→ un recomendador que elija entre conglomerados, y no entre recursos sueltos,")
print(f"  tiene {n_limpios} salidas posibles que no contienen ningún recurso saturado.")

# ───────────────── salidas ─────────────────
geo[["CODIGO DEL RECURSO", "NOMBRE DEL RECURSO", "REGIÓN", "latitud", "longitud",
     "ALTITUD", "ZONA_CLIMATICA", "CLUSTER"]].to_csv(
    "clusters_asignados.csv", sep=";", index=False)
comp.to_csv("comparativa_modelos.csv", sep=";", index=False)
perfil.to_csv("perfil_clusters.csv", sep=";", index=False)
pd.DataFrame(barrido).to_csv("barrido_k.csv", sep=";", index=False)
print("\nArchivos escritos: clusters_asignados.csv · comparativa_modelos.csv · "
      "perfil_clusters.csv · barrido_k.csv")
