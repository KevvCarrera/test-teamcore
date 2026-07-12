"""Caso de uso de `generar_reporte.py`: arma el reporte HTML de KPIs.

Lee el CSV de KPIs, calcula las métricas globales, dibuja los dos gráficos y
ensambla el HTML final autocontenido — todo a través de los puertos, sin
saber si detrás hay un CSV real o un doble de prueba.
"""

import logging
from pathlib import Path

from teamcore_http_kpi.application.ports import ChartRenderer, KpiRepository, ReportRenderer
from teamcore_http_kpi.domain.errors import DataInputError
from teamcore_http_kpi.domain.kpi import compute_global_metrics
from teamcore_http_kpi.infrastructure.reporting.html_report import (
    CHART_KEY_P90,
    CHART_KEY_REQUESTS,
)

logger = logging.getLogger(__name__)


def run(
    input_path: Path,
    output_path: Path,
    umbral_p90: float,
    *,
    kpi_repository: KpiRepository,
    chart_renderer: ChartRenderer,
    report_renderer: ReportRenderer,
) -> None:
    """Genera el reporte HTML en `output_path` a partir del CSV en `input_path`.

    Si el CSV existe pero no tiene ninguna fila, se aborta con
    `DataInputError` en vez de escribir un reporte vacío en silencio (el
    archivo inexistente o con columnas faltantes ya lo señala el propio
    `kpi_repository`).
    """
    rows = kpi_repository.read(input_path)
    if not rows:
        raise DataInputError(f"El CSV de KPIs no tiene ninguna fila: {input_path}")

    metrics = compute_global_metrics(rows)
    charts = {
        CHART_KEY_REQUESTS: chart_renderer.bar_requests_by_endpoint(rows),
        CHART_KEY_P90: chart_renderer.p90_by_endpoint(rows),
    }
    html = report_renderer.render(metrics, rows, charts, umbral_p90)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    logger.info("Reporte escrito en %s", output_path)
