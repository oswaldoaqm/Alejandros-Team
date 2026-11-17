"""Comprobaciones independientes de la entrega comercial ficticia.

Contrasta dos archivos y las relaciones del recorrido. No usa el generador para
calcular los valores esperados, de modo que detecta datos truncados o incoherentes.
"""

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from uuid import UUID

DATOS = Path(__file__).resolve().parents[1] / "data" / "simulacion"
JSON = DATOS / "negocio_300.json"
CSV = DATOS / "negocio_300.csv"


def _leer():
    contenido = json.loads(JSON.read_text(encoding="utf-8"))
    with CSV.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter=";"))
    return contenido, filas


def test_archivos_identifican_la_misma_cohorte_ficticia():
    contenido, filas = _leer()
    meta, registros = contenido["meta"], contenido["registros"]
    assert meta["tipo"] == "simulacion_comercial"
    assert meta["usuarios_ficticios"] == len(registros) == len(filas) == 300
    assert meta["fecha_inicio"] == min(r["fecha_local"] for r in registros)
    assert meta["fecha_fin"] == max(r["fecha_local"] for r in registros)
    assert len({r["usuario_id"] for r in registros}) == 300
    assert len({r["sesion"] for r in registros}) == 300
    assert [r["usuario_id"] for r in registros] == [r["usuario_id"] for r in filas]
    for registro, fila in zip(registros, filas, strict=True):
        UUID(registro["sesion"])
        date.fromisoformat(registro["fecha_local"])
        assert registro["sesion"] == fila["sesion"]
        assert registro["fecha_local"] == fila["fecha_local"]
        for campo in (
            "visito",
            "interactuo",
            "busco",
            "vio_propuestas",
            "abrio_propuesta",
            "acepto_propuesta",
            "compra_simulada",
            "guardo",
            "compartio",
        ):
            assert fila[campo] == str(registro[campo])
        for campo in ("importe_simulado", "costo_variable_simulado", "propuestas_mostradas"):
            assert int(fila[campo]) == registro[campo]


def test_embudo_opciones_y_compras_no_cuentan_eventos_imposibles():
    contenido, _ = _leer()
    registros = contenido["registros"]
    etapas = Counter()
    for r in registros:
        assert r["visito"] is True
        assert not r["interactuo"] or r["visito"]
        assert not r["busco"] or r["interactuo"]
        assert not r["vio_propuestas"] or r["busco"]
        assert not r["abrio_propuesta"] or r["vio_propuestas"]
        assert not r["acepto_propuesta"] or r["abrio_propuesta"]
        assert not r["compra_simulada"] or r["acepto_propuesta"]
        assert r["propuestas_mostradas"] == (2 if r["vio_propuestas"] else 0)
        assert (r["propuesta_abierta"] in {"A", "B"}) == r["abrio_propuesta"]
        assert (r["propuesta_aceptada"] in {"A", "B"}) == r["acepto_propuesta"]
        if r["acepto_propuesta"]:
            assert r["propuesta_aceptada"] == r["propuesta_abierta"]
        if r["vio_propuestas"]:
            assert isinstance(r["polo_A"], int) and isinstance(r["polo_B"], int)
            assert r["polo_A"] != r["polo_B"]
        else:
            assert r["polo_A"] is None and r["polo_B"] is None
        assert r["importe_simulado"] >= 0 and r["costo_variable_simulado"] >= 0
        if not r["compra_simulada"]:
            assert r["importe_simulado"] == r["costo_variable_simulado"] == 0
        etapas[r["etapa_final"]] += 1
    assert sum(etapas.values()) == 300
    assert etapas["compra_simulada"] == sum(r["compra_simulada"] for r in registros)
    assert etapas["aceptacion_sin_compra"] == sum(r["acepto_propuesta"] and not r["compra_simulada"] for r in registros)
    assert (
        sum(r["visito"] for r in registros)
        >= sum(r["interactuo"] for r in registros)
        >= sum(r["busco"] for r in registros)
        >= sum(r["vio_propuestas"] for r in registros)
        >= sum(r["abrio_propuesta"] for r in registros)
        >= sum(r["acepto_propuesta"] for r in registros)
        >= sum(r["compra_simulada"] for r in registros)
    )


def test_resultado_economico_surge_de_compras_ficticias_y_supuestos():
    contenido, _ = _leer()
    meta, registros = contenido["meta"], contenido["registros"]
    supuestos = meta["supuestos_economicos"]
    operaciones = sum(r["compra_simulada"] for r in registros)
    ingresos = sum(r["importe_simulado"] for r in registros)
    variables = sum(r["costo_variable_simulado"] for r in registros)
    assert ingresos == operaciones * supuestos["ingreso_por_compra_simulada_soles"]
    assert variables == operaciones * supuestos["costo_variable_por_compra_simulada_soles"]
    costos = variables + supuestos["costo_fijo_periodo_soles"] + supuestos["presupuesto_marketing_periodo_soles"]
    assert costos >= 0
    assert (
        ingresos - costos
        == sum(r["importe_simulado"] - r["costo_variable_simulado"] for r in registros)
        - supuestos["costo_fijo_periodo_soles"]
        - supuestos["presupuesto_marketing_periodo_soles"]
    )
    assert "SIMULACIÓN" in meta["etiqueta"]
    assert "fictici" in meta["definiciones"]["compra_simulada"].lower()


def test_segmentos_disjuntos_reconcilian_cohorte_y_montos():
    contenido, _ = _leer()
    registros = contenido["registros"]
    for campo in ("canal_simulado", "propuesta_abierta", "fecha_local"):
        grupos = {valor: [r for r in registros if r[campo] == valor] for valor in {r[campo] for r in registros}}
        assert sum(len(grupo) for grupo in grupos.values()) == 300
        for metrica in ("acepto_propuesta", "compra_simulada", "importe_simulado", "costo_variable_simulado"):
            assert sum(sum(r[metrica] for r in grupo) for grupo in grupos.values()) == sum(
                r[metrica] for r in registros
            )
    sin_apertura = [r for r in registros if r["propuesta_abierta"] is None]
    assert all(not r["acepto_propuesta"] and not r["compra_simulada"] for r in sin_apertura)


def test_escenario_filtrado_conserva_costos_del_periodo():
    contenido, _ = _leer()
    meta, registros = contenido["meta"], contenido["registros"]
    redes = [r for r in registros if r["canal_simulado"] == "Redes sociales"]
    assert len(redes) == 92
    assert sum(r["compra_simulada"] for r in redes) == 15
    ingresos = sum(r["importe_simulado"] for r in redes)
    variable = sum(r["costo_variable_simulado"] for r in redes)
    supuestos = meta["supuestos_economicos"]
    fijo = supuestos["costo_fijo_periodo_soles"]
    marketing = supuestos["presupuesto_marketing_periodo_soles"]
    assert (ingresos, variable, fijo, marketing) == (300, 75, 500, 300)
    assert ingresos - variable - fijo - marketing == -575
