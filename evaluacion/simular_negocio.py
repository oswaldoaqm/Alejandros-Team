"""Escenario comercial ficticio de 300 sesiones sobre el kit de DreemGO.

El recomendador real no confirma aceptaciones ni procesa pagos. Este archivo
simula esas decisiones para ensayar un tablero de negocio, conservando aparte
la telemetría original. Uso: python -m evaluacion.simular_negocio
"""

from __future__ import annotations

import csv
import json
import random
from datetime import date
from pathlib import Path

from evaluacion import simular_actividad

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "simulacion" / "negocio_300.json"
COLUMNAS = (
    "usuario_id",
    "sesion",
    "fecha_local",
    "hora_local",
    "canal_simulado",
    "origen",
    "intereses",
    "dias",
    "presupuesto_viaje",
    "visito",
    "interactuo",
    "busco",
    "vio_propuestas",
    "propuestas_mostradas",
    "abrio_propuesta",
    "propuesta_abierta",
    "polo_A",
    "polo_B",
    "acepto_propuesta",
    "propuesta_aceptada",
    "compra_simulada",
    "importe_simulado",
    "costo_variable_simulado",
    "guardo",
    "compartio",
    "error_consulta",
    "duracion_ms",
    "etapa_final",
)
CANALES = ("Directo", "Redes sociales", "Búsqueda", "Referidos")
PESOS_CANALES = (38, 32, 20, 10)
PROBABILIDADES = {
    "abrir_A_entre_A_B": 0.55,
    "aceptar_despues_de_abrir": 0.55,
    "comprar_despues_de_aceptar": 0.42,
}
ECONOMIA = {
    "ingreso_por_compra_simulada_soles": 20,
    "costo_variable_por_compra_simulada_soles": 5,
    "costo_fijo_periodo_soles": 500,
    "presupuesto_marketing_periodo_soles": 300,
}


def _primeros_dos_polos() -> tuple[dict[int, tuple[int, int]], str]:
    """A y B corresponden al primer y segundo puesto del motor existente."""
    polos, version = simular_actividad._leer_polos()
    return {consulta: (lista[0], lista[1]) for consulta, lista in polos.items()}, version


def generar(semilla: int = 73) -> dict:
    """Genera siempre 300 registros, con un único usuario ficticio por sesión."""
    actividad = simular_actividad.generar(sesiones=300, semilla=42, fecha_base=date(2026, 11, 10), dias_historia=28)
    polos, version = _primeros_dos_polos()
    azar = random.Random(semilla)
    eventos_por_sesion: dict[str, set[str]] = {}
    for evento in actividad["eventos"]:
        eventos_por_sesion.setdefault(evento["sesion"], set()).add(evento["tipo"])

    registros = []
    for usuario in actividad["usuarios"]:
        acciones = eventos_por_sesion[usuario["sesion"]]
        interactuo = "formulario_abierto" in acciones
        busco = "busqueda_iniciada" in acciones
        vio = usuario["resultados"] == 3
        abrio = "itinerario_abierto" in acciones
        # Las dos primeras alternativas del motor constituyen A y B en este
        # ejercicio. Es una comparación de opciones, no una prueba aleatoria.
        propuesta = ("A" if azar.random() < PROBABILIDADES["abrir_A_entre_A_B"] else "B") if abrio else None
        acepto = abrio and azar.random() < PROBABILIDADES["aceptar_despues_de_abrir"]
        compro = acepto and azar.random() < PROBABILIDADES["comprar_despues_de_aceptar"]
        if compro:
            etapa = "compra_simulada"
        elif acepto:
            etapa = "aceptacion_sin_compra"
        elif abrio:
            etapa = "propuesta_abierta_sin_aceptacion"
        elif vio:
            etapa = "propuestas_sin_apertura"
        elif "error_consulta" in acciones:
            etapa = "error_consulta"
        elif busco:
            etapa = "respuesta_sin_propuestas"
        elif interactuo:
            etapa = "formulario_sin_busqueda"
        else:
            etapa = "solo_visita"
        polo_a, polo_b = polos[usuario["consulta_kit"]]
        registro = {
            "usuario_id": usuario["usuario_ficticio"],
            "sesion": usuario["sesion"],
            "fecha_local": usuario["fecha_local"],
            "hora_local": usuario["hora_local"],
            "canal_simulado": azar.choices(CANALES, weights=PESOS_CANALES)[0],
            "origen": usuario["origen"],
            "intereses": usuario["intereses"],
            "dias": usuario["dias"],
            "presupuesto_viaje": usuario.get("presupuesto"),
            "visito": True,
            "interactuo": interactuo,
            "busco": busco,
            "vio_propuestas": vio,
            "propuestas_mostradas": 2 if vio else 0,
            "abrio_propuesta": abrio,
            "propuesta_abierta": propuesta,
            "polo_A": polo_a if vio else None,
            "polo_B": polo_b if vio else None,
            "acepto_propuesta": acepto,
            "propuesta_aceptada": propuesta if acepto else None,
            "compra_simulada": compro,
            "importe_simulado": ECONOMIA["ingreso_por_compra_simulada_soles"] if compro else 0,
            "costo_variable_simulado": (ECONOMIA["costo_variable_por_compra_simulada_soles"] if compro else 0),
            "guardo": usuario["guardo"],
            "compartio": usuario["compartio"],
            "error_consulta": "error_consulta" in acciones,
            "duracion_ms": usuario["duracion_ms"],
            "etapa_final": etapa,
        }
        registros.append(registro)

    return {
        "meta": {
            "tipo": "simulacion_comercial",
            "etiqueta": "SIMULACIÓN COMERCIAL: usuarios, aceptaciones y compras ficticios",
            "usuarios_ficticios": 300,
            "sesiones_por_usuario": 1,
            "fecha_inicio": actividad["meta"]["fecha_inicio"],
            "fecha_fin": actividad["meta"]["fecha_base"],
            "zona_horaria": "America/Lima",
            "semilla_actividad": 42,
            "semilla_negocio": semilla,
            "fuente_consultas": "evaluacion/consultas.csv",
            "fuente_alternativas": "data/evaluacion/clave.csv (puestos 1 y 2 del motor)",
            "version_datos_motor": version,
            "canales_ficticios": dict(zip(CANALES, PESOS_CANALES, strict=True)),
            "probabilidades_comerciales_supuestas": PROBABILIDADES,
            "supuestos_economicos": ECONOMIA,
            "definiciones": {
                "interactuo": "Abrió el formulario de planificación.",
                "vio_propuestas": "Recibió rutas del motor; A y B son las dos primeras.",
                "acepto_propuesta": "Decisión afirmativa simulada después de abrir A o B.",
                "compra_simulada": "Operación ficticia posterior a la aceptación; no hubo pago.",
                "canal_simulado": "Canal inventado para practicar análisis de marketing.",
            },
        },
        "registros": registros,
    }


def guardar(datos: dict, ruta: Path = SALIDA) -> tuple[Path, Path]:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    csv_ruta = ruta.with_suffix(".csv")
    with csv_ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS, delimiter=";")
        escritor.writeheader()
        for registro in datos["registros"]:
            escritor.writerow(
                {
                    **registro,
                    "intereses": "|".join(registro["intereses"]),
                }
            )
    return ruta, csv_ruta


def main() -> None:
    datos = generar()
    ruta, csv_ruta = guardar(datos)
    conteo = sum(r["compra_simulada"] for r in datos["registros"])
    print(f"SIMULACIÓN COMERCIAL: 300 sesiones, {conteo} compras ficticias; {ruta}; {csv_ruta}")


if __name__ == "__main__":
    main()
