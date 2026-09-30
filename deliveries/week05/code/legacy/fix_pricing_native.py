import csv
import math

CSV_PATH = "../data/dataset_enriched.csv"

# Coordenadas aproximadas de las 25 capitales regionales
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
    R = 6371  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def main():
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f, delimiter=";"))
        
    headers = reader[0]
    
    # Remover la columna NIVEL_PRECIO_PROXY vieja si existe
    if 'NIVEL_PRECIO_PROXY' in headers:
        idx_proxy = headers.index('NIVEL_PRECIO_PROXY')
        headers.pop(idx_proxy)
        for row in reader[1:]:
            row.pop(idx_proxy)
            
    # Agregar nuevas columnas
    headers.extend(['DISTANCIA_CAPITAL_KM', 'INDICE_COSTO_LOGISTICO'])
    
    idx_lat = headers.index('latitud')
    idx_lon = headers.index('longitud')
    idx_reg = headers.index('REGIÓN')
    
    for row in reader[1:]:
        lat_str = row[idx_lat]
        lon_str = row[idx_lon]
        region = row[idx_reg].upper()
        
        dist = ""
        costo = ""
        
        if lat_str and lon_str and region in CAPITALES:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                lat_cap, lon_cap = CAPITALES[region]
                d = haversine(lat, lon, lat_cap, lon_cap)
                dist = f"{d:.2f}"
                
                if d < 20: costo = "1"
                elif d < 80: costo = "2"
                else: costo = "3"
            except ValueError:
                pass
                
        row.extend([dist, costo])
        
    with open(CSV_PATH, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(reader)
        
    print("Variable actualizada con éxito. ¡Ahora usamos cálculos geoespaciales reales (Haversine)!")

if __name__ == "__main__":
    main()
