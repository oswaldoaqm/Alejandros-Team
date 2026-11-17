"""Genera actividad de ejemplo para enseñar el panel de DreemGO.

Las sesiones y acciones de este archivo son inventadas para una demostración. Las
consultas y los polos proceden del kit de evaluación del equipo; no representan
personas, compras, reservas ni tráfico observado.

Uso desde la raíz del proyecto::

    python -m evaluacion.simular_actividad
    python -m evaluacion.simular_actividad --sesiones 200 --semilla 42 --fecha-base 2026-11-10 --dias-historia 28
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CONSULTAS = RAIZ / "evaluacion" / "consultas.csv"
CLAVE = RAIZ / "data" / "evaluacion" / "clave.csv"
SALIDA = RAIZ / "data" / "simulacion" / "actividad_200.json"
EMPAQUETADA = RAIZ / "dreemgo" / "datos" / "actividad_200_simulacion.json"
HORA_PERU = timezone(timedelta(hours=-5), name="America/Lima")
SUPUESTOS = {
    "abrir_formulario": 0.92,
    "buscar_dado_formulario": 0.86,
    "error_dada_busqueda": 0.06,
    "sin_resultados_dada_respuesta": 0.08,
    "abrir_itinerario_dado_resultado": 0.79,
    "guardar_dado_itinerario": 0.42,
    "compartir_dado_itinerario": 0.24,
    "imprimir_dado_itinerario": 0.11,
    "respuesta_lenta": 0.08,
}
CAMPOS_CSV = (
    "sesion",
    "tipo",
    "instante",
    "origen",
    "polo",
    "intereses",
    "dias",
    "mes",
    "presupuesto",
    "resultados",
    "duracion_ms",
    "codigo_error",
)
TIPOS = {
    "sesion_iniciada",
    "formulario_abierto",
    "busqueda_iniciada",
    "busqueda_resultado",
    "itinerario_abierto",
    "viaje_guardado",
    "viaje_compartido",
    "viaje_impreso",
    "error_consulta",
}
CAMPOS_USUARIOS = (
    "usuario_ficticio",
    "sesion",
    "consulta_kit",
    "fecha_local",
    "hora_local",
    "origen",
    "mes",
    "dias",
    "intereses",
    "presupuesto",
    "etapa_final",
    "ultima_accion",
    "resultados",
    "duracion_ms",
    "acciones",
    "guardo",
    "compartio",
    "imprimio",
)


def _leer_consultas() -> list[dict[str, str]]:
    with CONSULTAS.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter=";"))
    if len(filas) != 40:
        raise ValueError("El kit de evaluación ya no contiene las 40 consultas esperadas.")
    return filas


def _leer_polos() -> tuple[dict[int, list[int]], str]:
    """Los tres polos que el motor propuso para cada consulta del kit."""
    with CLAVE.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter=";"))
    polos: dict[int, list[tuple[int, int]]] = {}
    versiones = set()
    for fila in filas:
        if not fila["puesto_motor"]:
            continue
        consulta = int(fila["consulta"])
        polos.setdefault(consulta, []).append((int(fila["puesto_motor"]), int(fila["polo"])))
        versiones.add(fila["version_datos"])
    ordenados = {consulta: [polo for _, polo in sorted(lista)] for consulta, lista in polos.items()}
    if len(ordenados) != 40 or any(len(lista) != 3 for lista in ordenados.values()) or len(versiones) != 1:
        raise ValueError("El kit de evaluación no tiene tres propuestas del motor por consulta y una versión.")
    return ordenados, versiones.pop()


def generar(
    sesiones: int = 200,
    semilla: int = 42,
    fecha_base: date = date(2026, 11, 10),
    dias_historia: int = 28,
) -> dict:
    """Un usuario ficticio por sesión durante un periodo histórico completo.

    Las probabilidades son decisiones para mostrar el embudo en la demo; no son
    estimaciones del comportamiento de los viajeros de DreemGO.
    """
    if sesiones < 1 or sesiones > 10_000:
        raise ValueError("La simulación admite entre 1 y 10 000 sesiones.")
    if dias_historia < 1 or dias_historia > 365:
        raise ValueError("El historial admite entre 1 y 365 días.")
    consultas = _leer_consultas()
    polos, version = _leer_polos()
    aleatorio = random.Random(semilla)
    eventos: list[dict] = []
    usuarios: list[dict] = []
    # Hay al menos una sesión por día si la muestra alcanza. Después se reparte
    # el resto al azar; no se programa una tendencia para favorecer la proyección.
    dias = list(range(min(sesiones, dias_historia)))
    dias.extend(aleatorio.randrange(dias_historia) for _ in range(sesiones - len(dias)))
    aleatorio.shuffle(dias)

    for numero in range(sesiones):
        consulta = consultas[numero % len(consultas)] if numero < len(consultas) else aleatorio.choice(consultas)
        id_consulta = int(consulta["id"])
        sesion = str(uuid.uuid5(uuid.NAMESPACE_URL, f"dreemgo-demo-{semilla}-{numero}"))
        dia = fecha_base - timedelta(days=dias[numero])
        hora = aleatorio.choices(range(8, 23), weights=[1, 1, 2, 2, 3, 3, 2, 2, 2, 3, 4, 5, 5, 4, 2])[0]
        momento = datetime(
            dia.year,
            dia.month,
            dia.day,
            hora,
            aleatorio.randrange(60),
            aleatorio.randrange(60),
            tzinfo=HORA_PERU,
        )
        contexto = {
            "origen": consulta["origen"],
            "mes": int(consulta["mes"]) if consulta["mes"] else int(consulta["fecha_inicio"][5:7]),
            "dias": int(consulta["dias"]),
            "intereses": [interes for interes in consulta["intereses"].split("|") if interes],
        }
        if consulta["presupuesto"]:
            contexto["presupuesto"] = int(consulta["presupuesto"])
        usuario = {
            "usuario_ficticio": f"U{numero + 1:04d}",
            "sesion": sesion,
            "consulta_kit": id_consulta,
            "fecha_local": dia.isoformat(),
            "hora_local": hora,
            **contexto,
            "etapa_final": "solo_visita",
            "ultima_accion": "sesion_iniciada",
            "resultados": None,
            "duracion_ms": None,
            "acciones": 0,
            "guardo": False,
            "compartio": False,
            "imprimio": False,
        }
        usuarios.append(usuario)

        def añadir(tipo: str, sesion_actual: str = sesion, usuario_actual: dict = usuario, **campos: object) -> None:
            nonlocal momento
            if tipo not in TIPOS:
                raise ValueError(f"Tipo de evento desconocido: {tipo}")
            eventos.append({"sesion": sesion_actual, "tipo": tipo, "instante": momento.isoformat(), **campos})
            usuario_actual["ultima_accion"] = tipo
            usuario_actual["acciones"] += 1
            momento += timedelta(seconds=aleatorio.randrange(4, 38))

        añadir("sesion_iniciada")
        if aleatorio.random() >= SUPUESTOS["abrir_formulario"]:
            continue  # abrió la página, pero no el formulario
        añadir("formulario_abierto")
        usuario["etapa_final"] = "formulario_sin_busqueda"
        if aleatorio.random() >= SUPUESTOS["buscar_dado_formulario"]:
            continue  # dejó el formulario antes de buscar
        añadir("busqueda_iniciada", **contexto)
        if aleatorio.random() < SUPUESTOS["error_dada_busqueda"]:
            añadir("error_consulta", codigo_error=aleatorio.choice(["503", "red", "tiempo_agotado"]))
            usuario["etapa_final"] = "error_consulta"
            continue
        # La dispersión y la cola lenta son supuestos didácticos, independientes
        # del rendimiento medido del motor y del presupuesto de la consulta.
        latencia = int(aleatorio.lognormvariate(6.5, 0.55))
        if aleatorio.random() < SUPUESTOS["respuesta_lenta"]:
            latencia += aleatorio.randrange(1800, 4501)
        latencia = max(100, min(latencia, 10_000))
        resultados = 0 if aleatorio.random() < SUPUESTOS["sin_resultados_dada_respuesta"] else 3
        añadir("busqueda_resultado", resultados=resultados, duracion_ms=latencia, **contexto)
        usuario["resultados"] = resultados
        usuario["duracion_ms"] = latencia
        usuario["etapa_final"] = "sin_resultados" if resultados == 0 else "resultado_sin_apertura"
        if resultados == 0 or aleatorio.random() >= SUPUESTOS["abrir_itinerario_dado_resultado"]:
            continue
        polo = aleatorio.choice(polos[id_consulta])
        añadir("itinerario_abierto", polo=polo, **contexto)
        usuario["etapa_final"] = "itinerario_sin_guardado"
        if aleatorio.random() < SUPUESTOS["guardar_dado_itinerario"]:
            añadir("viaje_guardado", polo=polo)
            usuario["guardo"] = True
            usuario["etapa_final"] = "guardado"
        if aleatorio.random() < SUPUESTOS["compartir_dado_itinerario"]:
            añadir("viaje_compartido", polo=polo)
            usuario["compartio"] = True
        if aleatorio.random() < SUPUESTOS["imprimir_dado_itinerario"]:
            añadir("viaje_impreso", polo=polo)
            usuario["imprimio"] = True

    eventos.sort(key=lambda evento: (evento["instante"], evento["sesion"]))
    return {
        "meta": {
            "tipo": "simulacion",
            "etiqueta": "SIMULACIÓN: no son usuarios ni ventas reales",
            "sesiones": sesiones,
            "usuarios_ficticios": sesiones,
            "sesiones_por_usuario": 1,
            "semilla": semilla,
            "fecha_base": fecha_base.isoformat(),
            "fecha_inicio": (fecha_base - timedelta(days=dias_historia - 1)).isoformat(),
            "dias_historia": dias_historia,
            "zona_horaria": "America/Lima",
            "supuestos_probabilidad": SUPUESTOS.copy(),
            "horario_local": "08:00–22:59, con mayor peso de sesiones al mediodía y al anochecer",
            "latencia_simulada": "Lognormal(mu=6.5, sigma=0.55) ms; 8% añade 1800–4500 ms; rango 100–10000 ms",
            "fuente_consultas": "evaluacion/consultas.csv",
            "fuente_polos": "data/evaluacion/clave.csv (puesto_motor)",
            "version_datos": version,
            "nota": (
                "Las tasas del recorrido son supuestos para demostrar el panel, "
                "no resultados de una prueba con personas ni de una prueba de carga. "
                "Las respuestas sin rutas y los errores son escenarios ficticios; "
                "no se volvió a ejecutar el motor para medirlos."
            ),
        },
        "eventos": eventos,
        "usuarios": usuarios,
    }


def guardar(salida: dict, ruta_json: Path, ruta_empaquetada: Path = EMPAQUETADA) -> tuple[Path, Path]:
    """Exporta eventos y una fila por usuario para ejercicios de clase."""
    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    ruta_empaquetada.parent.mkdir(parents=True, exist_ok=True)
    contenido = (json.dumps(salida, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    ruta_json.write_bytes(contenido)
    ruta_empaquetada.write_bytes(contenido)
    csv_ruta = ruta_json.with_suffix(".csv")
    usuarios_ruta = ruta_json.with_name(f"usuarios_{salida['meta']['usuarios_ficticios']}.csv")
    for ruta, campos, filas in (
        (csv_ruta, CAMPOS_CSV, salida["eventos"]),
        (usuarios_ruta, CAMPOS_USUARIOS, salida["usuarios"]),
    ):
        with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos, delimiter=";", extrasaction="ignore")
            escritor.writeheader()
            for fila in filas:
                escritor.writerow({**fila, "intereses": "|".join(fila.get("intereses", []))})
    return csv_ruta, usuarios_ruta


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera sesiones ficticias para el panel de DreemGO.")
    parser.add_argument("--sesiones", type=int, default=200)
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--fecha-base", type=date.fromisoformat, default=date(2026, 11, 10))
    parser.add_argument("--dias-historia", type=int, default=28)
    parser.add_argument("--salida", type=Path, default=SALIDA)
    args = parser.parse_args()
    salida = generar(args.sesiones, args.semilla, args.fecha_base, args.dias_historia)
    csv_ruta, usuarios_ruta = guardar(salida, args.salida)
    print(
        f"SIMULACIÓN: {salida['meta']['sesiones']} sesiones, {len(salida['eventos'])} eventos "
        f"en {args.salida}, {csv_ruta} y {usuarios_ruta}"
    )


if __name__ == "__main__":
    main()
