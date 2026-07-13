# Guía de pruebas por paso (mapeada al enunciado)

> Complementa a [test-strategy.md](test-strategy.md) (que explica la
> *estrategia* de pruebas automatizadas en general). Este documento responde
> una pregunta más concreta: **para cada paso del enunciado original**
> ([spec/Test Tecnico.md](../../spec/Test%20Tecnico.md)), ¿qué prueba automatizada
> lo cubre, y cómo lo verifico yo mismo a mano, con comandos reales?

Cada sección sigue el mismo formato:
1. **Qué pide el enunciado** (resumen, sin copiar el texto completo).
2. **Prueba automatizada** — qué archivo/función de `tests/` lo cubre y cómo correrla sola.
3. **Verificación manual** — comandos reales y qué mirar en el resultado.

---

## Parte 0 · Cliente HTTP

### Autenticación básica

- **Pide:** GET a `/basic-auth/{user}/{passwd}` con Basic Auth; validar que
  responde autenticado.
- **Prueba automatizada:**
  ```bash
  pytest tests/integration/test_http_tasks.py::test_basic_auth_success -v
  pytest tests/integration/test_http_tasks.py::test_basic_auth_failure_raises -v
  ```
  (usa `responses` como doble — no llama a `httpbin.org` real).
- **Verificación manual:**
  ```bash
  python cliente_http.py
  ```
  Busca en la salida la línea `Autenticación básica: OK — autenticado como
  usuario_test`. Si querés ver la llamada cruda: `curl -u usuario_test:clave123
  https://httpbin.org/basic-auth/usuario_test/clave123` debe devolver
  `{"authenticated": true, "user": "usuario_test"}`.

### Manejo de cookies y sesiones

- **Pide:** fijar `session=activa` en `/cookies/set`, confirmar en `/cookies`.
- **Prueba automatizada:**
  ```bash
  pytest tests/integration/test_http_tasks.py::test_set_and_get_cookies_success -v
  ```
- **Verificación manual:** en la salida de `python cliente_http.py`, la línea
  `Cookies y sesión: OK — cookie de sesión confirmada: session=activa`
  confirma que la *misma sesión* (mismo objeto `requests.Session`) vio la
  cookie que ella misma fijó un instante antes.

### Restricción de acceso (403)

- **Pide:** detectar el 403 de `/status/403` y manejarlo (reintentos/registro).
- **Prueba automatizada:**
  ```bash
  pytest tests/integration/test_http_tasks.py::test_simulate_forbidden_handles_403_as_success -v
  pytest tests/integration/test_http_client.py -k 403 -v   # política de reintentos/backoff ante 403
  ```
- **Verificación manual:** la salida de `cliente_http.py` marca este escenario
  `OK` cuando el 403 se agota tras los reintentos configurados (no cuando
  *no* hay 403 — ojo, aquí "OK" significa "se comportó como se esperaba ante
  un 403 persistente", no "la petición tuvo éxito"). Revisa los `WARNING` en
  stderr: deberías ver 3 líneas `Estado 403 en GET /status/403 (intento N),
  reintentando` antes de la línea final `OK`.

### Extracción y procesamiento de datos (JSON/XML/HTML)

- **Pide:** JSON de `/get` → `datos.json`; XML de `/xml` → `datos.xml`;
  título de `/html` → `titulo.html`.
- **Prueba automatizada:**
  ```bash
  pytest tests/integration/test_http_tasks.py -k "extract" -v
  ```
- **Verificación manual:**
  ```bash
  python cliente_http.py
  cat out/datos.json     # debe ser JSON válido con la respuesta de /get
  cat out/datos.xml      # debe empezar con <?xml version='1.0' encoding='UTF-8'?>
  cat out/titulo.html    # debe ser <title>Herman Melville - Moby-Dick</title>
  python -c "import json; json.load(open('out/datos.json'))"   # falla si no es JSON válido
  python -c "from lxml import etree; etree.parse('out/datos.xml')"  # falla si no es XML válido
  ```

### Envío de formularios

- **Pide:** POST a `/post` con los 4 campos de prueba; mostrar lo enviado y lo recibido.
- **Prueba automatizada:**
  ```bash
  pytest tests/integration/test_http_tasks.py::test_submit_form_success -v
  ```
- **Verificación manual:** la línea `Envío de formulario: OK — formulario
  reflejado correctamente en la respuesta` confirma que los 4 campos que
  `config.py` define (`Juan`/`Pérez`/`juan.perez@example.com`/mensaje) volvieron
  exactamente iguales en el `"form"` de la respuesta de `/post`.

### Manejo de redirecciones

- **Pide:** `/redirect-to?url=/get`, seguir hasta la respuesta final.
- **Prueba automatizada:**
  ```bash
  pytest tests/integration/test_http_tasks.py::test_follow_redirect_success -v
  ```
- **Verificación manual:** la línea `Redirección: OK — redirección seguida (1
  salto(s)) hasta /get` confirma que `response.history` (que `requests` llena
  automáticamente al seguir redirects) tiene al menos una entrada.

### Todo junto (los 8 escenarios en una sola corrida)

```bash
pytest tests/integration/test_http_scenarios.py tests/e2e/test_cliente_http_cli.py -v
pytest -m network -v   # opcional: humo real contra httpbin.org (excluido por defecto)
python cliente_http.py; echo "exit code: $?"   # debe ser 0 si los 8 salieron OK
```

---

## 1. Procesamiento de datos en Python

### 1.1 Generación de datos ficticios (`generar_datos.py`)

- **Pide:** `datos.jsonl` con 500 registros, esquema fijo, reproducible con `--seed`.
- **Prueba automatizada:**
  ```bash
  pytest tests/unit/test_generation.py -v         # reglas de negocio + determinismo puro
  pytest tests/e2e/test_generar_datos_cli.py -v   # la CLI completa
  ```
  Presta atención a `test_determinism_same_seed_same_ref_utc` (dominio,
  tiempo congelado) y a `test_rerun_with_same_params_is_byte_identical` (CLI
  completa, con el reloj congelado vía `monkeypatch` — ver el comentario en
  ese test sobre por qué hace falta congelarlo).
- **Verificación manual:**
  ```bash
  python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
  wc -l out/datos.jsonl                       # debe dar exactamente 500
  head -1 out/datos.jsonl | python -m json.tool   # una línea, esquema correcto
  # Reproducibilidad: correr dos veces con la misma seed y comparar
  python generar_datos.py --n_registros 50 --salida /tmp/a.jsonl --seed 7
  python generar_datos.py --n_registros 50 --salida /tmp/b.jsonl --seed 7
  diff /tmp/a.jsonl /tmp/b.jsonl              # sin diferencias si ref_utc no cruza un segundo
  ```
  > La reproducibilidad **estricta** (byte a byte) solo está garantizada
  > cuando además se fija `ref_utc` — la CLI usa la hora real, así que un
  > `diff` manual entre dos corridas separadas por más de un segundo puede
  > mostrar timestamps distintos; eso es esperado, no un bug (ver
  > `domain/generation.py`).

### 1.2 Cálculo de KPIs diarios (`calcular_kpi.py`)

- **Pide:** agrupar por `(date_utc, endpoint_base)`, calcular las 7 métricas,
  usando `numpy.percentile` para el p90 y normalizando `endpoint_base`.
- **Prueba automatizada:**
  ```bash
  pytest tests/unit/test_kpi.py tests/unit/test_endpoints.py -v   # dominio puro
  pytest tests/e2e/test_calcular_kpi_cli.py -v                    # CLI + golden files
  ```
  `tests/unit/test_kpi.py` compara `percentile_90` contra `numpy.percentile`
  directamente (no reimplementa la fórmula, así que la prueba está validando
  el uso correcto de la librería, no una reimplementación paralela).
- **Verificación manual:**
  ```bash
  python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv
  column -s, -t < out/kpi_por_endpoint_dia.csv | less -S   # inspección legible
  # Verificación cruzada del p90 con numpy, para un endpoint y fecha puntuales
  # (ajustar la fecha al valor real que haya quedado en tu out/datos.jsonl)
  python -c "
  import json, numpy as np
  from pathlib import Path
  records = [json.loads(l) for l in Path('out/datos.jsonl').read_text().splitlines()]
  latencias = [r['elapsed_ms'] for r in records
               if r['endpoint'].startswith('/get') and r['timestamp_utc'].startswith('2026-07-10')]
  print('p90 manual:', round(float(np.percentile(latencias, 90)), 2))
  "
  grep '^2026-07-10,/get,' out/kpi_por_endpoint_dia.csv   # misma fecha/endpoint — el último
  # número (p90_elapsed_ms) debe coincidir con el "p90 manual" de arriba.
  ```
- **Manejo de errores (ambos scripts):**
  ```bash
  python calcular_kpi.py --input out/no-existe.jsonl --output out/x.csv; echo $?   # → 1
  echo 'esto no es json' > /tmp/roto.jsonl
  python calcular_kpi.py --input /tmp/roto.jsonl --output out/x.csv; echo $?       # → 1 (sin filas válidas)
  python generar_datos.py --n_registros 0 --salida out/x.jsonl; echo $?            # → 2 (config inválida)
  ```
  Ver la tabla completa de códigos de salida en
  [operations-runbook.md §6](../runbook/operations-runbook.md).

---

## 2. Procesamiento con Pentaho Data Integration (PDI)

- **Pide:** `t_load_kpi.ktr` (CSV Input → tipificación → Filter Rows → 2×
  Table Output) y `j_daily_kpi.kjb` (ejecuta la transformación, verifica y
  registra el resultado).
- **Prueba automatizada** (estructural — no requiere PDI instalado):
  ```bash
  pytest tests/integration/test_etl_pdi_structure.py -v
  ```
  Verifica que el XML tiene los pasos/entradas correctos y que `sql/ddl.sql`
  es SQL válido — **no** ejecuta PDI (ver la nota de alcance en
  `test-strategy.md §9`).
- **Verificación manual (requiere Spoon/Kitchen/Pan instalados):**
  ```bash
  sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql
  python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
  python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv
  kitchen.sh -file=etl_pdi/j_daily_kpi.kjb -level=Basic   # Kitchen.bat en Windows
  sqlite3 etl_pdi/db/kpi.sqlite "SELECT COUNT(*) FROM fct_kpi_endpoint_dia;"
  sqlite3 etl_pdi/db/kpi.sqlite "SELECT * FROM etl_log ORDER BY run_at DESC LIMIT 1;"
  # Idempotencia: correr el job una segunda vez y confirmar que el COUNT no cambia
  # Camino de error: mover/renombrar temporalmente out/kpi_por_endpoint_dia.csv
  # y volver a correr el job — debe fallar y quedar registrado en etl_log/el log de PDI
  ```
  Instrucciones completas, con la lista de problemas reales encontrados al
  probar esto contra una instalación real, en
  [etl_pdi/README.md](../../etl_pdi/README.md).

---

## 3. Tablero o reporte con Python (`generar_reporte.py`)

- **Pide:** leer el CSV con **pandas**, dibujar 2 gráficos con **matplotlib**,
  marcar en rojo los `p90_elapsed_ms` que superen `--umbral_p90`.
- **Prueba automatizada:**
  ```bash
  pytest tests/integration/test_csv_repository.py -v   # lectura del CSV (con pandas)
  pytest tests/integration/test_charts.py -v            # los 2 gráficos son PNG válidos
  pytest tests/integration/test_html_report.py -v       # secciones, alerta, escape de HTML
  pytest tests/e2e/test_generar_reporte_cli.py -v       # la CLI completa
  ```
- **Verificación manual:**
  ```bash
  python generar_reporte.py --input out/kpi_por_endpoint_dia.csv \
      --output out/report/kpi_diario.html --umbral_p90 300
  # abrir out/report/kpi_diario.html en un navegador y confirmar a ojo:
  #   - 4 métricas globales arriba (total, % éxito, % error, p90 global)
  #   - una tabla con una fila por endpoint
  #   - 2 gráficos (barras horizontales de solicitudes; barras de p90)
  #   - cualquier p90 por encima de 300 ms aparece en rojo
  # Confirmar que es autocontenido (no depende de red ni de otros archivos):
  mv out/report/kpi_diario.html /tmp/ && python -m http.server --directory /dev/null &
  # abrir /tmp/kpi_diario.html directamente desde el disco (file://) — debe verse igual
  ```
- **Manejo de errores:**
  ```bash
  python generar_reporte.py --input out/no-existe.csv --output out/x.html; echo $?   # → 1
  echo "date_utc,endpoint_base" > /tmp/incompleto.csv
  python generar_reporte.py --input /tmp/incompleto.csv --output out/x.html; echo $?  # → 1
  ```

---

## Todo junto (gate completo, como en CI)

```bash
make check    # ruff + mypy --strict + pytest (sin red/navegador) — debe terminar en 0
make pipeline # generar_datos + calcular_kpi + generar_reporte, en orden
python cliente_http.py   # requiere red
```

Ver también la [matriz de trazabilidad](../requirements/requirements-traceability-matrix.md)
para el mapeo completo requisito → módulo → prueba, y
[validacion-criterios-enunciado.md](../project-plan/validacion-criterios-enunciado.md)
para la evaluación punto por punto contra los criterios del enunciado.
