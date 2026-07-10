# Requisitos Funcionales (FR)

Cada requisito se extrae del documento fuente (`spec/Test Tecnico.md`) y recibe un
identificador estable `FR-xx` usado en specs, pruebas y código. La columna
*Origen* referencia la sección del documento original.

**Convención de prioridad:** `MUST` (obligatorio), `SHOULD` (recomendado).

---

## Parte 0 — Cliente HTTP

### FR-01 · Autenticación básica · MUST
- **Origen:** «Autenticación Básica».
- **Descripción:** Realizar `GET /basic-auth/{user}/{passwd}` con autenticación
  HTTP básica y validar que la respuesta indica autenticación exitosa.
- **Entradas:** usuario `usuario_test`, contraseña `clave123` (desde configuración).
- **Salidas:** resultado de autenticación (log + valor booleano de dominio).
- **Aceptación:** con credenciales válidas la respuesta es `200` y
  `authenticated == true`; con credenciales inválidas se maneja el `401` sin
  abortar el resto del flujo.

### FR-02 · Cookies y sesiones · MUST
- **Origen:** «Manejo de Cookies y Sesiones».
- **Descripción:** Establecer una cookie de sesión con
  `/cookies/set?session=activa` y verificar con `GET /cookies` que quedó fijada,
  **reutilizando la misma sesión**.
- **Aceptación:** la respuesta de `/cookies` contiene `session == "activa"`.

### FR-03 · Restricciones de acceso (403) · MUST
- **Origen:** «Simulación de Restricciones de Acceso».
- **Descripción:** Solicitar `GET /status/403`, **detectar** el código 403 y
  **manejarlo** mediante reintentos y/o registro de error.
- **Aceptación:** el `403` se detecta explícitamente, se registra en log y se
  aplican reintentos con backoff según política configurada; el flujo no lanza una
  excepción no controlada.

### FR-04 · Extracción JSON (`/get`) · MUST
- **Origen:** «Extracción y Procesamiento de Datos — JSON».
- **Descripción:** Extraer y mostrar información de `GET /get`.
- **Salidas:** artefacto **`datos.json`** con la estructura de datos de `/get`.
- **Aceptación:** `datos.json` es JSON válido que refleja la respuesta de `/get`.

### FR-05 · Extracción XML (`/xml`) · MUST
- **Origen:** «Extracción y Procesamiento de Datos — XML».
- **Descripción:** Parsear y mostrar los datos de `GET /xml`.
- **Salidas:** artefacto **`datos.xml`** con el contenido parseado.
- **Aceptación:** `datos.xml` es XML bien formado; el parseo extrae al menos un
  dato representativo mostrado por consola/log.

### FR-06 · Extracción de título HTML (`/html`) · MUST
- **Origen:** «Extracción y Procesamiento de Datos — HTML».
- **Descripción:** Extraer el contenido del **título** de la página `GET /html`.
- **Salidas:** artefacto **`titulo.html`** que contiene el título extraído.
- **Aceptación:** `titulo.html` contiene el texto del `<title>`/encabezado
  principal de la página `/html`.

### FR-07 · Envío de formulario (`/post`) · MUST
- **Origen:** «Simulación de Envío de Formularios».
- **Descripción:** Enviar datos simulando un formulario con `POST /post` y mostrar
  los datos enviados y la respuesta recibida.
- **Entradas:** Nombre=`Juan`, Apellido=`Pérez`, Correo=`juan.perez@example.com`,
  Mensaje=`Este es un mensaje de prueba.` (desde configuración).
- **Aceptación:** la respuesta de `/post` refleja en `form` los cuatro campos
  enviados.

### FR-08 · Manejo de redirecciones · MUST
- **Origen:** «Manejo de Redirecciones».
- **Descripción:** Solicitar `GET /redirect-to?url=/get` y seguir la redirección
  hasta obtener la respuesta final.
- **Aceptación:** la respuesta final corresponde a `/get` (`200`), con el historial
  de redirección disponible/registrado.

---

## Parte 1 — Procesamiento de datos

### FR-09 · Generación de bitácora sintética · MUST
- **Origen:** «1.1 Generación de datos ficticios».
- **Descripción:** Script `generar_datos.py` que produce `datos.jsonl` con
  **500 registros** (una línea JSON por registro) según el esquema:
  `timestamp_utc`, `endpoint`, `status_code`, `elapsed_ms`, `parse_result`.
- **Reglas de generación:**
  1. `timestamp_utc`: UTC dentro de los **últimos 3 días**.
  2. `endpoint`: aleatorio entre `/get`, `/post`, `/status/403`, `/basic-auth`,
     `/cookies`, `/xml`, `/html`.
  3. `status_code`: entero en función del endpoint (`/status/403` ⇒ siempre `403`;
     el resto mayoritariamente `200`).
  4. `elapsed_ms`: decimal entre **50 y 800**.
  5. `parse_result`: `"ok"`, o `"error"` en ~**5 %** de los casos.
- **CLI (exacta):** `--n_registros`, `--salida`, `--seed`.
- **Aceptación:** misma semilla (y tiempo de referencia) ⇒ salida byte-idéntica;
  cada línea valida contra el esquema; conteos coherentes con las reglas.

### FR-10 · Cálculo de KPIs diarios · MUST
- **Origen:** «1.2 Cálculo de KPIs diarios».
- **Descripción:** Script `calcular_kpi.py` que lee `datos.jsonl` y genera
  `kpi_por_endpoint_dia.csv`. Para cada `(date_utc, endpoint_base)` calcula:
  `requests_total`, `success_2xx`, `client_4xx`, `server_5xx`, `parse_errors`,
  `avg_elapsed_ms`, `p90_elapsed_ms`.
- **Reglas:**
  - `endpoint_base`: normalización de rutas quitando parámetros/valores variables
    (p. ej. `/status/403` → `/status`). Ver
    [normalización](../contracts/data-contracts.md#normalización-de-endpoints).
  - `p90_elapsed_ms`: percentil 90 con `numpy.percentile`.
- **CLI:** parámetros de entrada y salida por línea de comandos
  (`--input`, `--output`).
- **Aceptación:** el CSV cumple el contrato de columnas/tipos/orden; los agregados
  son correctos frente a un dataset de referencia.

### FR-11 · Manejo de errores de E/S y datos · MUST
- **Origen:** «1.3 Indicaciones de desarrollo».
- **Descripción:** Manejar archivos inexistentes, JSON mal formado y casos
  límite con mensajes claros y códigos de salida apropiados.
- **Aceptación:** entrada inexistente ⇒ error controlado con mensaje accionable y
  exit code ≠ 0; línea JSONL corrupta ⇒ se reporta la línea y se aplica la política
  definida (abortar o descartar-con-aviso, según spec).

### FR-12 · README con ejemplos de ejecución · MUST
- **Origen:** «1.3» y «Criterios de Evaluación».
- **Descripción:** Proveer un `README.md` con ejemplos de ejecución de los scripts.
- **Aceptación:** el README documenta los comandos exactos de cada CLI.

---

## Parte 2 — ETL con Pentaho Data Integration (PDI)

> Parte del plan del enunciado; decisión de diseño en [ADR-0013](../adr/0013-pentaho-pdi-in-scope.md).
> Detalle en [SPEC-005](../specs/SPEC-005-etl-pdi.md).

### FR-14 · Transformación `t_load_kpi.ktr` · MUST
- **Origen:** «2.1 Transformación (.ktr)».
- **Descripción:** Transformación PDI que lee `out/kpi_por_endpoint_dia.csv`
  (CSV Input), **tipifica** columnas (fecha/entero/decimal), **valida** con Filter
  Rows (descarta `requests_total <= 0` o `p90_elapsed_ms < avg_elapsed_ms`) y **carga**
  a SQLite en `stg_kpi_endpoint_dia` (staging) y `fct_kpi_endpoint_dia` (fact), ambas
  con *Truncate* para idempotencia.
- **Aceptación:** el `.ktr` contiene esos pasos; una ejecución en PDI puebla ambas
  tablas solo con filas válidas.

### FR-15 · Job `j_daily_kpi.kjb` · MUST
- **Origen:** «2.2 Job (.kjb)».
- **Descripción:** Job PDI que ejecuta `t_load_kpi.ktr`, realiza una **verificación
  posterior** (Table Exists / SQL) sobre las filas cargadas y **registra** en un log
  el resultado y los errores.
- **Aceptación:** el `.kjb` orquesta la transformación, la verificación y el logging.

### FR-16 · Persistencia idempotente en SQLite · MUST
- **Origen:** «2.1 Salida» / «2.2».
- **Descripción:** Cargas con *Truncate*; DDL de las tablas versionado en
  `etl_pdi/sql/ddl.sql`. Reejecutar deja la BD en el mismo estado.
- **Aceptación:** dos ejecuciones consecutivas producen el mismo contenido.

### FR-17 · Configuración/credenciales separadas · MUST
- **Origen:** «2.3 Indicaciones de desarrollo».
- **Descripción:** La conexión a BD y credenciales se documentan en un archivo de
  configuración separado (`etl_pdi/config/kettle.properties.example`), sin secretos
  en git.
- **Aceptación:** existe la plantilla de configuración documentada.

---

## Parte 3 — Reporte

### FR-13 · Reporte HTML de KPIs · MUST
- **Origen:** «3.1 / 3.2 / 3.3».
- **Descripción:** Script `generar_reporte.py` que lee
  `kpi_por_endpoint_dia.csv` y genera `out/report/kpi_diario.html` con:
  - **Métricas globales:** total de solicitudes, % de éxitos (2xx), % de errores
    (4xx/5xx) y valor global de `p90_elapsed_ms`.
  - **Tabla por endpoint:** `endpoint_base`, `requests_total`, `%_success`,
    `%_client_4xx`, `%_server_5xx`, `avg_elapsed_ms`, `p90_elapsed_ms`.
  - **Gráficos:** (a) barra horizontal de `requests_total` por endpoint;
    (b) línea o barra de `p90_elapsed_ms` por endpoint.
- **CLI (exacta):** `--input`, `--output`, `--umbral_p90`.
- **Regla de alerta:** los `p90_elapsed_ms` que superen `--umbral_p90` se marcan en
  **rojo** en el reporte.
- **Tecnología:** `pandas` (carga CSV) + `matplotlib` (gráficos). Sin llamadas HTTP.
- **Aceptación:** el HTML abre en un navegador; las métricas y la alfa/roja por
  umbral son correctas frente a un CSV de referencia.

---

## Resumen

| ID | Título | Prioridad | Entrega principal |
|---|---|---|---|
| FR-01 | Autenticación básica | MUST | — |
| FR-02 | Cookies y sesiones | MUST | — |
| FR-03 | Restricciones 403 | MUST | log/reintentos |
| FR-04 | Extracción JSON | MUST | `datos.json` |
| FR-05 | Extracción XML | MUST | `datos.xml` |
| FR-06 | Título HTML | MUST | `titulo.html` |
| FR-07 | Envío de formulario | MUST | — |
| FR-08 | Redirecciones | MUST | — |
| FR-09 | Generar bitácora | MUST | `datos.jsonl` |
| FR-10 | Calcular KPIs | MUST | `kpi_por_endpoint_dia.csv` |
| FR-11 | Manejo de errores | MUST | — |
| FR-12 | README con ejemplos | MUST | `README.md` |
| FR-13 | Reporte HTML | MUST | `kpi_diario.html` |
| FR-14 | Transformación PDI | MUST | `t_load_kpi.ktr` |
| FR-15 | Job PDI | MUST | `j_daily_kpi.kjb` |
| FR-16 | Persistencia SQLite idempotente | MUST | `stg_*`, `fct_*`, `ddl.sql` |
| FR-17 | Config/credenciales separadas | MUST | `kettle.properties.example` |
