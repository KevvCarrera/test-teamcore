"""Reglas de generación de la bitácora sintética (FR-09, NFR-07).

Diseño y ejemplos en docs/specs/SPEC-002-generar-datos.md. Todas las
decisiones aleatorias (endpoint, status, latencia, parse_result, offset
temporal) se toman del mismo `numpy.random.Generator`, en el mismo orden, de
modo que la misma `seed` + el mismo `ref_utc` produzcan siempre la misma
secuencia de registros (determinismo, NFR-07).
"""

from collections.abc import Iterator
from datetime import datetime, timedelta

import numpy as np

from teamcore_http_kpi.domain.models import BitacoraRecord

CATALOG: tuple[str, ...] = (
    "/get",
    "/post",
    "/status/403",
    "/basic-auth",
    "/cookies",
    "/xml",
    "/html",
)

_WINDOW_DAYS = 3.0
_ELAPSED_MIN_MS = 50.0
_ELAPSED_MAX_MS = 800.0
_ELAPSED_DECIMALS = 1

_STATUS_OK = 200
_STATUS_SERVER_ERROR = 500
_STATUS_CLIENT_ERROR = 404
_P_STATUS_OK = 0.90
_P_STATUS_SERVER_ERROR = 0.06
# El resto de la probabilidad (1 - _P_STATUS_OK - _P_STATUS_SERVER_ERROR = 0.04)
# cae en _STATUS_CLIENT_ERROR, para enriquecer los KPIs con algo de 4xx además
# del 403 fijo de "/status/403".

_P_PARSE_ERROR = 0.05


def generate_records(n: int, *, seed: int, ref_utc: datetime) -> Iterator[BitacoraRecord]:
    """Genera `n` registros deterministas de la bitácora sintética.

    Args:
        n: número de registros a generar (debe ser mayor que 0).
        seed: semilla del generador `numpy.random.default_rng(seed)`.
        ref_utc: instante UTC de referencia ("ahora"); en producción es
            `datetime.now(UTC)`, en pruebas se inyecta un valor fijo.

    Yields:
        Registros con `timestamp_utc` dentro de las últimas 72 horas
        respecto a `ref_utc`, `endpoint` muestreado de `CATALOG`,
        `status_code` coherente con el endpoint, `elapsed_ms` en
        `[50, 800]` y `parse_result` "error" en ~5 % de los casos.

    Raises:
        ValueError: si `n` no es mayor que 0.
    """
    if n <= 0:
        raise ValueError("n debe ser mayor que 0")

    rng = np.random.default_rng(seed)
    endpoints = rng.choice(CATALOG, size=n)
    offset_days = rng.uniform(0.0, _WINDOW_DAYS, size=n)
    elapsed_ms = np.round(rng.uniform(_ELAPSED_MIN_MS, _ELAPSED_MAX_MS, size=n), _ELAPSED_DECIMALS)
    status_roll = rng.random(n)
    parse_roll = rng.random(n)

    for i in range(n):
        endpoint = str(endpoints[i])
        yield BitacoraRecord(
            timestamp_utc=ref_utc - timedelta(days=float(offset_days[i])),
            endpoint=endpoint,
            status_code=_status_code_for(endpoint, float(status_roll[i])),
            elapsed_ms=float(elapsed_ms[i]),
            parse_result="error" if parse_roll[i] < _P_PARSE_ERROR else "ok",
        )


def _status_code_for(endpoint: str, roll: float) -> int:
    """Determina `status_code` según el `endpoint` y un valor aleatorio `[0, 1)`."""
    if endpoint == "/status/403":
        return 403
    if roll < _P_STATUS_OK:
        return _STATUS_OK
    if roll < _P_STATUS_OK + _P_STATUS_SERVER_ERROR:
        return _STATUS_SERVER_ERROR
    return _STATUS_CLIENT_ERROR
