"""Fichas reales de MINCETUR (tests/fixtures/fichas, saneadas con sanear.py)."""

from pathlib import Path

import pytest

from pipeline.fichas import FichaInvalida, Lugar, leer_archivo, leer_ficha

FICHAS = Path(__file__).parents[1] / "fixtures" / "fichas"


def ficha(codigo: int):
    return leer_archivo(FICHAS / f"{codigo}.html.gz")


def test_todas_las_copias_de_prueba_se_leen():
    codigos = sorted(int(p.name.split(".")[0]) for p in FICHAS.glob("*.html.gz"))
    assert len(codigos) == 12
    for codigo in codigos:
        assert ficha(codigo).codigo == codigo


def test_caral_encabezado():
    caral = ficha(1237)
    assert caral.nombre == "Ciudad Sagrada De Caral"
    assert (caral.departamento, caral.provincia, caral.distrito) == ("Lima", "Barranca", "SUPE")
    assert (caral.categoria_num, caral.categoria) == (2, "Manifestaciones culturales")
    assert (caral.tipo, caral.subtipo) == ("Sitios Arqueológicos", "Zonas arqueológicas")
    assert (caral.jerarquia, caral.altitud_min_m, caral.altitud_max_m) == (4, 350, 350)
    assert caral.referencia == "km 184 carretera Panamericana Norte"
    assert caral.url.endswith("cod_Ficha=1237")
    assert caral.foto_url.startswith("https://consultasenlinea.mincetur.gob.pe/")


def test_caral_textos_con_parrafos():
    caral = ficha(1237)
    assert caral.descripcion.startswith("La Ciudad Sagrada de Caral está a 184 km al norte de Lima")
    assert "de la ciudad. La Ciudad Sagrada" in caral.descripcion  # "ciudad.La" en la ficha
    assert "UNESCO" in caral.reconocimientos
    assert caral.observaciones is None


def test_caral_rutas_de_acceso():
    tramos = ficha(1237).tramos
    assert len(tramos) == 6
    assert {t.recorrido for t in tramos} == {1, 2}
    primero = tramos[0]
    assert primero.desde == Lugar("Callao", "Prov. Const. Del Callao", "Callao")
    assert primero.hasta == Lugar("Lima", "Barranca", "Barranca")
    assert (primero.acceso, primero.medio, primero.via) == ("Terrestre", "Mini bus turístico", "Asfaltado")
    assert (primero.distancia_tiempo, primero.km, primero.minutos) == ("186 km / 3 h 55 min", 186, 235)
    assert tramos[3].minutos == 210  # "160 Km / 3.5 h"


def test_caral_ingreso_horario_y_visitantes():
    caral = ficha(1237)
    (ingreso,) = caral.ingresos
    assert ingreso.tipo == "boleto"
    assert (ingreso.tarifa.soles, ingreso.tarifa.regla) == (11, "adulto")
    (epoca,) = caral.epocas
    assert (epoca.epoca, epoca.abre, epoca.cierra, epoca.dias) == ("Todo el Año", "10:00", "16:00", tuple(range(7)))
    nacionales = next(v for v in caral.visitantes if v.tipo == "nacionales")
    assert (nacionales.cantidad, nacionales.anio) == (41463, 2022)


def test_actividades_con_su_grupo():
    caral = ficha(1237)
    assert ("Deportes / Aventura", "Caminata/Trekking") in {(a.grupo, a.actividad) for a in caral.actividades}
    assert "Alimentación: Restaurantes" in caral.servicios_fuera


@pytest.mark.parametrize(
    ("codigo", "tramo", "km", "minutos"),
    [
        (257, 0, 4.4, 7),  # "4.4.km/ 7 min"
        (257, 3, 74, 65),  # "74 km/ 1 hora con 5 min"
        (916, 1, 2.2, 4),  # "2.2. km / 4 min"
        (1179, 0, 1.1, 3),  # "1.1. Km. / 3 minutos."
        (22, 3, 0.5, 9),  # "500 Mts / 9 Min"
        (151, 0, 14, 191),  # "14 km /3 hr. 11 min"
        (11842, 1, 64.4, 107),  # "64, 4 Km /1h 47m"
    ],
)
def test_las_fichas_que_fallaban_en_v3(codigo, tramo, km, minutos):
    leido = ficha(codigo).tramos[tramo]
    assert (leido.km, leido.minutos) == (pytest.approx(km), pytest.approx(minutos))


@pytest.mark.parametrize(
    ("codigo", "soles", "regla"),
    [
        (257, 11, "adulto_nacional"),
        (1179, 5, "adulto"),
        (22, 5, "adulto"),
        (151, 10, "adulto"),  # "Personas de 12 a 64 años", no la de extranjeros
        (3486, 11, "adulto"),  # no la del servicio de guiado
        (11842, 5, "adulto"),
        (916, None, None),  # ingreso libre
    ],
)
def test_tarifa_de_cada_ficha(codigo, soles, regla):
    tarifa = ficha(codigo).ingresos[0].tarifa
    assert (tarifa.soles, tarifa.regla) == (soles, regla)


def test_jerarquia_que_no_es_numero():
    assert (ficha(104).jerarquia, ficha(104).jerarquia_texto) == (None, "No aplica")  # folclore
    assert (ficha(22).jerarquia, ficha(22).jerarquia_texto) == (None, "POR JERARQUIZAR")


def test_tipo_sin_la_letra_de_la_clasificacion():
    assert ficha(22).tipo == "Cuerpo de Agua"  # "g. Cuerpo de Agua"
    assert ficha(257).tipo == "Áreas Protegidas"  # "n. Áreas Protegidas"


def test_altitudes_con_formato():
    assert ficha(11).altitud_min_m == 3399  # "3,399 m"
    assert ficha(104).altitud_min_m == 4008  # "4008 m.s.n.m."


def test_museo_cierra_domingos():
    (epoca,) = ficha(1179).epocas
    assert (epoca.abre, epoca.cierra) == ("09:00", "17:00")
    assert epoca.dias == (0, 1, 2, 3, 4, 5)


def test_acontecimientos_sin_ruta_ni_horario():
    for codigo in (11, 11287, 12207):
        evento = ficha(codigo)
        assert evento.categoria_num == 5
        assert evento.tramos == () and evento.epocas == ()
    assert "25 de julio" in ficha(11287).observaciones
    assert (ficha(12207).tipo, ficha(12207).subtipo) == ("Eventos", "Festivales")


def test_secciones_presentes_y_omitidas():
    caral = ficha(1237)
    assert caral.secciones[1] == "Descripción"
    assert "Datos del Responsable" in caral.secciones  # se registra que existe, no se lee


PAGINA_MINIMA = """
<html><head><meta charset="utf-8"></head><body><div class="cuerpo">
<div class="TituloRecurso">Mirador De Prueba</div>
<div class="dato-imagen"><div class="prop-section"><table>
<tr><td>Código:</td><td>999</td></tr>
<tr><td>Categoría:</td><td>1. SITIOS NATURALES</td></tr>
<tr><td>Jerarquía:</td><td>1</td></tr>
</table></div></div>
<div id="accordionContent">
<h3>Descripción</h3><div><p>Un mirador. Informes al 987654321 o a mirador@correo.pe</p></div>
<h3>Datos del Responsable</h3><div><table>
<tr><td>Nombre:</td><td>Persona Responsable</td></tr>
<tr><td>Correo:</td><td>responsable@correo.pe</td></tr>
<tr><td>Teléfono:</td><td>912345678</td></tr>
</table></div>
</div></div></body></html>
"""


def test_no_lee_datos_personales():
    leida = leer_ficha(PAGINA_MINIMA)
    todo = repr(leida)
    for dato in ("Persona Responsable", "responsable@correo.pe", "912345678", "987654321", "mirador@correo.pe"):
        assert dato not in todo
    assert leida.descripcion.startswith("Un mirador. Informes al [contacto en la ficha oficial]")


def test_pagina_que_no_es_ficha():
    with pytest.raises(FichaInvalida):
        leer_ficha("<html><body><p>Error en el servidor</p></body></html>")


def test_codigo_distinto_al_pedido():
    with pytest.raises(FichaInvalida, match="999"):
        leer_ficha(PAGINA_MINIMA, codigo=1000)
