# Runbook de Operación

Guía práctica para ejecutar, diagnosticar y resolver problemas. Orientado a Windows
(PowerShell), con equivalentes POSIX.

## 1. Requisitos previos

- Python **3.11+** (`python --version`).
- Acceso a `httpbin.org` solo para el cliente HTTP en vivo (opcional).

## 2. Instalación

```powershell
# PowerShell (Windows)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

```bash
# POSIX
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

> No hay `.env`: la configuración (URL base, credenciales de prueba, datos del
> formulario, timeout/reintentos) vive como constantes en `config.py`.

## 3. Ejecución

| Acción | Comando |
|---|---|
| Cliente HTTP | `python cliente_http.py` |
| Generar datos | `python generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42` |
| Calcular KPIs | `python calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv` |
| Reporte HTML | `python generar_reporte.py --input out/kpi_por_endpoint_dia.csv --output out/report/kpi_diario.html --umbral_p90 300` |
| Pipeline (make) | `make pipeline` |
| ETL PDI (job) | `kitchen.sh -file=etl_pdi/j_daily_kpi.kjb` (o abrir en Spoon) |

> En Windows sin `make`: ejecutar los tres comandos de datos en orden, o usar Git
> Bash. Los shims raíz permiten `python <script>.py ...` en cualquier plataforma.

## 4. Calidad

```powershell
ruff check src tests      # lint
mypy                      # tipos (estricto)
pytest                    # pruebas sin red
pytest -m network         # incluye humo contra httpbin real
pytest --cov              # cobertura
```

## 5. Configuración (constantes en `config.py`)

No hay variables de entorno ni `.env`. La configuración son constantes tipadas en
`config.py` con los valores del enunciado: URL base (`https://httpbin.org`),
credenciales de prueba (`usuario_test`/`clave123`), datos del formulario, timeout,
reintentos y backoff. Para cambiar un valor, se edita `config.py` o se construye
`Settings(...)` en pruebas. El nivel de log se ajusta en el *composition root*
(`setup_logging(level=...)`).

## 6. Códigos de salida

| Código | Significado |
|---|---|
| `0` | Éxito |
| `1` | Error de datos/entrada (fichero inexistente, línea corrupta) |
| `2` | Error de configuración/uso (parámetro inválido) |
| `3` | Error de red/HTTP no recuperable |

## 7. Troubleshooting

| Síntoma | Causa probable | Acción |
|---|---|---|
| `InputFileNotFoundError` | Ruta de `--input` incorrecta o pipeline no ejecutado | Verificar que existe `out/datos.jsonl`; correr `generar_datos.py` primero |
| `WARNING: línea N inválida` | JSONL corrupto | Se descarta esa línea y se continúa; corregir la línea N si se desea incluirla |
| Cliente HTTP se cuelga | Timeout/red | Revisar el `timeout` en `config.py`; verificar conectividad |
| `403` constante | Comportamiento esperado de `/status/403` | Es el escenario FR-03; se registra y reintenta por diseño |
| httpbin.org caído | Servicio externo | Levantar httpbin local: `docker run -p 80:80 kennethreitz/httpbin` y ajustar `base_url` en `config.py` a `http://localhost` |
| Reporte sin gráficos | Backend de matplotlib | El proyecto fuerza backend `Agg`; verificar que `--output` es escribible |
| `mypy` falla en pandas | Stubs incompletos | Ya se ignoran vía overrides en `pyproject.toml` |

## 8. Alternativa: httpbin local (sin internet)

```bash
docker run -d -p 8080:80 kennethreitz/httpbin
# config.py → base_url = "http://localhost:8080"
```

## 9. ETL con Pentaho/PDI

El artefacto `out/kpi_por_endpoint_dia.csv` es la **entrada** del ETL de PDI
([SPEC-005](../specs/SPEC-005-etl-pdi.md)). Ejecución:

```bash
# 1. Preparar la base y las tablas (una vez)
sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql

# 2. Configurar la conexión
cp etl_pdi/config/kettle.properties.example ~/.kettle/kettle.properties  # o ajustar ruta

# 3. Ejecutar el job (línea de comandos) o abrir en Spoon
kitchen.sh -file=etl_pdi/j_daily_kpi.kjb -level=Basic     # Linux/macOS
Kitchen.bat /file:etl_pdi\j_daily_kpi.kjb /level:Basic    # Windows

# 4. Verificar la carga
sqlite3 etl_pdi/db/kpi.sqlite "SELECT COUNT(*) FROM fct_kpi_endpoint_dia;"
```

> Los ficheros `.ktr`/`.kjb` se entregan estructuralmente correctos pero **no se
> ejecutaron/validaron** en el entorno de desarrollo (sin Spoon/Kitchen). La
> validación funcional se realiza aquí, en tu instalación de PDI. No modificar el
> esquema del CSV sin seguir el
> [versionado del contrato](../contracts/data-contracts.md#versionado).
