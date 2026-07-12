"""Pruebas de integración de los 6 escenarios del cliente HTTP (FR-01…FR-08).

Usa `responses` para simular httpbin.org, un `RequestsHttpClient` real (con
`sleep` inyectado como no-op) y un `FileSystemArtifactWriter` real sobre
`tmp_path`, según docs/testing/test-strategy.md.
"""

import json
from pathlib import Path

import pytest
import responses

from teamcore_http_kpi.config import Settings
from teamcore_http_kpi.domain.errors import HttpTaskError
from teamcore_http_kpi.infrastructure.http import tasks
from teamcore_http_kpi.infrastructure.http.client import RequestsHttpClient
from teamcore_http_kpi.infrastructure.io.artifact_writer import FileSystemArtifactWriter

_BASE_URL = "https://httpbin.org"
_SETTINGS = Settings()


def _client() -> RequestsHttpClient:
    return RequestsHttpClient(
        _BASE_URL, timeout=5.0, max_retries=3, backoff_factor=0.01, sleep=lambda _s: None
    )


# --- FR-01: autenticación básica -------------------------------------------------


@pytest.mark.integration
@responses.activate
def test_basic_auth_success() -> None:
    responses.add(
        responses.GET,
        f"{_BASE_URL}/basic-auth/{_SETTINGS.basic_auth_user}/{_SETTINGS.basic_auth_password}",
        json={"authenticated": True, "user": _SETTINGS.basic_auth_user},
        status=200,
    )
    detail = tasks.basic_auth(_client(), _SETTINGS)
    assert _SETTINGS.basic_auth_user in detail


@pytest.mark.integration
@responses.activate
def test_basic_auth_failure_raises() -> None:
    responses.add(
        responses.GET,
        f"{_BASE_URL}/basic-auth/{_SETTINGS.basic_auth_user}/{_SETTINGS.basic_auth_password}",
        json={"authenticated": False},
        status=401,
    )
    with pytest.raises(HttpTaskError):
        tasks.basic_auth(_client(), _SETTINGS)


# --- FR-02: cookies y sesión ------------------------------------------------------


@pytest.mark.integration
@responses.activate
def test_set_and_get_cookies_success() -> None:
    responses.add(responses.GET, f"{_BASE_URL}/cookies/set", status=200)
    responses.add(
        responses.GET, f"{_BASE_URL}/cookies", json={"cookies": {"session": "activa"}}, status=200
    )
    detail = tasks.set_and_get_cookies(_client())
    assert "activa" in detail


@pytest.mark.integration
@responses.activate
def test_set_and_get_cookies_failure_raises() -> None:
    responses.add(responses.GET, f"{_BASE_URL}/cookies/set", status=200)
    responses.add(responses.GET, f"{_BASE_URL}/cookies", json={"cookies": {}}, status=200)
    with pytest.raises(HttpTaskError):
        tasks.set_and_get_cookies(_client())


# --- FR-03: restricción de acceso (403) -------------------------------------------


@pytest.mark.integration
@responses.activate
def test_simulate_forbidden_handles_403_as_success() -> None:
    for _ in range(4):  # 1 intento + 3 reintentos
        responses.add(responses.GET, f"{_BASE_URL}/status/403", status=403)
    detail = tasks.simulate_forbidden(_client())
    assert "403" in detail


@pytest.mark.integration
@responses.activate
def test_simulate_forbidden_raises_if_no_403_received() -> None:
    responses.add(responses.GET, f"{_BASE_URL}/status/403", status=200)
    with pytest.raises(HttpTaskError):
        tasks.simulate_forbidden(_client())


# --- FR-04: extracción JSON --------------------------------------------------------


@pytest.mark.integration
@responses.activate
def test_extract_json_writes_datos_json(tmp_out: Path) -> None:
    payload = {"args": {}, "url": f"{_BASE_URL}/get"}
    responses.add(responses.GET, f"{_BASE_URL}/get", json=payload, status=200)

    tasks.extract_json(_client(), FileSystemArtifactWriter(), tmp_out)

    written = json.loads((tmp_out / "datos.json").read_text(encoding="utf-8"))
    assert written == payload


# --- FR-05: extracción XML ---------------------------------------------------------


@pytest.mark.integration
@responses.activate
def test_extract_xml_writes_well_formed_xml(tmp_out: Path) -> None:
    xml_body = (
        b"<?xml version='1.0' encoding='us-ascii'?>"
        b"<slideshow title=\"Sample Slide Show\"><slide><title>Wake up</title></slide></slideshow>"
    )
    responses.add(
        responses.GET, f"{_BASE_URL}/xml", body=xml_body, status=200,
        content_type="application/xml",
    )

    detail = tasks.extract_xml(_client(), FileSystemArtifactWriter(), tmp_out)

    assert "Sample Slide Show" in detail
    destination = tmp_out / "datos.xml"
    assert destination.exists()
    from lxml import etree

    parsed = etree.fromstring(destination.read_bytes())
    assert parsed.tag == "slideshow"


# --- FR-06: extracción de título HTML -----------------------------------------------


@pytest.mark.integration
@responses.activate
def test_extract_html_title_from_title_tag(tmp_out: Path) -> None:
    html_body = "<html><head><title>Mi Título</title></head><body></body></html>"
    responses.add(responses.GET, f"{_BASE_URL}/html", body=html_body, status=200)

    detail = tasks.extract_html_title(_client(), FileSystemArtifactWriter(), tmp_out)

    assert "Mi Título" in detail
    assert "Mi Título" in (tmp_out / "titulo.html").read_text(encoding="utf-8")


@pytest.mark.integration
@responses.activate
def test_extract_html_title_falls_back_to_h1(tmp_out: Path) -> None:
    html_body = "<html><head></head><body><h1>Herman Melville - Moby-Dick</h1></body></html>"
    responses.add(responses.GET, f"{_BASE_URL}/html", body=html_body, status=200)

    detail = tasks.extract_html_title(_client(), FileSystemArtifactWriter(), tmp_out)

    assert "Moby-Dick" in detail
    assert "Moby-Dick" in (tmp_out / "titulo.html").read_text(encoding="utf-8")


@pytest.mark.integration
@responses.activate
def test_extract_html_title_raises_without_title_or_heading(tmp_out: Path) -> None:
    html_body = "<html><head></head><body><p>Sin título ni encabezado</p></body></html>"
    responses.add(responses.GET, f"{_BASE_URL}/html", body=html_body, status=200)

    with pytest.raises(HttpTaskError):
        tasks.extract_html_title(_client(), FileSystemArtifactWriter(), tmp_out)


@pytest.mark.integration
@responses.activate
def test_extract_html_title_escapes_content(tmp_out: Path) -> None:
    html_body = "<html><head><title>&lt;script&gt;</title></head><body></body></html>"
    responses.add(responses.GET, f"{_BASE_URL}/html", body=html_body, status=200)

    tasks.extract_html_title(_client(), FileSystemArtifactWriter(), tmp_out)

    content = (tmp_out / "titulo.html").read_text(encoding="utf-8")
    assert "<script>" not in content


# --- FR-07: envío de formulario ------------------------------------------------------


@pytest.mark.integration
@responses.activate
def test_submit_form_success() -> None:
    form = {
        "nombre": _SETTINGS.form_data.nombre,
        "apellido": _SETTINGS.form_data.apellido,
        "correo": _SETTINGS.form_data.correo,
        "mensaje": _SETTINGS.form_data.mensaje,
    }
    responses.add(responses.POST, f"{_BASE_URL}/post", json={"form": form}, status=200)
    detail = tasks.submit_form(_client(), _SETTINGS)
    assert "correctamente" in detail


@pytest.mark.integration
@responses.activate
def test_submit_form_mismatch_raises() -> None:
    responses.add(responses.POST, f"{_BASE_URL}/post", json={"form": {}}, status=200)
    with pytest.raises(HttpTaskError):
        tasks.submit_form(_client(), _SETTINGS)


# --- FR-08: redirecciones -------------------------------------------------------------


@pytest.mark.integration
@responses.activate
def test_follow_redirect_success() -> None:
    responses.add(
        responses.GET,
        f"{_BASE_URL}/redirect-to",
        status=302,
        headers={"Location": f"{_BASE_URL}/get"},
    )
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)

    detail = tasks.follow_redirect(_client())
    assert "/get" in detail


@pytest.mark.integration
@responses.activate
def test_follow_redirect_without_history_raises() -> None:
    responses.add(responses.GET, f"{_BASE_URL}/redirect-to", json={"args": {}}, status=200)
    with pytest.raises(HttpTaskError):
        tasks.follow_redirect(_client())
