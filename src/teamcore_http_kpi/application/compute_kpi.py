"""Caso de uso de `calcular_kpi.py`: leer la bitácora, agregar y escribir el CSV."""

import logging
from pathlib import Path

from teamcore_http_kpi.application.ports import BitacoraRepository, KpiRepository
from teamcore_http_kpi.domain.errors import DataInputError
from teamcore_http_kpi.domain.kpi import aggregate

logger = logging.getLogger(__name__)


def run(
    input_path: Path,
    output_path: Path,
    *,
    bitacora_repository: BitacoraRepository,
    kpi_repository: KpiRepository,
) -> int:
    """Lee `input_path`, agrega los KPIs y los escribe en `output_path`.

    Aborta con `DataInputError` si no queda ningún registro válido.
    Devuelve el número de filas de KPI escritas.
    """
    records = list(bitacora_repository.read(input_path))
    if not records:
        raise DataInputError(f"No se encontró ningún registro válido en {input_path}")

    rows = aggregate(records)
    kpi_repository.write(rows, output_path)
    logger.info("Se escribieron %d filas de KPI en %s", len(rows), output_path)
    return len(rows)
