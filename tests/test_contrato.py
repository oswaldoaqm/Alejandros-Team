"""El contrato rechaza lo que no cumple y acepta lo que sí."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from dreemgo.contrato import (
    ETIQUETAS_INTERES,
    Consulta,
    Costo,
    EventoNuevo,
    Interes,
    Respuesta,
    SinResultado,
)

EJEMPLO = Path(__file__).parents[1] / "docs" / "ejemplos" / "respuesta_ilustrativa.json"


class TestConsulta:
    def test_valores_por_defecto(self):
        c = Consulta(mes=7)
        assert (c.origen, c.dias, c.intereses, c.sorpresa) == ("lima", 6, [], False)

    def test_exige_mes_o_fecha(self):
        with pytest.raises(ValidationError, match="mes de viaje o la fecha"):
            Consulta()

    def test_la_fecha_fija_el_mes(self):
        assert Consulta(fecha_inicio=date(2026, 7, 20)).mes == 7

    def test_mes_y_fecha_que_no_coinciden(self):
        with pytest.raises(ValidationError, match="no coincide"):
            Consulta(mes=8, fecha_inicio=date(2026, 7, 20))

    def test_intereses_sin_repetidos_y_en_orden(self):
        c = Consulta(mes=1, intereses=["playa", "historia", "playa"])
        assert c.intereses == [Interes.playa, Interes.historia]

    @pytest.mark.parametrize(
        "campo, valor",
        [
            ("dias", 0),
            ("dias", 15),
            ("mes", 13),
            ("altitud_max", -1),
            ("altitud_max", 6_001),
            ("presupuesto", 99),
            ("origen", "Lima"),
            ("origen", "l"),
            ("intereses", ["museos"]),
        ],
    )
    def test_fuera_de_rango(self, campo, valor):
        with pytest.raises(ValidationError):
            Consulta(**{"mes": 7, campo: valor})

    def test_rechaza_campos_que_no_existen(self):
        with pytest.raises(ValidationError):
            Consulta(mes=7, moneda="USD")

    def test_cada_interes_tiene_etiqueta(self):
        assert set(ETIQUETAS_INTERES) == set(Interes)


class TestSalida:
    def test_banda_de_costo_ordenada(self):
        with pytest.raises(ValidationError, match="p20"):
            Costo(p20=500, p50=400, p80=600)

    def test_sin_rutas_hay_que_explicar_por_que(self):
        base = {"version_datos": "x", "consulta": {"mes": 2}, "atribucion": []}
        with pytest.raises(ValidationError, match="sin_resultado"):
            Respuesta(rutas=[], **base)
        r = Respuesta(rutas=[], sin_resultado=SinResultado(motivo="Febrero llueve en toda la sierra"), **base)
        assert r.sin_resultado is not None

    def test_el_ejemplo_ilustrativo_cumple_el_contrato(self):
        r = Respuesta.model_validate(json.loads(EJEMPLO.read_text(encoding="utf-8")))
        assert len(r.rutas) == 3
        for ruta in r.rutas:
            assert len(ruta.dias) == r.consulta.dias
            assert {p.recurso.codigo for d in ruta.dias for p in d.paradas}, "cada ruta visita algo"
            for d in ruta.dias:
                assert [p.orden for p in d.paradas] == list(range(1, len(d.paradas) + 1))


class TestEventoNuevo:
    BASE = {
        "nombre": "Festival de la Uva",
        "fecha_inicio": date(2027, 3, 5),
        "fecha_fin": date(2027, 3, 8),
        "distrito": "Lunahuaná",
        "provincia": "Cañete",
        "region": "Lima",
        "publicado_por": "Municipalidad de Lunahuaná",
    }

    def test_valido(self):
        assert EventoNuevo(**self.BASE).nombre == "Festival de la Uva"

    def test_fin_antes_del_inicio(self):
        with pytest.raises(ValidationError, match="anterior"):
            EventoNuevo(**{**self.BASE, "fecha_fin": date(2027, 3, 1)})

    def test_duracion_maxima(self):
        with pytest.raises(ValidationError, match="más de 60 días"):
            EventoNuevo(**{**self.BASE, "fecha_fin": date(2027, 6, 1)})

    def test_coordenadas_juntas_y_dentro_del_peru(self):
        with pytest.raises(ValidationError, match="juntas"):
            EventoNuevo(**{**self.BASE, "lat": -12.9})
        with pytest.raises(ValidationError):
            EventoNuevo(**{**self.BASE, "lat": 40.4, "lon": -3.7})
