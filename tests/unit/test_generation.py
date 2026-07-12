"""Pruebas de generación de la bitácora sintética (FR-09, NFR-07).

Criterios de aceptación en docs/specs/SPEC-002-generar-datos.md.
"""

from datetime import UTC, datetime, timedelta

import pytest

from teamcore_http_kpi.domain.generation import CATALOG, generate_records


@pytest.mark.unit
def test_generate_records_count(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(500, seed=seed, ref_utc=frozen_ref_utc))
    assert len(records) == 500


@pytest.mark.unit
def test_determinism_same_seed_same_ref_utc(frozen_ref_utc: datetime, seed: int) -> None:
    first = list(generate_records(50, seed=seed, ref_utc=frozen_ref_utc))
    second = list(generate_records(50, seed=seed, ref_utc=frozen_ref_utc))
    assert first == second


@pytest.mark.unit
def test_different_seed_produces_different_sequence(frozen_ref_utc: datetime, seed: int) -> None:
    first = list(generate_records(50, seed=seed, ref_utc=frozen_ref_utc))
    second = list(generate_records(50, seed=seed + 1, ref_utc=frozen_ref_utc))
    assert first != second


@pytest.mark.unit
def test_status_403_always_for_status_endpoint(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(500, seed=seed, ref_utc=frozen_ref_utc))
    for record in records:
        if record.endpoint == "/status/403":
            assert record.status_code == 403


@pytest.mark.unit
def test_timestamps_within_last_3_days(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(500, seed=seed, ref_utc=frozen_ref_utc))
    window_start = frozen_ref_utc - timedelta(days=3)
    for record in records:
        assert window_start <= record.timestamp_utc <= frozen_ref_utc


@pytest.mark.unit
def test_elapsed_ms_within_bounds(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(500, seed=seed, ref_utc=frozen_ref_utc))
    for record in records:
        assert 50.0 <= record.elapsed_ms <= 800.0


@pytest.mark.unit
def test_parse_result_only_ok_or_error(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(500, seed=seed, ref_utc=frozen_ref_utc))
    assert {r.parse_result for r in records} <= {"ok", "error"}


@pytest.mark.unit
def test_parse_error_proportion_near_5_percent(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(2000, seed=seed, ref_utc=frozen_ref_utc))
    error_ratio = sum(1 for r in records if r.parse_result == "error") / len(records)
    assert 0.02 <= error_ratio <= 0.08


@pytest.mark.unit
def test_endpoint_values_within_catalog(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(500, seed=seed, ref_utc=frozen_ref_utc))
    assert {r.endpoint for r in records} <= set(CATALOG)


@pytest.mark.unit
def test_timestamps_are_utc_aware(frozen_ref_utc: datetime, seed: int) -> None:
    records = list(generate_records(10, seed=seed, ref_utc=frozen_ref_utc))
    assert all(record.timestamp_utc.tzinfo == UTC for record in records)


@pytest.mark.unit
def test_rejects_non_positive_count(frozen_ref_utc: datetime, seed: int) -> None:
    with pytest.raises(ValueError):
        list(generate_records(0, seed=seed, ref_utc=frozen_ref_utc))
