# ADR-0006 · Estrategia de logging

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El enunciado valora el manejo de errores y la claridad. Necesitamos diagnóstico
observable sin ensuciar la salida de datos ni filtrar secretos, y sin `print()`.

## Decisión

- Usar el módulo estándar **`logging`**, configurado una vez en `logging_config.py`.
- **Separación de flujos:** logs a **`stderr`**; los **datos/artefactos** van a
  ficheros o `stdout` según el script. Así se puede *pipe* de datos sin ruido.
- **Nivel y formato configurables por parámetro** en el *composition root*:
  `setup_logging(level=INFO, fmt="text")`. Valores por defecto sensatos (`INFO`,
  `text`); el formato `json` queda disponible como opción. **Sin variables de
  entorno** (coherente con [ADR-0005](0005-configuration-and-secrets.md)).
- **Loggers por módulo** (`logging.getLogger(__name__)`), sin configurar el root en
  import (solo en el *composition root*).
- **Nunca** se registran credenciales ni cuerpos con datos sensibles.

## Consecuencias

- (+) Diagnóstico consistente y desacoplado de los datos.
- (+) Sin dependencias externas.
- (−) El formato `json` propio es básico (suficiente para el alcance).

## Alternativas consideradas

- **`print()`:** rechazado; no tiene niveles ni destino configurable.
- **`structlog`/`loguru`:** potentes, pero fuera de la frontera de dependencias.
