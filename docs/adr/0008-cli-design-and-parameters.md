# ADR-0008 · Diseño de CLI y parámetros

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El enunciado ejecuta comandos literales, p. ej.
`python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42` y
`python generar_reporte.py --input ... --output ... --umbral_p90 300`. Los nombres de
parámetros y de scripts son **criterio de aceptación**.

## Decisión

- **Parámetros exactos, sin renombrar:** `--n_registros`, `--salida`, `--seed`
  (generador); `--input`, `--output` (KPI y reporte); `--umbral_p90` (reporte). Para
  `calcular_kpi.py`, que el enunciado deja abierto, se usan `--input`/`--output` por
  consistencia con el reporte.
- **Scripts ejecutables por nombre:** shims raíz (`generar_datos.py`, etc.) de una
  línea que delegan en `teamcore_http_kpi.cli.*:main`. Además, `console_scripts` en
  `pyproject.toml` para instalación (`generar-datos`).
- **Librería:** `argparse` de la stdlib (sin dependencias extra).
- **Sin parámetros inventados.** Las CLIs exponen **únicamente** los flags que el
  enunciado define. Necesidades transversales (nivel de log, ancla temporal para
  pruebas, política ante líneas corruptas) se resuelven mediante **constantes en
  `config.py`** o a **nivel de función de dominio** (inyección en pruebas), nunca
  añadiendo flags que el enunciado no pide.
- **UX de CLI:** `-h/--help` con descripciones en español; validación temprana;
  códigos de salida definidos en [ADR-0007](0007-error-handling-retries-idempotency.md).

## Consecuencias

- (+) Compatibilidad literal con los comandos del enunciado.
- (+) Extensible sin romper la interfaz evaluada.
- (−) Doble punto de entrada (shim raíz + console_script); costo mínimo, se
  documenta.

## Alternativas consideradas

- **Solo `console_scripts`:** rompería `python generar_datos.py ...` literal.
- **`click`/`typer`:** ergonómicos, pero fuera de la frontera de dependencias.
