"""
Genera docs/ejemplos/respuesta_ilustrativa.json: una respuesta completa del contrato,
con recursos reales del inventario pero un itinerario armado a mano.

No es salida del motor. Existe para que la app se pueda construir y probar contra
el contrato antes de que el motor esté conectado, con nombres, códigos y fichas
reales. Las pruebas validan este archivo contra dreemgo.contrato.Respuesta, así
que si el contrato cambia y el ejemplo no, CI falla.

Uso:  python docs/ejemplos/generar_respuesta_ilustrativa.py
"""

from __future__ import annotations

import json
from pathlib import Path

from dreemgo.contrato import Respuesta

FICHA = "https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha={}"
SALIDA = Path(__file__).with_name("respuesta_ilustrativa.json")


def recurso(codigo, nombre, categoria, tipo, subtipo, jerarquia, lat, lon, alt, ingreso="libre", tarifa=None):
    return {
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "tipo": tipo,
        "subtipo": subtipo,
        "jerarquia": jerarquia,
        "lat": lat,
        "lon": lon,
        "altitud_m": alt,
        "url_ficha": FICHA.format(codigo),
        "descripcion": None,
        "ingreso": ingreso,
        "tarifa_soles": tarifa,
    }


def parada(orden, rec, llegada, min_traslado, km, min_visita):
    return {
        "orden": orden,
        "recurso": rec,
        "llegada": llegada,
        "minutos_traslado": min_traslado,
        "km_desde_anterior": km,
        "minutos_visita": min_visita,
    }


CULT, NAT = "Manifestaciones culturales", "Sitios naturales"
ARQ = "Sitios arqueológicos"

caral = recurso(
    "1237", "Ciudad Sagrada de Caral", CULT, ARQ, "Zonas arqueológicas", 4, -10.89282, -77.52323, 349, "pagado", 20.0
)
vichama = recurso(
    "3486", "Sitio Arqueológico de Vichama", CULT, ARQ, "Templos", 3, -11.03016, -77.62998, 27, "pagado", 20.0
)
paramonga = recurso("1298", "Fortaleza de Paramonga", CULT, ARQ, "Templos", 3, -10.65318, -77.84139, 15, "pagado", 15.0)
faraon = recurso("1238", "Playa La Isla del Faraón", NAT, "Costas", "Playas", 2, -10.80999, -77.75031, 0)
don_martin = recurso(
    "2054",
    "Isla Don Martín · Reserva Nacional de Islas, Islotes y Puntas Guaneras",
    NAT,
    "Costas",
    "Islas",
    2,
    -11.01879,
    -77.67103,
    0,
)
caleta_vidal = recurso("11108", "Playa Caleta Vidal", NAT, "Costas", "Playas", 2, -10.86174, -77.70484, 0)

huarco = recurso("3899", "Complejo Arqueológico El Huarco", CULT, ARQ, "Templos", 2, -13.0306, -76.48692, 28)
incahuasi = recurso("1854", "Sitio Arqueológico de Incahuasi", CULT, ARQ, "Templos", 2, -13.02361, -76.17668, 375)
muelle = recurso(
    "3495", "Muelle de Cerro Azul", CULT, "Arquitectura y espacios urbanos", "Muelles", 2, -13.0272, -76.48325, 0
)
montalvan = recurso(
    "12068",
    "Casa Hacienda Montalván",
    CULT,
    "Lugares históricos",
    "Casas haciendas",
    2,
    -13.07866,
    -76.39121,
    34,
    "pagado",
    2.0,
)

plaza_pozuzo = recurso(
    "11196",
    "Plaza Los Colonos · Pozuzo",
    CULT,
    "Arquitectura y espacios urbanos",
    "Plazas",
    3,
    -10.07084,
    -75.55075,
    737,
)
museo = recurso(
    "11365", "Museo Schafferer", CULT, "Museos y otros", "Casas museo", 2, -10.06814, -75.5512, 748, "pagado", 4.0
)
puente = recurso(
    "11604",
    "Puente Emperador Guillermo I · Pozuzo",
    CULT,
    "Arquitectura y espacios urbanos",
    "Puentes",
    2,
    -10.06811,
    -75.54962,
    740,
)
pozas = recurso(
    "11842",
    "Pozas de Agua y Sal · Pozuzo",
    NAT,
    "Manantiales",
    "Manantiales",
    2,
    -10.01248,
    -75.36143,
    714,
    "pagado",
    5.0,
)

LIMA_COSTA = {
    "mes": 7,
    "veredicto": "viable",
    "lluvia_mm": 0.6,
    "dias_con_lluvia": 0.4,
    "horas_sol": 2.1,
    "temp_min_c": 15.2,
    "temp_max_c": 19.8,
    "explicacion": "Julio casi no tiene lluvia, pero es invierno en la costa: cielo cubierto casi todo el "
    "día y garúa por las mañanas.",
    "mejores_meses": [2, 3, 1, 4, 12],
}

respuesta = {
    "version_contrato": "1.0",
    "version_datos": "ejemplo",
    "consulta": {
        "origen": "lima",
        "mes": 7,
        "fecha_inicio": None,
        "dias": 4,
        "intereses": ["historia", "naturaleza"],
        "presupuesto": 700,
        "altitud_max": 3500,
        "sorpresa": False,
    },
    "rutas": [
        {
            "polo": {
                "id": 70,
                "nombre": "Norte Chico · Huacho, Supe y Caral",
                "region": "Lima",
                "regiones": ["Lima"],
                "base": {"nombre": "Huacho", "lat": -11.1067, "lon": -77.6050, "altitud_m": 30},
                "recursos": 44,
                "fuera_del_circuito": False,
            },
            "puntaje": 0.81,
            "motivos": [
                "Caral, patrimonio de jerarquía 4, a 1 h 15 de la base",
                "Tres sitios arqueológicos de jerarquía 3 o 4 en el mismo polo",
                "Sin lluvia en julio",
            ],
            "estacionalidad": LIMA_COSTA,
            "traslado": {
                "desde": "Lima",
                "horas": 2.7,
                "dias_de_viaje": 0,
                "acceso": "terrestre",
                "fuente": "red_vial",
            },
            "dias": [
                {
                    "numero": 1,
                    "fecha": None,
                    "tipo": "ida_y_visita",
                    "horas": 7.6,
                    "km": 171.0,
                    "nota": "Salida de Lima a las 07:00; 2 h 40 por la Panamericana Norte.",
                    "paradas": [
                        parada(1, vichama, "09:50", 160, 148.0, 90),
                        parada(2, don_martin, "11:40", 20, 9.5, 45),
                    ],
                },
                {
                    "numero": 2,
                    "fecha": None,
                    "tipo": "visita",
                    "horas": 7.8,
                    "km": 118.0,
                    "paradas": [parada(1, caral, "09:15", 75, 44.0, 180), parada(2, faraon, "13:45", 90, 38.0, 90)],
                },
                {
                    "numero": 3,
                    "fecha": None,
                    "tipo": "visita",
                    "horas": 6.9,
                    "km": 142.0,
                    "paradas": [
                        parada(1, paramonga, "09:35", 95, 61.0, 90),
                        parada(2, caleta_vidal, "12:05", 60, 23.0, 75),
                    ],
                },
                {
                    "numero": 4,
                    "fecha": None,
                    "tipo": "visita_y_vuelta",
                    "horas": 3.1,
                    "km": 150.0,
                    "nota": "Mañana libre en Huacho y regreso a Lima: 2 h 40.",
                    "paradas": [],
                },
            ],
            "costo": {
                "p20": 486,
                "p50": 548,
                "p80": 631,
                "desglose": {"transporte": 118, "alojamiento": 210, "alimentacion": 165, "entradas": 55},
                "dentro_del_presupuesto": True,
                "exceso": None,
                "supuestos": [
                    "Bus interprovincial y colectivos locales",
                    "Hospedaje económico en Huacho, 3 noches",
                    "Tarifas de entrada de la ficha oficial",
                ],
            },
            "eventos": [],
            "avisos": [],
            "indicadores": {
                "paradas": 6,
                "jerarquia_media": 2.7,
                "paradas_jerarquia_alta": 3,
                "altitud_max_m": 349,
                "km_total": 581.0,
                "valor_capturado": 0.83,
            },
        },
        {
            "polo": {
                "id": 105,
                "nombre": "Lunahuaná y Cañete",
                "region": "Lima",
                "regiones": ["Lima"],
                "base": {"nombre": "Lunahuaná", "lat": -12.9611, "lon": -76.1392, "altitud_m": 470},
                "recursos": 38,
                "fuera_del_circuito": False,
            },
            "puntaje": 0.64,
            "motivos": [
                "Valle de Cañete: bodegas, sitios arqueológicos y costa en un solo polo",
                "Más sol que la costa en invierno: el valle queda sobre la neblina",
            ],
            "estacionalidad": {
                **LIMA_COSTA,
                "lluvia_mm": 0.3,
                "horas_sol": 4.6,
                "temp_min_c": 13.9,
                "temp_max_c": 23.4,
                "explicacion": "Julio seco. El valle alto de Cañete suele quedar sobre la neblina "
                "costera: más horas de sol que Lima.",
            },
            "traslado": {
                "desde": "Lima",
                "horas": 3.4,
                "dias_de_viaje": 0,
                "acceso": "terrestre",
                "fuente": "red_vial",
            },
            "dias": [
                {
                    "numero": 1,
                    "fecha": None,
                    "tipo": "ida_y_visita",
                    "horas": 6.5,
                    "km": 214.0,
                    "paradas": [parada(1, huarco, "10:30", 210, 146.0, 60), parada(2, muelle, "11:35", 5, 0.8, 30)],
                },
                {
                    "numero": 2,
                    "fecha": None,
                    "tipo": "visita",
                    "horas": 5.2,
                    "km": 88.0,
                    "paradas": [
                        parada(1, montalvan, "09:05", 65, 38.0, 75),
                        parada(2, incahuasi, "11:35", 75, 39.0, 60),
                    ],
                },
                {
                    "numero": 3,
                    "fecha": None,
                    "tipo": "visita",
                    "horas": 2.0,
                    "km": 12.0,
                    "nota": "Día libre en Lunahuaná: canotaje y bodegas del valle.",
                    "paradas": [],
                },
                {"numero": 4, "fecha": None, "tipo": "visita_y_vuelta", "horas": 3.4, "km": 182.0, "paradas": []},
            ],
            "costo": {
                "p20": 522,
                "p50": 596,
                "p80": 684,
                "desglose": {"transporte": 96, "alojamiento": 255, "alimentacion": 225, "entradas": 20},
                "dentro_del_presupuesto": True,
                "exceso": None,
                "supuestos": ["Hospedaje en Lunahuaná, 3 noches", "Colectivo Cañete-Lunahuaná"],
            },
            "eventos": [],
            "avisos": [
                {
                    "tipo": "datos",
                    "nivel": "info",
                    "mensaje": "Dos de las cuatro paradas piden permiso previo para entrar, según la ficha.",
                }
            ],
            "indicadores": {
                "paradas": 4,
                "jerarquia_media": 2.0,
                "paradas_jerarquia_alta": 0,
                "altitud_max_m": 375,
                "km_total": 496.0,
                "valor_capturado": 0.62,
            },
        },
        {
            "polo": {
                "id": 201,
                "nombre": "Pozuzo",
                "region": "Pasco",
                "regiones": ["Pasco"],
                "base": {"nombre": "Pozuzo", "lat": -10.0708, "lon": -75.5507, "altitud_m": 737},
                "recursos": 14,
                "fuera_del_circuito": True,
            },
            "puntaje": 0.58,
            "motivos": [
                "Colonia austroalemana en la selva alta, fuera del circuito habitual",
                "Temporada seca en julio",
                "El 25 de julio es el Día del Colono",
            ],
            "estacionalidad": {
                "mes": 7,
                "veredicto": "viable",
                "lluvia_mm": 38.0,
                "dias_con_lluvia": 5.1,
                "horas_sol": 5.8,
                "temp_min_c": 16.4,
                "temp_max_c": 29.1,
                "explicacion": "Julio es temporada seca en la selva alta: lluvias cortas y caminos en mejor estado.",
                "mejores_meses": [7, 8, 6, 9],
            },
            "traslado": {
                "desde": "Lima",
                "horas": 12.5,
                "dias_de_viaje": 2,
                "acceso": "terrestre",
                "fuente": "red_vial",
            },
            "dias": [
                {
                    "numero": 1,
                    "fecha": None,
                    "tipo": "ida",
                    "horas": 12.5,
                    "km": 504.0,
                    "nota": "Lima → La Oroya → La Merced → Oxapampa → Pozuzo.",
                    "paradas": [],
                },
                {
                    "numero": 2,
                    "fecha": None,
                    "tipo": "visita",
                    "horas": 5.9,
                    "km": 4.0,
                    "paradas": [
                        parada(1, plaza_pozuzo, "08:05", 5, 0.3, 45),
                        parada(2, museo, "08:55", 5, 0.4, 75),
                        parada(3, puente, "10:15", 5, 0.2, 30),
                    ],
                },
                {
                    "numero": 3,
                    "fecha": None,
                    "tipo": "visita",
                    "horas": 4.6,
                    "km": 42.0,
                    "paradas": [parada(1, pozas, "09:05", 65, 21.0, 120)],
                },
                {"numero": 4, "fecha": None, "tipo": "vuelta", "horas": 12.5, "km": 504.0, "paradas": []},
            ],
            "costo": {
                "p20": 690,
                "p50": 812,
                "p80": 951,
                "desglose": {"transporte": 260, "alojamiento": 240, "alimentacion": 300, "entradas": 12},
                "dentro_del_presupuesto": False,
                "exceso": 112,
                "supuestos": ["Bus Lima-La Merced y colectivo a Pozuzo", "Hospedaje en Pozuzo, 3 noches"],
            },
            "eventos": [
                {
                    "id": "mincetur-11287",
                    "nombre": "Aniversario de Pozuzo · Día del Colono",
                    "tipo": "Fiestas tradicionales",
                    "fecha_inicio": "2026-07-25",
                    "fecha_fin": "2026-07-25",
                    "precision_fecha": "aproximada",
                    "distrito": "Pozuzo",
                    "provincia": "Oxapampa",
                    "region": "Pasco",
                    "fuente": "mincetur",
                    "publicado_por": None,
                    "url": FICHA.format("11287"),
                }
            ],
            "avisos": [
                {
                    "tipo": "dias",
                    "nivel": "advertencia",
                    "mensaje": "Dos de los cuatro días se van en la carretera. Con 6 días el viaje rinde el doble.",
                },
                {
                    "tipo": "presupuesto",
                    "nivel": "advertencia",
                    "mensaje": "Te pasas en unos S/ 112 del presupuesto, sobre el costo típico.",
                },
            ],
            "indicadores": {
                "paradas": 4,
                "jerarquia_media": 2.25,
                "paradas_jerarquia_alta": 1,
                "altitud_max_m": 748,
                "km_total": 1054.0,
                "valor_capturado": 0.57,
            },
        },
    ],
    "sin_resultado": None,
    "atribucion": [
        "Inventario Nacional de Recursos Turísticos · MINCETUR · ODC-BY",
        "Clima: Open-Meteo.com, sobre ERA5 de Copernicus · CC BY 4.0",
        "Red vial: © colaboradores de OpenStreetMap · ODbL",
    ],
}

if __name__ == "__main__":
    validada = Respuesta.model_validate(respuesta)
    SALIDA.write_text(
        json.dumps(validada.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"escrito y validado: {SALIDA}")
