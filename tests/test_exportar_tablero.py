"""La copia independiente incorpora agregados, sin necesitar una lectura posterior."""

import json

import pytest

from evaluacion.exportar_tablero import MARCADOR, exportar


def test_exportar_incrusta_simulacion_y_preserva_el_resto_del_html(tmp_path):
    ruta = tmp_path / "tablero.html"
    ruta.write_text(
        '<h1>Prueba</h1><script id="datos-iniciales" type="application/json">{}</script><footer>Fin</footer>'
    )
    exportar(ruta)
    texto = ruta.read_text(encoding="utf-8")
    assert texto.startswith("<h1>Prueba</h1>") and texto.endswith("<footer>Fin</footer>")
    bloque = MARCADOR.search(texto)
    contenido = bloque.group(0).removeprefix(bloque.group(1)).removesuffix(bloque.group(2))
    datos = json.loads(contenido)
    assert datos["modo"] == "simulacion"
    assert next(i["valor"] for i in datos["indicadores"] if i["id"] == "sesiones") == 200
    assert len(datos["analisis"]["mapa_calor"]) == 168
    assert "eventos" not in datos and "usuarios" not in datos


@pytest.mark.parametrize(
    "texto",
    [
        "<h1>No hay bloque de datos</h1>",
        '<script id="datos-iniciales" type="application/json">{}</script>' * 2,
    ],
)
def test_exportar_no_reescribe_una_plantilla_sin_marcador_unico(tmp_path, texto):
    ruta = tmp_path / "tablero.html"
    ruta.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError, match="único bloque"):
        exportar(ruta)
    assert ruta.read_text(encoding="utf-8") == texto
