# Documentación del proyecto

Este directorio contiene **toda la ingeniería de especificación** del proyecto,
siguiendo Spec Driven Development (SDD). El código se implementa *después* y
*a partir* de estos documentos.

## Orden de lectura sugerido

1. **[project-charter.md](project-charter.md)** — Por qué existe el proyecto,
   alcance, fuera de alcance, supuestos y criterios de éxito.
2. **[requirements/](requirements/)** — Requisitos funcionales (FR) y no
   funcionales (NFR), y la **[matriz de trazabilidad](requirements/requirements-traceability-matrix.md)**.
3. **[architecture/](architecture/)** — Visión arquitectónica, estructura de
   carpetas, modelo de componentes y flujo de datos.
4. **[adr/](adr/)** — Decisiones de arquitectura (Architecture Decision Records).
5. **[contracts/](contracts/)** — Contratos de datos y esquemas (incluye el CSV
   que alimenta a Pentaho).
6. **[specs/](specs/)** — Especificación detallada por componente, con criterios
   de aceptación.
7. **[testing/](testing/)** — Estrategia y niveles de prueba.
8. **[use-cases/](use-cases/)** — Casos de uso y escenarios.
9. **[runbook/](runbook/)** — Operación, ejecución y troubleshooting.
10. **[project-plan/](project-plan/)** — Fases, entregables y Definition of Done.

## Mapa de documentos

| Categoría | Documento | Propósito |
|---|---|---|
| Charter | [project-charter.md](project-charter.md) | Visión y alcance |
| Requisitos | [functional-requirements.md](requirements/functional-requirements.md) | FR-01…FR-17 |
| Requisitos | [non-functional-requirements.md](requirements/non-functional-requirements.md) | NFR-01…NFR-14 |
| Requisitos | [requirements-traceability-matrix.md](requirements/requirements-traceability-matrix.md) | Req → spec → código → prueba |
| Arquitectura | [architecture-overview.md](architecture/architecture-overview.md) | Capas, principios, diagramas C4 |
| Arquitectura | [project-structure.md](architecture/project-structure.md) | Estructura de carpetas |
| Arquitectura | [component-model.md](architecture/component-model.md) | Puertos, adaptadores, módulos |
| Arquitectura | [data-flow.md](architecture/data-flow.md) | Flujo de ejecución y de datos |
| Decisiones | [adr/](adr/) | 13 ADRs |
| Contratos | [data-contracts.md](contracts/data-contracts.md) | Esquemas JSON/JSONL/CSV/SQLite + normalización |
| Specs | [SPEC-001…005](specs/) | Cliente HTTP, generador, KPI, reporte, ETL PDI |
| Pruebas | [test-strategy.md](testing/test-strategy.md) | Pirámide de pruebas |
| Casos de uso | [use-cases.md](use-cases/use-cases.md) | UC-01…UC-04 |
| Operación | [operations-runbook.md](runbook/operations-runbook.md) | Cómo ejecutar y diagnosticar |
| Plan | [roadmap-and-phases.md](project-plan/roadmap-and-phases.md) | Fases y entregables |
| Sin lenguaje técnico | [no-tecnico/README.md](no-tecnico/README.md) | Traducción a lenguaje simple de la estructura y el código, para perfiles no técnicos |

## Convenciones de la documentación

- **Idioma:** español para prosa; inglés para identificadores de código.
- **Diagramas como código:** se usa Mermaid embebido en Markdown (versionable y
  renderizable en GitHub) en lugar de imágenes binarias.
- **Identificadores estables:** `FR-xx`, `NFR-xx`, `ADR-xxxx`, `SPEC-xxx`,
  `UC-xx`. Se referencian entre documentos y en el código (docstrings/commits).
- **Estado de cada documento:** indicado en su encabezado
  (`Borrador` / `Aprobado` / `Obsoleto`).
