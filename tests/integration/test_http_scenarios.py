"""Pruebas de integración de `application.http_scenarios.run_all` (FR-01…FR-08).

Verifica que un fallo en un escenario no impide que se ejecuten los demás, y
que el orden y el conteo de resultados son los esperados.
"""

from pathlib import Path

import pytest
import responses

from teamcore_http_kpi.application.http_scenarios import run_all
from teamcore_http_kpi.config import Settings
from teamcore_http_kpi.infrastructure.http.client import RequestsHttpClient
from teamcore_http_kpi.infrastructure.io.artifact_writer import FileSystemArtifactWriter

_BASE_URL = "https://httpbin.org"
_SETTINGS = Settings()


def _client() -> RequestsHttpClient:
    return RequestsHttpClient(
        _BASE_URL, timeout=5.0, max_retries=3, backoff_factor=0.01, sleep=lambda _s: None
    )


def _register_all_happy_paths() -> None:
    responses.add(
        responses.GET,
        f"{_BASE_URL}/basic-auth/{_SETTINGS.basic_auth_user}/{_SETTINGS.basic_auth_password}",
        json={"authenticated": True, "user": _SETTINGS.basic_auth_user},
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
        responses.GET,
        f"{_BASE_URL}/xml",
        body=b"<slideshow title='S'><slide/></slideshow>",
        status=200,
    )
    responses.add(
        responses.GET, f"{_BASE_URL}/html", body="<html><title>T</title></html>", status=200
    )
    form = {
        "nombre": _SETTINGS.form_data.nombre,
        "apellido": _SETTINGS.form_data.apellido,
        "correo": _SETTINGS.form_data.correo,
        "mensaje": _SETTINGS.form_data.mensaje,
    }
    responses.add(responses.POST, f"{_BASE_URL}/post", json={"form": form}, status=200)
    responses.add(
        responses.GET,
        f"{_BASE_URL}/redirect-to",
        status=302,
        headers={"Location": f"{_BASE_URL}/get"},
    )
    # segunda llamada a /get, para el salto de la redirección
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)


@pytest.mark.integration
@responses.activate
def test_run_all_returns_8_results_all_ok(tmp_out: Path) -> None:
    _register_all_happy_paths()
    results = run_all(_client(), FileSystemArtifactWriter(), _SETTINGS, tmp_out)

    assert len(results) == 8
    assert all(result.ok for result in results)


@pytest.mark.integration
@responses.activate
def test_one_failure_does_not_stop_the_rest(tmp_out: Path) -> None:
    # /basic-auth falla, pero el resto de escenarios se registra igual.
    responses.add(
        responses.GET,
        f"{_BASE_URL}/basic-auth/{_SETTINGS.basic_auth_user}/{_SETTINGS.basic_auth_password}",
        json={"authenticated": False},
        status=401,
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
    responses.add(responses.POST, f"{_BASE_URL}/post", json={"form": {}}, status=200)
    responses.add(
        responses.GET,
        f"{_BASE_URL}/redirect-to",
        status=302,
        headers={"Location": f"{_BASE_URL}/get"},
    )
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)

    results = run_all(_client(), FileSystemArtifactWriter(), _SETTINGS, tmp_out)

    assert len(results) == 8
    by_name = {result.name: result for result in results}
    assert by_name["Autenticación básica"].ok is False
    assert by_name["Cookies y sesión"].ok is True
    assert (tmp_out / "datos.json").exists()  # el resto de escenarios sí corrió


@pytest.mark.integration
@responses.activate
def test_a_failed_scenario_never_logs_the_password(
    tmp_out: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Mismo registro que test_one_failure_does_not_stop_the_rest: /basic-auth falla.
    responses.add(
        responses.GET,
        f"{_BASE_URL}/basic-auth/{_SETTINGS.basic_auth_user}/{_SETTINGS.basic_auth_password}",
        json={"authenticated": False},
        status=401,
    )
    responses.add(responses.GET, f"{_BASE_URL}/cookies/set", status=200)
    responses.add(
        responses.GET, f"{_BASE_URL}/cookies", json={"cookies": {"session": "activa"}}, status=200
    )
    for _ in range(4):
        responses.add(responses.GET, f"{_BASE_URL}/status/403", status=403)
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)
    responses.add(responses.GET, f"{_BASE_URL}/xml", body=b"<slideshow title='S'/>", status=200)
    responses.add(
        responses.GET, f"{_BASE_URL}/html", body="<html><title>T</title></html>", status=200
    )
    responses.add(responses.POST, f"{_BASE_URL}/post", json={"form": {}}, status=200)
    responses.add(
        responses.GET,
        f"{_BASE_URL}/redirect-to",
        status=302,
        headers={"Location": f"{_BASE_URL}/get"},
    )
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)

    with caplog.at_level("WARNING"):
        run_all(_client(), FileSystemArtifactWriter(), _SETTINGS, tmp_out)

    assert _SETTINGS.basic_auth_password not in caplog.text
