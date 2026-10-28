"""Las cifras de la prueba de usabilidad (semana 12): el SUS con cuentas hechas a mano, las tareas y las
planillas sin llenar."""

import pytest

from evaluacion import usabilidad


def _escribir(carpeta, nombre, filas):
    (carpeta / nombre).write_text("﻿" + "\n".join(";".join(f) for f in filas) + "\n", encoding="utf-8")


def _planillas(carpeta, tareas=None):
    _escribir(
        carpeta,
        "participantes.csv",
        [["participante", "dispositivo", "fecha", "viajes_al_anio"], ["P1", "celular", "2026-10-26", "2-3"]]
        + [["P2", "computadora", "2026-10-26", "0-1"], ["P3", "", "", ""]],
    )
    _escribir(
        carpeta,
        "sus.csv",
        [["participante", *usabilidad.FRASES], ["P1", *"4242424242"], ["P2", *"3333333333"], ["P3", *[""] * 10]],
    )
    _escribir(
        carpeta,
        "tareas.csv",
        tareas
        or [
            ["participante", "tarea", "resultado", "segundos", "errores", "observaciones"],
            ["P1", "T1", "sola", "70", "0", ""],
            ["P2", "T1", "con_ayuda", "150", "2", "No vio dónde se cambia el mes"],
            ["P1", "T4", "no", "240", "3", ""],
            ["P2", "T4", "sola", "90", "1", ""],
            ["P3", "T1", "", "", "", ""],
        ],
    )
    _escribir(
        carpeta,
        "comentarios.csv",
        [["participante", "lo_mas_util", "lo_que_cambiaria"], ["P1", "El plan por día", "El mapa"], ["P2", "", ""]],
    )


def test_el_sus_de_una_persona():
    assert usabilidad.puntaje_sus([3] * 10) == 50
    assert usabilidad.puntaje_sus([5, 1] * 5) == 100
    assert usabilidad.puntaje_sus([1, 5] * 5) == 0
    assert usabilidad.puntaje_sus([4, 2] * 5) == 75


@pytest.mark.parametrize("respuestas", [[3] * 9, [3] * 9 + [6], [0] * 10])
def test_el_sus_pide_diez_respuestas_del_1_al_5(respuestas):
    with pytest.raises(ValueError):
        usabilidad.puntaje_sus(respuestas)


def test_el_adjetivo_es_el_de_la_media_mas_cercana():
    assert usabilidad.adjetivo(68) == "Buena"
    assert usabilidad.adjetivo(80) == "Excelente"
    assert usabilidad.adjetivo(90) == "Lo mejor imaginable"
    assert usabilidad.adjetivo(40) == "Mala"


def test_las_planillas_del_repositorio_todavia_sin_llenar():
    r = usabilidad.calcular()
    assert r["participantes"] == 0 and r["sus"] is None and r["tareas"] == {} and r["comentarios"] == []


def test_las_cifras_de_una_prueba(tmp_path):
    _planillas(tmp_path)
    r = usabilidad.calcular(tmp_path)
    assert r["participantes"] == 2 and r["dispositivos"] == {"celular": 1, "computadora": 1}
    assert r["sus_por_persona"] == {"P1": 75, "P2": 50}
    assert r["sus"]["media"] == pytest.approx(62.5) and r["sus"]["sobre_la_media_de_referencia"] == 1
    t1, t4 = r["tareas"]["T1"], r["tareas"]["T4"]
    assert (t1["sola"], t1["con_ayuda"], t1["no"], t1["logradas"]) == (1, 1, 0, 1.0)
    assert t1["segundos_mediana"] == 110 and t1["errores_media"] == 1
    assert t4["logradas"] == 0.5 and t4["segundos_mediana"] == 90  # el tiempo es de quienes la lograron
    assert r["comentarios"] == [{"participante": "P1", "lo_mas_util": "El plan por día", "lo_que_cambiaria": "El mapa"}]


def test_un_resultado_que_no_es_de_la_guia_se_rechaza(tmp_path):
    cabecera = ["participante", "tarea", "resultado", "segundos", "errores", "observaciones"]
    _planillas(tmp_path, tareas=[cabecera, ["P1", "T1", "casi", "70", "0", ""]])
    with pytest.raises(ValueError, match="casi"):
        usabilidad.calcular(tmp_path)
