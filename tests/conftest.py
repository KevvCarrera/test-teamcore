"""Fixtures compartidas por la suite (ver docs/testing/test-strategy.md).

Sin estado global; cada test es independiente y determinista.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.fixture
def tmp_out(tmp_path: Path) -> Iterator[Path]:
    """Directorio temporal de salida para artefactos generados en pruebas."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    yield out_dir


@pytest.fixture
def seed() -> int:
    """Semilla determinista por defecto para pruebas de generación."""
    return 42


@pytest.fixture
def frozen_ref_utc() -> datetime:
    """Instante UTC de referencia fijo, inyectado a nivel de función de dominio."""
    return datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)
