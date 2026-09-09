import pandas as pd
import numpy as np
import math

CSV_PATH = "../data/dataset_enriched.csv"

# Coordenadas aproximadas de las 25 capitales regionales del Perú
CAPITALES = {
    'AMAZONAS': (-6.2294, -77.8728), 'ANCASH': (-9.5278, -77.5278), 'APURIMAC': (-13.6339, -72.8814),
    'AREQUIPA': (-16.3989, -71.5350), 'AYACUCHO': (-13.1588, -74.2239), 'CAJAMARCA': (-7.1638, -78.5003),
    'CALLAO': (-12.0566, -77.1181), 'CUSCO': (-13.5226, -71.9673), 'HUANCAVELICA': (-12.7826, -74.9727),
    'HUANUCO': (-9.9306, -76.2422), 'ICA': (-14.0678, -75.7286), 'JUNIN': (-12.0651, -75.2049),
    'LA LIBERTAD': (-8.1091, -79.0215), 'LAMBAYEQUE': (-6.7714, -79.8409), 'LIMA': (-12.0464, -77.0282),
    'LORETO': (-3.7491, -73.2443), 'MADRE DE DIOS': (-12.5933, -69.1836), 'MOQUEGUA': (-17.1983, -70.9357),
    'PASCO': (-10.6675, -76.2567), 'PIURA': (-5.1945, -80.6328), 'PUNO': (-15.8402, -70.0219),
    'SAN MARTIN': (-6.4878, -76.3597), 'TACNA': (-18.0146, -70.2536), 'TUMBES': (-3.5669, -80.4515),
    'UCAYALI': (-8.3791, -74.5539)
}

def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia en km entre dos puntos de la tierra."""
    if pd.isna(lat1) or pd.isna(lon1): return np.nan
    R = 6371  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def main():
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8")
    
    # Eliminar la variable inventada anterior
    if 'NIVEL_PRECIO_PROXY' in df.columns:
        df = df.drop(columns=['NIVEL_PRECIO_PROXY'])
        
    distancias = []
    for idx, row in df.iterrows():
        region = str(row['REGIÓN']).upper()
        if region in CAPITALES and pd.notna(row['latitud']):
            lat_cap, lon_cap = CAPITALES[region]
            dist = haversine(row['latitud'], row['longitud'], lat_cap, lon_cap)
            distancias.append(dist)
        else:
            distancias.append(np.nan)
            
    df['DISTANCIA_CAPITAL_KM'] = distancias
    
    # Crear el nuevo Índice de Costo Logístico basado matemáticamente en la distancia
    def assign_cost(dist):
        if pd.isna(dist): return np.nan
        if dist < 20: return 1  # Bajo (Accesible localmente)
        elif dist < 80: return 2 # Medio (Transporte interprovincial)
        else: return 3 # Alto (Remoto, tour especializado)
        
    df['INDICE_COSTO_LOGISTICO'] = df['DISTANCIA_CAPITAL_KM'].apply(assign_cost)
    
    df.to_csv(CSV_PATH, index=False, sep=";", encoding="utf-8")
    print("Variable actualizada con éxito. ¡Ahora usamos cálculos geoespaciales reales!")

if __name__ == "__main__":
    main()
