"""`HtmlReportRenderer`: arma el HTML final del reporte, en un único archivo."""

import base64
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape

from teamcore_http_kpi.domain.models import GlobalMetrics, KpiRow

CHART_KEY_REQUESTS = "requests_by_endpoint"
CHART_KEY_P90 = "p90_by_endpoint"


@dataclass(frozen=True)
class _EndpointSummary:
    """Resumen de un `endpoint_base`, agregado sobre todas sus fechas."""

    endpoint_base: str
    requests_total: int
    pct_success: float
    pct_client_4xx: float
    pct_server_5xx: float
    avg_elapsed_ms: float
    p90_elapsed_ms: float


class HtmlReportRenderer:
    """Junta métricas, tabla y gráficos en una sola página HTML."""

    def render(
        self,
        metrics: GlobalMetrics,
        rows: Sequence[KpiRow],
        charts: Mapping[str, bytes],
        umbral_p90: float,
    ) -> str:
        """`rows` llega sin agregar por endpoint todavía; `charts` trae los PNG ya
        renderizados bajo las claves `CHART_KEY_REQUESTS` y `CHART_KEY_P90`.
        Cualquier `p90_elapsed_ms` por encima de `umbral_p90` sale marcado en rojo.
        """
        table_rows = "\n".join(
            _render_table_row(summary, umbral_p90) for summary in _summarize_by_endpoint(rows)
        )
        return _TEMPLATE.format(
            umbral_p90=umbral_p90,
            total_requests=metrics.total_requests,
            pct_success=metrics.pct_success * 100,
            pct_errors=metrics.pct_errors * 100,
            p90_global=metrics.p90_global,
            table_rows=table_rows,
            chart_requests=_embed_png(charts[CHART_KEY_REQUESTS]),
            chart_p90=_embed_png(charts[CHART_KEY_P90]),
        )


def _summarize_by_endpoint(rows: Sequence[KpiRow]) -> list[_EndpointSummary]:
    """Colapsa todas las fechas de cada endpoint en una sola fila de resumen."""
    groups: dict[str, list[KpiRow]] = defaultdict(list)
    for row in rows:
        groups[row.endpoint_base].append(row)

    summaries = []
    for endpoint_base, group in sorted(groups.items()):
        total = sum(r.requests_total for r in group)
        success = sum(r.success_2xx for r in group)
        client_4xx = sum(r.client_4xx for r in group)
        server_5xx = sum(r.server_5xx for r in group)
        weighted_avg = sum(r.avg_elapsed_ms * r.requests_total for r in group) / total
        # Aproximación: promedio ponderado de los p90 diarios, no un percentil
        # recalculado desde datos crudos (ya no hay latencias individuales aquí).
        weighted_p90 = sum(r.p90_elapsed_ms * r.requests_total for r in group) / total
        summaries.append(
            _EndpointSummary(
                endpoint_base=endpoint_base,
                requests_total=total,
                pct_success=success / total,
                pct_client_4xx=client_4xx / total,
                pct_server_5xx=server_5xx / total,
                avg_elapsed_ms=round(weighted_avg, 2),
                p90_elapsed_ms=round(weighted_p90, 2),
            )
        )
    return summaries


def _render_table_row(summary: _EndpointSummary, umbral_p90: float) -> str:
    """Arma una fila `<tr>` de la tabla, escapando valores y marcando la alerta."""
    p90_class = ' class="alert"' if summary.p90_elapsed_ms > umbral_p90 else ""
    return (
        "<tr>"
        f"<td>{escape(summary.endpoint_base)}</td>"
        f"<td>{summary.requests_total}</td>"
        f"<td>{summary.pct_success * 100:.1f}%</td>"
        f"<td>{summary.pct_client_4xx * 100:.1f}%</td>"
        f"<td>{summary.pct_server_5xx * 100:.1f}%</td>"
        f"<td>{summary.avg_elapsed_ms:.2f}</td>"
        f"<td{p90_class}>{summary.p90_elapsed_ms:.2f}</td>"
        "</tr>"
    )


def _embed_png(png_bytes: bytes) -> str:
    """Codifica `png_bytes` como un `data:` URI base64 para incrustar en `<img>`."""
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reporte diario de KPIs</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 2rem; color: #1a1a1a; }}
  h1, h2 {{ color: #2b2b2b; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ border: 1px solid #ccc; padding: 0.5rem 0.75rem; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ background-color: #f2f2f2; }}
  td.alert {{ color: #b00020; font-weight: bold; }}
  .metrics {{ display: flex; gap: 2rem; margin: 1rem 0 2rem; flex-wrap: wrap; }}
  .metric {{ background: #f7f7f7; padding: 1rem 1.5rem; border-radius: 6px; }}
  .metric .value {{ font-size: 1.5rem; font-weight: bold; }}
  img {{ max-width: 100%; margin: 1rem 0; }}
</style>
</head>
<body>
<h1>Reporte diario de KPIs</h1>
<p>Umbral de alerta de p90: <strong>{umbral_p90} ms</strong>
   (los valores que lo superan se marcan en rojo).</p>

<div class="metrics">
  <div class="metric">
    <div>Total de solicitudes</div><div class="value">{total_requests}</div>
  </div>
  <div class="metric">
    <div>% de éxito (2xx)</div><div class="value">{pct_success:.1f}%</div>
  </div>
  <div class="metric">
    <div>% de errores (4xx/5xx)</div><div class="value">{pct_errors:.1f}%</div>
  </div>
  <div class="metric">
    <div>p90 global (aprox.)</div><div class="value">{p90_global:.2f} ms</div>
  </div>
</div>

<h2>KPIs por endpoint</h2>
<table>
<thead>
<tr>
  <th>Endpoint</th><th>Solicitudes</th><th>% éxito</th><th>% error 4xx</th>
  <th>% error 5xx</th><th>Promedio (ms)</th><th>p90 (ms)</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>

<h2>Gráficos</h2>
<img src="{chart_requests}" alt="Solicitudes totales por endpoint">
<img src="{chart_p90}" alt="Percentil 90 de latencia por endpoint">
</body>
</html>
"""
