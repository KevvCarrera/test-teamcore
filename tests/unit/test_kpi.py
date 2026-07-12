"""Pruebas de agregados de KPI y percentil 90 (FR-10).

Definiciones en docs/contracts/data-contracts.md#kpis.
"""

from datetime import UTC, date, datetime

import numpy as np
import pytest

from teamcore_http_kpi.domain.kpi import aggregate, compute_global_metrics, percentile_90
from teamcore_http_kpi.domain.models import BitacoraRecord, KpiRow


@pytest.mark.unit
def test_percentile_90_matches_numpy() -> None:
    values = [50.0, 120.5, 300.25, 799.9, 640.0]
    assert percentile_90(values) == pytest.approx(float(np.percentile(values, 90)))


@pytest.mark.unit
def test_percentile_90_rejects_empty_sequence() -> None:
    with pytest.raises(ValueError):
        percentile_90([])


def _record(
    endpoint: str, status: int, elapsed: float, parse: str = "ok", day: int = 9
) -> BitacoraRecord:
    return BitacoraRecord(
        timestamp_utc=datetime(2026, 7, day, 10, 0, tzinfo=UTC),
        endpoint=endpoint,
        status_code=status,
        elapsed_ms=elapsed,
        parse_result=parse,
    )


@pytest.mark.unit
def test_aggregate_counts_by_status_range() -> None:
    records = [
        _record("/get", 200, 100.0),
        _record("/get", 404, 200.0),
        _record("/get", 500, 300.0),
        _record("/status/403", 403, 150.0, parse="error"),
    ]
    rows = aggregate(records)
    by_endpoint = {row.endpoint_base: row for row in rows}

    get_row = by_endpoint["/get"]
    assert get_row.requests_total == 3
    assert get_row.success_2xx == 1
    assert get_row.client_4xx == 1
    assert get_row.server_5xx == 1
    assert get_row.parse_errors == 0

    status_row = by_endpoint["/status"]
    assert status_row.requests_total == 1
    assert status_row.parse_errors == 1


@pytest.mark.unit
def test_aggregate_groups_by_normalized_endpoint() -> None:
    records = [_record("/status/403", 403, 100.0), _record("/status/500", 500, 200.0)]
    rows = aggregate(records)
    assert len(rows) == 1
    assert rows[0].endpoint_base == "/status"
    assert rows[0].requests_total == 2


@pytest.mark.unit
def test_aggregate_p90_matches_numpy_percentile() -> None:
    elapsed = [50.0, 120.0, 300.0, 640.0, 799.0]
    records = [_record("/get", 200, e) for e in elapsed]
    rows = aggregate(records)
    expected = round(float(np.percentile(elapsed, 90)), 2)
    assert rows[0].p90_elapsed_ms == pytest.approx(expected)


@pytest.mark.unit
def test_aggregate_avg_elapsed_rounded_to_2_decimals() -> None:
    records = [_record("/get", 200, 100.0), _record("/get", 200, 100.005)]
    rows = aggregate(records)
    assert rows[0].avg_elapsed_ms == round((100.0 + 100.005) / 2, 2)


@pytest.mark.unit
def test_aggregate_sorted_by_date_then_endpoint() -> None:
    records = [
        _record("/xml", 200, 100.0, day=10),
        _record("/get", 200, 100.0, day=9),
        _record("/html", 200, 100.0, day=9),
    ]
    rows = aggregate(records)
    keys = [(row.date_utc, row.endpoint_base) for row in rows]
    assert keys == sorted(keys)


@pytest.mark.unit
def test_aggregate_empty_input_returns_empty_list() -> None:
    assert aggregate([]) == []


def _kpi_row(
    endpoint_base: str,
    requests_total: int,
    success_2xx: int,
    client_4xx: int,
    server_5xx: int,
    avg_elapsed_ms: float,
    p90_elapsed_ms: float,
) -> KpiRow:
    return KpiRow(
        date_utc=date(2026, 7, 9),
        endpoint_base=endpoint_base,
        requests_total=requests_total,
        success_2xx=success_2xx,
        client_4xx=client_4xx,
        server_5xx=server_5xx,
        parse_errors=0,
        avg_elapsed_ms=avg_elapsed_ms,
        p90_elapsed_ms=p90_elapsed_ms,
    )


@pytest.mark.unit
def test_compute_global_metrics_totals_and_percentages() -> None:
    rows = [
        _kpi_row("/get", 8, 6, 2, 0, 100.0, 200.0),
        _kpi_row("/status", 2, 0, 0, 2, 150.0, 300.0),
    ]
    metrics = compute_global_metrics(rows)
    assert metrics.total_requests == 10
    assert metrics.pct_success == pytest.approx(6 / 10)
    assert metrics.pct_errors == pytest.approx(4 / 10)


@pytest.mark.unit
def test_compute_global_metrics_p90_is_weighted_average() -> None:
    rows = [
        _kpi_row("/get", 8, 8, 0, 0, 100.0, 200.0),
        _kpi_row("/status", 2, 2, 0, 0, 150.0, 300.0),
    ]
    metrics = compute_global_metrics(rows)
    expected = round((200.0 * 8 + 300.0 * 2) / 10, 2)
    assert metrics.p90_global == pytest.approx(expected)


@pytest.mark.unit
def test_compute_global_metrics_rejects_empty_rows() -> None:
    with pytest.raises(ValueError):
        compute_global_metrics([])
