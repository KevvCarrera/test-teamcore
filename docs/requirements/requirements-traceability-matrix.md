# Matriz de Trazabilidad de Requisitos (RTM)

Vincula cada requerimiento con su **especificación**, el **módulo** que lo
implementará y las **pruebas** que lo verifican. Es el mecanismo que garantiza que
*todo* el código tiene una razón documentada y que *ningún* requisito queda sin
cubrir.

> Los módulos/tests marcados como *planificado* pertenecen a la fase de
> implementación (aún no creados). Sus rutas ya están definidas por
> [project-structure.md](../architecture/project-structure.md).

## Requisitos funcionales

| Req | Spec | Módulo (planificado) | Prueba (planificada) | Entregable |
|---|---|---|---|---|
| FR-01 Auth básica | [SPEC-001](../specs/SPEC-001-http-client.md) | `infrastructure/http/tasks.py::basic_auth` | `tests/integration/test_http_tasks.py::test_basic_auth_ok` | — |
| FR-02 Cookies/sesión | [SPEC-001](../specs/SPEC-001-http-client.md) | `infrastructure/http/tasks.py::set_and_get_cookies` | `...::test_cookie_session_persists` | — |
| FR-03 Restricción 403 | [SPEC-001](../specs/SPEC-001-http-client.md) | `infrastructure/http/client.py` (retry) + `tasks.py::simulate_forbidden` | `...::test_403_detected_and_retried` | log |
| FR-04 JSON `/get` | [SPEC-001](../specs/SPEC-001-http-client.md) | `tasks.py::extract_json` + `io/artifact_writer.py` | `...::test_extract_json_writes_datos_json` | `datos.json` |
| FR-05 XML `/xml` | [SPEC-001](../specs/SPEC-001-http-client.md) | `tasks.py::extract_xml` | `...::test_extract_xml_writes_datos_xml` | `datos.xml` |
| FR-06 Título HTML `/html` | [SPEC-001](../specs/SPEC-001-http-client.md) | `tasks.py::extract_html_title` | `...::test_extract_title_writes_titulo_html` | `titulo.html` |
| FR-07 Formulario `/post` | [SPEC-001](../specs/SPEC-001-http-client.md) | `tasks.py::submit_form` | `...::test_submit_form_echoes_fields` | — |
| FR-08 Redirecciones | [SPEC-001](../specs/SPEC-001-http-client.md) | `tasks.py::follow_redirect` | `...::test_redirect_reaches_get` | — |
| FR-09 Generar bitácora | [SPEC-002](../specs/SPEC-002-generar-datos.md) | `application/generate_data.py` + `domain/generation.py` | `tests/unit/test_generation.py`, `tests/e2e/test_generar_datos_cli.py` | `datos.jsonl` |
| FR-10 Calcular KPIs | [SPEC-003](../specs/SPEC-003-calcular-kpi.md) | `application/compute_kpi.py` + `domain/kpi.py` + `domain/endpoints.py` | `tests/unit/test_kpi.py`, `tests/unit/test_endpoints.py`, `tests/e2e/test_calcular_kpi_cli.py` | `kpi_por_endpoint_dia.csv` |
| FR-11 Manejo de errores | [SPEC-002](../specs/SPEC-002-generar-datos.md), [SPEC-003](../specs/SPEC-003-calcular-kpi.md) | `domain/errors.py` + `io/jsonl_repository.py` | `tests/integration/test_io_errors.py` | — |
| FR-12 README | [SPEC-000](../specs/SPEC-000-template.md) (transversal) | `README.md` | revisión manual | `README.md` |
| FR-13 Reporte HTML | [SPEC-004](../specs/SPEC-004-generar-reporte.md) | `application/build_report.py` + `infrastructure/reporting/*` | `tests/unit/test_report_metrics.py`, `tests/e2e/test_generar_reporte_cli.py` | `kpi_diario.html` |
| FR-14 Transformación PDI | [SPEC-005](../specs/SPEC-005-etl-pdi.md) | `etl_pdi/t_load_kpi.ktr` | validación estructural + prueba de usuario en Spoon | `t_load_kpi.ktr` |
| FR-15 Job PDI | [SPEC-005](../specs/SPEC-005-etl-pdi.md) | `etl_pdi/j_daily_kpi.kjb` | validación estructural + prueba de usuario en Kitchen | `j_daily_kpi.kjb` |
| FR-16 Persistencia SQLite | [SPEC-005](../specs/SPEC-005-etl-pdi.md) | `etl_pdi/sql/ddl.sql` + Table Output (Truncate) | prueba de idempotencia (usuario) | `stg_*`, `fct_*` |
| FR-17 Config PDI | [SPEC-005](../specs/SPEC-005-etl-pdi.md) | `etl_pdi/config/kettle.properties.example` | revisión | plantilla de config |

## Requisitos no funcionales

| Req | Dónde se satisface | Verificación |
|---|---|---|
| NFR-01 Python 3.11+ | `pyproject.toml` (`requires-python`) | CI |
| NFR-02 Frontera de deps | `pyproject.toml`, [ADR-0012](../adr/0012-dependency-boundary-allowed-libraries.md) | revisión |
| NFR-03 Robustez | `domain/errors.py`, política de errores por spec | `tests/**/test_*errors*` |
| NFR-04 Legibilidad | Arquitectura por capas, funciones puras | `ruff`, revisión |
| NFR-05 Documentación | docstrings de `domain/endpoints.py` y `domain/kpi.py` | revisión |
| NFR-06 Formato entregables | `io/*`, `cli/*` | `tests/e2e/*` |
| NFR-07 Reproducibilidad | `domain/generation.py` (semilla; tiempo de referencia inyectable en pruebas) | `tests/unit/test_generation.py::test_determinism` |
| NFR-08 Idempotencia | escritura con truncado en `io/*` | `tests/e2e/*::test_idempotent_rerun` |
| NFR-09 Tipado | `type hints` + `mypy --strict` | `make type` |
| NFR-10 Observabilidad | `logging_config.py` | revisión + `tests/unit/test_logging.py` |
| NFR-11 Testabilidad | dominio puro; dobles HTTP | suite completa |
| NFR-12 Portabilidad | `pathlib`, UTF-8 | pruebas en `tmp_path` |
| NFR-13 Rendimiento | vectorización con `numpy`/`pandas` | `tests/e2e/*::test_volume_smoke` |
| NFR-14 Seguridad | `config.py` (constantes del enunciado) | revisión + [ADR-0005](../adr/0005-configuration-and-secrets.md) |

## Cobertura inversa (código → requisito)

Regla de oro (ver [CLAUDE.md](../../CLAUDE.md) §1.2): **no debe existir módulo de
producción sin al menos una entrada en esta tabla.** Durante la implementación, cada
PR/commit referencia el/los `FR`/`NFR` que aborda, y esta matriz se actualiza en el
mismo cambio.

## Estado de cobertura

| Fase | FR cubiertos | NFR cubiertos |
|---|---|---|
| Especificación (actual) | 17/17 especificados | 14/14 especificados |
| Implementación | 0/17 implementados | — |
| Verificación | 0/17 verificados | — |
