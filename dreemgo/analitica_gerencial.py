"""Lecturas descriptivas del uso de DreemGO y una proyección didáctica.

Se trabaja con las acciones ya recibidas, sin inferir compras ni causas de abandono.
Los modelos de proyección solo usan el pasado; la última semana se reserva para
compararlos. No son un modelo de demanda validado para el negocio.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from math import sqrt
from statistics import mean, stdev
from typing import Literal

from pydantic import BaseModel

HORA_PERU = timezone(timedelta(hours=-5), name="America/Lima")


class Distribucion(BaseModel):
    id: str
    nombre: str
    cantidad: int
    porcentaje: float


class Etapa(BaseModel):
    id: str
    nombre: str
    sesiones: int
    porcentaje: float | None


class Pareto(BaseModel):
    nombre: str
    cantidad: int
    porcentaje: float
    acumulado: float


class CeldaCalor(BaseModel):
    dia: int
    hora: int
    acciones: int


class Intervalo(BaseModel):
    desde: float
    hasta: float
    cantidad: int


class Latencia(BaseModel):
    n: int
    media: float | None
    mediana: float | None
    p25: float | None
    p75: float | None
    p95: float | None
    desviacion: float | None
    minimo: float | None
    maximo: float | None
    histograma: list[Intervalo]


class Variable(BaseModel):
    id: str
    nombre: str


class ParCorrelacion(BaseModel):
    x: str
    y: str
    r: float | None
    n: int


class Correlacion(BaseModel):
    variables: list[Variable]
    pares: list[ParCorrelacion]
    nota: str


class PuntoDispersion(BaseModel):
    dias: float
    presupuesto: float


class PuntoProyeccion(BaseModel):
    fecha: date
    valor: float


class Candidato(BaseModel):
    metodo: str
    mae: float


class Proyeccion(BaseModel):
    estado: Literal["disponible", "insuficiente"]
    metodo: str | None
    dias_historia: int
    n_validacion: int
    mae_validacion: float | None
    candidatos: list[Candidato]
    historico: list[PuntoProyeccion]
    futuro: list[PuntoProyeccion]
    nota: str


class AnalisisGerencial(BaseModel):
    distribucion: list[Distribucion]
    embudo: list[Etapa]
    pareto: list[Pareto]
    mapa_calor: list[CeldaCalor]
    latencia: Latencia
    correlacion: Correlacion
    dispersion: list[PuntoDispersion]
    proyeccion: Proyeccion
    nota: str


def _momento(evento: dict) -> datetime:
    return datetime.fromisoformat(evento["instante"].replace("Z", "+00:00")).astimezone(HORA_PERU)


def percentil(valores: list[float], fraccion: float) -> float | None:
    """Interpolación lineal entre los valores ordenados; misma regla para todas las vistas."""
    if not valores:
        return None
    ordenados = sorted(valores)
    posicion = (len(ordenados) - 1) * fraccion
    inferior = int(posicion)
    superior = min(inferior + 1, len(ordenados) - 1)
    return round(ordenados[inferior] + (ordenados[superior] - ordenados[inferior]) * (posicion - inferior), 2)


def resumen_latencia(eventos: list[dict]) -> Latencia:
    valores = [
        float(e["duracion_ms"])
        for e in eventos
        if e["tipo"] == "busqueda_resultado" and isinstance(e.get("duracion_ms"), (int, float))
    ]
    histograma = []
    if valores:
        minimo, maximo = min(valores), max(valores)
        # Seis intervalos iguales; el último incluye su extremo derecho.
        # Si todos los tiempos son iguales, una sola barra evita divisiones por cero.
        cantidad = 6 if maximo > minimo else 1
        ancho = (maximo - minimo) / cantidad if cantidad > 1 else 1.0
        frecuencias = Counter(min(int((v - minimo) / ancho), cantidad - 1) for v in valores)
        histograma = [
            Intervalo(
                desde=round(minimo + i * ancho, 2),
                hasta=round(minimo + (i + 1) * ancho, 2),
                cantidad=frecuencias[i],
            )
            for i in range(cantidad)
        ]
    return Latencia(
        n=len(valores),
        media=round(mean(valores), 2) if valores else None,
        mediana=percentil(valores, 0.5),
        p25=percentil(valores, 0.25),
        p75=percentil(valores, 0.75),
        p95=percentil(valores, 0.95),
        desviacion=round(stdev(valores), 2) if len(valores) > 1 else None,
        minimo=min(valores) if valores else None,
        maximo=max(valores) if valores else None,
        histograma=histograma,
    )


ESTADOS = [
    ("guardado", "Guardó un viaje"),
    ("abierto", "Abrió una ruta sin guardar"),
    ("resultados", "Recibió viajes sin abrir una ruta"),
    ("sin_resultados", "Obtuvo una respuesta sin viajes"),
    ("error", "Registró error sin recibir viajes"),
    ("sin_respuesta", "Buscó sin respuesta registrada"),
    ("formulario", "Abrió formulario sin buscar"),
    ("ayuda", "Usó la ayuda sin planear un viaje"),
    ("visita", "Solo registró la visita"),
]


def _estado_sesion(eventos: list[dict]) -> str:
    """Etapa más avanzada observada, con guardado priorizado; clases excluyentes.

    Un visitante puede reintentar o seguir interactuando después de un error.
    Por eso no se atribuye un fracaso final solo por haber recibido ese error.
    """
    tipos = {e["tipo"] for e in eventos}
    if "viaje_guardado" in tipos:
        return "guardado"
    if tipos & {"itinerario_abierto", "viaje_compartido", "viaje_impreso"}:
        return "abierto"
    if any(e["tipo"] == "busqueda_resultado" and e.get("resultados", 0) > 0 for e in eventos):
        return "resultados"
    if "busqueda_resultado" in tipos:
        return "sin_resultados"
    if "error_consulta" in tipos:
        return "error"
    if "busqueda_iniciada" in tipos:
        return "sin_respuesta"
    if "formulario_abierto" in tipos:
        return "formulario"
    if tipos & {"ayuda_consultada", "comentario_enviado"}:
        return "ayuda"
    return "visita"


def _embudo(por_sesion: dict[str, list[dict]]) -> list[Etapa]:
    """Solo cuenta una etapa si las anteriores aparecen antes en esa sesión.

    Un enlace directo o el filtro de fechas pueden dejar etapas fuera del periodo.
    Esa sesión aparece en el total y distribución, pero no inventamos sus pasos.
    """
    pasos = [
        ("visita", "Sesiones con actividad", None),
        ("formulario", "Abrieron el formulario", "formulario_abierto"),
        ("busqueda", "Iniciaron una búsqueda", "busqueda_iniciada"),
        ("resultados", "Recibieron viajes", "busqueda_resultado"),
        ("detalle", "Abrieron un itinerario", "itinerario_abierto"),
        ("guardado", "Guardaron un viaje", "viaje_guardado"),
    ]
    cuentas = [len(por_sesion), 0, 0, 0, 0, 0]
    for eventos in por_sesion.values():
        paso = 1
        for evento in sorted(eventos, key=_momento):
            if paso >= len(pasos):
                break
            coincide = evento["tipo"] == pasos[paso][2]
            if coincide and (paso != 3 or evento.get("resultados", 0) > 0):
                cuentas[paso] += 1
                paso += 1
    return [
        Etapa(
            id=id_paso,
            nombre=nombre,
            sesiones=cuentas[i],
            porcentaje=round(cuentas[i] * 100 / cuentas[0], 1) if cuentas[0] else None,
        )
        for i, (id_paso, nombre, _) in enumerate(pasos)
    ]


def _correlacion(por_sesion: dict[str, list[dict]]) -> Correlacion:
    variables = [
        Variable(id="dias", nombre="Días solicitados"),
        Variable(id="presupuesto", nombre="Presupuesto indicado"),
        Variable(id="latencia", nombre="Latencia mediana"),
        Variable(id="interacciones", nombre="Acciones sobre viajes"),
    ]
    filas = []
    for eventos in por_sesion.values():
        consultas = [e for e in sorted(eventos, key=_momento) if e["tipo"] == "busqueda_iniciada"]
        ultima = consultas[-1] if consultas else {}
        tiempos = [
            e["duracion_ms"]
            for e in eventos
            if e["tipo"] == "busqueda_resultado" and isinstance(e.get("duracion_ms"), (int, float))
        ]
        filas.append(
            {
                "dias": ultima.get("dias"),
                "presupuesto": ultima.get("presupuesto"),
                "latencia": percentil(tiempos, 0.5),
                "interacciones": sum(
                    e["tipo"] in {"itinerario_abierto", "viaje_guardado", "viaje_compartido", "viaje_impreso"}
                    for e in eventos
                ),
            }
        )
    pares = []
    for x in variables:
        for y in variables:
            completos = [(f[x.id], f[y.id]) for f in filas if f[x.id] is not None and f[y.id] is not None]
            r = None
            if len(completos) >= 5:
                media_x = mean(p[0] for p in completos)
                media_y = mean(p[1] for p in completos)
                sx = sum((p[0] - media_x) ** 2 for p in completos)
                sy = sum((p[1] - media_y) ** 2 for p in completos)
                if sx > 0 and sy > 0:
                    producto = sum((p[0] - media_x) * (p[1] - media_y) for p in completos)
                    r = round(max(-1.0, min(1.0, producto / sqrt(sx * sy))), 3)
            pares.append(ParCorrelacion(x=x.id, y=y.id, r=r, n=len(completos)))
    return Correlacion(
        variables=variables,
        pares=pares,
        nota=(
            "Pearson por sesión, usando pares completos. La consulta más reciente aporta días y presupuesto; "
            "la latencia es la mediana de sus respuestas y las interacciones cuentan abrir, guardar, compartir "
            "e imprimir. Menos de cinco pares o una variable constante no permiten calcular r. "
            "Una asociación no demuestra causalidad; en la simulación refleja sus supuestos."
        ),
    )


def _predecir(valores: list[float], horizonte: int, metodo: str) -> list[float]:
    if metodo == "Promedio de los últimos 7 días":
        return [mean(valores[-7:])] * horizonte
    centro_x = (len(valores) - 1) / 2
    centro_y = mean(valores)
    denominador = sum((i - centro_x) ** 2 for i in range(len(valores)))
    pendiente = sum((i - centro_x) * (v - centro_y) for i, v in enumerate(valores)) / denominador
    return [max(0.0, centro_y + pendiente * (len(valores) + i - centro_x)) for i in range(horizonte)]


def proyectar(serie: list[dict], modo: str, hoy: date | None = None) -> Proyeccion:
    hoy = hoy or datetime.now(HORA_PERU).date()
    historia = [
        PuntoProyeccion(fecha=p["fecha"], valor=p["sesiones"])
        for p in serie
        if modo == "simulacion" or date.fromisoformat(str(p["fecha"])) < hoy
    ]
    if len(historia) < 21:
        return Proyeccion(
            estado="insuficiente",
            metodo=None,
            dias_historia=len(historia),
            n_validacion=0,
            mae_validacion=None,
            candidatos=[],
            historico=historia,
            futuro=[],
            nota=(
                "Se necesitan al menos 21 días completos del periodo seleccionado. "
                "En actividad real se excluye el día actual. Selecciona un periodo más amplio para ver la proyección."
            ),
        )
    valores = [p.valor for p in historia]
    entrenamiento, validacion = valores[:-7], valores[-7:]
    candidatos = []
    for metodo in ("Promedio de los últimos 7 días", "Tendencia lineal"):
        esperado = _predecir(entrenamiento, 7, metodo)
        error = mean(abs(observado - estimado) for observado, estimado in zip(validacion, esperado, strict=True))
        candidatos.append(Candidato(metodo=metodo, mae=error))
    elegido = min(candidatos, key=lambda c: c.mae)
    futuro = _predecir(valores, 7, elegido.metodo)
    return Proyeccion(
        estado="disponible",
        metodo=elegido.metodo,
        dias_historia=len(historia),
        n_validacion=7,
        mae_validacion=round(elegido.mae, 2),
        candidatos=[Candidato(metodo=c.metodo, mae=round(c.mae, 2)) for c in candidatos],
        historico=historia,
        futuro=[
            PuntoProyeccion(fecha=historia[-1].fecha + timedelta(days=i + 1), valor=round(valor, 2))
            for i, valor in enumerate(futuro)
        ],
        nota=(
            "Proyección exploratoria de sesiones por día. Se compara promedio móvil de 7 días con tendencia "
            "lineal: se ajustan sin usar los últimos 7 días y se elige el menor error absoluto medio "
            "en esos 7 días. Luego se reajusta con toda la historia. Es una sola partición temporal, "
            "no validación cruzada ni garantía de demanda. No incluye intervalo de confianza. "
            + (
                "El historial es simulado; la proyección también es una demostración."
                if modo == "simulacion"
                else "El día actual se excluye por estar incompleto. "
                "Los eventos recibidos pueden omitir actividad sin permiso."
            )
        ),
    )


def analizar(eventos: list[dict], serie: list[dict], modo: str) -> AnalisisGerencial:
    por_sesion: dict[str, list[dict]] = defaultdict(list)
    calor: Counter[tuple[int, int]] = Counter()
    for evento in eventos:
        por_sesion[evento["sesion"]].append(evento)
        instante = _momento(evento)
        calor[instante.weekday(), instante.hour] += 1
    estados = Counter(_estado_sesion(grupo) for grupo in por_sesion.values())
    total = len(por_sesion)
    distribucion = [
        Distribucion(
            id=clave, nombre=nombre, cantidad=estados[clave], porcentaje=round(estados[clave] * 100 / total, 1)
        )
        for clave, nombre in ESTADOS
        if estados[clave] and total
    ]
    sin_guardado = sorted((d for d in distribucion if d.id != "guardado"), key=lambda d: (-d.cantidad, d.id))
    base_pareto = sum(d.cantidad for d in sin_guardado)
    acumuladas = 0
    pareto = []
    for grupo in sin_guardado:
        acumuladas += grupo.cantidad
        pareto.append(
            Pareto(
                nombre=grupo.nombre,
                cantidad=grupo.cantidad,
                porcentaje=round(grupo.cantidad * 100 / base_pareto, 1),
                acumulado=round(acumuladas * 100 / base_pareto, 1),
            )
        )
    dispersion = []
    for grupo in por_sesion.values():
        consultas = [e for e in sorted(grupo, key=_momento) if e["tipo"] == "busqueda_iniciada"]
        ultima = consultas[-1] if consultas else {}
        if isinstance(ultima.get("dias"), (int, float)) and isinstance(ultima.get("presupuesto"), (int, float)):
            dispersion.append(PuntoDispersion(dias=ultima["dias"], presupuesto=ultima["presupuesto"]))
    return AnalisisGerencial(
        distribucion=distribucion,
        embudo=_embudo(por_sesion),
        pareto=pareto,
        mapa_calor=[
            CeldaCalor(dia=dia, hora=hora, acciones=calor[dia, hora]) for dia in range(7) for hora in range(24)
        ],
        latencia=resumen_latencia(eventos),
        correlacion=_correlacion(por_sesion),
        dispersion=dispersion,
        proyeccion=proyectar(serie, modo),
        nota=(
            "La distribución asigna cada sesión a una sola etapa: se prioriza guardado y después el mayor "
            "avance observado en el periodo. No confirma abandono. El Pareto describe sesiones sin guardado, "
            "no sus causas. El embudo exige observar los pasos en orden. Los ceros diarios son días sin "
            "eventos recibidos dentro del tramo observado; no garantizan que el servicio estuviera disponible."
        ),
    )
