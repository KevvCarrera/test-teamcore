"""Agregados de KPI y percentil 90 (FR-10, NFR-05).

Definiciones exactas en docs/contracts/data-contracts.md#kpis.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date

import numpy as np

from teamcore_http_kpi.domain.endpoints import normalize_endpoint
from teamcore_http_kpi.domain.models import BitacoraRecord, KpiRow


def percentile_90(values: Sequence[float]) -> float:
    """Percentil 90 de `values` vía `numpy.percentile(values, 90)`.

    `numpy.percentile` calcula el percentil q-ésimo de un conjunto de datos;
    por defecto usa interpolación lineal entre los dos puntos más cercanos
    cuando el percentil no cae exactamente sobre una observación. El p90
    significa que el 90 % de las observaciones son menores o iguales a este
    valor: es un indicador de la "cola" de latencia, más robusto frente a
    valores atípicos aislados que el promedio simple.

    Args:
        values: latencias (`elapsed_ms`) de un grupo.

    Returns:
        El percentil 90, sin redondear (el redondeo a 2 decimales del
        contrato lo aplica `aggregate` al construir la fila del CSV).

    Raises:
        ValueError: si `values` está vacío (no se puede definir un percentil).
    """
    if not values:
        raise ValueError("No se puede calcular el percentil 90 de una secuencia vacía")
    return float(np.percentile(values, 90))


def aggregate(records: Iterable[BitacoraRecord]) -> list[KpiRow]:
    """Agrupa `records` por `(date_utc, endpoint_base)` y calcula sus KPIs.

    `date_utc` es la fecha (sin hora) de `timestamp_utc`; `endpoint_base` se
    obtiene con `normalize_endpoint`. Por cada grupo se calculan los conteos
    por rango de `status_code`, los `parse_errors`, la media de `elapsed_ms`
    (`avg_elapsed_ms`) y el percentil 90 (`p90_elapsed_ms`), ambos redondeados
    a 2 decimales según el contrato.

    Returns:
        Las filas resultantes, ordenadas ascendentemente por
        `(date_utc, endpoint_base)` para una salida determinista
        (docs/contracts/data-contracts.md#kpi-csv).
    """
    groups: dict[tuple[date, str], list[BitacoraRecord]] = defaultdict(list)
    for record in records:
        key = (record.timestamp_utc.date(), normalize_endpoint(record.endpoint))
        groups[key].append(record)

    rows = [
        _aggregate_group(date_utc, endpoint_base, group)
        for (date_utc, endpoint_base), group in groups.items()
    ]
    rows.sort(key=lambda row: (row.date_utc, row.endpoint_base))
    return rows


def _aggregate_group(
    date_utc: date, endpoint_base: str, group: Sequence[BitacoraRecord]
) -> KpiRow:
    """Calcula los KPIs de un único grupo `(date_utc, endpoint_base)`."""
    requests_total = len(group)
    success_2xx = sum(1 for r in group if 200 <= r.status_code <= 299)
    client_4xx = sum(1 for r in group if 400 <= r.status_code <= 499)
    server_5xx = sum(1 for r in group if 500 <= r.status_code <= 599)
    parse_errors = sum(1 for r in group if r.parse_result != "ok")
    elapsed = [r.elapsed_ms for r in group]
    avg_elapsed_ms = round(sum(elapsed) / len(elapsed), 2)
    p90_elapsed_ms = round(percentile_90(elapsed), 2)
    return KpiRow(
        date_utc=date_utc,
        endpoint_base=endpoint_base,
        requests_total=requests_total,
        success_2xx=success_2xx,
        client_4xx=client_4xx,
        server_5xx=server_5xx,
        parse_errors=parse_errors,
        avg_elapsed_ms=avg_elapsed_ms,
        p90_elapsed_ms=p90_elapsed_ms,
    )
