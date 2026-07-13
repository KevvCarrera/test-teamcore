# Cliente HTTP Automatizado · Procesamiento de KPIs · Reporte HTML

Solución en Python 3 para el ejercicio técnico de Teamcore, organizada
exactamente en las mismas partes en que lo pide
[spec/Test Tecnico.md](spec/Test%20Tecnico.md):

- **Parte 0** — Cliente HTTP automatizado contra `httpbin.org`.
- **Parte 1** — Procesamiento de datos en Python (generación + cálculo de KPIs).
- **Parte 2** — ETL con Pentaho Data Integration (PDI).
- **Parte 3** — Tablero/reporte HTML con Python.

Desarrollado con **Spec Driven Development (SDD)**: cada línea de código es
trazable a un requerimiento documentado en [docs/](docs/).

> **Estado actual:** ✅ *Implementado y verificado de punta a punta* (Fases 1–9
> completas; detalle en [TODO.md](TODO.md)). Las cuatro partes funcionan con
> los comandos exactos documentados abajo — se ejecutaron y verificaron tal
> cual, no son un contrato aspiracional. 181 pruebas automatizadas, cobertura
> global 99 %. Pendiente únicamente el cierre documental final (Fase 10).

| Parte | Entrega | Estado |
|---|---|---|
| 0 · Cliente HTTP | `datos.json`, `datos.xml`, `titulo.html` | ✅ Verificado contra `httpbin.org` real |
| 1.1 · Generación de datos | `out/datos.jsonl` (500 registros) | ✅ Verificado |
| 1.2 · Cálculo de KPIs | `out/kpi_por_endpoint_dia.csv` | ✅ Verificado |
| 2 · ETL Pentaho/PDI | SQLite `stg_*` + `fct_*` | ✅ Verificado con PDI 9.4 real |
| 3 · Reporte HTML | `out/report/kpi_diario.html` | ✅ Verificado |

El CSV de KPIs es el **contrato de interfaz** que alimenta tanto al reporte
(Parte 3) como al ETL de Pentaho (Parte 2); su esquema está congelado en
[data-contracts.md](docs/contracts/data-contracts.md).

---

## Tabla de contenidos

- [Puesta en marcha](#puesta-en-marcha)
- [Parte 0: Cliente HTTP Automatizado](#parte-0-cliente-http-automatizado)
- [Parte 1: Procesamiento de datos en Python](#parte-1-procesamiento-de-datos-en-python)
- [Parte 2: Procesamiento con Pentaho Data Integration (PDI)](#parte-2-procesamiento-con-pentaho-data-integration-pdi)
- [Parte 3: Tablero o reporte con Python](#parte-3-tablero-o-reporte-con-python)
- [Arquitectura y estructura del repositorio](#arquitectura-y-estructura-del-repositorio)
- [Solución de problemas comunes](#solución-de-problemas-comunes)
- [Documentación adicional](#documentación-adicional)
- [Calidad y pruebas](#calidad-y-pruebas)

---

## Puesta en marcha 

Requisitos: **Python 3.11+** (`python --version` para confirmar). No hace
falta Docker, base de datos externa ni variables de entorno. Dos herramientas
adicionales son necesarias según qué partes vayas a ejecutar:

- **`sqlite3` (CLI)** — obligatorio para la Parte 2 (ETL): crea el archivo
  `.sqlite` y sus tablas antes de la primera carga. No viene con Windows ni
  con Git Bash; instálalo con `winget install SQLite.SQLite` o descargando
  los binarios de [sqlite.org/download.html](https://sqlite.org/download.html).
  No hace falta para las Partes 0, 1 y 3. **Verifica que la carpeta que
  contiene `sqlite3.exe` quede agregada al `PATH`** (con winget normalmente
  se agrega sola al PATH de usuario; con los binarios descargados manualmente
  hay que agregarla a mano) y **abre una terminal nueva** después de
  instalar — una terminal ya abierta no toma el `PATH` actualizado.
- **`make`** — opcional, solo para usar los atajos del `Makefile` (`make
  check`, `make setup`, etc.). Tampoco viene con Windows/Git Bash; instálalo
  con `choco install make` o vía MSYS2 (`pacman -S make`), o simplemente
  ejecuta el comando equivalente de cada atajo directamente (todos listados
  en la [tabla de atajos](#resumen-de-todos-los-atajos-de-makefile)).

Pentaho (Parte 2) además requiere PDI (Spoon/Kitchen) instalado aparte para
*ejecutar* el job — no para crear la base de datos, que solo necesita
`sqlite3`.

### 1. Clonar el repositorio

```bash
git clone https://github.com/KevvCarrera/test-teamcore.git
cd test-teamcore
```

### 2. Crear el entorno virtual e instalar

```bash
python -m venv .venv
```

Activarlo (el comando cambia según tu shell):

```bash
source .venv/bin/activate        # Linux/macOS (bash/zsh)
source .venv/Scripts/activate    # Windows con Git Bash
.venv\Scripts\Activate.ps1       # Windows con PowerShell
```

Instalar el proyecto en modo editable, con las dependencias de desarrollo
(`pytest`, `ruff`, `mypy`, etc.) incluidas:

```bash
pip install -e ".[dev]"
```

> Atajo equivalente a estos 2 pasos: `make setup` (usa `bash`; en Windows,
> ejecútalo desde Git Bash o sigue los comandos manuales de arriba).

### 3. Verificar que todo quedó instalado correctamente

```bash
make check          # ruff + mypy --strict + pytest (sin red ni navegador)
# o, sin Makefile:
ruff check src tests && mypy && pytest
```

Salida esperada: `ruff` sin errores, `mypy` sin errores, y la suite de
pruebas en verde (181 pruebas passed, 2 deselected). Si algo de esto falla
justo después de instalar, revisa
[Solución de problemas comunes](#solución-de-problemas-comunes).

> La configuración (URL base, credenciales de prueba, datos del formulario)
> vive como constantes en `config.py` con los valores del enunciado; no
> requiere `.env`.

Con el entorno listo, las siguientes 4 secciones cubren cada parte del
enunciado en su propio orden — instrucciones, comando exacto y salida real.

---

## Parte 0: Cliente HTTP Automatizado

Ejecuta, contra `httpbin.org` real, los escenarios de autenticación básica,
cookies/sesión, restricción de acceso (403), extracción JSON/XML/HTML, envío
de formulario y redirecciones — y escribe `datos.json`, `datos.xml` y
`titulo.html`.

```bash
python cliente_http.py
```

Requiere conexión a internet (es el único comando de los cuatro que la
necesita). Salida real de una corrida verificada:

```
Autenticación básica: OK — autenticado como usuario_test
Cookies y sesión: OK — cookie de sesión confirmada: session=activa
Restricción de acceso (403): OK — 403 detectado y manejado tras agotar los reintentos configurados
Extracción JSON: OK — datos.json escrito
Extracción XML: OK — datos.xml escrito (dato representativo: 'Sample Slide Show')
Extracción de título HTML: OK — titulo.html escrito (título: 'Herman Melville - Moby-Dick')
Envío de formulario: OK — formulario reflejado correctamente en la respuesta
Redirección: OK — redirección seguida (1 salto(s)) hasta /get
$ echo $?
0
```

No acepta parámetros (el enunciado no define flags para esta parte); toda la
configuración (credenciales de prueba, datos del formulario) vive en
`config.py`. Detalle de cada escenario, su prueba automatizada y cómo
verificarlo a mano en
[guia-de-pruebas-por-paso.md § Parte 0](docs/testing/guia-de-pruebas-por-paso.md#parte-0--cliente-http).

<details>
<summary>Ejemplo real del contenido de los 3 artefactos generados</summary>

`out/datos.json` (respuesta de `/get`, tal cual la devuelve `httpbin.org`):

```json
{
  "args": {},
  "headers": {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Host": "httpbin.org",
    "User-Agent": "python-requests/2.34.2"
  },
  "origin": "x.x.x.x",
  "url": "https://httpbin.org/get"
}
```

`out/datos.xml` (parseado y re-serializado desde `/xml`, con declaración XML explícita):

```xml
<?xml version='1.0' encoding='UTF-8'?>
<slideshow title="Sample Slide Show" date="Date of publication" author="Yours Truly">
    <slide type="all">
      <title>Wake up to WonderWidgets!</title>
    </slide>
    <slide type="all">
        <title>Overview</title>
        <item>Why <em>WonderWidgets</em> are great</item>
    </slide>
</slideshow>
```

`out/titulo.html` (título extraído de `/html`):

```html
<title>Herman Melville - Moby-Dick</title>
```

</details>

---

## Parte 1: Procesamiento de datos en Python

### 1.1 Generación de datos ficticios

`generar_datos.py` crea una bitácora sintética de llamadas HTTP (no llama a
`httpbin.org`; simula datos con las reglas del enunciado: catálogo de
endpoints, status coherente con cada uno, latencia 50–800 ms, ~5 % de errores
de parseo).

```bash
python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
```

```
Se escribieron 500 registros en out\datos.jsonl
$ echo $?
0
```

`--seed` hace el resultado reproducible: la misma semilla siempre genera la
misma bitácora. Ejemplo real de una línea de `out/datos.jsonl`:

```json
{"timestamp_utc": "2026-07-11T05:10:48Z", "endpoint": "/get", "status_code": 200, "elapsed_ms": 245.3, "parse_result": "ok"}
```

### 1.2 Cálculo de KPIs diarios

`calcular_kpi.py` lee `out/datos.jsonl`, agrupa por `(date_utc,
endpoint_base)` y calcula `requests_total`, `success_2xx`, `client_4xx`,
`server_5xx`, `parse_errors`, `avg_elapsed_ms` y `p90_elapsed_ms` (con
`numpy.percentile`), normalizando el endpoint (`/status/403` → `/status`).

```bash
python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv
```

```
Se escribieron 28 filas de KPI en out\kpi_por_endpoint_dia.csv
$ echo $?
0
```

Primeras filas reales de `out/kpi_por_endpoint_dia.csv` (nótese `/status/403`
normalizado a `/status`, y el resto de columnas ya agregadas por día):

```csv
date_utc,endpoint_base,requests_total,success_2xx,client_4xx,server_5xx,parse_errors,avg_elapsed_ms,p90_elapsed_ms
2026-07-09,/basic-auth,6,6,0,0,0,480.9,765.1
2026-07-09,/cookies,2,2,0,0,0,259.2,282.4
2026-07-09,/get,5,5,0,0,0,384.16,661.44
```

Manejo de errores de ambos scripts (archivo inexistente, JSON mal formado,
parámetros inválidos):

```bash
python calcular_kpi.py --input out/no-existe.jsonl --output out/x.csv; echo $?   # → 1
python generar_datos.py --n_registros 0 --salida out/x.jsonl; echo $?            # → 2
```

Detalle línea por línea de dónde vive cada pieza de esta lógica (qué archivo,
qué función) y cómo verificarla, incluida una comprobación cruzada del p90
contra `numpy.percentile` calculado a mano, en
[guia-de-pruebas-por-paso.md § Parte 1](docs/testing/guia-de-pruebas-por-paso.md#1-procesamiento-de-datos-en-python).

---

## Parte 2: Procesamiento con Pentaho Data Integration (PDI)

`etl_pdi/t_load_kpi.ktr` (transformación) y `etl_pdi/j_daily_kpi.kjb` (job)
cargan `out/kpi_por_endpoint_dia.csv` a una base SQLite, con tipificación,
un filtro de sanidad y carga idempotente (Truncate) en dos tablas
(`stg_kpi_endpoint_dia`, `fct_kpi_endpoint_dia`).

### ¿La base SQLite se arma sola? No

**El archivo `.sqlite` y sus tablas no se crean automáticamente.** Ni Python
ni el job de PDI los generan por su cuenta — hay que correr el DDL **una
sola vez** (o cuando quieras reiniciar la base) antes de la primera carga.
Esto requiere el **CLI de `sqlite3`** instalado (ver
[Requisitos](#puesta-en-marcha); no viene con Windows ni con Git Bash):

```bash
sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql
```

> En PowerShell, `<` no funciona como redirección de entrada ("está
> reservado para uso futuro"); usa en su lugar:
> ```powershell
> Get-Content etl_pdi\sql\ddl.sql -Raw | sqlite3 etl_pdi\db\kpi.sqlite
> ```

Si te saltás este paso, el job de Kitchen falla con un error de `no such
table`, porque el paso *Table Output* (Truncate) espera que
`stg_kpi_endpoint_dia`/`fct_kpi_endpoint_dia` ya existan — no las crea él
mismo. `etl_pdi/db/` está en `.gitignore`: cada quien arma su propia base
localmente con este comando.

### Ejecución completa, paso a paso

```bash
# 1. Crear la base y las tablas (una sola vez)
sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql   # Linux/macOS/Git Bash

# 2. Tener el CSV de entrada listo (Parte 1.2)
python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv

# 3. Ejecutar el job (requiere Spoon/Kitchen/Pan instalados)
kitchen.sh -file=etl_pdi/j_daily_kpi.kjb -level=Basic       # Linux/macOS
```
```powershell
# 1. Crear la base y las tablas (una sola vez) — Windows/PowerShell
Get-Content etl_pdi\sql\ddl.sql -Raw | sqlite3 etl_pdi\db\kpi.sqlite

# 3. Ejecutar el job (requiere Spoon/Kitchen/Pan instalados) — Windows
& "<ruta_a_pdi>\Kitchen.bat" "-file=etl_pdi\j_daily_kpi.kjb" "-level=Basic"
```

```bash
# 4. Verificar la carga
sqlite3 etl_pdi/db/kpi.sqlite "SELECT COUNT(*) FROM fct_kpi_endpoint_dia;"
sqlite3 etl_pdi/db/kpi.sqlite "SELECT * FROM etl_log ORDER BY run_at DESC LIMIT 1;"
```

Salida real de una corrida verificada (28 filas del CSV de ejemplo, 500
solicitudes en total):

```
28
2026-07-13 02:57:54|OK_CON_NOTA|28|filas_cargadas=28 suma_2xx_4xx_5xx=500
```

> `OK_CON_NOTA` no es un error: es la nota de interpretación documentada en
> [etl_pdi/README.md](etl_pdi/README.md#nota-de-interpretación-ya-documentada-en-spec-005) —
> el número de filas (grupos `date_utc`+`endpoint_base`) y la suma de
> `success_2xx+client_4xx+server_5xx` (total de solicitudes) son magnitudes
> distintas por diseño, y quedan ambas registradas para que quien revise el
> log entienda por qué no coinciden.

Estos ficheros ya se **validaron contra una instalación real** de Pentaho
9.4 (no solo se redactaron a mano): carga correcta, Truncate idempotente
(dos corridas seguidas sin duplicar) y camino de error probado forzando un
CSV ausente. Instrucciones completas, los 3 problemas reales encontrados al
validarlo y notas de configuración en
[etl_pdi/README.md](etl_pdi/README.md).

---

## Parte 3: Tablero o reporte con Python

`generar_reporte.py` lee `out/kpi_por_endpoint_dia.csv` con **pandas** y
genera un HTML autocontenido con métricas globales, una tabla por endpoint y
2 gráficos (`matplotlib`): solicitudes totales por endpoint y p90 de
latencia por endpoint. `--umbral_p90` marca en rojo los valores que lo
superen.

```bash
python generar_reporte.py --input out/kpi_por_endpoint_dia.csv \
    --output out/report/kpi_diario.html --umbral_p90 300
```

```
Reporte escrito en out\report\kpi_diario.html
$ echo $?
0
```

Abrí `out/report/kpi_diario.html` directamente en un navegador (`file://`,
sin servidor) para verlo — es autocontenido: los gráficos van embebidos en
base64 dentro del propio HTML, no dependen de ningún otro archivo.

Ejemplo real de las 4 métricas globales que encabezan el reporte (HTML tal
cual quedó embebido, con los 500 registros del ejemplo de arriba):

```html
<div class="metrics">
  <div class="metric"><div>Total de solicitudes</div><div class="value">500</div></div>
  <div class="metric"><div>% de éxito (2xx)</div><div class="value">76.6%</div></div>
  <div class="metric"><div>% de errores (4xx/5xx)</div><div class="value">23.4%</div></div>
  <div class="metric"><div>p90 global (aprox.)</div><div class="value">699.09 ms</div></div>
</div>
```

Debajo de eso van la tabla por endpoint (con las filas en rojo si su
`p90_elapsed_ms` supera `--umbral_p90`) y los 2 gráficos de barras.

```bash
python generar_reporte.py --input out/no-existe.csv --output out/x.html; echo $?   # → 1
```

---

## Arquitectura y estructura del repositorio

Arquitectura por capas (dependencias hacia el dominio):

```
cli/  ──►  application/  ──►  domain/  ◄──  infrastructure/
(argparse)  (casos de uso)   (lógica pura)   (HTTP, ficheros, gráficos)
```

- **`domain`**: entidades, normalización de endpoints, KPIs y percentiles. Sin E/S.
- **`application`**: orquesta casos de uso (generar datos, calcular KPI, reporte).
- **`infrastructure`**: adaptadores de red (`requests`), ficheros (`csv`/`json`/
  `pandas` para cargar el CSV de KPIs) y gráficos (`matplotlib`).
- **`cli`**: puntos de entrada que respetan los parámetros exactos del enunciado.

Detalle y diagramas en
[architecture-overview.md](docs/architecture/architecture-overview.md).

```
.
├── CLAUDE.md                     # Reglas del agente / del proyecto
├── README.md
├── pyproject.toml                # Empaquetado, dependencias y config de tooling
├── Makefile                      # Atajos: setup, lint, type, test, run-*
├── docs/                         # Toda la ingeniería de especificaciones (SDD)
│   ├── project-charter.md
│   ├── requirements/             # FR/NFR + matriz de trazabilidad
│   ├── architecture/             # visión, estructura, flujo de datos, componentes
│   ├── adr/                      # decisiones de arquitectura (ADR)
│   ├── contracts/                # contratos de datos / esquemas
│   ├── specs/                    # especificaciones por componente
│   ├── testing/                  # estrategia de pruebas + guía de pruebas por paso
│   ├── use-cases/                # casos de uso
│   ├── runbook/                  # operación y troubleshooting
│   └── project-plan/             # fases, entregables y validación contra el enunciado
├── src/teamcore_http_kpi/        # código (domain/application/infrastructure/cli)
├── tests/                        # 181 pruebas (unit/integration/e2e/network/browser)
├── etl_pdi/                      # ETL Pentaho/PDI: .ktr, .kjb, sql/, config/
└── out/                          # artefactos generados (ignorado por git)
```

### Resumen de todos los atajos de `Makefile`

```bash
make help          # lista todos los atajos con su descripción
make setup          # entorno virtual + instalación editable
make lint           # ruff
make type           # mypy --strict
make test           # pytest (sin red/navegador)
make test-network   # incluye las pruebas @network contra httpbin.org real
make check          # lint + type + test (gate local completo)
make cov            # pytest con reporte de cobertura
make run-http       # python cliente_http.py            (Parte 0)
make run-datos      # python generar_datos.py            (Parte 1.1)
make run-kpi        # python calcular_kpi.py             (Parte 1.2)
make run-reporte    # python generar_reporte.py          (Parte 3)
make pipeline       # run-datos + run-kpi + run-reporte, en orden
make etl-init       # crea la base SQLite del ETL         (Parte 2)
make etl-run        # ejecuta el job de PDI (requiere Kitchen instalado)
make clean          # borra out/ y las cachés de herramientas
```

---

## Solución de problemas comunes

- **`make: command not found` en Windows** — `make` no viene con Windows ni
  con Git Bash por defecto (es un error común asumir que Git Bash lo incluye:
  no lo hace). Dos opciones:
  - Ejecuta el comando equivalente del `Makefile` directamente (todos listados
    arriba), p. ej. `ruff check src tests && mypy && pytest` en vez de
    `make check`.
  - O instala `make` aparte: `choco install make` (Chocolatey) o vía MSYS2
    (`pacman -S make`), y luego sí funciona `make check` tal cual desde Git
    Bash.
- **`sqlite3: command not found` (incluso después de instalarlo)** — igual
  que `make`, el CLI de `sqlite3` tampoco viene con Windows ni con Git Bash;
  solo hace falta para la Parte 2 (crear la base del ETL, ver
  [Requisitos](#puesta-en-marcha)). Instálalo con `winget install
  SQLite.SQLite` o desde
  [sqlite.org/download.html](https://sqlite.org/download.html) (sección
  "Precompiled Binaries for Windows"). Dos causas frecuentes si sigue sin
  encontrarse después de instalado:
  - La carpeta de `sqlite3.exe` no quedó en el `PATH` — agrégala a mano si
    instalaste los binarios manualmente (winget normalmente sí la agrega
    sola al `PATH` de usuario).
  - **La terminal ya estaba abierta antes de instalar** — el `PATH` se lee
    una vez al abrir la terminal; ábrela de nuevo (cierra y reabre Git Bash
    o la terminal integrada del editor) para que tome el `PATH` actualizado.
- **El script de activación del entorno virtual no corre en PowerShell**
  (`no se puede cargar porque la ejecución de scripts está deshabilitada`) —
  es la política de ejecución de PowerShell, no un problema del proyecto:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` antes de
  activar, o usa Git Bash con `source .venv/Scripts/activate`.
- **`pip install -e ".[dev]"` falla al resolver/compilar `numpy`** — el
  proyecto fija `numpy>=2.3.5,<2.5` a propósito: por debajo de `2.3.5` no hay
  wheels de Windows para Python 3.13/3.14 (pip intenta compilar desde código
  fuente y falla sin un compilador C instalado) y `numpy>=2.5` rompe
  `mypy --strict` bajo `python_version = "3.11"` (ver
  [ADR-0015](docs/adr/0015-python-3-13-3-14-compatibility.md)). Si tu
  resolutor de paquetes se queja, confirma que no haya otra versión de
  `numpy` fijada en un entorno preexistente.
- **`generar_reporte.py` falla con `DataInputError`** — casi siempre es que
  `--input` no es el CSV con el contrato exacto (columnas y orden de
  [data-contracts.md](docs/contracts/data-contracts.md)); reejecuta primero
  `calcular_kpi.py` para regenerarlo.
- **`cliente_http.py` marca algún escenario como fallido** — `httpbin.org` es
  un servicio público, ocasionalmente inestable; el comando ya reintenta con
  backoff automáticamente y el fallo de un escenario no detiene a los demás
  (revisa el detalle que imprime cada línea). No es necesariamente un error
  del código.
- **El job de PDI falla con "no such table"** — te saltaste el paso 1 de la
  Parte 2 (`sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql`); la base y
  las tablas no se crean solas.
- **Otros problemas con Spoon/Pan/Kitchen** — ver la sección específica en
  [etl_pdi/README.md](etl_pdi/README.md) (incluye el caso de
  `NoDefaultCurrentDirectoryInExePath` en Windows).

## Documentación adicional

Punto de entrada: **[docs/README.md](docs/README.md)** (orden de lectura sugerido).
Documentos clave:

- 📋 [Project Charter](docs/project-charter.md) — visión, alcance y fuera de alcance.
- ✅ [Requisitos + Trazabilidad](docs/requirements/requirements-traceability-matrix.md)
- 🏛️ [Arquitectura](docs/architecture/architecture-overview.md) y [ADRs](docs/adr/)
- 🔌 [Contratos de datos](docs/contracts/data-contracts.md)
- 🧩 [Especificaciones](docs/specs/) por componente
- 🧪 [Estrategia de pruebas](docs/testing/test-strategy.md)
- ✔️ [Guía de pruebas por paso](docs/testing/guia-de-pruebas-por-paso.md) — cada
  sección del enunciado, con su prueba automatizada y su verificación manual
- 🛠️ [Runbook de operación](docs/runbook/operations-runbook.md)
- 🔍 [Validación contra los criterios del enunciado](docs/project-plan/validacion-criterios-enunciado.md)

## Calidad y pruebas

```bash
make lint     # ruff (estilo + errores)
make type     # mypy --strict
make test     # pytest (sin red/navegador por defecto)
make check    # lint + type + test
```

Estado real de estos gates: `ruff` 0 errores, `mypy --strict` 0 errores,
**181 pruebas passed** (2 `browser` deselected por defecto), **cobertura
global 99 %**. Detalle de qué prueba cada requisito en la
[matriz de trazabilidad](docs/requirements/requirements-traceability-matrix.md).

Convenciones, principios (SOLID/Clean Code/DRY/KISS/YAGNI) y política de Git en
[CLAUDE.md](CLAUDE.md).
