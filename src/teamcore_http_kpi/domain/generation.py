"""Generación de la bitácora sintética: datos "aleatorios" pero reproducibles.

Todas las decisiones al azar (qué endpoint, qué status, cuánto tardó, si
falló el parseo, cuándo ocurrió) salen del mismo generador de números
aleatorios, siempre en el mismo orden. Por eso la misma `seed` junto con el
mismo `ref_utc` produce siempre exactamente la misma secuencia de registros.
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
    """Genera `n` registros de bitácora, deterministas dada la `seed` y `ref_utc`.

    `ref_utc` es el "ahora" desde el que se cuentan las últimas 72 horas; en
    producción es simplemente `datetime.now(UTC)`, y en pruebas se pasa un
    valor fijo para que el resultado sea comparable. Cada registro sale con
    un endpoint del catálogo, un status coherente con ese endpoint, una
    latencia entre 50 y 800 ms, y un ~5 % de probabilidad de marcar error de
    parseo.
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
