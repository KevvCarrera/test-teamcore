# Flujo de Ejecución y de Datos

> Estado: Aprobado. Describe cómo fluyen los datos entre componentes y artefactos.

## 1. Vista general del pipeline

```mermaid
flowchart LR
    subgraph P0[Parte 0 · Cliente HTTP]
        h[cliente_http] --> hb[(httpbin.org)]
        h --> aj[/out/datos.json/]
        h --> ax[/out/datos.xml/]
        h --> at[/out/titulo.html/]
    end

    subgraph P1[Parte 1 · Datos]
        g[generar_datos] --> jsonl[/out/datos.jsonl/]
        jsonl --> k[calcular_kpi] --> csv[/out/kpi_por_endpoint_dia.csv/]
    end

    subgraph P2[Parte 2 · ETL PDI]
        csv --> job[j_daily_kpi.kjb → t_load_kpi.ktr] --> db[(SQLite stg + fct)]
    end

    subgraph P3[Parte 3 · Reporte]
        csv --> r[generar_reporte] --> html[/out/report/kpi_diario.html/]
    end
```

Las cuatro partes son **independientes y encadenables por ficheros**. El acoplamiento
es por *contrato de datos*, no por código: cada etapa lee la salida de la anterior.
El CSV de KPIs alimenta tanto al reporte (Parte 3) como al ETL de PDI (Parte 2).

## 2. Cliente HTTP — secuencia de los 6 escenarios (FR-01…FR-08)

```mermaid
sequenceDiagram
    autonumber
    participant CLI as cliente_http
    participant UC as http_scenarios
    participant HC as RequestsHttpClient
    participant HB as httpbin.org
    participant AW as ArtifactWriter

    CLI->>UC: run_all(config)
    UC->>HC: get(/basic-auth/.., auth)         %% FR-01
    HC->>HB: GET (Basic Auth)
    HB-->>HC: 200 {authenticated:true}
    UC->>HC: get(/cookies/set?session=activa)  %% FR-02
    UC->>HC: get(/cookies)
    HB-->>HC: {cookies:{session:activa}}
    UC->>HC: get(/status/403) [retry+backoff]  %% FR-03
    HB-->>HC: 403
    UC->>HC: get(/get)                          %% FR-04
    UC->>AW: write_json(datos.json)
    UC->>HC: get(/xml)                           %% FR-05
    UC->>AW: write_xml(datos.xml)
    UC->>HC: get(/html)                           %% FR-06
    UC->>AW: write_text(titulo.html)
    UC->>HC: post(/post, form)                    %% FR-07
    UC->>HC: get(/redirect-to?url=/get)           %% FR-08
    HB-->>HC: 302 → 200 (/get)
    UC-->>CLI: ScenarioReport (OK/errores por tarea)
```

**Notas de diseño**
- Una **única `requests.Session`** se comparte entre escenarios ⇒ FR-02 (cookies)
  funciona de forma natural.
- La política de reintentos (FR-03) vive en el cliente y aplica a errores
  transitorios y a `403` de forma configurable.
- Cada escenario es independiente: un fallo se registra y **no aborta** los demás
  (se reporta un resumen final con estado por tarea).

## 3. Generación de datos (FR-09)

```mermaid
flowchart TB
    args[CLI: --n_registros --salida --seed] --> cfg[valida parámetros]
    cfg --> rng[numpy.random.default_rng seed]
    rng --> gen[domain.generation.generate_records]
    gen --> rec{{BitacoraRecord × N}}
    rec --> wr[JsonlBitacoraRepository.write]
    wr --> out[/out/datos.jsonl/]
```

Determinismo: la `seed` fija todas las decisiones aleatorias ⇒ NFR-07. El ancla
temporal es `datetime.now(UTC)` en ejecución real; en pruebas se inyecta un `ref_utc`
fijo a la función de dominio (no es un flag de CLI) para lograr salidas idénticas.

## 4. Cálculo de KPIs (FR-10)

```mermaid
flowchart TB
    in[/out/datos.jsonl/] --> rd[JsonlBitacoraRepository.read stream]
    rd --> val{línea válida?}
    val -- no --> err[política de error FR-11]
    val -- sí --> norm[domain.endpoints.normalize_endpoint]
    norm --> grp[agrupar por date_utc, endpoint_base]
    grp --> agg[domain.kpi.aggregate\n counts + avg + p90 numpy]
    agg --> wr[CsvKpiRepository.write]
    wr --> csv[/out/kpi_por_endpoint_dia.csv/]
```

- `date_utc` = fecha (YYYY-MM-DD) derivada de `timestamp_utc`.
- `endpoint_base` = normalización (`/status/403` → `/status`).
- `p90_elapsed_ms` = `numpy.percentile(elapsed, 90)` por grupo.

## 5. Reporte HTML (FR-13)

```mermaid
flowchart TB
    in[/out/kpi_por_endpoint_dia.csv/] --> load[pandas.read_csv]
    load --> gm[domain: métricas globales]
    load --> ch1[MatplotlibChartRenderer\n barra requests_total]
    load --> ch2[MatplotlibChartRenderer\n p90 por endpoint]
    gm --> tmpl[HtmlReportRenderer]
    ch1 --> tmpl
    ch2 --> tmpl
    tmpl --> alert{p90 > umbral_p90?}
    alert -- sí --> red[marca en rojo]
    tmpl --> html[/out/report/kpi_diario.html/]
```

Los gráficos se generan con backend `Agg` (sin display) y se **embeben** en el HTML
como PNG en base64 ⇒ un único fichero autocontenido, portable y versionable.

## 6. ETL con PDI (FR-14…FR-17)

```mermaid
flowchart TB
    in[/out/kpi_por_endpoint_dia.csv/] --> ci[CSV Input]
    ci --> ty[Select Values\n tipificación]
    ty --> fr{Filter Rows\n requests_total>0 AND p90>=avg}
    fr -- válidas --> stg[Table Output\n stg_kpi_endpoint_dia\n Truncate]
    fr -- válidas --> fct[Table Output\n fct_kpi_endpoint_dia\n Truncate]
    stg --> db[(SQLite)]
    fct --> db
    db --> ver[Job: verificación SQL + logging]
```

Orquestado por `j_daily_kpi.kjb`. Cargas con *Truncate* ⇒ idempotencia. Detalle en
[SPEC-005](../specs/SPEC-005-etl-pdi.md).

## 7. Contrato entre etapas

| Productor | Artefacto | Consumidor | Contrato |
|---|---|---|---|
| `generar_datos` | `out/datos.jsonl` | `calcular_kpi` | [esquema JSONL](../contracts/data-contracts.md#bitácora-datosjsonl) |
| `calcular_kpi` | `out/kpi_por_endpoint_dia.csv` | `generar_reporte` **y ETL PDI** | [contrato CSV](../contracts/data-contracts.md#kpi-csv) |
| `t_load_kpi.ktr` | SQLite `stg_*` / `fct_*` | Consultas del usuario | [modelo SQLite](../contracts/data-contracts.md#modelo-relacional-sqlite-pdi) |
| `cliente_http` | `datos.json`/`datos.xml`/`titulo.html` | Evaluador | [artefactos HTTP](../contracts/data-contracts.md#artefactos-del-cliente-http) |
