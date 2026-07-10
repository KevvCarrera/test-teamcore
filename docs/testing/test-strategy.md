# Estrategia de Pruebas

> Estado: Aprobado · Decisión: [ADR-0011](../adr/0011-testing-strategy-and-tooling.md)

## 1. Objetivos

- Verificar cada criterio de aceptación de las specs (FR) y los atributos de calidad
  (NFR).
- Ser **deterministas**, **rápidas** y **ejecutables sin red**.
- Servir de red de seguridad para refactors (mantenibilidad).

## 2. Pirámide de pruebas

```
        e2e (pocas)         → CLIs de extremo a extremo sobre golden files
     integration (algunas)  → adaptadores: HTTP con dobles, E/S en tmp_path
   unit (muchas)            → dominio puro: normalización, KPIs, p90, generación
```

Regla de reparto orientativa: **~70 % unit / ~20 % integration / ~10 % e2e**.

## 3. Niveles y alcance

| Nivel | Marcador | Qué prueba | Dependencias |
|---|---|---|---|
| Unit | `unit` | Funciones puras de `domain` | Ninguna (sin E/S, sin red) |
| Integration | `integration` | Adaptadores `infrastructure` (HTTP con `responses`, E/S en `tmp_path`) | Dobles, ficheros temporales |
| E2E | `e2e` | CLIs completas con golden input/output | Subproceso o `main()` en proceso |
| Network | `network` | Humo contra httpbin real | Red (excluido por defecto) |

Ejecución por defecto: `pytest` corre `-m "not network"`.

## 4. Casos mínimos por requisito

| Requisito | Pruebas clave |
|---|---|
| FR-01…FR-08 | Un test por escenario con `responses`; credenciales inválidas; agotamiento de reintentos (FR-03) |
| FR-04/05/06 | Artefactos `datos.json`/`datos.xml`/`titulo.html` con contenido correcto |
| FR-09 | Esquema por línea; determinismo (misma seed+ref-utc ⇒ idéntico); reglas de status/latencia/parse; conteo exacto |
| FR-10 | Normalización (tabla + límites); percentil vs `numpy.percentile`; conteos por rango; orden determinista; golden CSV |
| FR-11 | Fichero inexistente; línea corrupta (WARNING + skip); archivo sin registros válidos; parámetros inválidos |
| FR-13 | Métricas globales; % por endpoint; lógica de umbral (rojo/no rojo); HTML autocontenido |
| FR-14…FR-17 | Validación **estructural** de los XML de PDI (pasos presentes, referencias correctas, DDL válido); la validación funcional la ejecuta el usuario en Spoon/Kitchen |
| NFR-07/08 | Determinismo e idempotencia (doble ejecución byte-idéntica) |
| NFR-09 | `mypy --strict` en verde (gate de CI) |
| Arquitectura | Prueba que `domain` no importa `requests`/`pandas`/`matplotlib`/`argparse` |

## 5. Datos de prueba (golden files)

- `tests/data/bitacora_min.jsonl`: bitácora pequeña y controlada (entrada golden).
- `tests/data/kpi_expected.csv`: salida esperada de KPIs (output golden).
- Se generan de forma reproducible con `--seed` fijo y un tiempo de referencia
  inyectado a nivel de función; se versionan.

## 6. Fixtures y utilidades (`conftest.py`)

- `tmp_out` (dir temporal de salida), `frozen_ref_utc`, `seed`, `http_mock`
  (`responses`), `sample_records`.
- Sin estado global; cada test es independiente.

## 7. Cobertura y gates

| Gate | Umbral |
|---|---|
| Cobertura de `domain` | ≥ 90 % |
| Cobertura global | ≥ 80 % |
| `ruff check` | 0 errores |
| `mypy --strict` | 0 errores |
| `pytest -m "not network"` | 100 % verde |

`make check` = `lint` + `type` + `test`. Es el gate local equivalente a CI.

## 8. Estrategia de mocking

- **HTTP:** `responses` registra respuestas por endpoint; nunca se toca la red en la
  suite por defecto.
- **Tiempo:** se inyecta `ref_utc`; no se parchea el reloj global.
- **Aleatoriedad:** semilla explícita vía `numpy.random.default_rng`.
- **Sistema de ficheros:** `tmp_path` de pytest; nada se escribe fuera de él.

## 9. Validación de la parte PDI

Como no hay Spoon/Kitchen en el entorno de desarrollo, la parte de PDI se valida en
dos niveles (ver [SPEC-005](../specs/SPEC-005-etl-pdi.md)):
- **Automatizable aquí:** pruebas que parsean los XML `.ktr`/`.kjb` y verifican que
  contienen los pasos esperados (CSV Input, Filter Rows, dos Table Output con
  Truncate, verificación en el job) y que el `ddl.sql` es SQL válido.
- **Manual (usuario):** ejecución real en Spoon/Kitchen contra SQLite.

## 10. Qué NO se prueba (y por qué)

- La **ejecución** de PDI (requiere Kettle/JVM; la hace el usuario). Sí se valida la
  estructura de los ficheros y el contrato del CSV que consume.
- Librerías de terceros (`requests`, `numpy`, …): se confía en ellas; se prueba
  nuestro uso, no su implementación.
