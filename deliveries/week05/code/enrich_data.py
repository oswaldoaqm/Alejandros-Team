import pandas as pd
import requests
import time
import numpy as np

# Configuración de rutas (leyendo de week04, guardando en week05)
INPUT_CSV = "../../week04/data/sample.csv"
OUTPUT_CSV = "../data/dataset_enriched.csv"

def get_elevation_batch(lats, lons):
    """Consulta la API de Open-Meteo para obtener elevación en batches."""
    url = "https://api.open-meteo.com/v1/elevation"
    params = {
        "latitude": ",".join(map(str, lats)),
        "longitude": ",".join(map(str, lons))
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("elevation", [np.nan] * len(lats))
    except Exception as e:
        print(f"Error en API: {e}")
        return [np.nan] * len(lats)

def generate_price_proxy(row):
    """Genera un índice de precio (1=Bajo, 2=Medio, 3=Alto)."""
    region = str(row['REGIÓN']).upper()
    cat = str(row['CATEGORÍA'])
    
    base = 2 if region in ['CUSCO', 'LIMA', 'AREQUIPA'] else 1
    if "MANIFESTACIONES CULTURALES" in cat or "REALIZACIONES TÉCNICAS" in cat:
        base += 1
        
    return min(base, 3)

def main():
    print("1. Cargando datos desde week04...")
    df = pd.read_csv(INPUT_CSV, sep=";", encoding="latin-1")
    
    print("2. Corrigiendo LAT/LONG...")
    df = df.rename(columns={"LATITUD": "longitud", "LONGITUD": "latitud"})
    
    mask_coords = df['latitud'].notna() & df['longitud'].notna()
    df_coords = df[mask_coords].copy()
    
    print(f"3. Obteniendo elevación para {len(df_coords)} recursos...")
    elevations = []
    batch_size = 100
    
    for i in range(0, len(df_coords), batch_size):
        batch = df_coords.iloc[i:i+batch_size]
        elev = get_elevation_batch(batch['latitud'].tolist(), batch['longitud'].tolist())
        elevations.extend(elev)
        if (i // batch_size) % 10 == 0:
            print(f"   Procesados {i}/{len(df_coords)}...")
        time.sleep(0.5) 
        
    df_coords['ALTITUD'] = elevations
    df['ALTITUD'] = np.nan
    df.loc[mask_coords, 'ALTITUD'] = df_coords['ALTITUD']
    
    print("4. Generando NIVEL_PRECIO_PROXY...")
    df['NIVEL_PRECIO_PROXY'] = df.apply(generate_price_proxy, axis=1)
    
    print(f"5. Guardando en {OUTPUT_CSV}...")
    df.to_csv(OUTPUT_CSV, index=False, sep=";", encoding="utf-8")
    print("¡Listo!")

if __name__ == "__main__":
    main()
