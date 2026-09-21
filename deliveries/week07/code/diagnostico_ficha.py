"""
Diagnóstico: vuelca la estructura real de una ficha de MINCETUR.

No extrae nada. Solo muestra cómo está armada la página para poder escribir
selectores que acierten en lugar de adivinar.

Uso:  python diagnostico_ficha.py            # usa 2 fichas del master
      python diagnostico_ficha.py <URL>      # una URL concreta
"""
import csv, re, sys, unicodedata
import requests
from bs4 import BeautifulSoup

ENTRADA = "../data/processed/dreemgo_master_dataset.csv"
AGENTE = "DreemGO/1.0 (proyecto academico UTEC DS3022)"
CLAVES = ["jerarquia", "epoca", "ingreso", "altitud", "actividad", "tipo", "estado", "observa"]


def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip().lower()


def volcar(url):
    print("\n" + "#" * 78)
    print("#", url[:74])
    print("#" * 78)
    r = requests.get(url, headers={"User-Agent": AGENTE}, timeout=25)
    print(f"HTTP {r.status_code} · {len(r.content)} bytes")
    if r.status_code != 200:
        return
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()

    print("\n--- TABLAS: cada fila como  celda0 || celda1 || celda2 ...")
    for ti, tab in enumerate(soup.find_all("table")):
        filas = tab.find_all("tr")
        if not filas:
            continue
        print(f"\n  [tabla {ti}] {len(filas)} filas")
        for fi, tr in enumerate(filas[:25]):
            celdas = [c.get_text(" ", strip=True)[:70] for c in tr.find_all(["td", "th"])]
            if any(c for c in celdas):
                print(f"    {fi:>2}: " + "  ||  ".join(celdas))

    print("\n--- LÍNEAS DE TEXTO QUE CONTIENEN LAS PALABRAS CLAVE (con 2 de contexto)")
    lineas = [l.strip() for l in soup.get_text("\n").split("\n") if l.strip()]
    marcadas = {i for i, l in enumerate(lineas) if any(k in norm(l) for k in CLAVES)}
    ventana = set()
    for i in marcadas:
        ventana.update(range(max(0, i - 1), min(len(lineas), i + 3)))
    ant = -2
    for i in sorted(ventana):
        if i != ant + 1:
            print("    ...")
        marca = ">>" if i in marcadas else "  "
        print(f"  {marca} {i:>4}: {lineas[i][:110]}")
        ant = i

    print(f"\n--- ETIQUETAS <label>, <dt>, <strong>, <b> ({len(soup.find_all(['label','dt','strong','b']))})")
    for e in soup.find_all(["label", "dt", "strong", "b"])[:40]:
        t = e.get_text(" ", strip=True)
        if t:
            print(f"    <{e.name}> {t[:80]}")


def main():
    if len(sys.argv) > 1:
        volcar(sys.argv[1]); return
    with open(ENTRADA, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    # una ficha de sitio natural y una de acontecimiento programado
    urls = []
    for r in filas:
        cat = (r.get("CATEGORÍA") or "")
        u = (r.get("URL") or "").strip()
        if "mincetur.gob.pe" not in u:
            continue
        if cat.startswith("1") and not any("1" == c for c, _ in urls):
            urls.append(("1", u))
        if cat.startswith("5") and not any("5" == c for c, _ in urls):
            urls.append(("5", u))
        if len(urls) == 2:
            break
    for _, u in urls:
        volcar(u)


if __name__ == "__main__":
    main()
