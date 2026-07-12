"""Pruebas de integración de `MatplotlibChartRenderer` (FR-13).

Backend `Agg`; se verifica que el resultado son bytes PNG válidos, sin
inspeccionar los píxeles (eso corresponde a una revisión visual manual).
"""

from datetime import date

import pytest

from teamcore_http_kpi.domain.models import KpiRow
from teamcore_http_kpi.infrastructure.reporting.charts import MatplotlibChartRenderer

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _rows() -> list[KpiRow]:
    return [
        KpiRow(date(2026, 7, 9), "/get", 42, 40, 0, 2, 3, 418.77, 742.10),
        KpiRow(date(2026, 7, 10), "/get", 10, 10, 0, 0, 0, 100.0, 150.0),
        KpiRow(date(2026, 7, 9), "/status", 15, 0, 15, 0, 1, 433.05, 769.44),
    ]


@pytest.mark.integration
def test_bar_requests_by_endpoint_produces_valid_png() -> None:
    png = MatplotlibChartRenderer().bar_requests_by_endpoint(_rows())
    assert png.startswith(_PNG_MAGIC)


@pytest.mark.integration
def test_p90_by_endpoint_produces_valid_png() -> None:
    png = MatplotlibChartRenderer().p90_by_endpoint(_rows())
    assert png.startswith(_PNG_MAGIC)


@pytest.mark.integration
def test_charts_handle_single_row() -> None:
    single = [KpiRow(date(2026, 7, 9), "/get", 1, 1, 0, 0, 0, 100.0, 100.0)]
    renderer = MatplotlibChartRenderer()
    assert renderer.bar_requests_by_endpoint(single).startswith(_PNG_MAGIC)
    assert renderer.p90_by_endpoint(single).startswith(_PNG_MAGIC)
