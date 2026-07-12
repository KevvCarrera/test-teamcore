"""Pruebas de integración de `RequestsHttpClient` (FR-01…FR-08), sin red real.

Usa `responses` para simular `httpbin.org` (docs/testing/test-strategy.md).
El parámetro `sleep` se inyecta como no-op para no esperar tiempo real durante
los reintentos.
"""

import pytest
import requests
import responses

from teamcore_http_kpi.domain.errors import AccessForbiddenError, HttpTaskError
from teamcore_http_kpi.infrastructure.http.client import RequestsHttpClient

_BASE_URL = "https://httpbin.org"


def _client(*, max_retries: int = 3, retry_on_403: bool = True) -> RequestsHttpClient:
    return RequestsHttpClient(
        _BASE_URL,
        timeout=5.0,
        max_retries=max_retries,
        backoff_factor=0.01,
        retry_on_403=retry_on_403,
        sleep=lambda _seconds: None,
    )


@pytest.mark.integration
@responses.activate
def test_get_returns_response_on_first_success() -> None:
    responses.add(
        responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200
    )
    response = _client().get("/get")
    assert response.status_code == 200
    assert response.json() == {"args": {}}


@pytest.mark.integration
@responses.activate
def test_get_sends_basic_auth() -> None:
    responses.add(
        responses.GET,
        f"{_BASE_URL}/basic-auth/usuario_test/clave123",
        json={"authenticated": True, "user": "usuario_test"},
        status=200,
    )
    response = _client().get(
        "/basic-auth/usuario_test/clave123", auth=("usuario_test", "clave123")
    )
    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    sent_auth_header = responses.calls[0].request.headers["Authorization"]
    assert sent_auth_header.startswith("Basic ")


@pytest.mark.integration
@responses.activate
def test_post_sends_form_data() -> None:
    responses.add(responses.POST, f"{_BASE_URL}/post", json={"form": {}}, status=200)
    form = {"nombre": "Juan", "apellido": "Pérez"}

    _client().post("/post", data=form)

    sent_body = responses.calls[0].request.body
    assert sent_body is not None
    if isinstance(sent_body, bytes):
        sent_body = sent_body.decode("utf-8")
    assert "nombre=Juan" in sent_body
    assert "apellido=P" in sent_body  # Pérez va url-encoded


@pytest.mark.integration
@responses.activate
def test_session_cookies_persist_across_calls() -> None:
    responses.add(
        responses.GET,
        f"{_BASE_URL}/cookies/set",
        status=200,
        headers={"Set-Cookie": "session=activa"},
    )
    responses.add(
        responses.GET, f"{_BASE_URL}/cookies", json={"cookies": {"session": "activa"}}, status=200
    )

    client = _client()
    client.get("/cookies/set")
    response = client.get("/cookies")

    assert response.json() == {"cookies": {"session": "activa"}}
    assert responses.calls[1].request.headers.get("Cookie") == "session=activa"


@pytest.mark.integration
@responses.activate
def test_403_retries_then_raises_access_forbidden_after_exhausting_retries() -> None:
    for _ in range(4):  # 1 intento inicial + 3 reintentos
        responses.add(responses.GET, f"{_BASE_URL}/status/403", status=403)

    with pytest.raises(AccessForbiddenError):
        _client(max_retries=3).get("/status/403")

    assert len(responses.calls) == 4


@pytest.mark.integration
@responses.activate
def test_403_retries_then_succeeds() -> None:
    responses.add(responses.GET, f"{_BASE_URL}/status/403", status=403)
    responses.add(responses.GET, f"{_BASE_URL}/status/403", status=200, json={"ok": True})

    response = _client(max_retries=3).get("/status/403")

    assert response.status_code == 200
    assert len(responses.calls) == 2


@pytest.mark.integration
@responses.activate
def test_403_not_retried_when_disabled() -> None:
    """Con `retry_on_403=False`, el cliente no reintenta ni lanza excepción:
    devuelve la respuesta 403 cruda para que la capa de aplicación decida.
    """
    responses.add(responses.GET, f"{_BASE_URL}/status/403", status=403)

    response = _client(max_retries=3, retry_on_403=False).get("/status/403")

    assert response.status_code == 403
    assert len(responses.calls) == 1


@pytest.mark.integration
@responses.activate
def test_server_error_is_retried_then_succeeds() -> None:
    responses.add(responses.GET, f"{_BASE_URL}/get", status=500)
    responses.add(responses.GET, f"{_BASE_URL}/get", status=200, json={"args": {}})

    response = _client().get("/get")

    assert response.status_code == 200
    assert len(responses.calls) == 2


@pytest.mark.integration
@responses.activate
def test_persistent_server_error_raises_http_task_error_after_retries() -> None:
    """Encontrado al probar contra httpbin.org real: un 503 persistente no debe
    devolverse como si nada tras agotar los reintentos; debe avisar con
    HttpTaskError para que la capa de aplicación lo marque como fallido.
    """
    for _ in range(4):  # 1 intento + 3 reintentos
        responses.add(responses.GET, f"{_BASE_URL}/get", status=503)

    with pytest.raises(HttpTaskError):
        _client(max_retries=3).get("/get")

    assert len(responses.calls) == 4


@pytest.mark.integration
@responses.activate
def test_connection_error_retried_then_raises_http_task_error() -> None:
    for _ in range(4):
        responses.add(
            responses.GET,
            f"{_BASE_URL}/get",
            body=requests.exceptions.ConnectionError("boom"),
        )

    with pytest.raises(HttpTaskError):
        _client(max_retries=3).get("/get")

    assert len(responses.calls) == 4


@pytest.mark.integration
@responses.activate
def test_redirect_is_followed_and_history_not_empty() -> None:
    responses.add(
        responses.GET,
        f"{_BASE_URL}/redirect-to",
        status=302,
        headers={"Location": f"{_BASE_URL}/get"},
    )
    responses.add(responses.GET, f"{_BASE_URL}/get", json={"args": {}}, status=200)

    response = _client().get("/redirect-to?url=/get")

    assert response.status_code == 200
    assert len(response.history) == 1
