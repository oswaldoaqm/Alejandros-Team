"""
Guarda el HTML crudo de las 6 160 fichas oficiales de MINCETUR, para leerlas
las veces que haga falta sin volver a pedirlas.

Por qué todas y no solo las que faltan
--------------------------------------
fichas_mincetur.csv salió de un scraper que leía cada página una sola vez y no
guardaba nada. Tres cosas obligan a volver a la fuente:
  - Los 31 "errores" no fueron de red: la página respondió, pero el parser se
    cayó leyendo distancias como "1.200.5 km" y guardó el nombre de la
    excepción en la columna HTTP.
  - ACCESO_KM borra las comas (las trata como separador de miles) y suma todas
    las filas de la tabla de accesos sin distinguir el recorrido al que
    pertenecen: 38 fichas pasan de 1 000 km de acceso y una llega a 67 406 km.
  - La ficha trae la descripción del recurso y, en los Acontecimientos
    Programados, cuándo se celebra. Ninguna de las dos se extrajo, y la app
    necesita ambas: la descripción para mostrar cada lugar y la fecha para el
    calendario real de eventos (RF-03).
Con el HTML guardado, el parser se corrige con pruebas sobre páginas reales y
se vuelve a correr en minutos, sin volver a tocar el servidor de MINCETUR.

Orden: primero las 31 fallidas, luego los 749 acontecimientos y al final el
resto, así una corrida parcial ya sirve. Una petición por segundo: unas 2 a
3 horas en total. Si se corta, al volver a correrlo retoma donde quedó.

Salida (fuera de git)
  data/externos/fichas_html/<codigo>.html.gz   la página tal cual llegó, comprimida
  data/externos/fichas_html/indice.csv         una fila por intento: código, motivo,
                                               HTTP, bytes y fecha

Uso
  python pipeline/adquisicion/descargar_fichas_html.py
  python pipeline/adquisicion/descargar_fichas_html.py --limite 10
  python pipeline/adquisicion/descargar_fichas_html.py --codigos 11 22 130
"""
from __future__ import annotations

import argparse
import csv
import gzip
import time
from collections import Counter
from pathlib import Path

import requests

from _comun import AGENTE, EXTERNOS, RAIZ, ahora_utc, miles, utf8_consola

PAUSA, TIMEOUT = 1.0, 25
PROCESADOS = RAIZ / "deliveries" / "week06" / "data" / "processed"
MAESTRO = PROCESADOS / "dreemgo_master_dataset.csv"
FICHAS_V3 = PROCESADOS / "fichas_mincetur.csv"
DIR = EXTERNOS / "fichas_html"
INDICE = DIR / "indice.csv"
PRIORIDAD = {"pedido": 0, "fallida_v3": 0, "acontecimiento": 1, "resto": 2}


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def archivo(codigo: str) -> Path:
    return DIR / f"{codigo}.html.gz"


def objetivo(codigos_pedidos: list[str]) -> list[tuple[str, str, str]]:
    """(código, url, motivo) de las fichas a bajar, en orden de prioridad."""
    maestro = {r["CODIGO DEL RECURSO"].strip(): r for r in leer_csv(MAESTRO)}
    if codigos_pedidos:
        fuera = [c for c in codigos_pedidos if c not in maestro]
        if fuera:
            print(f"No están en el inventario, se ignoran: {', '.join(fuera)}")
        return [(c, maestro[c]["URL"].strip(), "pedido") for c in codigos_pedidos if c in maestro]

    fallidas = {r["CODIGO"].strip() for r in leer_csv(FICHAS_V3) if r["HTTP"].strip() != "200"}
    lista = []
    for cod, r in maestro.items():
        motivo = ("fallida_v3" if cod in fallidas
                  else "acontecimiento" if r["CATEGORÍA"].startswith("5.")
                  else "resto")
        lista.append((cod, r["URL"].strip(), motivo))
    lista.sort(key=lambda x: (PRIORIDAD[x[2]], int(x[0]) if x[0].isdigit() else 0))
    return lista


def pedir(sesion: requests.Session, url: str) -> tuple[str, bytes]:
    """(estado, contenido). Reintenta cortes de red y errores del servidor (5xx)."""
    estado = ""
    for intento in range(1, 4):
        try:
            r = sesion.get(url, timeout=TIMEOUT)
        except (requests.ConnectionError, requests.Timeout) as e:
            estado = type(e).__name__
        else:
            estado = str(r.status_code)
            if r.status_code == 200:
                return estado, r.content
            if r.status_code < 500:
                return estado, b""                 # 404 y similares: reintentar no cambia nada
        time.sleep(5 * intento)
    return estado, b""


def guardar(codigo: str, contenido: bytes) -> None:
    destino = archivo(codigo)
    tmp = destino.with_suffix(".gz.tmp")
    with gzip.open(tmp, "wb") as g:
        g.write(contenido)
    tmp.replace(destino)                            # nunca queda un .gz a medias


def main() -> None:
    utf8_consola()
    ap = argparse.ArgumentParser(description="Guarda el HTML crudo de las fichas de MINCETUR.")
    ap.add_argument("--limite", type=int, default=0, help="baja solo N fichas (prueba)")
    ap.add_argument("--codigos", nargs="*", default=[], help="baja solo estos códigos")
    a = ap.parse_args()

    DIR.mkdir(parents=True, exist_ok=True)
    lista = objetivo(a.codigos)
    pendientes = [x for x in lista if not archivo(x[0]).exists()]
    ya = len(lista) - len(pendientes)
    if a.limite:
        pendientes = pendientes[:a.limite]

    print(f"{miles(len(lista))} fichas objetivo · ya guardadas {miles(ya)} · "
          f"pendientes {miles(len(pendientes))}")
    if not pendientes:
        print("Nada que hacer: todas las fichas ya están guardadas.")
        return
    reparto = Counter(m for _, _, m in pendientes)
    print("  " + " · ".join(f"{m.replace('_', ' ')} {miles(n)}" for m, n in reparto.items()))
    print(f"Una por segundo: unos {len(pendientes) * (PAUSA + 0.4) / 60:.0f} min. "
          "Ctrl+C lo corta sin perder nada.\n")

    sesion = requests.Session()
    sesion.headers["User-Agent"] = AGENTE
    nuevo = not INDICE.exists()
    ok = err = 0
    with open(INDICE, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        if nuevo:
            w.writerow(["codigo", "motivo", "url", "http", "bytes", "descargado_utc"])
        try:
            for i, (cod, url, motivo) in enumerate(pendientes, 1):
                if "mincetur.gob.pe" not in url:
                    estado, contenido = "sin_url", b""
                else:
                    estado, contenido = pedir(sesion, url)
                    if contenido:
                        guardar(cod, contenido)
                    time.sleep(PAUSA)
                ok += bool(contenido)
                err += not contenido
                w.writerow([cod, motivo, url, estado, len(contenido), ahora_utc()])
                fh.flush()
                if i % 100 == 0 or i == len(pendientes):
                    print(f"[{miles(i)}/{miles(len(pendientes))}] guardadas {miles(ok)} · "
                          f"con error {err} · ahora: {motivo.replace('_', ' ')}", flush=True)
        except KeyboardInterrupt:
            print("\nCortado a mano. Lo guardado queda; vuelve a correrlo para seguir.")

    print(f"\nListo: {miles(ok)} fichas guardadas en {DIR}"
          + (f" · {err} con error (se reintentan al volver a correrlo)" if err else ""))


if __name__ == "__main__":
    main()
