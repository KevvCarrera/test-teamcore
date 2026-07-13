"""Pruebas e2e de `generar_datos.py` (FR-09, FR-11) sobre la CLI real.

Ejercita `main()` en proceso (sin subprocess), tal como sugiere
docs/testing/test-strategy.md.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from teamcore_http_kpi.cli._common import EXIT_CONFIG_ERROR, EXIT_DATA_ERROR, EXIT_OK
from teamcore_http_kpi.cli.generar_datos import main

_SCHEMA_FIELDS = {"timestamp_utc", "endpoint", "status_code", "elapsed_ms", "parse_result"}
_CATALOG = {"/get", "/post", "/status/403", "/basic-auth", "/cookies", "/xml", "/html"}


@pytest.mark.e2e
def test_generates_exact_count_and_valid_schema(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    exit_code = main(["--n_registros", "50", "--salida", str(destination), "--seed", "42"])

    assert exit_code == EXIT_OK
    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 50
    for line in lines:
        record = json.loads(line)
        assert set(record.keys()) == _SCHEMA_FIELDS
        assert record["endpoint"] in _CATALOG
        assert 50.0 <= record["elapsed_ms"] <= 800.0
        assert record["parse_result"] in {"ok", "error"}


@pytest.mark.e2e
def test_status_403_rule_holds_end_to_end(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    main(["--n_registros", "200", "--salida", str(destination), "--seed", "7"])

    for line in destination.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["endpoint"] == "/status/403":
            assert record["status_code"] == 403


@pytest.mark.e2e
def test_rerun_overwrites_instead_of_appending(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    main(["--n_registros", "30", "--salida", str(destination), "--seed", "1"])
    main(["--n_registros", "10", "--salida", str(destination), "--seed", "1"])

    assert len(destination.read_text(encoding="utf-8").splitlines()) == 10


class _FrozenClock:
    """Reemplaza a `datetime` dentro de `application.generate_data` en esta prueba.

    La CLI no expone `--ref-utc` (el enunciado no lo pide), así que usa
    `datetime.now(UTC)` internamente. Sin fijar el reloj, dos corridas
    "iguales" pueden diferir en el último segundo de `timestamp_utc` si el
    reloj real avanza entre una llamada y la otra — por eso la prueba de
    idempotencia real necesita congelarlo (regla del proyecto: ninguna
    prueba depende del reloj real).
    """

    @staticmethod
    def now(tz: object = None) -> datetime:
        return datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)


@pytest.mark.e2e
def test_rerun_with_same_params_is_byte_identical(
    tmp_out: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("teamcore_http_kpi.application.generate_data.datetime", _FrozenClock)
    destination = tmp_out / "datos.jsonl"

    main(["--n_registros", "40", "--salida", str(destination), "--seed", "5"])
    first_run = destination.read_text(encoding="utf-8")

    main(["--n_registros", "40", "--salida", str(destination), "--seed", "5"])
    second_run = destination.read_text(encoding="utf-8")

    assert first_run == second_run


@pytest.mark.e2e
def test_creates_missing_output_directory(tmp_out: Path) -> None:
    destination = tmp_out / "nested" / "dir" / "datos.jsonl"
    exit_code = main(["--n_registros", "5", "--salida", str(destination), "--seed", "1"])

    assert exit_code == EXIT_OK
    assert destination.exists()


@pytest.mark.e2e
def test_write_failure_is_a_data_error(tmp_out: Path) -> None:
    blocker = tmp_out / "blocker"
    blocker.write_text("esto es un archivo, no una carpeta", encoding="utf-8")
    destination = blocker / "sub" / "datos.jsonl"

    exit_code = main(["--n_registros", "5", "--salida", str(destination), "--seed", "1"])

    assert exit_code == EXIT_DATA_ERROR


@pytest.mark.e2e
def test_zero_registros_is_a_config_error(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    exit_code = main(["--n_registros", "0", "--salida", str(destination), "--seed", "1"])

    assert exit_code == EXIT_CONFIG_ERROR
    assert not destination.exists()


@pytest.mark.e2e
def test_negative_registros_is_a_config_error(tmp_out: Path) -> None:
    destination = tmp_out / "datos.jsonl"
    exit_code = main(["--n_registros", "-5", "--salida", str(destination), "--seed", "1"])

    assert exit_code == EXIT_CONFIG_ERROR


@pytest.mark.e2e
def test_default_arguments_use_500_and_seed_42(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main([])

    assert exit_code == EXIT_OK
    default_output = tmp_path / "out" / "datos.jsonl"
    assert len(default_output.read_text(encoding="utf-8").splitlines()) == 500
