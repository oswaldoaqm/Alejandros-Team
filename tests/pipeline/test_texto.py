"""Cada caso es una celda real de las fichas de MINCETUR (código de la ficha al lado).

Los casos de datos de contacto conservan la forma de la celda, con nombres, teléfonos y
correos inventados.
"""

import re

import pytest

from pipeline.texto import (
    CONTACTO_OMITIDO,
    leer_altitud,
    leer_dias,
    leer_distancia_tiempo,
    leer_horario,
    leer_tarifa,
    limpio,
    sin_contactos,
)


@pytest.mark.parametrize("celda", [None, "", "  ", "-", "--", "undefined", "NULL"])
def test_celdas_sin_dato(celda):
    assert limpio(celda) is None


@pytest.mark.parametrize(
    ("celda", "km", "minutos"),
    [
        ("186 km / 3 h 55 min", 186, 235),  # 1237
        ("16.4 km / 35 min", 16.4, 35),
        ("160 Km / 3.5 h", 160, 210),
        ("42 Km / 1 H 25 Min", 42, 85),  # 22
        ("500 Mts / 9 Min", 0.5, 9),
        ("14 km /3 hr. 11 min", 14, 191),  # 151
        ("14 km / 1hr", 14, 60),
        ("4.4.km/ 7 min", 4.4, 7),  # 257: punto sobrante
        ("74 km/ 1 hora con 5 min", 74, 65),
        ("74.km/ 1 hora y 20 min.", 74, 80),
        ("2.2. km / 4 min", 2.2, 4),  # 916
        ("1.1. Km. / 3 minutos.", 1.1, 3),  # 1179
        ("24.6 Km/ 40 min horas", 24.6, 40),  # 11842
        ("64, 4 Km /1h 47m", 64.4, 107),  # 11842: coma con espacio y "m" de minutos
        ("9,7 km / 25 min", 9.7, 25),
        ("110 metros / 1 minutos", 0.11, 1),
        ("1 Km. 500 metros/ 20 min", 1.5, 20),
        ("56 K. 55 m.", 56, 55),
        ("200 m / 20 m", 0.2, 20),
        ("1h 32m / 43 km ( mediante tren )", 43, 92),
        ("3:00 horas 8 km", 8, 180),
        ("02:30 horas / 131 km", 131, 150),
        ("210 kms / 3:00 horas", 210, 180),
        ("1.0 km / 30:00 minutos", 1, 30),
        ("2 horas y media", None, 150),
        ("120 km / 2 horas 1/2", 120, 150),
        ("1 1/2 km / 10 min", 1.5, 10),
        ("1/2km/10 minutos", 0.5, 10),
        ("1½ Km / 8 minutos", 1.5, 8),
        ("30 metros/ 30 segundos", 0.03, 0.5),
        ("2km/1o min", 2, 10),
        ("0.820 mts / 10 min.", 0.82, 10),
        ("1,200 m/20min", 1.2, 20),
        ("34.605 km / 2 h", 34.605, 120),
        ("107.53k m/2hrs :40 min", 107.53, 160),
        ("17 km / 15 munitos", 17, 15),
        ("1Km/5 mimutos.", 1, 5),
        ("40 minutos", None, 40),
        ("151 km / 3", 151, None),  # un número sin unidad no se adivina
        ("Plaza de Armas - Subida a Malconga", None, None),
    ],
)
def test_distancia_y_tiempo(celda, km, minutos):
    leido = leer_distancia_tiempo(celda)
    assert leido.km == pytest.approx(km)
    assert leido.minutos == pytest.approx(minutos)
    assert not leido.ambigua


@pytest.mark.parametrize(
    ("celda", "km", "minutos"),
    [
        ("136 kms / 2.20 horas", 136, 140),  # h.mm, como se escribe en las fichas
        ("142K.M/3.37Horas", 142, 217),
        ("85km / 2.30 min", 85, 150),  # 2,3 minutos para 85 km es imposible
        ("6.19 km/0.12 min", 6.19, 12),
        ("1.5 minutos /65 km", 65, 90),
        ("43 km / 1:10 min", 43, 70),
    ],
)
def test_lecturas_dudosas_quedan_marcadas(celda, km, minutos):
    leido = leer_distancia_tiempo(celda)
    assert (leido.km, leido.minutos, leido.ambigua) == (pytest.approx(km), pytest.approx(minutos), True)


def test_el_tiempo_se_detiene_si_una_unidad_se_repite():
    leido = leer_distancia_tiempo("180km/ 2 dias de ida y dos dias de retorno")
    assert (leido.km, leido.minutos) == (180, 2 * 24 * 60)


def test_millas_nauticas():
    assert leer_distancia_tiempo("6 millas/ 45 min").km == pytest.approx(6 * 1.852)


@pytest.mark.parametrize(
    ("celda", "esperado"),
    [
        ("350", (350, 350)),
        ("3,399 m", (3399, 3399)),  # 11
        ("4008 m.s.n.m.", (4008, 4008)),  # 104
        ("75 m.s.n.m.", (75, 75)),
        ("3.635 msnm", (3635, 3635)),  # punto de miles
        ("2 650 msnm", (2650, 2650)),
        ("4, 138 m.s.n.m", (4138, 4138)),
        ("4,153.21 msnm", (4153.21, 4153.21)),
        ("4,600. M.S.N.M.", (4600, 4600)),
        ("673,9", (673.9, 673.9)),
        ("3.5", (3.5, 3.5)),
        ("150 - 1550", (150, 1550)),
        ("1800-2300", (1800, 2300)),
        ("4310 a 4546", (4310, 4546)),
        (": 3822 m.s.n.m.", (3822, 3822)),
        ("8548773", (None, None)),  # fuera de 0–6 800 m
        ("23740 m.s.n.m.", (None, None)),
        (None, (None, None)),
    ],
)
def test_altitud(celda, esperado):
    assert leer_altitud(celda) == esperado


@pytest.mark.parametrize(
    ("celda", "esperado"),
    [
        ("10:00 a.m. - 04:00 p.m.", ("10:00", "16:00")),
        ("06:30 a.m. - 09:00 a.m.", ("06:30", "09:00")),
        ("08:00 a.m. - 12:00 p.m.", ("08:00", "12:00")),  # cierra al mediodía
        ("12:00 a.m. - 11:00 p.m.", ("00:00", "23:00")),
        ("07:00 p.m. - 12:00 a.m.", ("19:00", "24:00")),
        ("-", (None, None)),
    ],
)
def test_horario(celda, esperado):
    assert leer_horario(celda) == esperado


@pytest.mark.parametrize(
    ("celda", "esperado"),
    [
        ("De lunes a domingo", (0, 1, 2, 3, 4, 5, 6)),
        ("Lunes - Domingo", (0, 1, 2, 3, 4, 5, 6)),
        ("De martes a domingo", (1, 2, 3, 4, 5, 6)),
        ("Lunes a viernes", (0, 1, 2, 3, 4)),
        ("Sábados", (5,)),
        ("Viernes y sábados", (4, 5)),
        ("De viernes a lunes", (0, 4, 5, 6)),
        ("Todos los días excepto lunes", (1, 2, 3, 4, 5, 6)),
        ("Lunes cerrado", (1, 2, 3, 4, 5, 6)),
        # 1179: entre semana con pausa al mediodía y sábados en la mañana
        (
            "De lunes a viernes cierra de 01:00 p.m. a 03:00 p.m. Atención de sábados: 09:00 a.m. a 12:00 m.",
            (0, 1, 2, 3, 4, 5),
        ),
        ("El 25 de diciembre, 1 de enero y 15 de abril el museo esta cerrado.", None),
        ("Horario recomendado.", None),
    ],
)
def test_dias(celda, esperado):
    assert leer_dias(celda) == esperado


@pytest.mark.parametrize(
    ("celda", "soles", "regla"),
    [
        (
            "Adulto: S/ 11.00 - Estudiantes de Educación Superior : S/ 4.00 - Niños / Escolares : S/ 1.00 - "
            "Entrada Especial S/ 5.50 - Personas con Discapacidad S/ 5.50 - Guía Grupo hasta 9 personas S/ 20.00",
            11,
            "adulto",
        ),  # 1237: la tarifa de guía no es la de un adulto
        (
            "Tarifa Nacional y Extranjero (Válido Por Un Día) • Adultos: S/. 11.00 • Menores: S/ 3.00 "
            "Tarifa Local – Región Ica (Válido Por un Día) • Adultos: S/. 5.00 • Menores: S/. 3.00",
            11,
            "adulto_nacional",
        ),  # 257
        ("Niños de 4 a 11 años: s/5.00 Personas de 12 a 64 años: s/10.00 Extranjeros: s/15.00", 10, "adulto"),  # 151
        ("Compra de boleto para acceso a tres atractivos turísticos. Entrada general: S/5.00", 5, "adulto"),  # 22
        ("Entrada general S/ 5.00 a partir de los 10 años de edad.", 5, "adulto"),  # 11842
        ("Niños S/3.00, General S/5.00", 5, "adulto"),
        (
            "Costo de ingreso por un día. •Extranjero: s/. 30.00. •Nacional: Adultos s/. 15.00, Niños de 5 a 17 años: "
            "S/. 5.00 • Local: Adultos s/. 5.00 y niños de 5 a 17 años: S/. 3.00",
            15,
            "adulto_nacional",
        ),
        ("Parque Nacional Huascarán (Extranjeros s/.30.00 y Nacional s/.12.00)", 12, "nacional"),
        ("S/ 65.00 extranjeros y S/ 30.00 nacionales.", 30, "nacional"),  # el monto va antes de la etiqueta
        (
            "Tarifas establecidas por el SERNANP para un día S/. 30.00 extranjeros, S/. 12.00 nacionales; "
            "y para dos a tres dias: S/. 60.00 extranjeros y S/. 30.00 nacionales",
            12,
            "nacional",
        ),
        ("Nacionales adulto /12.00, Adulto local y niño nacional s/ 5.00 Extranjero s/ 30.00.", 12, "adulto_nacional"),
        (
            "Locales ruta corta S/.5.00, ruta larga S/.10.00, nacionales ruta corta S/.10.00, ruta larga S/.20.00",
            10,
            "nacional",
        ),
        ("BTG Extranjero general S/130, parcial S/70, Estudiante ext. S/70 Nacional S/70", 70, "nacional"),
        ("Tarifa de cueva S/5.00", 5, "unico"),
        ("Adultos: 5 nuevos soles. Niños: 3 nuevos soles", 5, "adulto"),
        ("Ticket general adulto S/. 8,00, especial-peruano (60 año) S/. 4,00, niños S/. 3,00.", 8, "adulto"),
        ("S/ 20.00 soles adultos y niños S/10.00", 20, "adulto"),
        ("s/. 5.00 para turistas y S/.10.00 para maestros curanderos, menores de edad no pagan.", 5, "adulto"),
        ("Adultos : S./ 10.00 / Niños: S./ 6.00", 10, "adulto"),  # "S./"
        ("El costo es 2.00 s/. entrada general.", 2, "adulto"),  # el monto antes de "s/."
        ("costo de ingreso Adultos 3 Soles; Niños 1 Sol; Extranjeros 6 Soles", 3, "adulto"),
        (
            "Niño local S/. 3.00, Adulto local S/. 3.00, Niño foráneo S/. 5.00, Adulto foráneo S/. 5.00.",
            5,
            "adulto_nacional",
        ),
        (
            "Menores Locales(Moquegua)de 5a16 años S/. 3.00, Adultos Locales(Moquegua) y Menores Nacionales(5a16 años)"
            "S/5.00, Adultos Nacionales S/.11.00, Extranjeros S/. 30.00",
            11,
            "adulto_nacional",
        ),
        (
            "Único pago para el ingreso a la laguna S/.5 soles, la boletería esta ubicado en la localidad de Yaurin",
            5,
            "unico",
        ),
        ("Tarifa pozas privadas: S/.10 Tarifa de la Piscina Termal: S/.5.00", 5, "minimo"),  # opciones, no personas
        ("Visita guiada: s/. 5.00 a partir de 12 a 65 años", 5, "unico_servicio"),
        (
            "Pago de S/.65.00 nuevos soles al PNH para 30 días de permanencia. Extranjero S/. 30.00 Nacional S/.15.00 "
            "Local S/. 5.00",
            15,
            "nacional",
        ),  # 1455: el primer monto no tiene etiqueta y el resto la lleva delante
        ("Pago por concepto de tour en fundo S/ 10.00 adultos y S/ 5.00 niños", 10, "adulto"),  # 11436
        ("s/ 2.00 Estudiante s/5.00 Turista Nacional s/7.00 Turista Extranjero", 5, "adulto_nacional"),  # 1137
        (
            "Costo de ingreso por unidad vehicular S/. 5.00 soles, en tanto que visitante que llega a pie no paga",
            None,
            None,
        ),
        ("Costo adultos: 10, estudiantes:5, niños: 1", 10, "adulto_sin_moneda"),
        ("Pagan US$ 10 los extranjeros", None, None),  # los dólares no cuentan
        ("--", None, None),
    ],
)
def test_tarifa_de_adulto_peruano(celda, soles, regla):
    tarifa = leer_tarifa(celda)
    assert (tarifa.soles, tarifa.regla) == (soles, regla)


def test_tarifa_de_boleto_combinado():
    tarifa = leer_tarifa("Incluido en el Circuito Religioso del Cusco Adultos S/30, Estudiantes S/ 15")
    assert (tarifa.soles, tarifa.combinada) == (30, True)


@pytest.mark.parametrize(
    "texto",
    [
        "Para visitas de delegaciones coordinar al Cel. 987654321 Lic. Nombre Apellido.",
        "reservas al 912 345 678 o por whatsapp",
        "llamar al (053) 123456",
        "comunicarse al +51 987 654 321",
        "correo: visitas@ejemplo.gob.pe.",
        "Teléfono: 01-4567890",
    ],
)
def test_sin_contactos_quita_telefonos_y_correos(texto):
    limpio_ = sin_contactos(texto)
    assert CONTACTO_OMITIDO in limpio_
    assert "@" not in limpio_
    assert not re.search(r"\d{3}[\s-]?\d{3}", limpio_)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        (
            "Previa coordinación con el Sr. Nombre Apellido al Cel. 987654321",
            "Previa coordinación con el [encargado] al Cel. [contacto en la ficha oficial]",
        ),
        (
            "coordinar al Cel. 987654321 Lic. Nombre Apellido Apellido.",
            "coordinar al Cel. [contacto en la ficha oficial] [encargado].",
        ),
        ("Encargado: Nombre J. Apellido 987654321", "[encargado] [contacto en la ficha oficial]"),
    ],
)
def test_sin_contactos_quita_el_nombre_de_quien_atiende(texto, esperado):
    assert sin_contactos(texto) == esperado


def test_sin_contactos_respeta_nombres_citados():
    texto = "escrito por la Dra. Ruth Shady Solis, en idioma español"  # 1237: una cita, no un contacto
    assert sin_contactos(texto) == texto


@pytest.mark.parametrize(
    "texto",
    [
        "Declarado mediante Resolución Viceministerial Nº 295-2011-VMPCIC-MC",
        "población de cerca de 1000 000 de personas",
        "Decreto Supremo N° 038-2021-MINAM.",
        "Ordenanza Municipal N° 037-2015-MPS",
    ],
)
def test_sin_contactos_no_toca_resoluciones_ni_cifras(texto):
    assert sin_contactos(texto) == texto


@pytest.mark.parametrize(
    "texto",
    [
        "reservas: Fulana Mengana-987654321 – Zutano Perengano - 912345678.",  # 14643: pegado a un guion
        "los teléfonos son: 987654321 (párroco) y 912 345 678- 987654322",  # 871
        "Informes: 2345678 / 3456789 / 987654321",  # 10931: fijos en una lista
        "Teléfonos: 987654321 / 234-5678",  # 1208
        "contactar con la Gerencia del Callao 234-5678/345-6789 anexos 123–456 ó a 987654321",  # 10941
        "Atención: Lunes a domingo / Informes: 234-5678 anexo 1234",  # 6822
        "Previa coordinación al numero 056-123456 o al correo reservas@ejemplo.pe",  # 11316
        "Teléfono fijo: 056 – 123456 Celular : 987654321",  # 6972
        "Mayores informes: 01 2345678 - 987654321",  # 1379
        "Consultas 064-123456, horario de lunes a viernes",  # 12662
        "Coordinaciones: 234-5678 | 987-654-321 | 912-345-678",  # 11193
        "N° de contacto : 234-5678.",  # 3499
        "comunicarse al telefono fijo 084-123456",  # 6915
        "al teléf 042123456",  # 11416
        "Previa llamada telefónica; al 074-123456 ó 987654321",  # 2350
        "Reservas al 234-5678",
        "Informes: info@info@ejemplo.gob.pe / 987654321",  # 4367: el correo escrito dos veces
    ],
)
def test_sin_contactos_quita_los_telefonos_que_nada_anuncia(texto):
    limpio_ = sin_contactos(texto)
    assert CONTACTO_OMITIDO in limpio_
    assert "@" not in limpio_
    assert not re.search(r"\d{3}[\s-]?\d{3}", limpio_)


@pytest.mark.parametrize(
    "texto",
    [
        "Informe Técnico N°001-2022",
        "Coordenadas UTM: Este 0264341 / Norte 8877279",
        "coordenadas Norte: 9123456.78 m S",
        "la Guerra del Pacífico (1879-1883)",
        "Jr. Próspero Nº 401-437 Esq. Jr. Morona Nº 181-199",
        "según R.M. N° 000092-2024-MC",
    ],
)
def test_sin_contactos_no_toca_coordenadas_ni_documentos(texto):
    assert sin_contactos(texto) == texto


OMITIDO = CONTACTO_OMITIDO


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        (  # 10215: sin tratamiento
            "Coordinar previamente con Fulano Mengano Zutano - Cel.: 987654321.",
            f"Coordinar previamente con [encargado] - Cel.: {OMITIDO}.",
        ),
        (  # 14643: dos personas, cada una con su teléfono
            "reservas: Fulana Mengana-987654321 – Zutano Perengano - 912345678.",
            f"reservas: [encargado]-{OMITIDO} – [encargado] - {OMITIDO}.",
        ),
        (  # 11112: el nombre después del teléfono
            "Comunicarse al 987654321 - Fulano Mengano o 912345678 Zutano Perengano.",
            f"Comunicarse al {OMITIDO} - [encargado] o {OMITIDO} [encargado].",
        ),
        (  # 10867: el tratamiento en minúsculas y con dos puntos
            "Previa coordinación con el encargado, el señor: Fulano Mengano. Cel. 987654321",
            f"Previa coordinación con el encargado, el [encargado]. Cel. {OMITIDO}",
        ),
        (  # 11288: el cargo se queda
            "Previa coordinación con el propietario Fulano Mengano al contacto 987654321 y presentación de boleto",
            f"Previa coordinación con el propietario [encargado] al contacto {OMITIDO} y presentación de boleto",
        ),
        (  # 11435: Julio también es un nombre
            "contactar con el sr. Julio Mengano , presidente del centro poblado, celular 987654321",
            f"contactar con el [encargado] , presidente del centro poblado, celular {OMITIDO}",
        ),
        (  # 13771: Mercado también es un apellido
            "Coordinar con el Director y propietario Fulano Mercado Mengano / Cel.: 987654321",
            f"Coordinar con el Director y propietario [encargado] / Cel.: {OMITIDO}",
        ),
        (  # 3644: un apellido compuesto
            "está el padre Fulano Mengano- Zutano, cuyo teléfono es el 987654321",
            f"está el padre [encargado], cuyo teléfono es el {OMITIDO}",
        ),
        (  # 14697: el apellido en minúsculas
            "Hacer de su conocimiento a la autoridad comunal Fulano mengano telf. 987654321",
            f"Hacer de su conocimiento a la autoridad comunal [encargado] telf. {OMITIDO}",
        ),
        (  # 12015: un nombre de pila solo
            "Paseos en cuatrimotos Fulana (cel: 987654321)",
            f"Paseos en cuatrimotos [encargado] (cel: {OMITIDO})",
        ),
        (  # 11543: todo en mayúsculas, solo lo pegado al contacto
            "VISITAS GUIADAS TODO EL AÑO PREVIA COORDINACION CON EL JEFE FULANA MENGANA ZUTANA CEL 987654321",
            f"VISITAS GUIADAS TODO EL AÑO PREVIA COORDINACION CON EL JEFE [encargado] CEL {OMITIDO}",
        ),
        (  # un solo nombre, lejos del teléfono: lo delata el cargo
            "El párroco Fulano atiende de lunes a viernes. Cel. 987654321",
            f"El párroco [encargado] atiende de lunes a viernes. Cel. {OMITIDO}",
        ),
    ],
)
def test_sin_contactos_quita_el_nombre_aunque_no_lleve_tratamiento(texto, esperado):
    assert sin_contactos(texto) == esperado


@pytest.mark.parametrize(
    ("texto", "queda"),
    [
        (  # 11068
            "El ingreso a la Catarata Gallito de las Rocas es previa coordinación con el administrador del Fundo "
            "Mesapata. Celular: 987654321.",
            "Catarata Gallito de las Rocas es previa coordinación con el administrador del Fundo Mesapata.",
        ),
        (  # 10224
            "Comunicarse con el Área de Turismo de la Municipalidad Distrital de Huayhuay - Cel. 987654321",
            "Municipalidad Distrital de Huayhuay",
        ),
        ("De Lunes a Domingo. Reservas al 987654321", "De Lunes a Domingo. Reservas al"),
        (
            "Fiesta de Santa Rosa, entre Abril y Julio. Informes al 987654321",
            "Fiesta de Santa Rosa, entre Abril y Julio. Informes al",
        ),
    ],
)
def test_sin_contactos_deja_los_lugares_las_instituciones_y_los_dias(texto, queda):
    limpio_ = sin_contactos(texto)
    assert queda in limpio_
    assert "[encargado]" not in limpio_


def test_el_nombre_del_encargado_no_se_lee_como_un_dia():
    # 11136: su encargado se llama Domingo, y el recurso figuraba como abierto los domingos.
    texto = "Lunes a sábado. Con orientación del presidente de la junta, sr. Santos Domingo Mengano al cel. 987654321."
    assert leer_dias(texto) == (0, 1, 2, 3, 4, 5, 6)
    assert leer_dias(sin_contactos(texto)) == (0, 1, 2, 3, 4, 5)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        (  # 11345: un fijo sin nada que lo anuncie
            "Previo aviso y pago de ticket. Contacto: Sr. Fulano Mengano Zutano 076123456.",
            f"Previo aviso y pago de ticket. Contacto: [encargado] {OMITIDO}.",
        ),
        (  # 13675: un celular al que le falta una cifra
            "te invitamos a contactar directamente al propietario, Fulano Mengano, al 98765432",
            f"te invitamos a contactar directamente al propietario, [encargado], al {OMITIDO}",
        ),
        (  # 13755: con su código de ciudad y entre paréntesis
            "Comunicarse con la secretaría del Obispado (073-123456).",
            f"Comunicarse con la secretaría del Obispado ({OMITIDO}).",
        ),
        ("084 123456, despacho parroquial", f"{OMITIDO}, despacho parroquial"),  # 903
        (  # 11762: sin teléfono, con tratamiento
            "Coordinar con el Sr. Fulano Mengano Zutano, presidente del barrio.",
            "Coordinar con el [encargado], presidente del barrio.",
        ),
        (  # 11837
            "Coordinar con el señor Fulano, encargado de la iglesia.",
            "Coordinar con el [encargado], encargado de la iglesia.",
        ),
        ("Previa coordinación con la familia Mengano.", "Previa coordinación con la familia [encargado]."),  # 327
        ("Coordinación con el párroco; Fulano Mengano Zutano", "Coordinación con el párroco; [encargado]"),  # 431
        (  # 5282: sin tratamiento ni cargo, el nombre completo de quien da el permiso
            "Previa autorización de la Comunidad San Jacinto - Fulano Mengano Zutano.",
            "Previa autorización de la Comunidad San Jacinto - [encargado].",
        ),
    ],
)
def test_en_un_aviso_el_nombre_y_el_numero_son_un_contacto(texto, esperado):
    assert sin_contactos(texto, aviso=True) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "Asimismo es necesario adquirir el servicio de un Guía Oficial de Alta Montaña.",  # 1330
        "Durante Semana Santa y la fiesta del Señor de los Milagros.",
        "Al formar parte del Camino Inca, se paga un boleto turístico.",  # 13698
        "Lunes a Domingo de 9 am a 5 pm.",
        "Adulto Nacional S/ 15.00, Niño Nacional S/ 7.50",  # 13101
        "Menores de edad: ingreso gratuito según Resolución Ministerial N° 000092-2024-MC.",  # 3792
        "Observación externa desde Jr. Próspero Nº 401-437 Esq. Jr. Morona Nº 181-199",  # 8384
        "Visitas según el Artículo N°10 de la Ordenanza Municipal N°01-2020-MDCF/A.",  # 11154
        "Previa coordinación con la empresa: SOUTHERN PERU COPPER CORPORATION",  # 513
    ],
)
def test_un_aviso_sin_contactos_queda_como_esta(texto):
    assert sin_contactos(texto, aviso=True) == texto


def test_fuera_de_un_aviso_un_nombre_sin_telefono_no_es_un_contacto():
    for texto in ("Coordinar con el Sr. Fulano Mengano.", "La festividad del Señor Cautivo de Ayabaca es en octubre."):
        assert sin_contactos(texto) == texto
