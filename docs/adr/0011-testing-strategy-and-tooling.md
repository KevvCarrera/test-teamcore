# ADR-0011 · Estrategia y tooling de pruebas

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El código debe ser testeable sin red, determinista y verificable en CI. El enunciado
restringe las librerías de *runtime*, pero el tooling de *desarrollo* es una
categoría distinta (ver [ADR-0012](0012-dependency-boundary-allowed-libraries.md)).

## Decisión

- **`pytest`** como runner; **`pytest-cov`** para cobertura.
- **`responses`** para simular httpbin sin red (dobles a nivel de `requests`).
- **Marcadores:** `unit`, `integration`, `e2e`, `network`. Por defecto se ejecuta
  `-m "not network"` (sin red).
- **Pirámide:** mayoría de pruebas unitarias de dominio (rápidas y puras); pocas
  e2e sobre las CLIs. Detalle en [test-strategy.md](../testing/test-strategy.md).
- **Determinismo:** semillas fijas, tiempo de referencia inyectado a nivel de
  función (no como flag de CLI), `tmp_path` para E/S. Nada depende del reloj ni del
  orden.
- **Golden files** en `tests/data/` para pruebas de contrato (JSONL/CSV/HTML).
- **Calidad estática como parte del "test":** `ruff` + `mypy --strict` en `make check`.

## Consecuencias

- (+) Suite rápida, determinista y ejecutable offline.
- (+) Verifica contratos, no solo funciones aisladas.
- (−) `responses` es dependencia de desarrollo adicional; justificada y aislada en
  el extra `[dev]`.

## Alternativas consideradas

- **`unittest`:** válido, pero `pytest` es más conciso y potente (fixtures/markers).
- **Pruebas contra httpbin real siempre:** rechazado; introduce flakiness y
  dependencia de red en CI. Se conservan como `@network` opcionales.
