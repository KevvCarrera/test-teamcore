"""Caso de uso de `generar_datos.py`: pedirle al dominio los registros y guardarlos."""

import logging
from datetime import UTC, datetime
from pathlib import Path

from teamcore_http_kpi.application.ports import BitacoraRepository
from teamcore_http_kpi.domain.errors import ConfigError
from teamcore_http_kpi.domain.generation import generate_records

logger = logging.getLogger(__name__)


def run(
    n_registros: int,
    salida: Path,
    seed: int,
    *,
    repository: BitacoraRepository,
    ref_utc: datetime | None = None,
) -> int:
    """Genera `n_registros` y los escribe en `salida`. Devuelve cuántos se escribieron.

    `ref_utc` no es un parámetro de la CLI (el enunciado no lo pide): se usa
    `datetime.now(UTC)` en producción, y las pruebas pasan un valor fijo aquí
    mismo para poder comparar resultados.
    """
    if n_registros <= 0:
        raise ConfigError(f"--n_registros debe ser mayor que 0 (recibido: {n_registros})")

    instant = ref_utc if ref_utc is not None else datetime.now(UTC)
    records = generate_records(n_registros, seed=seed, ref_utc=instant)
    count = repository.write(records, salida)
    logger.info("Se escribieron %d registros en %s", count, salida)
    return count
