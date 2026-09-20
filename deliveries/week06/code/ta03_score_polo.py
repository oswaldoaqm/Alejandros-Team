"""
DreemGO · Puntaje del polo con término de novedad

Problema detectado en la auditoría: ordenar los polos por jerarquía oficial
sobre-representa el circuito saturado. Con 23 % de polos que contienen Lima o
Cusco en la base, el top 10 por jerarquía pura sale con 60 % de ellos.

Es decir: la capa de ordenamiento empujaba justo en contra de la tesis de
dispersión del producto. El término de novedad no es un adorno del documento,
es lo que hace que la promesa sea cierta.

    puntaje = (1 - λ) · jerarquía_normalizada  +  λ · novedad
    novedad = 0,5 · (1 - saturación)  +  0,5 · lejanía_normalizada

donde saturación es la fracción del polo que está en Lima o Cusco, y lejanía es
el índice de distancia al hub logístico regional.

Uso:  python ta03_score_polo.py <polos_asignados_v2.csv> [lambda]
"""
import sys
import numpy as np
import pandas as pd

RUTA = sys.argv[1] if len(sys.argv) > 1 else "polos_asignados_v2.csv"
LAMBDA = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30
SATURADAS = ["LIMA", "CUSCO"]

d = pd.read_csv(RUTA, sep=None, engine="python")
d = d[d.POLO != -1].copy()
d["REG"] = d["REGIÓN"].str.upper().str.strip()

pol = d.groupby("POLO").agg(
    recursos=("POLO", "size"),
    jerarquia=("JERARQUIA_OFICIAL", "mean"),
    lejania=("INDICE_COSTO_LOGISTICO", "mean") if "INDICE_COSTO_LOGISTICO" in d.columns
            else ("POLO", "size"),
    region=("REG", lambda s: s.mode().iat[0]),
    regiones=("REG", "nunique"),
    saturacion=("REG", lambda s: s.isin(SATURADAS).mean()),
).reset_index()

nrm = lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0
pol["novedad"] = 0.5 * (1 - pol.saturacion) + 0.5 * nrm(pol.lejania)
pol["limpio"] = pol.saturacion == 0

print("=" * 76)
print(f"PUNTAJE DEL POLO · λ = {LAMBDA}")
print("=" * 76)
print(f"Polos: {len(pol)} · recursos: {pol.recursos.sum()}")
print(f"Base  : {(~pol.limpio).mean()*100:.0f} % de los polos contienen Lima o Cusco\n")

print(f"{'λ':>6} {'Lima/Cusco top10':>18} {'jerarquía top10':>17} {'regiones top10':>16}")
for L in (0.0, 0.2, 0.3, 0.4, 0.5, 0.7):
    pol["s"] = (1 - L) * nrm(pol.jerarquia) + L * pol.novedad
    t = pol.nlargest(10, "s")
    print(f"{L:>6.1f} {(~t.limpio).sum()*10:>16} % {t.jerarquia.mean():>17.2f} "
          f"{t.region.nunique():>16}")

pol["puntaje"] = (1 - LAMBDA) * nrm(pol.jerarquia) + LAMBDA * pol.novedad
top = pol.nlargest(12, "puntaje")
print(f"\nTop 12 con λ = {LAMBDA}:")
print(top[["POLO", "recursos", "jerarquia", "novedad", "puntaje", "region", "limpio"]]
      .to_string(index=False, float_format=lambda x: f"{x:.2f}"))

base = pol.nlargest(10, "jerarquia")
t10 = pol.nlargest(10, "puntaje")
print(f"\nEfecto de λ = {LAMBDA}:")
print(f"  jerarquía media del top 10 : {base.jerarquia.mean():.2f} → {t10.jerarquia.mean():.2f} "
      f"({(t10.jerarquia.mean()/base.jerarquia.mean()-1)*100:+.1f} %)")
print(f"  polos con Lima o Cusco     : {(~base.limpio).sum()}/10 → {(~t10.limpio).sum()}/10")
print(f"  regiones representadas     : {base.region.nunique()} → {t10.region.nunique()}")

pol.sort_values("puntaje", ascending=False).to_csv("puntaje_polos.csv", sep=";", index=False)
print("\nEscrito: puntaje_polos.csv")
