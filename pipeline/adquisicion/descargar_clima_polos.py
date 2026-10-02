"""
Clima diario 2016-2025 en el centro de cada polo, desde Open-Meteo Archive.

Por qué un punto por polo
-------------------------
Hasta ahora el clima venía de 24 puntos, uno por capital regional. El polo de
Pozuzo (748 m, selva alta) recibía el clima medido en Cerro de Pasco (más de
4 000 m). Agrupar por región × zona climática tampoco alcanza: 73 de esos 88
grupos abarcan más de 60 km de radio. Un punto por polo sí: ningún polo pasa
de 80 km de diámetro.

La cuota, y por qué este script tarda días
------------------------------------------
Open-Meteo es gratis para uso no comercial con 10 000 llamadas al día, 5 000
por hora y 600 por minuto. Pedir 10 años de datos diarios de un punto cuenta como
~261 llamadas (una por cada 14 días de datos). Por eso el script:
  - pide un polo por vez y anota lo gastado en cuota.json;
  - no pasa de 550 por minuto (dos polos), 4 800 por hora ni 9 500 por día;
  - cuando se acaba la cuota, espera solo y sigue (Ctrl+C lo corta sin perder
    nada: al volver a correrlo retoma donde quedó);
  - baja primero los polos que más se recomiendan, así lo parcial ya sirve.
Los 222 polos toman unos 6 días con la PC prendida. Si la apagas, vuelves a
lanzarlo y sigue.

Qué pide por punto
------------------
- Lluvia diaria y horas con lluvia: qué meses llueve y cuántos días.
- Nieve: los pasos altos de los polos con nevados.
- Horas de sol: la costa en invierno casi no registra lluvia pero pasa meses
  sin ver el sol; con solo la lluvia, el modelo la daría por temporada ideal.
- Temperatura máxima, mínima y media, a la altura del terreno en ese punto
  (Open-Meteo la devuelve en `elevation`). No se fija otra altura a propósito:
  en polos con nevados la mediana de los recursos es la de las cumbres (el
  polo 112 da 6 134 m), y lo que importa es el frío donde el viajero duerme.
  El pipeline ajusta la temperatura a la altitud del punto base con el
  gradiente estándar, sin gastar cuota.
Siete variables cuestan lo mismo que una: Open-Meteo solo cobra de más a
partir de diez.

Salida (fuera de git; el promedio mensual lo arma el pipeline)
  data/externos/clima/puntos_polos.csv       los puntos pedidos, en orden
  data/externos/clima/crudo/polo_<id>.json   respuesta cruda por polo
  data/externos/clima/cuota.json             lo gastado de la cuota

Licencia: CC BY 4.0 · Open-Meteo.com, sobre reanálisis ERA5 y ERA5-Land
(Copernicus Climate Change Service).

Uso
  python pipeline/adquisicion/descargar_clima_polos.py             # corre y espera la cuota
  python pipeline/adquisicion/descargar_clima_polos.py --sin-esperar   # para al agotarla
  python pipeline/adquisicion/descargar_clima_polos.py --limite 2      # prueba con 2 polos
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from collections import Counter
from datetime import date, datetime

import requests

from _comun import AGENTE, EXTERNOS, RAIZ, ahora_utc, escribir_json, miles, utf8_consola

API = "https://archive-api.open-meteo.com/v1/archive"
INICIO, FIN = "2016-01-01", "2025-12-31"
VARIABLES = [
    "precipitation_sum",
    "precipitation_hours",
    "snowfall_sum",
    "sunshine_duration",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
]

TOPE_MINUTO, TOPE_HORA, TOPE_DIA = 550, 4_800, 9_500  # límites reales: 600, 5 000 y 10 000
DIAS = (date.fromisoformat(FIN) - date.fromisoformat(INICIO)).days + 1
PESO = DIAS / 14 * max(1.0, len(VARIABLES) / 10)  # regla de conteo de Open-Meteo

POLOS = RAIZ / "deliveries" / "week06" / "data" / "processed" / "polos_asignados_v2.csv"
PUNTAJE = RAIZ / "deliveries" / "week06" / "data" / "processed" / "puntaje_polos.csv"
DIR = EXTERNOS / "clima"
PUNTOS = DIR / "puntos_polos.csv"
CRUDO = DIR / "crudo"
CUOTA = DIR / "cuota.json"


# ───────────────────────────── puntos ─────────────────────────────


def leer_csv(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def armar_puntos() -> list[dict]:
    """Centro de cada polo, altitud mediana de sus recursos, ordenado por puntaje."""
    por_polo: dict[str, list[dict]] = {}
    for r in leer_csv(POLOS):
        if r["POLO"] in ("", "-1") or not r["latitud"]:
            continue
        por_polo.setdefault(r["POLO"], []).append(r)
    puntaje = {r["POLO"]: float(r["puntaje"]) for r in leer_csv(PUNTAJE) if r.get("puntaje")}

    puntos = []
    for polo, rs in por_polo.items():
        puntos.append(
            {
                "polo": polo,
                "region": Counter(r["REGIÓN"] for r in rs).most_common(1)[0][0],
                "lat": round(statistics.fmean(float(r["latitud"]) for r in rs), 5),
                "lon": round(statistics.fmean(float(r["longitud"]) for r in rs), 5),
                "altitud_m": round(statistics.median(float(r["ALTITUD"]) for r in rs)),
                "recursos": len(rs),
                "puntaje": puntaje.get(polo, ""),
            }
        )
    # primero lo que más se recomienda; los polos fuera del ranking, al final
    puntos.sort(key=lambda p: (p["puntaje"] == "", -(p["puntaje"] or 0), -p["recursos"]))
    return puntos


def cargar_puntos(regenerar: bool) -> list[dict]:
    if PUNTOS.exists() and not regenerar:
        return leer_csv(PUNTOS)  # misma lista durante toda la descarga
    puntos = armar_puntos()
    DIR.mkdir(parents=True, exist_ok=True)
    with open(PUNTOS, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(puntos[0]), delimiter=";")
        w.writeheader()
        w.writerows(puntos)
    return [{k: str(v) for k, v in p.items()} for p in puntos]


# ───────────────────────────── cuota ─────────────────────────────


def leer_cuota() -> list[list[float]]:
    if not CUOTA.exists():
        return []
    ahora = time.time()
    return [e for e in json.loads(CUOTA.read_text(encoding="utf-8"))["llamadas"] if ahora - e[0] < 86_400]


def anotar(cuota: list[list[float]], peso: float) -> None:
    cuota.append([time.time(), peso])
    escribir_json(CUOTA, {"nota": "timestamp unix y peso de cada llamada, ultimas 24 h", "llamadas": cuota})


def espera_necesaria(cuota: list[list[float]], peso: float) -> float:
    """Segundos hasta que caben `peso` llamadas sin pasar los topes."""
    ahora, espera = time.time(), 0.0
    for ventana, tope in ((60, TOPE_MINUTO), (3_600, TOPE_HORA), (86_400, TOPE_DIA)):
        dentro = sorted(e for e in cuota if ahora - e[0] < ventana)
        usado = sum(p for _, p in dentro)
        for t, p in dentro:  # las más viejas vencen primero
            if usado + peso <= tope:
                break
            usado -= p
            espera = max(espera, t + ventana - ahora)
    return espera


def usado(cuota, ventana) -> float:
    ahora = time.time()
    return sum(p for t, p in cuota if ahora - t < ventana)


# ───────────────────────────── descarga ─────────────────────────────


def ya_bajado(polo: str) -> bool:
    f = CRUDO / f"polo_{polo}.json"
    if not f.exists():
        return False
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return len(d["open_meteo"]["daily"]["time"]) == DIAS
    except (ValueError, KeyError, TypeError):
        return False  # archivo roto: se vuelve a pedir


def pedir(sesion: requests.Session, p: dict) -> tuple[str, object]:
    """('ok', json) · ('cuota', motivo) · ('rechazo', motivo) · ('red', motivo)"""
    params = {
        "latitude": p["lat"],
        "longitude": p["lon"],
        "start_date": INICIO,
        "end_date": FIN,
        "daily": ",".join(VARIABLES),
        "timezone": "America/Lima",
    }
    for intento in range(1, 4):
        try:
            r = sesion.get(API, params=params, timeout=(20, 120))
        except (requests.ConnectionError, requests.Timeout) as e:
            time.sleep(15 * intento)
            motivo = type(e).__name__
            continue
        if r.status_code == 200:
            return "ok", r.json()
        motivo = ""
        try:
            motivo = r.json().get("reason", "")
        except ValueError:
            motivo = r.text[:200]
        if r.status_code == 429:
            return "cuota", motivo
        if r.status_code == 400:
            return "rechazo", motivo
        time.sleep(15 * intento)  # 5xx: el servidor está ocupado
    return "red", motivo


def dormir(segundos: float, por_que: str) -> None:
    if segundos >= 120:  # la pausa del tope por minuto no se anuncia
        fin = datetime.fromtimestamp(time.time() + segundos).strftime("%H:%M")
        print(
            f"  {por_que}: espero {segundos / 60:.0f} min y sigo a las {fin}. "
            "Ctrl+C para cortar; al volver a correrlo retoma.",
            flush=True,
        )
    time.sleep(segundos + 5)


def main() -> None:
    utf8_consola()
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-esperar", action="store_true", help="para al agotar la cuota en vez de esperar")
    ap.add_argument("--limite", type=int, default=0, help="baja solo N polos (prueba)")
    ap.add_argument("--regenerar-puntos", action="store_true")
    a = ap.parse_args()

    puntos = cargar_puntos(a.regenerar_puntos)
    CRUDO.mkdir(parents=True, exist_ok=True)
    pendientes = [p for p in puntos if not ya_bajado(p["polo"])]
    if a.limite:
        pendientes = pendientes[: a.limite]
    hechos = len(puntos) - len([p for p in puntos if not ya_bajado(p["polo"])])
    print(f"{len(puntos)} polos · ya bajados {hechos} · pendientes {len(pendientes)}")
    print(f"Cada polo cuesta {PESO:.0f} llamadas de la cuota (10 años de datos diarios).")
    if not pendientes:
        print("Nada que hacer: el clima de todos los polos ya está.")
        return
    dias_restantes = len(pendientes) * PESO / TOPE_DIA
    print(f"Con la cuota gratuita, esto toma unos {max(dias_restantes, 0.1):.1f} días.\n")

    sesion = requests.Session()
    sesion.headers["User-Agent"] = AGENTE
    cuota = leer_cuota()
    rechazados = []
    rechazos_seguidos = 0

    try:
        i = 0
        while i < len(pendientes):
            p = pendientes[i]
            espera = espera_necesaria(cuota, PESO)
            if espera > 0:
                if a.sin_esperar and espera >= 120:
                    print("\nCuota agotada por ahora. Vuelve a correrlo más tarde: retoma donde quedó.")
                    break
                dormir(espera, "Cuota de Open-Meteo al tope")
                cuota = leer_cuota()
                continue

            estado, dato = pedir(sesion, p)
            if estado == "cuota":
                if a.sin_esperar:
                    print(f"\nOpen-Meteo dice que se acabó la cuota ({dato}). Retoma más tarde.")
                    break
                motivo = str(dato).lower()
                pausa = 3_600 if "daily" in motivo else 65 if "minute" in motivo else 600
                dormir(pausa, f"Open-Meteo pidió pausa ({dato})")
                continue
            if estado != "ok":
                print(f"  polo {p['polo']}: {estado} ({dato}); se salta en esta corrida")
                rechazados.append(p["polo"])
                rechazos_seguidos = rechazos_seguidos + 1 if estado == "rechazo" else 0
                if rechazos_seguidos == 3:
                    # tres puntos distintos rechazados seguidos: el problema es la
                    # petición (una variable, una fecha), no los puntos
                    sys.exit(
                        f"\nOpen-Meteo rechaza la petición misma: {dato}\n"
                        "No tiene sentido seguir: hay que revisar las variables y las fechas que pide este script."
                    )
                i += 1
                continue

            rechazos_seguidos = 0
            anotar(cuota, PESO)  # Open-Meteo la cobró, sirva o no
            serie = dato.get("daily", {})
            llegaron = len(serie.get("time", []))
            if llegaron != DIAS:
                print(f"  polo {p['polo']}: llegaron {llegaron} días, no {DIAS}; se reintenta luego")
                rechazados.append(p["polo"])
                i += 1
                continue

            lluvia = serie.get("precipitation_sum", [])
            nulos = sum(v is None for v in lluvia) / max(len(lluvia), 1)
            escribir_json(
                CRUDO / f"polo_{p['polo']}.json",
                {
                    "polo": p["polo"],
                    "region": p["region"],
                    "punto": {"lat": p["lat"], "lon": p["lon"], "altitud_m": p["altitud_m"], "recursos": p["recursos"]},
                    "pedido": {"api": API, "inicio": INICIO, "fin": FIN, "variables": VARIABLES},
                    "descargado_utc": ahora_utc(),
                    "open_meteo": dato,
                },
            )
            hechos += 1
            aviso = f" · ojo: {nulos:.1%} de días sin dato" if nulos > 0.02 else ""
            print(
                f"[{hechos:>3}/{len(puntos)}] polo {p['polo']:>3} · {p['region'][:14]:<14} · "
                f"{p['altitud_m']:>5} m · cuota hora {miles(usado(cuota, 3_600))}/{miles(TOPE_HORA)} · "
                f"día {miles(usado(cuota, 86_400))}/{miles(TOPE_DIA)}{aviso}",
                flush=True,
            )
            i += 1
    except KeyboardInterrupt:
        print("\nCortado a mano. Lo bajado queda guardado; vuelve a correrlo para seguir.")

    faltan = sum(not ya_bajado(p["polo"]) for p in puntos)
    print(f"\nPolos con clima: {len(puntos) - faltan} de {len(puntos)}.")
    if rechazados:
        print(f"Saltados en esta corrida: {', '.join(rechazados)}. Se reintentan al volver a correrlo.")
    if faltan:
        print("Falta terminar: vuelve a correr el mismo comando.")
    else:
        print("Listo. Lo que sigue: python -m pipeline.clima, que arma el clima de cada polo mes a mes.")


if __name__ == "__main__":
    main()
