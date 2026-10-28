"""Calendario de acontecimientos. Los textos son de fichas reales (código al lado)."""

import csv
from datetime import date

import pandas as pd
import pytest

from dreemgo.calendario import Regla
from pipeline.eventos import ANOTADOS, SANTORAL, evaluar, leer_fecha
from pipeline.maestro import PROCESADOS, REFERENCIA


def test_santoral_valido():
    with open(REFERENCIA / "santoral.csv", encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    assert len(filas) == len(SANTORAL) > 90
    for fila in filas:
        Regla(fila["regla"])  # no lanza


@pytest.mark.parametrize(
    ("nombre", "texto", "regla", "central"),
    [
        (
            "Festividad De La Santísima Cruz Del Tres De Mayo",  # 3751
            "La Santísima Cruz del Tres de Mayo de Puerto Eten, se celebra del 23 de abril al 04 de mayo de todos "
            "los años. El 03 de mayo, gran día central, los integrantes de la hermandad salen en procesión.",
            "fija 04-23..05-04",
            "05-03",
        ),
        (
            "Festival De San Juan - Kimbiri",  # 10802
            "El Festival de San Juan se celebra cada 24 de junio, en donde se le rinde homenaje al Santo Patrón.",
            "fija 06-24",
            None,
        ),
        (
            "Festival De La Fresa",  # 3158
            "Es la celebración de la cosecha de fresas del distrito, que se realiza cada primer domingo de noviembre, "
            "desde 1989.",
            "nesimo 11 1 dom",
            None,
        ),
        (
            "Feria Nacional Agropecuaria Meseta Del Bombom",  # 11681: "25 junio", sin "de"
            "Actualmente, la feria se lleva a cabo todos los años entre el 25 junio al 2 de julio.",
            "fija 06-25..07-02",
            None,
        ),
        (
            "Wawa Pampay",  # 11660
            "Es una costumbre ancestral que se manifiesta el primero de noviembre de todos los años.",
            "fija 11-01",
            None,
        ),
        (
            "Festividad De San Pedro De Catas",  # 12554
            "Actualmente, esta fiesta se realiza los días 28,29,30 de junio.",
            "fija 06-28..06-30",
            None,
        ),
        (
            "Festividad Del Señor De La Buena Muerte De Chocan",  # 6348: el rango y su día central
            "La fiesta religiosa se lleva a cabo desde el 23 de enero hasta el 11 de febrero en el distrito de "
            "Querecotillo, siendo el día central de la festividad el 02 de febrero.",
            "fija 01-23..02-11",
            "02-02",
        ),
        (
            "Akshu Tatay De Pucará",  # 13778
            "Tiene sus raíces en las prácticas agrícolas; se realiza durante el mes de febrero, cuando las lluvias "
            "son intensas.",
            "mes 02",
            None,
        ),
        (
            "Fiesta De Pascua De Reyes De Huancaya",  # 13234: "5 a 8", sin "del"
            "Se celebra los días 5 a 8 de enero de cada año, en honor a la Virgen Acepciona.",
            "fija 01-05..01-08",
            None,
        ),
        (
            "Fiesta Patronal De San Pedro",  # 14484: la lista entera, no solo "29 y 30"
            "Las actividades se desarrollan en los días 28, 29 y 30 de junio.",
            "fija 06-28..06-30",
            None,
        ),
        (
            "Feria Regional De La Uva",  # 3972: el día central son dos días
            "Se lleva a cabo del 25 de Julio al 29 de Julio, siendo el 28 y 29 de julio el día central.",
            "fija 07-25..07-29",
            "07-28..07-29",
        ),
        (
            "La Santísima Cruz De Los Motilones De Lamas",  # 5321: "fecha central" no es la fecha de un documento
            "Del 7 al 16 de julio de cada año se realiza una de las fiestas populares más grandes de la Amazonía "
            "peruana, una tradición que tiene como fecha central el 16 de julio.",
            "fija 07-07..07-16",
            "07-16",
        ),
    ],
)
def test_fecha_escrita_en_la_ficha(nombre, texto, regla, central):
    fecha = leer_fecha(nombre, descripcion=texto)
    assert (fecha.regla, fecha.dia_central) == (regla, central)
    Regla(fecha.regla)


def test_el_dia_central_gana_a_la_novena():  # 10194
    fecha = leer_fecha(
        "Fiesta Patronal De Santa Rosa De Ocopa",
        observaciones="Se celebra cada 30 de Agosto de cada año en honor a Santa Rosa de Lima.",
        descripcion="La Comisión Patronal empieza con las misas de novena del 20 al 28 de agosto.",
    )
    assert (fecha.regla, fecha.precision, fecha.fuente) == ("fija 08-30", "exacta", "texto_ficha")


def test_el_dia_central_despues_de_la_fecha():  # 10861
    fecha = leer_fecha(
        "Fiesta Patronal En Honor A San Agustin De Marcac",
        observaciones="La fiesta patronal se realiza desde el 27 al 29 de Agosto.",
        descripcion="El 28 de Agosto es considerado como el día central, que se da inicio con la distribución "
        "del desayuno.",
    )
    assert (fecha.regla, fecha.dia_central) == ("fija 08-27..08-29", "08-28")


def test_el_dia_central_de_otra_fecha():  # 12672: el central es "el 16", no el 1 de julio
    fecha = leer_fecha(
        "Fiesta Patronal Virgen Del Carmen",
        descripcion="El 01 de Julio es la bajada de la Virgen, el 16 es el día central de la virgen del Carmen.",
    )
    assert fecha.regla == "fija 07-16"


def test_el_dia_central_no_cruza_un_punto():  # 11160
    fecha = leer_fecha(
        "Festividad De Las Santísimas Cruces De Matakaka",
        descripcion="Recogen las flores que adornarán las cruces el día central de la festividad. El 30 de abril "
        "se realiza la retreta de bandas. El 02 de mayo día central de la festividad se realiza la veneración.",
    )
    assert fecha.regla == "fija 05-02"


def test_el_santoral_compara_sin_tildes_ni_enie():
    assert leer_fecha("FESTIVIDAD DEL SENOR DE LOS TEMBLORES").regla == "pascua -6"
    assert leer_fecha("Fiesta del Niño Jesús de Praga").regla == "fija 12-24..01-06"


def test_una_fiesta_movil_por_su_nombre():
    fecha = leer_fecha("Semana Santa Pampacolca", descripcion="Se celebra del 13 al 20 de abril de 2025.")
    assert (fecha.regla, fecha.precision, fecha.fuente) == ("pascua -7..0", "aproximada", "nombre_movil")
    assert leer_fecha("Festividad Del Señor De Los Temblores").regla == "pascua -6"
    assert leer_fecha("El Carnaval De Conache").regla == "pascua -50..-47"


def test_una_fiesta_movil_en_el_texto():  # 14693
    fecha = leer_fecha(
        "Retorno O Bajada Del Dr. Patron San Jeronimo",
        descripcion="Es una actividad que se realiza anualmente un día después de la Octava de Corpus Christi.",
    )
    assert (fecha.regla, fecha.fuente) == ("pascua 67..68", "texto_movil")


def test_el_carnaval_llega_hasta_donde_dice_la_ficha():
    despacho = leer_fecha(  # 13267
        "Carnavales De Machaguay",
        descripcion="El día martes es el día central, y finalmente el Miércoles de Ceniza se hace el despacho "
        "de carnavales.",
    )
    assert (despacho.regla, despacho.fuente) == ("pascua -50..-46", "nombre_movil")
    assert "despacho" in despacho.evidencia
    tentacion = leer_fecha(  # 14688
        "Carnaval De Tarata",
        descripcion="La celebración tiene como uno de sus días centrales el Miércoles de Ceniza, aunque "
        "determinadas actividades pueden desarrollarse también durante el Martes de Carnaval y el domingo de "
        "tentación.",
    )
    assert tentacion.regla == "pascua -50..-42"
    previo = leer_fecha(  # 3035: termina el martes
        "Carnaval Riojano",
        descripcion="La festividad concluye un día martes previo al miércoles de ceniza, con la lectura del "
        "testamento.",
    )
    assert (previo.regla, previo.evidencia) == ("pascua -50..-47", "carnaval")


def test_el_santoral_cuando_la_ficha_no_da_fecha():
    fecha = leer_fecha("Fiesta Patronal De Santa Rosa", descripcion="Una fiesta muy concurrida.")
    assert (fecha.regla, fecha.precision, fecha.fuente) == ("fija 08-30", "aproximada", "santoral")


def test_fechas_que_no_son_de_la_fiesta():
    # Una calle, un documento y una fecha histórica no son la fecha de la celebración.
    fecha = leer_fecha(
        "Festividad Del Señor De Chiquito",
        descripcion="La capilla se ubica en la calle 3 de mayo cdra. 1. Declarada por la Resolución del 5 de junio "
        "de 2019. El capitán fundó la ciudad el 25 de julio de 1540, fiesta de Santiago.",
    )
    assert fecha.regla is None and fecha.precision == "por_confirmar"


def test_una_fecha_con_su_anio_es_historia():  # 11657
    fecha = leer_fecha(
        "Día De La Gratuidad De La Educación",
        descripcion="Los días 20, 21 y 22 de junio del año 1969 se desarrollaron grandes movilizaciones. Todos "
        "los 22 de junio de cada año las instituciones públicas participan del homenaje.",
    )
    assert fecha.regla == "fija 06-22"


def test_aniversario_usa_la_fecha_de_creacion():
    fecha = leer_fecha(
        "Aniversario De Fundación Política De Soritor",  # 12124
        descripcion="La Creación Política de Soritor como distrito fue el 02 de enero de 1857, fecha que se celebra "
        "cada año.",
    )
    assert fecha.regla == "fija 01-02"


def test_la_fecha_de_una_edicion_es_aproximada():
    fecha = leer_fecha("Festival Del Mango", descripcion="El festival se realizó del 10 al 12 de febrero de 2024.")
    assert (fecha.regla, fecha.precision) == ("fija 02-10..02-12", "aproximada")


def test_evaluar_compara_con_las_fechas_anotadas():
    eventos = pd.DataFrame(
        {"codigo": [1, 2, 3, 4], "regla": ["fija 12-24..01-06", "fija 07-01", "pascua -50..-47", None]}
    )
    anotados = pd.DataFrame(
        {
            "codigo": [1, 2, 3, 4],
            "nombre": ["Navidad", "Virgen del Carmen", "Carnaval", "Fiesta del Agua"],
            "inicio": ["2026-12-24", "2026-07-01", "2026-02-14", "2026-09-26"],
            "fin": ["2027-01-06", "2026-07-31", "2026-02-22", "2026-09-26"],
            "central": ["2026-12-25", "2026-07-16", "2026-02-18", None],
        }
    )
    r = evaluar(eventos, anotados).set_index("codigo")
    assert r.loc[1, "en_la_fiesta"] and r.loc[1, "incluye_central"]  # cruza el año
    assert r.loc[2, "en_la_fiesta"] and not r.loc[2, "incluye_central"]  # empieza el 1, el central es el 16
    assert r.loc[3, "en_la_fiesta"] and not r.loc[3, "incluye_central"]  # sin el miércoles de ceniza
    assert pd.isna(r.loc[4, "regla"]) and pd.isna(r.loc[4, "en_la_fiesta"])  # sin regla no se evalúa


def test_las_anotaciones_son_validas():
    anotados = pd.read_csv(ANOTADOS, sep=";", encoding="utf-8", dtype=str)
    assert len(anotados) == anotados["codigo"].nunique() == 40
    for a in anotados.itertuples(index=False):
        inicio, fin = date.fromisoformat(a.inicio), date.fromisoformat(a.fin)
        assert inicio.year == 2026 and inicio <= fin, a
        if isinstance(a.central, str):
            ini, _, fin_central = a.central.partition("..")
            assert inicio <= date.fromisoformat(ini) <= date.fromisoformat(fin_central or ini) <= fin, a


def test_la_muestra_anotada_cae_en_la_fiesta():
    """El calendario publicado cumple la meta del plan (90 %) sobre la muestra anotada a mano."""
    ruta = PROCESADOS / "eventos_v3.csv"
    if not ruta.exists():
        pytest.skip("falta data/procesados/eventos_v3.csv: python -m pipeline.eventos")
    eventos = pd.read_csv(ruta, sep=";", encoding="utf-8-sig")
    anotados = pd.read_csv(ANOTADOS, sep=";", encoding="utf-8")
    assert set(anotados["codigo"]) <= set(eventos["codigo"])
    r = evaluar(eventos, anotados)
    con_fecha = r[r["regla"].notna()]
    assert len(con_fecha) >= 0.9 * len(r)
    assert con_fecha["en_la_fiesta"].astype(bool).mean() >= 0.9, con_fecha[~con_fecha["en_la_fiesta"].astype(bool)]
    assert con_fecha["incluye_central"].dropna().astype(bool).mean() >= 0.9
