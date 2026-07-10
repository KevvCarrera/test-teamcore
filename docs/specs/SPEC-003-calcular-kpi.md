# SPEC-003 · Cálculo de KPIs diarios (`calcular_kpi.py`)

- **ID:** SPEC-003
- **Estado:** Aprobado
- **Requisitos cubiertos:** FR-10, FR-11, NFR-05, NFR-08, NFR-13
- **Contratos:** [KPI CSV](../contracts/data-contracts.md#kpi-csv),
  [normalización](../contracts/data-contracts.md#normalización-de-endpoints)
- **Decisiones:** [ADR-0009](../adr/0009-data-contracts-and-formats.md)

## 1. Objetivo

Leer `datos.jsonl` y producir `kpi_por_endpoint_dia.csv` con los KPIs agregados por
`(date_utc, endpoint_base)`, conforme al contrato, con el p90 vía `numpy.percentile`.

## 2. Entradas y salidas

- **CLI (entrada y salida por línea de comandos, como pide el enunciado):**
  `python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv`
- **Entrada:** `datos.jsonl` (contrato de bitácora).
- **Salida:** `kpi_por_endpoint_dia.csv` (contrato de KPI), filas ordenadas por
  `(date_utc, endpoint_base)`.

## 3. Comportamiento

Lógica pura en `domain/kpi.py` y `domain/endpoints.py`; E/S en `io/*`; orquestación
en `application/compute_kpi.py`.

1. **Lectura en streaming** del JSONL (memoria acotada, NFR-13).
2. **Normalización** de `endpoint` → `endpoint_base` (documentada, NFR-05).
3. **`date_utc`** = fecha (`YYYY-MM-DD`) de `timestamp_utc`.
4. **Agrupación** por `(date_utc, endpoint_base)`.
5. **Agregados por grupo:**
   - `requests_total` = conteo.
   - `success_2xx`/`client_4xx`/`server_5xx` = conteos por rango de `status_code`.
   - `parse_errors` = conteo de `parse_result != "ok"`.
   - `avg_elapsed_ms` = media (2 decimales).
   - `p90_elapsed_ms` = `numpy.percentile(elapsed_ms, 90)` (2 decimales).
6. **Escritura** determinista del CSV (encabezado + filas ordenadas).

> **Comentario obligatorio en código (NFR-05):** el docstring de
> `normalize_endpoint` explica la regla de "primer segmento" con ejemplos, y el de
> `percentile_90` explica que usa `numpy.percentile(x, 90)` con interpolación lineal
> y qué significa el p90.

## 4. Interfaz pública (diseño)

```python
# domain/endpoints.py
def normalize_endpoint(raw: str) -> str: ...

# domain/kpi.py
def percentile_90(values: Sequence[float]) -> float:
    """p90 vía numpy.percentile(values, 90) (interpolación lineal)."""

def aggregate(records: Iterable[BitacoraRecord]) -> list[KpiRow]:
    """Agrupa por (date_utc, endpoint_base) y calcula los KPIs. Orden determinista."""
```

## 5. Manejo de errores (FR-11)

- Entrada inexistente ⇒ `InputFileNotFoundError` (exit `1`) con la ruta.
- Línea JSONL mal formada / campo faltante ⇒ política fija (sin flag): se emite un
  `WARNING` con el **nº de línea**, se descarta la línea y se continúa (robustez).
  Se lleva un contador de líneas descartadas que se registra al final.
- Si **ninguna** línea es válida (o el archivo está vacío) ⇒ `DataInputError`
  (exit `1`), para no producir un CSV vacío silenciosamente (fail fast).
- Grupo con `elapsed_ms` vacío no ocurre (todo registro tiene latencia); aun así el
  cálculo de p90 valida entrada no vacía (fail fast).

## 6. Criterios de aceptación (Gherkin)

```gherkin
Feature: Cálculo de KPIs (FR-10)
  Scenario: Salida conforme al contrato
    Given un datos.jsonl de referencia (golden input)
    When ejecuto calcular_kpi.py --input ... --output ...
    Then el CSV tiene el encabezado y el orden de columnas del contrato
    And las filas están ordenadas por (date_utc, endpoint_base)
    And los valores coinciden con el CSV de referencia (golden output)

  Scenario: Normalización de endpoint
    Given registros con endpoint "/status/403"
    Then aparecen agregados bajo endpoint_base "/status"

  Scenario: Percentil 90
    Given un grupo con latencias conocidas
    Then p90_elapsed_ms es igual a numpy.percentile(latencias, 90) redondeado a 2 decimales

  Scenario: Conteos por rango de status
    Then success_2xx cuenta 200-299, client_4xx cuenta 400-499, server_5xx cuenta 500-599

  Scenario: Manejo de errores (FR-11)
    When el archivo de entrada no existe
    Then termina con código 1 y un mensaje que incluye la ruta
    When una línea está corrupta (JSON mal formado)
    Then se omite esa línea con un WARNING que indica el número de línea
    And el resto de registros se procesa normalmente
    When ninguna línea es válida
    Then termina con código 1 sin generar un CSV vacío

  Scenario: Idempotencia (NFR-08)
    When ejecuto dos veces con la misma entrada
    Then el CSV resultante es idéntico
```

## 7. Pruebas asociadas

- `tests/unit/test_endpoints.py`: tabla de normalización + casos límite.
- `tests/unit/test_kpi.py`: percentil, conteos por rango, medias, orden determinista.
- `tests/integration/test_io_errors.py`: fichero inexistente, línea corrupta
  (WARNING + skip), archivo sin registros válidos.
- `tests/e2e/test_calcular_kpi_cli.py`: golden input → golden output; idempotencia.

## 8. Trazabilidad

FR-10, FR-11, NFR-05/08/13 → [RTM](../requirements/requirements-traceability-matrix.md).
