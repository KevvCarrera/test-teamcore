# Estructura del Proyecto

> Estado: Aprobado · Cambiar esta estructura requiere un **nuevo ADR**
> (ver [CLAUDE.md](../../CLAUDE.md) §2.6).

Layout `src/`-based (evita imports accidentales del paquete sin instalar y fuerza
un empaquetado correcto).

```
test-teamcore/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── Makefile
├── .gitignore
│
├── spec/                                # Documento fuente (test técnico)
│   └── Test Tecnico.md
│
├── docs/                                # Ingeniería de especificación (SDD)
│   └── ...                              # (ver docs/README.md)
│
├── src/
│   └── teamcore_http_kpi/               # Paquete instalable
│       ├── __init__.py
│       ├── config.py                    # Constantes tipadas (valores del enunciado)
│       ├── logging_config.py            # Configuración de logging estructurado
│       │
│       ├── domain/                      # Lógica pura (sin E/S, sin red)
│       │   ├── __init__.py
│       │   ├── models.py                # BitacoraRecord, KpiRow, GlobalMetrics, FormData
│       │   ├── endpoints.py             # Catálogo + normalización de endpoints
│       │   ├── kpi.py                   # Agregados y percentil 90 (numpy)
│       │   ├── generation.py            # Reglas de generación de la bitácora
│       │   └── errors.py                # Excepciones de dominio
│       │
│       ├── application/                 # Casos de uso / orquestación
│       │   ├── __init__.py
│       │   ├── ports.py                 # Interfaces: HttpPort, repositorios, ChartRenderer
│       │   ├── http_scenarios.py        # Orquesta los 6 escenarios (Parte 0)
│       │   ├── generate_data.py         # Caso de uso FR-09
│       │   ├── compute_kpi.py           # Caso de uso FR-10
│       │   └── build_report.py          # Caso de uso FR-13
│       │
│       ├── infrastructure/              # Adaptadores concretos
│       │   ├── __init__.py
│       │   ├── http/
│       │   │   ├── client.py            # HttpClient sobre requests (sesión, retries, auth)
│       │   │   └── tasks.py             # Implementa los 6 escenarios httpbin
│       │   ├── io/
│       │   │   ├── jsonl_repository.py  # Lectura/escritura de datos.jsonl
│       │   │   ├── csv_repository.py    # Lectura/escritura del CSV de KPIs
│       │   │   └── artifact_writer.py   # datos.json, datos.xml, titulo.html
│       │   └── reporting/
│       │       ├── charts.py            # Gráficos matplotlib → PNG base64
│       │       └── html_report.py       # Ensamblado del HTML
│       │
│       └── cli/                         # Puntos de entrada (argparse)
│           ├── __init__.py
│           ├── _common.py               # utilidades compartidas de CLI
│           ├── cliente_http.py          # main() Parte 0
│           ├── generar_datos.py         # main() FR-09
│           ├── calcular_kpi.py          # main() FR-10
│           └── generar_reporte.py       # main() FR-13
│
├── cliente_http.py                      # Shim raíz → cli.cliente_http:main
├── generar_datos.py                     # Shim raíz → cli.generar_datos:main
├── calcular_kpi.py                      # Shim raíz → cli.calcular_kpi:main
├── generar_reporte.py                   # Shim raíz → cli.generar_reporte:main
│
├── tests/
│   ├── conftest.py                      # fixtures compartidas (tmp, semillas, dobles)
│   ├── data/                            # datasets de referencia (golden files)
│   ├── unit/                            # dominio puro
│   ├── integration/                     # adaptadores (E/S, HTTP con dobles)
│   └── e2e/                             # CLIs de extremo a extremo
│
├── etl_pdi/                             # ETL Pentaho/PDI (Parte 2 · SPEC-005)
│   ├── t_load_kpi.ktr                   # transformación (XML de PDI)
│   ├── j_daily_kpi.kjb                  # job (XML de PDI)
│   ├── sql/
│   │   └── ddl.sql                      # DDL de stg_* y fct_*
│   ├── config/
│   │   └── kettle.properties.example    # conexión/rutas (sin secretos)
│   ├── db/                              # SQLite generado (git-ignored)
│   └── README.md                        # abrir en Spoon / ejecutar con Kitchen
│
└── out/                                 # artefactos generados (git-ignored)
    ├── datos.json                       # Parte 0 (/get)
    ├── datos.xml                        # Parte 0 (/xml)
    ├── titulo.html                      # Parte 0 (/html)
    ├── datos.jsonl                      # Parte 1.1
    ├── kpi_por_endpoint_dia.csv         # Parte 1.2
    └── report/
        └── kpi_diario.html              # Parte 3
```

## Justificación de decisiones estructurales

- **`src/` layout:** evita que las pruebas importen el paquete desde el árbol de
  fuentes sin instalar; alinea con empaquetado moderno. (Ver
  [ADR-0002](../adr/0002-runtime-python-and-packaging.md).)
- **Shims raíz (`generar_datos.py`, …):** el enunciado ejecuta literalmente
  `python generar_datos.py ...`. Los shims de una línea delegan en el paquete y así
  se honra el comando exacto sin duplicar lógica. (Ver
  [ADR-0008](../adr/0008-cli-design-and-parameters.md).)
- **Artefactos del cliente HTTP en `out/`:** con los nombres exactos del enunciado
  (`datos.json`, `datos.xml`, `titulo.html`). No se inventan subcarpetas ni flags de
  ruta. `datos.json` (Parte 0) y `datos.jsonl` (Parte 1) conviven sin conflicto por
  su extensión distinta.
- **`etl_pdi/` como entregable separado:** los ficheros de PDI no forman parte del
  paquete Python; usan otro toolchain (Kettle/JVM). Ver
  [SPEC-005](../specs/SPEC-005-etl-pdi.md) y [ADR-0013](../adr/0013-pentaho-pdi-in-scope.md).
- **`tests/data/` (golden files):** datasets pequeños y deterministas para pruebas
  de contrato y de KPIs.

## Convenciones de nombres

| Elemento | Convención | Ejemplo |
|---|---|---|
| Módulos/paquetes | `snake_case` | `html_report.py` |
| Clases | `PascalCase` | `HttpClient`, `KpiRow` |
| Funciones/variables | `snake_case` | `normalize_endpoint` |
| Constantes | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT_SECONDS` |
| Tests | `test_<unidad>_<escenario>` | `test_normalize_status_endpoint` |

## Convención de idioma

- **Documentación/prosa/logs orientados al usuario:** español.
- **Identificadores de código y nombres de test:** inglés.
- **Docstrings de reglas de negocio:** español (el enunciado pide comentar en
  español cómo se normaliza el endpoint y cómo se calcula el p90).
