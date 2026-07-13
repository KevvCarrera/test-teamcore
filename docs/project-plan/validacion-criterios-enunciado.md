# Validación contra los criterios del enunciado

> Auditoría (2026-07-12, actualizada el mismo día tras corregir los 2
> hallazgos de la primera pasada) de las "Indicaciones de desarrollo" y los
> "Criterios de Evaluación" del documento fuente
> ([spec/Test Tecnico.md](../../spec/Test%20Tecnico.md)), contra el estado real
> del código en este repositorio. No reemplaza a la
> [RTM](../requirements/requirements-traceability-matrix.md) (que trazabiliza
> FR/NFR); esto es una revisión dirigida a esas dos listas específicas.

## Indicaciones de desarrollo

| Indicación | Evidencia | Veredicto |
|---|---|---|
| Bibliotecas estándar (`json`, `datetime`, `csv`) y `numpy` para calcular | `json`: [jsonl_repository.py](../../src/teamcore_http_kpi/infrastructure/io/jsonl_repository.py), [artifact_writer.py](../../src/teamcore_http_kpi/infrastructure/io/artifact_writer.py). `csv`: [csv_repository.py](../../src/teamcore_http_kpi/infrastructure/io/csv_repository.py) (columna de escritura). `datetime`: [generation.py](../../src/teamcore_http_kpi/domain/generation.py), [kpi.py](../../src/teamcore_http_kpi/domain/kpi.py), [models.py](../../src/teamcore_http_kpi/domain/models.py). `numpy`: `percentile_90` en [kpi.py](../../src/teamcore_http_kpi/domain/kpi.py) (vía `np.percentile`) y generación de latencias en [generation.py](../../src/teamcore_http_kpi/domain/generation.py) (`np.random.default_rng`) | ✅ Cumple |
| "Incluso `polars` u otras que conozcas" (sección 1.3, sobre `generar_datos.py`/`calcular_kpi.py`) | No se usa — es una sugerencia opcional ("incluso"), no obligatoria, y los volúmenes del enunciado (hasta ~10⁵ filas) se procesan en segundos con estructuras estándar + `numpy` (ver `tests/e2e/test_volume_smoke.py`) | ✅ Cumple (opcional, deliberadamente no ejercida — YAGNI) |
| **"Utiliza pandas para cargar el CSV" (sección 3.1) / "matplotlib y pandas son suficientes" (sección 3.3), para `generar_reporte.py`** | `CsvKpiRepository.read()` en [csv_repository.py](../../src/teamcore_http_kpi/infrastructure/io/csv_repository.py) usa `pandas.read_csv` para cargar `kpi_por_endpoint_dia.csv` antes de convertirlo a `KpiRow` | ✅ Cumple — **corregido** en esta revisión (ver Hallazgos, #1) |
| Estructurar el código en funciones pequeñas y testeables | Función más larga del proyecto: 23 líneas (`JsonlBitacoraRepository.read`); la mayoría son de 5-15 líneas. Cada función pública de `domain/` tiene su contraparte de prueba unitaria sin E/S ni red | ✅ Cumple |
| Documentar cómo se normaliza el endpoint y cómo se calcula el p90 | Docstrings dedicados en [domain/endpoints.py](../../src/teamcore_http_kpi/domain/endpoints.py) (`normalize_endpoint`) y [domain/kpi.py](../../src/teamcore_http_kpi/domain/kpi.py) (`percentile_90`), con el razonamiento explicado, no solo el "qué"; la misma aproximación de p90-ponderado se documentó también donde se repite en el reporte ([html_report.py](../../src/teamcore_http_kpi/infrastructure/reporting/html_report.py)) | ✅ Cumple |
| Manejo de errores: archivos inexistentes, JSON mal formado, etc. | `InputFileNotFoundError` (archivo ausente), `MalformedRecordError` (línea JSONL inválida — ver Hallazgos, #2) capturado por línea en `JsonlBitacoraRepository.read` (se avisa con `WARNING` y se sigue, no se aborta por una línea corrupta), `DataInputError` para CSV con columnas faltantes, vacío o valores inválidos, sin `except` desnudo en ningún módulo | ✅ Cumple |
| Ejemplos de ejecución en `README.md` | Los 4 comandos documentados con su salida real (se ejecutaron de verdad, incluido `cliente_http.py` contra `httpbin.org` en vivo), más una guía de inicio completa desde `git clone` — ver [README.md](../../README.md) | ✅ Cumple |

## Criterios de Evaluación

| Criterio | Evidencia | Veredicto |
|---|---|---|
| Correcta implementación de cada tarea descrita | Las 4 partes del enunciado (cliente HTTP, generación de datos, cálculo de KPIs, reporte HTML) más el ETL de Pentaho/PDI están implementadas y verificadas — ver [TODO.md](../../TODO.md) y la [RTM](../requirements/requirements-traceability-matrix.md) (17/17 FR, 14/14 NFR verificados) | ✅ Cumple |
| Manejo adecuado de errores y excepciones | Jerarquía propia en [domain/errors.py](../../src/teamcore_http_kpi/domain/errors.py) (`TeamcoreError` y subtipos), *fail fast* en configuración inválida (`--n_registros <= 0` → exit 2), cada CLI mapea sus excepciones a un código de salida distinto, todos los tipos de error definidos están además realmente en uso | ✅ Cumple |
| Claridad y organización del código | Arquitectura por capas (`domain → application → infrastructure ← cli`), verificada automáticamente por [test_architecture_layering.py](../../tests/unit/test_architecture_layering.py) (el dominio no importa nada de E/S/red/CLI) | ✅ Cumple |
| Uso apropiado de las bibliotecas permitidas | Sin dependencias fuera de la frontera declarada en [ADR-0012](../adr/0012-dependency-boundary-allowed-libraries.md); todas las dependencias declaradas están efectivamente en uso (incluida `pandas`, tras el fix); `ruff`/`mypy --strict` en verde | ✅ Cumple |
| Documentación y comentarios que expliquen la lógica implementada | Docstrings explicando el *por qué*, no solo el *qué*, en los módulos de dominio e infraestructura; ADRs para cada decisión de diseño relevante; [guia-de-pruebas-por-paso.md](../testing/guia-de-pruebas-por-paso.md) nueva, mapeada 1:1 al enunciado; `docs/no-tecnico/` como capa adicional en lenguaje simple | ✅ Cumple |
| Entrega de archivos con el formato especificado | `datos.json`, `datos.xml`, `titulo.html`, `datos.jsonl`, `kpi_por_endpoint_dia.csv`, `kpi_diario.html` — los seis se generaron con esos nombres exactos en la corrida de verificación | ✅ Cumple |

## Hallazgos de la primera pasada — ambos corregidos

1. **`CsvKpiRepository.read()` no usaba `pandas`**, pese a que la sección 3.1
   del enunciado lo pide explícitamente ("Utiliza pandas para cargar el CSV")
   para `generar_reporte.py`, y la 3.3 lo reafirma ("matplotlib y pandas son
   suficientes"). La implementación original usaba `csv.DictReader` — funcionalmente
   correcta, pero no la biblioteca que el enunciado nombra para ese paso en
   particular. **Corregido:** `read()` ahora usa `pandas.read_csv(..., dtype=str,
   keep_default_na=False)` para cargar el CSV completo, preservando el mismo
   contrato de errores (`InputFileNotFoundError`, `DataInputError` por columnas
   faltantes/CSV vacío/valores inválidos). Se agregó
   `test_read_raises_data_input_error_when_file_is_truly_empty` para cubrir el
   nuevo camino de error que introduce `pandas.errors.EmptyDataError`.
2. **`MalformedRecordError` estaba definida, documentada y probada, pero nunca
   se lanzaba en producción** — `JsonlBitacoraRepository.read` capturaba
   excepciones genéricas de `json`/Python y registraba el `WARNING` a mano, sin
   pasar por el tipo de dominio pensado para esto. **Corregido:** ahora se
   construye un `MalformedRecordError(line_number, motivo)` real y se registra
   su mensaje ya formateado; el comportamiento observable (se avisa y se sigue
   con la siguiente línea) no cambió, solo la claridad interna. Se eliminó
   también, por quedar inalcanzable tras este cambio, el chequeo redundante de
   columnas faltantes dentro de `csv_repository._from_payload` (esa validación
   ya la hace `read()` antes de llegar ahí).

Ambos fixes están cubiertos por la suite existente/ampliada: **181 pruebas
passed**, `ruff`/`mypy --strict` en verde, cobertura global 99 %.

## Conclusión

El proyecto cumple todas las indicaciones de desarrollo y todos los criterios
de evaluación listados. Los 2 hallazgos de la revisión inicial (uso de
`pandas` para el reporte y conexión de `MalformedRecordError`) ya están
corregidos y verificados con pruebas.
