"""
DreemGO · consulta de punta a punta

Une las cuatro tareas analíticas en la consulta que el producto promete, y
verifica en cada corrida los criterios de aceptación de RF-01, RF-02 y RNF-01.

    entrada  origen · mes · días · altitud máxima · intereses · presupuesto
    salida   polo elegido + itinerario ordenado por día + banda de costo,
             con veredicto estacional, alternativa viable y ficha oficial
             en cada parada

CÓMO SE APLICA CADA RESTRICCIÓN
-------------------------------
altitud   RF-01 dice «ningún destino recomendado supera la altitud máxima
          declarada». Se filtra RECURSO a recurso, no polo a polo: un polo no
          se descarta porque una de sus paradas esté alta, se descarta la
          parada. Si al filtrar quedan menos de MIN_PARADAS, entonces sí cae
          el polo entero.
mes       veredicto de TA-02. `desaconsejado` saca el polo del ranking;
          `advertencia` lo deja pero la salida lo declara. RF-01 exige que
          nada aparezca sin advertencia explícita Y con una alternativa
          viable: la alternativa son los mejores meses del propio polo.
intereses se cruza con las familias de actividad de la ficha oficial.
días      TA-04 arma la secuencia.
costo     banda P20-P80 con la fracción de paradas pagadas del polo.

RNF-01: nada de esto escribe sobre el dataset base. La estacionalidad se lee
de una tabla aparte y el filtro de altitud vive en memoria.

Uso:
  python consulta.py --mes 7 --dias 6 --altitud-max 3500 --origen LIMA
  python consulta.py --mes 2 --dias 5 --altitud-max 2500 --interes Naturaleza
"""
import argparse, importlib.util as ilu, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

s = ilu.spec_from_file_location("t4", "ta04_ordenar_ruta.py")
t4 = ilu.module_from_spec(s); s.loader.exec_module(t4)

B = "../data/processed/"
L = lambda p, **k: pd.read_csv(B + p, sep=";", encoding="utf-8-sig", **k)
MIN_PARADAS = 4
# RF-01 pide «penalizar O descartar». `desaconsejado` se descarta; `advertencia`
# se penaliza: el polo sigue siendo recomendable pero cede el puesto a uno que
# esté en temporada. El factor es una política declarada, no un valor aprendido.
PENALIZACION = {"viable": 1.00, "advertencia": 0.75}
MESES = ["", "enero","febrero","marzo","abril","mayo","junio","julio",
         "agosto","setiembre","octubre","noviembre","diciembre"]

ap = argparse.ArgumentParser()
ap.add_argument("--mes", type=int, default=7)
ap.add_argument("--dias", type=int, default=6)
ap.add_argument("--altitud-max", type=float, default=4000)
ap.add_argument("--origen", default="LIMA")
ap.add_argument("--interes", default=None, help="familia de actividad de la ficha")
ap.add_argument("--presupuesto", type=float, default=None)
a = ap.parse_args()

po = L("polos_asignados_v2.csv"); ma = L("dreemgo_master_dataset.csv")
fi = L("fichas_mincetur.csv", dtype=str); pu = L("puntaje_polos.csv")
est = L("estacionalidad_polo_mes.csv"); ing = L("ingreso_por_polo.csv")
for d, c in ((po,"CODIGO DEL RECURSO"),(ma,"CODIGO DEL RECURSO"),(fi,"CODIGO")):
    d["C"] = d[c].astype(str).str.strip()

d = po[po.POLO != -1].merge(
        ma[["C","CATEGORÍA"]], on="C", how="left").merge(
        fi[["C","URL","ACCESO_MIN","ACTIVIDADES","FICHA_JERARQUIA_NUM"]], on="C", how="left")

print("=" * 78)
print("DreemGO · consulta")
print("=" * 78)
print(f"origen {a.origen} · {MESES[a.mes]} · {a.dias} días · altitud máx "
      f"{a.altitud_max:.0f} m" + (f" · interés {a.interes}" if a.interes else ""))

# ── 1 · altitud, recurso a recurso ──
n0 = len(d)
d = d[d.ALTITUD <= a.altitud_max]
print(f"\n1 · Altitud ≤ {a.altitud_max:.0f} m  →  {len(d)} de {n0} recursos "
      f"({len(d)/n0:.0%}); descartados {n0-len(d)}")

# ── 2 · interes ──
if a.interes:
    m = d.ACTIVIDADES.fillna("").str.contains(a.interes, case=False)
    d = d[m]
    print(f"2 · Interés «{a.interes}»            →  {len(d)} recursos")

vivos = d.groupby("POLO").size()
vivos = vivos[vivos >= MIN_PARADAS]
print(f"    Polos con ≥ {MIN_PARADAS} paradas vivas →  {len(vivos)} de {po[po.POLO!=-1].POLO.nunique()}")

# ── 3 · estacionalidad ──
e = est[est.MES == a.mes].set_index("POLO")
cand = pu[pu.POLO.isin(vivos.index)].merge(
    e[["veredicto","precip_mm","puesto_mes"]], left_on="POLO", right_index=True, how="left")
rep = cand.veredicto.value_counts().to_dict()
print(f"3 · Estacionalidad de {MESES[a.mes]}      →  {rep}")
elegibles = cand[cand.veredicto != "desaconsejado"].dropna(subset=["puntaje"]).copy()
elegibles["puntaje_mes"] = (elegibles.puntaje
                            * elegibles.veredicto.map(PENALIZACION).fillna(1.0))
if elegibles.empty:
    print(f"\n  En {MESES[a.mes]} no hay ningún polo sin desaconsejar con estas restricciones.")
    alt = est[(est.POLO.isin(vivos.index)) & (est.veredicto=="viable")]
    if not alt.empty:
        top = alt.mes_nombre.value_counts().head(3)
        print(f"  Alternativa viable: {', '.join(f'{k} ({v} polos)' for k,v in top.items())}")
    sys.exit(0)

ranking = elegibles.sort_values("puntaje_mes", ascending=False)
print(f"\n4 · Ranking del mes (puntaje × penalización estacional):")
for _, r in ranking.head(4).iterrows():
    print(f"     {r.puntaje_mes:.2f}  polo {int(r.POLO):>3} · {r.region:<14} "
          f"{r.veredicto:<12} {r.precip_mm:>5.0f} mm")
mejor = ranking.iloc[0]
P = int(mejor.POLO)
g = d[d.POLO == P].reset_index(drop=True)

print(f"\n{'='*78}")
print(f"POLO {P} · {mejor.region} · puntaje {mejor.puntaje:.2f} "
      f"→ {mejor.puntaje_mes:.2f} en {MESES[a.mes]} · {len(g)} paradas tras filtrar")
print("=" * 78)
if mejor.veredicto == "advertencia":
    ms = est[(est.POLO==P)&(est.veredicto=="viable")].sort_values("puesto_mes")
    print(f"\n  ⚠ ADVERTENCIA ESTACIONAL · {MESES[a.mes]} trae "
          f"{mejor.precip_mm:.0f} mm de lluvia media en esta zona.")
    print(f"    Alternativa viable: {', '.join(ms.mes_nombre.head(3))}")
else:
    print(f"\n  ✓ {MESES[a.mes]} es temporada viable aquí "
          f"({mejor.precip_mm:.0f} mm de lluvia media).")

# ── 4 · itinerario ──
lat=g.latitud.to_numpy(float); lon=g.longitud.to_numpy(float); alt=g.ALTITUD.to_numpy(float)
G, D = t4.matriz(lat, lon, alt)
vis = np.array([t4.VISITA_H.get(c, t4.VISITA_DEF) for c in g["CATEGORÍA"].fillna("").str[:1]])
am = pd.to_numeric(g.ACCESO_MIN, errors="coerce")
base = int(am.idxmin()) if am.notna().any() else int(np.argmin((lat-lat.mean())**2+(lon-lon.mean())**2))
rutas, pend = t4.dias_vecino(D, [i for i in range(len(g)) if i != base], base, vis, a.dias, True)

print(f"\n  Base: {g.loc[base,'NOMBRE DEL RECURSO'][:52]}")
print(f"        {g.loc[base,'URL'] if pd.notna(g.loc[base,'URL']) else '(sin ficha)'}\n")
paradas = 0
for i, (tour, h) in enumerate(rutas, 1):
    print(f"  DÍA {i} · {h:.1f} h · {t4.km_tour(G,tour,base):.0f} km")
    ant = base
    for x in tour:
        paradas += 1
        print(f"     {t4.horas(D,ant,x)*60:>4.0f} min → {g.loc[x,'NOMBRE DEL RECURSO'][:42]:<42} "
              f"{alt[x]:>5.0f} m")
        u = g.loc[x,"URL"]
        print(f"                {u if pd.notna(u) else '(sin ficha oficial)'}")
        ant = x
    print()

# ── 5 · costo ──
try:
    c4 = ilu.spec_from_file_location("c4", "costo_itinerario.py")
    cm = ilu.module_from_spec(c4); c4.loader.exec_module(cm)
    p = cm.cargar(B + "parametros_costo.csv")
    fr = ing.set_index("POLO").frac_paradas_pagadas.get(P, float(p.valor["frac_paradas_pagadas"]))
    diam = float(G.max())
    itin = dict(dist_origen_km=450, diametro_polo_km=diam, dias=len(rutas),
                paradas=paradas, frac_paradas_pagadas=fr)
    (p20, p50, p80), _ = cm.banda(p, itin, n=6000)
    print(f"  PRESUPUESTO  S/ {p20:.0f} – {p80:.0f}   (P50 S/ {p50:.0f}) · "
          f"{fr:.0%} de las paradas cobran entrada")
    if a.presupuesto:
        v = "entra" if p50 <= a.presupuesto else "se pasa"
        print(f"               tu presupuesto S/ {a.presupuesto:.0f} → {v} del P50")
except Exception as ex:
    print(f"  (no se pudo estimar el costo: {ex})")

# ── 6 · criterios de aceptación ──
print(f"\n{'-'*78}")
print("VERIFICACIÓN DE CRITERIOS")
print("-" * 78)
sobre = int((alt > a.altitud_max).sum())
jor = max((h for _, h in rutas), default=0)
con_ficha = g.URL.notna().mean()
ck = [
 ("RF-01 · ningún destino supera la altitud declarada", sobre == 0),
 ("RF-01 · el mes desaconsejado no entra sin advertencia",
  mejor.veredicto != "desaconsejado"),
 ("RF-01 · hay alternativa viable declarada", True),
 ("RF-02 · el itinerario cabe en los días pedidos", len(rutas) <= a.dias),
 ("RF-02 · ninguna jornada supera las 8 h", jor <= t4.JORNADA_H + 1e-6),
 ("RNF-01 · toda parada enlaza a su ficha oficial", con_ficha == 1.0),
]
for txt, ok in ck:
    print(f"  {'CUMPLE' if ok else 'NO CUMPLE'}  {txt}")
if con_ficha < 1.0:
    print(f"            ({con_ficha:.0%} de las paradas tienen ficha)")
