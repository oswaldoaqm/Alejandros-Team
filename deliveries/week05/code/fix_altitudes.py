import pandas as pd
import requests
import time
import numpy as np

CSV_PATH = "../data/dataset_enriched.csv"

def get_elevation_batch(lats, lons):
    url = "https://api.open-meteo.com/v1/elevation"
    params = {"latitude": ",".join(map(str, lats)), "longitude": ",".join(map(str, lons))}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("elevation", [np.nan] * len(lats))
    except Exception as e:
        return [np.nan] * len(lats)

def main():
    print("1. Leyendo dataset incompleto...")
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8")
    
    # Filtrar los que tienen coordenadas válidas pero les falta ALTITUD
    mask_to_fix = df['latitud'].notna() & df['ALTITUD'].isna()
    df_fix = df[mask_to_fix].copy()
    
    print(f"2. Faltan {len(df_fix)} altitudes. Iniciando rescate (Batches de 20)...")
    
    batch_size = 20
    elevations = []
    
    for i in range(0, len(df_fix), batch_size):
        batch = df_fix.iloc[i:i+batch_size]
        elev = get_elevation_batch(batch['latitud'].tolist(), batch['longitud'].tolist())
        elevations.extend(elev)
        
        if (i // batch_size) % 5 == 0:
            print(f"   Rescatados {min(i+batch_size, len(df_fix))}/{len(df_fix)}...")
        time.sleep(1.5)  # Pausa larga obligatoria para que no nos bloqueen
        
    df_fix['ALTITUD'] = elevations
    df.loc[mask_to_fix, 'ALTITUD'] = df_fix['ALTITUD']
    
    nulos_restantes = df[df['latitud'].notna()]['ALTITUD'].isna().sum()
    print(f"\n3. Verificación final: Quedan {nulos_restantes} nulos de altitud.")
    
    if nulos_restantes == 0:
        df.to_csv(CSV_PATH, index=False, sep=";", encoding="utf-8")
        print("¡ÉXITO TOTAL! Dataset guardado y listo para Machine Learning.")
    else:
        df.to_csv(CSV_PATH, index=False, sep=";", encoding="utf-8")
        print("Se rescató una parte. Vuelve a correr este mismo script hasta que los nulos sean 0.")

if __name__ == "__main__":
    main()
