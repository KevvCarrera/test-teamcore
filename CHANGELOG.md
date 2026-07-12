# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[SemVer](https://semver.org/lang/es/).

## [No publicado]

### Añadido
- **Fase 5 — Aplicación y CLI de datos**: los dos primeros comandos del
  enunciado ya funcionan de punta a punta, tal como se piden literalmente.
  - `generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42`
    genera la bitácora sintética.
  - `calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv`
    calcula el CSV de KPIs.
  - Manejo de errores: `--n_registros <= 0` termina con código 2; archivo de
    entrada inexistente o sin ningún registro válido termina con código 1
    (sin generar un CSV vacío en silencio); fallo de escritura también
    código 1.
  - Golden files versionados en `tests/data/` (`bitacora_min.jsonl`,
    `kpi_expected.csv`) para las pruebas de contrato.
  - 13 pruebas e2e nuevas; cobertura global 95 %.
  - Verificado manualmente que ambos comandos, ejecutados tal cual los pide
    el enunciado, terminan con código de salida 0.

- **Fase 4 — Infraestructura (adaptadores)**: implementación concreta de los
  puertos definidos en la arquitectura, con pruebas de integración (E/S real
  sobre directorios temporales, HTTP simulado sin red).
  - `application/ports.py`: los 6 puertos (`Protocol`) que conectan
    `application` con `infrastructure`.
  - `infrastructure/io/jsonl_repository.py`: lectura/escritura de
    `datos.jsonl`, en streaming, con descarte de líneas corruptas vía
    `WARNING` (FR-09, FR-11).
  - `infrastructure/io/csv_repository.py`: lectura/escritura del CSV de KPIs
    conforme al contrato (FR-10, FR-13).
  - `infrastructure/io/artifact_writer.py`: escritura de `datos.json`,
    `datos.xml` y `titulo.html` (FR-04, FR-05, FR-06).
  - `infrastructure/http/client.py`: `RequestsHttpClient` con sesión
    compartida, reintentos con backoff exponencial y manejo configurable
    del `403` (FR-01…FR-08).
  - `infrastructure/reporting/charts.py` y `html_report.py`:
    `MatplotlibChartRenderer` (gráficos PNG, backend `Agg`) y
    `HtmlReportRenderer` (HTML autocontenido, con alerta por umbral de p90 y
    escape de valores) (FR-13).
  - `domain/kpi.py`: se añadió `compute_global_metrics` (métricas globales
    del reporte), resolviendo una discrepancia menor entre `SPEC-004` (que
    sugería un `domain/report.py` separado) y la estructura ya aprobada.
  - 41 pruebas de integración nuevas; cobertura global 86 %.

- **Fase 3 — Dominio (TDD)**: lógica de negocio pura, sin red ni E/S, con
  cobertura de pruebas del 100 %.
  - `domain/models.py`: `BitacoraRecord`, `KpiRow`, `GlobalMetrics`.
  - `domain/endpoints.py`: `normalize_endpoint` — normalización de rutas para
    agrupar KPIs (FR-10), documentada con la regla y ejemplos (NFR-05).
  - `domain/kpi.py`: `percentile_90` (vía `numpy.percentile`, documentado) y
    `aggregate` — conteos por rango de estado, promedio y p90 por
    `(date_utc, endpoint_base)`, con orden determinista.
  - `domain/generation.py`: `generate_records` — genera la bitácora sintética
    con todas las reglas del enunciado (catálogo de endpoints, status por
    endpoint, latencia 50–800 ms, ~5 % de errores de parseo), determinista por
    `seed` + `ref_utc`.
  - `domain/errors.py`: jerarquía completa de excepciones (`TeamcoreError` y
    subtipos) para el manejo de errores del resto del sistema.
  - 44 pruebas unitarias nuevas (normalización, percentil, agregación,
    generación, jerarquía de errores); `make check` en verde.

- **Fase 2 — Scaffolding del paquete**: árbol completo `src/teamcore_http_kpi/`
  (capas `domain`, `application`, `infrastructure`, `cli`) con módulos tipados
  vacíos, listos para recibir la lógica de negocio en las fases siguientes.
  - `config.py`: constantes tipadas (`Settings`, `FormData`) con los valores
    fijos del enunciado (URL base, credenciales de prueba, datos de formulario).
  - `logging_config.py`: logging estructurado a `stderr` (`setup_logging`),
    sin `print()`, con soporte de formato `text`/`json`.
  - Shims raíz (`cliente_http.py`, `generar_datos.py`, `calcular_kpi.py`,
    `generar_reporte.py`) que delegan en el paquete instalado.
  - Prueba de arquitectura que verifica que `domain` no importa librerías de
    E/S, red o CLI (`requests`, `pandas`, `matplotlib`, `bs4`, `lxml`, `argparse`).
  - Entorno virtual `.venv` e instalación editable con extras de desarrollo.
  - `make check` (ruff + mypy --strict + pytest) en verde sobre el esqueleto.

- **Fase 1 — Especificación (SDD) completa**, cubriendo las 4 partes del enunciado:
  - `CLAUDE.md` con reglas de trabajo y política estricta de Git.
  - Ingeniería de requisitos: FR-01…FR-17, NFR-01…NFR-14 y matriz de trazabilidad.
  - Arquitectura por capas pragmática: visión, estructura, modelo de componentes
    (puertos/adaptadores) y flujo de datos, con diagramas Mermaid.
  - 13 ADRs documentando las decisiones clave (incluye PDI en alcance, ADR-0013).
  - Contratos de datos (JSONL, CSV de KPIs, tablas SQLite, artefactos HTTP) y regla de
    normalización de endpoints.
  - Especificaciones por componente SPEC-001…SPEC-005 con criterios de aceptación.
  - Estrategia de pruebas, casos de uso, runbook y plan de fases.
  - Scaffolding de proyecto: `pyproject.toml`, `Makefile`, `.gitignore` ampliado.

### Cambiado
- Revisados los comentarios y docstrings de todo `src/` para que se lean como
  una explicación natural en vez de una plantilla repetida (menos estructura
  mecánica tipo `Args:`/`Returns:` en funciones simples, sin repetir la misma
  frase de "pendiente de implementación" en cada stub, y sin etiquetar cada
  línea con `FR-xx`/`NFR-xx`). No cambia ninguna lógica ni comportamiento.

### Corregido
- Acotado el rango de `numpy` en `pyproject.toml` a `>=1.26,<2.3`: a partir de
  `numpy==2.3` los stubs usan sintaxis PEP 695, incompatible con
  `mypy --strict` bajo `python_version = "3.11"` (NFR-01).

### Ceñido al enunciado (sin invenciones)
- Las CLIs exponen **solo** los parámetros del documento. Se eliminaron los flags/
  rutas inventados (`--ref-utc`, `--on-error`, `--salida`/subcarpeta del cliente
  HTTP); el determinismo temporal y la política de líneas corruptas se resuelven sin
  flags nuevos. Artefactos de la Parte 0 en `out/` con los nombres exactos.
- Se eliminó el ADR de "Pentaho fuera de alcance" (ya no aplica); la decisión vigente
  es [ADR-0013 · PDI dentro del alcance](docs/adr/0013-pentaho-pdi-in-scope.md).
- Se eliminó la configuración por entorno (`.env`/variables `TEAMCORE_`): la
  configuración pasa a ser constantes tipadas en `config.py` con los valores del
  enunciado ([ADR-0005](docs/adr/0005-configuration-and-secrets.md)).

### Límite conocido
- Los `.ktr`/`.kjb` no se ejecutan/validan en este entorno (sin Spoon/Kitchen); la
  validación funcional de PDI la realiza el usuario en su instalación.

### Pendiente
- Fases 3–10: dominio, infraestructura, CLIs, cliente HTTP, reporte, ETL PDI,
  verificación y cierre documental (ver
  [roadmap-and-phases.md](docs/project-plan/roadmap-and-phases.md)).
