"""`SeleniumHttpClient`: adaptador alternativo de `HttpPort` sobre un navegador real.

Ver docs/adr/0014-selenium-adapter-as-alternative.md. No es el cliente por
defecto (`cliente_http.py` usa `RequestsHttpClient`). Cada llamada ejecuta un
`fetch()` dentro del navegador (vía `execute_async_script`) en vez de navegar
directamente, para no dejar que Chrome/Edge re-renderice el JSON/XML.
"""

import base64
import json
import logging
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol
from urllib.parse import urlencode

from teamcore_http_kpi.domain.errors import AccessForbiddenError, HttpTaskError

logger = logging.getLogger(__name__)

_RETRYABLE_SERVER_STATUS = {500, 502, 503, 504}

_FETCH_SCRIPT = """
const [url, method, headers, body, callback] = arguments;
const opts = {method: method, credentials: "include", headers: headers, redirect: "follow"};
if (body !== null) { opts.body = body; }
fetch(url, opts)
    .then(async (resp) => {
        const text = await resp.text();
        callback({status: resp.status, text: text, redirected: resp.redirected, ok: true});
    })
    .catch((err) => callback({status: 0, text: String(err), redirected: false, ok: false}));
"""


class SeleniumDriver(Protocol):
    """Lo mínimo que este adaptador necesita de un `selenium.webdriver.*` real."""

    def get(self, url: str) -> None: ...

    def execute_async_script(self, script: str, *args: object) -> Any: ...

    def quit(self) -> None: ...


class _SeleniumResponse:
    """Respuesta obtenida vía `fetch()` dentro de un navegador real.

    `headers` siempre vacío, `history` a lo sumo una entrada sintética
    (limitaciones de `fetch()` desde el navegador, ver ADR-0014).
    """

    def __init__(self, status_code: int, text: str, *, redirected: bool = False) -> None:
        self.status_code = status_code
        self._text = text
        self._history: list[_SeleniumResponse] = [_SeleniumResponse(302, "")] if redirected else []

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._text.encode("utf-8")

    def json(self) -> Any:
        return json.loads(self._text)

    @property
    def headers(self) -> Mapping[str, str]:
        return {}

    @property
    def history(self) -> Sequence["_SeleniumResponse"]:
        return self._history


class SeleniumHttpClient:
    """Cliente HTTP alternativo: un navegador real controlado por Selenium,
    implementando el mismo `HttpPort` que `RequestsHttpClient`.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float,
        max_retries: int,
        backoff_factor: float,
        retry_on_403: bool = True,
        driver: SeleniumDriver | None = None,
        sleep: Callable[[float], None] | None = None,
        headless: bool = True,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._retry_on_403 = retry_on_403
        self._sleep = sleep if sleep is not None else time.sleep
        self._driver = driver if driver is not None else _build_chrome_driver(headless, timeout)
        # Se navega una vez a la URL base: así los fetch() posteriores son del
        # mismo origen y comparten la bandeja de cookies real del navegador.
        self._driver.get(f"{self._base_url}/")

    def get(
        self, path: str, *, auth: tuple[str, str] | None = None, allow_redirects: bool = True
    ) -> _SeleniumResponse:
        """`allow_redirects=False` no tiene soporte completo: ver ADR-0014."""
        headers = _basic_auth_header(auth) if auth else {}
        return self._fetch_with_retries("GET", path, headers=headers)

    def post(self, path: str, *, data: Mapping[str, str]) -> _SeleniumResponse:
        body = urlencode(data)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return self._fetch_with_retries("POST", path, headers=headers, body=body)

    def close(self) -> None:
        """Cierra el navegador. Sin esto, el proceso del navegador queda abierto."""
        self._driver.quit()

    def __enter__(self) -> "SeleniumHttpClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _fetch_with_retries(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str],
        body: str | None = None,
    ) -> _SeleniumResponse:
        url = f"{self._base_url}{path}"
        last_result: dict[str, Any] | None = None

        for attempt in range(self._max_retries + 1):
            is_last_attempt = attempt >= self._max_retries
            last_result = self._driver.execute_async_script(
                _FETCH_SCRIPT, url, method, dict(headers), body
            )

            if not last_result["ok"]:
                if is_last_attempt:
                    raise HttpTaskError(f"Fallo de red en {method} {path}: {last_result['text']}")
                logger.warning(
                    "Intento %d de %s %s falló: %s",
                    attempt + 1,
                    method,
                    path,
                    last_result["text"],
                )
                self._sleep(self._backoff_factor * (2**attempt))
                continue

            status = last_result["status"]
            if self._should_retry(status) and not is_last_attempt:
                logger.warning(
                    "Estado %d en %s %s (intento %d), reintentando",
                    status,
                    method,
                    path,
                    attempt + 1,
                )
                self._sleep(self._backoff_factor * (2**attempt))
                continue
            break

        assert last_result is not None  # el bucle ejecuta al menos un intento
        status = last_result["status"]
        if status == 403 and self._retry_on_403:
            raise AccessForbiddenError(
                f"Acceso denegado (403) en {method} {path} tras agotar los reintentos"
            )
        if status in _RETRYABLE_SERVER_STATUS:
            raise HttpTaskError(
                f"Estado {status} persistente en {method} {path} tras agotar los reintentos"
            )
        return _SeleniumResponse(status, last_result["text"], redirected=last_result["redirected"])

    def _should_retry(self, status_code: int) -> bool:
        if status_code == 403 and self._retry_on_403:
            return True
        return status_code in _RETRYABLE_SERVER_STATUS


def _basic_auth_header(auth: tuple[str, str]) -> dict[str, str]:
    user, password = auth
    token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def _build_chrome_driver(headless: bool, timeout: float) -> SeleniumDriver:
    """Construye un Chrome real. Selenium 4 resuelve el driver solo (Selenium Manager)."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.set_script_timeout(timeout)
    return driver
