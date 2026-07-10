# Casos de Uso

> Actor principal: **Operador/Evaluador** que ejecuta las CLIs. Actor secundario:
> **Desarrollador/a de la parte PDI** (consumidor del CSV).

## UC-01 · Ejecutar los escenarios del cliente HTTP

- **Requisitos:** FR-01…FR-08
- **Precondición:** conectividad a `httpbin.org` (o httpbin local); config válida.
- **Flujo principal:**
  1. El operador ejecuta `python cliente_http.py`.
  2. El sistema ejecuta los 6 escenarios sobre una única sesión.
  3. Escribe `datos.json`, `datos.xml`, `titulo.html` en `out/`.
  4. Muestra un resumen con el estado por escenario y termina con código `0`.
- **Flujos alternativos:**
  - *403 persistente (FR-03):* se registra, se reintenta y el escenario se marca
    fallido sin abortar los demás.
  - *Fallo de red:* reintentos con backoff; si persiste, ese escenario falla (exit `3`).
- **Postcondición:** artefactos presentes y válidos; log con el detalle.

## UC-02 · Generar la bitácora sintética

- **Requisitos:** FR-09
- **Precondición:** Python y paquete instalados.
- **Flujo principal:**
  1. Ejecuta `python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42`.
  2. El sistema genera 500 registros deterministas conforme al esquema.
  3. Escribe `out/datos.jsonl` (trunca si existía) y termina con `0`.
- **Alternativo:** `--n_registros 0` ⇒ error de configuración (exit `2`).
- **Postcondición:** `datos.jsonl` reproducible con la misma `seed` (las pruebas fijan
  además el ancla temporal a nivel de función).

## UC-03 · Calcular KPIs diarios

- **Requisitos:** FR-10, FR-11
- **Precondición:** existe `out/datos.jsonl`.
- **Flujo principal:**
  1. Ejecuta `python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv`.
  2. Lee en streaming, normaliza endpoints, agrupa por `(date_utc, endpoint_base)`.
  3. Calcula KPIs (incluye p90 con `numpy.percentile`) y escribe el CSV conforme al
     contrato; termina con `0`.
- **Alternativos (FR-11):**
  - Entrada inexistente ⇒ exit `1` con la ruta.
  - Línea corrupta ⇒ `WARNING` con el nº de línea, se descarta y continúa; si no
    queda ningún registro válido ⇒ exit `1`.
- **Postcondición:** CSV válido, listo para el reporte **y para el ETL de PDI**.

## UC-04 · Generar el reporte HTML

- **Requisitos:** FR-13
- **Precondición:** existe `out/kpi_por_endpoint_dia.csv`.
- **Flujo principal:**
  1. Ejecuta
     `python generar_reporte.py --input out/kpi_por_endpoint_dia.csv --output out/report/kpi_diario.html --umbral_p90 300`.
  2. Carga el CSV, calcula métricas globales, genera 2 gráficos y ensambla el HTML.
  3. Marca en rojo los `p90` que superan el umbral; escribe el HTML autocontenido.
- **Alternativos:** CSV inexistente o sin columnas del contrato ⇒ exit `1`.
- **Postcondición:** `kpi_diario.html` abrible en navegador.

## UC-05 · Cargar los KPIs a SQLite con PDI

- **Requisitos:** FR-14…FR-17
- **Actor:** Operador de PDI (usuario), en su instalación de Spoon/Kitchen.
- **Precondición:** existe `out/kpi_por_endpoint_dia.csv`; conexión SQLite configurada.
- **Flujo principal:**
  1. El usuario abre/ejecuta `etl_pdi/j_daily_kpi.kjb` (Spoon o `kitchen.sh`).
  2. El job ejecuta `t_load_kpi.ktr`: CSV Input → tipificación → Filter Rows →
     Table Output a `stg_kpi_endpoint_dia` y `fct_kpi_endpoint_dia` (Truncate).
  3. El job verifica la carga (SQL/Table Exists) y registra el resultado en el log.
- **Alternativos:** fila inválida (`requests_total<=0` o `p90<avg`) ⇒ descartada por
  Filter Rows; error de carga ⇒ registrado y el job aborta.
- **Postcondición:** tablas pobladas con las filas válidas; reejecutar es idempotente.

## UC-06 · Ejecutar el pipeline completo

- **Requisitos:** FR-09 → FR-10 → FR-13 (+ FR-14…FR-17 en PDI)
- **Flujo:** `make pipeline` (o los tres comandos en orden) produce
  `datos.jsonl` → `kpi_por_endpoint_dia.csv` → `kpi_diario.html`; el usuario ejecuta
  además el job de PDI para la carga a SQLite.
- **Valor:** demuestra el encadenamiento por contratos de fichero de extremo a extremo.

## Mapa UC ↔ FR

| UC | FR |
|---|---|
| UC-01 | FR-01…FR-08 |
| UC-02 | FR-09 |
| UC-03 | FR-10, FR-11 |
| UC-04 | FR-13 |
| UC-05 | FR-14…FR-17 |
| UC-06 | FR-09, FR-10, FR-13…FR-17 |
