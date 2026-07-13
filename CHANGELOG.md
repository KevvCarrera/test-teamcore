# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[SemVer](https://semver.org/lang/es/).

## [No publicado]

### Añadido
- **Validación puntual contra las "Indicaciones de desarrollo" y "Criterios de
  Evaluación" del enunciado**, con auditoría documentada en
  [docs/project-plan/validacion-criterios-enunciado.md](docs/project-plan/validacion-criterios-enunciado.md).
  - `docs/testing/guia-de-pruebas-por-paso.md`: guía nueva que mapea, paso por
    paso, cada sección del enunciado original (`spec/Test Tecnico.md`) a su
    prueba automatizada y a su verificación manual con comandos reales.
  - Comentarios ampliados en `infrastructure/http/tasks.py` (por qué se
    re-serializa el XML, por qué el título de HTML cae a `<h1>` como
    alternativa) y en `infrastructure/reporting/html_report.py` (por qué el
    p90 del resumen por endpoint es una aproximación ponderada, no un
    percentil recalculado).
  - `docs/runbook/operations-runbook.md` corregido: ya no dice que el ETL de
    PDI "no se ejecutó/validó" (desactualizado desde la Fase 8) y se corrigió
    la sintaxis de `Kitchen.bat` en Windows (`-file=...`, no `/file:...`).
  - README.md y `docs/no-tecnico/` actualizados en consecuencia.

- **Fase 9 — Verificación y endurecimiento**: se cerró el hueco entre lo que la
  matriz de trazabilidad ya exigía y lo que había prueba automatizada de verdad;
  no hizo falta cambiar código de producción, el manejo de errores/logging ya
  era correcto.
  - Prueba de idempotencia real de `generar_datos.py` (mismos parámetros dos
    veces ⇒ salida byte-idéntica), que complementa el test de sobrescritura de
    la Fase 5.
  - `tests/unit/test_logging.py` (NFR-10): siete pruebas sobre `setup_logging`
    (destino `stderr`, nivel por defecto/configurable, formato `text`/`json`,
    filtrado por nivel, no duplica *handlers* en llamadas repetidas).
  - Prueba de que un escenario HTTP fallido nunca deja la contraseña de prueba
    en el log (verificado en código, no solo por revisión).
  - `tests/e2e/test_volume_smoke.py` (NFR-13): 100 000 registros de punta a
    punta (`generar_datos` → `calcular_kpi`) en segundos (~5-6 s reales, límite
    de la prueba en 30 s), con verificación de conteos exactos.
  - RTM actualizada: 17/17 requisitos funcionales y 14/14 no funcionales
    marcados como verificados (no solo implementados).
  - `make check` en verde: 180 pruebas, cobertura global 99 %.

- **Fase 8 — ETL con Pentaho/PDI (Parte 2)**: `etl_pdi/t_load_kpi.ktr` y
  `etl_pdi/j_daily_kpi.kjb`, **validados contra una instalación real de
  Pentaho Data Integration 9.4** (no solo redactados a mano).
  - `t_load_kpi.ktr`: CSV Input → tipificación (Select Values) → Filter Rows
    (descarta `requests_total <= 0` o `p90 < avg`) → dos Table Output
    (`stg_kpi_endpoint_dia`, `fct_kpi_endpoint_dia`) con Truncate.
  - `j_daily_kpi.kjb`: ejecuta la transformación, verifica la carga con un
    paso SQL (registrado en la nueva tabla `etl_log`) y registra éxito o
    error.
  - `sql/ddl.sql`, `config/kettle.properties.example`, `README.md`.
  - 16 pruebas de validación estructural nuevas.
  - **3 problemas reales encontrados y corregidos probando con PDI real**
    (no habrían aparecido con solo validación estructural): el tag correcto
    del paso de tipificación es `<meta>` no `<metadata>`; las rutas se
    resuelven con `${Internal.Transformation.Filename.Directory}` en vez de
    rutas relativas simples; y `date_utc` se guarda como texto en vez de
    tipo Fecha (el driver JDBC de SQLite lo serializaría como epoch).
  - Verificado idempotente (Truncate) y el camino de error (forzando un CSV
    ausente) con la instalación real.

- **Fase 7 — Reporte HTML (Parte 3)**: el tercer comando del enunciado ya
  funciona de punta a punta.
  - `application/build_report.py`: orquesta métricas globales, gráficos y
    HTML (reutiliza `charts.py`/`html_report.py` de la Fase 4, sin cambios).
  - CLI `generar_reporte.py --input ... --output ... --umbral_p90 300`.
  - 12 pruebas e2e nuevas: secciones del reporte, alerta por umbral,
    HTML autocontenido, idempotencia, errores de datos/configuración.
  - Verificado manualmente el pipeline completo (`generar_datos` →
    `calcular_kpi` → `generar_reporte`) con los comandos exactos del
    enunciado; HTML inspeccionado y correcto.

- **Adaptador Selenium real** (no contemplado en el plan original; agregado
  a pedido explícito, ver [ADR-0014](docs/adr/0014-selenium-adapter-as-alternative.md)):
  demuestra un uso genuino de Selenium, permitido por el enunciado, sin
  reemplazar ni arriesgar el cliente HTTP ya probado (Fase 6).
  - `infrastructure/http/selenium_client.py`: `SeleniumHttpClient` implementa
    el mismo puerto `HttpPort` que `RequestsHttpClient` — misma política de
    reintentos, mismos errores de dominio. Las funciones de `tasks.py`
    funcionan igual con cualquiera de los dos adaptadores, sin modificarlas.
  - Usa `fetch()` ejecutado dentro del navegador real (vía
    `execute_async_script`) en vez de navegar directamente a cada URL, para
    evitar que Chrome/Edge re-rendericen el JSON/XML en su visor interno.
  - `cliente_http.py` **sigue usando `RequestsHttpClient` por defecto**; no
    se agregó ningún parámetro de CLI nuevo.
  - `selenium` pasa a ser dependencia de runtime real (antes "permitida pero
    no usada"); `ADR-0012` actualizado.
  - 23 pruebas nuevas con un doble del *driver* (rápidas, sin navegador
    real) + 2 pruebas opcionales marcadas `browser` (excluidas por defecto)
    para verificación manual con Chrome/Edge real.
  - Verificado con un Chrome real: el mecanismo funciona correctamente
    (mismo hallazgo de disponibilidad de `httpbin.org` que en la Fase 6).

- **Fase 6 — Cliente HTTP (Parte 0)**: los 6 escenarios contra
  `httpbin.org` ya funcionan de punta a punta con `python cliente_http.py`
  (sin parámetros, tal como pide el enunciado).
  - `infrastructure/http/tasks.py`: auth básica, cookies/sesión, 403 (se
    detecta y maneja correctamente tras agotar los reintentos), extracción
    JSON/XML/HTML, envío de formulario y redirección.
  - `application/http_scenarios.py`: `run_all` ejecuta los 6 sobre la misma
    sesión; el fallo de uno no impide que se ejecuten los demás.
  - `application/ports.py`: se corrigió `HttpResponse` (propiedades de solo
    lectura + `content: bytes`) para que un `requests.Response` real
    conforme el puerto sin envoltorios adicionales.
  - 26 pruebas nuevas: los 6 escenarios con dobles (`responses`), la
    orquestación, y un e2e completo de la CLI.
  - Verificado además contra `httpbin.org` real.

- **Fase 5 — Aplicación y CLI de datos**: los dos primeros comandos del
  enunciado ya funcionan de punta a punta, tal como se piden literalmente.
  - `generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42`
    genera la bitácora sintética.
  - `calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv`
    calcula el CSV de KPIs.
  - Manejo de errores: `--n_registros <= 0` termina con código 2; archivo de
    entrada inexistente o sin ningún registro válido termina con código 1
    (sin generar un CSV vacío en silencio); fallo de escritura también
    código 1.
  - Golden files versionados en `tests/data/` (`bitacora_min.jsonl`,
    `kpi_expected.csv`) para las pruebas de contrato.
  - 13 pruebas e2e nuevas; cobertura global 95 %.
  - Verificado manualmente que ambos comandos, ejecutados tal cual los pide
    el enunciado, terminan con código de salida 0.

- **Fase 4 — Infraestructura (adaptadores)**: implementación concreta de los
  puertos definidos en la arquitectura, con pruebas de integración (E/S real
  sobre directorios temporales, HTTP simulado sin red).
  - `application/ports.py`: los 6 puertos (`Protocol`) que conectan
    `application` con `infrastructure`.
  - `infrastructure/io/jsonl_repository.py`: lectura/escritura de
    `datos.jsonl`, en streaming, con descarte de líneas corruptas vía
    `WARNING` (FR-09, FR-11).
  - `infrastructure/io/csv_repository.py`: lectura/escritura del CSV de KPIs
    conforme al contrato (FR-10, FR-13).
  - `infrastructure/io/artifact_writer.py`: escritura de `datos.json`,
    `datos.xml` y `titulo.html` (FR-04, FR-05, FR-06).
  - `infrastructure/http/client.py`: `RequestsHttpClient` con sesión
    compartida, reintentos con backoff exponencial y manejo configurable
    del `403` (FR-01…FR-08).
  - `infrastructure/reporting/charts.py` y `html_report.py`:
    `MatplotlibChartRenderer` (gráficos PNG, backend `Agg`) y
    `HtmlReportRenderer` (HTML autocontenido, con alerta por umbral de p90 y
    escape de valores) (FR-13).
  - `domain/kpi.py`: se añadió `compute_global_metrics` (métricas globales
    del reporte), resolviendo una discrepancia menor entre `SPEC-004` (que
    sugería un `domain/report.py` separado) y la estructura ya aprobada.
  - 41 pruebas de integración nuevas; cobertura global 86 %.

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

### Cambiado
- Revisados los comentarios y docstrings de todo `src/` para que se lean como
  una explicación natural en vez de una plantilla repetida (menos estructura
  mecánica tipo `Args:`/`Returns:` en funciones simples, sin repetir la misma
  frase de "pendiente de implementación" en cada stub, y sin etiquetar cada
  línea con `FR-xx`/`NFR-xx`). No cambia ninguna lógica ni comportamiento.

### Corregido
- **`CsvKpiRepository.read()` no usaba `pandas`**, pese a que el enunciado lo
  pide explícitamente para `generar_reporte.py` ("Utiliza pandas para cargar
  el CSV"; "matplotlib y pandas son suficientes"). Ahora carga el CSV con
  `pandas.read_csv`, preservando el mismo contrato de errores; se agregó una
  prueba para el caso de archivo vacío (`pandas.errors.EmptyDataError`).
- **`MalformedRecordError` estaba definida, documentada y probada, pero nunca
  se lanzaba en producción** — `JsonlBitacoraRepository.read` manejaba las
  líneas corruptas con excepciones genéricas en vez de este tipo de dominio.
  Ahora se usa realmente; se eliminó además un chequeo de columnas duplicado
  y ya inalcanzable en `csv_repository.py`.
- **Prueba de idempotencia de `generar_datos.py` (agregada en la Fase 9) era
  intermitente**: dependía del reloj real (`datetime.now(UTC)`) sin fijarlo,
  violando la regla del proyecto de que ninguna prueba depende del reloj
  real. Corregida fijando el reloj con `monkeypatch`.
- **`CsvKpiRepository` no traducía columnas faltantes o valores inválidos a
  `DataInputError`** (dejaba propagar `KeyError`/`ValueError` crudos), algo
  que `SPEC-004` exige explícitamente para el reporte HTML. Corregido con
  pruebas de regresión.
- **Bug encontrado probando en vivo contra `httpbin.org`**: cuando un error
  5xx persistía tras agotar los reintentos, `RequestsHttpClient` devolvía la
  respuesta cruda en vez de avisar con `HttpTaskError` — un escenario con un
  503 sostenido terminaba tumbando toda la CLI con un traceback sin
  controlar, en vez de marcarse como fallido y dejar correr a los demás.
  Corregido con una prueba de regresión.
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

### Pendiente
- Fase 10: cierre documental y handoff (ver
  [roadmap-and-phases.md](docs/project-plan/roadmap-and-phases.md)).
