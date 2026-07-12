-- DDL de las tablas de staging y fact para el ETL de KPIs (FR-16).
-- Ver docs/contracts/data-contracts.md#modelo-relacional-sqlite-pdi.
-- Idempotente: CREATE TABLE IF NOT EXISTS; las cargas usan Truncate (ver t_load_kpi.ktr).

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

-- Log de ejecución del job (FR-15): resultado de la carga y errores.
CREATE TABLE IF NOT EXISTS etl_log (
    run_at          TEXT    NOT NULL,
    status          TEXT    NOT NULL,   -- 'OK' / 'ERROR'
    rows_loaded     INTEGER,
    detail          TEXT
);
