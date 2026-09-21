"""
DreemGO · TA-02 — viabilidad estacional del polo, mes a mes

RF-01 pide cruzar la zona climática del destino con el mes de viaje para
«penalizar o descartar» recursos cuya temporada no acompañe, ANTES de construir
el itinerario. Esto produce esa capa.

RNF-01 exige que las variables estáticas del inventario queden desacopladas de
las reglas dinámicas de tiempo: cambiar de mes no debe alterar el dataset base.
Por eso este módulo NO toca polos_asignados_v2.csv ni el maestro. Escribe una
tabla aparte, polo × mes, que se consulta en tiempo de query.

EL UMBRAL, Y POR QUÉ NO ES UNO SOLO
-----------------------------------
Un corte absoluto de milímetros no sirve en el Perú. El mes MÁS SECO de Loreto
son 127,8 mm — más que el mes más húmedo de media docena de regiones. Con un
corte absoluto, la selva quedaría desaconsejada todo el año y el producto nunca
la recomendaría. Un corte puramente relativo falla al revés: los 316 mm de
Loreto en su peor mes pasarían por aceptables porque son «solo» 2,5 veces su
mínimo.

Se usan los dos ejes:

  absoluto  · precipitación ≥ 150 mm/mes. Anclado en el percentil 75 de las 288
              combinaciones región × mes del país (P75 = 142,5 mm): el cuartil
              más lluvioso del Perú.
  relativo  · el mes está entre los 3 más lluviosos de su propia región —la
              definición operativa de «su temporada de lluvias»— Y además supera
              un piso de 50 mm. El piso hace falta: sin él, febrero en La
              Libertad salía con advertencia teniendo 27 mm de lluvia, porque es
              de sus meses más húmedos aunque sea un desierto costero. 50 mm es
              la mediana nacional de región × mes: por debajo de eso la lluvia no
              es un problema de viaje en ninguna parte del país.

  desaconsejado · disparan los dos
  advertencia   · dispara uno
  viable        · no dispara ninguno

Esto es una regla, no un modelo aprendido, y se declara como tal. Lo que la
respalda es que la precipitación viene de diez años de Open-Meteo y no de una
suposición sobre cómo es el clima peruano.

LIMITACIÓN CONOCIDA
-------------------
El clima está por REGIÓN (24 puntos). Un polo que va de la costa a la sierra
dentro de la misma región recibe el promedio de las dos. `fetch_climate_v2.py`
baja 88 puntos región × zona climática y cubriría el 99,3 % de los recursos;
está escrito y sin ejecutar. Hasta entonces, esta capa es más gruesa de lo que
el diseño pide.

Uso:  python ta02_estacionalidad.py
"""
import unicodedata
import numpy as np
import pandas as pd


def nm(s):
    """Normaliza el nombre de region: el clima trae HUANUCO y el inventario HUÁNUCO."""
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()

B = "../data/processed/"
UMBRAL_MM = 150.0          # P75 nacional de region x mes
PISO_MM = 50.0             # mediana nacional · por debajo, la lluvia no estorba
N_LLUVIOSOS = 3            # meses mas lluviosos de cada region
MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "setiembre", "octubre", "noviembre", "diciembre"]

L = lambda p, **k: pd.read_csv(B + p, sep=";", encoding="utf-8-sig", **k)

cl = L("historial_clima_regiones.csv")
po = L("polos_asignados_v2.csv")
po = po[po.POLO != -1].copy()
po["REG"] = po["REGIÓN"].map(nm)

# ── clima normal de cada region: media de 10 años por mes ──
norm = (cl.assign(REG=cl.REGION.map(nm))
          .groupby(["REG", "MES"])
          .agg(precip_mm=("PRECIPITACION_TOTAL_MM", "mean"),
               temp_c=("TEMPERATURA_MEDIA_C", "mean")).reset_index())

# rango de la region: que puesto ocupa el mes en su propio ciclo
norm["rank_lluvia"] = norm.groupby("REG").precip_mm.rank(ascending=False, method="min")
norm["es_temporada_lluvias"] = (norm.rank_lluvia <= N_LLUVIOSOS) & (norm.precip_mm >= PISO_MM)

# ── peso de cada region dentro del polo, por numero de recursos ──
peso = (po.groupby(["POLO", "REG"]).size().rename("n").reset_index())
peso["w"] = peso.n / peso.groupby("POLO").n.transform("sum")

pm = peso.merge(norm, on="REG", how="left")
faltan = pm[pm.precip_mm.isna()].REG.unique()
if len(faltan):
    print(f"AVISO · sin clima para: {sorted(faltan)}")
    pm = pm.dropna(subset=["precip_mm"])

est = (pm.assign(p=pm.precip_mm * pm.w, t=pm.temp_c * pm.w,
                 l=pm.es_temporada_lluvias * pm.w)
         .groupby(["POLO", "MES"])
         .agg(precip_mm=("p", "sum"), temp_c=("t", "sum"),
              frac_lluvias=("l", "sum")).reset_index())

est["absoluto"] = est.precip_mm >= UMBRAL_MM
est["relativo"] = est.frac_lluvias >= 0.5          # la mayoria del polo en su temporada
est["veredicto"] = np.select(
    [est.absoluto & est.relativo, est.absoluto | est.relativo],
    ["desaconsejado", "advertencia"], default="viable")
est["mes_nombre"] = est.MES.map(lambda m: MESES[int(m)])

# ranking de meses de cada polo: de aqui sale la "alternativa viable" de RF-01
est["puesto_mes"] = est.groupby("POLO").precip_mm.rank(method="min")

est = est[["POLO", "MES", "mes_nombre", "precip_mm", "temp_c", "frac_lluvias",
           "veredicto", "puesto_mes"]].sort_values(["POLO", "MES"])
est.round(2).to_csv(B + "estacionalidad_polo_mes.csv", sep=";", index=False)

print("=" * 78)
print("TA-02 · viabilidad estacional polo × mes")
print("=" * 78)
print(f"Filas: {len(est)}  ({est.POLO.nunique()} polos × 12 meses)")
print(f"Umbral absoluto: {UMBRAL_MM:.0f} mm/mes · relativo: top-{N_LLUVIOSOS} "
      f"de la región con piso de {PISO_MM:.0f} mm\n")
print("Reparto de veredictos:")
for k, v in est.veredicto.value_counts().items():
    print(f"  {k:<15} {v:>5}  ({v/len(est)*100:>4.1f} %)")

print("\nPolos viables por mes:")
t = est[est.veredicto == "viable"].groupby("mes_nombre").size()
for m in range(1, 13):
    n = int(t.get(MESES[m], 0))
    print(f"  {MESES[m]:<11} {n:>4} de {est.POLO.nunique()}  {'█'*int(n/6)}")

print(f"\nTodo polo tiene al menos un mes viable: "
      f"{est[est.veredicto=='viable'].POLO.nunique() == est.POLO.nunique()}")
sin = set(est.POLO) - set(est[est.veredicto == "viable"].POLO)
if sin:
    print(f"  excepto {len(sin)} polos: {sorted(sin)[:8]}")
print(f"\nEscrito: {B}estacionalidad_polo_mes.csv")
print("(el dataset base no se modificó — RNF-01)")
