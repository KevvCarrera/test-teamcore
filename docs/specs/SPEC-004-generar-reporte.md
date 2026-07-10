# SPEC-004 · Reporte HTML de KPIs (`generar_reporte.py`)

- **ID:** SPEC-004
- **Estado:** Aprobado
- **Requisitos cubiertos:** FR-13, NFR-05, NFR-09
- **Contratos:** [KPI CSV](../contracts/data-contracts.md#kpi-csv)
- **Decisiones:** [ADR-0010](../adr/0010-reporting-pandas-matplotlib.md)

## 1. Objetivo

Leer `kpi_por_endpoint_dia.csv` y generar `out/report/kpi_diario.html`, un reporte
visual autocontenido con métricas globales, tabla por endpoint y dos gráficos, con
alerta por umbral de `p90`.

## 2. Entradas y salidas

- **CLI (exacta):**
  `python generar_reporte.py --input out/kpi_por_endpoint_dia.csv --output out/report/kpi_diario.html --umbral_p90 300`
- **Parámetros:**
  - `--input` (path): CSV de KPIs. Requerido.
  - `--output` (path): HTML de salida. Requerido.
  - `--umbral_p90` (float): umbral de alerta para `p90_elapsed_ms`. Por defecto `300`.
- **Salida:** HTML UTF-8 autocontenido (gráficos PNG embebidos en base64).

## 3. Comportamiento

Carga con `pandas`; métricas en dominio; gráficos con `matplotlib` (backend `Agg`);
ensamblado por `HtmlReportRenderer`. **Sin llamadas HTTP.**

### Métricas globales
- `total_requests` = Σ `requests_total`.
- `%_success` = Σ `success_2xx` / `total_requests`.
- `%_errors` = (Σ `client_4xx` + Σ `server_5xx`) / `total_requests`.
- `p90_global` = `numpy.percentile` de las latencias representadas. Como el CSV ya
  está agregado, el p90 global se aproxima como el **máximo de los `p90` por
  endpoint** *o* se recomputa desde `datos.jsonl` si se provee; el método elegido se
  documenta en el reporte y en el código (NFR-05). **Decisión por defecto:** p90
  global = percentil 90 ponderado por `requests_total` sobre los `p90` por grupo, con
  nota explicativa de su carácter aproximado.

### Tabla por endpoint (agregada sobre fechas)
Columnas: `endpoint_base`, `requests_total`, `%_success`, `%_client_4xx`,
`%_server_5xx`, `avg_elapsed_ms`, `p90_elapsed_ms`.

### Gráficos
1. **Barra horizontal:** `requests_total` por `endpoint_base`.
2. **Barra/línea:** `p90_elapsed_ms` por `endpoint_base` (con línea del umbral).

### Alerta por umbral
Celdas de `p90_elapsed_ms` con valor `> --umbral_p90` se pintan de **rojo**
(clase CSS `.alert`). Se muestra el umbral usado en el encabezado del reporte.

## 4. Interfaz pública (diseño)

```python
# domain/report.py
@dataclass(frozen=True)
class GlobalMetrics:
    total_requests: int
    pct_success: float
    pct_errors: float
    p90_global: float

def compute_global_metrics(rows: Sequence[KpiRow]) -> GlobalMetrics: ...
def aggregate_by_endpoint(rows: Sequence[KpiRow]) -> list[EndpointSummary]: ...

# infrastructure/reporting/html_report.py
class HtmlReportRenderer:
    def render(self, metrics: GlobalMetrics, summaries: Sequence[EndpointSummary],
               charts: Mapping[str, bytes], umbral_p90: float) -> str: ...
```

## 5. Manejo de errores

- `--input` inexistente ⇒ `InputFileNotFoundError` (exit `1`).
- CSV sin las columnas del contrato ⇒ `DataInputError` explicando la columna
  faltante (exit `1`).
- `--umbral_p90` no numérico ⇒ `ConfigError` (exit `2`).
- Directorio de salida se crea si falta; escritura idempotente (sobrescribe).
- Valores se **escapan** al insertarse en HTML (seguridad, NFR-14).

## 6. Criterios de aceptación (Gherkin)

```gherkin
Feature: Reporte HTML (FR-13)
  Scenario: Contenido del reporte
    Given un CSV de KPIs de referencia
    When ejecuto generar_reporte.py --input ... --output ... --umbral_p90 300
    Then el HTML incluye total de solicitudes, % de éxito y % de errores
    And incluye una tabla con una fila por endpoint_base
    And incluye dos gráficos embebidos (requests_total y p90 por endpoint)

  Scenario: Alerta por umbral
    Given un endpoint con p90_elapsed_ms = 742 y umbral 300
    Then esa celda de p90 se marca con la clase de alerta (rojo)
    And un endpoint con p90 = 120 no se marca

  Scenario: Autocontenido
    Then el HTML no referencia archivos de imagen externos
    And abre correctamente en un navegador sin recursos adicionales

  Scenario: Errores (FR-11/NFR)
    When el CSV no existe
    Then termina con código 1 y mensaje con la ruta
    When falta una columna del contrato
    Then termina con código 1 indicando la columna ausente
```

## 7. Pruebas asociadas

- `tests/unit/test_report_metrics.py`: métricas globales, agregación por endpoint,
  cálculo de porcentajes, lógica de umbral (marcar/no marcar).
- `tests/e2e/test_generar_reporte_cli.py`: genera HTML desde golden CSV; verifica
  presencia de secciones, celdas de alerta y ausencia de `<img src="archivo">`
  externo (todo en base64).

## 8. Trazabilidad

FR-13, NFR-05/09 → [RTM](../requirements/requirements-traceability-matrix.md).
