import csv
import random
from datetime import datetime, timedelta

# Regiones y coordenadas base aproximadas para generar data cercana
REGIONES_BASE = {
    'CUSCO': (-13.5226, -71.9673), 'LIMA': (-12.0464, -77.0282), 'AREQUIPA': (-16.3989, -71.5350),
    'PUNO': (-15.8402, -70.0219), 'ICA': (-14.0678, -75.7286), 'ANCASH': (-9.5278, -77.5278),
    'LORETO': (-3.7491, -73.2443), 'PIURA': (-5.1945, -80.6328), 'CAJAMARCA': (-7.1638, -78.5003)
}

TIPOS_EVENTO = [
    ("Feria Gastronómica", "Gastronomía"), ("Fiesta Patronal", "Cultura"), 
    ("Descuento de Temporada - Hotel", "Alojamiento"), ("Tour Promocional", "Aventura"),
    ("Exhibición de Artesanía", "Cultura"), ("Festival de Música Local", "Entretenimiento")
]

NOMBRES_LOCALES = ["El Buen Sabor", "La Tradición", "Pacha", "Andes", "Sol y Luna", "Místico", "Aventura Extrema"]

CSV_OUTPUT = "../data/comercios_ferias_locales.csv"

def generate_synthetic_data(num_records=500):
    records = []
    # Generaremos eventos para el año 2024 (Futuro cercano para predicción)
    base_date = datetime(2024, 1, 1)
    
    for i in range(1, num_records + 1):
        region, (lat, lon) = random.choice(list(REGIONES_BASE.items()))
        tipo_nombre, categoria = random.choice(TIPOS_EVENTO)
        
        # Dispersión geográfica (Eventos esparcidos alrededor de la ciudad)
        lat_evento = lat + random.uniform(-0.1, 0.1)
        lon_evento = lon + random.uniform(-0.1, 0.1)
        
        nombre_evento = f"{tipo_nombre} {random.choice(NOMBRES_LOCALES)} {region}"
        
        # Fechas aleatorias (Los eventos duran entre 1 y 15 días)
        start_days_offset = random.randint(0, 350)
        duracion = random.randint(1, 15)
        
        fecha_inicio = base_date + timedelta(days=start_days_offset)
        fecha_fin = fecha_inicio + timedelta(days=duracion)
        
        # Simular un "Costo Promedio" o entrada
        costo = random.choice([0, 0, 15, 30, 50, 100]) # Mucho evento gratuito (0)
        
        # Score de relevancia (Qué tanto invirtió el negocio en publicidad 1-5)
        relevancia_ad = random.randint(1, 5)
        
        records.append({
            "ID_EVENTO": f"EVT-{i:04d}",
            "NOMBRE_EVENTO": nombre_evento,
            "REGION": region,
            "CATEGORIA": categoria,
            "LATITUD": round(lat_evento, 6),
            "LONGITUD": round(lon_evento, 6),
            "FECHA_INICIO": fecha_inicio.strftime("%Y-%m-%d"),
            "FECHA_FIN": fecha_fin.strftime("%Y-%m-%d"),
            "COSTO_PEN": costo,
            "RELEVANCIA_PUBLICIDAD": relevancia_ad
        })
        
    return records

def main():
    print("Generando 500 registros sintéticos de eventos y comercios locales...")
    datos = generate_synthetic_data(500)
    
    campos = ["ID_EVENTO", "NOMBRE_EVENTO", "REGION", "CATEGORIA", "LATITUD", "LONGITUD", 
              "FECHA_INICIO", "FECHA_FIN", "COSTO_PEN", "RELEVANCIA_PUBLICIDAD"]
              
    with open(CSV_OUTPUT, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
        writer.writeheader()
        writer.writerows(datos)
        
    print(f"¡Éxito! Dataset comercial generado en: {CSV_OUTPUT}")

if __name__ == "__main__":
    main()
