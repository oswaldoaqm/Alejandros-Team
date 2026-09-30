"""Maestro v3: reglas de resumen, intereses, duración, polos y la construcción completa."""

import csv
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dreemgo.contrato import Interes
from pipeline.fichas import leer_archivo
from pipeline.inventario import leer_inventario
from pipeline.maestro import (
    COLUMNAS,
    DIAMETRO_MAX,
    REFERENCIA,
    ReglasDuracion,
    ReglasIntereses,
    asignar_polos,
    construir,
    descripcion_corta,
    distancia_a_su_distrito,
    distancia_efectiva_km,
    nombre_legible,
    resumen,
    resumen_acceso,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"


def ficha(codigo: int):
    return leer_archivo(FIXTURES / "fichas" / f"{codigo}.html.gz")


@pytest.mark.parametrize(
    ("nombre", "legible"),
    [
        ("Festividad Del Señor De Los Temblores", "Festividad del Señor de los Temblores"),
        ("Festival De La Uva, Vino Y Canotaje De Lunahuaná", "Festival de la Uva, Vino y Canotaje de Lunahuaná"),
        ("Playa La Mina", "Playa La Mina"),  # el artículo es parte del nombre
        ("Camino A La Laguna", "Camino a la Laguna"),
        ("Museo De Sitio UNAS De Tingo María", "Museo de Sitio UNAS de Tingo María"),  # la sigla se queda
        ("El Tambo", "El Tambo"),
    ],
)
def test_nombre_legible(nombre, legible):
    assert nombre_legible(nombre) == legible


def test_descripcion_corta_corta_en_una_oracion():
    texto = "Primera oración corta. " + "Segunda oración bastante más larga que la anterior. " * 10
    corta = descripcion_corta(texto, limite=80)
    assert corta == "Primera oración corta. Segunda oración bastante más larga que la anterior."
    assert descripcion_corta("Breve.", limite=80) == "Breve."
    assert descripcion_corta("palabra " * 50, limite=40).endswith("…")
    assert descripcion_corta(None) is None


def test_acceso_elige_el_recorrido_mas_rapido():
    acceso = resumen_acceso(ficha(1237).tramos)  # Caral: 295 min en minibús turístico, 270 en bus y combi
    assert acceso["recorridos"] == 2
    assert (acceso["acceso_min"], acceso["acceso_km"]) == (270, 196.4)
    assert (acceso["ultimo_medio"], acceso["ultimo_via"]) == ("Combi", "Afirmado")
    assert acceso["acceso_desde"] == "Lima/Lima/Independencia"
    assert (acceso["caminata_min"], acceso["acceso_acuatico"]) == (0, False)


def test_acceso_cuenta_la_caminata_final():
    acceso = resumen_acceso(ficha(22).tramos)  # Lauricocha: termina con 500 m a pie
    assert acceso["caminata_min"] == 9
    assert acceso["ultimo_medio"] == "A pie"


def test_acceso_sin_tramos():
    assert resumen_acceso(ficha(104).tramos)["recorridos"] == 0


def test_referencias_usan_los_intereses_del_contrato():
    with open(REFERENCIA / "intereses.csv", encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    assert {f["interes"] for f in filas} <= {i.value for i in Interes}
    assert {f["campo"] for f in filas} <= {"categoria", "tipo", "subtipo", "actividad", "excluir_subtipo"}


def test_intereses():
    reglas = ReglasIntereses.cargar()
    caral = ficha(1237)
    assert {"historia", "caminatas"} <= set(
        reglas.de(2, caral.tipo, caral.subtipo, [a.actividad for a in caral.actividades])
    )
    assert reglas.de(1, "Costas", "Playas", []) == ["playa"]  # una playa no es «naturaleza» por sí sola
    assert reglas.de(1, "Costas", "Playas", ["Observación de aves"]) == ["naturaleza", "playa"]
    assert reglas.de(5, "Fiestas", "Fiestas religiosas-patronales", []) == ["fiestas"]


def test_duracion_de_lo_especifico_a_lo_general():
    reglas = ReglasDuracion.cargar()
    assert reglas.de(2, "Museos y otros", "Museos") == (75, "referencia:subtipo")
    assert reglas.de(2, "Museos y otros", "Algo nuevo") == (60, "referencia:tipo")
    assert reglas.de(4, "Tipo nuevo", None) == (45, "referencia:categoria")
    assert reglas.de(3, "Gastronomía", "Platos Típicos") == (None, None)  # el folclore no se visita
    with open(REFERENCIA / "duracion_visita.csv", encoding="utf-8") as f:
        assert all(int(fila["minutos"]) > 0 for fila in csv.DictReader(f, delimiter=";"))


def test_distancia_a_su_distrito_detecta_el_punto_perdido():
    tabla = pd.DataFrame(
        {
            "region": ["Lima"] * 6,
            "provincia": ["Barranca"] * 6,
            "distrito": ["Supe"] * 6,
            "lat": [-10.80, -10.81, -10.82, -10.79, -10.80, -13.50],  # el último, 300 km al sur
            "lon": [-77.70, -77.71, -77.69, -77.70, -77.72, -76.00],
        }
    )
    distancia = distancia_a_su_distrito(tabla)
    assert distancia.iloc[:5].max() < 5
    assert distancia.iloc[5] > 300


def _tabla_polos(filas):
    return pd.DataFrame(
        filas, columns=["codigo", "categoria_num", "lat", "lon", "altitud_m", "coordenada_revisar"]
    ).astype({"coordenada_revisar": bool})


def test_asignar_polos():
    # Polo 1 alrededor de (-12, -77); polo 2 a unos 330 km al sur.
    v2 = pd.DataFrame(
        {
            "codigo": [1, 2, 3, 4, 5, 6],
            "lat_v2": [-12.00, -12.10, -12.20, -15.00, -15.10, -12.05],
            "lon_v2": [-77.00, -77.10, -77.00, -75.00, -75.10, -77.05],
            "alt_v2": [100.0, 120.0, 90.0, 500.0, 520.0, 110.0],
            "polo_v2": [1, 1, 1, 2, 2, 1],
        }
    )
    tabla = _tabla_polos(
        [
            (1, 1, -12.00, -77.00, 100, False),
            (2, 2, -12.10, -77.10, 120, False),
            (3, 2, -12.20, -77.00, 90, False),
            (4, 1, -15.00, -75.00, 500, False),
            (5, 1, -15.10, -75.10, 520, False),
            (6, 2, -13.50, -76.20, 300, False),  # estaba en el polo 1 y se movió 180 km
            (7, 2, -12.15, -77.05, 100, False),  # nuevo, dentro del polo 1
            (8, 5, -15.05, -75.05, 510, False),  # acontecimiento nuevo, dentro del polo 2
            (9, 1, -9.00, -78.50, 50, False),  # nuevo, lejos de todo
            (10, 2, -12.05, -77.05, 100, True),  # coordenada a revisar
        ]
    )
    resultado = asignar_polos(tabla, v2).set_index("codigo")
    assert resultado.loc[[1, 2, 3], "polo"].tolist() == [1, 1, 1]
    assert (resultado.loc[1, "polo_fuente"], resultado.loc[4, "polo_fuente"]) == ("v2", "v2")
    assert (resultado.loc[6, "polo"], resultado.loc[6, "polo_fuente"]) == (-1, "salio_de_su_polo")
    assert (resultado.loc[7, "polo"], resultado.loc[7, "polo_fuente"]) == (1, "asignado_v3")
    assert (resultado.loc[8, "polo"], resultado.loc[8, "polo_fuente"]) == (2, "asignado_v3")
    assert (resultado.loc[9, "polo"], resultado.loc[9, "polo_fuente"]) == (-1, "sin_polo_cercano")
    assert (resultado.loc[10, "polo"], resultado.loc[10, "polo_fuente"]) == (-1, "coordenada_revisar")


def test_asignar_polos_respeta_el_diametro():
    # Una fila de puntos cada 15 km hacia el este: el polo no puede crecer más allá de 80 km.
    lon = -77.0 + np.arange(12) * 0.1375  # ~15 km por paso a 12° S
    v2 = pd.DataFrame({"codigo": [0], "lat_v2": [-12.0], "lon_v2": [lon[0]], "alt_v2": [100.0], "polo_v2": [1]})
    tabla = _tabla_polos([(i, 1, -12.0, lon[i], 100, False) for i in range(12)])
    resultado = asignar_polos(tabla, v2)
    miembros = resultado.index[resultado["polo"] == 1]
    la, lo = np.full(len(miembros), -12.0), lon[miembros]
    alt = np.full(len(miembros), 100.0)
    diametro = distancia_efectiva_km(la[:, None], lo[:, None], alt[:, None], la[None, :], lo[None, :], alt[None, :])
    assert diametro.max() <= DIAMETRO_MAX
    assert (resultado["polo_fuente"] == "sin_polo_cercano").sum() > 0


def test_construir_con_la_muestra():
    inventario = leer_inventario(FIXTURES / "inventario_muestra.csv")
    fichas = {c: ficha(c) for c in (11, 22, 257, 1237, 11287)}
    v2 = pd.DataFrame(
        {
            "CODIGO DEL RECURSO": [1237, 257],
            "latitud": [-10.892818, -13.855618],
            "longitud": [-77.523228, -76.337225],
            "ALTITUD": [349.0, 99.0],
            "POLO": [70, 180],
        }
    )
    maestro = construir(inventario, fichas, v2).set_index("codigo")
    assert list(maestro.reset_index().columns) == COLUMNAS
    caral = maestro.loc[1237]
    assert (caral.nombre, caral.polo, caral.polo_fuente) == ("Ciudad Sagrada de Caral", 70, "v2")
    assert (caral.jerarquia, caral.altitud_m, caral.altitud_fuente, caral.altitud_dem_m) == (4, 350, "ficha", 349)
    assert (caral.tarifa_soles, caral.abre, caral.cierra) == (11, "10:00", "16:00")
    assert caral.dias == "lun|mar|mie|jue|vie|sab|dom"
    assert caral.es_parada and caral.visita_min == 90
    assert "historia" in caral.intereses.split("|")
    assert caral.url_ficha.endswith("cod_Ficha=1237")
    assert maestro.loc[11287, "motivo_no_parada"] == "acontecimiento"
    assert maestro.loc[364, "motivo_no_parada"] == "sin_ficha"  # su ficha no está en la muestra
    assert maestro.loc[11287, "coordenada"] == "sin_coordenada"
    assert maestro.loc[935, "distrito"] == "Quehue"
    datos = resumen(maestro.reset_index())
    assert datos["recursos"] == 9 and datos["con_ficha"] == 5
