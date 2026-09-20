"""
DreemGO · generador del diagrama de arquitectura

Dibuja la arquitectura del producto de datos por capas y escribe un SVG.
Se mantiene como script para que el diagrama se regenere cuando cambie el
pipeline, en vez de quedar como una imagen huérfana que envejece sola.

Uso:  python arquitectura_dreemgo.py [salida.svg]
"""
import sys
from xml.sax.saxutils import escape

SALIDA = sys.argv[1] if len(sys.argv) > 1 else "arquitectura_dreemgo.svg"

W, H = 1720, 1244
FUENTE = "DejaVu Sans, Segoe UI, Helvetica, Arial, sans-serif"

NARANJA = "#C2410C"
TEAL    = "#0D9488"
MORADO  = "#7C3AED"
TINTA   = "#1C1917"
GRIS    = "#57534E"
SUAVE   = "#A8A29E"

X0, X1 = 250, 1672          # columna de contenido
GUTTER = 48                 # x del nombre de la capa

svg = []


def add(s):
    svg.append(s)


def texto(x, y, t, tam=13, color=TINTA, peso="normal", anchor="start", espaciado=0):
    add(f'<text x="{x}" y="{y}" font-family="{FUENTE}" font-size="{tam}" '
        f'fill="{color}" font-weight="{peso}" text-anchor="{anchor}"'
        + (f' letter-spacing="{espaciado}"' if espaciado else "")
        + f'>{escape(t)}</text>')


def banda(y, h, nombre, numero, color):
    add(f'<rect x="{GUTTER}" y="{y}" width="{X1 - GUTTER}" height="{h}" rx="14" '
        f'fill="#FAFAF9" stroke="#E7E5E4" stroke-width="1"/>')
    add(f'<rect x="{GUTTER}" y="{y}" width="5" height="{h}" rx="2.5" fill="{color}"/>')
    texto(GUTTER + 26, y + 34, numero, 26, color, "bold")
    # nombre de la capa, partido en líneas si hace falta
    for i, ln in enumerate(nombre.split("|")):
        texto(GUTTER + 26, y + 62 + i * 19, ln, 14.5, TINTA, "bold")


def caja(x, y, w, h, titulo, lineas, color, punteada=False, etiqueta=None):
    guion = ' stroke-dasharray="6 4"' if punteada else ""
    relleno = "#FFFFFF" if not punteada else "#FCFCFB"
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{relleno}" '
        f'stroke="{color if not punteada else SUAVE}" stroke-width="1.6"{guion}/>')
    add(f'<rect x="{x}" y="{y}" width="{w}" height="4" rx="2" '
        f'fill="{color if not punteada else SUAVE}"/>')
    texto(x + 15, y + 27, titulo, 13.5, TINTA if not punteada else GRIS, "bold")
    for i, ln in enumerate(lineas):
        texto(x + 15, y + 47 + i * 16.5, ln, 11.5, GRIS)
    if etiqueta:
        tw = len(etiqueta) * 6.2 + 14
        add(f'<rect x="{x + w - tw - 12}" y="{y + 14}" width="{tw}" height="19" rx="9.5" '
            f'fill="#F5F5F4" stroke="{SUAVE}" stroke-width="1"/>')
        texto(x + w - tw - 12 + tw / 2, y + 27.5, etiqueta, 10.5, GRIS, "bold", "middle")


def flechas_entrada(cols, y_banda):
    """Una flecha por caja de destino, centrada en ella."""
    for x, w in cols:
        cx = x + w / 2
        add(f'<line x1="{cx}" y1="{y_banda - 24}" x2="{cx}" y2="{y_banda - 3}" '
            f'stroke="{SUAVE}" stroke-width="1.8" marker-end="url(#punta)"/>')


def repartir(n, gap=16):
    ancho = (X1 - X0 - gap * (n - 1)) / n
    return [(X0 + i * (ancho + gap), ancho) for i in range(n)]


# ───────────────────────────── lienzo ─────────────────────────────
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}">')
add('<defs><marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" '
    'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
    f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{SUAVE}"/></marker></defs>')
add(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

texto(GUTTER, 48, "DreemGO · arquitectura del producto de datos", 26, TINTA, "bold")
texto(GUTTER, 74,
      "DS3022 Desarrollo de Producto de Datos · UTEC · estado al 20 de septiembre de 2026",
      13, GRIS)
# leyenda
add(f'<rect x="{X1 - 300}" y="34" width="14" height="14" rx="4" fill="#FFF" '
    f'stroke="{TINTA}" stroke-width="1.6"/>')
texto(X1 - 280, 45, "implementado y verificado", 11.5, GRIS)
add(f'<rect x="{X1 - 300}" y="58" width="14" height="14" rx="4" fill="#FCFCFB" '
    f'stroke="{SUAVE}" stroke-width="1.6" stroke-dasharray="4 3"/>')
texto(X1 - 280, 69, "pendiente · semana indicada", 11.5, GRIS)

# ───────────────────────── 1 · fuentes ─────────────────────────
Y = 108
banda(Y, 152, "Fuentes|de datos", "1", NARANJA)
cols = repartir(5, 14)
caja(cols[0][0], Y + 22, cols[0][1], 112,
     "Inventario Nacional MINCETUR",
     ["CSV de datos abiertos", "6 160 recursos · 25 regiones",
      "licencia ODC-BY", "corte 31-08-2026"], NARANJA)
caja(cols[1][0], Y + 22, cols[1][1], 112,
     "Ficha oficial del recurso",
     ["HTML · una página por recurso", "jerarquía, tarifa, actividades,",
      "accesos, visitantes", "lo que el CSV no publica"], NARANJA)
caja(cols[2][0], Y + 22, cols[2][1], 112,
     "Open-Meteo Archive",
     ["API pública · sin credencial", "climatología mensual 2014-2023",
      "precipitación y temperatura", "10 años por punto"], NARANJA)
caja(cols[3][0], Y + 22, cols[3][1], 112,
     "INEI · datosTurismo",
     ["tablas publicadas", "tarifa de hospedaje por región",
      "gasto promedio del turista", "calibración del modelo de costo"], NARANJA,
     punteada=True, etiqueta="S7")
caja(cols[4][0], Y + 22, cols[4][1], 112,
     "Eventos y comercio local",
     ["749 acontecimientos del", "inventario + registro municipal",
      "hoy: dataset simulado", "lado de la oferta"], NARANJA,
     punteada=True, etiqueta="S7")


# ───────────────────────── 2 · ingesta ─────────────────────────
Y = 284
banda(Y, 136, "Ingesta y|validación", "2", NARANJA)
cols = repartir(3, 18)
flechas_entrada(cols, Y)
caja(cols[0][0], Y + 22, cols[0][1], 96,
     "scraper_mincetur_v3.py",
     ["1 petición/s · agente identificado · reanudable",
      "identifica cada tabla por la firma de su cabecera,",
      "no por proximidad de texto  →  fichas_mincetur.csv"], TEAL)
caja(cols[1][0], Y + 22, cols[1][1], 96,
     "fetch_climate_v2.py",
     ["88 puntos: región × zona climática (antes 24 capitales)",
      "cubre el 99,3 % de los recursos geolocalizables",
      "→ historial_clima_zonas.csv"], TEAL, punteada=True, etiqueta="S7")
caja(cols[2][0], Y + 22, cols[2][1], 96,
     "Carga y saneamiento del CSV",
     ["corrige latitud/longitud invertidas en el origen",
      "normaliza región, categoría y 187 subtipos",
      "deriva ALTITUD y ZONA_CLIMATICA"], TEAL)


# ───────────────────────── 3 · datos ─────────────────────────
Y = 444
banda(Y, 168, "Capa de datos|modelo dimensional", "3", TEAL)
cols = repartir(4, 16)
flechas_entrada(cols, Y)
caja(cols[0][0], Y + 22, cols[0][1], 128,
     "dim_recurso",
     ["6 160 filas × 19 columnas", "clave: CÓDIGO DEL RECURSO",
      "geolocalizables 4 915 (79,8 %)", "sin coordenadas 1 245 (20,2 %)",
      "— folclore y acontecimientos —"], TEAL)
caja(cols[1][0], Y + 22, cols[1][1], 128,
     "hecho_clima",
     ["2 880 filas hoy · 10 560 con los 88 puntos",
      "grano: punto × mes × año",
      "precipitación y temperatura", "base de la estacionalidad",
      "Cusco: 228 mm enero → 8 mm junio"], TEAL)
caja(cols[2][0], Y + 22, cols[2][1], 128,
     "dim_polo",
     ["222 polos turísticos", "salida de TA-01 v2",
      "diámetro, desnivel, región dominante", "puntaje con término de novedad",
      "4 786 recursos encadenables"], TEAL)
caja(cols[3][0], Y + 22, cols[3][1], 128,
     "parametros_costo",
     ["un parámetro por fila", "valor base, mínimo y máximo",
      "origen y estado de calibración", "alimenta la simulación de costo",
      "6 parámetros · ninguno calibrado aún"], TEAL)


# ───────────────────────── 4 · modelos ─────────────────────────
Y = 636
banda(Y, 182, "Modelos|analíticos", "4", MORADO)
cols = repartir(3, 16)
flechas_entrada(cols, Y)
caja(cols[0][0], Y + 22, cols[0][1], 142,
     "TA-01 · Polos con diámetro acotado",
     ["enlace completo jerárquico sobre distancia",
      "de viaje efectiva  d = √(haversine² + (Δalt·0,06)²)",
      "umbral 80 km · tamaño mínimo 5 recursos",
      "el enlace completo acota el diámetro por",
      "construcción: 222 polos, máximo 79 km ≈ 3,2 h",
      "cobertura 77,7 % del inventario"], MORADO)
caja(cols[1][0], Y + 22, cols[1][1], 142,
     "TA-02 · Estacionalidad  ·  TA-03 · Puntaje",
     ["TA-02: matriz mes × zona climática construida",
      "con 10 años de clima, no con una regla inventada",
      "",
      "TA-03: puntaje = (1−λ)·jerarquía + λ·novedad",
      "λ = 0,30 · top-10 con Lima o Cusco: 60 % → 30 %",
      "perdiendo menos del 2 % de jerarquía media"], MORADO)
caja(cols[2][0], Y + 22, cols[2][1], 142,
     "Modelo de costo  ·  TA-04 · Ruta",
     ["costo: transporte + movilidad interna +",
      "alojamiento + alimentación + entradas",
      "Monte Carlo → banda P20–P80, no 'bajo/medio/alto'",
      "caso base S/961 · incertidumbre ±15,8 %",
      "",
      "TA-04 ordenamiento de la ruta (TTDP) — semana 10"], MORADO)


# ───────────────────────── 5 · servicio ─────────────────────────
Y = 842
banda(Y, 136, "Servicio", "5", MORADO)
cols = repartir(2, 20)
flechas_entrada(cols, Y)
caja(cols[0][0], Y + 22, cols[0][1], 96,
     "Motor de itinerarios",
     ["entrada: origen, fechas, días disponibles, presupuesto,",
      "altitud máxima tolerada, intereses",
      "salida: polo elegido → paradas ordenadas → banda de costo"], MORADO)
caja(cols[1][0], Y + 22, cols[1][1], 96,
     "Publicación de eventos  (RF-03)",
     ["el gestor municipal o la DMO publica un evento con",
      "ventana temporal; entra al itinerario solo si las fechas",
      "del viajero caen dentro de la ventana"], MORADO,
     punteada=True, etiqueta="S8")


# ───────────────────────── 6 · consumo ─────────────────────────
Y = 1002
banda(Y, 118, "Consumo", "6", NARANJA)
cols = repartir(2, 20)
flechas_entrada(cols, Y)
caja(cols[0][0], Y + 20, cols[0][1], 80,
     "Viajero",
     ["arma el viaje, ve la banda de costo antes de decidir",
      "y descubre polos fuera del circuito saturado"], NARANJA)
caja(cols[1][0], Y + 20, cols[1][1], 80,
     "Gestor municipal / DMO",
     ["publica eventos y ve qué polos de su jurisdicción",
      "aparecen y con qué puntaje"], NARANJA)

# ───────────────────────── transversales ─────────────────────────
Y = 1146
add(f'<rect x="{GUTTER}" y="{Y}" width="{X1 - GUTTER}" height="62" rx="12" '
    f'fill="#FAFAF9" stroke="#E7E5E4" stroke-width="1"/>')
texto(GUTTER + 22, Y + 25, "TRANSVERSAL", 11, GRIS, "bold", espaciado=1.2)
partes = [
    "Reproducibilidad · semilla 42, rutas relativas, todo el pipeline se regenera en minutos",
    "Versionado · un directorio por entrega en GitHub, commits convencionales",
    "Gobierno del dato · diccionario de datos por tabla, ODC-BY, sin fuentes con TdS restrictivos",
]
xx = GUTTER + 22
for i, p in enumerate(partes):
    texto(xx, Y + 47, p, 11.5, GRIS)
    xx += len(p) * 5.95 + 26
    if i < len(partes) - 1:
        texto(xx - 17, Y + 47, "·", 11.5, SUAVE)

add("</svg>")

with open(SALIDA, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print(f"escrito: {SALIDA}")
