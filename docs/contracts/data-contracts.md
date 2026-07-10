# Contratos de Datos

> Estado: Aprobado · Versión de esquema: **1.0** · Decisión:
> [ADR-0009](../adr/0009-data-contracts-and-formats.md)

Este documento congela los formatos de todos los artefactos del sistema. Son
**contratos**: cambiarlos de forma incompatible exige un ADR y avisar a los
consumidores (incluida la parte de Pentaho).

---

## Bitácora `datos.jsonl`

Archivo de texto **UTF-8**, un objeto **JSON por línea** (JSON Lines), sin coma final
ni array envolvente. Producido por `generar_datos.py` (FR-09).

### Esquema de cada registro

| Campo | Tipo | Restricciones | Ejemplo |
|---|---|---|---|
| `timestamp_utc` | string | ISO-8601 UTC, sufijo `Z`, dentro de los últimos 3 días respecto a `ref_utc` | `"2026-07-09T10:15:23Z"` |
| `endpoint` | string | ∈ `{"/get","/post","/status/403","/basic-auth","/cookies","/xml","/html"}` | `"/get"` |
| `status_code` | integer | ver [reglas de status](#reglas-de-status_code) | `200` |
| `elapsed_ms` | number | `50.0 ≤ x ≤ 800.0`, 1 decimal | `120.5` |
| `parse_result` | string | `"ok"` o `"error"` | `"ok"` |

### Reglas de `status_code`
- `endpoint == "/status/403"` ⇒ **siempre** `403`.
- Resto de endpoints ⇒ **mayoritariamente** `200`; una minoría puede tomar otros
  códigos plausibles (p. ej. `500` esporádico) para dar variedad a los KPIs. La
  distribución exacta se fija en [SPEC-002](../specs/SPEC-002-generar-datos.md) y es
  determinista por `seed`.

### Regla de `parse_result`
- `"error"` en ~**5 %** de los registros; `"ok"` en el resto. Muestreo determinista
  por `seed`.

### Ejemplo (2 líneas)
```jsonl
{"timestamp_utc":"2026-07-09T10:15:23Z","endpoint":"/get","status_code":200,"elapsed_ms":120.5,"parse_result":"ok"}
{"timestamp_utc":"2026-07-08T22:41:02Z","endpoint":"/status/403","status_code":403,"elapsed_ms":97.3,"parse_result":"ok"}
```

### JSON Schema (validación en pruebas)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["timestamp_utc", "endpoint", "status_code", "elapsed_ms", "parse_result"],
  "properties": {
    "timestamp_utc": {"type": "string", "format": "date-time"},
    "endpoint": {"type": "string",
      "enum": ["/get","/post","/status/403","/basic-auth","/cookies","/xml","/html"]},
    "status_code": {"type": "integer", "minimum": 100, "maximum": 599},
    "elapsed_ms": {"type": "number", "minimum": 50, "maximum": 800},
    "parse_result": {"type": "string", "enum": ["ok", "error"]}
  }
}
```

---

## KPI CSV `kpi_por_endpoint_dia.csv`

Archivo **UTF-8**, delimitador `,`, con **encabezado**, punto decimal, salto de línea
`\n`. Una fila por combinación `(date_utc, endpoint_base)`. Producido por
`calcular_kpi.py` (FR-10) y consumido por `generar_reporte.py` (FR-13) **y por el
ETL de PDI** ([SPEC-005](../specs/SPEC-005-etl-pdi.md)).

### Columnas (orden congelado)

| # | Columna | Tipo | Definición |
|---|---|---|---|
| 1 | `date_utc` | date `YYYY-MM-DD` | Fecha UTC derivada de `timestamp_utc` |
| 2 | `endpoint_base` | string | Endpoint normalizado (ver abajo) |
| 3 | `requests_total` | integer | Nº de registros del grupo |
| 4 | `success_2xx` | integer | `status_code` ∈ [200, 299] |
| 5 | `client_4xx` | integer | `status_code` ∈ [400, 499] |
| 6 | `server_5xx` | integer | `status_code` ∈ [500, 599] |
| 7 | `parse_errors` | integer | `parse_result != "ok"` |
| 8 | `avg_elapsed_ms` | number | Media de `elapsed_ms` (redondeo: 2 decimales) |
| 9 | `p90_elapsed_ms` | number | `numpy.percentile(elapsed_ms, 90)` (2 decimales) |

**Orden de filas:** ascendente por `(date_utc, endpoint_base)` para salida
determinista (idempotencia y golden files).

### Ejemplo
```csv
date_utc,endpoint_base,requests_total,success_2xx,client_4xx,server_5xx,parse_errors,avg_elapsed_ms,p90_elapsed_ms
2026-07-09,/get,42,40,0,2,3,418.77,742.10
2026-07-09,/status,15,0,15,0,1,433.05,769.44
```

### KPIs — definiciones precisas
- **`success_2xx` / `client_4xx` / `server_5xx`:** conteos por rango de
  `status_code`. Nota: códigos `3xx` (redirecciones) no entran en ninguno de los
  tres; se contabilizan en `requests_total` pero no como éxito ni error (documentado).
- **`avg_elapsed_ms`:** media aritmética simple.
- **`p90_elapsed_ms`:** percentil 90 con **`numpy.percentile(x, 90)`**, interpolación
  lineal por defecto. Interpretación: el 90 % de las llamadas del grupo tardó ≤ este
  valor; es un indicador de *cola* de latencia más robusto que el promedio.

---

## Normalización de endpoints

Convierte `endpoint` (bitácora) en `endpoint_base` (KPI). Regla determinista:

1. Quitar query string y fragmento (`?...`, `#...`).
2. Quitar `/` final redundante.
3. Tomar el **primer segmento** de la ruta como base: `"/" + path.strip("/").split("/")[0]`.

### Tabla de casos (todos los endpoints del generador)

| `endpoint` | `endpoint_base` |
|---|---|
| `/get` | `/get` |
| `/post` | `/post` |
| `/status/403` | `/status` |
| `/basic-auth` | `/basic-auth` |
| `/cookies` | `/cookies` |
| `/xml` | `/xml` |
| `/html` | `/html` |

Casos límite adicionales (robustez, cubiertos por pruebas): `/status/500` → `/status`;
`/cookies/set` → `/cookies`; `""`/`"/"` → error de dato controlado. La razón de la
regla se documenta en el docstring de `domain/endpoints.py` (NFR-05).

---

## Artefactos del cliente HTTP

| Artefacto | Origen | Formato | Contenido |
|---|---|---|---|
| `datos.json` | `/get` (FR-04) | JSON UTF-8 | Estructura de la respuesta de `/get` |
| `datos.xml` | `/xml` (FR-05) | XML UTF-8 bien formado | Contenido parseado/serializado de `/xml` |
| `titulo.html` | `/html` (FR-06) | HTML/texto UTF-8 | Título extraído de la página `/html` |

Ubicación por defecto: `out/`. Nombres **exactos** del enunciado (NFR-06). No se
inventan subcarpetas ni parámetros de ruta.

---

## Modelo relacional SQLite (PDI)

Destino de la carga del ETL de PDI ([SPEC-005](../specs/SPEC-005-etl-pdi.md)). Dos
tablas con columnas espejo del CSV. DDL versionado en `etl_pdi/sql/ddl.sql`.

```sql
-- Staging: carga sin transformaciones adicionales (Truncate en cada corrida)
CREATE TABLE IF NOT EXISTS stg_kpi_endpoint_dia (
    date_utc        TEXT    NOT NULL,   -- 'YYYY-MM-DD'
    endpoint_base   TEXT    NOT NULL,
    requests_total  INTEGER NOT NULL,
    success_2xx     INTEGER NOT NULL,
    client_4xx      INTEGER NOT NULL,
    server_5xx      INTEGER NOT NULL,
    parse_errors    INTEGER NOT NULL,
    avg_elapsed_ms  REAL    NOT NULL,
    p90_elapsed_ms  REAL    NOT NULL
);

-- Fact: copia directa desde el flujo filtrado (Truncate en cada corrida)
CREATE TABLE IF NOT EXISTS fct_kpi_endpoint_dia (
    date_utc        TEXT    NOT NULL,
    endpoint_base   TEXT    NOT NULL,
    requests_total  INTEGER NOT NULL,
    success_2xx     INTEGER NOT NULL,
    client_4xx      INTEGER NOT NULL,
    server_5xx      INTEGER NOT NULL,
    parse_errors    INTEGER NOT NULL,
    avg_elapsed_ms  REAL    NOT NULL,
    p90_elapsed_ms  REAL    NOT NULL,
    PRIMARY KEY (date_utc, endpoint_base)
);
```

> SQLite es *dinámicamente tipado*; los tipos declarados actúan como *affinity*. La
> tipificación fuerte (fecha/entero/decimal) la aplica PDI en el paso de tipificación
> antes de la carga.

---

## Invariantes y validaciones aguas abajo

El ETL de PDI ([SPEC-005](../specs/SPEC-005-etl-pdi.md)) aplica un paso **Filter Rows**
con estas validaciones. Se documentan aquí porque el generador/KPI deben ser
consistentes con ellas:

| Validación (Filter Rows) | Comportamiento del CSV de KPIs |
|---|---|
| `requests_total > 0` | **Siempre** se cumple: un grupo existe solo si tiene ≥ 1 registro |
| `p90_elapsed_ms >= avg_elapsed_ms` | Se cumple en el caso general (distribución 50–800 ms). En grupos muy pequeños podría no cumplirse; es matemáticamente posible y **esperado**. El Filter Rows descartará esas filas; el CSV no las oculta |

Invariantes propios garantizados:
- `success_2xx + client_4xx + server_5xx ≤ requests_total` (la diferencia son `3xx`).
- `0 ≤ parse_errors ≤ requests_total`.
- Todas las columnas numéricas son no negativas.
- No hay filas duplicadas para una misma `(date_utc, endpoint_base)`.

---

## Versionado

Este contrato es **v1.0**. Un cambio incompatible (renombrar/reordenar columnas,
cambiar tipos o semántica) requiere: (a) nuevo ADR, (b) incremento de versión mayor,
(c) nota de migración para el consumidor PDI.
