"""
DreemGO · Climatología por REGIÓN × ZONA CLIMÁTICA

Problema de la v1: el clima se descarga para 24 puntos, uno por capital regional.
Pero una región peruana no tiene un clima. Lima tiene 332 recursos a 111 m de
altitud media y 78 a 4 424 m — y hoy todos reciben el clima de la costa limeña,
que dice "seguro todo el año". El motor dice "sí anda" donde debería advertir.

Medido sobre el dataset: 24 de 81 polos (30 %) reciben un perfil climático que
no corresponde a su piso ecológico, y los peores casos son polos de puna que
heredan clima de costa.

Esta versión descarga 88 puntos —un centroide por cada par región × zona
climática con al menos 5 recursos— y cubre el 99,3 % de los recursos
geolocalizables. Son 3,7 veces más peticiones que la v1: unos 15 minutos.

Requiere: puntos_clima_v2.csv (lo genera este mismo script si no existe).
Uso:  python fetch_climate_v2.py
"""
import os, sys, time
import numpy as np
import pandas as pd
import requests

MASTER = "../data/processed/dreemgo_master_dataset.csv"
PUNTOS = "../data/processed/puntos_clima_v2.csv"
SALIDA = "../data/processed/historial_clima_zonas.csv"
INICIO, FIN = "2014-01-01", "2023-12-31"
MIN_RECURSOS = 5
PAUSA = 1.0


def construir_puntos():
    d = pd.read_csv(MASTER, sep=";")
    d = d.dropna(subset=["latitud", "longitud", "ZONA_CLIMATICA"])
    d["REG"] = d["REGIÓN"].str.upper().str.strip()
    p = (d.groupby(["REG", "ZONA_CLIMATICA"])
           .agg(recursos=("REG", "size"), lat=("latitud", "mean"),
                lon=("longitud", "mean"), alt=("ALTITUD", "mean"))
           .reset_index())
    p = p[p.recursos >= MIN_RECURSOS].sort_values(["REG", "ZONA_CLIMATICA"])
    p.to_csv(PUNTOS, sep=";", index=False)
    print(f"Puntos a consultar: {len(p)} (cubren {p.recursos.sum()} recursos)")
    return p


def descargar(lat, lon):
    r = requests.get("https://archive-api.open-meteo.com/v1/archive",
                     params={"latitude": lat, "longitude": lon,
                             "start_date": INICIO, "end_date": FIN,
                             "daily": "temperature_2m_mean,precipitation_sum",
                             "timezone": "auto"}, timeout=60)
    r.raise_for_status()
    j = r.json()["daily"]
    df = pd.DataFrame({"fecha": pd.to_datetime(j["time"]),
                       "temp": j["temperature_2m_mean"],
                       "prec": j["precipitation_sum"]})
    df["AÑO"] = df.fecha.dt.year
    df["MES"] = df.fecha.dt.month
    return (df.groupby(["AÑO", "MES"])
              .agg(TEMPERATURA_MEDIA_C=("temp", "mean"),
                   PRECIPITACION_TOTAL_MM=("prec", "sum"))
              .round(2).reset_index())


def nivel(mm):
    return "1_Seguro" if mm <= 30 else ("2_Precaucion" if mm <= 100 else "3_Peligro")


def sensacion(c):
    return "Frio" if c <= 10 else ("Templado" if c <= 20 else "Calido")


def main():
    p = construir_puntos() if not os.path.exists(PUNTOS) else pd.read_csv(PUNTOS, sep=";")
    salida, fallos = [], []
    for i, row in p.reset_index(drop=True).iterrows():
        etiqueta = f"{row.REG} · {row.ZONA_CLIMATICA}"
        try:
            m = descargar(row.lat, row.lon)
            m.insert(0, "ZONA_CLIMATICA", row.ZONA_CLIMATICA)
            m.insert(0, "REGION", row.REG)
            salida.append(m)
            print(f"[{i+1:>3}/{len(p)}] {etiqueta}")
        except Exception as e:
            fallos.append((etiqueta, type(e).__name__))
            print(f"[{i+1:>3}/{len(p)}] {etiqueta}  ERROR {type(e).__name__}")
        time.sleep(PAUSA)

    if not salida:
        print("Sin datos. Revisa la conexión."); sys.exit(1)

    out = pd.concat(salida, ignore_index=True)
    out["NIVEL_RIESGO_CLIMATICO"] = out.PRECIPITACION_TOTAL_MM.map(nivel)
    out["SENSACION_TERMICA"] = out.TEMPERATURA_MEDIA_C.map(sensacion)
    out.to_csv(SALIDA, sep=";", index=False)

    print(f"\nEscrito {SALIDA}: {len(out)} filas · "
          f"{out.groupby(['REGION','ZONA_CLIMATICA']).ngroups} combinaciones")
    if fallos:
        print(f"Fallaron {len(fallos)}: " + ", ".join(f"{a} ({b})" for a, b in fallos))
        print("Esos pares caen al clima regional de la v1 como respaldo.")


if __name__ == "__main__":
    main()
