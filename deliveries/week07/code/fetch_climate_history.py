import requests
import csv
import time
from collections import defaultdict
from datetime import datetime

# Usamos los mismos Nodos Logísticos (Capitales) que el dataset base para asegurar la relación 1 a 1
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

# 10 años de data histórica (2014 a 2023 completo)
START_DATE = "2014-01-01"
END_DATE = "2023-12-31"
CSV_OUTPUT = "../data/historial_clima_regiones.csv"

def main():
    print("Iniciando descarga histórica del clima (2014-2023)...")
    resultados_mensuales = []

    # Iteramos sobre cada región para relacionarlo con nuestro dataset original
    for region, coords in CAPITALES.items():
        lat, lon = coords
        print(f"Descargando data para {region}...")
        
        # Endpoint del archivo histórico de Open-Meteo
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={START_DATE}&end_date={END_DATE}&daily=temperature_2m_mean,precipitation_sum&timezone=America%2FLima"
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                fechas = data['daily']['time']
                temps = data['daily']['temperature_2m_mean']
                precs = data['daily']['precipitation_sum']
                
                # Agruparemos la data diaria a un resumen mensual por año para ML de Forecasting
                meses_agrupados = defaultdict(lambda: {"temp_sum": 0, "prec_sum": 0, "dias": 0})
                
                for i in range(len(fechas)):
                    if temps[i] is not None and precs[i] is not None:
                        # Extraer 'YYYY-MM'
                        year_month = fechas[i][:7] 
                        meses_agrupados[year_month]["temp_sum"] += temps[i]
                        meses_agrupados[year_month]["prec_sum"] += precs[i]
                        meses_agrupados[year_month]["dias"] += 1
                
                # Guardar el promedio/suma mensual
                for year_month, stats in meses_agrupados.items():
                    avg_temp = stats["temp_sum"] / stats["dias"]
                    total_precip = stats["prec_sum"]
                    
                    year, month = year_month.split('-')
                    
                    resultados_mensuales.append({
                        "REGION": region,
                        "AÑO": year,
                        "MES": month,
                        "TEMPERATURA_MEDIA_C": round(avg_temp, 2),
                        "PRECIPITACION_TOTAL_MM": round(total_precip, 2)
                    })
                    
            else:
                print(f"  -> Error API para {region}: {response.status_code}")
        except Exception as e:
            print(f"  -> Excepción en {region}: {e}")
        
        # Pausa para no saturar la API gratuita
        time.sleep(2)
        
    # Escribir el CSV resultante
    if resultados_mensuales:
        campos = ["REGION", "AÑO", "MES", "TEMPERATURA_MEDIA_C", "PRECIPITACION_TOTAL_MM"]
        with open(CSV_OUTPUT, "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            writer.writeheader()
            writer.writerows(resultados_mensuales)
        print(f"\n¡Exito! Historial consolidado guardado en: {CSV_OUTPUT}")
        print(f"Total de registros generados: {len(resultados_mensuales)} meses de data meteorológica.")

if __name__ == "__main__":
    main()
