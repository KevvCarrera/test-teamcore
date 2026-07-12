"""Humo real de `SeleniumHttpClient`: un Chrome real (headless) contra `httpbin.org`.

Excluida por defecto (marcador `browser`, ver pyproject.toml), igual que las
pruebas `@network`. Ejecutar explícitamente con:

    pytest -m browser tests/browser

Requiere Chrome o Edge instalado; Selenium 4 resuelve el driver solo.
"""

import pytest

from teamcore_http_kpi.infrastructure.http.selenium_client import SeleniumHttpClient


@pytest.mark.browser
def test_get_against_real_httpbin() -> None:
    with SeleniumHttpClient(
        "https://httpbin.org", timeout=10.0, max_retries=2, backoff_factor=0.5
    ) as client:
        response = client.get("/get")
        assert response.status_code == 200
        assert "url" in response.json()


@pytest.mark.browser
def test_cookies_persist_across_calls_in_real_browser() -> None:
    with SeleniumHttpClient(
        "https://httpbin.org", timeout=10.0, max_retries=2, backoff_factor=0.5
    ) as client:
        client.get("/cookies/set?session=activa")
        response = client.get("/cookies")
        assert response.json()["cookies"]["session"] == "activa"
