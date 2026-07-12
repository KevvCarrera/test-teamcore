"""Jerarquía de excepciones de dominio (FR-11, NFR-03).

Ver docs/architecture/component-model.md#5-jerarquía-de-errores-resumen y
docs/adr/0007-error-handling-retries-idempotency.md. Prohibido `except:`
desnudo o silenciar excepciones en el resto del código: todo error se maneja
a través de un tipo concreto de esta jerarquía.
"""

from pathlib import Path


class TeamcoreError(Exception):
    """Excepción base de todos los errores propios del proyecto."""


class ConfigError(TeamcoreError):
    """Configuración o parámetros de CLI inválidos (fail fast, exit code 2)."""


class HttpTaskError(TeamcoreError):
    """Fallo no recuperable en un escenario del cliente HTTP (exit code 3)."""


class AccessForbiddenError(HttpTaskError):
    """Se agotaron los reintentos tras recibir 403 en un escenario (FR-03)."""


class DataInputError(TeamcoreError):
    """Error de entrada de datos: E/S o contenido inválido (exit code 1)."""


class InputFileNotFoundError(DataInputError):
    """El fichero de entrada indicado no existe."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"No se encontró el archivo de entrada: {path}")
        self.path = path


class MalformedRecordError(DataInputError):
    """Una línea del JSONL de entrada no es válida (se reporta con su número)."""

    def __init__(self, line_number: int, reason: str) -> None:
        super().__init__(f"Línea {line_number} inválida: {reason}")
        self.line_number = line_number
        self.reason = reason


class ReportError(TeamcoreError):
    """Fallo al construir el reporte HTML (FR-13)."""
