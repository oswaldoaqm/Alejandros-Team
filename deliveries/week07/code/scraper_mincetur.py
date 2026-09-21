"""
Web Scraper Oficial COMPLETO - DreemGO (Tarea Analítica 3)
----------------------------------------------------------
Este script extrae información oficial de las 4,915 fichas de MINCETUR.
Tiempo estimado de ejecución: 1.5 - 2 horas.
"""

import csv
import time
import requests
from bs4 import BeautifulSoup
import re

# Usamos la nueva estructura de carpetas
CSV_INPUT = "../data/raw/dataset_enriched.csv"
CSV_OUTPUT = "../data/processed/dreemgo_master_dataset.csv"

def extract_info_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text(separator=' ', strip=True)
    
    data = {
        "EPOCA_PROPICIA": "Todo el año", # Valor por defecto
        "TIPO_INGRESO": "No especificado",
        "JERARQUIA_OFICIAL": "No clasificado"
    }
    
    epoca_match = re.search(r'(?:Época propicia|Epoca propicia).*?:?\s*([A-Za-z0-9,\s]+)', text_content, re.IGNORECASE)
    if epoca_match:
        data["EPOCA_PROPICIA"] = epoca_match.group(1)[:50].strip()
        
    ingreso_match = re.search(r'(?:Tipo de Ingreso|Ingreso).*?:?\s*([A-Za-z0-9,\s]+)', text_content, re.IGNORECASE)
    if ingreso_match:
        data["TIPO_INGRESO"] = ingreso_match.group(1)[:30].strip()
        
    jerarquia_match = re.search(r'(?:Jerarquía|Jerarquia).*?:?\s*([1-4])', text_content, re.IGNORECASE)
    if jerarquia_match:
        data["JERARQUIA_OFICIAL"] = jerarquia_match.group(1).strip()
        
    return data

def main():
    print("Iniciando Web Scraping MASIVO de MINCETUR (4,915 registros)...")
    
    with open(CSV_INPUT, "r", encoding="utf-8") as f_in:
        reader = list(csv.DictReader(f_in, delimiter=";"))
        
    fieldnames = list(reader[0].keys())
    if "EPOCA_PROPICIA" not in fieldnames:
        fieldnames.extend(["EPOCA_PROPICIA", "TIPO_INGRESO", "JERARQUIA_OFICIAL"])
        
    # Abrimos el archivo de salida
    with open(CSV_OUTPUT, "w", encoding="utf-8", newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        
        # PROCESAMOS TODO EL DATASET (Sin el límite de 10)
        total_filas = len(reader)
        for idx, row in enumerate(reader):
            url = row.get("URL", "")
            
            if "mincetur.gob.pe" in url:
                if idx % 50 == 0:
                    print(f"[{idx}/{total_filas}] Extrayendo datos... (Por favor espera)")
                    
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        extraido = extract_info_from_html(response.text)
                        row["EPOCA_PROPICIA"] = extraido["EPOCA_PROPICIA"]
                        row["TIPO_INGRESO"] = extraido["TIPO_INGRESO"]
                        row["JERARQUIA_OFICIAL"] = extraido["JERARQUIA_OFICIAL"]
                    else:
                        row["EPOCA_PROPICIA"] = "No accesible"
                except Exception as e:
                    row["EPOCA_PROPICIA"] = "Error de conexión"
                    
                # PAUSA DE SEGURIDAD OBLIGATORIA (1 segundo) para no ser bloqueados
                time.sleep(1)
            else:
                row["EPOCA_PROPICIA"] = "Sin URL"
                row["TIPO_INGRESO"] = "Sin URL"
                row["JERARQUIA_OFICIAL"] = "Sin URL"
                
            writer.writerow(row)
            # Flush asegura que si cancelas a la mitad, los datos extraídos hasta ahí se guarden
            f_out.flush() 
            
    print("\n¡Proceso finalizado! Datos reales guardados en dreemgo_master_dataset.csv")

if __name__ == "__main__":
    main()
