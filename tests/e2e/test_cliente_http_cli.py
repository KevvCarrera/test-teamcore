"""Prueba e2e de `cliente_http.py` (FR-01…FR-08): la CLI completa, sin red real.

Ejercita `main()` en proceso, con los 6 escenarios simulados vía `responses`
y los artefactos escritos en un `out/` dentro de un directorio temporal
(`monkeypatch.chdir`), ya que la CLI no acepta una ruta de salida por
parámetro (el enunciado no la define para esta parte).
"""

from pathlib import Path

import pytest
import responses

from teamcore_http_kpi.cli._common import EXIT_OK
from teamcore_http_kpi.cli.cliente_http import main
from teamcore_http_kpi.config import DEFAULT_SETTINGS

_BASE_URL = DEFAULT_SETTINGS.base_url


def _register_all_happy_paths() -> None:
    settings = DEFAULT_SETTINGS
    responses.add(
        responses.GET,
        f"{_BASE_URL}/basic-auth/{settings.basic_auth_user}/{settings.basic_auth_password}",
        json={"authenticated": True, "user": settings.basic_auth_user},
        status=200,
    )
    responses.add(responses.GET, f"{_BASE_URL}/cookies/set", status=200)
    responses.add(
        responses.GET, f"{_BASE_URL}/cookies", json={"cookies": {"session": "activa"}}, status=200
    )
    for _ in range(4):
        responses.add(responses.GET, f"{_BASE_URL}/status/403", status=403)
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)
    responses.add(
        responses.GET, f"{_BASE_URL}/xml", body=b"<slideshow title='S'/>", status=200
    )
    responses.add(
        responses.GET, f"{_BASE_URL}/html", body="<html><title>T</title></html>", status=200
    )
    form = {
        "nombre": settings.form_data.nombre,
        "apellido": settings.form_data.apellido,
        "correo": settings.form_data.correo,
        "mensaje": settings.form_data.mensaje,
    }
    responses.add(responses.POST, f"{_BASE_URL}/post", json={"form": form}, status=200)
    responses.add(
        responses.GET,
        f"{_BASE_URL}/redirect-to",
        status=302,
        headers={"Location": f"{_BASE_URL}/get"},
    )
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)


@pytest.mark.e2e
@responses.activate
def test_cliente_http_writes_all_artifacts_and_exits_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _register_all_happy_paths()

    exit_code = main()

    assert exit_code == EXIT_OK
    assert (tmp_path / "out" / "datos.json").exists()
    assert (tmp_path / "out" / "datos.xml").exists()
    assert (tmp_path / "out" / "titulo.html").exists()
