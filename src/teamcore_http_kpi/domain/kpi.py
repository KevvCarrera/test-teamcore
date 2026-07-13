"""Cálculo de los KPIs diarios por endpoint, incluido el percentil 90."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date

import numpy as np

from teamcore_http_kpi.domain.endpoints import normalize_endpoint
from teamcore_http_kpi.domain.models import BitacoraRecord, GlobalMetrics, KpiRow


def percentile_90(values: Sequence[float]) -> float:
    """Percentil 90 de un conjunto de latencias (`numpy.percentile`, sin redondear)."""
    if not values:
        raise ValueError("No se puede calcular el percentil 90 de una secuencia vacía")
    return float(np.percentile(values, 90))


def aggregate(records: Iterable[BitacoraRecord]) -> list[KpiRow]:
    """Agrupa registros por `(date_utc, endpoint_base)` y calcula sus KPIs.

    Las filas salen ordenadas para que la salida sea determinista.
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


def compute_global_metrics(rows: Sequence[KpiRow]) -> GlobalMetrics:
    """Calcula los números globales del reporte HTML.

    `pct_success`/`pct_errors` son fracciones [0, 1]. `p90_global` es un
    promedio de `p90_elapsed_ms` ponderado por `requests_total`, no un
    percentil recalculado desde cero.
    """
    if not rows:
        raise ValueError("No se pueden calcular métricas globales sin filas de KPI")

    total_requests = sum(row.requests_total for row in rows)
    total_success = sum(row.success_2xx for row in rows)
    total_errors = sum(row.client_4xx + row.server_5xx for row in rows)
    weighted_p90 = sum(row.p90_elapsed_ms * row.requests_total for row in rows)

    return GlobalMetrics(
        total_requests=total_requests,
        pct_success=total_success / total_requests,
        pct_errors=total_errors / total_requests,
        p90_global=round(weighted_p90 / total_requests, 2),
    )


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
