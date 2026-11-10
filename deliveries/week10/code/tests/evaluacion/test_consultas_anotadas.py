"""Las 40 consultas de la evaluación (semana 12, decisión 0021): que el contrato las acepte y que cubran lo
que dice evaluacion/consultas.py."""

from collections import Counter

from dreemgo.contrato import Interes
from evaluacion import consultas


def test_son_cuarenta_con_su_numero_y_su_perfil():
    todas = consultas.leer()
    assert [c.id for c in todas] == list(range(1, 41))
    assert all(len(c.perfil) > 20 for c in todas)


def test_cubren_lo_que_promete_el_producto():
    todas = [c.consulta for c in consultas.leer()]
    origenes = Counter(c.origen for c in todas)
    assert len(origenes) == 15 and origenes["lima"] == 16
    assert {c.mes for c in todas} == set(range(1, 13))
    assert min(c.dias for c in todas) == 2 and max(c.dias for c in todas) == 10
    intereses = Counter(i for c in todas for i in c.intereses)
    assert all(intereses[i] >= 2 for i in Interes)
    assert sum(1 for c in todas if not c.intereses) == 5
    assert sum(1 for c in todas if c.fecha_inicio is not None) == 2
    assert all(any(getattr(c, campo) for c in todas) for campo in ("presupuesto", "altitud_max", "solo_por_tierra"))
    assert any(c.sorpresa for c in todas)
