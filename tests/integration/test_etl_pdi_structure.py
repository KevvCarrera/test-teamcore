"""Validación estructural del ETL de Pentaho/PDI (FR-14…FR-17).

Estos archivos no son código Python: son XML de Pentaho Data Integration.
Aquí se verifica que tengan los pasos/entradas esperados y que el DDL sea SQL
válido. La validación funcional completa (abrir y ejecutar en Spoon/Kitchen)
la hizo el desarrollador manualmente contra una instalación real de PDI 9.4
(ver etl_pdi/README.md) — estas pruebas automatizadas son la red de seguridad
estructural que sí puede correr sin PDI instalado (docs/testing/test-strategy.md#9).
"""

import sqlite3
from pathlib import Path

import pytest
from lxml import etree

_ETL_DIR = Path(__file__).resolve().parents[2] / "etl_pdi"
_KTR_PATH = _ETL_DIR / "t_load_kpi.ktr"
_KJB_PATH = _ETL_DIR / "j_daily_kpi.kjb"
_DDL_PATH = _ETL_DIR / "sql" / "ddl.sql"


def _parse(path: Path) -> etree._Element:
    root = etree.parse(str(path)).getroot()
    assert root is not None
    return root


def _text(element: etree._Element, tag: str) -> str:
    value = element.findtext(tag)
    assert value is not None, f"falta <{tag}> en {element.tag}"
    return value


def _find_one(root: etree._Element, xpath_expr: str) -> etree._Element:
    results = root.xpath(xpath_expr)
    assert isinstance(results, list) and len(results) == 1, xpath_expr
    element = results[0]
    assert isinstance(element, etree._Element)
    return element


def _step_types(root: etree._Element) -> dict[str, str]:
    return {_text(step, "name"): _text(step, "type") for step in root.findall("step")}


def _entry_types(root: etree._Element) -> dict[str, str]:
    entries = root.find("entries")
    assert entries is not None
    return {_text(entry, "name"): _text(entry, "type") for entry in entries.findall("entry")}


@pytest.mark.integration
def test_ktr_is_well_formed_xml() -> None:
    assert _parse(_KTR_PATH).tag == "transformation"


@pytest.mark.integration
def test_ktr_has_csv_input_reading_the_kpi_csv() -> None:
    root = _parse(_KTR_PATH)
    assert _step_types(root).get("CSV Input") == "CsvInput"

    csv_step = _find_one(root, "//step[name='CSV Input']")
    assert "kpi_por_endpoint_dia.csv" in _text(csv_step, "filename")


@pytest.mark.integration
def test_ktr_has_typing_step() -> None:
    assert _step_types(_parse(_KTR_PATH)).get("Tipificar columnas") == "SelectValues"


@pytest.mark.integration
def test_ktr_typing_step_converts_numeric_columns() -> None:
    root = _parse(_KTR_PATH)
    select_values = _find_one(root, "//step[name='Tipificar columnas']")
    typed_fields = {
        _text(meta, "name"): _text(meta, "type") for meta in select_values.findall(".//meta")
    }
    assert typed_fields["requests_total"] == "Integer"
    assert typed_fields["avg_elapsed_ms"] == "Number"
    assert typed_fields["p90_elapsed_ms"] == "Number"


@pytest.mark.integration
def test_ktr_has_filter_rows_with_sanity_conditions() -> None:
    root = _parse(_KTR_PATH)
    assert _step_types(root).get("Filter Rows") == "FilterRows"

    filter_step = _find_one(root, "//step[name='Filter Rows']")
    left_values = {node.text for node in filter_step.findall(".//condition/leftvalue")}
    assert "requests_total" in left_values
    assert "p90_elapsed_ms" in left_values


@pytest.mark.integration
def test_ktr_has_two_table_outputs_with_truncate() -> None:
    root = _parse(_KTR_PATH)
    steps = _step_types(root)
    table_outputs = [name for name, type_ in steps.items() if type_ == "TableOutput"]
    assert len(table_outputs) == 2

    tables = set()
    for name in table_outputs:
        step = _find_one(root, f"//step[name='{name}']")
        assert _text(step, "truncate") == "Y"
        tables.add(_text(step, "table"))

    assert tables == {"stg_kpi_endpoint_dia", "fct_kpi_endpoint_dia"}


@pytest.mark.integration
def test_ktr_hops_connect_filter_rows_to_both_table_outputs() -> None:
    root = _parse(_KTR_PATH)
    hops_from_filter = [
        _text(hop, "to")
        for hop in root.findall("order/hop")
        if hop.findtext("from") == "Filter Rows"
    ]
    assert set(hops_from_filter) == {"Staging (Truncate)", "Fact (Truncate)"}


@pytest.mark.integration
def test_kjb_is_well_formed_xml() -> None:
    assert _parse(_KJB_PATH).tag == "job"


@pytest.mark.integration
def test_kjb_executes_the_transformation() -> None:
    root = _parse(_KJB_PATH)
    entries = _entry_types(root)
    trans_entries = [name for name, type_ in entries.items() if type_ == "TRANS"]
    assert len(trans_entries) == 1

    trans_entry = _find_one(root, f"//entry[name='{trans_entries[0]}']")
    assert "t_load_kpi.ktr" in _text(trans_entry, "filename")


@pytest.mark.integration
def test_kjb_has_a_verification_step() -> None:
    entries = _entry_types(_parse(_KJB_PATH))
    assert "SQL" in entries.values() or "TABLE_EXISTS" in entries.values()


@pytest.mark.integration
def test_kjb_logs_success_and_failure() -> None:
    root = _parse(_KJB_PATH)
    entries = _entry_types(root)
    log_entries = [name for name, type_ in entries.items() if type_ == "WRITE_TO_LOG"]
    assert len(log_entries) == 2

    levels = {
        name: _text(_find_one(root, f"//entry[name='{name}']"), "loglevel") for name in log_entries
    }
    assert "Error" in levels.values()
    assert "Basic" in levels.values()


@pytest.mark.integration
def test_kjb_has_a_failure_path_independent_of_the_success_path() -> None:
    root = _parse(_KJB_PATH)
    failure_hops = [hop for hop in root.findall("hops/hop") if hop.findtext("evaluation") == "N"]
    assert failure_hops, "Debe existir al menos un hop de fallo (evaluation=N)"


@pytest.mark.integration
def test_ddl_is_valid_sql_and_creates_the_contract_tables() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(_DDL_PATH.read_text(encoding="utf-8"))
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        connection.close()

    assert {"stg_kpi_endpoint_dia", "fct_kpi_endpoint_dia", "etl_log"} <= tables


@pytest.mark.integration
def test_ddl_is_idempotent_to_reexecute() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        script = _DDL_PATH.read_text(encoding="utf-8")
        connection.executescript(script)
        connection.executescript(script)  # no debe fallar la segunda vez
    finally:
        connection.close()


@pytest.mark.integration
def test_support_files_exist() -> None:
    assert (_ETL_DIR / "config" / "kettle.properties.example").exists()
    assert (_ETL_DIR / "README.md").exists()


@pytest.mark.integration
def test_kettle_properties_example_has_no_active_credential_assignments() -> None:
    content = (_ETL_DIR / "config" / "kettle.properties.example").read_text(encoding="utf-8")
    active_lines = [
        line for line in content.splitlines() if line.strip() and not line.strip().startswith("#")
    ]
    credential_assignments = [
        line for line in active_lines if "password" in line.lower() or "secret" in line.lower()
    ]
    assert not credential_assignments
