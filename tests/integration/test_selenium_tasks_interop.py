"""Demuestra que `infrastructure/http/tasks.py` funciona sin cambios con
`SeleniumHttpClient`, no solo con `RequestsHttpClient` (ver ADR-0014): la
misma lógica de negocio, dos adaptadores distintos de `HttpPort`.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from teamcore_http_kpi.config import Settings
from teamcore_http_kpi.domain.errors import HttpTaskError
from teamcore_http_kpi.infrastructure.http import tasks
from teamcore_http_kpi.infrastructure.http.selenium_client import SeleniumHttpClient
from teamcore_http_kpi.infrastructure.io.artifact_writer import FileSystemArtifactWriter

_SETTINGS = Settings()


class _FakeDriver:
    """Doble mínimo de `selenium.webdriver.*` para estas pruebas de interoperabilidad."""

    def __init__(self, results: Sequence[dict[str, Any]]) -> None:
        self._results = list(results)
        self.get_calls: list[str] = []

    def get(self, url: str) -> None:
        self.get_calls.append(url)

    def execute_async_script(self, script: str, *args: object) -> Any:
        return self._results.pop(0)

    def quit(self) -> None:
        pass


def _ok(status: int, text: str, *, redirected: bool = False) -> dict[str, Any]:
    return {"status": status, "text": text, "redirected": redirected, "ok": True}


def _client(results: Sequence[dict[str, Any]]) -> SeleniumHttpClient:
    return SeleniumHttpClient(
        "https://httpbin.org",
        timeout=5.0,
        max_retries=3,
        backoff_factor=0.01,
        driver=_FakeDriver(results),
        sleep=lambda _s: None,
    )


@pytest.mark.integration
def test_basic_auth_works_through_selenium_adapter() -> None:
    client = _client([_ok(200, '{"authenticated": true, "user": "usuario_test"}')])
    detail = tasks.basic_auth(client, _SETTINGS)
    assert "usuario_test" in detail


@pytest.mark.integration
def test_set_and_get_cookies_works_through_selenium_adapter() -> None:
    client = _client([_ok(200, "{}"), _ok(200, '{"cookies": {"session": "activa"}}')])
    detail = tasks.set_and_get_cookies(client)
    assert "activa" in detail


@pytest.mark.integration
def test_simulate_forbidden_works_through_selenium_adapter() -> None:
    client = _client([_ok(403, "")] * 4)
    detail = tasks.simulate_forbidden(client)
    assert "403" in detail


@pytest.mark.integration
def test_extract_json_works_through_selenium_adapter(tmp_out: Path) -> None:
    client = _client([_ok(200, '{"args": {}, "url": "https://httpbin.org/get"}')])
    tasks.extract_json(client, FileSystemArtifactWriter(), tmp_out)
    assert (tmp_out / "datos.json").exists()


@pytest.mark.integration
def test_extract_xml_works_through_selenium_adapter(tmp_out: Path) -> None:
    xml_text = (
        "<slideshow title='Sample Slide Show'><slide><title>Wake up</title></slide></slideshow>"
    )
    client = _client([_ok(200, xml_text)])
    detail = tasks.extract_xml(client, FileSystemArtifactWriter(), tmp_out)
    assert "Sample Slide Show" in detail
    assert (tmp_out / "datos.xml").exists()


@pytest.mark.integration
def test_extract_html_title_works_through_selenium_adapter(tmp_out: Path) -> None:
    client = _client([_ok(200, "<html><head><title>Mi Título</title></head></html>")])
    detail = tasks.extract_html_title(client, FileSystemArtifactWriter(), tmp_out)
    assert "Mi Título" in detail


@pytest.mark.integration
def test_submit_form_works_through_selenium_adapter() -> None:
    form = {
        "nombre": _SETTINGS.form_data.nombre,
        "apellido": _SETTINGS.form_data.apellido,
        "correo": _SETTINGS.form_data.correo,
        "mensaje": _SETTINGS.form_data.mensaje,
    }
    import json as _json

    client = _client([_ok(200, _json.dumps({"form": form}))])
    detail = tasks.submit_form(client, _SETTINGS)
    assert "correctamente" in detail


@pytest.mark.integration
def test_follow_redirect_works_through_selenium_adapter() -> None:
    client = _client([_ok(200, '{"args": {}}', redirected=True)])
    detail = tasks.follow_redirect(client)
    assert "/get" in detail


@pytest.mark.integration
def test_persistent_error_still_raises_http_task_error() -> None:
    client = _client([_ok(503, "")] * 4)
    with pytest.raises(HttpTaskError):
        tasks.extract_json(client, FileSystemArtifactWriter(), Path("unused"))
