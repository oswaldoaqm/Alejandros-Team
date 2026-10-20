"""
Qué hacer de noche en un viaje (decisión 0018). Nada de esto cambia los días: las paradas, sus
horas y el costo son los mismos con plan de noche o sin él.

- **Qué noches.** Las que se duermen en la base: desde el día en que se llega hasta la víspera
  del día en que se deja. Un viaje de un día no tiene noche.
- **Salir**, con vida_nocturna: bares, pubs, discotecas, karaokes y peñas a no más de unos 25
  minutos a pie de la base (pipeline/noche.py). Cada noche propone hasta tres, de tipos
  distintos si los hay, del más al menos confiable; la noche siguiente, otros tres, mientras
  alcancen.
- **Descanso**, con vida_nocturna: la primera noche en la altura, con la misma regla que el primer
  día tranquilo (``aclimatacion.py``): en una base de 2 500 m o más, si se llega de al menos 1 000 m
  más abajo. El alcohol empeora el mal de altura.
- **Estrellas**, con naturaleza o sin ningún interés: una noche por viaje, desde la base si su
  cielo es oscuro (brillo menor que 2) o, si no, en un observatorio o un planetario a menos de
  45 minutos. Con fecha, la noche con más horas sin luna; sin fecha, la segunda en la base si
  la hay. No se propone en un mes en que no sale despejada ni una de cada cinco noches. Si
  también toca salir, esa noche son las estrellas y las otras, salir.
"""

from __future__ import annotations

from datetime import time, timedelta

from dreemgo import astronomia
from dreemgo.contrato import (
    Cielo,
    CieloDeLaZona,
    Consulta,
    Interes,
    LugarDeEstrellas,
    LugarDeNoche,
    Luna,
    Noche,
    NocheDeLaZona,
)
from dreemgo.motor import aclimatacion, textos
from dreemgo.motor.datos import Datos, Origen
from dreemgo.motor.datos import Polo as PoloDatos

OSCURO, MUY_OSCURO = 2.0, 0.3  # las clases del Servicio de Parques Nacionales de EE. UU.
LUGARES_POR_NOCHE = 3
DESPEJADAS_MINIMO = 0.2
SALIR_PARA_EL_PUNTAJE = 5  # con 5 lugares para salir o más, la zona no pierde puntaje
FRIO_C = 10

NOMBRES = {
    "bar": ("bar", "bares"),
    "pub": ("pub", "pubs"),
    "discoteca": ("discoteca", "discotecas"),
    "karaoke": ("karaoke", "karaokes"),
    "pena": ("peña", "peñas"),
    "musica": ("local con música en vivo", "locales con música en vivo"),
    "comedia": ("local de comedia", "locales de comedia"),
}
ORDEN_DE_TIPOS = ("bar", "pub", "discoteca", "karaoke", "pena", "musica", "comedia")


# ─────────────────────────────── qué toca ───────────────────────────────


def pide_salir(consulta: Consulta) -> bool:
    return Interes.vida_nocturna in consulta.intereses


def pide_estrellas(consulta: Consulta) -> bool:
    return Interes.naturaleza in consulta.intereses or not consulta.intereses


def factor_de_noche(polo: PoloDatos, consulta: Consulta) -> float:
    """Lo que la vida nocturna multiplica en el puntaje de una zona: 1 si hay al menos cinco lugares
    para salir cerca de la base; si no, 0,6 más 0,08 por cada uno. Sin vida_nocturna, 1."""
    if not pide_salir(consulta):
        return 1.0
    n = len(polo.noche.get("lugares", []))
    return 1.0 if n >= SALIR_PARA_EL_PUNTAJE else 0.6 + 0.08 * n


# ─────────────────────────────── los lugares ───────────────────────────────


def url_osm(osm: str | None, lat: float, lon: float) -> str:
    if osm:
        return f"https://www.openstreetmap.org/{osm}"
    return f"https://www.openstreetmap.org/?mlat={lat:.6f}&mlon={lon:.6f}#map=19/{lat:.6f}/{lon:.6f}"


def lugar_de_noche(lugar: dict) -> LugarDeNoche:
    return LugarDeNoche(
        nombre=lugar["nombre"],
        tipo=lugar["tipo"],
        lat=lugar["lat"],
        lon=lugar["lon"],
        minutos_a_pie=lugar["minutos_a_pie"],
        fuente="openstreetmap" if lugar["fuente"] == "osm" else "overture",
        url=url_osm(lugar.get("osm"), lugar["lat"], lugar["lon"]),
        horario=lugar.get("horario"),
    )


def clase(brillo: float) -> str:
    return "muy_oscuro" if brillo < MUY_OSCURO else "oscuro" if brillo < OSCURO else "con_luz"


def lugar_de_estrellas(lugar: dict) -> LugarDeEstrellas:
    return LugarDeEstrellas(
        nombre=lugar["nombre"],
        tipo=lugar["tipo"],
        minutos=lugar["minutos"],
        lat=lugar["lat"],
        lon=lugar["lon"],
        url=url_osm(lugar["osm"], lugar["lat"], lugar["lon"]) if lugar.get("osm") else None,
        brillo=lugar["brillo"],
        clase=clase(lugar["brillo"]),
    )


def la_base(polo: PoloDatos) -> LugarDeEstrellas:
    b = polo.base
    brillo = polo.noche["cielo"]["brillo"]
    return LugarDeEstrellas(
        nombre=b["nombre"], tipo="base", minutos=0, lat=b["lat"], lon=b["lon"], brillo=brillo, clase=clase(brillo)
    )


def cuantos(lugares: list[dict], tipos_max: int | None = None) -> str:
    """«48 bares, 16 pubs, 11 discotecas y 1 peña», en el orden de ``ORDEN_DE_TIPOS``; con
    ``tipos_max``, solo los tipos con más lugares, en ese mismo orden."""
    por_tipo = {t: sum(1 for x in lugares if x["tipo"] == t) for t in ORDEN_DE_TIPOS}
    hay = [t for t in ORDEN_DE_TIPOS if por_tipo[t]]
    if tipos_max is not None:
        mas = set(sorted(hay, key=lambda t: (-por_tipo[t], ORDEN_DE_TIPOS.index(t)))[:tipos_max])
        hay = [t for t in hay if t in mas]
    return textos.lista([f"{por_tipo[t]} {NOMBRES[t][0 if por_tipo[t] == 1 else 1]}" for t in hay])


def para_cada_noche(lugares: list[dict], noches: int) -> list[list[dict]]:
    """Hasta ``LUGARES_POR_NOCHE`` por noche: primero de tipos distintos, después los que siguen, del
    más al menos confiable. Una noche no repite lo de las anteriores mientras queden otros; cuando
    se acaban, se vuelve a empezar."""
    salida, quedan = [], list(range(len(lugares)))
    for _ in range(noches):
        if len(quedan) < min(LUGARES_POR_NOCHE, len(lugares)):
            quedan = list(range(len(lugares)))
        elegidos, tipos = [], set()
        for i in quedan:
            if lugares[i]["tipo"] not in tipos:
                elegidos.append(i)
                tipos.add(lugares[i]["tipo"])
            if len(elegidos) == LUGARES_POR_NOCHE:
                break
        for i in quedan:
            if len(elegidos) == LUGARES_POR_NOCHE:
                break
            if i not in elegidos:
                elegidos.append(i)
        quedan = [i for i in quedan if i not in elegidos]
        salida.append([lugares[i] for i in sorted(elegidos)])
    return salida


# ─────────────────────────────── el cielo ───────────────────────────────


def desde_donde(polo: PoloDatos) -> tuple[LugarDeEstrellas | None, LugarDeEstrellas | None]:
    """(desde dónde se miran las estrellas, el observatorio cercano para mencionarlo): la base si
    su cielo es oscuro; si no, el observatorio o planetario a menos de 45 minutos; si tampoco,
    None."""
    cielo = polo.noche.get("cielo")
    if not cielo:
        return None, None
    astro = lugar_de_estrellas(cielo["astro"]) if cielo.get("astro") else None
    if cielo["brillo"] < OSCURO:
        return la_base(polo), astro
    return astro, None


def _hhmm(t: time | None) -> str | None:
    return None if t is None else f"{t.hour:02d}:{t.minute:02d}"


def _luna(noche: astronomia.Noche) -> Luna:
    return Luna(
        iluminada=noche.luna,
        creciente=noche.creciente,
        sale=_hhmm(noche.luna_sale),
        se_pone=_hhmm(noche.luna_se_pone),
        horas_sin_luna=noche.horas_sin_luna,
    )


def _veces(parte: float) -> str:
    """0,9 → «unas 9 de cada 10»; nunca menos de 1."""
    return f"unas {max(1, round(parte * 10))} de cada 10"


def nota_del_cielo(polo: PoloDatos, cielo: Cielo, mes: int, anio: int) -> str:
    base, desde = polo.base["nombre"], cielo.desde
    frases = []
    if desde.tipo == "base":
        if desde.clase == "muy_oscuro":
            frases.append(f"Desde {base} el cielo es muy oscuro: se ve la Vía Láctea de lado a lado.")
        else:
            frases.append(f"Desde {base} el cielo es oscuro: se ve la Vía Láctea, con algo de luz en el horizonte.")
        if cielo.observatorio is not None:
            o = cielo.observatorio
            frases.append(
                f"Cerca hay un {o.tipo}: {o.nombre}, a {textos.duracion(o.minutos)}. Confirma sus horarios antes de ir."
            )
    else:
        luz = "de la ciudad" if polo.base.get("lugar") == "ciudad" else "del pueblo"
        frases.append(
            f"El cielo de {base} tiene la luz {luz}. {desde.nombre} es un {desde.tipo} a "
            f"{textos.duracion(desde.minutos)}: confirma sus horarios antes de ir."
        )
    if cielo.noches_despejadas is not None:
        frases.append(f"En {textos.mes(mes)} salen despejadas {_veces(cielo.noches_despejadas)} noches.")
    if cielo.luna is not None:
        frases.append(_frase_de_luna(cielo))
    elif cielo.lunas_nuevas:
        dias = textos.lista([f"el {d.day}" for d in cielo.lunas_nuevas])
        frases.append(f"Las noches sin luna son las mejores: en {textos.mes(mes)} de {anio}, la luna nueva es {dias}.")
    if cielo.temp_min_c is not None and cielo.temp_min_c <= FRIO_C:
        frases.append(f"De noche baja a unos {round(cielo.temp_min_c)}{textos.ESPACIO}°C: lleva abrigo.")
    return " ".join(frases)


def _frase_de_luna(cielo: Cielo) -> str:
    luna = cielo.luna
    parte = f"{round(luna.iluminada * 100)}{textos.ESPACIO}%"
    if luna.iluminada < astronomia.LUNA_QUE_NO_ESTORBA:
        return f"Esa noche no hay luna: oscurece del todo a las {cielo.oscurece}."
    if luna.se_pone is not None and luna.sale is None:
        return (
            f"La luna, al {parte}, se pone a las {luna.se_pone}: desde ahí, cielo sin luna hasta que aclara, "
            f"a las {cielo.aclara}."
        )
    if luna.sale is not None and luna.se_pone is None:
        return (
            f"Oscurece del todo a las {cielo.oscurece} y la luna, al {parte}, sale a las {luna.sale}: antes, "
            "cielo sin luna."
        )
    if luna.horas_sin_luna < 1 and luna.iluminada >= 0.9:
        return "Hay luna llena toda la noche: alumbra tanto que la Vía Láctea casi no se ve."
    horas = round(luna.horas_sin_luna)
    sin_luna = "casi ninguna hora" if horas == 0 else f"{'una hora' if horas == 1 else f'unas {horas} horas'}"
    return f"La luna está al {parte}: esa noche hay {sin_luna} de cielo sin luna."


def cielo_de_la_noche(polo: PoloDatos, desde: LugarDeEstrellas, observatorio, consulta, fecha, anio) -> Cielo:
    datos = polo.noche["cielo"]
    despejadas = datos["despejadas"][consulta.mes - 1]
    temp = polo.clima[consulta.mes - 1].get("temp_min_c")
    cielo = Cielo(
        desde=desde,
        observatorio=observatorio,
        noches_despejadas=despejadas,
        fuente_nubes=datos.get("nubes") if despejadas is not None else None,
        aeropuerto=datos.get("aeropuerto") if despejadas is not None else None,
        temp_min_c=temp,
    )
    if fecha is not None:
        n = astronomia.noche(fecha, desde.lat, desde.lon)
        cielo = cielo.model_copy(update={"oscurece": _hhmm(n.oscurece), "aclara": _hhmm(n.aclara), "luna": _luna(n)})
    else:
        cielo = cielo.model_copy(update={"lunas_nuevas": astronomia.lunas_nuevas(anio, consulta.mes)})
    return cielo


# ─────────────────────────────── las noches del viaje ───────────────────────────────


def noches_en_la_base(plan) -> list[int]:
    """Los días cuya noche se duerme en la base."""
    if plan.tipo_viaje == "excursion":
        return []
    return list(range(plan.llegada, plan.salida))


def plan_de_noches(it, consulta: Consulta, origen: Origen, datos: Datos, anio: int) -> dict[int, Noche]:
    """La noche de cada día que la tiene, según lo que pide la consulta."""
    polo = it.polo
    noches = noches_en_la_base(it.plan)
    if not noches or not polo.noche:
        return {}
    fechas = {
        n: None if consulta.fecha_inicio is None else consulta.fecha_inicio + timedelta(days=n - 1) for n in noches
    }
    salida: dict[int, Noche] = {}

    lugares = polo.noche.get("lugares", [])
    salir = pide_salir(consulta) and bool(lugares)
    altura = polo.base["altitud_m"]
    if salir and aclimatacion.pesa(altura, aclimatacion.del_origen(origen, datos)):
        salida[noches[0]] = Noche(
            tipo="descanso",
            titulo="Noche tranquila",
            nota=f"Primera noche a {textos.miles(altura)} m: el cuerpo todavía se está acostumbrando a la altura, y "
            "el alcohol empeora el soroche. Mejor cenar temprano y dejar la salida para otra noche.",
        )

    desde, observatorio = desde_donde(polo) if pide_estrellas(consulta) else (None, None)
    despejadas = polo.noche.get("cielo", {}).get("despejadas", [None] * 12)[consulta.mes - 1]
    if desde is not None and (despejadas is None or despejadas >= DESPEJADAS_MINIMO):
        libres = [n for n in noches if n not in salida] or noches
        if consulta.fecha_inicio is not None:
            horas = {n: astronomia.noche(fechas[n], desde.lat, desde.lon).horas_sin_luna for n in libres}
            elegida = max(libres, key=lambda n: (horas[n], -n))
        else:  # la segunda noche, si está libre: la primera se llega cansado
            elegida = noches[1] if len(noches) > 1 and noches[1] in libres else libres[0]
        cielo = cielo_de_la_noche(polo, desde, observatorio, consulta, fechas[elegida], anio)
        salida[elegida] = Noche(
            tipo="estrellas",
            titulo="Noche de estrellas" if desde.tipo == "base" else f"Estrellas en {desde.nombre}",
            nota=nota_del_cielo(polo, cielo, consulta.mes, anio),
            cielo=cielo,
        )

    if salir:
        pendientes = [n for n in noches if n not in salida]
        resumen = (
            f"A no más de {max(x['minutos_a_pie'] for x in lugares)} minutos a pie de donde duermes hay "
            f"{cuantos(lugares)}."
        )
        for n, elegidos in zip(pendientes, para_cada_noche(lugares, len(pendientes)), strict=True):
            salida[n] = Noche(
                tipo="salir",
                titulo=f"Salir en {polo.base['nombre']}",
                nota=resumen,
                lugares=[lugar_de_noche(x) for x in elegidos],
            )
    return dict(sorted(salida.items()))


def noche_de_la_zona(polo: PoloDatos) -> NocheDeLaZona | None:
    """Lo que la página de una zona muestra de su noche."""
    cielo = polo.noche.get("cielo")
    if not cielo:
        return None
    despejadas = cielo["despejadas"]
    return NocheDeLaZona(
        lugares=[lugar_de_noche(x) for x in polo.noche.get("lugares", [])],
        cielo=CieloDeLaZona(
            desde=la_base(polo),
            mas_oscuro=lugar_de_estrellas(cielo["oscuro"]) if cielo.get("oscuro") else None,
            observatorio=lugar_de_estrellas(cielo["astro"]) if cielo.get("astro") else None,
            noches_despejadas=despejadas,
            fuente_nubes=cielo.get("nubes") if any(x is not None for x in despejadas) else None,
            aeropuerto=cielo.get("aeropuerto"),
        ),
    )
