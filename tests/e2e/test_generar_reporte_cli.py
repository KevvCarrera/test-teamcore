"""Pruebas e2e de `generar_reporte.py` (FR-13).

Valida secciones del reporte, alerta por umbral y que el HTML es
autocontenido, sobre un CSV de KPIs real (golden file y uno hecho a medida
para controlar el umbral).
"""

from pathlib import Path

import pytest

from teamcore_http_kpi.cli._common import EXIT_DATA_ERROR, EXIT_OK
from teamcore_http_kpi.cli.generar_reporte import main

_GOLDEN_INPUT = Path(__file__).resolve().parents[1] / "data" / "kpi_expected.csv"

_CSV_HEADER = (
    "date_utc,endpoint_base,requests_total,success_2xx,client_4xx,"
    "server_5xx,parse_errors,avg_elapsed_ms,p90_elapsed_ms\n"
)


def _write_csv(destination: Path, rows: list[str]) -> None:
    destination.write_text(_CSV_HEADER + "\n".join(rows) + "\n", encoding="utf-8")


@pytest.mark.e2e
def test_golden_csv_produces_report_with_expected_sections(tmp_out: Path) -> None:
    destination = tmp_out / "report" / "kpi_diario.html"
    exit_code = main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])

    assert exit_code == EXIT_OK
    html = destination.read_text(encoding="utf-8")
    assert "Total de solicitudes" in html
    assert "% de éxito" in html
    assert "% de errores" in html
    assert "p90 global" in html
    assert "KPIs por endpoint" in html


@pytest.mark.e2e
def test_report_is_self_contained(tmp_out: Path) -> None:
    destination = tmp_out / "kpi_diario.html"
    main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])

    html = destination.read_text(encoding="utf-8")
    assert "data:image/png;base64," in html
    assert 'src="out/' not in html
    assert 'src="./' not in html


@pytest.mark.e2e
def test_alert_marks_rows_above_threshold_and_not_below(tmp_out: Path) -> None:
    csv_path = tmp_out / "kpi.csv"
    _write_csv(
        csv_path,
        [
            "2026-07-09,/lento,10,10,0,0,0,100.0,742.10",
            "2026-07-09,/rapido,10,10,0,0,0,100.0,120.00",
        ],
    )
    destination = tmp_out / "kpi_diario.html"

    exit_code = main(
        ["--input", str(csv_path), "--output", str(destination), "--umbral_p90", "300"]
    )

    assert exit_code == EXIT_OK
    html = destination.read_text(encoding="utf-8")
    assert html.count('class="alert"') == 1


@pytest.mark.e2e
def test_default_umbral_is_300(tmp_out: Path) -> None:
    csv_path = tmp_out / "kpi.csv"
    _write_csv(csv_path, ["2026-07-09,/lento,10,10,0,0,0,100.0,301.0"])
    destination = tmp_out / "kpi_diario.html"

    main(["--input", str(csv_path), "--output", str(destination)])

    assert 'class="alert"' in destination.read_text(encoding="utf-8")


@pytest.mark.e2e
def test_missing_input_file_is_a_data_error(tmp_out: Path) -> None:
    destination = tmp_out / "kpi_diario.html"
    exit_code = main(
        ["--input", str(tmp_out / "no-existe.csv"), "--output", str(destination)]
    )

    assert exit_code == EXIT_DATA_ERROR
    assert not destination.exists()


@pytest.mark.e2e
def test_csv_with_only_header_is_a_data_error(tmp_out: Path) -> None:
    csv_path = tmp_out / "kpi.csv"
    csv_path.write_text(_CSV_HEADER, encoding="utf-8")
    destination = tmp_out / "kpi_diario.html"

    exit_code = main(["--input", str(csv_path), "--output", str(destination)])

    assert exit_code == EXIT_DATA_ERROR
    assert not destination.exists()


@pytest.mark.e2e
def test_missing_column_is_a_data_error(tmp_out: Path) -> None:
    csv_path = tmp_out / "kpi.csv"
    csv_path.write_text("date_utc,endpoint_base,requests_total\n2026-07-09,/get,10\n", "utf-8")
    destination = tmp_out / "kpi_diario.html"

    exit_code = main(["--input", str(csv_path), "--output", str(destination)])

    assert exit_code == EXIT_DATA_ERROR


@pytest.mark.e2e
def test_creates_missing_output_directory(tmp_out: Path) -> None:
    destination = tmp_out / "nested" / "report" / "kpi_diario.html"
    exit_code = main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])

    assert exit_code == EXIT_OK
    assert destination.exists()


@pytest.mark.e2e
def test_rerun_is_idempotent(tmp_out: Path) -> None:
    destination = tmp_out / "kpi_diario.html"
    main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])
    first = destination.read_text(encoding="utf-8")

    main(["--input", str(_GOLDEN_INPUT), "--output", str(destination)])
    second = destination.read_text(encoding="utf-8")

    assert first == second


@pytest.mark.e2e
def test_non_numeric_umbral_is_a_config_error(tmp_out: Path) -> None:
    """`argparse` valida `--umbral_p90` como `float` y aborta solo (exit 2, SPEC-004)."""
    destination = tmp_out / "kpi_diario.html"
    with pytest.raises(SystemExit) as exc_info:
        main(
            ["--input", str(_GOLDEN_INPUT), "--output", str(destination), "--umbral_p90", "abc"]
        )
    assert exc_info.value.code == 2
