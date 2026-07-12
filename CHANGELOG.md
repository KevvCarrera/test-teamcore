# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[SemVer](https://semver.org/lang/es/).

## [No publicado]

### Añadido
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
