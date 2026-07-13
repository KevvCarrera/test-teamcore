"""Pruebas de `logging_config.py` (NFR-10): destino, formato, nivel y secretos.

Ver ADR-0006 para la decisión de diseño que estas pruebas verifican.
"""

import json
import logging
import sys
from collections.abc import Iterator

import pytest

from teamcore_http_kpi.logging_config import setup_logging


@pytest.fixture(autouse=True)
def _restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    yield
    root.handlers.clear()
    root.handlers.extend(original_handlers)
    root.setLevel(original_level)


@pytest.mark.unit
def test_setup_logging_sends_records_to_stderr() -> None:
    setup_logging()
    root = logging.getLogger()

    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0], logging.StreamHandler)
    assert root.handlers[0].stream is sys.stderr


@pytest.mark.unit
def test_setup_logging_defaults_to_info_level() -> None:
    setup_logging()
    assert logging.getLogger().level == logging.INFO


@pytest.mark.unit
def test_setup_logging_respects_explicit_level() -> None:
    setup_logging(level=logging.WARNING)

    assert logging.getLogger().level == logging.WARNING


@pytest.mark.unit
def test_text_format_is_human_readable(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging(fmt="text")
    logging.getLogger("teamcore_http_kpi.test").warning("mensaje de prueba")

    output = capsys.readouterr().err
    assert "WARNING" in output
    assert "mensaje de prueba" in output


@pytest.mark.unit
def test_json_format_produces_one_valid_json_object_per_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup_logging(fmt="json")
    logging.getLogger("teamcore_http_kpi.test").error("fallo controlado")

    output = capsys.readouterr().err.strip()
    payload = json.loads(output)

    assert payload["level"] == "ERROR"
    assert payload["message"] == "fallo controlado"
    assert payload["logger"] == "teamcore_http_kpi.test"


@pytest.mark.unit
def test_level_below_threshold_is_filtered_out(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging(level=logging.WARNING)
    logging.getLogger("teamcore_http_kpi.test").info("no debería aparecer")

    assert capsys.readouterr().err == ""


@pytest.mark.unit
def test_calling_setup_logging_twice_does_not_duplicate_handlers() -> None:
    setup_logging()
    setup_logging()

    assert len(logging.getLogger().handlers) == 1
