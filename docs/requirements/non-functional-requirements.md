# Requisitos No Funcionales (NFR)

Atributos de calidad transversales. Algunos derivan explícitamente del documento
fuente («Criterios de Evaluación», «Indicaciones de desarrollo»); otros son
estándares de ingeniería que este proyecto adopta para alcanzar nivel producción.

| ID | Atributo | Requisito | Verificación |
|---|---|---|---|
| **NFR-01** | Plataforma | Python **3.11+** (el enunciado pide Python 3) | `pyproject.toml`, CI |
| **NFR-02** | Frontera de dependencias | Runtime limitado a librerías permitidas: `requests`, `beautifulsoup4`, `lxml`, `numpy`, `pandas`, `matplotlib` + stdlib (`json`, `csv`, `datetime`, `argparse`). `selenium`/`playwright` permitidas pero no usadas | Revisión de `pyproject.toml` + [ADR-0004](../adr/0004-http-requests-over-browser-automation.md), [ADR-0012](../adr/0012-dependency-boundary-allowed-libraries.md) |
| **NFR-03** | Robustez | Manejo explícito de errores y excepciones; *fail fast* en config inválida; sin `except` desnudo | Pruebas de error + `ruff` |
| **NFR-04** | Legibilidad / organización | Funciones pequeñas y puras; separación de responsabilidades; nombres claros | Revisión + `ruff` (complejidad) |
| **NFR-05** | Documentación | Comentarios/docstrings que expliquen la lógica clave: **normalización de endpoints** y **cálculo del p90** | Revisión + doctest/enlaces a specs |
| **NFR-06** | Formato de entregables | Nombres y formatos exactos: `datos.json`, `datos.xml`, `titulo.html`, `datos.jsonl`, `kpi_por_endpoint_dia.csv`, `kpi_diario.html` | Pruebas e2e |
| **NFR-07** | Reproducibilidad | Misma semilla (+ tiempo de referencia) ⇒ salida idéntica | Prueba de determinismo |
| **NFR-08** | Idempotencia | Reejecutar un script sobrescribe su salida de forma determinista, sin efectos acumulativos | Prueba de idempotencia |
| **NFR-09** | Tipado | `type hints` completos; `mypy --strict` sin errores | CI (`make type`) |
| **NFR-10** | Observabilidad | Logging estructurado y configurable (nivel/formato); sin `print` para diagnóstico; sin secretos en logs | Revisión + [ADR-0006](../adr/0006-logging-strategy.md) |
| **NFR-11** | Testabilidad | Dominio unit-testeable sin red ni ficheros reales; pruebas deterministas | [test-strategy.md](../testing/test-strategy.md) |
| **NFR-12** | Portabilidad | Ejecuta en Windows, Linux y macOS; rutas vía `pathlib`; codificación UTF-8 explícita | Pruebas en rutas temporales |
| **NFR-13** | Rendimiento | Procesar 500 registros (y hasta ~10⁵) en segundos, con uso de memoria acotado | Prueba de volumen (smoke) |
| **NFR-14** | Seguridad | Credenciales de prueba (no sensibles) como constantes documentadas en `config.py`; sin secretos reales en el repo; credenciales fuera de logs; contenido remoto tratado como dato no confiable | Revisión + [ADR-0005](../adr/0005-configuration-and-secrets.md) |

## Atributos de calidad priorizados

Orden de prioridad cuando haya conflicto entre atributos (deriva de las prioridades
que fijó el usuario):

1. **Mantenibilidad** y **testabilidad** (base de todo lo demás).
2. **Simplicidad** (KISS/YAGNI) por encima de flexibilidad especulativa.
3. **Separación de responsabilidades** y **reutilización** (DRY).
4. **Escalabilidad** razonable (el diseño no debe impedir crecer, pero no se
   optimiza prematuramente).

> Nota sobre KISS vs. Clean Architecture: se adopta una arquitectura por capas
> *pragmática*, no una Clean Architecture ceremoniosa, para equilibrar
> separación de responsabilidades con simplicidad. Justificación en
> [ADR-0003](../adr/0003-pragmatic-layered-architecture.md).

## Presupuestos y umbrales

| Métrica | Umbral objetivo |
|---|---|
| Cobertura de pruebas (capa `domain`) | ≥ 90 % |
| Cobertura global | ≥ 80 % |
| Tiempo de `make check` | < 60 s en equipo de desarrollo |
| Complejidad ciclomática por función | ≤ 10 (guía, no dogma) |
| Advertencias de `mypy --strict` | 0 |
| Errores de `ruff` | 0 |
