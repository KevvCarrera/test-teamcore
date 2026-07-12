"""`MatplotlibChartRenderer`: dibuja los dos gráficos del reporte como PNG.

Se usa el backend `Agg` porque no hay pantalla detrás (esto puede correr en
un servidor sin monitor). Los PNG no se guardan como archivo: se devuelven
como bytes, para que `html_report.py` los incruste directamente en el HTML.
"""

import io
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from teamcore_http_kpi.domain.models import KpiRow


class MatplotlibChartRenderer:
    """Los dos gráficos del reporte, sumando/comparando entre endpoints."""

    def bar_requests_by_endpoint(self, rows: Sequence[KpiRow]) -> bytes:
        """Barra horizontal: total de solicitudes por endpoint."""
        grouped = _grouped_by_endpoint(rows)
        endpoints = list(grouped.keys())
        totals = [sum(row.requests_total for row in group) for group in grouped.values()]

        fig, ax = plt.subplots()
        ax.barh(endpoints, totals, color="#4C72B0")
        ax.set_xlabel("Total de solicitudes")
        ax.set_ylabel("Endpoint")
        ax.set_title("Solicitudes totales por endpoint")
        fig.tight_layout()
        return _render_png(fig)

    def p90_by_endpoint(self, rows: Sequence[KpiRow]) -> bytes:
        """Barra: percentil 90 de latencia por endpoint (el mayor entre sus fechas)."""
        grouped = _grouped_by_endpoint(rows)
        endpoints = list(grouped.keys())
        p90s = [max(row.p90_elapsed_ms for row in group) for group in grouped.values()]

        fig, ax = plt.subplots()
        ax.bar(endpoints, p90s, color="#DD8452")
        ax.set_xlabel("Endpoint")
        ax.set_ylabel("p90 elapsed (ms)")
        ax.set_title("Percentil 90 de latencia por endpoint")
        fig.tight_layout()
        return _render_png(fig)


def _grouped_by_endpoint(rows: Sequence[KpiRow]) -> dict[str, list[KpiRow]]:
    """Agrupa `rows` por `endpoint_base`, sumando/comparando entre fechas."""
    groups: dict[str, list[KpiRow]] = defaultdict(list)
    for row in rows:
        groups[row.endpoint_base].append(row)
    return dict(sorted(groups.items()))


def _render_png(fig: Any) -> bytes:
    """Serializa una figura de matplotlib a bytes PNG y libera sus recursos."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    return buffer.getvalue()
