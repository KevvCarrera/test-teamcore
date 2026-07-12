"""Cálculo de los KPIs diarios por endpoint, incluido el percentil 90."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date

import numpy as np

from teamcore_http_kpi.domain.endpoints import normalize_endpoint
from teamcore_http_kpi.domain.models import BitacoraRecord, GlobalMetrics, KpiRow


def percentile_90(values: Sequence[float]) -> float:
    """Percentil 90 de un conjunto de latencias, vía `numpy.percentile`.

    El p90 responde a la pregunta "¿cuánto tardó el 90 % de las llamadas, o
    menos?" — es una medida de la cola de latencia, y aguanta mucho mejor un
    par de valores atípicos que el promedio simple. Se delega el cálculo en
    `numpy` (interpolación lineal por defecto) en vez de reimplementar la
    fórmula a mano.

    El resultado se devuelve sin redondear; `aggregate` decide el redondeo a
    2 decimales al construir cada fila del CSV.
    """
    if not values:
        raise ValueError("No se puede calcular el percentil 90 de una secuencia vacía")
    return float(np.percentile(values, 90))


def aggregate(records: Iterable[BitacoraRecord]) -> list[KpiRow]:
    """Agrupa registros por día y endpoint, y calcula sus KPIs.

    Cada grupo es una combinación de `date_utc` (la fecha de `timestamp_utc`,
    sin la hora) y `endpoint_base` (vía `normalize_endpoint`). Por grupo se
    cuentan las respuestas por rango de estado, los errores de parseo, y se
    calcula el promedio y el percentil 90 de la latencia.

    Las filas salen ordenadas por `(date_utc, endpoint_base)`: así, correr
    esto dos veces con la misma entrada da siempre el mismo CSV, línea por
    línea.
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
    """Calcula los números globales que encabezan el reporte HTML.

    `pct_success` y `pct_errors` son fracciones entre 0 y 1 (quien los
    muestra decide multiplicarlos por 100). El caso curioso es `p90_global`:
    para cuando llegamos aquí, los datos ya están agregados por grupo, así
    que ya no tenemos las latencias individuales para sacar un percentil de
    verdad. Lo que se hace en su lugar es una media del `p90_elapsed_ms` de
    cada grupo, ponderada por su `requests_total` — una aproximación
    razonable, no un percentil recalculado desde cero.
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
