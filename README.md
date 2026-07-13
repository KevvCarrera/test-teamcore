# Cliente HTTP Automatizado · Procesamiento de KPIs · Reporte HTML

Solución en Python 3 que (1) interactúa con distintos endpoints de
[httpbin.org](https://httpbin.org) simulando escenarios de scraping/consumo de
APIs, (2) genera una bitácora sintética de llamadas y calcula KPIs diarios, y
(3) produce un reporte HTML con métricas y gráficos.

Desarrollado con **Spec Driven Development (SDD)**: cada línea de código es
trazable a un requerimiento documentado.

> **Estado actual:** ✅ *Implementado y verificado de punta a punta* (Fases 1–9
> completas; ver [roadmap-and-phases.md](docs/project-plan/roadmap-and-phases.md)
> y el detalle en [TODO.md](TODO.md)). Las cuatro partes del enunciado
> funcionan con los comandos exactos documentados más abajo — no son un
> contrato aspiracional, se ejecutaron y verificaron tal cual. 181 pruebas
> automatizadas, cobertura global 99 %. Pendiente únicamente el cierre
> documental final (Fase 10).

---

## Tabla de contenidos

- [Alcance](#alcance)
- [Arquitectura en 30 segundos](#arquitectura-en-30-segundos)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Guía de inicio rápido (desde clonar el repo)](#guía-de-inicio-rápido-desde-clonar-el-repo)
- [Uso (CLIs)](#uso-clis)
- [Solución de problemas comunes](#solución-de-problemas-comunes)
- [Documentación](#documentación)
- [Calidad y pruebas](#calidad-y-pruebas)

## Alcance

| Módulo | Entrega | Estado |
|---|---|---|
| **Cliente HTTP** (6 escenarios httpbin) | `datos.json`, `datos.xml`, `titulo.html` | ✅ Verificado contra `httpbin.org` real |
| **Generador de datos** (`generar_datos.py`) | `out/datos.jsonl` (500 registros) | ✅ Verificado |
| **Cálculo de KPIs** (`calcular_kpi.py`) | `out/kpi_por_endpoint_dia.csv` | ✅ Verificado |
| **ETL Pentaho/PDI** (`.ktr`, `.kjb`) | SQLite `stg_*` + `fct_*` | ✅ Verificado con PDI 9.4 real |
| **Reporte HTML** (`generar_reporte.py`) | `out/report/kpi_diario.html` | ✅ Verificado |
| **Adaptador Selenium** (alternativa al cliente HTTP) | mismo `HttpPort`, sin CLI nueva | ✅ Verificado con Chrome real |

El CSV de KPIs es el **contrato de interfaz** que alimenta tanto al reporte como al
ETL de Pentaho; su esquema está congelado en
[data-contracts.md](docs/contracts/data-contracts.md). Los ficheros `.ktr`/`.kjb` se
autoran fielmente al formato de PDI; su ejecución/validación final se realiza en una
instalación de PDI (ver [ADR-0013](docs/adr/0013-pentaho-pdi-in-scope.md)).

## Arquitectura en 30 segundos

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

## Estructura del repositorio

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
│   ├── testing/                  # estrategia de pruebas
│   ├── use-cases/                # casos de uso
│   ├── runbook/                  # operación y troubleshooting
│   └── project-plan/             # fases, entregables y Definition of Done
├── src/teamcore_http_kpi/        # código (domain/application/infrastructure/cli)
├── tests/                        # 180 pruebas (unit/integration/e2e/network/browser)
├── etl_pdi/                      # ETL Pentaho/PDI: .ktr, .kjb, sql/, config/
└── out/                          # artefactos generados (ignorado por git)
```

## Guía de inicio rápido (desde clonar el repo)

Requisitos: **Python 3.11+** (`python --version` para confirmar). Nada más —
no hace falta Docker, base de datos externa ni variables de entorno. El ETL
de Pentaho (paso 6) es opcional y requiere PDI instalado aparte.

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

> Atajo equivalente a los pasos 2-3: `make setup` (usa `bash`; en Windows,
> ejecútalo desde Git Bash o sigue los comandos manuales de arriba).

### 3. Verificar que todo quedó instalado correctamente

```bash
make check          # ruff + mypy --strict + pytest (sin red ni navegador)
# o, sin Makefile:
ruff check src tests && mypy && pytest
```

Salida esperada: `ruff` sin errores, `mypy` sin errores, y la suite de
pruebas en verde (180 pruebas passed, 2 deselected). Si algo de esto falla
justo después de instalar, revisa la sección
[Solución de problemas comunes](#solución-de-problemas-comunes) más abajo.

### 4. Ejecutar el pipeline completo, en orden

Los tres comandos siguientes son independientes de red (no requieren
`httpbin.org`) y generan sus artefactos en `out/`:

```bash
python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv
python generar_reporte.py --input out/kpi_por_endpoint_dia.csv \
    --output out/report/kpi_diario.html --umbral_p90 300
```

Al terminar, abre `out/report/kpi_diario.html` en un navegador para ver el
reporte (autocontenido: no necesita servidor ni conexión a internet, los
gráficos van embebidos como imágenes en el propio HTML).

> Atajo equivalente: `make pipeline`.

### 5. Ejecutar el cliente HTTP (requiere red)

```bash
python cliente_http.py
```

Este sí necesita conexión a internet: ejecuta los escenarios contra
`httpbin.org` real y escribe `out/datos.json`, `out/datos.xml` y
`out/titulo.html`. Salida esperada, exit code y detalle de cada escenario en
la sección [Uso (CLIs)](#uso-clis) más abajo.

### 6. (Opcional) Cargar los KPIs a SQLite con Pentaho

Solo si tienes Pentaho Data Integration (Spoon/Kitchen/Pan) instalado.
Instrucciones completas, verificadas contra una instalación real, en
[etl_pdi/README.md](etl_pdi/README.md):

```bash
sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql   # una sola vez
kitchen.sh -file=etl_pdi/j_daily_kpi.kjb -level=Basic  # o Kitchen.bat en Windows
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
make run-http       # python cliente_http.py
make run-datos      # python generar_datos.py (parámetros del enunciado)
make run-kpi        # python calcular_kpi.py (parámetros del enunciado)
make run-reporte    # python generar_reporte.py (parámetros del enunciado)
make pipeline       # run-datos + run-kpi + run-reporte, en orden
make etl-init       # crea la base SQLite del ETL
make etl-run        # ejecuta el job de PDI (requiere Kitchen instalado)
make clean          # borra out/ y las cachés de herramientas
```

> La configuración (URL base, credenciales de prueba, datos del formulario) vive como
> constantes en `config.py` con los valores del enunciado; no requiere `.env`.

## Uso (CLIs)

> Los comandos respetan literalmente los parámetros del enunciado (no se
> agregaron ni renombraron flags). Los cuatro se ejecutaron tal cual para
> verificar este README; salida real abajo de cada uno.

```bash
# (Parte 0) Cliente HTTP: ejecuta los escenarios FR-01…FR-08 contra httpbin.org
# y genera datos.json/datos.xml/titulo.html
python cliente_http.py
```
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

```bash
# (1.1) Generar bitácora sintética reproducible
python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
```
```
Se escribieron 500 registros en out\datos.jsonl
$ echo $?
0
```

```bash
# (1.2) Calcular KPIs diarios por endpoint
python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv
```
```
Se escribieron 28 filas de KPI en out\kpi_por_endpoint_dia.csv
$ echo $?
0
```

```bash
# (3) Generar reporte HTML con umbral de alerta para p90
python generar_reporte.py --input out/kpi_por_endpoint_dia.csv \
    --output out/report/kpi_diario.html --umbral_p90 300
```
```
Reporte escrito en out\report\kpi_diario.html
$ echo $?
0
```

La parte 2 (ETL Pentaho/PDI) no tiene CLI propia: se ejecuta desde Spoon/Kitchen
sobre `etl_pdi/j_daily_kpi.kjb`. Instrucciones completas y verificadas en
[etl_pdi/README.md](etl_pdi/README.md).

## Solución de problemas comunes

- **`make: command not found` en Windows** — `make` no viene con Windows por
  defecto. Usa Git Bash (donde sí suele estar disponible) o simplemente
  ejecuta el comando equivalente del `Makefile` directamente (todos están
  listados arriba en texto plano).
- **El script de activación del entorno virtual no corre en PowerShell**
  (`no se puede cargar porque la ejecución de scripts está deshabilitada`) —
  es la política de ejecución de PowerShell, no un problema del proyecto:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` antes de
  activar, o usa Git Bash con `source .venv/Scripts/activate`.
- **`pip install -e ".[dev]"` falla al resolver `numpy`** — el proyecto fija
  `numpy>=1.26,<2.3` a propósito (`numpy>=2.3` rompe `mypy --strict`, ver
  `pyproject.toml`); si tu resolutor de paquetes se queja, confirma que no
  haya otra versión de `numpy` fijada en un entorno preexistente.
- **`generar_reporte.py` falla con `DataInputError`** — casi siempre es que
  `--input` no es el CSV con el contrato exacto (columnas y orden de
  [data-contracts.md](docs/contracts/data-contracts.md)); reejecuta primero
  `calcular_kpi.py` para regenerarlo.
- **`cliente_http.py` marca algún escenario como fallido** — `httpbin.org` es
  un servicio público, ocasionalmente inestable; el comando ya reintenta con
  backoff automáticamente y el fallo de un escenario no detiene a los demás
  (revisa el detalle que imprime cada línea). No es necesariamente un error
  del código.
- **Problemas con Spoon/Pan/Kitchen (ETL Pentaho)** — ver la sección de
  solución de problemas específica en [etl_pdi/README.md](etl_pdi/README.md)
  (incluye el caso de `NoDefaultCurrentDirectoryInExePath` en Windows).

## Documentación

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

Estado real de estos gates (Fase 9): `ruff` 0 errores, `mypy --strict` 0
errores, **181 pruebas passed** (2 `browser` deselected por defecto),
**cobertura global 99 %**. Detalle de qué prueba cada requisito en la
[matriz de trazabilidad](docs/requirements/requirements-traceability-matrix.md).

Convenciones, principios (SOLID/Clean Code/DRY/KISS/YAGNI) y política de Git en
[CLAUDE.md](CLAUDE.md).
