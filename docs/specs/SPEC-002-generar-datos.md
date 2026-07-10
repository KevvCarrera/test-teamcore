# SPEC-002 · Generación de bitácora sintética (`generar_datos.py`)

- **ID:** SPEC-002
- **Estado:** Aprobado
- **Requisitos cubiertos:** FR-09, FR-11, NFR-07, NFR-08
- **Contratos:** [bitácora `datos.jsonl`](../contracts/data-contracts.md#bitácora-datosjsonl)
- **Decisiones:** [ADR-0009](../adr/0009-data-contracts-and-formats.md),
  [ADR-0008](../adr/0008-cli-design-and-parameters.md)

## 1. Objetivo

Producir de forma **reproducible** un archivo `datos.jsonl` con `N` registros que
simulan la bitácora de llamadas HTTP, conforme al esquema del contrato.

## 2. Entradas y salidas

- **CLI (exacta, tal como el enunciado — sin parámetros inventados):**
  `python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42`
- **Parámetros:**
  - `--n_registros` (int, > 0): número de registros. Por defecto `500`.
  - `--salida` (path): destino del JSONL. Por defecto `out/datos.jsonl`.
  - `--seed` (int): semilla para reproducibilidad. Por defecto `42`.
- **Salida:** `datos.jsonl` (una línea JSON por registro), UTF-8, `\n`.

> **Nota:** el instante base para «últimos 3 días» es `datetime.now(UTC)` (como pide
> el enunciado). Para pruebas deterministas, la **función de dominio** acepta un
> `ref_utc` inyectable (no expuesto como flag de CLI); así se evita inventar
> parámetros en la interfaz evaluada.

## 3. Comportamiento

Lógica pura en `domain/generation.py`; E/S en `infrastructure/io/jsonl_repository.py`;
orquestación en `application/generate_data.py`.

- **RNG:** `numpy.random.default_rng(seed)`. **Todas** las decisiones aleatorias
  (endpoint, status, latencia, parse_result, offset temporal) usan este generador ⇒
  misma `seed` + mismo `ref_utc` ⇒ salida byte-idéntica (NFR-07).
- **`timestamp_utc`:** `ref_utc - Δ`, con `Δ` uniforme en `[0, 3 días)`; formateado
  ISO-8601 UTC con sufijo `Z`.
- **`endpoint`:** muestreo uniforme del catálogo de 7 endpoints.
- **`status_code`:** determinado por endpoint:
  - `/status/403` ⇒ `403` siempre.
  - resto ⇒ `200` con alta probabilidad (p. ej. ~0.9), con una cola menor de
    `{500}` (y opcionalmente algún `4xx`) para enriquecer los KPIs. Distribución
    exacta como constante documentada en el módulo.
- **`elapsed_ms`:** uniforme en `[50, 800]`, redondeado a 1 decimal.
- **`parse_result`:** `"error"` con prob. ~`0.05`, si no `"ok"`.

> **Nota de reproducibilidad:** el enunciado pide reproducir el dataset con la
> semilla. La `seed` fija **todas** las decisiones aleatorias (endpoint, status,
> latencia, parse_result y el offset temporal dentro de la ventana de 3 días). El
> ancla temporal es `now(UTC)` en ejecución real; en pruebas se inyecta un `ref_utc`
> fijo a la función de dominio para lograr salidas byte-idénticas sin añadir flags.

## 4. Interfaz pública (diseño)

```python
# domain/generation.py
CATALOG: tuple[str, ...] = ("/get","/post","/status/403","/basic-auth","/cookies","/xml","/html")

def generate_records(n: int, *, seed: int, ref_utc: datetime) -> Iterator[BitacoraRecord]:
    """Genera n registros deterministas. Documenta la distribución de status_code."""

# infrastructure/io/jsonl_repository.py
class JsonlBitacoraRepository:
    def write(self, records: Iterable[BitacoraRecord], destination: Path) -> int: ...
```

## 5. Manejo de errores

- `--n_registros <= 0` ⇒ `ConfigError` (exit `2`).
- `--seed` no entero ⇒ `ConfigError` (exit `2`).
- Directorio de salida inexistente ⇒ se crea (`mkdir -p`); si falla la escritura,
  error de E/S accionable (exit `1`).
- Idempotencia: la escritura **trunca** el destino (NFR-08).

## 6. Criterios de aceptación (Gherkin)

```gherkin
Feature: Generación reproducible de la bitácora (FR-09)
  Scenario: Conteo y esquema
    When ejecuto generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42
    Then el archivo tiene exactamente 500 líneas
    And cada línea valida contra el JSON Schema de la bitácora

  Scenario: Determinismo por semilla (a nivel de función, con ref_utc fijo)
    Given dos invocaciones de generate_records con la misma seed y el mismo ref_utc
    Then ambas secuencias de registros son idénticas
    And al serializarlas producen archivos byte-idénticos

  Scenario: Reglas de negocio
    Then todos los registros con endpoint "/status/403" tienen status_code 403
    And todos los timestamps caen dentro de las últimas 72 horas respecto al ancla temporal
    And elapsed_ms está entre 50 y 800
    And la proporción de parse_result="error" es cercana a 5%

  Scenario: Validación de parámetros (FR-11)
    When ejecuto con --n_registros 0
    Then termina con código 2 y un mensaje de configuración inválida
```

## 7. Pruebas asociadas

- `tests/unit/test_generation.py`: esquema, reglas de status/latencia/parse,
  determinismo (`test_determinism`), rango temporal.
- `tests/e2e/test_generar_datos_cli.py`: conteo de líneas, idempotencia, exit codes.

## 8. Trazabilidad

FR-09, FR-11, NFR-07/08 → [RTM](../requirements/requirements-traceability-matrix.md).
