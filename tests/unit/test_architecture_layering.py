"""Prueba de arquitectura: `domain` no debe importar librerías de E/S.

Verifica la Regla de Dependencia (docs/architecture/architecture-overview.md
§3): ninguna flecha entra a `domain`. Si un módulo de dominio importa
`requests`, `pandas`, `matplotlib`, `bs4`, `lxml` o `argparse`, esta prueba
falla.
"""

import ast
from pathlib import Path

import pytest

_FORBIDDEN_ROOTS = {"requests", "pandas", "matplotlib", "bs4", "lxml", "argparse"}
_DOMAIN_DIR = Path(__file__).resolve().parents[2] / "src" / "teamcore_http_kpi" / "domain"


def _imported_roots(source: str) -> set[str]:
    """Devuelve los nombres raíz de todos los módulos importados en `source`."""
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.unit
def test_domain_does_not_import_infrastructure_libraries() -> None:
    """Ningún módulo de `domain` importa librerías de E/S, red o CLI."""
    domain_files = sorted(_DOMAIN_DIR.glob("*.py"))
    assert domain_files, f"No se encontraron módulos de dominio en {_DOMAIN_DIR}"

    violations: dict[str, set[str]] = {}
    for path in domain_files:
        forbidden = _imported_roots(path.read_text(encoding="utf-8")) & _FORBIDDEN_ROOTS
        if forbidden:
            violations[path.name] = forbidden

    assert not violations, f"Módulos de dominio con imports prohibidos: {violations}"
