# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[SemVer](https://semver.org/lang/es/).

## [No publicado]

### Añadido
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
- Fases 2–10: implementación (incluye ETL PDI), verificación y cierre documental (ver
  [roadmap-and-phases.md](docs/project-plan/roadmap-and-phases.md)).
