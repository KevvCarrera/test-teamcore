# ETL de KPIs con Pentaho Data Integration (Parte 2)

Carga `out/kpi_por_endpoint_dia.csv` (el CSV que produce `calcular_kpi.py`) a una
base SQLite, con tipificación, validación y staging + fact idempotentes. Ver
[SPEC-005](../docs/specs/SPEC-005-etl-pdi.md) y
[ADR-0013](../docs/adr/0013-pentaho-pdi-in-scope.md) para el diseño completo.

> **Estos ficheros ya se probaron de punta a punta** con Pentaho Data
> Integration 9.4 real (`Pan.bat`/`Kitchen.bat`), no solo se redactaron a mano:
> se verificó que cargan las 28 filas de un CSV de ejemplo (500 registros de
> `generar_datos.py`), que el Truncate hace las cargas idempotentes (dos
> corridas seguidas dejan el mismo resultado), y que el camino de error
> (transformación fallida) efectivamente dispara el log de error sin
> completar el resto del job.

## Contenido

| Archivo | Qué es |
|---|---|
| `t_load_kpi.ktr` | Transformación: CSV Input → tipificación → Filter Rows → 2× Table Output (Truncate) |
| `j_daily_kpi.kjb` | Job: ejecuta la transformación, verifica la carga y registra el resultado |
| `sql/ddl.sql` | DDL de `stg_kpi_endpoint_dia`, `fct_kpi_endpoint_dia` y `etl_log` |
| `config/kettle.properties.example` | Plantilla de configuración (sin secretos; SQLite no usa credenciales) |
| `db/` | Base SQLite generada (ignorada por git) |

## Cómo ejecutarlo

### 1. Preparar la base de datos (una sola vez, o cuando quieras reiniciarla)

```bash
sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql
```

### 2. Tener el CSV de entrada listo

```bash
python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv
```

### 3. Ejecutar el job (recomendado) o solo la transformación

Con una instalación de PDI (Spoon/Kitchen/Pan) en el `PATH`, **desde la raíz
del repositorio**:

```powershell
# Windows (PowerShell) — job completo (transformación + verificación + log)
& "<ruta_a_pdi>\Kitchen.bat" "-file=etl_pdi\j_daily_kpi.kjb" "-level=Basic"

# Solo la transformación (sin la verificación/log del job)
& "<ruta_a_pdi>\Pan.bat" "-file=etl_pdi\t_load_kpi.ktr" "-level=Basic"
```

```bash
# Linux/macOS
kitchen.sh -file=etl_pdi/j_daily_kpi.kjb -level=Basic
pan.sh -file=etl_pdi/t_load_kpi.ktr -level=Basic
```

> Nota práctica: si tu `cmd`/PowerShell tiene la variable de entorno
> `NoDefaultCurrentDirectoryInExePath` activa, `Kitchen.bat`/`Pan.bat` pueden
> fallar al intentar invocar `Spoon.bat` internamente sin encontrarlo. Si eso
> pasa, agrega la carpeta de instalación de PDI a tu `PATH` antes de llamarlos
> (`$env:Path = "<ruta_a_pdi>;" + $env:Path` en PowerShell).

### 4. Abrir en Spoon (para inspeccionar/editar visualmente)

Abre `Spoon.bat`/`spoon.sh`, y desde el menú `Archivo → Abrir`, selecciona
`t_load_kpi.ktr` o `j_daily_kpi.kjb` directamente desde el sistema de ficheros
(no hace falta un repositorio de PDI).

### 5. Verificar la carga

```bash
sqlite3 etl_pdi/db/kpi.sqlite "SELECT COUNT(*) FROM fct_kpi_endpoint_dia;"
sqlite3 etl_pdi/db/kpi.sqlite "SELECT * FROM etl_log ORDER BY run_at DESC LIMIT 1;"
```

## Qué hace cada paso

**Transformación (`t_load_kpi.ktr`):**
1. **CSV Input** — lee `out/kpi_por_endpoint_dia.csv` (ruta resuelta con
   `${Internal.Transformation.Filename.Directory}`, relativa al propio
   fichero `.ktr`, no al directorio desde donde se invoque Pan/Kitchen).
2. **Tipificar columnas** (Select Values) — `requests_total`, `success_2xx`,
   `client_4xx`, `server_5xx`, `parse_errors` → Integer; `avg_elapsed_ms`,
   `p90_elapsed_ms` → Number. `date_utc` se deja como String a propósito (ver
   nota abajo).
3. **Filter Rows** — conserva solo filas con `requests_total > 0` **y**
   `p90_elapsed_ms >= avg_elapsed_ms`; el resto se descarta (FR-14).
4. **Staging (Truncate)** y **Fact (Truncate)** — cargan el mismo flujo
   filtrado a `stg_kpi_endpoint_dia` y `fct_kpi_endpoint_dia`, ambas con
   *Truncate* (idempotencia, FR-16).

**Job (`j_daily_kpi.kjb`):**
1. Ejecuta `t_load_kpi.ktr`.
2. **Verificar carga** (paso SQL) — inserta en `etl_log` una comparación entre
   filas cargadas y la suma de `success_2xx + client_4xx + server_5xx` (ver
   nota de interpretación abajo).
3. Registra el resultado: **Log de éxito** si todo salió bien, **Log de
   error** si la transformación o la verificación fallaron — probado
   forzando ambos caminos.

## Nota de interpretación (ya documentada en SPEC-005)

El enunciado (2.2.2) pide verificar que "el número de filas cargadas coincide
con la suma de `success_2xx`, `client_4xx` y `server_5xx`". Literalmente,
**el número de filas = número de grupos** `(date_utc, endpoint_base)`,
mientras que esa suma = **total de solicitudes clasificadas** — ambos números
coinciden solo si hubiera exactamente una solicitud por grupo, lo cual no es
el caso general. La verificación se implementa tal como la describe el
enunciado (consulta SQL explícita, registrada en `etl_log` con el estado
`OK` si coinciden o `OK_CON_NOTA` si no, sin abortar el job por esta
discrepancia esperada) — se probó con datos reales y, efectivamente, no
coinciden (28 filas vs. 500 solicitudes), confirmando que es un matiz del
enunciado y no un error de la carga.

## Por qué `date_utc` no se tipifica como Fecha

Se intentó tipificar `date_utc` a tipo Fecha en "Tipificar columnas" (como
pide el enunciado: "asigna tipos adecuados: fecha, entero, decimal"), pero al
probarlo contra SQLite real, el driver JDBC serializa un valor de tipo Fecha
como número de milisegundos desde época — no como el texto `'YYYY-MM-DD'` que
exige el contrato (`date_utc TEXT NOT NULL`). Como SQLite no tiene un tipo de
fecha nativo (solo *affinity*, ver
[data-contracts.md](../docs/contracts/data-contracts.md#modelo-relacional-sqlite-pdi)),
y el CSV de origen ya trae `date_utc` exactamente en formato `YYYY-MM-DD`, se
deja como String: es un ajuste basado en la prueba real, no una omisión.

## Límite conocido

Los pasos y el job se probaron con Pentaho Data Integration 9.4.0.0-343.
Otras versiones de PDI deberían abrir estos ficheros sin problema (el formato
XML de `.ktr`/`.kjb` es estable entre versiones 8.x/9.x), pero no se probó
contra otras versiones específicas.

## Nota de handoff: el contrato del CSV de entrada

Quien mantenga esta parte del ETL **no controla** `calcular_kpi.py` (vive en
el lado Python del repositorio) — el punto de contacto entre ambos mundos es
exclusivamente el CSV `kpi_por_endpoint_dia.csv`, cuyo esquema está congelado
en [data-contracts.md § KPI CSV](../docs/contracts/data-contracts.md#kpi-csv-kpi_por_endpoint_diacsv)
como **v1.0**. Lo que necesitas saber para operar/mantener `t_load_kpi.ktr`
sin sorpresas:

- **Columnas y orden exactos** (el paso *CSV Input* las lee por posición, no
  solo por nombre): `date_utc, endpoint_base, requests_total, success_2xx,
  client_4xx, server_5xx, parse_errors, avg_elapsed_ms, p90_elapsed_ms`.
- **`date_utc` es String, no Fecha** — deliberado, ver la sección de arriba
  ("Por qué `date_utc` no se tipifica como Fecha"). Si algún día cambias esta
  transformación para tipificarlo como Fecha, vuelve a probar contra SQLite
  real: el driver JDBC serializa Fecha como epoch-milisegundos, rompiendo el
  contrato `date_utc TEXT`.
- **El paso Filter Rows asume** `requests_total > 0` (siempre cierto por
  construcción) y `p90_elapsed_ms >= avg_elapsed_ms` (cierto en el caso
  general, pero **no** garantizado matemáticamente — ver
  [data-contracts.md § Invariantes](../docs/contracts/data-contracts.md#invariantes-y-validaciones-aguas-abajo)).
  Si el generador de datos cambia su distribución de latencias, revisa si
  este filtro sigue descartando lo que debe.
- **Si el lado Python cambia el esquema del CSV** (columnas nuevas, renombradas,
  reordenadas, o tipos distintos), el contrato exige un ADR y un incremento de
  versión mayor antes del cambio — eso es tu señal para revisar y volver a
  probar `t_load_kpi.ktr` contra PDI real, no asumir que sigue funcionando.
- **Antes de cualquier cambio a este `.ktr`/`.kjb`**, vuelve a ejecutarlo con
  Pan.bat/Kitchen.bat reales (no te fíes solo de las 16 pruebas estructurales
  de `tests/integration/test_etl_pdi_structure.py` — esas comprueban que el
  XML tiene la forma correcta, no que Pentaho lo ejecuta sin errores; los 3
  bugs de la Fase 8 solo aparecieron al ejecutar de verdad).
