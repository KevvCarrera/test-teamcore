# ADR-0009 · Contratos de datos y formatos

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El pipeline encadena etapas por ficheros y, además, el CSV de KPIs es consumido por
el ETL de Pentaho/PDI (ver [ADR-0013](0013-pentaho-pdi-in-scope.md)). Los formatos, nombres de columnas,
tipos y orden deben ser estables y explícitos.

## Decisión

- **Bitácora en JSONL** (`datos.jsonl`): un objeto JSON por línea. Ventajas:
  streaming, tolerancia a fallos por línea, y es lo que pide el enunciado.
- **KPIs en CSV** (`kpi_por_endpoint_dia.csv`): formato tabular universal, ideal
  como entrada de PDI. **UTF-8**, separador `,`, encabezado obligatorio, punto
  decimal, orden de columnas congelado. Contrato completo en
  [data-contracts.md](../contracts/data-contracts.md).
- **Percentil 90 con `numpy.percentile(x, 90)`** (interpolación lineal por
  defecto). Se documenta explícitamente el método (NFR-05).
- **Normalización de endpoints** con regla determinista y probada
  (`/status/403` → `/status`).
- **Artefactos del cliente HTTP:** `datos.json` (JSON de `/get`), `datos.xml`
  (XML de `/xml`), `titulo.html` (título de `/html`), con nombres exactos.
- **Serialización determinista:** claves ordenadas donde aplique, formato de fecha
  ISO-8601 UTC con sufijo `Z`, redondeo documentado de decimales.
- **Versionado del contrato:** el CSV declara su versión de esquema en la
  documentación; cambios incompatibles ⇒ nuevo ADR + aviso al consumidor PDI.

## Consecuencias

- (+) Etapas desacopladas e interoperables; PDI consume un contrato estable.
- (+) Reproducibilidad y comparabilidad (golden files en pruebas).
- (−) Congelar el orden/tipos de columnas reduce flexibilidad; es intencional.

## Alternativas consideradas

- **Parquet para KPIs:** más eficiente, pero menos universal para PDI y fuera del
  set permitido; el CSV es el formato natural aquí.
- **Percentil manual:** rechazado; el enunciado exige `numpy.percentile`.
