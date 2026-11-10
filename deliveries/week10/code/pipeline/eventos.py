"""
Calendario de acontecimientos: cuándo se celebra cada fiesta, festival o evento del
inventario, leído de su ficha oficial.

Cada acontecimiento recibe una **regla** (ver dreemgo/calendario.py) y no una fecha,
porque muchas fiestas cambian de día cada año. Se decide en este orden:

1. Si el nombre es de una fiesta móvil (Semana Santa, Corpus Christi, Carnaval, Señor de
   los Temblores…), su regla desde la Pascua. Una fecha escrita en la ficha sería la de
   un solo año. El carnaval se alarga si la ficha dice que llega al miércoles de ceniza
   o al domingo de tentación.
2. Una fecha escrita en la ficha con una palabra que la ata a la celebración ("se
   celebra del 24 al 30 de julio", "su día central es el 3 de mayo", "cada 24 de junio",
   "el segundo domingo de abril"). Si la ficha también dice cuándo empieza y termina, la
   regla es el rango y el día elegido queda como día central.
3. Una fiesta móvil que el texto ata a la celebración ("un día después de la Octava de
   Corpus Christi").
4. El santo o la advocación del nombre, con su fecha del santoral.
5. Un mes con una palabra de celebración ("se celebra en el mes de abril").
6. Si no hay nada de eso, la fecha queda por confirmar.

La precisión sigue el contrato: ``exacta`` si la fuente publica el día, ``aproximada``
si se calcula (santoral, Pascua) o solo se conoce el mes, ``por_confirmar`` si no hay
fecha. Cada regla guarda la frase de la ficha que la respalda.

Al terminar compara las reglas con una muestra al azar cuyas fechas se leyeron a mano
(referencia/eventos_anotados.csv) e imprime cuántas caen en la fiesta.

Uso:  python -m pipeline.eventos     (después de python -m pipeline.maestro)
"""

from __future__ import annotations

import argparse
import calendar
import csv
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from dreemgo.calendario import DIAS, Regla
from pipeline.fichas import Ficha
from pipeline.maestro import EXTERNOS, PROCESADOS, REFERENCIA, leer_fichas
from pipeline.texto import normalizar, sin_tildes

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "setiembre": 9,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
ORDINALES = {"primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4, "ultimo": -1}
DIAS_LARGOS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")

_M = r"(" + "|".join(MESES) + r")"
_D = r"(\d{1,2}|primero)(?:\s*(?:°|º|ro|er))?"
_DE = r"\s+(?:de\s+)?"  # "25 de junio" y también "25 junio"
_DE_ANIO = re.compile(r"\s*,?\s*(?:de|del)\s+(?:año\s+)?(\d{4})")  # "de 1969", "del año 1969"

# Patrones de fecha, del más informativo al menos. Cada uno da (tipo, grupos).
_RANGO = [
    re.compile(rf"\bdel?\s+(?:dia\s+)?{_D}(?:{_DE}{_M})?\s+(?:al|hasta\s+el|a)\s+(?:dia\s+)?{_D}{_DE}{_M}"),
    re.compile(rf"\bdesde\s+el\s+(?:dia\s+)?{_D}(?:{_DE}{_M})?\s+hasta\s+el\s+(?:dia\s+)?{_D}{_DE}{_M}"),
    re.compile(rf"\bentre\s+el\s+(?:dia\s+)?{_D}(?:{_DE}{_M})?\s+(?:y|al)\s+(?:el\s+)?(?:dia\s+)?{_D}{_DE}{_M}"),
    re.compile(rf"\b{_D}(?:{_DE}{_M})?\s+(?:al|y|a)\s+(?:el\s+)?{_D}{_DE}{_M}"),
]
_LISTA = re.compile(rf"\b(\d{{1,2}})(?:\s*,\s*\d{{1,2}})+(?:\s*(?:,|y)\s*(\d{{1,2}}))?{_DE}{_M}")
_UNICA = re.compile(rf"\b{_D}{_DE}{_M}")
_NESIMO = re.compile(
    r"\b(" + "|".join(ORDINALES) + r")\s+(" + "|".join(DIAS_LARGOS) + r")(?:\s+y\s+(" + "|".join(DIAS_LARGOS) + r"))?"
    rf"\s+(?:del\s+mes\s+(?:de\s+)?|de\s+){_M}"
)
# "la tercera semana de marzo", "la segunda quincena de julio": un rango aproximado.
SEMANAS = {"primera": (1, 7), "segunda": (8, 14), "tercera": (15, 21), "cuarta": (22, 28)}
_SEMANA = re.compile(rf"\b(primera|segunda|tercera|cuarta|ultima)\s+(semana|quincena)\s+(?:del\s+mes\s+)?de\s+{_M}")
_MISMO_MES = re.compile(rf"\b(?:desde\s+el|del?)\s+{_D}{_DE}{_M}\s+(?:al|hasta\s+el)\s+{_D}\s+del\s+mismo\s+mes")
_SOLO_MES = re.compile(
    r"\b(?:mes\s+de|durante\s+(?:el\s+mes\s+de\s+)?|en\s+(?:el\s+mes\s+de\s+)?"
    rf"|(?:a\s+)?(?:inicios|fines|finales|mediados|comienzos)\s+de)\s*{_M}\b"
)
_ENTRE_MESES = re.compile(rf"\b(?:entre\s+)?los\s+meses\s+de\s+{_M}\s+(?:y|a|hasta)\s+{_M}\b")

_CELEBRACION = re.compile(
    r"celebr|festej|conmemor|realiz|llev\w*\s+a\s+cabo|desarroll|culmina|finaliza|termina|concluye|clausura"
    r"|cada\s+ano|todos\s+los\s+anos|anualmente|\bcada\b|fiesta|festividad|festival|procesion|homenaje|\bhonor\b"
    r"|aniversario|principal|\bdia\s+del?\b|inicia|empieza|comienza|vispera|programa|jubilar"
)
# Lo que hace de una fecha el día de la fiesta, y lo que la vuelve secundaria.
_CENTRAL = re.compile(r"(?:dias?|fechas?)\s+(?:central|principal)(?:es)?|dia\s+de\s+fiesta")
# "El 15 de julio, víspera del día central" no es el día central.
_ANTES_DEL_CENTRAL = re.compile(r"vispera|antes|previ|hasta|prepar|novena")
_SE_CELEBRA = re.compile(
    r"(?:se\s+celebra|se\s+festeja|se\s+conmemora|celebrarse|cada)\s+(?:el\s+|los\s+dias\s+|el\s+dia\s+)?$"
)
_CADA_ANO = re.compile(r"^\s*(?:de\s+)?(?:cada\s+ano|todos\s+los\s+anos)")
_SECUNDARIA = re.compile(
    r"novena|vispera|preparativo|ensayo|inicia|empieza|comienza|antevispera|octava|prolong|hasta\s+el"
)
_FIN = re.compile(r"culmina|finaliza|termina|concluye|clausura|hasta\s+el|se\s+extiende")
# Una fecha pegada a estas palabras no es la de la fiesta: "calle 3 de mayo", "R. M. del 5 de junio".
_NO_ES_FIESTA = re.compile(
    r"(?:calle|av\.|avenida|\bjr\.?|jiron|pasaje|psje|urb\.?|urbanizacion|plaza|colegio|i\.e\.|institucion"
    r"|resolucion|\br\.\s?[md]\.|oficio|\bof\.|ordenanza|decreto|\bley\b|informe|carta|\b(?:de|con)\s+fecha\b|\bn[°º]"
    r"|fundad|fundacion|creacion|\bcreado|\bcreada|declarad|naci[oó]|muri[oó]|falleci|inaugur)[^.]{0,20}$"
)
ANIO_RECIENTE = 2015  # una fecha con año anterior a este es historia, no la fiesta
ANOTADOS = REFERENCIA / "eventos_anotados.csv"  # muestra al azar con sus fechas leídas a mano


@dataclass(frozen=True, slots=True)
class Fecha:
    regla: str | None  # dreemgo.calendario.Regla
    precision: str  # exacta, aproximada, por_confirmar
    fuente: str | None  # nombre_movil, texto_ficha, texto_movil, santoral, mes_texto
    evidencia: str | None  # la frase de la ficha o el patrón del santoral
    dia_central: str | None = None  # MM-DD o MM-DD..MM-DD, cuando la ficha lo distingue dentro de un rango


@dataclass(frozen=True, slots=True)
class _Candidata:
    regla: str
    puntaje: float
    precision: str
    inicio: int
    fin: int
    seccion: str
    texto: str
    fecha_final: tuple[int, int] | None  # (mes, día) de la última fecha, para extender un día único
    central: bool = False  # la ficha la llama día central o principal


def _dia(texto: str) -> int:
    return 1 if texto == "primero" else int(texto)


def _mmdd(mes: int, dia: int) -> str:
    return f"{mes:02d}-{dia:02d}"


def _valida(mes: int, dia: int) -> bool:
    try:
        date(2024, mes, dia)  # año bisiesto: acepta el 29 de febrero
    except ValueError:
        return False
    return True


def _clave(texto: str) -> str:
    """Minúsculas sin tildes y con la ñ como n: "Señor" y "senor" se comparan igual."""
    return sin_tildes(normalizar(texto)).replace("ñ", "n")


def _cargar_santoral() -> list[tuple[str, str]]:
    with open(REFERENCIA / "santoral.csv", encoding="utf-8", newline="") as f:
        return [(_clave(fila["patron"]), fila["regla"]) for fila in csv.DictReader(f, delimiter=";")]


SANTORAL = _cargar_santoral()
CARNAVAL = dict(SANTORAL)["carnaval"]
# Días con nombre de la temporada de carnaval, contados desde la Pascua. Si la ficha dice
# que la fiesta llega a uno de ellos ("termina el miércoles de ceniza con el entierro del
# ño carnavalón"), la regla del carnaval se alarga hasta ese día.
DIAS_DE_CARNAVAL = {
    "miercoles de ceniza": -46,
    "jueves de carnaval": -45,
    "jueves de tornaboda": -45,
    "sabado de tentacion": -43,
    "domingo de tentacion": -42,
}
_ANTES_DE = re.compile(r"(?:previ[oa]s?|anterior(?:es)?|antes)\s+(?:al|del?)\s+\W?$")


def _alargar_carnaval(regla: str, textos: list[str]) -> tuple[str, str | None]:
    """La regla del carnaval hasta el último día con nombre que la ficha incluye en la
    fiesta, y la frase que lo dice. "Los días previos al miércoles de ceniza" no lo incluye."""
    inicio, _, fin = regla.removeprefix("pascua ").partition("..")
    hasta, frase = int(fin or inicio), None
    for original in textos:
        texto = _clave(original)
        for dia, desfase in DIAS_DE_CARNAVAL.items():
            for m in re.finditer(rf"\b{dia}\b", texto):
                if desfase > hasta and not _ANTES_DE.search(texto[max(0, m.start() - 30) : m.start()]):
                    hasta = desfase
                    ini_frase = max(texto.rfind(". ", 0, m.start()) + 2, m.start() - 120, 0)
                    frase = texto[ini_frase : m.end() + 40].strip()
    return f"pascua {inicio}..{hasta}", frase


def _del_santoral(nombre: str, moviles: bool) -> tuple[str, str] | None:
    """(patrón, regla) del primer patrón del santoral que aparece en el nombre."""
    n = _clave(nombre)
    for patron, regla in SANTORAL:
        if regla.startswith("pascua") == moviles and re.search(rf"\b{re.escape(patron)}", n):
            return patron, regla
    return None


def _movil_en_texto(textos: list[str]) -> tuple[str, str] | None:
    """Una fiesta móvil que el texto ata a la celebración: "un día después de la Octava de
    Corpus Christi", "se celebra en Semana Santa". (patrón, frase) o None."""
    for original in textos:
        texto = _clave(original)
        for patron, regla in SANTORAL:
            if not regla.startswith("pascua"):
                continue
            for m in re.finditer(rf"\b{re.escape(patron)}", texto):
                antes = texto[max(0, m.start() - 80) : m.start()]
                if antes.endswith("mes de "):
                    continue  # "durante el mes de carnavales" dice una temporada, no una fecha
                if re.search(
                    r"(?:domingo|semana|dias|jueves|viernes)\s+(?:posterior(?:es)?|despues)\s+(?:a|al|de)\s+(?:la\s+)?$",
                    antes,
                ):
                    continue  # "el segundo domingo después de Pentecostés": un desfase que no se calcula
                if _CELEBRACION.search(antes) and not _NO_ES_FIESTA.search(antes):
                    inicio = max(texto.rfind(". ", 0, m.start()) + 2, 0)
                    return patron, texto[inicio : m.end() + 40].strip()
    return None


def _central_despues(frase: str) -> bool:
    """Si la frase que sigue a la fecha la llama día central: "(El 28 de agosto) es
    considerado como el día central". No cuenta si en medio la vuelve víspera ("el 27,
    víspera del día central") o la pasa a otro día ("el 1 de julio es la bajada, el 16 es
    el día central")."""
    m = _CENTRAL.search(frase)
    if m is None:
        return False
    entre = frase[: m.start()]
    return not _ANTES_DEL_CENTRAL.search(entre) and not re.search(r"\d", entre)


def _candidatas(seccion: str, original: str, aniversario: bool) -> list[_Candidata]:
    texto = sin_tildes(normalizar(original))
    if len(texto) != len(normalizar(original)):
        original = texto  # sin la misma longitud no se puede recortar la evidencia del original
    else:
        original = normalizar(original)
    ocupado: list[tuple[int, int]] = []
    candidatas: list[_Candidata] = []
    bono_seccion = {"Observaciones": 2.0, "Descripción": 1.0}.get(seccion, 0.0)

    def contexto(ini: int, fin: int) -> tuple[str, str]:
        return texto[max(0, ini - 70) : ini], texto[fin : fin + 30]

    def agregar(ini: int, fin: int, regla: str, tipo: str, precision: str, final=None) -> None:
        if any(a < fin and ini < b for a, b in ocupado):
            return
        antes, despues = contexto(ini, fin)
        anio = _DE_ANIO.match(texto, fin)
        if anio and int(anio.group(1)) < ANIO_RECIENTE and not aniversario:
            return
        if _NO_ES_FIESTA.search(antes) and not aniversario:
            return
        # Lo "cercano" no cruza un punto: "…el día central de la festividad. El 30 de abril…"
        # no hace del 30 de abril el día central.
        cerca_antes = antes[-40:].rsplit(". ", 1)[-1]
        cerca_despues = despues.split(". ", 1)[0]
        claves = {m.group(0) for m in _CELEBRACION.finditer(antes + " " + despues)}
        central = bool(_CENTRAL.search(cerca_antes)) or _central_despues(texto[fin : fin + 60].split(". ", 1)[0])
        if not claves and not central:
            return
        if anio and int(anio.group(1)) >= ANIO_RECIENTE:
            precision = "aproximada"  # la fecha de una edición, no la regla de todos los años
        bono_tipo = {"rango": 2.0, "unica": 0.0, "nesimo": 1.0, "semana": -1.0, "mes": -2.0}[tipo]
        puntaje = (
            min(len(claves), 3)
            + 6 * central
            + 4 * bool(_SE_CELEBRA.search(antes))
            + 3 * bool(_CADA_ANO.match(despues))
            - 2 * bool(_SECUNDARIA.search(cerca_antes + " " + cerca_despues))
            + bono_seccion
            + bono_tipo
            - ini / 5000
        )
        oracion_ini = max(texto.rfind(". ", 0, ini) + 2, ini - 120, 0)
        oracion_fin = min([p for p in (texto.find(". ", fin), fin + 80) if p >= 0])
        evidencia = original[oracion_ini:oracion_fin].strip()
        candidatas.append(_Candidata(regla, puntaje, precision, ini, fin, seccion, evidencia, final, central))
        ocupado.append((ini, fin))

    # La lista antes que el rango: en "el 07, 08 y 09 de noviembre" el rango solo vería "08 y 09".
    for m in _LISTA.finditer(texto):  # "los días 28,29,30 de junio"
        dias = [int(d) for d in re.findall(r"\d{1,2}", texto[m.start() : m.end() - len(m.group(3))])]
        mes = MESES[m.group(3)]
        if all(_valida(mes, d) for d in dias) and dias == sorted(dias) and dias[-1] - dias[0] <= 15:
            agregar(m.start(), m.end(), f"fija {_mmdd(mes, dias[0])}..{_mmdd(mes, dias[-1])}", "rango", "exacta")
    for patron in _RANGO:
        for m in patron.finditer(texto):
            d1, m1, d2, m2 = m.groups()
            mes2 = MESES[m2]
            mes1 = MESES[m1] if m1 else mes2
            d1, d2 = _dia(d1), _dia(d2)
            if not (_valida(mes1, d1) and _valida(mes2, d2)):
                continue
            inicio, fin = date(2024, mes1, d1), date(2024 if mes2 >= mes1 else 2025, mes2, d2)
            if not timedelta(0) < fin - inicio <= timedelta(days=60):
                continue
            agregar(m.start(), m.end(), f"fija {_mmdd(mes1, d1)}..{_mmdd(mes2, d2)}", "rango", "exacta")
    for m in _MISMO_MES.finditer(texto):  # "desde el 19 de mayo al 21 del mismo mes"
        d1, mes, d2 = _dia(m.group(1)), MESES[m.group(2)], _dia(m.group(3))
        if _valida(mes, d1) and _valida(mes, d2) and d1 < d2:
            agregar(m.start(), m.end(), f"fija {_mmdd(mes, d1)}..{_mmdd(mes, d2)}", "rango", "exacta")
    for m in _NESIMO.finditer(texto):
        ordinal, dia, otro_dia, mes = m.groups()
        regla = f"nesimo {MESES[mes]:02d} {ORDINALES[ordinal]} {DIAS[DIAS_LARGOS.index(dia)]}"
        if otro_dia:  # "último sábado y domingo": el día nombrado y los que siguen
            regla += f" {(DIAS_LARGOS.index(otro_dia) - DIAS_LARGOS.index(dia)) % 7}"
        agregar(m.start(), m.end(), regla, "nesimo", "exacta")
    for m in _SEMANA.finditer(texto):
        cual, unidad, mes = m.group(1), m.group(2), MESES[m.group(3)]
        ultimo = calendar.monthrange(2023, mes)[1]
        if unidad == "quincena":
            d1, d2 = (1, 15) if cual == "primera" else (16, ultimo) if cual in ("segunda", "ultima") else (0, 0)
        else:
            d1, d2 = SEMANAS.get(cual, (ultimo - 6, ultimo))
        if d1:
            agregar(m.start(), m.end(), f"fija {_mmdd(mes, d1)}..{_mmdd(mes, d2)}", "semana", "aproximada")
    for m in _UNICA.finditer(texto):
        dia, mes = _dia(m.group(1)), MESES[m.group(2)]
        if _valida(mes, dia):
            agregar(m.start(), m.end(), f"fija {_mmdd(mes, dia)}", "unica", "exacta", (mes, dia))
    for m in _ENTRE_MESES.finditer(texto):  # "entre los meses de mayo y junio"
        agregar(m.start(), m.end(), f"mes {MESES[m.group(1)]:02d}..{MESES[m.group(2)]:02d}", "mes", "aproximada")
    for m in _SOLO_MES.finditer(texto):
        agregar(m.start(), m.end(), f"mes {MESES[m.group(1)]:02d}", "mes", "aproximada")
    return candidatas


def _dentro(regla: str) -> tuple[date, date] | None:
    """(inicio, fin) de una regla fija, en un año bisiesto de referencia."""
    if not regla.startswith("fija"):
        return None
    ini, _, fin = regla.removeprefix("fija ").partition("..")
    (m1, d1), (m2, d2) = map(int, ini.split("-")), map(int, (fin or ini).split("-"))
    return date(2024, m1, d1), date(2024 if (m2, d2) >= (m1, d1) else 2025, m2, d2)


def _con_su_rango(mejor: _Candidata, fechas: list[_Candidata]) -> tuple[str | None, str | None]:
    """Si lo elegido cae dentro de un rango más largo que la ficha también da ("desde el 23
    de enero hasta el 11 de febrero, siendo el día central el 2 de febrero"), la regla es
    el rango y lo elegido queda como día central. Si lo elegido ya es el rango, se busca
    su día central. Un día central puede ser varios días: "07-28..07-29".
    (regla, día central) o (None, None)."""
    propio = _dentro(mejor.regla)
    if propio is None:
        return None, None
    if propio[0] == propio[1] or mejor.central:  # un día, o días que la ficha llama centrales
        # Primero los rangos que la ficha escribe con sus días; "la última semana de julio" después.
        for otra in sorted(fechas, key=lambda c: (c.precision != "exacta", -c.puntaje)):
            rango = _dentro(otra.regla)
            if (
                rango
                and rango != propio
                and rango[0] <= propio[0] <= propio[1] <= rango[1]
                and rango[1] - rango[0] <= timedelta(45)
            ):
                return otra.regla, mejor.regla.removeprefix("fija ")
    if propio[0] == propio[1]:
        return None, None
    centrales = [
        c.regla.removeprefix("fija ")
        for c in fechas
        if c.central and (d := _dentro(c.regla)) and d != propio and propio[0] <= d[0] <= d[1] <= propio[1]
    ]
    return mejor.regla, centrales[0] if centrales else None


def _extender(elegida: _Candidata, todas: list[_Candidata]) -> str:
    """Un día único se vuelve rango si la ficha dice, poco después, cuándo termina."""
    if not elegida.regla.startswith("fija") or ".." in elegida.regla or elegida.fecha_final is None:
        return elegida.regla
    mes, dia = elegida.fecha_final
    inicio = date(2024, mes, dia)
    for otra in todas:
        if otra.seccion != elegida.seccion or not 0 < otra.inicio - elegida.fin <= 200 or otra.fecha_final is None:
            continue
        texto_entre = otra.texto
        if not _FIN.search(texto_entre):
            continue
        m2, d2 = otra.fecha_final
        fin = date(2024 if (m2, d2) >= (mes, dia) else 2025, m2, d2)
        if timedelta(0) < fin - inicio <= timedelta(days=45):
            return f"fija {_mmdd(mes, dia)}..{_mmdd(m2, d2)}"
    return elegida.regla


def leer_fecha(
    nombre: str,
    observaciones: str | None = None,
    descripcion: str | None = None,
    particularidades: str | None = None,
) -> Fecha:
    """La regla de fecha de un acontecimiento, según su nombre y los textos de su ficha."""
    secciones = [
        ("Observaciones", observaciones),
        ("Descripción", descripcion),
        ("Particularidades", particularidades),
    ]
    textos = [t for _, t in secciones if t]
    movil = _del_santoral(nombre, moviles=True)
    if movil:
        if movil[1] == CARNAVAL:
            regla, frase = _alargar_carnaval(CARNAVAL, textos)
            return Fecha(regla, "aproximada", "nombre_movil", frase or movil[0])
        return Fecha(movil[1], "aproximada", "nombre_movil", movil[0])

    aniversario = "aniversario" in sin_tildes(nombre)
    candidatas = [c for s, t in secciones if t for c in _candidatas(s, t, aniversario)]
    fechas = [c for c in candidatas if not c.regla.startswith("mes")]
    santo = _del_santoral(nombre, moviles=False)
    if fechas:
        # El día del santo del nombre, si la ficha también lo escribe, es casi siempre el
        # de la fiesta: "Virgen del Carmen" y "16 de julio" en el texto.
        dia_santo = _dentro(santo[1]) if santo else None

        def puntaje(c: _Candidata) -> float:
            propio = _dentro(c.regla)
            coincide = dia_santo is not None and propio is not None and propio[0] == propio[1] == dia_santo[0]
            return c.puntaje + 5 * coincide

        mejor = max(fechas, key=puntaje)
        regla, central = _con_su_rango(mejor, fechas)
        if regla is None:
            regla = _extender(mejor, candidatas)
        return Fecha(regla, mejor.precision, "texto_ficha", mejor.texto, central)

    movil_texto = _movil_en_texto(textos)
    if movil_texto:
        regla = dict(SANTORAL)[movil_texto[0]]
        if regla == CARNAVAL:
            regla = _alargar_carnaval(regla, textos)[0]
        return Fecha(regla, "aproximada", "texto_movil", movil_texto[1])

    if santo:
        return Fecha(santo[1], "aproximada", "santoral", santo[0])

    meses = [c for c in candidatas if c.regla.startswith("mes")]
    if meses:
        mejor = max(meses, key=lambda c: c.puntaje)
        return Fecha(mejor.regla, "aproximada", "mes_texto", mejor.texto)
    return Fecha(None, "por_confirmar", None, None)


COLUMNAS = [
    "codigo",
    "nombre",
    "tipo",
    "subtipo",
    "region",
    "provincia",
    "distrito",
    "polo",
    "lat",
    "lon",
    "regla",
    "dia_central",
    "precision_fecha",
    "fuente_fecha",
    "evidencia",
    "url_ficha",
]


def construir(maestro: pd.DataFrame, fichas: dict[int, Ficha]) -> pd.DataFrame:
    """Una fila por acontecimiento programado (categoría 5) con su regla de fecha."""
    eventos = maestro[maestro["categoria_num"] == 5].copy()
    sin_fecha = Fecha(None, "por_confirmar", None, None)
    fechas = [
        leer_fecha(f.nombre, f.observaciones, f.descripcion, f.particularidades) if (f := fichas.get(c)) else sin_fecha
        for c in eventos["codigo"]
    ]
    for f in fechas:
        if f.regla:
            Regla(f.regla)  # toda regla escrita tiene que ser válida
    eventos["regla"] = [f.regla for f in fechas]
    eventos["dia_central"] = [f.dia_central for f in fechas]
    eventos["precision_fecha"] = [f.precision for f in fechas]
    eventos["fuente_fecha"] = [f.fuente for f in fechas]
    eventos["evidencia"] = [f.evidencia for f in fechas]
    return eventos[COLUMNAS].reset_index(drop=True)


def evaluar(eventos: pd.DataFrame, anotados: pd.DataFrame) -> pd.DataFrame:
    """Compara cada regla con las fechas de 2026 que se anotaron a mano leyendo su ficha.

    Una fila por acontecimiento anotado. ``en_la_fiesta``: la regla da días en que la ficha
    dice que hay fiesta. ``incluye_central``: entre ellos está el día que la ficha llama
    central. Quedan vacías si no hay regla o si la ficha no nombra un día central.
    """
    reglas = dict(zip(eventos["codigo"], eventos["regla"], strict=True))
    filas = []
    for a in anotados.itertuples(index=False):
        texto = reglas.get(a.codigo)
        regla = Regla(texto) if isinstance(texto, str) else None
        en_la_fiesta = incluye_central = None
        if regla:
            en_la_fiesta = regla.cae_en(date.fromisoformat(a.inicio), date.fromisoformat(a.fin)) is not None
            if isinstance(a.central, str):
                ini, _, fin = a.central.partition("..")
                incluye_central = regla.cae_en(date.fromisoformat(ini), date.fromisoformat(fin or ini)) is not None
        filas.append((a.codigo, a.nombre, texto if regla else None, en_la_fiesta, incluye_central))
    return pd.DataFrame(filas, columns=["codigo", "nombre", "regla", "en_la_fiesta", "incluye_central"])


def resumen_evaluacion(evaluacion: pd.DataFrame) -> str:
    con_fecha = int(evaluacion["regla"].notna().sum())
    centrales = evaluacion["incluye_central"].dropna()
    return (
        f"muestra anotada: {con_fecha} de {len(evaluacion)} con fecha · "
        f"{int(evaluacion['en_la_fiesta'].fillna(False).sum())} de {con_fecha} caen en la fiesta · "
        f"{int(centrales.sum())} de {len(centrales)} incluyen el día central"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Construye el calendario de acontecimientos.")
    ap.add_argument("--maestro", type=Path, default=PROCESADOS / "maestro_v3.csv")
    ap.add_argument("--fichas", type=Path, default=EXTERNOS / "fichas_html")
    ap.add_argument("--salida", type=Path, default=PROCESADOS / "eventos_v3.csv")
    a = ap.parse_args()
    maestro = pd.read_csv(a.maestro, sep=";", encoding="utf-8-sig", dtype={"dias": str})
    codigos = set(maestro.loc[maestro["categoria_num"] == 5, "codigo"])
    eventos = construir(maestro, leer_fichas(a.fichas, codigos))
    eventos.to_csv(a.salida, sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")
    print(f"{len(eventos)} acontecimientos · {eventos['precision_fecha'].value_counts().to_dict()}")
    print(resumen_evaluacion(evaluar(eventos, pd.read_csv(ANOTADOS, sep=";", encoding="utf-8"))))
    print(f"Escrito en {a.salida}")


if __name__ == "__main__":
    main()
