"""Pruebas de agregados de KPI y percentil 90 (FR-10).

Definiciones en docs/contracts/data-contracts.md#kpis.
"""

from datetime import UTC, datetime

import numpy as np
import pytest

from teamcore_http_kpi.domain.kpi import aggregate, percentile_90
from teamcore_http_kpi.domain.models import BitacoraRecord


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
