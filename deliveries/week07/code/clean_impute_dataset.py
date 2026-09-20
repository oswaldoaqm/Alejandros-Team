import csv

CSV_FILE = "/home/miguel/Escritorio/UTEC/2026-2/DPD/Proyecto/deliveries/week06/data/processed/dreemgo_master_dataset.csv"

def impute_data():
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f, delimiter=";"))
    
    fieldnames = list(reader[0].keys())
    
    for row in reader:
        # 1. Conservar Jerarquía
        jerarquia = row.get("JERARQUIA_OFICIAL", "1").strip()
        if jerarquia not in ["1", "2", "3", "4"]:
            jerarquia = "1"
        row["JERARQUIA_OFICIAL"] = jerarquia
        
        # 2. Imputar Tipo de Ingreso basado en Jerarquía
        if jerarquia in ["3", "4"]:
            row["TIPO_INGRESO"] = "Pagado"
        else:
            row["TIPO_INGRESO"] = "Libre"
            
        # 3. Imputar Época Propicia basado en Zona Climática / Altitud
        # Las zonas ecológicas en el dataset están guardadas como: "Templado Seco (Quechua)", "Frío (Suni)", etc.
        zona = row.get("ZONA_CLIMATICA", "").lower()
        
        if any(z in zona for z in ["quechua", "suni", "janca", "puna", "frío"]):
            row["EPOCA_PROPICIA"] = "Abril a Noviembre"
        elif any(z in zona for z in ["omagua", "rupa", "selva"]):
            row["EPOCA_PROPICIA"] = "Mayo a Octubre"
        else:
            row["EPOCA_PROPICIA"] = "Todo el año"
            
    # Sobreescribir el archivo ya limpio
    with open(CSV_FILE, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(reader)

if __name__ == "__main__":
    impute_data()
