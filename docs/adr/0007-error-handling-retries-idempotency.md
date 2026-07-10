# ADR-0007 · Errores, reintentos e idempotencia

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

FR-03 pide detectar y manejar el `403` (reintentos/registro). FR-11 pide manejar
archivos inexistentes y JSON mal formado. Los NFR exigen robustez, idempotencia y
*fail fast*. Necesitamos una política coherente y explícita.

## Decisión

### Jerarquía de excepciones (dominio)
`TeamcoreError` como base, con subtipos específicos (ver
[component-model.md](../architecture/component-model.md#5-jerarquía-de-errores-resumen)).
Prohibido `except:` desnudo o silenciar excepciones.

### Reintentos (cliente HTTP)
- Backoff exponencial: `backoff_factor * (2 ** intento)`, con `max_retries`
  configurable. Aplica a errores transitorios (timeouts, 5xx) y, de forma
  **configurable**, al `403` (FR-03).
- Tras agotar reintentos en `403`, se lanza `AccessForbiddenError`, se **registra**
  y el escenario se marca como fallido sin abortar el resto.

### Errores de entrada (FR-11)
- Fichero inexistente ⇒ `InputFileNotFoundError` (mensaje con la ruta) y exit≠0.
- Línea JSONL inválida ⇒ **política fija** (sin flags inventados): se emite `WARNING`
  con el **número de línea**, se descarta la línea, se incrementa un contador y se
  continúa (robustez ante datos parcialmente corruptos).
- Si **ninguna** línea es válida (o el archivo está vacío) ⇒ `DataInputError`
  (exit `1`), para no generar un CSV vacío en silencio (*fail fast*).

### Idempotencia
- Los escritores **truncan/sobrescriben** su destino: reejecutar produce el mismo
  resultado, sin acumulación.
- La generación es determinista por `seed` + `ref_utc` (NFR-07/08).

### Fail fast
- La configuración inválida aborta *antes* de cualquier efecto (E/S o red).

### Códigos de salida (CLI)
`0` éxito · `1` error de datos/entrada · `2` error de configuración/uso ·
`3` error de red/HTTP no recuperable.

## Consecuencias

- (+) Comportamiento predecible y auditable ante fallos.
- (+) Reejecuciones seguras (idempotencia).
- (+) Interfaz de CLI ceñida al enunciado (sin flags inventados).
- (−) Descartar líneas corruptas con `WARNING` podría ocultar problemas si no se
  revisan los logs; se mitiga registrando el contador de descartes y abortando si no
  queda ningún registro válido.

## Alternativas consideradas

- **Silenciar/continuar siempre:** rechazado; oculta problemas de datos.
- **Reintentos infinitos:** rechazado; riesgo de cuelgue. Se acota con `max_retries`.
