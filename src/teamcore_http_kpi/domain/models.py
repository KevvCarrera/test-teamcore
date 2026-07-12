"""Modelos de dominio: dataclasses inmutables tipadas.

Nota de interpretación: `project-structure.md` menciona `FormData` como parte
de este módulo, pero `HttpPort.post` (docs/architecture/component-model.md)
recibe `data: Mapping[str, str]`, no un objeto de dominio propio. Los datos de
formulario ya viven, tipados, en `config.FormData` (Fase 2, ADR-0005); no se
duplica aquí para no introducir un segundo modelo con el mismo propósito.
"""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class BitacoraRecord:
    """Un registro de la bitácora sintética de llamadas HTTP (FR-09).

    Espejo en memoria de una línea de `datos.jsonl`
    (docs/contracts/data-contracts.md#bitácora-datosjsonl). La serialización a
    JSON (incluido el formato `Z` de `timestamp_utc`) es responsabilidad de la
    capa `infrastructure/io`, no de este modelo.
    """

    timestamp_utc: datetime
    endpoint: str
    status_code: int
    elapsed_ms: float
    parse_result: str


@dataclass(frozen=True)
class KpiRow:
    """Una fila del CSV de KPIs, agregada por `(date_utc, endpoint_base)` (FR-10).

    Columnas y orden exactos según docs/contracts/data-contracts.md#kpi-csv.
    """

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
    """Métricas globales del reporte HTML (FR-13, docs/specs/SPEC-004-generar-reporte.md)."""

    total_requests: int
    pct_success: float
    pct_errors: float
    p90_global: float
