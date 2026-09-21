"""
DreemGO - verificacion de fichas_mincetur.csv antes de integrarlo

Tres preguntas, en orden de importancia:

  1. La jerarquia del master coincide con la de la ficha oficial?
     Es la pregunta que arrastramos desde la auditoria. JERARQUIA_OFICIAL
     del master salio de random.choices() en build_master_dataset.py, y
     6.4 de ModelSelection descansa sobre ella.

  2. INGRESO_TIPO, EPOCA_PROPICIA y ACCESO_KM salieron los tres en 74 %.
     Faltan en las MISMAS fichas? Si si, es estructural -- hay un tipo de
     recurso cuya ficha no trae esas tablas -- y no es un fallo del parser.
     Si no, es un fallo del parser y hay que arreglarlo antes de integrar.

  3. Que son los 31 errores?

Uso:  python verificar_fichas.py
      (desde deliveries/week06/code)
"""
import re
import pandas as pd

FICHAS = "../data/processed/fichas_mincetur.csv"
MASTER = "../data/processed/dreemgo_master_dataset.csv"
CAMPOS = ["INGRESO_TIPO", "EPOCA_PROPICIA", "ACCESO_KM"]


def leer(ruta):
    return pd.read_csv(ruta, sep=";", dtype=str, encoding="utf-8-sig")


def col(df, patron):
    for c in df.columns:
        if re.search(patron, c, re.I):
            return c
    return None


def linea(t=""):
    print(("-" * 78) if not t else "\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


fi = leer(FICHAS)
ma = leer(MASTER)
print("fichas: %d filas . master: %d filas" % (len(fi), len(ma)))

c_cod_ma = col(ma, r"c[oó]digo")
c_cat = col(ma, r"categor")
c_jer_ma = col(ma, r"jerarquia_oficial")
fi["CODIGO"] = fi["CODIGO"].astype(str).str.strip()
ma[c_cod_ma] = ma[c_cod_ma].astype(str).str.strip()

ok = fi[fi["HTTP"] == "200"].copy()
print("con HTTP 200: %d" % len(ok))

linea("1 . JERARQUIA - ficha oficial contra el master")

txt = ok["FICHA_JERARQUIA_TXT"].fillna("").str.strip()
print("\nLo que dicen las fichas, tal cual:")
for v, n in txt.str.upper().value_counts().head(12).items():
    print("  %6d  %s" % (n, v[:64]))

util = ok["FICHA_JERARQUIA_NUM"].notna() & (ok["FICHA_JERARQUIA_NUM"] != "")
print("\nFichas con jerarquia numerica real (1-4): %d de %d (%.1f %%)"
      % (util.sum(), len(ok), util.mean() * 100))
print("Fichas sin jerarquia asignable          : %d (%.1f %%)"
      % ((~util).sum(), (~util).mean() * 100))

if c_jer_ma:
    j = ok.merge(ma[[c_cod_ma, c_jer_ma]], left_on="CODIGO", right_on=c_cod_ma, how="inner")
    j = j[j["FICHA_JERARQUIA_NUM"].notna() & (j["FICHA_JERARQUIA_NUM"] != "")]
    j["real"] = pd.to_numeric(j["FICHA_JERARQUIA_NUM"], errors="coerce")
    j["master"] = pd.to_numeric(j[c_jer_ma], errors="coerce")
    j = j.dropna(subset=["real", "master"])
    if len(j):
        print("\nDonde AMBAS existen (%d recursos):" % len(j))
        print("  coinciden exactamente : %.1f %%" % ((j.real == j.master).mean() * 100))
        print("  (el azar puro daria ~25 %% con cuatro niveles)")
        print("\n  matriz real (filas) x master (columnas):")
        print(pd.crosstab(j.real.astype(int), j.master.astype(int)).to_string())
        print("\n  jerarquia media . ficha %.2f . master %.2f" % (j.real.mean(), j.master.mean()))
    else:
        print("\nNo hay recursos con jerarquia en ambos lados.")
else:
    print("\nEl master no tiene columna JERARQUIA_OFICIAL en esta copia.")

linea("2 . POR QUE TRES CAMPOS DISTINTOS DAN EL MISMO 74 %?")

falta = {c: ok[c].isna() | (ok[c].astype(str).str.strip() == "") for c in CAMPOS}
for c in CAMPOS:
    print("  vacio en %-16s: %d" % (c, falta[c].sum()))

todos = falta[CAMPOS[0]] & falta[CAMPOS[1]] & falta[CAMPOS[2]]
alguno = falta[CAMPOS[0]] | falta[CAMPOS[1]] | falta[CAMPOS[2]]
print("\n  vacio en LOS TRES a la vez : %d" % todos.sum())
print("  vacio en al menos uno      : %d" % alguno.sum())
print("  solapamiento               : %.1f %%" % (todos.sum() / max(alguno.sum(), 1) * 100))
print("\n  -> cerca del 100 %% significa que es estructural: hay un tipo de ficha")
print("     que no trae esas tablas. Por debajo de ~90 %% el parser esta fallando.")

if "TABLAS_RECONOCIDAS" in ok.columns:
    t = pd.to_numeric(ok["TABLAS_RECONOCIDAS"], errors="coerce")
    print("\n  tablas reconocidas . fichas completas  : %.2f" % t[~alguno].mean())
    print("  tablas reconocidas . fichas incompletas: %.2f" % t[alguno].mean())
    print("  (si la incompleta reconoce MENOS tablas, la pagina trae menos tablas;")
    print("   si reconoce las mismas, las trae y no las estamos leyendo)")

if c_cat:
    m = ok.merge(ma[[c_cod_ma, c_cat]], left_on="CODIGO", right_on=c_cod_ma, how="left")
    m["incompleta"] = alguno.to_numpy()
    tab = m.groupby(c_cat).agg(fichas=("CODIGO", "size"), incompletas=("incompleta", "sum"))
    tab["pct"] = (tab.incompletas / tab.fichas * 100).round(1)
    print("\n  Por categoria del recurso:")
    print(tab.sort_values("pct", ascending=False).to_string())

print("\n  Cinco codigos con los tres campos vacios, para abrirlos a mano:")
for c in ok.loc[todos, "CODIGO"].head(5):
    print("    %s  https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod=%s" % (c, c))

linea("3 . LOS 31 ERRORES")
err = fi[fi["HTTP"] != "200"]
print("\n  %d fichas sin HTTP 200 (%.2f %% del total)" % (len(err), len(err) / len(fi) * 100))
print(err["HTTP"].value_counts().to_string())
print("\n  codigos: " + ", ".join(err["CODIGO"].head(40)))

linea("4 . COBERTURA DEL JOIN CONTRA EL MASTER")
en_master = set(ma[c_cod_ma])
en_ficha = set(ok["CODIGO"])
print("\n  recursos del master con ficha usable : %d de %d (%.1f %%)"
      % (len(en_master & en_ficha), len(en_master),
         len(en_master & en_ficha) / len(en_master) * 100))
print("  fichas sin contraparte en el master  : %d" % len(en_ficha - en_master))
print("\n(nada de esto escribe ningun archivo)")
