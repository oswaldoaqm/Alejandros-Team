"""Una instalación incompleta no debe anunciar que el motor está listo."""

from fastapi.testclient import TestClient

from dreemgo.api.app import app
from dreemgo.motor import datos


def test_el_manifiesto_solo_no_alcanza_para_iniciar_el_motor(tmp_path):
    (tmp_path / "manifiesto.json").write_text("{}", encoding="utf-8")
    assert not datos.hay_datos(tmp_path)


def test_se_necesitan_todos_los_archivos_del_motor(tmp_path):
    for nombre in datos.ARCHIVOS_DEL_MOTOR:
        (tmp_path / nombre).touch()
    assert datos.hay_datos(tmp_path)

    (tmp_path / "eventos.json.gz").unlink()
    assert not datos.hay_datos(tmp_path)


def test_el_api_avisa_si_la_copia_de_datos_esta_incompleta(tmp_path, monkeypatch):
    (tmp_path / "manifiesto.json").write_text("{}", encoding="utf-8")
    comprobar = datos.hay_datos
    monkeypatch.setattr(datos, "hay_datos", lambda: comprobar(tmp_path))

    with TestClient(app) as cliente:
        assert cliente.get("/v1/salud").json()["version_datos"] is None
        respuesta = cliente.get("/v1/viajes", params={"mes": 7})
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "El motor no tiene sus artefactos cargados."
