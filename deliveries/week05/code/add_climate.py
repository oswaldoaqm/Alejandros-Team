import csv

CSV_PATH = "deliveries/week05/data/dataset_enriched.csv"

def clasificar_clima(altitud, region):
    if altitud == "":
        return ""
    
    alt = float(altitud)
    reg = region.upper()
    
    selva = ['LORETO', 'UCAYALI', 'MADRE DE DIOS', 'SAN MARTIN', 'AMAZONAS']
    
    if reg in selva and alt < 1500:
        return "Tropical Húmedo (Selva)"
    
    if alt <= 500: return "Cálido / Desértico (Costa)"
    elif alt <= 2300: return "Templado Cálido (Yunga)"
    elif alt <= 3500: return "Templado Seco (Quechua)"
    elif alt <= 4000: return "Frío (Suni)"
    elif alt <= 4800: return "Muy Frío (Puna)"
    else: return "Glacial / Nieve (Janca)"

def main():
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f, delimiter=";"))
        
    headers = reader[0]
    
    if 'ZONA_CLIMATICA' in headers:
        idx_clima = headers.index('ZONA_CLIMATICA')
        headers.pop(idx_clima)
        for row in reader[1:]:
            row.pop(idx_clima)
            
    headers.append('ZONA_CLIMATICA')
    
    idx_alt = headers.index('ALTITUD')
    idx_reg = headers.index('REGIÓN')
    
    for row in reader[1:]:
        alt = row[idx_alt]
        reg = row[idx_reg]
        clima = clasificar_clima(alt, reg)
        row.append(clima)
        
    with open(CSV_PATH, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(reader)
        
    print("Variable ZONA_CLIMATICA agregada exitosamente mediante Inferencia Geográfica.")

if __name__ == "__main__":
    main()
