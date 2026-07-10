# ADR-0013 · Pentaho/PDI dentro del alcance

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

La Sección 2 del enunciado (Pentaho Data Integration) forma parte del plan del test
técnico y debe implementarse. Análisis de viabilidad: los ficheros de PDI/Kettle
(`.ktr`, `.kjb`) son **XML**; Spoon es únicamente un editor gráfico. Es factible
**autorar los ficheros** de forma fiel al formato de PDI, implementando todos los
pasos que describe el enunciado. La restricción es que en el entorno de desarrollo
actual **no hay Spoon/Kitchen/Pan** para ejecutar y validar los ficheros
end-to-end; la validación final la realiza el usuario en su instalación de PDI.

## Decisión

Implementar la parte de PDI **tal como la describe el enunciado**, con estos
entregables en `etl_pdi/`:

1. `t_load_kpi.ktr` — transformación que lee `out/kpi_por_endpoint_dia.csv`, tipifica
   columnas (fecha/entero/decimal), filtra filas inválidas (`requests_total <= 0` o
   `p90_elapsed_ms < avg_elapsed_ms`) y carga a **SQLite** en `stg_kpi_endpoint_dia` y
   `fct_kpi_endpoint_dia` (ambas con *Truncate* para idempotencia).
2. `j_daily_kpi.kjb` — job que ejecuta la transformación, verifica la carga y registra
   el resultado y los errores en un log.
3. `sql/ddl.sql` — DDL de las tablas de staging y fact.
4. `config/kettle.properties.example` — conexión/rutas de ejemplo (sin secretos).
5. `README.md` — cómo abrir en Spoon y ejecutar con Kitchen/Pan.

- **Base de datos:** **SQLite** (el enunciado permite «SQLite o la que prefieras»);
  fichero local, sin servidor. Se ignora en git.
- **Fidelidad al enunciado (no inventar):** se implementan exactamente los pasos
  descritos (CSV Input, tipificación, Filter Rows, Table Output con Truncate, Table
  Exists / SQL de verificación, logging). Ver [SPEC-005](../specs/SPEC-005-etl-pdi.md).
- **Contrato de entrada intacto:** el CSV `kpi_por_endpoint_dia.csv` es el punto de
  integración; su esquema no cambia ([data-contracts.md](../contracts/data-contracts.md)).
- **Validación:** los ficheros se entregan estructuralmente correctos; la ejecución
  real (Spoon/Kitchen) y su verificación quedan del lado del usuario.

## Consecuencias

- (+) Cobertura completa del enunciado, incluida la Sección 2.
- (+) Pipeline extremo a extremo: `datos.jsonl → CSV → SQLite (stg/fct) → reporte`.
- (+) Idempotencia por *Truncate* en las cargas.
- (−) No se puede validar la ejecución de PDI en este entorno; la verificación final
  depende de la instalación del usuario. Mitigado con DDL, config y runbook claros.
- (−) Introduce un toolchain no-Python (PDI/Kettle, JVM). Es un entregable separado en
  `etl_pdi/`, no una dependencia del paquete Python.

## Notas de interpretación (a confirmar con el usuario)

- **Versión de PDI:** se apunta a un formato compatible con PDI 9.x (ampliamente
  estable). Si el usuario usa otra versión, se ajusta.
- **Verificación de carga (enunciado 2.2.2):** el texto pide comprobar que «el número
  de filas cargadas coincide con la suma de `success_2xx`, `client_4xx` y
  `server_5xx`». Se implementa la verificación **tal como la describe el enunciado**
  (consulta SQL explícita) y se deja documentado el matiz semántico en
  [SPEC-005](../specs/SPEC-005-etl-pdi.md) para su revisión.

## Alternativas consideradas

- **Generar la carga con Python (`sqlite3`) en vez de PDI:** descartado; el enunciado
  pide explícitamente `.ktr`/`.kjb` en Spoon.
