"""`python cliente_http.py`: corre los 6 escenarios contra httpbin.org.

Sin parámetros: el enunciado no define flags para esta parte. Todo lo
necesario (URL base, credenciales de prueba, datos del formulario) ya vive
en `config.DEFAULT_SETTINGS`.
"""

import logging
from pathlib import Path

from teamcore_http_kpi.application.http_scenarios import run_all
from teamcore_http_kpi.cli._common import EXIT_NETWORK_ERROR, EXIT_OK
from teamcore_http_kpi.config import DEFAULT_SETTINGS
from teamcore_http_kpi.infrastructure.http.client import RequestsHttpClient
from teamcore_http_kpi.infrastructure.io.artifact_writer import FileSystemArtifactWriter
from teamcore_http_kpi.logging_config import setup_logging

logger = logging.getLogger(__name__)

_OUT_DIR = Path("out")


def main() -> int:
    """Punto de entrada de `cliente_http.py`."""
    setup_logging()
    settings = DEFAULT_SETTINGS
    http = RequestsHttpClient(
        settings.base_url,
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
        backoff_factor=settings.backoff_factor,
        retry_on_403=settings.retry_on_403,
    )
    writer = FileSystemArtifactWriter()

    results = run_all(http, writer, settings, _OUT_DIR)
    for result in results:
        estado = "OK" if result.ok else "FALLÓ"
        level = logging.INFO if result.ok else logging.WARNING
        logger.log(level, "%s: %s — %s", result.name, estado, result.detail)

    return EXIT_OK if all(result.ok for result in results) else EXIT_NETWORK_ERROR
