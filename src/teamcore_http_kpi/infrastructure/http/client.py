"""`RequestsHttpClient`: un cliente HTTP con sesión compartida y reintentos con
backoff exponencial. Si se agotan los reintentos ante un 403, lanza
`AccessForbiddenError`.
"""

import logging
import time
from collections.abc import Callable, Mapping

import requests

from teamcore_http_kpi.domain.errors import AccessForbiddenError, HttpTaskError

logger = logging.getLogger(__name__)

_RETRYABLE_SERVER_STATUS = {500, 502, 503, 504}


class RequestsHttpClient:
    """Cliente HTTP con sesión compartida y reintentos con backoff exponencial."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float,
        max_retries: int,
        backoff_factor: float,
        retry_on_403: bool = True,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        """`sleep` es inyectable para que las pruebas no esperen tiempo real entre reintentos."""
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._retry_on_403 = retry_on_403
        self._session = session if session is not None else requests.Session()
        self._sleep = sleep if sleep is not None else time.sleep

    def get(
        self, path: str, *, auth: tuple[str, str] | None = None, allow_redirects: bool = True
    ) -> requests.Response:
        """Realiza un `GET` a `path`, con reintentos según la política configurada."""
        return self._request_with_retries(
            "GET", path, auth=auth, allow_redirects=allow_redirects
        )

    def post(self, path: str, *, data: Mapping[str, str]) -> requests.Response:
        """Realiza un `POST` a `path` enviando `data` como formulario."""
        return self._request_with_retries("POST", path, data=data)

    def _request_with_retries(
        self,
        method: str,
        path: str,
        *,
        auth: tuple[str, str] | None = None,
        allow_redirects: bool = True,
        data: Mapping[str, str] | None = None,
    ) -> requests.Response:
        url = f"{self._base_url}{path}"
        last_response: requests.Response | None = None

        for attempt in range(self._max_retries + 1):
            is_last_attempt = attempt >= self._max_retries
            try:
                last_response = self._session.request(
                    method,
                    url,
                    auth=auth,
                    data=data,
                    timeout=self._timeout,
                    allow_redirects=allow_redirects,
                )
            except requests.RequestException as exc:
                if is_last_attempt:
                    raise HttpTaskError(f"Fallo de red en {method} {path}: {exc}") from exc
                logger.warning("Intento %d de %s %s falló: %s", attempt + 1, method, path, exc)
                self._sleep(self._backoff_factor * (2**attempt))
                continue

            if self._should_retry(last_response.status_code) and not is_last_attempt:
                logger.warning(
                    "Estado %d en %s %s (intento %d), reintentando",
                    last_response.status_code,
                    method,
                    path,
                    attempt + 1,
                )
                self._sleep(self._backoff_factor * (2**attempt))
                continue
            break

        assert last_response is not None  # el bucle ejecuta al menos un intento
        if last_response.status_code == 403 and self._retry_on_403:
            raise AccessForbiddenError(
                f"Acceso denegado (403) en {method} {path} tras agotar los reintentos"
            )
        if last_response.status_code in _RETRYABLE_SERVER_STATUS:
            raise HttpTaskError(
                f"Estado {last_response.status_code} persistente en {method} {path} "
                "tras agotar los reintentos"
            )
        return last_response

    def _should_retry(self, status_code: int) -> bool:
        if status_code == 403 and self._retry_on_403:
            return True
        return status_code in _RETRYABLE_SERVER_STATUS
