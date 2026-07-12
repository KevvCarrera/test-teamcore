"""Pruebas e2e de `calcular_kpi.py` (FR-10, FR-11) con golden input/output.

Golden files en tests/data/: `bitacora_min.jsonl` (entrada) y
`kpi_expected.csv` (salida esperada), generados con `seed=42` y un
`ref_utc` fijo.
"""

from pathlib import Path

import pytest

from teamcore_http_kpi.cli._common import EXIT_DATA_ERROR, EXIT_OK
from teamcore_http_kpi.cli.calcular_kpi import main

_GOLDEN_DIR = Path(__file__).resolve().parents[1] / "data"
_GOLDEN_INPUT = _GOLDEN_DIR / "bitacora_min.jsonl"
_GOLDEN_OUTPUT = _GOLDEN_DIR / "kpi_expected.csv"


@pytest.mark.e2e
def test_golden_input_produces_golden_output(tmp_out: Path) -> None:
    destination = tmp_out / "kpi.csv"
    exit_code = main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])

    assert exit_code == EXIT_OK
    assert destination.read_text(encoding="utf-8") == _GOLDEN_OUTPUT.read_text(encoding="utf-8")


@pytest.mark.e2e
def test_rerun_is_idempotent(tmp_out: Path) -> None:
    destination = tmp_out / "kpi.csv"
    main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])
    first_run = destination.read_text(encoding="utf-8")

    main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])
    second_run = destination.read_text(encoding="utf-8")

    assert first_run == second_run


@pytest.mark.e2e
def test_missing_input_file_is_a_data_error(tmp_out: Path) -> None:
    destination = tmp_out / "kpi.csv"
    exit_code = main(["--input", str(tmp_out / "no-existe.jsonl"), "--output", str(destination)])

    assert exit_code == EXIT_DATA_ERROR
    assert not destination.exists()


@pytest.mark.e2e
def test_only_corrupt_lines_is_a_data_error(tmp_out: Path) -> None:
    input_path = tmp_out / "solo-corrupto.jsonl"
    input_path.write_text("esto no es json\n{}\n", encoding="utf-8")
    destination = tmp_out / "kpi.csv"

    exit_code = main(["--input", str(input_path), "--output", str(destination)])

    assert exit_code == EXIT_DATA_ERROR
    assert not destination.exists()


@pytest.mark.e2e
def test_mixed_valid_and_corrupt_lines_keeps_the_valid_ones(tmp_out: Path) -> None:
    good_line = (
        '{"timestamp_utc": "2026-07-09T10:15:23Z", "endpoint": "/get", '
        '"status_code": 200, "elapsed_ms": 120.5, "parse_result": "ok"}'
    )
    input_path = tmp_out / "mixto.jsonl"
    input_path.write_text(f"{good_line}\nesto no es json\n", encoding="utf-8")
    destination = tmp_out / "kpi.csv"

    exit_code = main(["--input", str(input_path), "--output", str(destination)])

    assert exit_code == EXIT_OK
    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # encabezado + 1 fila
