"""Errores propios del proyecto, organizados por tipo de problema."""

from pathlib import Path


class TeamcoreError(Exception):
    """La raíz de todos los errores propios del proyecto."""


class ConfigError(TeamcoreError):
    """Un parámetro de configuración o de CLI no es válido (exit code 2)."""


class HttpTaskError(TeamcoreError):
    """Un escenario del cliente HTTP falló de forma no recuperable (exit code 3)."""


class AccessForbiddenError(HttpTaskError):
    """Se recibió 403 y se agotaron los reintentos configurados."""


class DataInputError(TeamcoreError):
    """Algo falló al leer los datos de entrada: no existen o son inválidos (exit code 1)."""


class InputFileNotFoundError(DataInputError):
    """El archivo de entrada no existe en la ruta indicada."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"No se encontró el archivo de entrada: {path}")
        self.path = path


class MalformedRecordError(DataInputError):
    """Una línea del JSONL no se pudo interpretar; se guarda el número de línea."""

    def __init__(self, line_number: int, reason: str) -> None:
        super().__init__(f"Línea {line_number} inválida: {reason}")
        self.line_number = line_number
        self.reason = reason


class ReportError(TeamcoreError):
    """Algo falló al construir el reporte HTML."""
