"""`python generar_datos.py --n_registros ... --salida ... --seed ...`."""

import argparse
import logging
from pathlib import Path

from teamcore_http_kpi.application.generate_data import run
from teamcore_http_kpi.cli._common import EXIT_CONFIG_ERROR, EXIT_DATA_ERROR, EXIT_OK
from teamcore_http_kpi.domain.errors import ConfigError
from teamcore_http_kpi.infrastructure.io.jsonl_repository import JsonlBitacoraRepository
from teamcore_http_kpi.logging_config import setup_logging

logger = logging.getLogger(__name__)

_DEFAULT_N_REGISTROS = 500
_DEFAULT_SALIDA = Path("out/datos.jsonl")
_DEFAULT_SEED = 42


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una bitácora sintética de llamadas HTTP (datos.jsonl)."
    )
    parser.add_argument(
        "--n_registros",
        type=int,
        default=_DEFAULT_N_REGISTROS,
        help=f"Número de registros a generar (por defecto {_DEFAULT_N_REGISTROS}).",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=_DEFAULT_SALIDA,
        help=f"Ruta del archivo JSONL de salida (por defecto {_DEFAULT_SALIDA}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=_DEFAULT_SEED,
        help=f"Semilla para reproducibilidad (por defecto {_DEFAULT_SEED}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de `generar_datos.py`."""
    setup_logging()
    args = _parse_args(argv)

    try:
        run(args.n_registros, args.salida, args.seed, repository=JsonlBitacoraRepository())
    except ConfigError as exc:
        logger.error(str(exc))
        return EXIT_CONFIG_ERROR
    except OSError as exc:
        logger.error("Error de E/S al escribir %s: %s", args.salida, exc)
        return EXIT_DATA_ERROR
    return EXIT_OK
