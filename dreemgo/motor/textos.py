"""Cómo se escriben horas, duraciones, montos y listas en las respuestas."""

from __future__ import annotations

# Un espacio que no parte la línea, para que «3 500» y «S/ 80» no queden a caballo entre dos
# renglones. La app escribe igual sus propios números (app/src/formato.ts).
ESPACIO = "\u00a0"

MESES = (
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "setiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def hora(minuto_del_dia: int) -> str:
    """ "07:05" para el minuto 425; después de medianoche vuelve a contar desde 00:00."""
    m = int(minuto_del_dia) % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def duracion(minutos: float) -> str:
    """ "45 min", "2 h", "2 h 40"."""
    m = int(round(minutos))
    if m < 60:
        return f"{m} min"
    h, resto = divmod(m, 60)
    return f"{h} h" if resto == 0 else f"{h} h {resto:02d}"


def miles(n: float) -> str:
    """1250 → "1 250", con un espacio que no parte la línea."""
    return f"{int(round(n)):,}".replace(",", ESPACIO)


def soles(n: float, decimales: int = 0) -> str:
    """1250 → "S/ 1 250"; con dos decimales, 0.33 → "S/ 0,33". Tampoco se parte."""
    monto = f"{n:.{decimales}f}".replace(".", ",") if decimales else miles(n)
    return f"S/{ESPACIO}{monto}"


def lista(cosas: list[str], conjuncion: str = "y") -> str:
    """["a", "b", "c"] → "a, b y c"."""
    cosas = [c for c in cosas if c]
    if len(cosas) <= 1:
        return "".join(cosas)
    return ", ".join(cosas[:-1]) + f" {conjuncion} " + cosas[-1]


def por_medios(medios: list[str]) -> str:
    """["carretera"] → "por carretera"; ["carretera", "tren"] → "por carretera y en tren";
    ["bote"] → "en bote"."""
    return lista(["por carretera" if m == "carretera" else f"en {m}" for m in medios]) or "por carretera"


def fechas(inicio, fin) -> str:
    """ "16 de julio", "del 24 al 30 de julio", "del 28 de diciembre al 6 de enero"."""
    if fin is None or fin == inicio:
        return f"{inicio.day} de {MESES[inicio.month]}"
    if (inicio.year, inicio.month) == (fin.year, fin.month):
        return f"del {inicio.day} al {fin.day} de {MESES[fin.month]}"
    return f"del {inicio.day} de {MESES[inicio.month]} al {fin.day} de {MESES[fin.month]}"


def mes(n: int) -> str:
    return MESES[n]


def meses(ns: list[int]) -> str:
    """[5, 6, 7, 8] → "mayo, junio, julio y agosto"."""
    return lista([MESES[n] for n in ns])


def a_minutos(hhmm: str | None, defecto: int) -> int:
    """ "08:30" → 510; None o un texto raro → ``defecto``."""
    if not hhmm or ":" not in hhmm:
        return defecto
    h, m = hhmm.split(":", 1)
    try:
        return int(h) * 60 + int(m)
    except ValueError:
        return defecto
