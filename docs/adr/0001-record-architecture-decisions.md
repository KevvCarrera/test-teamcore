# ADR-0001 · Registrar decisiones de arquitectura

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El proyecto se desarrolla con Spec Driven Development y debe ser mantenible por un
equipo senior. Las decisiones técnicas relevantes necesitan quedar documentadas con
su contexto y consecuencias para que sean auditables y reversibles con criterio.

## Decisión

Usar **Architecture Decision Records (ADR)** en `docs/adr/`, con el formato de
Michael Nygard: *Contexto → Decisión → Consecuencias → Alternativas*. Los ADR son
inmutables; un cambio de rumbo se registra en un ADR nuevo que supersede al previo.
Todo cambio estructural o de dependencias exige un ADR (ver [CLAUDE.md](../../CLAUDE.md)).

## Consecuencias

- (+) Trazabilidad de *por qué* el sistema es como es.
- (+) Onboarding más rápido; discusiones no se repiten.
- (−) Disciplina adicional para escribir el ADR antes de decidir.

## Alternativas consideradas

- **No documentar decisiones:** rechazado; incompatible con el objetivo de calidad.
- **Wiki externa:** rechazado; se prefiere documentación versionada junto al código.
