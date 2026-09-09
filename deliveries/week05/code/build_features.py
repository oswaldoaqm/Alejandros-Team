"""
Pipeline de Feature Engineering Espacial - DreemGO (Semana 5)
-------------------------------------------------------------
Autor: Equipo DreemGO
Descripción: Script que procesa los datos turísticos y genera características (features)
matemáticas justificadas para el modelo de Machine Learning, evitando el uso de
datos scrapeados ilegalmente (ej. TripAdvisor).

Justificación del Modelo de Costos:
Dado que el precio dinámico por temporada no está disponible de forma abierta,
el costo de turismo interno en Perú se modela matemáticamente basado en la
ACCESIBILIDAD LOGÍSTICA. 
1. Se calcula la Distancia Haversine al nodo logístico más cercano (Capital).
2. A mayor distancia, mayor es el costo de transporte (buses, tours 4x4, tiempo).
3. Se aplica un leve recargo a sitios Arqueológicos/Museos asumiendo cobro de ticket.
"""

import csv
import math

CSV_PATH = "../data/dataset_enriched.csv"

# Coordenadas de los principales nodos logísticos (Capitales Regionales)
CAPITALES = {
    'AMAZONAS': (-6.2294, -77.8728), 'ANCASH': (-9.5278, -77.5278), 'CUSCO': (-13.5226, -71.9673),
    'LIMA': (-12.0464, -77.0282), 'AREQUIPA': (-16.3989, -71.5350), 'PUNO': (-15.8402, -70.0219),
    'LORETO': (-3.7491, -73.2443), 'PIURA': (-5.1945, -80.6328), 'ICA': (-14.0678, -75.7286),
    'JUNIN': (-12.0651, -75.2049), 'CAJAMARCA': (-7.1638, -78.5003), 'LA LIBERTAD': (-8.1091, -79.0215),
    'LAMBAYEQUE': (-6.7714, -79.8409), 'AYACUCHO': (-13.1588, -74.2239), 'HUANUCO': (-9.9306, -76.2422),
    'UCAYALI': (-8.3791, -74.5539), 'SAN MARTIN': (-6.4878, -76.3597), 'TACNA': (-18.0146, -70.2536),
    'MADRE DE DIOS': (-12.5933, -69.1836), 'APURIMAC': (-13.6339, -72.8814), 'PASCO': (-10.6675, -76.2567),
    'MOQUEGUA': (-17.1983, -70.9357), 'TUMBES': (-3.5669, -80.4515), 'HUANCAVELICA': (-12.7826, -74.9727),
    'CALLAO': (-12.0566, -77.1181)
}

def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia geodésica en kilómetros entre dos puntos terrestres."""
    R = 6371  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calcular_indice_costo(distancia_km, categoria):
    """
    Asigna un Índice de Costo Logístico (1=Bajo, 2=Medio, 3=Alto).
    Lógica Sensata:
    - Menos de 15 km: Accesible con transporte urbano local (Costo 1).
    - De 15 a 60 km: Requiere transporte interprovincial o tour corto (Costo 2).
    - Más de 60 km: Requiere expedición, auto 4x4 o tour de día completo (Costo 3).
    - Penalización por Entrada: Sitios Culturales y Museos suelen cobrar boleto.
    """
    if distancia_km == "":
        return ""
    
    dist = float(distancia_km)
    
    # 1. Base logística por distancia
    if dist < 15:
        costo = 1
    elif dist < 60:
        costo = 2
    else:
        costo = 3
        
    # 2. Penalización por ticket de ingreso (Heurística sensata)
    if "MANIFESTACIONES CULTURALES" in categoria or "REALIZACIONES TÉCNICAS" in categoria:
        costo += 1  # Sumamos 1 nivel asumiendo pago de boleto turístico/museo
        
    # El índice máximo es 3 (Exclusivo/Caro)
    return min(costo, 3)

def main():
    print("Iniciando Pipeline de Feature Engineering...")
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f, delimiter=";"))
        
    headers = reader[0]
    
    # Limpiar ejecuciones previas para no duplicar columnas
    for col in ['DISTANCIA_CAPITAL_KM', 'INDICE_COSTO_LOGISTICO', 'NIVEL_PRECIO_PROXY']:
        if col in headers:
            idx = headers.index(col)
            headers.pop(idx)
            for row in reader[1:]:
                row.pop(idx)
                
    # Agregar las nuevas columnas definitivas
    headers.extend(['DISTANCIA_CAPITAL_KM', 'INDICE_COSTO_LOGISTICO'])
    
    idx_lat = headers.index('latitud')
    idx_lon = headers.index('longitud')
    idx_reg = headers.index('REGIÓN')
    idx_cat = headers.index('CATEGORÍA')
    
    for row in reader[1:]:
        lat_str = row[idx_lat]
        lon_str = row[idx_lon]
        region = row[idx_reg].upper()
        categoria = row[idx_cat]
        
        dist_str = ""
        costo_str = ""
        
        if lat_str and lon_str and region in CAPITALES:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                lat_cap, lon_cap = CAPITALES[region]
                
                # Cálculo real de Haversine
                dist = haversine(lat, lon, lat_cap, lon_cap)
                dist_str = f"{dist:.2f}"
                
                # Asignación sensata
                costo = calcular_indice_costo(dist, categoria)
                costo_str = str(costo)
            except ValueError:
                pass
                
        row.extend([dist_str, costo_str])
        
    # Guardar sobreescribiendo el mismo CSV enriquecido
    with open(CSV_PATH, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(reader)
        
    print("¡Finalizado! El dataset tiene ahora cálculos espaciales reales y documentados.")

if __name__ == "__main__":
    main()
