"""Pruebas de `SeleniumHttpClient` con un doble del *driver* (sin navegador real).

El doble imita exactamente lo poco que este adaptador necesita de
`selenium.webdriver.*` (`get`, `execute_async_script`, `quit`), igual que
`responses` imita `requests` para `RequestsHttpClient`. Una prueba con un
navegador real de verdad vive aparte, marcada `@pytest.mark.browser`
(excluida por defecto — ver tests/browser/test_selenium_client_live.py).
"""

from collections.abc import Sequence
from typing import Any

import pytest

from teamcore_http_kpi.domain.errors import AccessForbiddenError, HttpTaskError
from teamcore_http_kpi.infrastructure.http.selenium_client import SeleniumHttpClient


class FakeDriver:
    """Doble de `selenium.webdriver.*`: registra llamadas y responde en cola."""

    def __init__(self, results: Sequence[dict[str, Any]]) -> None:
        self._results = list(results)
        self.get_calls: list[str] = []
        self.script_calls: list[tuple[str, str, dict[str, str], str | None]] = []
        self.quit_called = False

    def get(self, url: str) -> None:
        self.get_calls.append(url)

    def execute_async_script(self, script: str, *args: Any) -> Any:
        url, method, headers, body = args
        self.script_calls.append((str(url), str(method), dict(headers), body))
        return self._results.pop(0)

    def quit(self) -> None:
        self.quit_called = True


def _client(
    driver: FakeDriver, *, max_retries: int = 3, retry_on_403: bool = True
) -> SeleniumHttpClient:
    return SeleniumHttpClient(
        "https://httpbin.org",
        timeout=5.0,
        max_retries=max_retries,
        backoff_factor=0.01,
        retry_on_403=retry_on_403,
        driver=driver,
        sleep=lambda _s: None,
    )


def _ok(status: int, text: str, *, redirected: bool = False) -> dict[str, Any]:
    return {"status": status, "text": text, "redirected": redirected, "ok": True}


def _network_failure(message: str) -> dict[str, Any]:
    return {"status": 0, "text": message, "redirected": False, "ok": False}


@pytest.mark.unit
def test_navigates_to_base_url_once_on_construction() -> None:
    driver = FakeDriver([])
    _client(driver)
    assert driver.get_calls == ["https://httpbin.org/"]


@pytest.mark.unit
def test_get_returns_status_and_text() -> None:
    driver = FakeDriver([_ok(200, '{"args": {}}')])
    response = _client(driver).get("/get")

    assert response.status_code == 200
    assert response.json() == {"args": {}}


@pytest.mark.unit
def test_get_sends_basic_auth_header() -> None:
    driver = FakeDriver([_ok(200, '{"authenticated": true}')])
    _client(driver).get("/basic-auth/usuario_test/clave123", auth=("usuario_test", "clave123"))

    _, _, headers, _ = driver.script_calls[0]
    assert headers["Authorization"].startswith("Basic ")


@pytest.mark.unit
def test_response_headers_are_always_empty() -> None:
    """Limitación documentada en ADR-0014: `fetch()` no expone las cabeceras."""
    driver = FakeDriver([_ok(200, "{}")])
    response = _client(driver).get("/get")
    assert response.headers == {}


@pytest.mark.unit
def test_post_sends_urlencoded_body() -> None:
    driver = FakeDriver([_ok(200, '{"form": {}}')])
    _client(driver).post("/post", data={"nombre": "Juan", "apellido": "Pérez"})

    _, method, headers, body = driver.script_calls[0]
    assert method == "POST"
    assert headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert body is not None
    assert "nombre=Juan" in body


@pytest.mark.unit
def test_redirected_flag_populates_history() -> None:
    driver = FakeDriver([_ok(200, '{"args": {}}', redirected=True)])
    response = _client(driver).get("/redirect-to?url=/get")
    assert len(response.history) == 1


@pytest.mark.unit
def test_no_redirect_means_empty_history() -> None:
    driver = FakeDriver([_ok(200, "{}")])
    response = _client(driver).get("/get")
    assert response.history == []


@pytest.mark.unit
def test_403_retries_then_raises_access_forbidden() -> None:
    driver = FakeDriver([_ok(403, "")] * 4)
    with pytest.raises(AccessForbiddenError):
        _client(driver, max_retries=3).get("/status/403")
    assert len(driver.script_calls) == 4


@pytest.mark.unit
def test_403_retries_then_succeeds() -> None:
    driver = FakeDriver([_ok(403, ""), _ok(200, "{}")])
    response = _client(driver, max_retries=3).get("/status/403")
    assert response.status_code == 200


@pytest.mark.unit
def test_403_not_retried_when_disabled() -> None:
    driver = FakeDriver([_ok(403, "")])
    response = _client(driver, max_retries=3, retry_on_403=False).get("/status/403")
    assert response.status_code == 403
    assert len(driver.script_calls) == 1


@pytest.mark.unit
def test_persistent_server_error_raises_http_task_error() -> None:
    driver = FakeDriver([_ok(503, "")] * 4)
    with pytest.raises(HttpTaskError):
        _client(driver, max_retries=3).get("/get")


@pytest.mark.unit
def test_server_error_retried_then_succeeds() -> None:
    driver = FakeDriver([_ok(500, ""), _ok(200, "{}")])
    response = _client(driver).get("/get")
    assert response.status_code == 200
    assert len(driver.script_calls) == 2


@pytest.mark.unit
def test_fetch_failure_retried_then_raises_http_task_error() -> None:
    driver = FakeDriver([_network_failure("TypeError: Failed to fetch")] * 4)
    with pytest.raises(HttpTaskError):
        _client(driver, max_retries=3).get("/get")


@pytest.mark.unit
def test_close_quits_the_driver() -> None:
    driver = FakeDriver([])
    client = _client(driver)
    client.close()
    assert driver.quit_called is True


@pytest.mark.unit
def test_context_manager_quits_the_driver() -> None:
    driver = FakeDriver([])
    with _client(driver) as client:
        assert client is not None
    assert driver.quit_called is True
