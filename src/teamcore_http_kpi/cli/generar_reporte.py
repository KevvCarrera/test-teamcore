"""`python generar_reporte.py --input ... --output ... --umbral_p90 ...`."""

import argparse
import logging
from pathlib import Path

from teamcore_http_kpi.application.build_report import run
from teamcore_http_kpi.cli._common import EXIT_DATA_ERROR, EXIT_OK
from teamcore_http_kpi.domain.errors import DataInputError
from teamcore_http_kpi.infrastructure.io.csv_repository import CsvKpiRepository
from teamcore_http_kpi.infrastructure.reporting.charts import MatplotlibChartRenderer
from teamcore_http_kpi.infrastructure.reporting.html_report import HtmlReportRenderer
from teamcore_http_kpi.logging_config import setup_logging

logger = logging.getLogger(__name__)

_DEFAULT_UMBRAL_P90 = 300.0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera el reporte HTML de KPIs a partir del CSV agregado."
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Ruta del CSV de KPIs de entrada."
    )
    parser.add_argument("--output", type=Path, required=True, help="Ruta del HTML de salida.")
    parser.add_argument(
        "--umbral_p90",
        type=float,
        default=_DEFAULT_UMBRAL_P90,
        help=f"Umbral de alerta para p90_elapsed_ms (por defecto {_DEFAULT_UMBRAL_P90}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de `generar_reporte.py`."""
    setup_logging()
    args = _parse_args(argv)

    try:
        run(
            args.input,
            args.output,
            args.umbral_p90,
            kpi_repository=CsvKpiRepository(),
            chart_renderer=MatplotlibChartRenderer(),
            report_renderer=HtmlReportRenderer(),
        )
    except DataInputError as exc:
        logger.error(str(exc))
        return EXIT_DATA_ERROR
    return EXIT_OK
