"""
DreemGO · Extracción de fichas oficiales de MINCETUR (v3)

Escrita contra la estructura real de la ficha, verificada con diagnostico_ficha.py.
Las versiones anteriores buscaban etiquetas por proximidad de texto y devolvían
basura: "Observaciones" como tipo de ingreso, y la cola de la etiqueta
"Actividades desarrolladas dentro del recurso turístico" como si fuera el valor.

La ficha son TABLAS. Cada una se identifica por la firma de su fila de
encabezado, no por cercanía de palabras. Eso es determinista y auditable.

Tablas que reconoce
-------------------
  cabecera    Código: | Toponimia: | Departamento: | ... | Jerarquía: | Altitud:
  ingreso     Tipo de ingreso | Observaciones
  epoca       Época propicia de visita al recurso | Especificación | Hora ...
  actividades Actividad | Tipo | Observación
  accesos     Recorrido | Tramo | Detalle | ... | Distancia en kms./tiempo
  visitantes  Tipo de Visitante | Cantidad | Fuente de datos | Año | Observación
  servicios   Instalación | Servicio | Tipo de Servicio | Observación

Ojo con la jerarquía: la ficha NO siempre publica un número. Los valores
observados incluyen "No aplica" y "POR JERARQUIZAR". Se guarda el texto crudo
en FICHA_JERARQUIA_TXT y el número solo si existe, en FICHA_JERARQUIA_NUM.
Inventarse un 1 donde la fuente dice "No aplica" fue el error de la v1.

Uso:
    python scraper_mincetur_v3.py --limite 20     # prueba, ~25 s
    python scraper_mincetur_v3.py                 # completo, ~1 h 45 min
"""
import argparse, csv, os, re, sys, time, unicodedata
import requests
from bs4 import BeautifulSoup

ENTRADA = "../data/processed/dreemgo_master_dataset.csv"
SALIDA = "../data/processed/fichas_mincetur.csv"
PAUSA, TIMEOUT = 1.0, 25
AGENTE = ("DreemGO/1.0 (proyecto academico UTEC DS3022; 1 req/s; "
          "contacto oswaldoaqm@gmail.com)")

COLS = [
    "CODIGO", "URL", "HTTP",
    "FICHA_JERARQUIA_TXT", "FICHA_JERARQUIA_NUM", "FICHA_ALTITUD_M", "FICHA_TOPONIMIA",
    "INGRESO_TIPO", "INGRESO_OBS", "TARIFA_SOLES",
    "EPOCA_PROPICIA", "EPOCA_ESPECIFICACION", "HORA_VISITA",
    "N_ACTIVIDADES", "ACTIVIDADES",
    "N_TRAMOS", "ACCESO_KM", "ACCESO_MIN", "ACCESO_MEDIOS", "ACCESO_VIAS",
    "VISITANTES_NAC", "VISITANTES_EXT", "VISITANTES_LOC", "VISITANTES_ANIO",
    "N_SERV_ALOJAMIENTO", "N_SERV_ALIMENTACION",
    "TABLAS_RECONOCIDAS",
]


def nm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower().rstrip(":")


def celdas(tr):
    return [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]


def firma(tab):
    fs = tab.find_all("tr")
    return [nm(c) for c in celdas(fs[0])] if fs else []


def num(txt):
    m = re.search(r"(\d[\d.,]*)", str(txt or "").replace(" ", ""))
    if not m:
        return None
    v = m.group(1).replace(",", "")
    try:
        return float(v)
    except ValueError:
        return None


def km_min(txt):
    """'11.2 Km / 24 Min' · '42 Km / 1 H 25 Min' · '500 Mts / 9 Min'"""
    t = nm(txt)
    km = None
    m = re.search(r"([\d.,]+)\s*(km|kms|mts|m)\b", t)
    if m:
        v = float(m.group(1).replace(",", ""))
        km = v / 1000 if m.group(2) in ("mts", "m") else v
    mins = 0
    h = re.search(r"(\d+)\s*h\b", t)
    mi = re.search(r"(\d+)\s*min", t)
    if h:  mins += int(h.group(1)) * 60
    if mi: mins += int(mi.group(1))
    return km, (mins or None)


def soles(*textos):
    """Mayor importe en soles que aparezca: 'Entrada general: S/5.00' -> 5.0"""
    vals = []
    for t in textos:
        for m in re.finditer(r"s/\.?\s*([\d]+(?:[.,]\d{1,2})?)", nm(t)):
            try: vals.append(float(m.group(1).replace(",", ".")))
            except ValueError: pass
    return max(vals) if vals else None


def extraer(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()
    f = {c: "" for c in COLS}
    vistas = []

    for tab in soup.find_all("table"):
        fs = tab.find_all("tr")
        if not fs:
            continue
        cab = firma(tab)
        filas = [celdas(tr) for tr in fs]

        # ── cabecera: pares etiqueta: valor ──
        if any(c.startswith("codigo") for c in cab):
            vistas.append("cabecera")
            for cs in filas:
                if len(cs) < 2:
                    continue
                et, val = nm(cs[0]), cs[-1].strip()
                if et.startswith("jerarqu"):
                    f["FICHA_JERARQUIA_TXT"] = val
                    m = re.fullmatch(r"\s*([1-4])\s*", val)
                    f["FICHA_JERARQUIA_NUM"] = m.group(1) if m else ""
                elif et.startswith("altitud"):
                    v = num(val); f["FICHA_ALTITUD_M"] = int(v) if v else ""
                elif et.startswith("toponimia"):
                    f["FICHA_TOPONIMIA"] = val[:250]

        # ── tipo de ingreso ──
        elif cab[:2] == ["tipo de ingreso", "observaciones"]:
            vistas.append("ingreso")
            tipos, obs = [], []
            for cs in filas[1:]:
                if cs and cs[0].strip():
                    tipos.append(cs[0].strip())
                    obs.append(cs[1].strip() if len(cs) > 1 else "")
            f["INGRESO_TIPO"] = " | ".join(tipos)[:250]
            f["INGRESO_OBS"] = " | ".join(x for x in obs if x)[:400]
            t = soles(f["INGRESO_TIPO"], f["INGRESO_OBS"])
            f["TARIFA_SOLES"] = t if t is not None else ""

        # ── época propicia ──
        elif cab and cab[0].startswith("epoca propicia"):
            vistas.append("epoca")
            if len(filas) > 1:
                cs = filas[1]
                f["EPOCA_PROPICIA"] = (cs[0] if len(cs) > 0 else "").strip()[:120]
                f["EPOCA_ESPECIFICACION"] = (cs[1] if len(cs) > 1 else "").strip()[:200]
                f["HORA_VISITA"] = (cs[2] if len(cs) > 2 else "").strip()[:120]

        # ── actividades ──
        elif cab[:3] == ["actividad", "tipo", "observacion"]:
            vistas.append("actividades")
            act = []
            for cs in filas[1:]:
                if len(cs) >= 2 and cs[0].strip() and cs[1].strip():
                    act.append(f"{cs[0].strip()}>{cs[1].strip()}")
            f["N_ACTIVIDADES"] = len(act)
            f["ACTIVIDADES"] = " | ".join(act)[:1500]

        # ── accesos ──
        elif any("distancia en kms" in c for c in cab):
            vistas.append("accesos")
            i_d = next(i for i, c in enumerate(cab) if "distancia en kms" in c)
            i_med = next((i for i, c in enumerate(cab) if "medio de transporte" in c), None)
            i_via = next((i for i, c in enumerate(cab) if "tipo de via" in c), None)
            km_t = mn_t = 0.0
            n = 0
            med, via = set(), set()
            for cs in filas[1:]:
                if len(cs) <= i_d:
                    continue
                k, mi = km_min(cs[i_d])
                if k is None and mi is None:
                    continue
                n += 1
                km_t += k or 0
                mn_t += mi or 0
                if i_med is not None and len(cs) > i_med and cs[i_med].strip():
                    med.add(cs[i_med].strip())
                if i_via is not None and len(cs) > i_via and cs[i_via].strip():
                    via.add(cs[i_via].strip())
            if n:
                f["N_TRAMOS"] = n
                f["ACCESO_KM"] = round(km_t, 2)
                f["ACCESO_MIN"] = int(mn_t) if mn_t else ""
                f["ACCESO_MEDIOS"] = " | ".join(sorted(med))[:200]
                f["ACCESO_VIAS"] = " | ".join(sorted(via))[:200]

        # ── visitantes ──
        elif cab and cab[0].startswith("tipo de visitante"):
            vistas.append("visitantes")
            i_c = next((i for i, c in enumerate(cab) if c.startswith("cantidad")), 1)
            i_a = next((i for i, c in enumerate(cab) if c.startswith("ano")), None)
            for cs in filas[1:]:
                if len(cs) <= i_c:
                    continue
                q = num(cs[i_c]); t = nm(cs[0])
                if q is None:
                    continue
                if "nacional" in t:      f["VISITANTES_NAC"] = int(q)
                elif "extranjer" in t:   f["VISITANTES_EXT"] = int(q)
                elif "local" in t or "excursion" in t: f["VISITANTES_LOC"] = int(q)
                if i_a is not None and len(cs) > i_a and not f["VISITANTES_ANIO"]:
                    a = num(cs[i_a])
                    if a and 1990 < a < 2100:
                        f["VISITANTES_ANIO"] = int(a)

        # ── servicios ──
        elif cab and (cab[0].startswith("instalacion") or cab[0].startswith("servicio")):
            vistas.append("servicios")
            i_s = 1 if cab[0].startswith("instalacion") else 0
            alo = ali = 0
            for cs in filas[1:]:
                if len(cs) <= i_s:
                    continue
                t = nm(cs[i_s])
                if "alojamiento" in t or "hospedaje" in t: alo += 1
                if "alimentacion" in t: ali += 1
            f["N_SERV_ALOJAMIENTO"] = (f["N_SERV_ALOJAMIENTO"] or 0) + alo
            f["N_SERV_ALIMENTACION"] = (f["N_SERV_ALIMENTACION"] or 0) + ali

    f["TABLAS_RECONOCIDAS"] = "|".join(sorted(set(vistas)))
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--entrada", default=ENTRADA)
    ap.add_argument("--salida", default=SALIDA)
    a = ap.parse_args()

    with open(a.entrada, encoding="utf-8") as fh:
        base = list(csv.DictReader(fh, delimiter=";"))

    hechos = set()
    if os.path.exists(a.salida):
        with open(a.salida, encoding="utf-8-sig") as fh:
            hechos = {r["CODIGO"] for r in csv.DictReader(fh, delimiter=";")}

    pend = [r for r in base if str(r.get("CODIGO DEL RECURSO", "")) not in hechos]
    if a.limite:
        pend = pend[:a.limite]

    print(f"inventario {len(base)} · ya hechas {len(hechos)} · pendientes {len(pend)}")
    if not pend:
        print("nada que hacer"); return
    print(f"tiempo estimado {len(pend)*PAUSA/60:.0f} min\n")

    CLAVE = ["FICHA_JERARQUIA_TXT", "INGRESO_TIPO", "EPOCA_PROPICIA",
             "ACTIVIDADES", "ACCESO_KM", "VISITANTES_NAC", "TARIFA_SOLES"]
    lleno = {c: 0 for c in CLAVE}
    ok = err = 0

    nuevo = not os.path.exists(a.salida)
    with open(a.salida, "a", encoding="utf-8-sig", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=COLS, delimiter=";")
        if nuevo:
            w.writeheader()

        for i, r in enumerate(pend, 1):
            cod = str(r.get("CODIGO DEL RECURSO", ""))
            url = (r.get("URL") or "").strip()
            f = {c: "" for c in COLS}
            f["CODIGO"], f["URL"] = cod, url

            if "mincetur.gob.pe" not in url:
                f["HTTP"] = "sin_url"
            else:
                try:
                    resp = requests.get(url, headers={"User-Agent": AGENTE}, timeout=TIMEOUT)
                    f["HTTP"] = resp.status_code
                    if resp.status_code == 200:
                        d = extraer(resp.text)
                        d["CODIGO"], d["URL"], d["HTTP"] = cod, url, 200
                        f = d
                        ok += 1
                        for c in CLAVE:
                            if str(f.get(c, "")).strip():
                                lleno[c] += 1
                    else:
                        err += 1
                except Exception as e:
                    f["HTTP"] = type(e).__name__; err += 1
                time.sleep(PAUSA)

            w.writerow(f); fo.flush()

            if i % 25 == 0 or i == len(pend) or a.limite:
                tasa = " ".join(f"{c.split('_')[0][:6].lower()}={lleno[c]*100//max(ok,1):>3}%"
                                for c in CLAVE)
                print(f"[{i}/{len(pend)}] ok={ok} err={err} | {tasa}")

    print(f"\nEscrito {a.salida}")
    print(f"  ok {ok} · errores {err}")
    print("\n  relleno por campo (sobre las fichas con HTTP 200):")
    for c in CLAVE:
        print(f"    {c:<22} {lleno[c]:>5} / {ok}  ({lleno[c]*100//max(ok,1)} %)")
    print("\nSe une al master por CODIGO. El master NO se toca aquí.")


if __name__ == "__main__":
    main()
