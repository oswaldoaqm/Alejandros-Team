"""El informe de la evaluación (decisión 0021), con un kit y calificaciones de juguete: como las descarga el
cuadernillo o como las deja Excel, y uno que no es del kit."""

import csv
import json
import sys

import pytest

from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from evaluacion import consultas, informe

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

CLAVE = [
    # consulta, opción, polo, zona, puesto del sistema a, del b
    (1, "A", 70, "Huacho", 1, ""),
    (1, "B", 33, "Huancayo", 2, 1),
    (1, "C", 14, "Huaraz", "", 2),
    (2, "A", 85, "Los Órganos", 1, 1),
]


def _kit(tmp_path, notas: dict[str, list], separador=";", codificacion="utf-8-sig"):
    clave = tmp_path / "clave.csv"
    with open(clave, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";", lineterminator="\n")
        w.writerow(["consulta", "opcion", "polo", "zona", "puesto_a", "puesto_b", "version_datos", "kit"])
        w.writerows([[*fila, "2026.10.8", "x"] for fila in CLAVE])
    carpeta = tmp_path / "calificaciones"
    carpeta.mkdir()
    for quien, valores in notas.items():
        with open(carpeta / f"{quien}.csv", "w", encoding=codificacion, newline="") as fh:
            w = csv.writer(fh, delimiter=separador, lineterminator="\r\n")
            w.writerow(["consulta", "opcion", "zona", "calificacion", "comentario"])
            w.writerows([[c, o, z, v, ""] for (c, o, _, z, *_), v in zip(CLAVE, valores, strict=True)])
    return clave, carpeta


def test_si_todos_coinciden_el_acuerdo_es_total_y_gana_quien_propone_lo_mejor(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 0, 2, 1], "CD": [2, 0, 2, 1], "EF": [2, 0, 2, 1]})
    notas, filas, resumen = informe.calcular(clave, carpeta)
    assert resumen["acuerdo"]["kappa_fleiss"] == pytest.approx(1)
    assert resumen["acuerdo"]["alfa_krippendorff_ordinal"] == pytest.approx(1)
    assert [n["media"] for n in notas] == [2, 0, 2, 1]
    por = {(f["consulta"], f["sistema"]): f for f in filas}
    assert por[(1, "a")]["ndcg3"] == pytest.approx(1 / (1 + 1 / 1.585), abs=1e-3)  # el 2.º era el peor
    assert por[(1, "b")]["ndcg3"] < por[(1, "a")]["ndcg3"] and por[(2, "a")]["ndcg3"] == 1
    assert resumen["cobertura"]["a"]["zonas_distintas"] == 3


def test_lee_lo_que_deja_excel_con_comas_y_en_windows_1252(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 1, 0, 2], "CD": [1, 1, 0, ""]}, separador=",", codificacion="cp1252")
    notas, _, resumen = informe.calcular(clave, carpeta)
    assert notas[3]["zona"] == "Los Órganos" and notas[3]["media"] == 2
    assert resumen["acuerdo"]["viajes_con_todas_las_notas"] == 3


def test_se_niega_si_unas_calificaciones_son_de_otro_kit(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 1, 0, 2], "CD": [1, 1, 0, 2]})
    ruta = carpeta / "CD.csv"
    ruta.write_text(ruta.read_text(encoding="utf-8-sig").replace("Huaraz", "Caraz"), encoding="utf-8-sig")
    with pytest.raises(ValueError, match="CD.csv no es de este kit"):
        informe.calcular(clave, carpeta)


def test_la_nota_segun_cuanto_del_viaje_se_lleva_el_bus_de_noche(tmp_path):
    """Lo que vio quien calificó: la consulta 1 es de dos días, así que 8 h 24 de bus por tramo son el 35 % del
    viaje (decisión 0027)."""
    clave, carpeta = _kit(tmp_path, {"AB": [2, 0, 2, 1], "CD": [1, 0, 2, 1]})
    tarjeta = "<article class='opcion' id='c{}-{}'><p>{}</p></article>"
    cuadernillo = tmp_path / "cuadernillo.html"
    cuadernillo.write_text(
        tarjeta.format(1, "A", "En bus de noche: sale a las 21:30 y llega a las 06:00, 8 h 24 de puerta a puerta.")
        + tarjeta.format(1, "B", "Por carretera, 5 h 10 de puerta a puerta.")
        + tarjeta.format(1, "C", "En bus de noche: sale a las 22:00 y llega a las 05:00, 7 h de puerta a puerta.")
        + tarjeta.format(2, "A", "En avión (Lima–Piura), 4 h 30 de puerta a puerta."),
        encoding="utf-8",
    )
    partes = informe.parte_en_bus(cuadernillo.read_text(encoding="utf-8"), {1: 2, 2: 5})
    assert partes[(1, "A")] == pytest.approx(0.35) and partes[(1, "C")] == pytest.approx(7 / 24)
    assert partes[(1, "B")] is None and partes[(2, "A")] is None
    _, _, resumen = informe.calcular(clave, carpeta, cuadernillo)
    assert resumen["nota_por_parte_en_bus"] == {
        "del_20_al_30": {"viajes": 1, "media": 2.0, "no_encajan": 0.0},
        "del_30_al_40": {"viajes": 1, "media": 1.5, "no_encajan": 0.0},
        "sin_bus_de_noche": {"viajes": 2, "media": 0.5, "no_encajan": 0.5},
    }


def test_lo_que_propone_el_motor_de_ahora_contra_el_kit():
    """Si el motor de ahora propone lo mismo que el del kit, no cambia nada; si cambia el primer puesto, se dice
    cuál era, cuál es y qué nota tenían."""
    datos = artefactos.cargar()
    [c1] = [c for c in consultas.leer() if c.id == 1]
    ahora = [r.polo.id for r in viaje.resolver(c1.consulta, datos, sugerir=False).rutas]
    viajes = [informe.Viaje(1, "ABC"[i], p, f"Zona {p}", {"motor": i + 1}) for i, p in enumerate(ahora)]
    media = {(1, v.opcion): float(i) for i, v in enumerate(viajes)}
    igual = informe.motor_de_ahora(viajes, media, datos)
    assert (igual["consultas_que_cambian"], igual["sin_nota_en_el_kit"], igual["otro_primer_puesto"]) == (0, 0, [])
    al_reves = [informe.Viaje(1, v.opcion, v.polo, v.zona, {"motor": len(viajes) - i}) for i, v in enumerate(viajes)]
    otro = informe.motor_de_ahora(al_reves, media, datos)
    assert otro["consultas_que_cambian"] == 1
    assert otro["otro_primer_puesto"] == [
        {
            "consulta": 1,
            "antes": viajes[-1].zona,
            "nota_antes": media[(1, viajes[-1].opcion)],
            "ahora": viajes[0].zona,
            "nota_ahora": 0.0,
        }
    ]


def test_una_opcion_sin_juzgar_deja_la_consulta_pendiente_no_la_convierte_en_cero(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, "", 0, 2], "CD": [2, "", 0, 2]})
    notas, filas, resumen = informe.calcular(clave, carpeta)
    assert notas[1]["media"] == ""
    assert notas[2]["media"] == 0  # Un cero explícito sí es una valoración.
    assert {f["consulta"] for f in filas} == {2}
    assert resumen["evaluacion"]["consultas_pendientes"] == [1]
    assert resumen["evaluacion"]["consultas_evaluadas"] == 1
    assert resumen["evaluacion"]["viajes_sin_calificar"] == 1
    assert resumen["por_sistema"]["a"]["ndcg3"] == 1


def test_sin_valoraciones_no_inventa_metricas_ni_acuerdo_y_genera_el_informe(tmp_path, monkeypatch, capsys):
    clave, carpeta = _kit(tmp_path, {"AB": ["", "", "", ""], "CD": ["", "", "", ""]})
    salida = tmp_path / "resultados"
    monkeypatch.setattr(
        sys, "argv", ["informe", "--clave", str(clave), "--calificaciones", str(carpeta), "--salida", str(salida)]
    )
    informe.main()
    resumen = json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["evaluacion"]["consultas_evaluadas"] == 0
    assert resumen["evaluacion"]["consultas_pendientes"] == [1, 2]
    assert resumen["acuerdo"]["kappa_fleiss"] is None
    assert resumen["acuerdo"]["alfa_krippendorff_ordinal"] is None
    assert resumen["por_sistema"]["a"]["ndcg3"] is None
    assert resumen["comparaciones"] == {}
    assert len((salida / "metricas.csv").read_text(encoding="utf-8-sig").splitlines()) == 1
    assert "sin datos suficientes" in capsys.readouterr().out


def test_con_una_sola_nota_por_opcion_no_afirma_acuerdo_entre_personas(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 0, "", ""], "CD": ["", "", 1, 2]})
    _, filas, resumen = informe.calcular(clave, carpeta)
    assert len(filas) == 4
    assert resumen["acuerdo"]["kappa_fleiss"] is None
    assert resumen["acuerdo"]["alfa_krippendorff_ordinal"] is None


def test_una_calificacion_duplicada_no_sobrescribe_la_primera(tmp_path):
    clave, carpeta = _kit(tmp_path, {"AB": [2, 1, 0, 2], "CD": [1, 1, 0, 2]})
    ruta = carpeta / "CD.csv"
    with ruta.open("a", encoding="utf-8", newline="") as archivo:
        archivo.write("1;A;Huacho;0;\n")
    with pytest.raises(ValueError, match="duplicada"):
        informe.calcular(clave, carpeta)


def test_una_clave_vacia_se_explica_con_un_error_claro(tmp_path):
    clave = tmp_path / "clave.csv"
    clave.write_text("consulta;opcion;polo;zona;puesto_a\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no contiene viajes"):
        informe.leer_clave(clave)
