"""Los tres modelos de datos del dominio: fichas inmutables, sin lógica propia.

`FormData` vive en `config.py`, no aquí; `HttpPort.post` recibe un
`Mapping[str, str]` plano.
"""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class BitacoraRecord:
    """Una llamada HTTP simulada: la versión en memoria de una línea de `datos.jsonl`."""

    timestamp_utc: datetime
    endpoint: str
    status_code: int
    elapsed_ms: float
    parse_result: str


@dataclass(frozen=True)
class KpiRow:
    """Una fila del CSV de KPIs: un resumen por día y por tipo de endpoint."""

    date_utc: date
    endpoint_base: str
    requests_total: int
    success_2xx: int
    client_4xx: int
    server_5xx: int
    parse_errors: int
    avg_elapsed_ms: float
    p90_elapsed_ms: float


@dataclass(frozen=True)
class GlobalMetrics:
    """Los números que van arriba del todo en el reporte HTML."""

    total_requests: int
    pct_success: float
    pct_errors: float
    p90_global: float
