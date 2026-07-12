"""Pruebas de integración de `JsonlBitacoraRepository` (FR-09, FR-11).

E/S real sobre `tmp_path` (sin red), según docs/testing/test-strategy.md.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest

from teamcore_http_kpi.domain.errors import InputFileNotFoundError
from teamcore_http_kpi.domain.models import BitacoraRecord
from teamcore_http_kpi.infrastructure.io.jsonl_repository import JsonlBitacoraRepository


def _record(endpoint: str = "/get") -> BitacoraRecord:
    return BitacoraRecord(
        timestamp_utc=datetime(2026, 7, 9, 10, 15, 23, tzinfo=UTC),
        endpoint=endpoint,
        status_code=200,
        elapsed_ms=120.5,
        parse_result="ok",
    )


@pytest.mark.integration
def test_write_creates_parent_dir_and_returns_count(tmp_out: Path) -> None:
    destination = tmp_out / "nested" / "datos.jsonl"
    repo = JsonlBitacoraRepository()

    count = repo.write([_record(), _record("/post")], destination)

    assert count == 2
    assert destination.exists()


@pytest.mark.integration
def test_write_then_read_round_trips(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    repo = JsonlBitacoraRepository()
    original = [_record("/get"), _record("/status/403")]

    repo.write(original, destination)
    read_back = list(repo.read(destination))

    assert read_back == original


@pytest.mark.integration
def test_write_format_matches_contract(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    repo = JsonlBitacoraRepository()
    repo.write([_record()], destination)

    line = destination.read_text(encoding="utf-8").splitlines()[0]
    assert line == (
        '{"timestamp_utc": "2026-07-09T10:15:23Z", "endpoint": "/get", '
        '"status_code": 200, "elapsed_ms": 120.5, "parse_result": "ok"}'
    )


@pytest.mark.integration
def test_write_truncates_existing_file(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    repo = JsonlBitacoraRepository()

    repo.write([_record(), _record(), _record()], destination)
    repo.write([_record()], destination)

    assert len(destination.read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.integration
def test_read_raises_when_file_missing(tmp_out: Path) -> None:
    repo = JsonlBitacoraRepository()
    with pytest.raises(InputFileNotFoundError):
        list(repo.read(tmp_out / "no-existe.jsonl"))


@pytest.mark.integration
def test_read_skips_malformed_line_with_warning(
    tmp_out: Path, caplog: pytest.LogCaptureFixture
) -> None:
    destination = tmp_out / "datos.jsonl"
    good_line = (
        '{"timestamp_utc": "2026-07-09T10:15:23Z", "endpoint": "/get", '
        '"status_code": 200, "elapsed_ms": 120.5, "parse_result": "ok"}'
    )
    destination.write_text(f"{good_line}\nesto no es json\n{good_line}\n", encoding="utf-8")

    repo = JsonlBitacoraRepository()
    with caplog.at_level(logging.WARNING):
        records = list(repo.read(destination))

    assert len(records) == 2
    assert any("Línea 2" in message for message in caplog.messages)


@pytest.mark.integration
def test_read_skips_line_with_missing_field(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    destination.write_text('{"endpoint": "/get"}\n', encoding="utf-8")

    repo = JsonlBitacoraRepository()
    assert list(repo.read(destination)) == []


@pytest.mark.integration
def test_read_skips_line_that_is_not_a_json_object(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    destination.write_text("[1, 2, 3]\n", encoding="utf-8")

    repo = JsonlBitacoraRepository()
    assert list(repo.read(destination)) == []


@pytest.mark.integration
def test_read_skips_line_with_non_string_timestamp(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    destination.write_text(
        '{"timestamp_utc": 123, "endpoint": "/get", "status_code": 200, '
        '"elapsed_ms": 120.5, "parse_result": "ok"}\n',
        encoding="utf-8",
    )

    repo = JsonlBitacoraRepository()
    assert list(repo.read(destination)) == []


@pytest.mark.integration
def test_read_ignores_blank_lines(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    good_line = (
        '{"timestamp_utc": "2026-07-09T10:15:23Z", "endpoint": "/get", '
        '"status_code": 200, "elapsed_ms": 120.5, "parse_result": "ok"}'
    )
    destination.write_text(f"{good_line}\n\n\n", encoding="utf-8")

    repo = JsonlBitacoraRepository()
    assert len(list(repo.read(destination))) == 1
