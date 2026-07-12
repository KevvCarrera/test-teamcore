"""Pruebas de integración de `CsvKpiRepository` (FR-10, FR-13).

E/S real sobre `tmp_path` (sin red), según docs/testing/test-strategy.md.
"""

from datetime import date
from pathlib import Path

import pytest

from teamcore_http_kpi.domain.errors import InputFileNotFoundError
from teamcore_http_kpi.domain.models import KpiRow
from teamcore_http_kpi.infrastructure.io.csv_repository import CsvKpiRepository


def _row(endpoint_base: str = "/get") -> KpiRow:
    return KpiRow(
        date_utc=date(2026, 7, 9),
        endpoint_base=endpoint_base,
        requests_total=42,
        success_2xx=40,
        client_4xx=0,
        server_5xx=2,
        parse_errors=3,
        avg_elapsed_ms=418.77,
        p90_elapsed_ms=742.10,
    )


@pytest.mark.integration
def test_write_creates_parent_dir_with_header_and_rows(tmp_out: Path) -> None:
    destination = tmp_out / "nested" / "kpi.csv"
    CsvKpiRepository().write([_row()], destination)

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert lines[0] == (
        "date_utc,endpoint_base,requests_total,success_2xx,client_4xx,"
        "server_5xx,parse_errors,avg_elapsed_ms,p90_elapsed_ms"
    )
    assert lines[1] == "2026-07-09,/get,42,40,0,2,3,418.77,742.1"


@pytest.mark.integration
def test_write_then_read_round_trips(tmp_out: Path) -> None:
    destination = tmp_out / "kpi.csv"
    repo = CsvKpiRepository()
    original = [_row("/get"), _row("/status")]

    repo.write(original, destination)
    read_back = repo.read(destination)

    assert read_back == original


@pytest.mark.integration
def test_write_truncates_existing_file(tmp_out: Path) -> None:
    destination = tmp_out / "kpi.csv"
    repo = CsvKpiRepository()

    repo.write([_row(), _row("/post"), _row("/xml")], destination)
    repo.write([_row()], destination)

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # encabezado + 1 fila


@pytest.mark.integration
def test_read_raises_when_file_missing(tmp_out: Path) -> None:
    with pytest.raises(InputFileNotFoundError):
        CsvKpiRepository().read(tmp_out / "no-existe.csv")
