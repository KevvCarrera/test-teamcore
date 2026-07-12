"""Pruebas de la jerarquía de excepciones de dominio (FR-11, NFR-03)."""

from pathlib import Path

import pytest

from teamcore_http_kpi.domain.errors import (
    AccessForbiddenError,
    ConfigError,
    DataInputError,
    HttpTaskError,
    InputFileNotFoundError,
    MalformedRecordError,
    ReportError,
    TeamcoreError,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "exc_type",
    [ConfigError, HttpTaskError, DataInputError, ReportError],
)
def test_direct_subclasses_inherit_from_teamcore_error(exc_type: type[Exception]) -> None:
    assert issubclass(exc_type, TeamcoreError)


@pytest.mark.unit
def test_access_forbidden_error_is_http_task_error() -> None:
    assert issubclass(AccessForbiddenError, HttpTaskError)


@pytest.mark.unit
def test_input_file_not_found_error_is_data_input_error() -> None:
    assert issubclass(InputFileNotFoundError, DataInputError)


@pytest.mark.unit
def test_malformed_record_error_is_data_input_error() -> None:
    assert issubclass(MalformedRecordError, DataInputError)


@pytest.mark.unit
def test_input_file_not_found_error_message_includes_path() -> None:
    path = Path("out/datos.jsonl")
    err = InputFileNotFoundError(path)
    assert "out" in str(err)
    assert err.path == path


@pytest.mark.unit
def test_malformed_record_error_message_includes_line_number() -> None:
    err = MalformedRecordError(7, "JSON inválido")
    assert "7" in str(err)
    assert err.line_number == 7
    assert err.reason == "JSON inválido"
