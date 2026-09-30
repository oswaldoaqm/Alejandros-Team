"""
=========================  SCRIPT SUPERADO - NO EJECUTAR  =========================

Genera JERARQUIA_OFICIAL y TIPO_INGRESO con random.choices() y los escribe sobre
data/processed/dreemgo_master_dataset.csv, que es el MISMO archivo de salida que
produce scraper_mincetur.py con datos reales de la ficha de MINCETUR.

Ejecutarlo destruye la extraccion real. El dataset que hay hoy en el repositorio
SI contiene la jerarquia oficial verdadera; esta verificado en
DataAnalysis.md seccion 3.1 (chi2 contra los pesos del generador, asociacion con
categoria y region, y revision de recursos concretos: Machu Picchu 4, Chan Chan 4,
Ventana del Colca 1).

Se conserva solo como registro de un paso intermedio del desarrollo. No forma parte
del pipeline reproducible descrito en week06/README.md.
==================================================================================
"""

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
