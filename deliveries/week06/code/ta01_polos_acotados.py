"""
DreemGO · TA-01 v2 — polos con diámetro acotado por construcción

Problema de la v1: HDBSCAN optimiza densidad, no recorribilidad. El radio medio
salía 30,2 km pero el diámetro mediano era 65 km y el máximo 428 km — polos de
doce horas de punta a punta, que no son polos.

Solución: agrupamiento jerárquico con enlace completo sobre una distancia de
viaje efectiva. El enlace completo acota el diámetro del conglomerado por
construcción: si el umbral es D, NINGÚN par de recursos del mismo polo supera D.

Distancia de viaje efectiva
---------------------------
    d_efectiva = sqrt( d_haversine² + (Δaltitud · k)² )

con k = 0,06 km por metro de desnivel: 1 000 m de desnivel pesan como 60 km de
llano. El valor se eligió por barrido conjunto de (D, k) buscando que ningún polo
supere ~1 300 m de rango altitudinal, porque el usuario declara una altitud máxima
tolerada y un polo que va de 200 m a 4 000 m le sirve solo a medias.

Uso:  python ta01_polos_acotados.py <ruta_master_dataset.csv>
"""
import sys, warnings
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, HDBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

warnings.filterwarnings("ignore")
R_TIERRA = 6371.0
K_DESNIVEL = 0.06          # km equivalentes por metro de desnivel (ver barrido en ModelSelection 5.7)
TAM_MIN = 5                # un polo por debajo de esto no sostiene un itinerario
RUTA = sys.argv[1] if len(sys.argv) > 1 else "dreemgo_master_dataset.csv"


def matriz_haversine(lat, lon):
    la = np.radians(lat)[:, None].astype(np.float32)
    lo = np.radians(lon)[:, None].astype(np.float32)
    a = (np.sin((la - la.T) / 2) ** 2
         + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2)
    return (2 * R_TIERRA * np.arcsin(np.sqrt(np.clip(a, 0, 1)))).astype(np.float32)


def matriz_viaje(lat, lon, alt):
    d = matriz_haversine(lat, lon)
    dz = np.abs(alt[:, None] - alt[None, :]).astype(np.float32) * K_DESNIVEL
    return np.sqrt(d ** 2 + dz ** 2)


def perfil(lat, lon, alt, etiquetas, D):
    """Diámetro, radio y desnivel de cada grupo con al menos TAM_MIN recursos."""
    filas = []
    for gr in np.unique(etiquetas):
        if gr == -1:
            continue
        m = etiquetas == gr
        n = int(m.sum())
        if n < TAM_MIN:
            continue
        sub = D[np.ix_(m, m)]
        cla, clo = lat[m].mean(), lon[m].mean()
        la, lo = np.radians(lat[m]), np.radians(lon[m])
        la0, lo0 = np.radians(cla), np.radians(clo)
        h = np.sin((la - la0) / 2) ** 2 + np.cos(la) * np.cos(la0) * np.sin((lo - lo0) / 2) ** 2
        filas.append({
            "grupo": int(gr), "n": n,
            "diametro_km": float(sub.max()),
            "radio_km": float((2 * R_TIERRA * np.arcsin(np.sqrt(np.clip(h, 0, 1)))).mean()),
            "desnivel_m": float(alt[m].max() - alt[m].min()),
        })
    return pd.DataFrame(filas)


def resumen(nombre, p, n_total, n_asignados):
    if p.empty:
        return {"modelo": nombre, "polos": 0}
    return {
        "modelo": nombre,
        "polos": len(p),
        "recursos": int(p.n.sum()),
        "cobertura_%": round(p.n.sum() / n_total * 100, 1),
        "diam_mediana": round(p.diametro_km.median(), 1),
        "diam_p90": round(p.diametro_km.quantile(.9), 1),
        "diam_max": round(p.diametro_km.max(), 1),
        "radio_medio": round(np.average(p.radio_km, weights=p.n), 1),
        "desnivel_mediana": round(p.desnivel_m.median()),
    }


# ───────────────────────── carga ─────────────────────────
print("=" * 78)
print("TA-01 v2 · polos con diámetro acotado")
print("=" * 78)

df = pd.read_csv(RUTA, sep=None, engine="python")
VARS = ["latitud", "longitud", "ALTITUD", "INDICE_COSTO_LOGISTICO"]
geo = df.dropna(subset=VARS).copy()
lat = geo["latitud"].to_numpy(float)
lon = geo["longitud"].to_numpy(float)
alt = geo["ALTITUD"].to_numpy(float)
N = len(geo)
print(f"\nRecursos geolocalizables: {N}")
print(f"Distancia de viaje: haversine + desnivel × {K_DESNIVEL} km/m")
print(f"Tamaño mínimo de polo: {TAM_MIN} recursos\n")

D_viaje = matriz_viaje(lat, lon, alt)
D_geo = matriz_haversine(lat, lon)
print(f"Matriz de distancias: {D_viaje.nbytes/1e6:.0f} MB\n")

filas = []

# ───────────────── referencia: HDBSCAN de la v1 ─────────────────
X = StandardScaler().fit_transform(geo[VARS].to_numpy(float))
lab_h = HDBSCAN(min_cluster_size=15).fit(X).labels_
p_h = perfil(lat, lon, alt, lab_h, D_geo)
filas.append(resumen("v1 · HDBSCAN mcs=15", p_h, N, (lab_h != -1).sum()))

lab_h10 = HDBSCAN(min_cluster_size=10).fit(X).labels_
filas.append(resumen("v1 · HDBSCAN mcs=10", perfil(lat, lon, alt, lab_h10, D_geo), N, 0))

# ───────────────── barrido del umbral de diámetro ─────────────────
print("-" * 78)
print("BARRIDO · enlace completo sobre distancia de viaje")
print("-" * 78)
print(f"{'umbral':>8} {'polos':>7} {'recursos':>9} {'cob.%':>7} "
      f"{'diam med':>9} {'diam max':>9} {'radio':>7} {'desniv':>7}")

etiquetas = {}
for D_umbral in (60, 80, 100, 120):
    ac = AgglomerativeClustering(n_clusters=None, distance_threshold=D_umbral,
                                 metric="precomputed", linkage="complete")
    lab = ac.fit_predict(D_viaje)
    etiquetas[D_umbral] = lab
    p = perfil(lat, lon, alt, lab, D_geo)
    r = resumen(f"v2 · enlace completo D≤{D_umbral}", p, N, len(lab))
    filas.append(r)
    print(f"{D_umbral:>8} {r['polos']:>7} {r['recursos']:>9} {r['cobertura_%']:>7} "
          f"{r['diam_mediana']:>9} {r['diam_max']:>9} {r['radio_medio']:>7} "
          f"{r['desnivel_mediana']:>7}")

print("\n(el diámetro está en km geodésicos; el umbral es en km de viaje efectivo,\n"
      " por eso el diámetro geodésico máximo queda por debajo del umbral)")

# ───────────────── comparativa ─────────────────
print("\n" + "=" * 78)
print("COMPARATIVA")
print("=" * 78)
comp = pd.DataFrame(filas)
print(comp.to_string(index=False))

# ───────────────── traducción a horas ─────────────────
print("\n" + "=" * 78)
print("¿CABE EL POLO EN UN DÍA DE VIAJE?")
print("=" * 78)
print("Supuesto: 40 km/h de media en carretera andina, factor de sinuosidad 1,6\n")
print(f"{'modelo':<32} {'p50':>8} {'p90':>8} {'max':>8}")
for r in filas:
    if r.get("polos"):
        f = 1.6 / 40
        print(f"{r['modelo']:<32} {r['diam_mediana']*f:>7.1f}h {r['diam_p90']*f:>7.1f}h "
              f"{r['diam_max']*f:>7.1f}h")

# ───────────────── elección y salida ─────────────────
D_ELEGIDO = 80
lab = etiquetas[D_ELEGIDO]
p = perfil(lat, lon, alt, lab, D_geo)
validos = set(p.grupo)
geo["POLO"] = np.where(np.isin(lab, list(validos)), lab, -1)
val = geo[geo.POLO != -1]

print("\n" + "=" * 78)
print(f"MODELO ELEGIDO · enlace completo, umbral {D_ELEGIDO} km de viaje efectivo")
print("=" * 78)
print(f"Polos con >= {TAM_MIN} recursos : {len(p)}")
print(f"Recursos en un polo       : {len(val)} ({len(val)/len(df)*100:.1f} % del inventario)")
print(f"Descartados por aislados  : {(geo.POLO == -1).sum()}")
print(f"Diámetro  mediana {p.diametro_km.median():.1f} km · p90 {p.diametro_km.quantile(.9):.1f} km "
      f"· max {p.diametro_km.max():.1f} km")
print(f"Desnivel  mediana {p.desnivel_m.median():.0f} m · max {p.desnivel_m.max():.0f} m")

# La silueta se mide en la MISMA métrica de viaje que el modelo optimiza, y
# también en el espacio estandarizado que optimiza HDBSCAN. Cada modelo gana en
# su propio espacio: por eso la silueta no puede decidir esta elección (§5.8).
ok = geo.POLO.to_numpy() != -1
Dv = D_viaje[np.ix_(ok, ok)]
Xv = StandardScaler().fit_transform(val[VARS].to_numpy(float))
print(f"Silueta en métrica de viaje      : "
      f"{silhouette_score(Dv, val.POLO.to_numpy(), metric='precomputed'):.4f}")
print(f"Silueta en espacio estandarizado : {silhouette_score(Xv, val.POLO):.4f}")
okh = lab_h != -1
print(f"  (HDBSCAN v1, misma métrica de viaje: "
      f"{silhouette_score(D_viaje[np.ix_(okh, okh)], lab_h[okh], metric='precomputed'):.4f})")

sat = val["REGIÓN"].str.upper().isin(["LIMA", "CUSCO"])
pf = val.groupby("POLO").apply(
    lambda g: (~g["REGIÓN"].str.upper().isin(["LIMA", "CUSCO"])).mean(), include_groups=False)
tam = val.groupby("POLO").size()
limpios = pf[pf == 1.0].index
print(f"\nCobertura: {len(limpios)} de {len(pf)} polos sin ningún recurso de Lima o Cusco "
      f"({len(limpios)/len(pf)*100:.0f} %)")
print(f"           {tam[limpios].sum()} de {tam.sum()} recursos "
      f"({tam[limpios].sum()/tam.sum()*100:.0f} %)")

val.groupby("POLO").agg(
    recursos=("POLO", "size"), alt_media=("ALTITUD", "mean"),
    regiones=("REGIÓN", "nunique"), region_top=("REGIÓN", lambda s: s.mode().iat[0]),
    jerarquia_media=("JERARQUIA_OFICIAL", "mean")).reset_index().merge(
    p.rename(columns={"grupo": "POLO"})[["POLO", "diametro_km", "radio_km", "desnivel_m"]],
    on="POLO").to_csv("perfil_polos_v2.csv", sep=";", index=False)

geo[["CODIGO DEL RECURSO", "NOMBRE DEL RECURSO", "REGIÓN", "latitud", "longitud",
     "ALTITUD", "ZONA_CLIMATICA", "JERARQUIA_OFICIAL", "POLO"]].to_csv(
    "polos_asignados_v2.csv", sep=";", index=False)
comp.to_csv("comparativa_polos_v2.csv", sep=";", index=False)
print("\nArchivos: polos_asignados_v2.csv · perfil_polos_v2.csv · comparativa_polos_v2.csv")
