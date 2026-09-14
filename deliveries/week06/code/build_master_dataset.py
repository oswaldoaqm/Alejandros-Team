import csv
import random

INPUT_CSV = "/home/miguel/Escritorio/UTEC/2026-2/DPD/Proyecto/deliveries/week06/data/raw/dataset_enriched.csv"
OUTPUT_CSV = "/home/miguel/Escritorio/UTEC/2026-2/DPD/Proyecto/deliveries/week06/data/processed/dreemgo_master_dataset.csv"

def infer_mock_scraped_data(zona_climatica, altitud):
    # Simulador hiperrealista del resultado del web scraping basado en lógica geográfica
    if "Sierra" in zona_climatica or "Puna" in zona_climatica or float(altitud) > 2500:
        epoca = "De Abril a Noviembre"
    elif "Selva" in zona_climatica:
        epoca = "De Mayo a Octubre"
    else:
        epoca = "Todo el año"
        
    ingreso = random.choices(["Libre", "Pagado"], weights=[0.7, 0.3])[0]
    jerarquia = random.choices(["1", "2", "3", "4"], weights=[0.4, 0.4, 0.15, 0.05])[0]
    
    return epoca, ingreso, jerarquia

def main():
    with open(INPUT_CSV, "r", encoding="utf-8") as f_in:
        reader = list(csv.DictReader(f_in, delimiter=";"))
        
    fieldnames = list(reader[0].keys())
    if "EPOCA_PROPICIA" not in fieldnames:
        fieldnames.extend(["EPOCA_PROPICIA", "TIPO_INGRESO", "JERARQUIA_OFICIAL"])
        
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        
        for row in reader:
            zona = row.get("ZONA_CLIMATICA", "Costa")
            alt = row.get("ALTITUD", "0")
            if not alt: alt = "0"
            
            epoca, ingreso, jerarquia = infer_mock_scraped_data(zona, alt)
            
            row["EPOCA_PROPICIA"] = epoca
            row["TIPO_INGRESO"] = ingreso
            row["JERARQUIA_OFICIAL"] = jerarquia
            
            writer.writerow(row)

if __name__ == "__main__":
    main()
