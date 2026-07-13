# ADR-0003 · Arquitectura por capas pragmática

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El proyecto exige aplicar Clean Architecture *y* KISS/YAGNI (ver `CLAUDE.md`,
sección 3). Ambos objetivos están en tensión: una Clean Architecture "de manual"
(entidades, casos de uso, gateways, presenters, DTOs en cada frontera, contenedor
de DI) sería sobre-ingeniería para tres scripts CLI y un cliente HTTP. Pero un
único módulo monolítico dañaría la
testabilidad y la separación de responsabilidades.

## Decisión

Adoptar una **arquitectura por capas pragmática** inspirada en Clean/Hexagonal,
tomando solo lo que aporta valor aquí:

1. **`domain`** puro (reglas de negocio, modelos) — sin E/S, sin red, sin CLI.
2. **`application`** con casos de uso que orquestan **puertos** (`Protocol`).
3. **`infrastructure`** con adaptadores concretos de los puertos.
4. **`cli`** como *composition root* (inyección manual de dependencias).

Se **omite** deliberadamente: contenedor de DI, DTOs redundantes entre capas,
presenters formales, y puertos para operaciones que no cruzan una frontera de E/S.

**Invariante:** la Regla de Dependencia (nada apunta hacia afuera del dominio) se
mantiene y se puede verificar con una prueba de arquitectura.

## Consecuencias

- (+) Dominio testeable sin dobles pesados; SRP y separación claras.
- (+) Extensible (nuevos adaptadores) sin tocar el núcleo.
- (+) Evita ceremonia innecesaria (KISS/YAGNI).
- (−) Requiere criterio para decidir "qué merece un puerto"; se documenta la guía
  en [component-model.md](../architecture/component-model.md).

## Alternativas consideradas

- **Clean Architecture completa:** rechazada por sobre-ingeniería para el tamaño.
- **Scripts planos sin capas:** rechazado; comprometería testabilidad y
  mantenibilidad, ambos objetivos prioritarios del proyecto (regla 9 de
  `CLAUDE.md`).
