import pandas as pd
import numpy as np

from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset_enriched.csv"

def main():
    try:
        df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8")
    except FileNotFoundError:
        print("ERROR_FILE_NOT_FOUND")
        return
        
    print(f"--- REVISIÓN MINUCIOSA DEL DATASET ENRIQUECIDO ---")
    print(f"Registros totales: {len(df)}")
    print(f"Columnas totales: {len(df.columns)}\n")
    
    # 1. Chequeo de Latitud/Longitud (¿Se hizo el swap?)
    peru_lat = (-18.4, 0.0)
    peru_lon = (-81.4, -68.6)
    
    mask_valid = df['latitud'].notna() & df['longitud'].notna()
    df_coords = df[mask_valid]
    
    lat_ok = df_coords['latitud'].between(*peru_lat).mean()
    lon_ok = df_coords['longitud'].between(*peru_lon).mean()
    print(f"1. LATITUD/LONGITUD:")
    print(f"   - % Latitudes dentro de Perú: {lat_ok:.2%}")
    print(f"   - % Longitudes dentro de Perú: {lon_ok:.2%}")
    if lat_ok < 1 or lon_ok < 1:
        print("   [ALERTA] Hay coordenadas fuera del territorio peruano.")
        
    # 2. Chequeo de Altitud
    print(f"\n2. ALTITUD:")
    alt_nulos = df_coords['ALTITUD'].isna().sum()
    print(f"   - Nulos en recursos geolocalizados: {alt_nulos} (Esperado: 0)")
    
    alt_min = df_coords['ALTITUD'].min()
    alt_max = df_coords['ALTITUD'].max()
    print(f"   - Rango de Altitud: {alt_min:.1f} msnm a {alt_max:.1f} msnm")
    
    # Chequeo lógico de altitud (Cusco debe ser alto, Lima debe ser bajo)
    cusco_alt = df_coords[df_coords['REGIÓN'].str.upper() == 'CUSCO']['ALTITUD'].mean()
    lima_alt = df_coords[df_coords['REGIÓN'].str.upper() == 'LIMA']['ALTITUD'].mean()
    print(f"   - Altitud promedio Cusco: {cusco_alt:.1f} msnm (Lógico: > 2500)")
    print(f"   - Altitud promedio Lima: {lima_alt:.1f} msnm (Lógico: < 1500)")
    
    if alt_max > 6800:
        print(f"   [ALERTA] Altitud máxima ({alt_max}) excede la montaña más alta del Perú (Huascarán, ~6768m). Posible error de API.")
    if alt_min < -100:
        print(f"   [ALERTA] Altitud mínima ({alt_min}) es absurdamente negativa.")

    # 3. Índice de lejanía. NIVEL_PRECIO_PROXY se descartó esta misma semana:
    #    fix_pricing.py lo elimina y deja INDICE_COSTO_LOGISTICO, que solo mide distancia.
    print(f"\n3. INDICE_COSTO_LOGISTICO (índice de lejanía):")
    g = df.dropna(subset=['DISTANCIA_CAPITAL_KM'])
    esperado = np.select([g['DISTANCIA_CAPITAL_KM'] < 20, g['DISTANCIA_CAPITAL_KM'] < 80], [1, 2], 3)
    coincide = (g['INDICE_COSTO_LOGISTICO'] == esperado).mean()
    print(f"   - Sigue la regla 1 = <20 km · 2 = <80 km · 3 = 80 km o más: {coincide:.2%} (Esperado: 100%)")
    for val, count in g['INDICE_COSTO_LOGISTICO'].value_counts().sort_index().items():
        print(f"       Nivel {int(val)}: {count} recursos ({count / len(g):.2%})")
    if 'NIVEL_PRECIO_PROXY' in df.columns:
        print("   [ALERTA] Sigue la columna NIVEL_PRECIO_PROXY: falta correr fix_pricing.py.")

    # 4. Zona climática
    zonas = df['ZONA_CLIMATICA'].value_counts()
    print(f"\n4. ZONA_CLIMATICA:")
    print(f"   - {len(zonas)} pisos ecológicos · nulos: {df['ZONA_CLIMATICA'].isna().sum()} "
          f"(Esperado: los mismos 1 245 recursos sin coordenadas)")

if __name__ == "__main__":
    main()
