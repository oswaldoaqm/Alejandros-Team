"""Qué hacer de noche (contrato 1.5, decisión 0018): salir con «Vida nocturna» y las estrellas con
«Naturaleza» o sin intereses, las noches que se duermen en la base, sin tocar nada del día. Corre
contra los artefactos de dreemgo/datos."""

from datetime import date

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import noche, viaje

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


def _zona(nombre: str) -> int:
    [polo] = [p.id for p in artefactos.cargar().polos.values() if p.nombre == nombre]
    return polo


def _viaje(**consulta):
    [ruta] = viaje.resolver(Consulta(**consulta), artefactos.cargar()).rutas
    return ruta


def _noches(ruta) -> dict[int, object]:
    return {d.numero: d.noche for d in ruta.dias if d.noche is not None}


@con_datos
def test_salir_en_el_cusco_cada_noche_otros_lugares_y_la_primera_se_descansa():
    ruta = _viaje(origen="lima", mes=7, dias=6, intereses=["vida_nocturna"], destino=_zona("Cuzco"))
    noches = _noches(ruta)
    # Se llega en avión el día 1 y se vuelve el 6: se duerme en el Cusco las noches del 1 al 5.
    assert sorted(noches) == [1, 2, 3, 4, 5]
    assert noches[1].tipo == "descanso" and "3 400 m" in noches[1].nota.replace(" ", " ")
    salidas = [noches[n] for n in (2, 3, 4, 5)]
    assert all(n.tipo == "salir" and 1 <= len(n.lugares) <= noche.LUGARES_POR_NOCHE for n in salidas)
    nombres = [lugar.nombre for n in salidas for lugar in n.lugares]
    assert len(nombres) == len(set(nombres))  # con cien lugares, ninguna noche repite
    assert all(len({lugar.tipo for lugar in n.lugares}) == len(n.lugares) for n in salidas)
    assert all(lugar.minutos_a_pie <= 26 for n in salidas for lugar in n.lugares)
    assert any("De noche, " in m for m in ruta.motivos)


@con_datos
def test_con_fecha_las_estrellas_van_la_noche_con_mas_horas_sin_luna():
    # Del 3 al 8 de julio de 2027: la luna nueva es el 4.
    ruta = _viaje(
        origen="lima",
        fecha_inicio=date(2027, 7, 3),
        dias=6,
        intereses=["naturaleza", "vida_nocturna"],
        destino=_zona("Cuzco"),
    )
    noches = _noches(ruta)
    [estrellas] = [n for n, x in noches.items() if x.tipo == "estrellas"]
    assert estrellas == 2  # la noche del 4
    cielo = noches[estrellas].cielo
    # El Cusco tiene la luz de la ciudad: las estrellas, en el planetario.
    assert cielo.desde.tipo == "planetario" and cielo.desde.nombre == "Planetarium Cusco"
    assert cielo.luna.iluminada < 0.05 and cielo.oscurece == "18:50"
    assert cielo.noches_despejadas > 0.8 and cielo.fuente_nubes == "goes"
    assert {x.tipo for n, x in noches.items() if n != estrellas} == {"descanso", "salir"}


@con_datos
def test_sin_fecha_las_estrellas_van_la_segunda_noche_y_dicen_la_luna_nueva():
    ruta = _viaje(origen="arequipa", mes=8, dias=4, destino=_zona("Mazo Cruz"))
    noches = _noches(ruta)
    assert [x.tipo for x in noches.values()] == ["estrellas"]
    [(numero, estrellas)] = noches.items()
    assert numero == 2  # la segunda en la base: la primera se llega cansado
    assert estrellas.cielo.desde.tipo == "base" and estrellas.cielo.desde.clase == "muy_oscuro"
    assert estrellas.cielo.lunas_nuevas == [date(2027, 8, 1), date(2027, 8, 31)]
    assert "la luna nueva es el 1 y el 31" in estrellas.nota
    assert "Vía Láctea de lado a lado" in estrellas.nota


@con_datos
def test_en_un_mes_de_nubes_no_se_proponen_estrellas():
    # En febrero, en el Cusco, sale despejada menos de una noche de cada diez.
    ruta = _viaje(origen="lima", mes=2, dias=6, intereses=["naturaleza"], destino=_zona("Cuzco"))
    assert not _noches(ruta)


@con_datos
def test_solo_lo_que_se_pide():
    cusco = _zona("Cuzco")
    sin_noche = _viaje(origen="lima", mes=7, dias=6, intereses=["historia"], destino=cusco)
    assert not _noches(sin_noche)
    con_naturaleza = _viaje(origen="lima", mes=7, dias=6, intereses=["naturaleza"], destino=cusco)
    assert [x.tipo for x in _noches(con_naturaleza).values()] == ["estrellas"]


@con_datos
def test_la_noche_no_cambia_nada_del_dia():
    cusco = _zona("Cuzco")
    solo_dia = _viaje(origen="lima", mes=7, dias=6, intereses=["historia"], destino=cusco)
    con_noche = _viaje(origen="lima", mes=7, dias=6, intereses=["historia", "vida_nocturna"], destino=cusco)
    sin = {"noche"}
    assert [d.model_dump(exclude=sin) for d in con_noche.dias] == [d.model_dump(exclude=sin) for d in solo_dia.dias]
    assert con_noche.costo == solo_dia.costo and con_noche.traslado == solo_dia.traslado


@con_datos
def test_un_viaje_de_un_dia_no_tiene_noche():
    datos = artefactos.cargar()
    respuesta = viaje.resolver(Consulta(origen="lima", mes=7, dias=1, intereses=["vida_nocturna"]), datos)
    assert respuesta.rutas and not any(d.noche for r in respuesta.rutas for d in r.dias)


@con_datos
def test_sin_lugares_para_salir_lo_dice():
    ruta = _viaje(origen="arequipa", mes=8, dias=4, intereses=["vida_nocturna"], destino=_zona("Yanque"))
    assert not any(n.tipo == "salir" for n in _noches(ruta).values())
    assert any("No tenemos registrados bares" in a.mensaje for a in ruta.avisos)


@con_datos
def test_la_vida_nocturna_pesa_al_elegir_las_zonas():
    datos = artefactos.cargar()
    consulta = Consulta(origen="lima", mes=7, dias=6, intereses=["vida_nocturna"])
    sin_bares = datos.polos[_zona("Yanque")]
    con_bares = datos.polos[_zona("Cuzco")]
    assert noche.factor_de_noche(sin_bares, consulta) == 0.6
    assert noche.factor_de_noche(con_bares, consulta) == 1.0
    assert noche.factor_de_noche(sin_bares, consulta.model_copy(update={"intereses": []})) == 1.0
    con_tres = datos.polos[_zona("Chachapoyas")]
    assert len(con_tres.noche["lugares"]) >= noche.SALIR_PARA_EL_PUNTAJE or noche.factor_de_noche(
        con_tres, consulta
    ) == pytest.approx(0.6 + 0.08 * len(con_tres.noche["lugares"]))
    rutas = viaje.resolver(consulta, datos).rutas
    assert rutas and all(len(datos.polos[r.polo.id].noche["lugares"]) >= 5 for r in rutas)


@con_datos
def test_la_altura_del_origen_es_la_de_su_ciudad():
    datos = artefactos.cargar()
    assert noche.altura_del_origen(datos.origenes["lima"], datos) < 300
    assert noche.altura_del_origen(datos.origenes["cusco"], datos) == datos.polos[_zona("Cuzco")].base["altitud_m"]
    # Del Cusco a Puno no se sube 1 000 m: la primera noche no es de descanso.
    ruta = _viaje(origen="cusco", mes=7, dias=4, intereses=["vida_nocturna"], destino=_zona("Puno"))
    assert all(n.tipo == "salir" for n in _noches(ruta).values())


@con_datos
def test_cada_lugar_se_puede_verificar():
    ruta = _viaje(origen="lima", mes=7, dias=6, intereses=["vida_nocturna"], destino=_zona("Cuzco"))
    for n in _noches(ruta).values():
        for lugar in n.lugares:
            url = str(lugar.url)
            assert url.startswith("https://www.openstreetmap.org/")
            assert (lugar.fuente == "openstreetmap") == ("mlat=" not in url)


@con_datos
def test_la_misma_consulta_da_las_mismas_noches():
    consulta = dict(origen="lima", fecha_inicio=date(2027, 7, 3), dias=6, intereses=["naturaleza", "vida_nocturna"])
    assert _primera(consulta) == _primera(consulta)


def _primera(consulta):
    return viaje.resolver(Consulta(**consulta), artefactos.cargar()).rutas[0].model_dump_json()


def test_para_cada_noche_alterna_tipos_y_no_repite_mientras_alcancen():
    lugares = [{"nombre": f"{t}{i}", "tipo": t} for i in range(3) for t in ("bar", "pub", "discoteca")]
    lugares.sort(key=lambda x: x["nombre"])  # el orden de confianza: el de la lista
    noches = noche.para_cada_noche(lugares, 4)
    assert [len(n) for n in noches] == [3, 3, 3, 3]
    assert all(len({x["tipo"] for x in n}) == 3 for n in noches[:3])
    assert len({x["nombre"] for n in noches[:3] for x in n}) == 9
    assert noches[3] == noches[0]  # se acabaron: vuelve a empezar


def test_cuantos_cuenta_por_tipo_y_en_orden():
    lugares = [{"tipo": t} for t in ["discoteca", "bar", "bar", "pena", "pub", "karaoke", "bar"]]
    assert noche.cuantos(lugares) == "3 bares, 1 pub, 1 discoteca, 1 karaoke y 1 peña"
    assert noche.cuantos(lugares, tipos_max=2) == "3 bares y 1 pub"
