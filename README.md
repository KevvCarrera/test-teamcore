# Cliente HTTP Automatizado · Procesamiento de KPIs · Reporte HTML

Solución en Python 3 que (1) interactúa con distintos endpoints de
[httpbin.org](https://httpbin.org) simulando escenarios de scraping/consumo de
APIs, (2) genera una bitácora sintética de llamadas y calcula KPIs diarios, y
(3) produce un reporte HTML con métricas y gráficos.

Desarrollado con **Spec Driven Development (SDD)**: cada línea de código es
trazable a un requerimiento documentado.

> **Estado actual:** 📐 *Fase de especificación completada.* La implementación se
> ejecuta como fase posterior, gobernada por las specs de este repositorio.
> Ver [roadmap-and-phases.md](docs/project-plan/roadmap-and-phases.md).

---

## Tabla de contenidos

- [Alcance](#alcance)
- [Arquitectura en 30 segundos](#arquitectura-en-30-segundos)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Puesta en marcha](#puesta-en-marcha)
- [Uso (CLIs)](#uso-clis)
- [Documentación](#documentación)
- [Calidad y pruebas](#calidad-y-pruebas)

## Alcance

| Módulo | Entrega | Estado |
|---|---|---|
| **Cliente HTTP** (6 escenarios httpbin) | `datos.json`, `datos.xml`, `titulo.html` | En alcance |
| **Generador de datos** (`generar_datos.py`) | `out/datos.jsonl` (500 registros) | En alcance |
| **Cálculo de KPIs** (`calcular_kpi.py`) | `out/kpi_por_endpoint_dia.csv` | En alcance |
| **ETL Pentaho/PDI** (`.ktr`, `.kjb`) | SQLite `stg_*` + `fct_*` | En alcance |
| **Reporte HTML** (`generar_reporte.py`) | `out/report/kpi_diario.html` | En alcance |

El CSV de KPIs es el **contrato de interfaz** que alimenta tanto al reporte como al
ETL de Pentaho; su esquema está congelado en
[data-contracts.md](docs/contracts/data-contracts.md). Los ficheros `.ktr`/`.kjb` se
autoran fielmente al formato de PDI; su ejecución/validación final se realiza en una
instalación de PDI (ver [ADR-0013](docs/adr/0013-pentaho-pdi-in-scope.md)).

## Arquitectura en 30 segundos

Arquitectura por capas (dependencias hacia el dominio):

```
cli/  ──►  application/  ──►  domain/  ◄──  infrastructure/
(argparse)  (casos de uso)   (lógica pura)   (HTTP, ficheros, gráficos)
```

- **`domain`**: entidades, normalización de endpoints, KPIs y percentiles. Sin E/S.
- **`application`**: orquesta casos de uso (generar datos, calcular KPI, reporte).
- **`infrastructure`**: adaptadores de red (`requests`), ficheros y `matplotlib`.
- **`cli`**: puntos de entrada que respetan los parámetros exactos del enunciado.

Detalle y diagramas en
[architecture-overview.md](docs/architecture/architecture-overview.md).

## Estructura del repositorio

```
.
├── CLAUDE.md                     # Reglas del agente / del proyecto
├── README.md
├── pyproject.toml                # Empaquetado, dependencias y config de tooling
├── Makefile                      # Atajos: setup, lint, type, test, run-*
├── docs/                         # Toda la ingeniería de especificaciones (SDD)
│   ├── project-charter.md
│   ├── requirements/             # FR/NFR + matriz de trazabilidad
│   ├── architecture/             # visión, estructura, flujo de datos, componentes
│   ├── adr/                      # decisiones de arquitectura (ADR)
│   ├── contracts/                # contratos de datos / esquemas
│   ├── specs/                    # especificaciones por componente
│   ├── testing/                  # estrategia de pruebas
│   ├── use-cases/                # casos de uso
│   ├── runbook/                  # operación y troubleshooting
│   └── project-plan/             # fases, entregables y Definition of Done
├── src/teamcore_http_kpi/        # (código — fase de implementación)
├── tests/                        # (pruebas — fase de implementación)
├── etl_pdi/                      # ETL Pentaho/PDI: .ktr, .kjb, sql/, config/
└── out/                          # artefactos generados (ignorado por git)
```

## Puesta en marcha

Requisitos: **Python 3.11+**.

```bash
# Crear entorno e instalar (modo editable con extras de desarrollo)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

> La configuración (URL base, credenciales de prueba, datos del formulario) vive como
> constantes en `config.py` con los valores del enunciado; no requiere `.env`.

## Uso (CLIs)

> Los comandos respetan literalmente los parámetros del enunciado. Se documentan
> aquí como contrato; su implementación pertenece a la fase de desarrollo.

```bash
# (Parte 0) Cliente HTTP: ejecuta los 6 escenarios y genera datos.json/datos.xml/titulo.html
python cliente_http.py

# (1.1) Generar bitácora sintética reproducible
python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42

# (1.2) Calcular KPIs diarios por endpoint
python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv

# (3) Generar reporte HTML con umbral de alerta para p90
python generar_reporte.py --input out/kpi_por_endpoint_dia.csv \
    --output out/report/kpi_diario.html --umbral_p90 300
```

## Documentación

Punto de entrada: **[docs/README.md](docs/README.md)** (orden de lectura sugerido).
Documentos clave:

- 📋 [Project Charter](docs/project-charter.md) — visión, alcance y fuera de alcance.
- ✅ [Requisitos + Trazabilidad](docs/requirements/requirements-traceability-matrix.md)
- 🏛️ [Arquitectura](docs/architecture/architecture-overview.md) y [ADRs](docs/adr/)
- 🔌 [Contratos de datos](docs/contracts/data-contracts.md)
- 🧩 [Especificaciones](docs/specs/) por componente
- 🧪 [Estrategia de pruebas](docs/testing/test-strategy.md)
- 🛠️ [Runbook de operación](docs/runbook/operations-runbook.md)

## Calidad y pruebas

```bash
make lint     # ruff (estilo + errores)
make type     # mypy --strict
make test     # pytest (sin red por defecto)
make check    # lint + type + test
```

Convenciones, principios (SOLID/Clean Code/DRY/KISS/YAGNI) y política de Git en
[CLAUDE.md](CLAUDE.md).
