# ADR-0002 · Runtime Python y empaquetado

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El enunciado exige Python 3. Necesitamos fijar una versión mínima, un layout de
paquete y un backend de build que favorezcan tipado moderno, empaquetado limpio y
reproducibilidad.

## Decisión

- **Python 3.11+** como versión mínima (`requires-python = ">=3.11"`). Motivos:
  `datetime.UTC`, mejores mensajes de error, `tomllib`, tipado más expresivo
  (`X | Y`), rendimiento mejorado.
- **Layout `src/`** con el paquete `teamcore_http_kpi`. Evita imports accidentales
  del árbol de fuentes y fuerza a probar el paquete *instalado*.
- **Build backend:** `setuptools` vía `pyproject.toml` (estándar PEP 517/621), sin
  añadir herramientas pesadas. `pip install -e ".[dev]"` para desarrollo.
- **Gestión de entorno:** `venv` + `pip` (ubicuo). `uv` es opcional y compatible,
  pero no se impone (KISS).

## Consecuencias

- (+) Empaquetado estándar, instalable y testeable como en producción.
- (+) Aprovecha características modernas del lenguaje.
- (−) Excluye Python ≤ 3.10 (aceptable para un entorno de evaluación controlado).

## Alternativas consideradas

- **Poetry / PDM:** válidas, pero añaden una herramienta más; `setuptools`+`pip`
  cubre las necesidades sin fricción.
- **Layout plano (sin `src/`):** rechazado por el riesgo de imports implícitos y
  pruebas que no reflejan el paquete instalado.
