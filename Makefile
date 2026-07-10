# Atajos de desarrollo. En Windows pueden ejecutarse vía Git Bash o traducirse
# a los comandos equivalentes (ver docs/runbook/operations-runbook.md).
.DEFAULT_GOAL := help
PY ?= python

.PHONY: help setup lint format type test test-network cov check \
        run-http run-datos run-kpi run-reporte pipeline etl-init etl-run clean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Crea entorno e instala en modo editable con extras de desarrollo
	$(PY) -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

lint: ## Linter (ruff)
	ruff check src tests

format: ## Formatea el código (ruff format)
	ruff format src tests

type: ## Verificación de tipos (mypy --strict)
	mypy

test: ## Pruebas sin red (por defecto)
	pytest

test-network: ## Incluye pruebas marcadas @network (requieren httpbin.org)
	pytest -m network

cov: ## Pruebas con reporte de cobertura
	pytest --cov --cov-report=term-missing

check: lint type test ## Verificación completa (CI local)

run-http: ## Ejecuta el cliente HTTP (Parte 0)
	$(PY) cliente_http.py

run-datos: ## Genera la bitácora sintética (1.1)
	$(PY) generar_datos.py --n_registros 500 --salida out/datos.jsonl --seed 42

run-kpi: ## Calcula KPIs diarios (1.2)
	$(PY) calcular_kpi.py --input out/datos.jsonl --output out/kpi_por_endpoint_dia.csv

run-reporte: ## Genera el reporte HTML (3)
	$(PY) generar_reporte.py --input out/kpi_por_endpoint_dia.csv \
		--output out/report/kpi_diario.html --umbral_p90 300

pipeline: run-datos run-kpi run-reporte ## Ejecuta el pipeline de datos completo

etl-init: ## Crea la base SQLite y las tablas del ETL (Parte 2)
	sqlite3 etl_pdi/db/kpi.sqlite < etl_pdi/sql/ddl.sql

etl-run: ## Ejecuta el job de PDI (requiere Kitchen/PDI instalado)
	kitchen.sh -file=etl_pdi/j_daily_kpi.kjb -level=Basic

clean: ## Limpia artefactos generados y cachés
	rm -rf out .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
