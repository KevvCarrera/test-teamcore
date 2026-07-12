"""Orquestación de los 6 escenarios del cliente HTTP.

`run_all` los ejecuta en orden, todos sobre la misma sesión HTTP. Si uno
falla, se registra y se sigue con el siguiente — nadie se queda esperando a
que los 6 salgan perfectos para saber cómo les fue a los demás.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from teamcore_http_kpi.application.ports import ArtifactWriter, HttpPort
from teamcore_http_kpi.config import Settings
from teamcore_http_kpi.domain.errors import HttpTaskError
from teamcore_http_kpi.infrastructure.http import tasks

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskResult:
    """El resultado de un escenario: su nombre, si salió bien, y el detalle."""

    name: str
    ok: bool
    detail: str


def run_all(
    http: HttpPort, writer: ArtifactWriter, settings: Settings, out_dir: Path
) -> list[TaskResult]:
    """Ejecuta los 6 escenarios y devuelve un resultado por cada uno, en orden."""
    scenarios: tuple[tuple[str, Callable[[], str]], ...] = (
        ("Autenticación básica", lambda: tasks.basic_auth(http, settings)),
        ("Cookies y sesión", lambda: tasks.set_and_get_cookies(http)),
        ("Restricción de acceso (403)", lambda: tasks.simulate_forbidden(http)),
        ("Extracción JSON", lambda: tasks.extract_json(http, writer, out_dir)),
        ("Extracción XML", lambda: tasks.extract_xml(http, writer, out_dir)),
        ("Extracción de título HTML", lambda: tasks.extract_html_title(http, writer, out_dir)),
        ("Envío de formulario", lambda: tasks.submit_form(http, settings)),
        ("Redirección", lambda: tasks.follow_redirect(http)),
    )

    results: list[TaskResult] = []
    for name, scenario in scenarios:
        try:
            detail = scenario()
            results.append(TaskResult(name=name, ok=True, detail=detail))
        except HttpTaskError as exc:
            logger.warning("Escenario %r falló: %s", name, exc)
            results.append(TaskResult(name=name, ok=False, detail=str(exc)))
    return results
