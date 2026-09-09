import pandas as pd
import numpy as np

CSV_PATH = "../data/dataset_enriched.csv"

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

    # 3. Chequeo del Proxy de Precio
    print(f"\n3. NIVEL_PRECIO_PROXY:")
    print("   - Distribución de valores:")
    dist = df['NIVEL_PRECIO_PROXY'].value_counts().sort_index()
    for val, count in dist.items():
        print(f"       Nivel {val}: {count} recursos ({(count/len(df)):.2%})")
        
    # Verificación de lógica de negocio
    cusco_cultural = df[(df['REGIÓN'].str.upper() == 'CUSCO') & (df['CATEGORÍA'].str.contains('MANIFESTACIONES CULTURALES', na=False))]
    if not cusco_cultural.empty:
        precio_cusco_cult = cusco_cultural['NIVEL_PRECIO_PROXY'].mean()
        print(f"   - Prueba de estrés: Sitios culturales en Cusco tienen nivel promedio de {precio_cusco_cult:.1f} (Esperado: 3.0)")

if __name__ == "__main__":
    main()
