# ADR-0012 · Frontera de librerías permitidas

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El enunciado limita las librerías: «requests, selenium, playwright, beautifulsoup4,
lxml, json, csv» para el cliente HTTP, y «matplotlib y pandas son suficientes» (más
`numpy` para el p90) en las partes de datos/reporte. Hay que distinguir dependencias
de *runtime* (entregable) de las de *desarrollo* (tooling).

## Decisión

Definir dos conjuntos explícitos:

**Runtime (entregable)** — solo estas, dentro de lo permitido:
`requests`, `beautifulsoup4`, `lxml`, `numpy`, `pandas`, `matplotlib` + stdlib
(`json`, `csv`, `datetime`, `argparse`, `pathlib`, `logging`, `dataclasses`,
`typing`, `urllib`). `selenium`/`playwright` quedan permitidas pero **sin usar**
(ver [ADR-0004](0004-http-requests-over-browser-automation.md)).

**Desarrollo (no entregable)** — no forman parte del runtime:
`pytest`, `pytest-cov`, `responses`, `ruff`, `mypy`, `types-requests`.

Reglas:
- Añadir cualquier dependencia de **runtime** nueva exige un ADR.
- El código de `domain` no importa librerías de E/S (solo stdlib y `numpy` para
  cálculo).
- Se documenta el mapeo librería → dónde se usa.

| Librería | Ámbito | Uso |
|---|---|---|
| requests | runtime | Cliente HTTP (FR-01…FR-08) |
| beautifulsoup4 / lxml | runtime | Parseo HTML/XML (FR-05, FR-06) |
| numpy | runtime | Percentil 90 (FR-10) |
| pandas | runtime | Carga CSV en reporte (FR-13) |
| matplotlib | runtime | Gráficos (FR-13) |
| pytest/responses/ruff/mypy | dev | Pruebas y calidad |

## Consecuencias

- (+) Cumplimiento verificable de la restricción del enunciado.
- (+) Separación limpia entre lo entregable y el tooling.
- (−) El evaluador podría esperar ver Selenium/Playwright; se explicita el porqué
  en ADR-0004 para evitar malentendidos.

## Alternativas consideradas

- **Tratar el tooling como "no permitido":** rechazado; pruebas y linters no son
  parte del runtime y son estándar de la industria.
