"""
Lectura de cifras escritas a mano en las fichas de MINCETUR.

Cada ficha la llena una persona distinta, así que la misma cifra aparece de muchas
formas: "4.4.km/ 7 min", "74 km/ 1 hora con 5 min", "64, 4 Km /1h 47m", "3,399 m",
"3.635 msnm", "1:30 horas", "2 horas y media". Estas funciones son puras: reciben
texto y devuelven números o None, nunca inventan. Cuando una lectura es posible pero
no segura lo dicen (``ambigua``), para que quien las use decida.

Las reglas salen de revisar las 14 456 celdas de distancia y tiempo, las 6 075
altitudes y las tarifas de las 6 160 fichas descargadas el 30 de septiembre de 2026.
Las pruebas en tests/pipeline/test_texto.py fijan los casos reales que motivaron cada
regla.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from math import fsum

# Celdas con las que la ficha dice "sin dato".
VACIOS = frozenset({"", "-", "--", "---", "undefined", "null", "none", "s/d", "n/a"})

# Altitud máxima creíble en el Perú: el Huascarán tiene 6 768 m.
ALTITUD_MAXIMA_M = 6_800.0


def normalizar(texto: str | None) -> str:
    """Espacios colapsados y forma Unicode compuesta; nunca None."""
    if texto is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", texto)).strip()


def limpio(texto: str | None) -> str | None:
    """El texto normalizado, o None si la celda está vacía o dice que no hay dato."""
    t = normalizar(texto)
    return None if t.lower() in VACIOS else t


def sin_tildes(texto: str) -> str:
    """Minúsculas sin tildes ni diéresis, para comparar. La ñ se conserva."""
    t = unicodedata.normalize("NFD", texto.lower().replace("ñ", "\x00"))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").replace("\x00", "ñ")


def decimal(texto: str) -> float:
    """Un número con punto o coma decimal: "64,4" → 64.4."""
    return float(texto.replace(",", "."))


# ── Datos de contacto ────────────────────────────────────────────────────────────────
# Las fichas publican teléfonos y correos de personas en el texto libre ("coordinar al
# Cel. 9xx xxx xxx con la Sra. …"). El producto no los necesita, porque cada parada
# enlaza a su ficha oficial. Se reemplazan al leer, antes de que el texto llegue a un
# artefacto.

CONTACTO_OMITIDO = "[contacto en la ficha oficial]"
_OMITIDO = re.escape(CONTACTO_OMITIDO)

_CORREO = re.compile(r"(?:[\w.+-]+@)+[\w-]+(?:\.[\w-]+)+")
# Nueve cifras que empiezan en 9, juntas o en grupos. Un guion solo lo descarta si lo une a
# otra cifra, como en una resolución: "Rios-9xx…" y "9xx…- Cel." sí son celulares.
_CELULAR = re.compile(r"(?<!\d)(?<!\d-)(?:\+?51[\s-]?)?9\d{2}[\s-]?\d{3}[\s-]?\d{3}(?!\d)(?!-\d)")
_FIJO_CON_CODIGO = re.compile(r"\(0?\d{1,2}\)\s?\d{3}[\s-]?\d{3,4}(?!\d)")
_TELEFONO_CON_PALABRA = re.compile(
    r"(?i)\b((?:tel[eé]f(?:onos?)?|telfs?|tlfs?|tel|fono|celular|cel|whats?app|wsp|rpm|rpc)"
    r"(?:\s+(?:fijo|m[oó]vil|de\s+contacto))?)"
    r"(\.?\s*(?:n[°º.]?\s*)?[:.]?\s*)"
    r"(\+?[\d(][\d\s()–-]{4,}\d)"
)
_DNI = re.compile(r"(?i)\bDNI\s*(?:n[°º.]?\s*)?[:.]?\s*\d{8}\b")

# Un fijo sin la palabra «teléfono» delante ("Informes: 632 1543 / 330 3988") se parece a un
# año o a una resolución. Solo se quita cuando lo delata lo que tiene al lado: otro contacto
# de la misma lista, su anexo, o un aviso como «informes» o «número».
_CODIGO = r"(?:\(0\d{1,2}\)|0\d{1,2})"  # el de la ciudad: 01, (053), 064
_FIJO = rf"(?:{_CODIGO}[\s–-]*)?\d{{3}}[\s-]?\d{{3,4}}"
_ENTRE_CONTACTOS = r"\s*(?:[/|,;–-]|\b(?:o|ó|u|y|y/o)\b(?:\s+al?\b)?)\s*"
_FIJO_TRAS_CONTACTO = re.compile(rf"(?<={_OMITIDO})({_ENTRE_CONTACTOS})(?<!\d){_FIJO}(?!\d)(?![-/]\w)")
_FIJO_ANTES_DE_CONTACTO = re.compile(rf"(?<![\w/-]){_FIJO}(?!\d)({_ENTRE_CONTACTOS})(?={_OMITIDO})")
_FIJO_CON_ANEXO = re.compile(rf"(?<![\w-]){_FIJO}(?=\s*,?\s*\(?(?i:anexos?)\b)")
_FIJO_CON_AVISO = re.compile(
    r"(?i)(\b(?:n[uú]meros?|informes|consultas|reservas|reservaciones|coordinaciones|contactos?|informaci[oó]n"
    rf"|llamar|llamando|comunicarse|contactar|contactarse)\b[^\d\[\n°º]{{0,20}}?)(?<![\w/-]){_FIJO}(?!\d)(?![-/]\w)"
)


# El nombre de quien atiende ese teléfono ("coordinar con el Sr. Nombre Apellido al
# Cel. …") también se quita, pero solo en un texto que trae un contacto: el nombre de una
# investigadora citada en la descripción no es un dato de contacto.
#
# Una persona se reconoce por sus mayúsculas: dos o más palabras seguidas que empiezan con
# mayúscula y no son un cargo, una institución ni un día; o una sola detrás de un
# tratamiento o de un cargo ("el señor Neyra", "el párroco Juan") o pegada al contacto
# ("con Marisol al cel. …"). Ante la duda se quita: aquí es mejor perder el nombre de un
# caserío que dejar el de una persona.
NOMBRE_OMITIDO = "[encargado]"

# Tratamientos: se van con el nombre.
_TRATAMIENTOS = frozenset(
    "sr sra sres srta sro señor señora señores señorita don doña lic ing dr dra prof arq blgo bach tec abog "
    "mg pbro rvdo rev hno hna hnos fray sor mons cmdte gral encargado encargada responsable".split()
)
# Cargos: se quedan, y lo que sigue con mayúscula es el nombre de quien lo ocupa.
_CARGOS = frozenset(
    "propietario propietaria dueño dueña administrador administradora presidente presidenta alcalde "
    "alcaldesa parroco padre sacerdote presbitero hermano hermana hermanos esposos familia familias teniente "
    "gobernador promotor promotora guia economo sacristan guardian vigilante cuidador cuidadora custodio "
    "coordinador coordinadora jefe jefa director directora gerente secretario secretaria tesorero "
    "tesorera fiscal mayordomo comunero comunera tecnico tecnica ingeniero ingeniera profesor profesora "
    "licenciado licenciada biologo biologa arqueologo arqueologa contacto contactos capitan comandante".split()
)
# Lo que suele ir delante del nombre de un lugar: "Catarata X", "Fundo X Y", "Parque Nacional X".
_ANTE_UN_LUGAR = frozenset(
    "catarata cascada cascadas laguna lago rio cerro cerros nevado bosque isla islas playa mirador gruta "
    "caverna fundo hacienda casa bodega templo iglesia capilla santuario museo parque reserva nacional "
    "parroquia caserio anexo sector barrio calle jiron jr avenida av pasaje alto bajo nuevo nueva gran "
    "viejo vieja".split()
)
# Palabras comunes que también son nombres de pila: solas no dicen nada, junto a un apellido sí.
_TAMBIEN_NOMBRES = frozenset("julio abril domingo santos rosa cruz luz sol angel angeles san santa santo".split())
# Y las que también son apellidos: no empiezan un nombre, pero lo continúan ("… Mercado Ramos").
_TAMBIEN_APELLIDOS = frozenset("mercado flora mayor mayo".split())
# Instituciones y sus adjetivos: lo que sigue con mayúscula suele ser un lugar.
_INSTITUCIONES = frozenset(
    """
    comunidad comunidades campesina campesinas nativa nativas municipalidad
    municipal munic municip distrital provincial regional gobierno gerencia subgerencia sub oficina
    area direccion desconcentrada jefatura administracion presidencia directiva comite comision
    asociacion cooperativa empresa sociedad agencia agencias operador club hermandad beneficencia
    ministerio autoridad unidad programa proyecto red sistema servicio servicios junta arzobispado
    obispado catedral convento biblioteca galeria restaurante hotel resort tienda mercado estacion
    puesto garita control sede centro poblado distrito provincia region departamento parcialidad
    asentamiento zona turismo turistico turistica turisticos cultura cultural desarrollo economico
    social humano educacion deporte recreacion ambiente ambiental naturales recursos recurso
    conservacion proteccion flora fauna vigilancia ecoturismo interpretacion registro flujo
    cc cp ccnn sernanp sernamp dircetur mincetur ddc
    """.split()
)
# Lo demás que lleva mayúscula sin ser el nombre de nadie.
_COMUNES = frozenset(
    """
    a al con de del el en la las los no o para por se si sin su sus un una y ya es e u
    previa previo previamente coordinar coordinas coordinacion coordinaciones comunicar comunicarse
    contactar contactarse contactandose solicitar solicitud realizar reservar ingresar enviar llamar
    llamando llevar hacer tener debe deben puede presentarse ponerse considerar atiende cierra
    permiso autorizacion ingreso entrada salida tarifa tarifas precio precios costo pago boleto ticket
    visita visitas visitantes atencion horario horarios turno turnos informes informacion consultas
    reservas reservaciones inscripciones tambien asimismo ademas solo solamente cuando segun
    hasta fuera todos mayor mayores general libre gratuito gratuitas restringido recomendable
    preferentemente observacion taller talleres experiencia recorridos paseos actividades max
    cel celular celulares telefono telefonos telf telef tel tlf fono fijo movil whats whatsapp wsp
    correo correos email mail electronico numero numeros num nro nº anexos dni ruc web pagina
    facebook instagram fb app semana fiesta comunal comunitario
    ninos nino adultos adulto estudiantes escolares universitarios nacionales extranjeros
    extranjero locales grupos persona personas soles usd
    lunes martes miercoles jueves viernes sabado sabados domingos feriado feriados
    enero febrero marzo mayo junio agosto septiembre setiembre octubre noviembre diciembre
    """.split()
)
_NO_ES_NOMBRE = _COMUNES | _INSTITUCIONES | _CARGOS | _TRATAMIENTOS
_PARTICULAS = frozenset("de del la las los y e".split())
_PALABRA = re.compile(r"[^\W\d_]+")
# Lo que puede haber entre un nombre suelto y su contacto: "Doris (cel: …", "Marisol al …",
# y hasta dos palabras más, que suelen ser un apellido en minúsculas.
_HASTA_EL_CONTACTO = re.compile(
    r"(?i)((?:\s+[a-záéíóúñ]+){0,2}?)[\s(\[,;:.-]*(?:(?:al|a|el|la|en|su|n[°ºo]?|nro|n[uú]mero|cel|celular|tel|telf"
    r"|tel[eé]fono|fono|wsp|whatsapp|correo|e-?mail|contacto|m[oó]vil)\b[\s.:°º]*){0,4}"
)
# En un texto largo solo cuenta lo que rodea al contacto; en uno escrito en mayúsculas, donde
# todo parece un nombre, solo lo que está pegado a él.
_TEXTO_CORTO = 400
_CERCA_ANTES, _CERCA_DESPUES = 130, 70
_PEGADO = 30


def _con_mayuscula(palabra: str) -> bool:
    return len(palabra) > 1 and palabra[0].isupper() and (palabra[1:].islower() or palabra.isupper())


def _clase(palabra: str, llana: str, con_punto: bool) -> str:
    """N nombre, S también nombre, A también apellido, L ante un lugar, I inicial, P partícula;
    «M» lleva mayúscula sin ser nada de eso y «-» es cualquier otra palabra."""
    if len(palabra) == 1:
        return "I" if palabra.isupper() and con_punto else "P" if llana in _PARTICULAS else "-"
    if llana in _PARTICULAS:
        return "P"
    if not _con_mayuscula(palabra):
        return "-"
    if llana in _TAMBIEN_NOMBRES:
        return "S"
    if llana in _TAMBIEN_APELLIDOS:
        return "A"
    if llana in _ANTE_UN_LUGAR:
        return "L"
    return "M" if llana in _NO_ES_NOMBRE else "N"


def _quitar_nombres(t: str) -> str:
    """Quita del texto, que ya trae un contacto omitido, los nombres de persona."""
    contactos = [(m.start(), m.end()) for m in re.finditer(_OMITIDO, t)]
    letras = [c for c in t.replace(CONTACTO_OMITIDO, "") if c.isalpha()]
    en_mayusculas = bool(letras) and sum(c.isupper() for c in letras) > 0.6 * len(letras)
    antes, despues = (_PEGADO, _PEGADO) if en_mayusculas else (_CERCA_ANTES, _CERCA_DESPUES)

    def cerca(inicio: int, fin: int) -> bool:
        if len(t) <= _TEXTO_CORTO and not en_mayusculas:
            return True
        return any(c_ini - antes <= fin <= c_ini or c_fin <= inicio <= c_fin + despues for c_ini, c_fin in contactos)

    palabras: list[tuple[int, int, str, str]] = []  # inicio, fin, sin tildes y clase
    for m in _PALABRA.finditer(t):
        if not any(c_ini <= m.start() < c_fin for c_ini, c_fin in contactos):
            llana = sin_tildes(m.group(0))
            palabras.append((m.start(), m.end(), llana, _clase(m.group(0), llana, t[m.end() :][:1] == ".")))

    def seguidas(i: int) -> bool:
        """La palabra i+1 sigue a la i sin más que espacios, el punto de una inicial o un guion."""
        entre = t[palabras[i][1] : palabras[i + 1][0]]
        return entre in (".", "-", ". ", "- ") or (entre != "" and entre.isspace() and "\n" not in entre)

    quitar: list[tuple[int, int]] = []
    i = 0
    while i < len(palabras):
        previa = palabras[i - 1] if i > 0 else None
        pegada = previa is not None and t[previa[1] : palabras[i][0]].strip(" .:,;") == ""
        tratamiento = pegada and previa[2] in _TRATAMIENTOS
        # Tras un tratamiento, cualquier palabra con mayúscula es el nombre: "Sra. Flora …".
        if palabras[i][3] not in ("NS" if not tratamiento else "NSALM"):
            i += 1
            continue
        # La racha: nombres, iniciales y, entre ellos, partículas ("de la") o un apellido que
        # también es otra cosa ("Carlos Calle"). Termina en la última palabra con mayúscula.
        j = ultimo = i
        while j + 1 < len(palabras) and seguidas(j) and palabras[j + 1][3] in "NSALIP":
            j += 1
            if palabras[j][3] != "P":
                ultimo = j
        rango = palabras[i : ultimo + 1]
        inicio, fin = palabras[i][0], palabras[ultimo][1]
        if palabras[ultimo][3] == "I":
            fin += 1  # el punto de una inicial al final: "Nombre A."
        nombres = sum(1 for p in rango if p[3] == "N")
        # Una sigla con una inicial ("APROCTUR C.") no es un nombre con su apellido.
        cuentan = "NSALI" if not t[inicio : palabras[i][1]].isupper() else "NSAL"
        con_mayuscula = sum(1 for p in rango if p[3] in cuentan)
        cargo = pegada and previa[2] in _CARGOS
        lugar = previa is not None and previa[2] in _ANTE_UN_LUGAR and t[previa[1] : inicio].isspace()
        suelto = None  # un nombre solo, pegado al contacto que lo sigue
        if con_mayuscula == 1 and nombres == 1 and not t[inicio:fin].isupper():
            siguiente = min((c_ini for c_ini, _ in contactos if c_ini >= fin), default=None)
            if siguiente is not None and siguiente - fin <= 45:
                suelto = _HASTA_EL_CONTACTO.fullmatch(t[fin:siguiente])
            if previa is not None and (
                previa[3] in "NSALI" or previa[2] in _PARTICULAS | _ANTE_UN_LUGAR | _INSTITUCIONES
            ):
                suelto = None  # "comunidad de Huayhuay - Cel. …", "Isla Juspique al …"
        if tratamiento or cargo:
            es_persona = True
        elif lugar and con_mayuscula <= 2:
            es_persona = False
        else:
            es_persona = (nombres >= 1 and con_mayuscula >= 2) or suelto is not None
        if es_persona and cerca(inicio, fin):
            if suelto is not None and not (tratamiento or cargo):
                fin += len(suelto.group(1))
            quitar.append((previa[0] if tratamiento else inicio, fin))
        i = ultimo + 1

    for inicio, fin in reversed(quitar):
        t = t[:inicio] + NOMBRE_OMITIDO + t[fin:]
    return t


def sin_contactos(texto: str | None) -> str | None:
    """El texto sin correos, celulares, teléfonos, DNI ni el nombre de quien atiende."""
    if texto is None:
        return None
    t = _CORREO.sub(CONTACTO_OMITIDO, texto)
    t = _DNI.sub(CONTACTO_OMITIDO, t)
    t = _TELEFONO_CON_PALABRA.sub(lambda m: m.group(1) + m.group(2) + CONTACTO_OMITIDO, t)
    t = _FIJO_CON_CODIGO.sub(CONTACTO_OMITIDO, t)
    t = _CELULAR.sub(CONTACTO_OMITIDO, t)
    t = _FIJO_CON_ANEXO.sub(CONTACTO_OMITIDO, t)
    t = _FIJO_CON_AVISO.sub(lambda m: m.group(1) + CONTACTO_OMITIDO, t)
    while CONTACTO_OMITIDO in t:  # una lista de teléfonos: cada uno delata al de al lado
        nuevo = _FIJO_TRAS_CONTACTO.sub(lambda m: m.group(1) + CONTACTO_OMITIDO, t)
        nuevo = _FIJO_ANTES_DE_CONTACTO.sub(lambda m: CONTACTO_OMITIDO + m.group(1), nuevo)
        if nuevo == t:
            break
        t = nuevo
    return _quitar_nombres(t) if CONTACTO_OMITIDO in t else t


# ── Altitud ──────────────────────────────────────────────────────────────────────────

_NUMERO_ALTITUD = re.compile(r"\d{1,3}(?:[ ,]\d{3})+(?:\.\d+)?(?!\d)|\d+(?:[.,]\d+)?")
_ENTRE_RANGO = re.compile(r"\s*(?:-|–|—|a|al|hasta|y)\s*")


def _numero_altitud(token: str) -> float | None:
    if re.fullmatch(r"\d{1,3}(?:[ ,]\d{3})+(?:\.\d+)?", token):  # 3,399 · 2 650 · 4,153.21
        return float(re.sub(r"[ ,]", "", token))
    if re.fullmatch(r"\d{1,2}\.\d{3}", token):  # 3.635 msnm: punto de miles
        return float(token.replace(".", ""))
    if re.fullmatch(r"\d+(?:[.,]\d+)?", token):  # 350 · 3.5 · 673,9
        return decimal(token)
    return None


def leer_altitud(texto: str | None) -> tuple[float | None, float | None]:
    """(mínima, máxima) en metros sobre el nivel del mar; iguales si hay un solo valor.

    Acepta "350", "3,399 m", "4008 m.s.n.m.", "3.635 msnm", "2 650 msnm", "150 - 1550"
    y "4310 a 4546". Devuelve (None, None) si no hay número, si hay más de dos, si dos
    números no forman un rango o si alguno cae fuera de 0–6 800 m ("8548773").
    """
    t = limpio(texto)
    if t is None:
        return None, None
    t = re.sub(r"(\d)([.,])\s+(\d{3})(?!\d)", r"\1\2\3", sin_tildes(t))  # "4, 138" → "4,138"
    tokens = list(_NUMERO_ALTITUD.finditer(t))
    if not 1 <= len(tokens) <= 2:
        return None, None
    if len(tokens) == 2 and not _ENTRE_RANGO.fullmatch(t[tokens[0].end() : tokens[1].start()]):
        return None, None
    valores = [_numero_altitud(m.group()) for m in tokens]
    if any(v is None or not 0 <= v <= ALTITUD_MAXIMA_M for v in valores):
        return None, None
    return min(valores), max(valores)  # type: ignore[type-var]


# ── Distancia y tiempo de un tramo de acceso ─────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class DistanciaTiempo:
    """Lo que dice una celda "Distancia en kms./tiempo".

    ``ambigua`` marca las lecturas posibles pero no seguras: horas con dos decimales
    ("1.30 horas" se lee 1 h 30 min, como se usa en las fichas, aunque podría ser 1,3 h)
    y minutos que solo tienen sentido como horas ("85km / 2.30 min").
    """

    km: float | None
    minutos: float | None
    ambigua: bool = False


_PALABRAS_NUMERO = {
    "cuarenta y cinco": "45",
    "un": "1",
    "una": "1",
    "uno": "1",
    "dos": "2",
    "tres": "3",
    "cuatro": "4",
    "cinco": "5",
    "seis": "6",
    "siete": "7",
    "ocho": "8",
    "nueve": "9",
    "diez": "10",
    "doce": "12",
    "quince": "15",
    "veinte": "20",
    "treinta": "30",
    "cuarenta": "40",
    "cincuenta": "50",
}
_PALABRA_ANTES_DE_UNIDAD = re.compile(
    r"(?<![a-z])(" + "|".join(_PALABRAS_NUMERO) + r")\s+(?=(?:horas?|hrs?|minutos?|dias?|kilometros?|km|metros?)\b)"
)
# Unidades con las variantes y erratas que aparecen en las fichas: "kms.", "K.M", "k m",
# "mts", "metos", "hras", "hs", "mint.", "mimutos", "minutoss", "munitos". Los metros
# escritos con letras quedan como "mt"; una "m" suelta puede ser metros o minutos.
_UNIDADES = [
    (re.compile(r"(?<![a-z])(?:kilometros?|kms?|kim|klms?|kmts?|k\.\s?m\.?s?|k\s+m)\.?(?![a-z])"), " km "),
    (re.compile(r"(?<=\d)\s*k\.?(?![a-z])"), " km "),
    (re.compile(r"(?<![a-z])millas?(?![a-z])"), " mn "),
    (re.compile(r"(?<![a-z])(?:metros?|metos|mtrs?|mts?|ms)\.?(?![a-z])"), " mt "),
    (re.compile(r"(?<![a-z])(?:h[oa]?r[a-z]*|hs|h)\.?(?![a-z])"), " h "),
    (re.compile(r"(?<![a-z])m[iu][nm][a-z]*\.?(?![a-z])|'"), " min "),
    (re.compile(r"(?<![a-z])(?:segundos?|segs?)\.?(?![a-z])"), " s "),
    (re.compile(r"(?<![a-z])dias?(?![a-z])"), " d "),
]
_TOKEN = re.compile(
    r"(?P<hh>\d{1,2}):(?P<mm>[0-5]\d)(?:\s*(?P<ur>h|min)(?![a-z]))?"
    r"|(?P<n>\d+(?:[.,]\d+)?)\s*(?P<u>km|mn|mt|min|m|h|d|s)?(?![a-z\d])"
)
_RANGO_TIEMPO = {"d": 4, "h": 3, "min": 2, "s": 1}

# En las rutas por mar o lago la milla es náutica.
KM_POR_MILLA_NAUTICA = 1.852
# Ningún tramo de acceso de las fichas, ni en avioneta, pasa de esta velocidad con una
# lectura sensata; una lectura más rápida viene de una unidad mal escrita.
VELOCIDAD_IMPOSIBLE_KMH = 150.0


def _preparar_tramo(texto: str) -> str:
    t = sin_tildes(texto).replace("½", " 1/2")
    t = _PALABRA_ANTES_DE_UNIDAD.sub(lambda m: _PALABRAS_NUMERO[m.group(1)] + " ", t)
    t = re.sub(r"(?<![a-z])media\s+hora\b", "30 min", t)
    t = re.sub(r"(?<![a-z])(?:un\s+)?cuarto\s+de\s+hora\b", "15 min", t)
    t = re.sub(r"(\d+)\s*(horas?|hrs?|h)\.?\s*(?:y\s+media|1/2)", r"\1.5 \2", t)  # 2 horas y media
    t = re.sub(r"(\d+)\s*(dias?)\s*y\s+medio\b", r"\1.5 \2", t)  # 1 dia y medio
    t = re.sub(r"(\d+)\s+1/2", r"\1.5", t)  # 1 1/2 km
    t = re.sub(r"(?<![\d.,/])1/2", "0.5", t)  # 1/2 km
    t = re.sub(r"(\d)([.,])\s+(\d)", r"\1\2\3", t)  # 64, 4 km
    t = re.sub(r"(\d)[.,](?=\s*[a-z'])", r"\1 ", t)  # 4.4.km · 74.km
    t = re.sub(r"(\d)o(?=\s*(?:k|m|h))", r"\g<1>0", t)  # "1o min": una o por un cero
    for patron, unidad in _UNIDADES:
        t = patron.sub(unidad, t)
    return t


def _minutos_de_horas(valor: str) -> tuple[float, bool]:
    """Horas escritas con decimales. Dos decimales hasta 59 se leen como h.mm (dudosa)."""
    entero, _, fraccion = valor.replace(",", ".").partition(".")
    if len(fraccion) == 2 and fraccion != "00" and int(fraccion) <= 59:
        return int(entero) * 60 + int(fraccion), True
    return decimal(valor) * 60, False


def _metros(valor: str) -> float:
    """Metros; "1,200 m" y "0.820 mts" llevan separador de miles."""
    if re.fullmatch(r"\d{1,3}[.,]\d{3}", valor):
        return float(re.sub(r"[.,]", "", valor))
    return decimal(valor)


class _Lector:
    """Recorre los números con unidad de una celda y arma distancia y tiempo."""

    def __init__(self) -> None:
        self.km: float | None = None
        self.minutos = 0.0
        self.hay_tiempo = False
        self.tiempo_cerrado = False
        self.ultimo_rango = 99  # el tiempo se suma mientras las unidades bajen
        self.anterior: str | None = None
        self.ambigua = False
        # Lecturas literales que podrían ser horas mal rotuladas: (literal, como horas).
        self.revisables: list[tuple[float, float]] = []

    def distancia(self, unidad: str, valor: str) -> None:
        if unidad in ("mt", "m") and self.anterior == "km" and not self.hay_tiempo:
            if self.km is not None:
                self.km += _metros(valor) / 1000  # "1 km 500 metros"
            self.anterior = "mt"
            return
        if self.km is None:
            if unidad == "km":
                self.km = decimal(valor)
            elif unidad == "mn":
                self.km = decimal(valor) * KM_POR_MILLA_NAUTICA
            else:
                self.km = _metros(valor) / 1000
        self.anterior = unidad
        if self.hay_tiempo:
            self.tiempo_cerrado = True  # "3:00 horas 8 km": lo que siga ya no es este tiempo

    def tiempo(self, unidad: str, minutos: float, revisable: tuple[float, float] | None = None) -> None:
        rango = _RANGO_TIEMPO[unidad]
        if self.tiempo_cerrado or rango >= self.ultimo_rango:
            self.tiempo_cerrado = True  # "2 dias de ida y dos dias de retorno"
            return
        self.minutos += minutos
        if revisable is not None:
            self.revisables.append(revisable)
        self.hay_tiempo, self.ultimo_rango, self.anterior = True, rango, unidad

    def resultado(self) -> DistanciaTiempo:
        if not self.hay_tiempo:
            return DistanciaTiempo(self.km, None)
        minutos = self.minutos
        if self.revisables and self.km and minutos and self.km / (minutos / 60) > VELOCIDAD_IMPOSIBLE_KMH:
            # "85km / 2.30 min", "6.19 km/0.12 min", "1.0 km / 30:00 minutos" al revés: la
            # lectura literal es imposible, así que se usa la otra y queda marcada.
            minutos += fsum(horas - literal for literal, horas in self.revisables)
            self.ambigua = True
        return DistanciaTiempo(self.km, round(minutos, 2), self.ambigua)


def leer_distancia_tiempo(texto: str | None) -> DistanciaTiempo:
    """Kilómetros y minutos de una celda de tramo.

    - La distancia es el primer número con unidad de longitud. Unos metros justo después
      de los kilómetros se suman ("1 km 500 metros").
    - El tiempo suma unidades que bajan en orden (días, horas, minutos, segundos) y se
      detiene si una se repite, como en "2 dias de ida y dos dias de retorno".
    - Una "m" suelta es de minutos si sigue a unas horas ("1h 47m") o si la distancia
      ya se leyó ("200 m / 20 m"); si no, es de metros. Tras los kilómetros, "500 m" con
      tres cifras son metros y "55 m" con dos son minutos ("56 K. 55 m.").
    - "h:mm" son horas y minutos. Con "minutos" detrás ("30:00 minutos") se lee como
      minutos y segundos, salvo que eso dé una velocidad imposible ("43 km / 1:10 min").
    - Un número sin unidad no se adivina.
    """
    t = limpio(texto)
    if t is None:
        return DistanciaTiempo(None, None)
    lector = _Lector()
    for m in _TOKEN.finditer(_preparar_tramo(t)):
        if m.group("hh") is not None:
            hh, mm = int(m.group("hh")), int(m.group("mm"))
            if m.group("ur") == "min":
                lector.tiempo("min", hh + mm / 60, revisable=(hh + mm / 60, hh * 60 + mm))
            else:
                lector.tiempo("h", hh * 60 + mm)
                lector.ultimo_rango = _RANGO_TIEMPO["min"]
            continue
        valor, unidad = m.group("n"), m.group("u")
        if unidad == "m":
            if lector.anterior == "h":
                unidad = "min"
            elif lector.anterior == "km" and not lector.hay_tiempo:
                unidad = "mt" if re.fullmatch(r"\d{3}", valor) else "min"
            elif lector.km is not None:
                unidad = "min"
            else:
                unidad = "mt"
        if unidad in ("km", "mt", "mn"):
            lector.distancia(unidad, valor)
        elif unidad == "h":
            minutos, dudosa = _minutos_de_horas(valor)
            lector.ambigua = lector.ambigua or dudosa
            lector.tiempo("h", minutos)
        elif unidad == "min":
            revisable = None
            if re.search(r"[.,]", valor):  # "2.30 min": ¿minutos u horas?
                revisable = (decimal(valor), _minutos_de_horas(valor)[0])
            lector.tiempo("min", decimal(valor), revisable)
        elif unidad == "d":
            lector.tiempo("d", decimal(valor) * 24 * 60)
        elif unidad == "s":
            lector.tiempo("s", decimal(valor) / 60)
    return lector.resultado()


# ── Horario ──────────────────────────────────────────────────────────────────────────

_HORA_12 = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\b\.?")


def leer_horario(texto: str | None) -> tuple[str | None, str | None]:
    """(abre, cierra) en 24 h desde "10:00 a.m. - 04:00 p.m.".

    Las 12 a.m. son medianoche: al abrir es 00:00 y al cerrar, 24:00. Devuelve
    (None, None) si no hay exactamente dos horas con a.m. o p.m.
    """
    t = limpio(texto)
    if t is None:
        return None, None
    horas = _HORA_12.findall(sin_tildes(t))
    if len(horas) != 2:
        return None, None
    convertidas = []
    for h, m, ap in horas:
        hora, minuto = int(h), int(m or 0)
        if not (1 <= hora <= 12 and 0 <= minuto <= 59):
            return None, None
        convertidas.append((hora % 12 + (12 if ap == "p" else 0), minuto))
    (h1, m1), (h2, m2) = convertidas
    if (h2, m2) == (0, 0):
        h2 = 24
    return f"{h1:02d}:{m1:02d}", f"{h2:02d}:{m2:02d}"


# ── Días de atención ─────────────────────────────────────────────────────────────────

DIAS_SEMANA = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
_DIA = r"(lunes|martes|miercoles|jueves|viernes|sabado|domingo)s?"
_RANGO_DIAS = re.compile(rf"{_DIA}\s*(?:a|al|hasta|-|–)\s*{_DIA}")
_EXCEPCION = re.compile(
    rf"(?:excepto|salvo|menos|cerrad[oa]s?|no\s+(?:se\s+)?(?:atiende|abre|hay\s+atencion))\s+(?:(?:los|el|dias?)\s+)*{_DIA}"
    rf"|{_DIA}\s*(?:[:,-]\s*)?(?:cerrad[oa]|no\s+(?:se\s+)?(?:atiende|abre|hay\s+atencion))"
)
_TODOS = re.compile(r"todos\s+los\s+dias|diariamente|\bdiario\b|toda\s+la\s+semana")


def leer_dias(texto: str | None) -> tuple[int, ...] | None:
    """Días de atención (0 = lunes … 6 = domingo), o None si el texto no los dice.

    Entiende rangos ("De martes a domingo"), listas ("sábados y domingos"),
    "todos los días" y excepciones ("excepto lunes", "lunes cerrado").
    """
    t = limpio(texto)
    if t is None:
        return None
    t = sin_tildes(t)
    dias: set[int] = set()
    if _TODOS.search(t):
        dias.update(range(7))
    quitados: set[int] = set()
    for m in _EXCEPCION.finditer(t):
        nombre = m.group(1) or m.group(2)
        quitados.add(DIAS_SEMANA.index(nombre))
    resto = _EXCEPCION.sub(" ", t)
    for m in _RANGO_DIAS.finditer(resto):
        inicio, fin = DIAS_SEMANA.index(m.group(1)), DIAS_SEMANA.index(m.group(2))
        dias.update((inicio + i) % 7 for i in range((fin - inicio) % 7 + 1))
    for m in re.finditer(_DIA, _RANGO_DIAS.sub(" ", resto)):
        dias.add(DIAS_SEMANA.index(m.group(1)))
    if not dias and not quitados:
        return None
    if not dias:
        dias.update(range(7))  # "cerrado los lunes": se atiende el resto de la semana
    return tuple(sorted(dias - quitados))


# ── Tarifa ───────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Tarifa:
    """La entrada de un adulto peruano, en soles, y cómo se eligió entre los montos.

    ``regla`` es una de: adulto_nacional, adulto, nacional, unico, maximo,
    adulto_sin_moneda, o None si no se pudo decidir. ``combinada`` marca las entradas
    que forman parte de un boleto para varios lugares (el Boleto Turístico del Cusco, un
    circuito): se paga una vez por viaje, no en cada parada.
    """

    soles: float | None
    regla: str | None
    combinada: bool = False


_NUMERO_MONTO = r"(\d{1,4}(?:[.,]\d{1,2})?)"
_SOLES = r"(?:nuevos\s+)?(?:soles?|solos)\b"
_MONTO = re.compile(
    rf"s\s?\.?\s?/\s?\.?\s*{_NUMERO_MONTO}(?:\s*{_SOLES})?"  # S/ 11.00 · S/.5 · S./ 10.00
    rf"|{_NUMERO_MONTO}\s*{_SOLES}"  # 5 nuevos soles · 1 sol
    rf"|{_NUMERO_MONTO}\s*s\s?/\.?(?!\w)"  # 2.00 s/.
    r"|(?<=\s)/\s?(\d{1,4}[.,]\d{2})(?!\d)"  # "adulto /12.00"
)
_NOMBRES_CON_NACIONAL = re.compile(
    r"\b(?:parque|reserva|santuario|museo|bosque|coto|refugio|patrimonio|monumento|biblioteca|teatro|universidad)"
    r"\s+(?:historico\s+)?nacional\w*"
)
_ETIQUETAS = {
    "extranjero": re.compile(r"extranjer|no\s+residente|internacional|\bext\b"),
    # "Foráneo" en las fichas es quien no es del lugar, peruano o no.
    "nacional": re.compile(r"nacional|peruan|\bnac\b|foraneo"),
    "local": re.compile(r"\blocal(?:es)?\b|residente|cusquen|poblador|comuner|region\s+\w+"),
    # "Entrada", "tarifa", "costo" o "boleto" solos no dicen para quién es el monto.
    "adulto": re.compile(r"adult|general|publico|persona|visitante|turista"),
    "reducido": re.compile(
        r"ni[nñ][oa]|menor|escolar|estudiant|universitari|jubilad|mayor(?:es)?\s+de|tercera\s+edad|docente|profesor"
        r"|conadis|discapacidad|militar|reducid|especial|infant|bebe|joven|colegio|adolescente"
    ),
    "vehiculo": re.compile(r"vehicul|carro|\bauto|\bmoto|estacionamiento|parqueo|cochera|unidad\s+movil"),
    "servicio": re.compile(
        r"gu[ii]a|grupo|delegaci|camping|campament|carpa|pernoct|pernot|bote|paseo|alquiler|foto|filmaci|camara|\btour"
        r"|almuerzo|hospedaje|alojamiento|noche|caballo|kayak|lancha|dron|cuatrimoto|canopy|zip|equipo|chaleco"
        r"|ruta\s+larga|donaci|colaboraci|orientador|hidromasaje|sauna"
    ),
}
_COMBINADO = re.compile(
    r"boleto\s+turistico|\bbtg\b|\bbtci\b|boleto\s+integral|boleto\s+parcial|circuito|incluid[oa]\s+en"
)


def _etiquetas(contexto: str) -> set[str]:
    c = re.sub(r"adultos?\s+mayor(?:es)?", "jubilado", _NOMBRES_CON_NACIONAL.sub(" ", contexto))
    return {nombre for nombre, patron in _ETIQUETAS.items() if patron.search(c)}


def _hasta_separador(texto: str) -> str:
    """Lo que describe al monto anterior cuando la ficha escribe el monto primero."""
    return re.split(r"[,;/]|\s-\s|\sy\s", texto, maxsplit=1)[0]


_CERCA = 25  # caracteres: una etiqueta más lejos no se considera pegada al monto


def _distancia_antes(contexto: str) -> int | None:
    """Caracteres entre la última etiqueta (hasta el fin de su palabra) y el monto."""
    if re.search(r"[:=]\s*$", contexto):
        return 0  # "Adultos: S/ 5.00": los dos puntos atan la etiqueta al monto
    fines = [
        re.match(r"\w*", contexto[m.end() :]).end() + m.end() for p in _ETIQUETAS.values() for m in p.finditer(contexto)
    ]
    return len(contexto) - max(fines) if fines else None


def _distancia_despues(contexto: str) -> int | None:
    inicios = [m.start() for patron in _ETIQUETAS.values() for m in patron.finditer(_hasta_separador(contexto))]
    return min(inicios) if inicios else None


def _monto_primero(antes: list[str], despues: list[str]) -> bool:
    """¿La ficha escribe "S/ 65.00 extranjeros" (etiqueta después) o "Adultos: S/ 11.00"?

    Cada monto vota por el lado donde su etiqueta está más pegada. Si empatan, decide
    si el primer monto tiene alguna etiqueta delante.
    """
    votos = 0
    for a, d in zip(antes, despues, strict=True):
        da, dd = _distancia_antes(a), _distancia_despues(d)
        da = da if da is not None and da <= _CERCA else None
        dd = dd if dd is not None and dd <= _CERCA else None
        if dd is not None and (da is None or dd < da):
            votos += 1
        elif da is not None and (dd is None or da < dd):
            votos -= 1
    if votos:
        return votos > 0
    return not _etiquetas(antes[0]) and bool(_etiquetas(_hasta_separador(despues[0])))


def leer_tarifa(texto: str | None) -> Tarifa:
    """La tarifa de un adulto peruano a partir del texto libre de "Tipo de ingreso".

    Cada monto en soles toma las palabras que lo rodean: las de antes ("Adultos:
    S/ 11.00") o, si la ficha escribe el monto primero ("S/ 65.00 extranjeros y S/ 30.00
    nacionales"), las de después hasta la siguiente coma o "y" (ver ``_monto_primero``).
    Se elige, en este orden:

    1. ``adulto_nacional``: el primer monto de adulto nacional.
    2. ``adulto``: el primer monto de adulto que no sea de extranjero, local, vehículo,
       servicio (guía, bote, hospedaje) ni tarifa reducida.
    3. ``nacional``: el primer monto nacional que no sea reducido, vehículo ni servicio.
    4. ``unico``: el único monto, si no es de extranjero, local, vehículo ni servicio.
    5. Entre los montos que no son de extranjero, local, vehículo ni servicio: el mayor
       (``maximo``) si alguno es una tarifa reducida, porque la de adulto es la más alta;
       si no, el menor (``minimo``), porque son opciones como poza o piscina.
    6. ``unico_servicio``: el único monto, aunque sea de un servicio como la visita
       guiada, porque la ficha dice que el ingreso es con boleto.
    7. ``adulto_sin_moneda``: si no hay montos en soles, "Adultos: 10".

    Los montos en dólares no cuentan. Un monto por vehículo no es la entrada de una
    persona ("por unidad vehicular S/. 5.00, a pie no paga").
    """
    t = limpio(texto)
    if t is None:
        return Tarifa(None, None)
    t = sin_tildes(t)
    combinada = bool(_COMBINADO.search(t))
    montos = [(m.start(), m.end(), decimal(next(g for g in m.groups() if g is not None))) for m in _MONTO.finditer(t)]
    if not montos:
        m = re.search(r"adult\w*\s*:?\s*(\d{1,3}(?:[.,]\d{1,2})?)(?!\s*(?:\d|anos|años))", t)
        return Tarifa(decimal(m.group(1)), "adulto_sin_moneda", combinada) if m else Tarifa(None, None, combinada)
    antes = [t[(montos[i - 1][1] if i else 0) : ini] for i, (ini, _, _) in enumerate(montos)]
    despues = [t[fin : (montos[i + 1][0] if i + 1 < len(montos) else len(t))] for i, (_, fin, _) in enumerate(montos)]
    monto_primero = _monto_primero(antes, despues)
    etiquetas = [_etiquetas(_hasta_separador(despues[i]) if monto_primero else antes[i]) for i in range(len(montos))]

    def es(i: int, *nombres: str) -> bool:
        return all(n in etiquetas[i] for n in nombres)

    def extranjero(i: int) -> bool:
        return es(i, "extranjero") and not es(i, "nacional")

    def local(i: int) -> bool:
        return es(i, "local") and not es(i, "nacional")

    def aparte(i: int) -> bool:
        return es(i, "servicio") or es(i, "vehiculo")

    reglas = [
        (
            "adulto_nacional",
            lambda i: es(i, "adulto", "nacional") and not (aparte(i) or es(i, "reducido") or es(i, "local")),
        ),
        ("adulto", lambda i: es(i, "adulto") and not (extranjero(i) or local(i) or aparte(i) or es(i, "reducido"))),
        ("nacional", lambda i: es(i, "nacional") and not (es(i, "reducido") or aparte(i))),
    ]
    for nombre, cumple in reglas:
        for i, (_, _, valor) in enumerate(montos):
            if cumple(i):
                return Tarifa(valor, nombre, combinada)
    validos = [i for i in range(len(montos)) if not (extranjero(i) or local(i) or aparte(i))]
    if len(montos) == 1 and validos:
        return Tarifa(montos[0][2], "unico", combinada)
    if validos:
        hay_reducida = any(es(i, "reducido") and not es(i, "adulto") for i in validos)
        valores = [montos[i][2] for i in validos]
        return Tarifa(max(valores), "maximo", combinada) if hay_reducida else Tarifa(min(valores), "minimo", combinada)
    if len(montos) == 1 and es(0, "servicio") and not (es(0, "vehiculo") or extranjero(0)):
        return Tarifa(montos[0][2], "unico_servicio", combinada)
    return Tarifa(None, None, combinada)
