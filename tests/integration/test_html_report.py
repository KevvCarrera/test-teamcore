"""Pruebas de integración de `HtmlReportRenderer` (FR-13).

Verifica secciones, alerta por umbral y que el HTML es autocontenido
(sin referencias a imágenes externas), según docs/specs/SPEC-004-generar-reporte.md.
"""

from datetime import date

import pytest

from teamcore_http_kpi.domain.kpi import compute_global_metrics
from teamcore_http_kpi.domain.models import KpiRow
from teamcore_http_kpi.infrastructure.reporting.html_report import (
    CHART_KEY_P90,
    CHART_KEY_REQUESTS,
    HtmlReportRenderer,
)

_FAKE_PNG = b"\x89PNG\r\n\x1a\nfake"


def _rows() -> list[KpiRow]:
    return [
        KpiRow(date(2026, 7, 9), "/get", 42, 40, 0, 2, 3, 418.77, 200.0),
        KpiRow(date(2026, 7, 9), "/status", 15, 0, 15, 0, 1, 433.05, 769.44),
    ]


def _charts() -> dict[str, bytes]:
    return {CHART_KEY_REQUESTS: _FAKE_PNG, CHART_KEY_P90: _FAKE_PNG}


@pytest.mark.integration
def test_render_includes_global_metrics() -> None:
    rows = _rows()
    metrics = compute_global_metrics(rows)
    html = HtmlReportRenderer().render(metrics, rows, _charts(), umbral_p90=300.0)

    assert "Total de solicitudes" in html
    assert str(metrics.total_requests) in html


@pytest.mark.integration
def test_render_includes_one_table_row_per_endpoint() -> None:
    rows = _rows()
    metrics = compute_global_metrics(rows)
    html = HtmlReportRenderer().render(metrics, rows, _charts(), umbral_p90=300.0)

    assert html.count("<tr>") == 1 + 2  # encabezado + 2 endpoints
    assert ">/get<" in html
    assert ">/status<" in html


@pytest.mark.integration
def test_render_marks_p90_above_threshold_in_red() -> None:
    rows = _rows()
    metrics = compute_global_metrics(rows)
    html = HtmlReportRenderer().render(metrics, rows, _charts(), umbral_p90=300.0)

    assert 'class="alert"' in html  # /status con p90=769.44 > 300


@pytest.mark.integration
def test_render_does_not_mark_p90_below_threshold() -> None:
    rows = [KpiRow(date(2026, 7, 9), "/get", 10, 10, 0, 0, 0, 100.0, 120.0)]
    metrics = compute_global_metrics(rows)
    html = HtmlReportRenderer().render(metrics, rows, _charts(), umbral_p90=300.0)

    assert 'class="alert"' not in html


@pytest.mark.integration
def test_render_is_self_contained_with_embedded_charts() -> None:
    rows = _rows()
    metrics = compute_global_metrics(rows)
    html = HtmlReportRenderer().render(metrics, rows, _charts(), umbral_p90=300.0)

    assert "data:image/png;base64," in html
    assert 'src="out/' not in html
    assert 'src="./' not in html


@pytest.mark.integration
def test_render_escapes_endpoint_values() -> None:
    rows = [KpiRow(date(2026, 7, 9), "/<script>", 1, 1, 0, 0, 0, 100.0, 100.0)]
    metrics = compute_global_metrics(rows)
    html = HtmlReportRenderer().render(metrics, rows, _charts(), umbral_p90=300.0)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
