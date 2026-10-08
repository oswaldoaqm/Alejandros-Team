"""
El motor: de una consulta a hasta tres viajes (docs/CONTRATO.md).

1. Por cada polo, qué se puede visitar: las paradas a las que se llega por carretera desde
   la base, que no pasan la altitud máxima y que no son una excursión de varios días. Cada
   una vale según su jerarquía: 1, 2, 6 o 24; 2 si MINCETUR no la jerarquizó. Si la consulta
   trae intereses, la que no atiende ninguno vale la cuarta parte.
2. Cómo se reparten los días: la ida y la vuelta (por carretera, en tren o en bote) y los
   días en la base. Un día de solo viaje puede durar hasta 9 horas; una ida más larga se
   parte en partes iguales y se duerme a mitad de camino. El día de llegada y el de salida
   se usan para visitar si, con el viaje, sobran al menos 90 minutos de una jornada de 8.
3. Un itinerario por polo para los más prometedores (``planificador.py``).
4. El puntaje: (1 − λ) · calidad · temporada · presupuesto + λ · novedad, con λ = 0,3. La
   calidad es el valor que visita el itinerario frente al mejor de la consulta, por la
   parte de las jornadas que tienen paradas; la temporada multiplica por 1, 0,75 o 0,4
   según el veredicto del mes; el presupuesto, por (presupuesto / costo)² si el costo
   central lo pasa. Con «Sorpréndeme», λ = 0,5 y solo entran polos fuera del circuito de
   Lima y Cusco.
5. Las tres mejores rutas, cada una con una base distinta.

Un viaje sale de su ciudad: un polo cuya base queda a menos de media hora del origen no se
propone para dormir (desde Lima, Lima no es un destino), y en un viaje de un día no entran
las paradas a menos de media hora del origen.

Los eventos que publican los municipios (``dreemgo/publicados.py``) se suman a los del
calendario oficial en cada ruta, y nada más: no entran al puntaje ni a los motivos, así que
publicar un evento no mueve ningún polo de su lugar.

Determinista: no hay azar sin semilla ni orden que dependa de un diccionario o un conjunto.
"""

from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from dreemgo.calendario import DIAS as DIAS_SEMANA
from dreemgo.calendario import Regla
from dreemgo.contrato import (
    DIAS_MAX,
    RUTAS_MAX,
    Aviso,
    Consulta,
    Costo,
    Dia,
    Estacionalidad,
    Evento,
    Indicadores,
    Parada,
    Polo,
    Punto,
    Recurso,
    Respuesta,
    Ruta,
    SinResultado,
    Sugerencia,
    Traslado,
)
from dreemgo.motor import costo as costos
from dreemgo.motor import textos
from dreemgo.motor.datos import Datos, Origen
from dreemgo.motor.datos import Polo as PoloDatos
from dreemgo.motor.planificador import Candidata, Jornada, Recorrido, Tiempos, mejor_plan, valor_visitado
from dreemgo.publicados import SIN_PUBLICADOS, Instantanea

JORNADA_MIN = 8 * 60
# Un día en el que solo se viaja, sin visitas, puede durar una hora más que una jornada: lo que
# tarda un bus de Lima a Huaraz. Partir ese viaje en dos días le quitaba dos al destino.
SOLO_VIAJE_MAX_MIN = 9 * 60
SALIDA_DEL_ORIGEN = 7 * 60
INICIO_DE_VISITAS = 8 * 60
MINIMO_PARA_VISITAR = 90
VISITA_POR_DEFECTO_MIN = 60
VISITA_MAX_MIN = 6 * 60  # visita más caminata de ida y vuelta: más que esto es una excursión aparte
# Lo que vale una parada según su jerarquía. De un nivel al siguiente se multiplica por 2, por 3
# y por 4: una de jerarquía 4 vale lo que doce de jerarquía 2, que son dos jornadas llenas. Con
# 1, 2, 4 y 8, un día de seis paradas de jerarquía 2 valía más que Machu Picchu. Es un supuesto
# del producto, por calibrar (decisión 0013).
VALOR_POR_JERARQUIA = {1: 1.0, 2: 2.0, 3: 6.0, 4: 24.0}
VALOR_SIN_JERARQUIA = 2.0  # como una de jerarquía 2: ni se premia ni se castiga lo que no se evaluó
FACTOR_SIN_INTERES = 0.25
FACTOR_TEMPORADA = {"viable": 1.0, "advertencia": 0.75, "desaconsejado": 0.4}
LAMBDA, LAMBDA_SORPRESA = 0.3, 0.5
CASA_MIN = 30  # una base más cerca que esto del origen es la misma ciudad
POLOS_A_PLANIFICAR = 12  # como mínimo; se sigue hasta tener tres bases distintas
POLOS_A_PLANIFICAR_MAX = 30
CANDIDATAS_MAX = 40
ALTITUD_AVISO_M = 3_500
ACLIMATACION_M = 2_500
KM_CARRETERA_MIN = 1.0  # menos que esto fuera del tren y del bote es ir a la estación o al muelle


class OrigenDesconocido(ValueError):
    pass


# ─────────────────────────────── qué se puede visitar ───────────────────────────────


def valor(recurso: dict, intereses: set[str]) -> float:
    v = VALOR_SIN_JERARQUIA if recurso["jerarquia"] is None else VALOR_POR_JERARQUIA[recurso["jerarquia"]]
    if intereses and not intereses & set(recurso["intereses"]):
        v *= FACTOR_SIN_INTERES
    return v


def minutos_de_visita(recurso: dict) -> int:
    return (recurso["visita_min"] or VISITA_POR_DEFECTO_MIN) + 2 * (recurso["caminata_min"] or 0)


def _candidata(i: int, recurso: dict, intereses: set[str]) -> Candidata:
    abre = textos.a_minutos(recurso["abre"], 0)
    cierra = textos.a_minutos(recurso["cierra"], 24 * 60)
    if cierra <= abre:  # horario nocturno o mal escrito: no se restringe
        abre, cierra = 0, 24 * 60
    dias = frozenset(DIAS_SEMANA.index(d) for d in recurso["dias"] if d in DIAS_SEMANA) if recurso["dias"] else None
    return Candidata(
        i=i,
        valor=valor(recurso, intereses),
        visita=minutos_de_visita(recurso),
        abre=abre,
        cierra=cierra,
        subtipo=recurso["subtipo"],
        dias=dias or None,
    )


def candidatas(polo: PoloDatos, consulta: Consulta, datos: Datos, desde: np.ndarray) -> list[Candidata]:
    """Las paradas del polo que se pueden programar, en el orden de sus códigos.
    ``desde``: minutos del depósito a cada parada (nan si no hay carretera)."""
    intereses = {i.value for i in consulta.intereses}
    salida = []
    for i, codigo in enumerate(polo.paradas):
        r = datos.recursos[codigo]
        if not np.isfinite(desde[i]) or minutos_de_visita(r) > VISITA_MAX_MIN:
            continue
        if consulta.altitud_max is not None and (r["altitud_m"] is None or r["altitud_m"] > consulta.altitud_max):
            continue
        salida.append(_candidata(i, r, intereses))
    return salida


def _mejores(cands: list[Candidata], desde: np.ndarray, cuantas: int) -> list[Candidata]:
    """Las ``cuantas`` con más valor por minuto (visita más ida y vuelta desde el depósito)."""
    orden = sorted(cands, key=lambda c: (-c.valor / (c.visita + 2 * desde[c.i]), c.i))
    return sorted(orden[:cuantas], key=lambda c: c.i)


# ─────────────────────────────── cómo se reparten los días ───────────────────────────────


@dataclass(frozen=True)
class Plan:
    """Los días del viaje antes de elegir paradas."""

    tipo_viaje: str  # "estrella" (con base) o "excursion" (un día desde el origen)
    jornadas: list[Jornada]
    dia_de_jornada: list[int]  # número de día (1..D) de cada jornada
    tramos: dict[int, int]  # día → minutos de carretera entre el origen y la base ese día
    llegada: int  # día en que se llega a la base
    salida: int  # día en que se deja la base


def plan_de_dias(dias: int, minutos_ida: float, fecha_inicio: date | None) -> Plan | None:
    """La ida y la vuelta, partidas en partes iguales si pasan de 9 horas, y los días en la
    base; None si no caben. El día de llegada y el de salida tienen visitas solo si el viaje
    y las visitas caben juntos en una jornada de 8 horas."""

    def dia_semana(n: int) -> int | None:
        return None if fecha_inicio is None else (fecha_inicio + timedelta(days=n - 1)).weekday()

    ida = int(math.ceil(minutos_ida))
    k = max(1, math.ceil(ida / SOLO_VIAJE_MAX_MIN))  # días de viaje de ida (y de vuelta)
    if dias < 2 * k:
        return None
    tramo = math.ceil(ida / k)
    ultimo = ida - tramo * (k - 1)  # el día de llegada (y el de salida) maneja un poco menos
    tramos = {n: tramo for n in range(1, k)} | {k: ultimo}
    tramos |= {dias - k + 1: ultimo} | {n: tramo for n in range(dias - k + 2, dias + 1)}
    jornadas, dia_de = [], []
    libre = JORNADA_MIN - ultimo
    if libre >= MINIMO_PARA_VISITAR:
        jornadas.append(Jornada(SALIDA_DEL_ORIGEN + ultimo, libre, dia_semana(k)))
        dia_de.append(k)
    for n in range(k + 1, dias - k + 1):
        jornadas.append(Jornada(INICIO_DE_VISITAS, JORNADA_MIN, dia_semana(n)))
        dia_de.append(n)
    if libre >= MINIMO_PARA_VISITAR:
        jornadas.append(Jornada(INICIO_DE_VISITAS, libre, dia_semana(dias - k + 1)))
        dia_de.append(dias - k + 1)
    return Plan("estrella", jornadas, dia_de, tramos, llegada=k, salida=dias - k + 1)


def plan_de_excursion(fecha_inicio: date | None) -> Plan:
    dia = None if fecha_inicio is None else fecha_inicio.weekday()
    return Plan("excursion", [Jornada(SALIDA_DEL_ORIGEN, JORNADA_MIN, dia)], [1], {}, llegada=1, salida=1)


# ─────────────────────────────── fechas y clima ───────────────────────────────


def anio_de_referencia(version_datos: str, mes: int) -> int:
    """El año del próximo «mes» desde la fecha de los datos: con datos de octubre de 2026,
    julio es julio de 2027. Así la respuesta solo depende de la consulta y de los datos."""
    anio, mes_datos = (int(x) for x in version_datos.split(".")[:2])
    return anio if mes >= mes_datos else anio + 1


def ventana(consulta: Consulta, version_datos: str) -> tuple[date, date]:
    if consulta.fecha_inicio is not None:
        return consulta.fecha_inicio, consulta.fecha_inicio + timedelta(days=consulta.dias - 1)
    anio = anio_de_referencia(version_datos, consulta.mes)
    return date(anio, consulta.mes, 1), date(anio, consulta.mes, calendar.monthrange(anio, consulta.mes)[1])


def mejores_meses(clima: tuple[dict, ...]) -> list[int]:
    for veredicto in ("viable", "advertencia"):
        meses = [c for c in clima if c["veredicto"] == veredicto]
        if meses:
            return [c["mes"] for c in sorted(meses, key=lambda c: (c["lluvia_mm"], c["mes"]))]
    return []


def estacionalidad(polo: PoloDatos, mes: int) -> Estacionalidad:
    c = polo.clima[mes - 1]
    lluvia, nombre = c["lluvia_mm"], textos.mes(mes).capitalize()
    if c["veredicto"] == "desaconsejado":
        texto = f"{nombre} es plena temporada de lluvias: {lluvia:.0f} mm, de los tres meses más lluviosos del polo."
    elif c["veredicto"] == "advertencia" and c["puesto_lluvia"] <= 3:
        texto = f"{nombre} es de los tres meses más lluviosos del polo ({lluvia:.0f} mm), aunque llueve poco."
    elif c["veredicto"] == "advertencia":
        texto = f"{nombre} es lluvioso aquí ({lluvia:.0f} mm), aunque no de los peores meses del polo."
    elif lluvia < 50:
        texto = f"{nombre} es temporada seca: {lluvia:.0f} mm de lluvia en el mes."
    else:
        texto = f"{nombre} trae algo de lluvia ({lluvia:.0f} mm), sin ser de los meses más lluviosos del polo."
    if c["temp_min_c"] is not None and c["temp_min_c"] < 0:
        texto += f" Las noches bajan de cero en la base ({c['temp_min_c']:.0f} °C)."
    return Estacionalidad(
        mes=mes,
        veredicto=c["veredicto"],
        lluvia_mm=lluvia,
        dias_con_lluvia=c["dias_con_lluvia"],
        horas_sol=None,
        temp_min_c=c["temp_min_c"],
        temp_max_c=c["temp_max_c"],
        explicacion=texto,
        mejores_meses=mejores_meses(polo.clima),
    )


def eventos_del_polo(polo: PoloDatos, desde: date, hasta: date, datos: Datos) -> list[Evento]:
    salida = []
    for codigo in polo.eventos:
        e = datos.eventos[codigo]
        if not e["regla"]:
            continue
        cae = Regla(e["regla"]).cae_en(desde, hasta)
        if cae is None:
            continue
        salida.append(
            Evento(
                id=e["id"],
                nombre=e["nombre"],
                tipo=e["tipo"],
                fecha_inicio=cae[0],
                fecha_fin=cae[1],
                precision_fecha=e["precision_fecha"],
                distrito=e["distrito"],
                provincia=e["provincia"],
                region=e["region"],
                fuente="mincetur",
                url=e["url"],
            )
        )
    return sorted(salida, key=lambda e: (e.fecha_inicio, e.id))


# ─────────────────────────────── piezas de la respuesta ───────────────────────────────


def recurso(r: dict) -> Recurso:
    return Recurso(
        codigo=r["codigo"],
        nombre=r["nombre"],
        categoria=r["categoria"],
        tipo=r["tipo"],
        subtipo=r["subtipo"],
        jerarquia=r["jerarquia"],
        lat=r["lat"],
        lon=r["lon"],
        altitud_m=r["altitud_m"],
        url_ficha=r["url_ficha"],
        descripcion=r["descripcion"],
        ingreso=r["ingreso"],
        tarifa_soles=r["tarifa_soles"],
    )


def polo_publico(polo: PoloDatos) -> Polo:
    b = polo.base
    return Polo(
        id=polo.id,
        nombre=polo.nombre,
        region=polo.region,
        regiones=list(polo.regiones),
        base=Punto(nombre=b["nombre"], lat=b["lat"], lon=b["lon"], altitud_m=b["altitud_m"]),
        recursos=polo.recursos,
        fuera_del_circuito=polo.fuera_del_circuito,
    )


@dataclass
class Itinerario:
    polo: PoloDatos
    plan: Plan
    recorridos: list[Recorrido]
    candidatas: list[Candidata]
    valor: float
    minutos_ida: float
    km_ida: float
    km_tren_ida: float = 0.0
    km_bote_ida: float = 0.0
    desde_en_capa: tuple[np.ndarray, np.ndarray] | None = None  # km en tren y en bote del depósito a cada parada


# ─────────────────────────────── tren y bote ───────────────────────────────


def _numero(x) -> float:
    x = float(x)
    return 0.0 if math.isnan(x) else x


def medios(km: float, km_tren: float, km_bote: float) -> list[str]:
    """Con qué se hace un camino: carretera (si más de un km no va en tren ni en bote), tren y
    bote, en ese orden."""
    tren, bote = _numero(km_tren), _numero(km_bote)
    salida = ["carretera"] if _numero(km) - tren - bote >= KM_CARRETERA_MIN or not (tren or bote) else []
    return salida + [m for m, k in (("tren", tren), ("bote", bote)) if k > 0]


def _en_capa_desde_deposito(polo: PoloDatos, origen: Origen, excursion: bool) -> tuple[np.ndarray, np.ndarray]:
    """(km en tren, km en bote) del depósito a cada parada: la base o, en un viaje de un día, el origen."""
    if not excursion:
        return polo.base_km_tren, polo.base_km_bote
    pares = [origen.a_parada_en_capa.get(c, (0.0, 0.0)) for c in polo.paradas]
    return np.array([t for t, _ in pares], dtype=float), np.array([b for _, b in pares], dtype=float)


def tramos_en_capa(it: Itinerario, recorrido: Recorrido) -> list[tuple[float, float]]:
    """(km en tren, km en bote) de cada tramo de un paseo: del depósito a la primera parada,
    entre paradas y de la última de vuelta al depósito."""
    idx = [v.candidata.i for v in recorrido.visitas]
    if not idx or it.desde_en_capa is None:
        return [(0.0, 0.0)] * (len(idx) + 1 if idx else 0)
    tren, bote = it.desde_en_capa
    polo = it.polo
    tramos = [(tren[idx[0]], bote[idx[0]])]
    tramos += [(polo.entre_km_tren[a, b], polo.entre_km_bote[a, b]) for a, b in zip(idx, idx[1:], strict=False)]
    tramos.append((tren[idx[-1]], bote[idx[-1]]))
    return [(_numero(t), _numero(b)) for t, b in tramos]


def medios_del_traslado(it: Itinerario) -> list[str]:
    """Con qué se hace la ida; en un viaje de un día, con qué se recorre el día."""
    if it.plan.tipo_viaje != "excursion":
        return medios(it.km_ida, it.km_tren_ida, it.km_bote_ida)
    tramos = [t for r in it.recorridos for t in tramos_en_capa(it, r)]
    tren, bote = sum(t for t, _ in tramos), sum(b for _, b in tramos)
    return medios(KM_CARRETERA_MIN + tren + bote, tren, bote)


def _nota_en_capa(it: Itinerario, recorrido: Recorrido, paradas: list[Parada]) -> str | None:
    """«En bote hasta Isla Taquile.»: las paradas a las que solo se llega en tren o en bote, las
    que lo necesitan ya desde el depósito. Volver de una isla en bote no hace «en bote» a la
    parada que sigue."""
    if it.desde_en_capa is None:
        return None
    idx = [v.candidata.i for v in recorrido.visitas]
    frases = []
    for medio, desde in zip(("tren", "bote"), it.desde_en_capa, strict=True):
        nombres = [p.recurso.nombre for p, i in zip(paradas, idx, strict=True) if _numero(desde[i]) > 0]
        if nombres:
            frases.append(f"En {medio} hasta {textos.lista(nombres)}.")
    return " ".join(frases) or None


def _km(polo: PoloDatos, recorrido: Recorrido, km_desde: np.ndarray) -> float:
    if not recorrido.visitas:
        return 0.0
    idx = [v.candidata.i for v in recorrido.visitas]
    km = km_desde[idx[0]] + km_desde[idx[-1]]
    km += sum(polo.entre_km[a, b] for a, b in zip(idx, idx[1:], strict=False))
    return float(km) if np.isfinite(km) else 0.0


def _paradas(polo: PoloDatos, recorrido: Recorrido, km_desde: np.ndarray, datos: Datos) -> list[Parada]:
    salida, anterior = [], None
    for orden, v in enumerate(recorrido.visitas, start=1):
        i = v.candidata.i
        km = km_desde[i] if anterior is None else polo.entre_km[anterior, i]
        salida.append(
            Parada(
                orden=orden,
                recurso=recurso(datos.recursos[polo.paradas[i]]),
                llegada=textos.hora(v.llegada),
                minutos_traslado=v.traslado,
                km_desde_anterior=round(float(km), 1) if np.isfinite(km) else 0.0,
                minutos_visita=v.candidata.visita,
            )
        )
        anterior = i
    return salida


def dias_del_viaje(it: Itinerario, consulta: Consulta, origen: Origen, datos: Datos) -> list[Dia]:
    polo, plan = it.polo, it.plan
    base = polo.base["nombre"]
    por_dia = dict(zip(plan.dia_de_jornada, it.recorridos, strict=True))
    excursion = plan.tipo_viaje == "excursion"
    km_desde = _km_desde_deposito(polo, origen, excursion)
    por = textos.por_medios(medios_del_traslado(it))
    dias = []
    for n in range(1, consulta.dias + 1):
        fecha = None if consulta.fecha_inicio is None else consulta.fecha_inicio + timedelta(days=n - 1)
        recorrido = por_dia.get(n)
        paradas = _paradas(polo, recorrido, km_desde, datos) if recorrido else []
        visita_min = recorrido.minutos if recorrido else 0
        visita_km = _km(polo, recorrido, km_desde) if recorrido else 0.0
        carretera = plan.tramos.get(n, 0)
        km_carretera = it.km_ida * carretera / it.minutos_ida if carretera and it.minutos_ida else 0.0
        viaje, salida = textos.duracion(carretera), textos.hora(SALIDA_DEL_ORIGEN)
        if excursion:
            tipo, nota = "ida_visita_y_vuelta", f"Sale de {origen.nombre} a las {salida} y vuelve el mismo día."
        elif n == 1 and n < plan.llegada:
            tipo, nota = (
                "ida",
                f"Salida de {origen.nombre} a las {salida}: {viaje} {por} hacia {base}; se duerme en el camino.",
            )
        elif n < plan.llegada:
            tipo, nota = "ida", f"Otro tramo hacia {base}: {viaje} {por}; se duerme en el camino."
        elif n == plan.llegada:
            tipo = "ida_y_visita" if paradas else "ida"
            nota = f"Salida de {origen.nombre} a las {salida}; {viaje} {por} hasta {base}."
            if n > 1:
                nota = f"Último tramo hasta {base}: {viaje} {por}."
        elif n == plan.salida:
            tipo = "visita_y_vuelta" if paradas else "vuelta"
            nota = f"Vuelta a {origen.nombre}: {viaje} {por}."
            if n < consulta.dias:
                nota = f"Se deja {base}: {viaje} {por} hacia {origen.nombre}; se duerme en el camino."
        elif n > plan.salida:
            tipo = "vuelta"
            nota = f"Último tramo de vuelta a {origen.nombre}: {viaje} {por}."
            if n < consulta.dias:
                nota = f"Otro tramo de vuelta a {origen.nombre}: {viaje} {por}; se duerme en el camino."
        else:
            tipo, nota = "visita", None if paradas else f"Día libre en {base}."
        en_capa = _nota_en_capa(it, recorrido, paradas) if recorrido else None
        # El día de salida se visita antes de volver: su nota va en ese orden.
        notas = (en_capa, nota) if not excursion and n == plan.salida else (nota, en_capa)
        dias.append(
            Dia(
                numero=n,
                fecha=fecha,
                tipo=tipo,
                horas=round((carretera + visita_min) / 60, 1),
                km=round(km_carretera + visita_km, 1),
                paradas=paradas,
                nota=" ".join(t for t in notas if t) or None,
            )
        )
    return dias


def _km_desde_deposito(polo: PoloDatos, origen: Origen, excursion: bool) -> np.ndarray:
    if not excursion:
        return polo.base_km
    return np.array([origen.a_parada.get(c, (np.nan, np.nan))[1] for c in polo.paradas], dtype=float)


def _minutos_desde_deposito(polo: PoloDatos, origen: Origen, excursion: bool) -> np.ndarray:
    if not excursion:
        return polo.base_minutos
    return np.array([origen.a_parada.get(c, (np.nan, np.nan))[0] for c in polo.paradas], dtype=float)


def _visitadas(it: Itinerario) -> list[Candidata]:
    return [v.candidata for r in it.recorridos for v in r.visitas]


def costo_del_viaje(it: Itinerario, consulta: Consulta, datos: Datos, dias: list[Dia]) -> Costo:
    excursion = it.plan.tipo_viaje == "excursion"
    tarifas, combinados, sin_tarifa = [], [], 0
    for c in _visitadas(it):
        r = datos.recursos[it.polo.paradas[c.i]]
        if r["ingreso"] != "pagado":
            continue
        if r["tarifa_soles"] is None:
            sin_tarifa += 1
        elif r["boleto_combinado"]:
            combinados.append(r["tarifa_soles"])
        else:
            tarifas.append(r["tarifa_soles"])
    # El tren y el bote se pagan aparte: lo demás va en bus o en movilidad local.
    tramos = [t for r in it.recorridos for t in tramos_en_capa(it, r)]
    tren_local, bote_local = sum(t for t, _ in tramos), sum(b for _, b in tramos)
    km_locales = sum(d.km for d in dias) if excursion else sum(_km(it.polo, r, it.polo.base_km) for r in it.recorridos)
    tren_ida, bote_ida = (0.0, 0.0) if excursion else (_numero(it.km_tren_ida), _numero(it.km_bote_ida))
    gastos = costos.Gastos(
        dias=consulta.dias,
        noches=0 if excursion else consulta.dias - 1,
        km_interprovincial=0.0 if excursion else max(it.km_ida - tren_ida - bote_ida, 0.0),
        km_locales=max(km_locales - tren_local - bote_local, 0.0),
        tarifas=tuple(tarifas),
        combinados=tuple(combinados),
        sin_tarifa=sin_tarifa,
        base=it.polo.base["nombre"],
        tramos_tren=(2 if tren_ida > 0 else 0) + sum(1 for t, _ in tramos if t > 0),
        km_bote=2 * bote_ida + bote_local,
    )
    return costos.estimar(datos.costos, gastos, consulta.presupuesto)


def indicadores(it: Itinerario, dias: list[Dia], datos: Datos, alcanzable: float) -> Indicadores:
    visitadas = [datos.recursos[it.polo.paradas[c.i]] for c in _visitadas(it)]
    jerarquias = [r["jerarquia"] for r in visitadas if r["jerarquia"] is not None]
    altitudes = [r["altitud_m"] for r in visitadas if r["altitud_m"] is not None]
    capturado = sum(c.valor for c in _visitadas(it))
    return Indicadores(
        paradas=len(visitadas),
        jerarquia_media=round(sum(jerarquias) / len(jerarquias), 2) if jerarquias else None,
        paradas_jerarquia_alta=sum(1 for j in jerarquias if j >= 3),
        altitud_max_m=max(altitudes) if altitudes else None,
        km_total=round(sum(d.km for d in dias), 1),
        valor_capturado=round(min(1.0, capturado / alcanzable), 3) if alcanzable else 0.0,
    )


def motivos(
    it: Itinerario, consulta: Consulta, origen: Origen, est: Estacionalidad, eventos: list[Evento], datos: Datos
) -> list[str]:
    visitadas = sorted(
        (datos.recursos[it.polo.paradas[c.i]] for c in _visitadas(it)),
        key=lambda r: (-(r["jerarquia"] or 0), r["codigo"]),
    )
    salida = []
    altas = [r for r in visitadas if (r["jerarquia"] or 0) >= 3]
    if len(altas) == 1:
        salida.append(f"{altas[0]['nombre']}, de jerarquía {altas[0]['jerarquia']}")
    elif altas:
        nombres = textos.lista([r["nombre"] for r in altas[:3]])
        salida.append(f"{len(altas)} lugares de jerarquía 3 o 4: {nombres}")
    if consulta.intereses:
        pedidos = {i.value for i in consulta.intereses}
        atienden = sum(1 for r in visitadas if pedidos & set(r["intereses"]))
        etiquetas = textos.lista([datos.intereses[i.value]["etiqueta"].lower() for i in consulta.intereses], "o")
        if atienden == len(visitadas):
            salida.append(f"Todas sus paradas son de {etiquetas}")
        elif atienden:
            salida.append(f"{atienden} de sus {len(visitadas)} paradas son de {etiquetas}")
    if est.veredicto == "viable" and est.lluvia_mm < 50:
        salida.append(f"{textos.mes(est.mes).capitalize()} es temporada seca aquí")
    if eventos:
        e = eventos[0]
        salida.append(f"Coincide con {e.nombre} ({textos.fechas(e.fecha_inicio, e.fecha_fin)})")
    if it.polo.fuera_del_circuito:
        salida.append("Fuera del circuito de Lima y Cusco")
    if it.plan.tipo_viaje == "estrella":
        por = textos.por_medios(medios_del_traslado(it))
        salida.append(f"A {textos.duracion(it.minutos_ida)} de {origen.nombre} {por}")
    return salida[:4]


def avisos(
    it: Itinerario, consulta: Consulta, est: Estacionalidad, costo: Costo, dias: list[Dia], datos: Datos
) -> list[Aviso]:
    polo, salida = it.polo, []
    if est.veredicto != "viable":
        mejores = textos.meses(est.mejores_meses[:4]) if est.mejores_meses else "ninguno del todo seco"
        salida.append(
            Aviso(
                tipo="estacionalidad",
                nivel="advertencia",
                mensaje=f"{est.explicacion} Mejores meses para ir: {mejores}.",
            )
        )
    visitadas = [datos.recursos[polo.paradas[c.i]] for c in _visitadas(it)]
    altas = sorted((r for r in visitadas if (r["altitud_m"] or 0) >= ALTITUD_AVISO_M), key=lambda r: -r["altitud_m"])
    if altas:
        salida.append(
            Aviso(
                tipo="altitud",
                nivel="info",
                mensaje=f"Hay paradas a más de {textos.miles(ALTITUD_AVISO_M)} m: la más alta, "
                f"{altas[0]['nombre']}, a {textos.miles(altas[0]['altitud_m'])} m.",
            )
        )
    altura_base = polo.base["altitud_m"]
    if it.plan.tipo_viaje == "estrella" and altura_base is not None and altura_base >= ACLIMATACION_M:
        salida.append(
            Aviso(
                tipo="aclimatacion",
                nivel="advertencia",
                mensaje=f"Se duerme a {textos.miles(altura_base)} m en {polo.base['nombre']}. Si llegas desde "
                "la costa, el cuerpo tarda uno o dos días en acostumbrarse: conviene un primer día tranquilo.",
            )
        )
    if costo.exceso:
        salida.append(
            Aviso(
                tipo="presupuesto",
                nivel="advertencia",
                mensaje=f"El costo central ({textos.soles(costo.p50)}) pasa tu presupuesto "
                f"por {textos.soles(costo.exceso)}.",
            )
        )
    en_tren = "tren" in medios_del_traslado(it) or any(t > 0 for r in it.recorridos for t, _ in tramos_en_capa(it, r))
    if en_tren:
        salida.append(
            Aviso(
                tipo="acceso",
                nivel="info",
                mensaje="Parte del viaje va en tren, con horarios y cupos fijos: compra el pasaje con anticipación.",
            )
        )
    largas = [r for r in visitadas if (r["caminata_min"] or 0) >= 60]
    if largas:
        nombres = textos.lista([r["nombre"] for r in largas[:3]])
        salida.append(
            Aviso(tipo="acceso", nivel="info", mensaje=f"Hay que caminar más de una hora para llegar a {nombres}.")
        )
    carretera = sum(it.plan.tramos.values())
    if it.plan.tipo_viaje == "estrella" and carretera >= 0.4 * consulta.dias * JORNADA_MIN:
        salida.append(
            Aviso(
                tipo="dias",
                nivel="advertencia",
                mensaje=f"La ida y la vuelta se llevan {textos.duracion(carretera)} de tus {consulta.dias} días: "
                "con más días, el viaje rinde más.",
            )
        )
    libres = [d.numero for d in dias if d.tipo == "visita" and not d.paradas]
    if libres:
        salida.append(
            Aviso(
                tipo="dias",
                nivel="info",
                mensaje=f"{'Queda un día libre' if len(libres) == 1 else f'Quedan {len(libres)} días libres'} "
                f"en {polo.base['nombre']}: no hay más paradas que quepan con lo que pediste.",
            )
        )
    if polo.clima[0]["fuente"] != "open_meteo_polo":
        salida.append(
            Aviso(
                tipo="datos",
                nivel="info",
                mensaje="El clima de este polo es el promedio de su región; el del propio polo "
                "todavía no se ha cargado.",
            )
        )
    if it.plan.tipo_viaje == "estrella" and altura_base is None:
        salida.append(
            Aviso(tipo="datos", nivel="info", mensaje=f"No se sabe a qué altitud está {polo.base['nombre']}.")
        )
    return salida


# ─────────────────────────────── el motor ───────────────────────────────


@dataclass
class Preparado:
    polo: PoloDatos
    plan: Plan
    candidatas: list[Candidata]
    tiempos: Tiempos
    minutos_ida: float
    km_ida: float
    temporada: float
    cota: float  # valor que cabe, aproximado, para elegir qué polos planificar
    km_tren_ida: float = 0.0
    km_bote_ida: float = 0.0
    desde_en_capa: tuple[np.ndarray, np.ndarray] | None = None


def _cota(cands: list[Candidata], desde: np.ndarray, capacidad: float) -> float:
    total, usado = 0.0, 0.0
    for c in sorted(cands, key=lambda c: (-c.valor / (c.visita + 2 * desde[c.i]), c.i)):
        costo = c.visita + 2 * desde[c.i]
        if usado + costo <= capacidad:
            total, usado = total + c.valor, usado + costo
    return total


def preparar(polo: PoloDatos, consulta: Consulta, origen: Origen, datos: Datos) -> Preparado | None:
    """Lo que hace falta para planificar el polo, o None si no se puede ir."""
    base_altitud = polo.base["altitud_m"]
    if consulta.altitud_max is not None and base_altitud is not None and base_altitud > consulta.altitud_max:
        return None
    if consulta.sorpresa and not polo.fuera_del_circuito:
        return None
    excursion = consulta.dias == 1
    if not excursion and origen.a_base.get(polo.id, (np.inf,))[0] < CASA_MIN:
        return None
    if excursion:
        plan = plan_de_excursion(consulta.fecha_inicio)
        minutos_ida, km_ida, km_tren_ida, km_bote_ida = 0.0, 0.0, 0.0, 0.0
    else:
        minutos_ida, km_ida = origen.a_base.get(polo.id, (np.nan, np.nan))
        km_tren_ida, km_bote_ida = origen.a_base_en_capa.get(polo.id, (0.0, 0.0))
        if not np.isfinite(minutos_ida):
            return None
        plan = plan_de_dias(consulta.dias, minutos_ida, consulta.fecha_inicio)
        if plan is None or not plan.jornadas:
            return None
    desde = _minutos_desde_deposito(polo, origen, excursion)
    if excursion:  # lo que queda en la misma ciudad del origen no es una excursión
        desde = np.where(desde < CASA_MIN, np.nan, desde)
    cands = candidatas(polo, consulta, datos, desde)
    if not cands:
        return None
    cands = _mejores(cands, desde, CANDIDATAS_MAX)
    capacidad = sum(j.tope for j in plan.jornadas)
    veredicto = polo.clima[consulta.mes - 1]["veredicto"]
    return Preparado(
        polo=polo,
        plan=plan,
        candidatas=cands,
        tiempos=Tiempos(desde, polo.entre_minutos),
        minutos_ida=float(minutos_ida),
        km_ida=float(km_ida),
        temporada=FACTOR_TEMPORADA[veredicto],
        cota=_cota(cands, desde, capacidad),
        km_tren_ida=km_tren_ida,
        km_bote_ida=km_bote_ida,
        desde_en_capa=_en_capa_desde_deposito(polo, origen, excursion),
    )


def resolver(
    consulta: Consulta, datos: Datos, publicados: Instantanea = SIN_PUBLICADOS, sugerir: bool = True
) -> Respuesta:
    origen = datos.origenes.get(consulta.origen)
    if origen is None:
        raise OrigenDesconocido(consulta.origen)
    lam = LAMBDA_SORPRESA if consulta.sorpresa else LAMBDA

    preparados = [p for polo in datos.polos.values() if (p := preparar(polo, consulta, origen, datos)) is not None]
    if preparados:
        tope = max(p.cota for p in preparados) or 1.0
        preparados.sort(key=lambda p: (-((1 - lam) * p.temporada * p.cota / tope + lam * p.polo.novedad), p.polo.id))

    itinerarios, bases_planificadas = [], set()
    for n, p in enumerate(preparados[:POLOS_A_PLANIFICAR_MAX]):
        if n >= POLOS_A_PLANIFICAR and len(bases_planificadas) >= RUTAS_MAX:
            break
        recorridos = mejor_plan(p.candidatas, p.plan.jornadas, p.tiempos)
        visitado = valor_visitado(recorridos)
        if visitado > 0:
            it = Itinerario(
                p.polo,
                p.plan,
                recorridos,
                p.candidatas,
                visitado,
                p.minutos_ida,
                p.km_ida,
                p.km_tren_ida,
                p.km_bote_ida,
                p.desde_en_capa,
            )
            itinerarios.append((p, it))
            bases_planificadas.add(p.polo.base["nombre"])

    # Primero se eligen tres bases distintas por su puntaje sin el presupuesto, que solo
    # reordena esas tres y avisa: un presupuesto corto nunca esconde una ruta (CONTRATO §3.7).
    mejor = max((it.valor for _, it in itinerarios), default=1.0)
    puntuados = []
    for p, it in itinerarios:
        ocupacion = sum(1 for r in it.recorridos if r.visitas) / len(it.recorridos)
        calidad = it.valor / mejor * ocupacion * p.temporada
        puntuados.append((calidad, (1 - lam) * calidad + lam * it.polo.novedad, p, it))
    puntuados.sort(key=lambda x: (-x[1], x[2].polo.id))
    desde, hasta = ventana(consulta, datos.version)
    elegidas, bases = [], set()
    for calidad, _, p, it in puntuados:
        if it.polo.base["nombre"] in bases:
            continue
        bases.add(it.polo.base["nombre"])
        dias = dias_del_viaje(it, consulta, origen, datos)
        costo = costo_del_viaje(it, consulta, datos, dias)
        est = estacionalidad(it.polo, consulta.mes)
        eventos = eventos_del_polo(it.polo, desde, hasta, datos)
        # Lo publicado se lista con lo oficial, pero no es un motivo para proponer el polo.
        todos = sorted(eventos + publicados.entre(desde, hasta, it.polo.id), key=lambda e: (e.fecha_inicio, e.id))
        presupuesto = 1.0 if not costo.exceso else (consulta.presupuesto / costo.p50) ** 2
        puntaje = (1 - lam) * calidad * presupuesto + lam * it.polo.novedad
        elegidas.append(
            Ruta(
                polo=polo_publico(it.polo),
                puntaje=round(min(1.0, puntaje), 3),
                motivos=motivos(it, consulta, origen, est, eventos, datos),
                estacionalidad=est,
                traslado=_traslado(it, origen),
                dias=dias,
                costo=costo,
                eventos=todos,
                avisos=avisos(it, consulta, est, costo, dias, datos),
                indicadores=indicadores(it, dias, datos, sum(c.valor for c in p.candidatas)),
            )
        )
        if len(elegidas) == RUTAS_MAX:
            break
    elegidas.sort(key=lambda r: (-r.puntaje, r.polo.id))

    sin_resultado = None if elegidas else _sin_resultado(consulta, origen, datos, sugerir)
    return Respuesta(
        version_datos=publicados.version(datos.version),
        consulta=consulta,
        rutas=elegidas,
        sin_resultado=sin_resultado,
        atribucion=list(datos.atribucion),
    )


def _traslado(it: Itinerario, origen: Origen) -> Traslado:
    medios_ = medios_del_traslado(it)
    acceso = "sin_acceso_terrestre" if "bote" in medios_ else "terrestre"
    if it.plan.tipo_viaje == "excursion":
        primera = it.recorridos[0].visitas[0] if it.recorridos[0].visitas else None
        horas = None if primera is None else round(primera.traslado / 60, 1)
        return Traslado(
            desde=origen.nombre, horas=horas, dias_de_viaje=0, medios=medios_, acceso=acceso, fuente="red_vial"
        )
    tramos = it.plan.tramos
    return Traslado(
        desde=origen.nombre,
        horas=round(it.minutos_ida / 60, 1),
        dias_de_viaje=len(tramos),
        medios=medios_,
        acceso=acceso,
        fuente="red_vial",
    )


def _sin_resultado(consulta: Consulta, origen: Origen, datos: Datos, sugerir: bool) -> SinResultado:
    dias = f"{consulta.dias} {'día' if consulta.dias == 1 else 'días'}"
    motivo = f"Ningún polo cabe en {dias} desde {origen.nombre} con lo que pediste."
    if consulta.dias == 1:
        motivo = f"En un día no se llega desde {origen.nombre} a ninguna parada que cumpla lo que pediste y volver."
    sugerencias = []
    if sugerir:
        pruebas = []
        if consulta.dias < DIAS_MAX:
            mas = min(DIAS_MAX, consulta.dias + (2 if consulta.dias > 1 else 3))
            pruebas.append(("dias", mas, {"dias": mas}))
        if consulta.altitud_max is not None:
            pruebas.append(("altitud_max", None, {"altitud_max": None}))
        if consulta.intereses:
            pruebas.append(("intereses", [], {"intereses": []}))
        for campo, valor_nuevo, cambio in pruebas:
            otra = consulta.model_copy(update=cambio)
            n = len(resolver(otra, datos, sugerir=False).rutas)
            if n:
                efecto = f"aparece{'' if n == 1 else 'n'} {n} ruta{'' if n == 1 else 's'}"
                sugerencias.append(Sugerencia(campo=campo, valor=valor_nuevo, efecto=efecto))
    return SinResultado(motivo=motivo, sugerencias=sugerencias)
