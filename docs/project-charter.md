# Project Charter

| Campo | Valor |
|---|---|
| Proyecto | Cliente HTTP Automatizado + Procesamiento de KPIs + Reporte HTML |
| Origen | Test técnico (`spec/Test Tecnico.md`) |
| Metodología | Spec Driven Development (SDD) |
| Estado | Aprobado (especificación) |
| Versión | 1.0 |

## 1. Contexto y propósito

El documento fuente plantea un ejercicio de ingeniería que simula tareas reales
de **scraping y consumo de APIs** y su posterior **procesamiento analítico**. El
objetivo del proyecto es entregar una solución en Python que demuestre dominio de:

- interacción robusta con endpoints HTTP (autenticación, sesiones, cookies,
  restricciones, redirecciones, formatos JSON/XML/HTML, formularios);
- ingeniería de datos (generación reproducible de una bitácora y cálculo de KPIs);
- visualización (reporte HTML con métricas y gráficos);
- prácticas de ingeniería de software de nivel producción (arquitectura, pruebas,
  documentación, trazabilidad).

## 2. Objetivos y criterios de éxito

| # | Objetivo | Criterio de éxito medible |
|---|---|---|
| O1 | Implementar los 6 escenarios HTTP | Cada escenario ejecuta correctamente y produce los artefactos exigidos (`datos.json`, `datos.xml`, `titulo.html`) |
| O2 | Generar bitácora sintética reproducible | `generar_datos.py` produce 500 registros deterministas por semilla, conformes al esquema |
| O3 | Calcular KPIs diarios por endpoint | `calcular_kpi.py` produce el CSV conforme al contrato, con p90 vía `numpy.percentile` |
| O4 | Producir reporte HTML | `generar_reporte.py` genera un HTML con métricas globales, tabla y 2 gráficos, con alerta por umbral |
| O5 | Calidad de ingeniería | `ruff` + `mypy --strict` + `pytest` en verde; cobertura de dominio ≥ 90 % |
| O6 | Trazabilidad | 100 % de requisitos con FR/NFR, spec, prueba y código enlazados en la RTM |

## 3. Alcance

### En alcance

- **Parte 0 — Cliente HTTP** (6 tareas): autenticación básica, cookies/sesión,
  manejo de 403, extracción JSON/XML/HTML, envío de formulario, redirecciones.
- **Parte 1 — Procesamiento en Python**: `generar_datos.py` (1.1) y
  `calcular_kpi.py` (1.2).
- **Parte 2 — ETL con Pentaho/PDI**: transformación `t_load_kpi.ktr`, job
  `j_daily_kpi.kjb`, carga a SQLite (staging + fact) y verificación con logging —
  ver [ADR-0013](adr/0013-pentaho-pdi-in-scope.md) y [SPEC-005](specs/SPEC-005-etl-pdi.md).
- **Parte 3 — Reporte**: `generar_reporte.py` (reporte HTML con gráficos).
- Documentación, pruebas, arquitectura y tooling de calidad.

### Fuera de alcance

- **Ninguna sección del enunciado queda fuera de alcance.** Todas las partes (0–3)
  se cubren.
- **Límite de la parte PDI:** los ficheros `.ktr`/`.kjb` se autoran fielmente al
  formato de PDI, pero **no se ejecutan/validan en este entorno** (no hay Spoon/
  Kitchen). La validación funcional final la realiza el usuario en su instalación de
  PDI. Ver [ADR-0013](adr/0013-pentaho-pdi-in-scope.md).

## 4. Interesados (stakeholders)

| Rol | Interés |
|---|---|
| Panel evaluador (Teamcore) | Verificar correctitud, claridad, uso de librerías y calidad de ingeniería |
| Operador de PDI (usuario) | Abrir en Spoon y ejecutar/validar el ETL en su instalación |
| Mantenedor futuro | Comprender y extender el sistema a partir de las specs |

## 5. Supuestos

- `httpbin.org` está disponible para las pruebas manuales del cliente HTTP; las
  pruebas automatizadas usan dobles y no dependen de la red.
- Los endpoints de `/html` y `/xml` sirven contenido estático (sin JavaScript),
  por lo que no se requiere un navegador real (ver
  [ADR-0004](adr/0004-http-requests-over-browser-automation.md)).
- Python 3.11+ disponible en el entorno de evaluación.
- Las credenciales `usuario_test` / `clave123` son de prueba y no sensibles.

## 6. Restricciones

- **Librerías de runtime** limitadas a las permitidas por el enunciado
  (ver [NFR-02](requirements/non-functional-requirements.md)).
- **Parámetros de CLI y nombres de archivos** son exactos y no negociables
  (criterio de aceptación).
- El percentil 90 debe calcularse con `numpy.percentile`.

## 7. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Indisponibilidad de httpbin.org | Bloquea prueba manual del cliente HTTP | Pruebas con dobles; runbook documenta alternativa local (`kennethreitz/httpbin` en Docker) |
| Reproducibilidad rota por el reloj | Timestamps no reproducibles entre corridas | La semilla fija todas las decisiones aleatorias; las pruebas inyectan un tiempo de referencia a nivel de función (ver [SPEC-002](specs/SPEC-002-generar-datos.md)) |
| `p90 < avg` en grupos pequeños | Filas descartadas por el Filter Rows del ETL | Documentado como invariante esperado; el Filter Rows de PDI las descarta por diseño ([SPEC-005](specs/SPEC-005-etl-pdi.md)) |
| No poder ejecutar PDI en este entorno | La validación funcional del ETL queda del lado del usuario | Ficheros fieles al formato PDI + DDL + runbook; el usuario valida en Spoon/Kitchen ([ADR-0013](adr/0013-pentaho-pdi-in-scope.md)) |
| Ambigüedad en normalización de endpoints | KPIs mal agrupados | Regla de normalización especificada y probada ([data-contracts.md](contracts/data-contracts.md)) |
| Sobre-ingeniería | Viola KISS/YAGNI | Arquitectura pragmática por capas, justificada en [ADR-0003](adr/0003-pragmatic-layered-architecture.md) |

## 8. Glosario

| Término | Definición |
|---|---|
| **Bitácora** | Archivo `datos.jsonl` con 500 registros que simulan llamadas HTTP |
| **endpoint_base** | Endpoint normalizado (p. ej. `/status/403` → `/status`) |
| **KPI** | Indicador agregado por `(date_utc, endpoint_base)` |
| **p90** | Percentil 90 de `elapsed_ms`, calculado con `numpy.percentile` |
| **Artefacto** | Fichero de salida generado por el sistema |
| **RTM** | Requirements Traceability Matrix (matriz de trazabilidad) |
| **ADR** | Architecture Decision Record |
| **Doble (test double)** | Sustituto de una dependencia real en pruebas (mock/stub) |

## 9. Entregables

Ver el detalle por fase en
[project-plan/roadmap-and-phases.md](project-plan/roadmap-and-phases.md). En
síntesis: especificación (esta fase) → implementación por componente → verificación
→ documentación de cierre.
