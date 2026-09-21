import csv

FILE_PATH = "/home/miguel/Escritorio/UTEC/2026-2/DPD/Proyecto/deliveries/week06/data/processed/historial_clima_regiones.csv"

def discretize_rain(mm):
    if mm <= 30: return '1_Seguro'
    elif mm <= 100: return '2_Precaucion'
    else: return '3_Peligro'

def discretize_temp(celsius):
    if celsius <= 10: return 'Frio'
    elif celsius <= 20: return 'Templado'
    else: return 'Calido'

def main():
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f, delimiter=';'))
        
    fieldnames = list(reader[0].keys())
    if "NIVEL_RIESGO_CLIMATICO" not in fieldnames:
        fieldnames.extend(["NIVEL_RIESGO_CLIMATICO", "SENSACION_TERMICA"])
        
    with open(FILE_PATH, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        
        for row in reader:
            precip = float(row.get("PRECIPITACION_TOTAL_MM", 0))
            temp = float(row.get("TEMPERATURA_MEDIA_C", 0))
            
            row["NIVEL_RIESGO_CLIMATICO"] = discretize_rain(precip)
            row["SENSACION_TERMICA"] = discretize_temp(temp)
            
            writer.writerow(row)
            
    print("¡Discretización completada con Python puro!")

if __name__ == "__main__":
    main()
