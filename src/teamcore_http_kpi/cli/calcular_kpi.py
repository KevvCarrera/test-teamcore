"""`python calcular_kpi.py --input ... --output ...`."""

import argparse
import logging
from pathlib import Path

from teamcore_http_kpi.application.compute_kpi import run
from teamcore_http_kpi.cli._common import EXIT_DATA_ERROR, EXIT_OK
from teamcore_http_kpi.domain.errors import DataInputError
from teamcore_http_kpi.infrastructure.io.csv_repository import CsvKpiRepository
from teamcore_http_kpi.infrastructure.io.jsonl_repository import JsonlBitacoraRepository
from teamcore_http_kpi.logging_config import setup_logging

logger = logging.getLogger(__name__)

_DEFAULT_INPUT = Path("out/datos.jsonl")
_DEFAULT_OUTPUT = Path("out/kpi_por_endpoint_dia.csv")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calcula los KPIs diarios por endpoint a partir de la bitácora."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=_DEFAULT_INPUT,
        help=f"Ruta de la bitácora JSONL de entrada (por defecto {_DEFAULT_INPUT}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=f"Ruta del CSV de KPIs de salida (por defecto {_DEFAULT_OUTPUT}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de `calcular_kpi.py`."""
    setup_logging()
    args = _parse_args(argv)

    try:
        run(
            args.input,
            args.output,
            bitacora_repository=JsonlBitacoraRepository(),
            kpi_repository=CsvKpiRepository(),
        )
    except DataInputError as exc:
        logger.error(str(exc))
        return EXIT_DATA_ERROR
    return EXIT_OK
