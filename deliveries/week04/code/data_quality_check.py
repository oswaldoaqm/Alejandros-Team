"""
DreemGO — Semana 4
Esta es la verificación reproducible de calidad del Inventario Nacional de Recursos Turísticos (MINCETUR).

Regenera igualito todas las cifras reportadas en data/data_quality.md.

Uso:
    python code/data_quality_check.py [ruta_csv]

Requiere: pandas
"""

import sys
from pathlib import Path

import pandas as pd

CSV = Path(sys.argv[1] if len(sys.argv) > 1 else "../data/sample.csv")

# Bounding box del territorio peruano (WGS 84)
PERU_LAT = (-18.35, -0.04)
PERU_LON = (-81.33, -68.65)


def cargar(ruta: Path) -> pd.DataFrame:
    """El archivo obtenido del MINCETUR usa ';' y codificación latin-1, no los valores por defecto."""
    return pd.read_csv(ruta, sep=";", encoding="latin-1")


def titulo(txt: str) -> None:
    print(f"\n{'=' * 72}\n{txt}\n{'=' * 72}")


def main() -> None:
    if not CSV.exists():
        sys.exit(f"No se encontró {CSV}. Pasa la ruta como argumento o ejecuta desde la raíz del repo.")

    df = cargar(CSV)

    titulo("1. ESTRUCTURA")
    print(f"Registros: {len(df):,}   Columnas: {df.shape[1]}")
    print(f"Filas duplicadas completas: {df.duplicated().sum()}")
    print(f"CODIGO DEL RECURSO duplicado: {df['CODIGO DEL RECURSO'].duplicated().sum()}")
    print(f"Fecha(s) de corte: {sorted(df['FECHA_DE_CORTE'].unique())}")

    titulo("2. HALLAZGO CRÍTICO — ¿ESTÁN INTERCAMBIADAS LATITUD Y LONGITUD?")
    g = df.dropna(subset=["LATITUD", "LONGITUD"])
    tal_cual = (g["LATITUD"].between(*PERU_LAT) & g["LONGITUD"].between(*PERU_LON)).mean()
    swap = (g["LONGITUD"].between(*PERU_LAT) & g["LATITUD"].between(*PERU_LON)).mean()
    print(f"Registros con coordenadas: {len(g):,}")
    print(f"  Dentro del Perú con las etiquetas originales : {tal_cual:7.2%}")
    print(f"  Dentro del Perú si se intercambian columnas  : {swap:7.2%}")
    veredicto = "SÍ — hay que intercambiarlas" if swap > tal_cual else "no"
    print(f"  Veredicto: {veredicto}")

    mp = df[df["NOMBRE DEL RECURSO"].str.contains("Machu Picchu", case=False, na=False)]
    if not mp.empty:
        fila = mp.iloc[0]
        print(f"\n  Control: {fila['NOMBRE DEL RECURSO'].strip()}")
        print(f"    columna LATITUD  = {fila['LATITUD']:.4f}   (Machu Picchu real: lon -72.54)")
        print(f"    columna LONGITUD = {fila['LONGITUD']:.4f}   (Machu Picchu real: lat -13.16)")

    titulo("3. VALORES FALTANTES")
    nulos = pd.DataFrame({"n": df.isna().sum(), "pct": (df.isna().mean() * 100).round(2)})
    print(nulos[nulos["n"] > 0].to_string())

    print("\n¿Los faltantes de coordenadas son aleatorios? Distribución por categoría:")
    por_cat = (
        df.assign(sin_coord=df["LATITUD"].isna())
        .groupby("CATEGORÍA")["sin_coord"]
        .agg(total="size", sin_coord="sum", pct="mean")
    )
    por_cat["pct"] = (por_cat["pct"] * 100).round(1)
    print(por_cat.sort_values("pct", ascending=False).to_string())
    print("\n-> No son aleatorios: se concentran en Folclore y Acontecimientos Programados,")
    print("   que son prácticas y eventos sin punto geográfico. No se imputan.")

    print("\nCobertura por región (peores y mejores):")
    por_reg = (
        df.assign(sin_coord=df["LATITUD"].isna())
        .groupby("REGIÓN")["sin_coord"]
        .agg(total="size", sin_coord="sum", pct="mean")
    )
    por_reg["pct"] = (por_reg["pct"] * 100).round(1)
    por_reg = por_reg.sort_values("pct", ascending=False)
    print(por_reg.head(4).to_string())
    print("...")
    print(por_reg.tail(4).to_string())

    titulo("4. INCONSISTENCIAS DE FORMATO")
    for col in ["NOMBRE DEL RECURSO", "SUB TIPO CATEGORÍA"]:
        s = df[col].dropna().astype(str)
        n = int((s != s.str.strip()).sum())
        print(f"Espacios sobrantes en {col}: {n}")

    for col in ["REGIÓN", "PROVINCIA", "DISTRITO"]:
        s = df[col].dropna()
        fmt = "MAYÚSCULAS" if (s == s.str.upper()).all() else "Title Case"
        print(f"Formato de {col:10s}: {fmt:12s} ({s.nunique()} valores únicos)")

    tipos = df["TIPO DE CATEGORÍA"].dropna().unique()
    con_prefijo = [t for t in tipos if len(t) > 2 and t[1] == "." and t[0].isalpha()]
    print(f"\nTIPO DE CATEGORÍA con prefijo de letra: {len(con_prefijo)} de {len(tipos)}")
    print(f"  ejemplos: {con_prefijo[:4]}")

    titulo("5. VALORES SOSPECHOSOS")
    dup = df[df.duplicated(subset=["NOMBRE DEL RECURSO", "DISTRITO"], keep=False)]
    print(f"Pares con mismo nombre y distrito pero distinto código: {len(dup) // 2}")
    if not dup.empty:
        print(dup[["REGIÓN", "DISTRITO", "CODIGO DEL RECURSO", "NOMBRE DEL RECURSO"]]
              .sort_values("NOMBRE DEL RECURSO").to_string(index=False))

    cod_url = df["URL"].str.extract(r"cod_Ficha=(\d+)")[0].astype("int64")
    coincide = bool((cod_url == df["CODIGO DEL RECURSO"]).all())
    print(f"\nTrazabilidad: cod_Ficha de la URL coincide con CODIGO DEL RECURSO: {coincide}")
    print(f"URLs únicas: {df['URL'].nunique():,} de {len(df):,}")

    titulo("6. RESUMEN")
    print(f"Registros                       : {len(df):,}")
    print(f"Regiones / provincias / distritos: {df['REGIÓN'].nunique()} / "
          f"{df['PROVINCIA'].nunique()} / {df['DISTRITO'].nunique()}")
    print(f"Categorías / tipos / subtipos    : {df['CATEGORÍA'].nunique()} / "
          f"{df['TIPO DE CATEGORÍA'].nunique()} / {df['SUB TIPO CATEGORÍA'].nunique()}")
    print(f"Geolocalizables tras corregir    : {len(g):,} ({len(g) / len(df):.1%})")


if __name__ == "__main__":
    main()
