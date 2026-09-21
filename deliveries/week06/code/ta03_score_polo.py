"""
DreemGO · Puntaje del polo con término de novedad

Problema detectado en la auditoría: ordenar los polos por jerarquía oficial
sobre-representa el circuito saturado. El término de novedad no es un adorno
del documento, es lo que hace que la promesa de dispersión sea cierta.

    puntaje = (1 - λ) · jerarquía_normalizada  +  λ · novedad
    novedad = 0,5 · (1 - saturación)  +  0,5 · lejanía_normalizada

QUÉ CAMBIÓ EN ESTA VERSIÓN
--------------------------
1. La jerarquía sale de la ficha oficial de MINCETUR (FICHA_JERARQUIA_NUM),
   no de JERARQUIA_OFICIAL del master. Verificamos que el master coincide al
   100 % con la ficha en los 3 660 recursos donde la ficha da un número, y que
   inventa un valor en los otros 2 469 — donde la ficha dice "No aplica" o
   "POR JERARQUIZAR". Ese 40 % inventado inflaba por siete la cantidad de
   recursos de jerarquía alta del país.

2. `lejania` se lee del master. Antes caía a un fallback que usaba el TAMAÑO
   del polo, así que el término de novedad medía cuántos recursos tenía el
   polo en vez de qué tan lejos estaba del hub logístico.

QUÉ HACEMOS CON LOS RECURSOS SIN JERARQUÍA
------------------------------------------
Dentro de los polos hay 1 240 recursos sin jerarquía real: 882 "POR
JERARQUIZAR", 328 "No aplica" y 30 cuya ficha falló. No se imputa ningún
valor. Imputar la mediana repetiría exactamente el error que acabamos de
encontrar, y poner cero castigaría a los recursos que el Estado todavía no
ha evaluado — que son justo los que este producto existe para sacar a la luz.

La jerarquía del polo es el promedio SOBRE LOS QUE SÍ LA TIENEN, y se publica
junto a `cobertura_jerarquia`: qué fracción del polo sostiene ese promedio. Un
polo por debajo de COBERTURA_MIN no entra al ranking, porque su jerarquía
sería el promedio de demasiado poco.

Uso:  python ta03_score_polo.py <polos_asignados_v2.csv> [lambda] [cobertura_min]
"""
import sys
import numpy as np
import pandas as pd

RUTA = sys.argv[1] if len(sys.argv) > 1 else "../data/processed/polos_asignados_v2.csv"
LAMBDA = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30
COBERTURA_MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.30
SATURADAS = ["LIMA", "CUSCO"]
FICHAS = "../data/processed/fichas_mincetur.csv"
MASTER = "../data/processed/dreemgo_master_dataset.csv"


def leer(ruta, **kw):
    return pd.read_csv(ruta, sep=";", encoding="utf-8-sig", **kw)


d = leer(RUTA)
d = d[d.POLO != -1].copy()
d["REG"] = d["REGIÓN"].str.upper().str.strip()
d["COD"] = d["CODIGO DEL RECURSO"].astype(str).str.strip()

# ── jerarquía real desde la ficha oficial ──
fi = leer(FICHAS, dtype=str)
fi["COD"] = fi.CODIGO.astype(str).str.strip()
fi["jer_real"] = pd.to_numeric(fi.FICHA_JERARQUIA_NUM, errors="coerce")
d = d.merge(fi[["COD", "jer_real", "FICHA_JERARQUIA_TXT"]], on="COD", how="left")

# ── lejanía real desde el master (antes se caía a un fallback por tamaño) ──
ma = leer(MASTER)
ma["COD"] = ma["CODIGO DEL RECURSO"].astype(str).str.strip()
d = d.merge(ma[["COD", "INDICE_COSTO_LOGISTICO"]], on="COD", how="left")

n_sin = d.jer_real.isna().sum()
print("=" * 76)
print(f"PUNTAJE DEL POLO · λ = {LAMBDA} · cobertura mínima = {COBERTURA_MIN:.0%}")
print("=" * 76)
print(f"Recursos en un polo      : {len(d)}")
print(f"  con jerarquía oficial  : {d.jer_real.notna().sum()}")
print(f"  sin jerarquía oficial  : {n_sin} ({n_sin/len(d)*100:.1f} %) · no se imputa")
print(d.loc[d.jer_real.isna(), "FICHA_JERARQUIA_TXT"].fillna("(ficha con error)")
      .str.upper().value_counts().to_string())

pol = d.groupby("POLO").agg(
    recursos=("POLO", "size"),
    jerarquia=("jer_real", "mean"),
    jer_conocida=("jer_real", "count"),
    lejania=("INDICE_COSTO_LOGISTICO", "mean"),
    region=("REG", lambda s: s.mode().iat[0]),
    regiones=("REG", "nunique"),
    saturacion=("REG", lambda s: s.isin(SATURADAS).mean()),
).reset_index()
pol["cobertura_jerarquia"] = pol.jer_conocida / pol.recursos
pol["limpio"] = pol.saturacion == 0

sin_dato = pol.jerarquia.isna()
bajo = (~sin_dato) & (pol.cobertura_jerarquia < COBERTURA_MIN)
print(f"\nPolos totales            : {len(pol)}")
print(f"  sin ningún recurso jerarquizado : {sin_dato.sum()} · fuera del ranking")
print(f"  con cobertura < {COBERTURA_MIN:.0%}            : {bajo.sum()} · fuera del ranking")
print(f"  rankeables                      : {(~sin_dato & ~bajo).sum()}")
print(f"  cobertura mediana               : {pol.cobertura_jerarquia.median():.0%}")

rk = pol[~sin_dato & ~bajo].copy()
nrm = lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0
rk["novedad"] = 0.5 * (1 - rk.saturacion) + 0.5 * nrm(rk.lejania)

print(f"\nBase: {(~rk.limpio).mean()*100:.0f} % de los polos rankeables contienen Lima o Cusco\n")
print(f"{'λ':>6} {'Lima/Cusco top10':>18} {'jerarquía top10':>17} {'regiones top10':>16}")
for L in (0.0, 0.2, 0.3, 0.4, 0.5, 0.7):
    rk["s"] = (1 - L) * nrm(rk.jerarquia) + L * rk.novedad
    t = rk.nlargest(10, "s")
    print(f"{L:>6.1f} {(~t.limpio).sum()*10:>16} % {t.jerarquia.mean():>17.2f} "
          f"{t.region.nunique():>16}")

rk["puntaje"] = (1 - LAMBDA) * nrm(rk.jerarquia) + LAMBDA * rk.novedad
top = rk.nlargest(12, "puntaje")
print(f"\nTop 12 con λ = {LAMBDA}:")
print(top[["POLO", "recursos", "jerarquia", "cobertura_jerarquia", "novedad",
           "puntaje", "region", "limpio"]]
      .to_string(index=False, float_format=lambda x: f"{x:.2f}"))

base = rk.nlargest(10, "jerarquia")
t10 = rk.nlargest(10, "puntaje")
print(f"\nEfecto de λ = {LAMBDA}:")
print(f"  jerarquía media del top 10 : {base.jerarquia.mean():.2f} → {t10.jerarquia.mean():.2f} "
      f"({(t10.jerarquia.mean()/base.jerarquia.mean()-1)*100:+.1f} %)")
print(f"  polos con Lima o Cusco     : {(~base.limpio).sum()}/10 → {(~t10.limpio).sum()}/10")
print(f"  regiones representadas     : {base.region.nunique()} → {t10.region.nunique()}")

alto = d[d.jer_real >= 3]
sat_pol = set(pol.loc[~pol.limpio, "POLO"])
fuera = (~alto.POLO.isin(sat_pol)).sum()
print(f"\nDispersión, con la jerarquía real:")
print(f"  recursos de jerarquía 3 o 4 en polos : {len(alto)}")
print(f"  fuera del circuito saturado          : {fuera}")
print(f"  dentro                               : {len(alto)-fuera}")

pol.merge(rk[["POLO", "novedad", "puntaje"]], on="POLO", how="left") \
   .sort_values("puntaje", ascending=False) \
   .to_csv("../data/processed/puntaje_polos.csv", sep=";", index=False)
print("\nEscrito: ../data/processed/puntaje_polos.csv")
