import csv
import sys

CSV_PATH = "../data/dataset_enriched.csv"

def main():
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = list(reader)
    except FileNotFoundError:
        print("ERROR_FILE_NOT_FOUND")
        return
        
    print(f"--- REVISIÓN MINUCIOSA DEL DATASET ENRIQUECIDO ---")
    print(f"Registros totales: {len(rows)}")
    
    if len(rows) == 0:
        return
        
    cols = list(rows[0].keys())
    print(f"Columnas totales: {len(cols)}\n")
    
    if "ALTITUD" not in cols or "NIVEL_PRECIO_PROXY" not in cols:
        print("[ERROR CRÍTICO] Las columnas ALTITUD o NIVEL_PRECIO_PROXY no existen.")
        return

    # 1. Chequeo de Latitud/Longitud
    peru_lat = (-18.4, 0.0)
    peru_lon = (-81.4, -68.6)
    
    coords_valid = 0
    lat_ok = 0
    lon_ok = 0
    
    # 2. Chequeo de Altitud
    altitudes = []
    cusco_alts = []
    lima_alts = []
    alt_nulos = 0
    
    # 3. Chequeo de Precios
    precios = {"1": 0, "2": 0, "3": 0}
    cusco_cult_count = 0
    cusco_cult_sum = 0
    
    for row in rows:
        lat_str = row.get("latitud", "")
        lon_str = row.get("longitud", "")
        alt_str = row.get("ALTITUD", "")
        precio_str = row.get("NIVEL_PRECIO_PROXY", "")
        region = row.get("REGIÓN", "").upper()
        categoria = row.get("CATEGORÍA", "")
        
        # Conteo de Precios
        if precio_str in precios:
            precios[precio_str] += 1
            
        if region == "CUSCO" and "MANIFESTACIONES CULTURALES" in categoria:
            cusco_cult_count += 1
            if precio_str.isdigit():
                cusco_cult_sum += int(precio_str)
        
        if lat_str and lon_str:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                coords_valid += 1
                
                if peru_lat[0] <= lat <= peru_lat[1]:
                    lat_ok += 1
                if peru_lon[0] <= lon <= peru_lon[1]:
                    lon_ok += 1
                    
                if alt_str:
                    alt = float(alt_str)
                    altitudes.append(alt)
                    if region == "CUSCO": cusco_alts.append(alt)
                    if region == "LIMA": lima_alts.append(alt)
                else:
                    alt_nulos += 1
            except ValueError:
                pass
                
    if coords_valid > 0:
        print(f"1. LATITUD/LONGITUD:")
        print(f"   - Registros con coordenadas: {coords_valid}")
        print(f"   - % Latitudes dentro de Perú: {lat_ok/coords_valid:.2%}")
        print(f"   - % Longitudes dentro de Perú: {lon_ok/coords_valid:.2%}")
        if lat_ok < coords_valid or lon_ok < coords_valid:
            print("   [ALERTA CRÍTICA] Hay coordenadas fuera del territorio peruano.")
            
        print(f"\n2. ALTITUD:")
        print(f"   - Nulos en recursos geolocalizados: {alt_nulos} (Esperado: 0)")
        if altitudes:
            alt_min = min(altitudes)
            alt_max = max(altitudes)
            print(f"   - Rango de Altitud: {alt_min:.1f} msnm a {alt_max:.1f} msnm")
            
            cusco_prom = sum(cusco_alts)/len(cusco_alts) if cusco_alts else 0
            lima_prom = sum(lima_alts)/len(lima_alts) if lima_alts else 0
            print(f"   - Altitud promedio Cusco: {cusco_prom:.1f} msnm (Lógico: > 2500)")
            print(f"   - Altitud promedio Lima: {lima_prom:.1f} msnm (Lógico: < 1500)")
            
            if alt_max > 6800:
                print(f"   [ALERTA] Altitud máxima ({alt_max}) excede la montaña más alta del Perú.")
            if alt_min < -100:
                print(f"   [ALERTA] Altitud mínima ({alt_min}) es muy negativa (posible océano/falla API).")
                
    print(f"\n3. NIVEL_PRECIO_PROXY:")
    print("   - Distribución de valores:")
    for val, count in precios.items():
        print(f"       Nivel {val}: {count} recursos ({(count/len(rows)):.2%})")
        
    if cusco_cult_count > 0:
        print(f"   - Prueba de estrés: Sitios culturales en Cusco tienen nivel promedio de {cusco_cult_sum/cusco_cult_count:.1f} (Esperado: 3.0)")

if __name__ == "__main__":
    main()
