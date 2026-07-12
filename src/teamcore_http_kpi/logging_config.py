"""Configuración de logging estructurado (ver docs/adr/0006-logging-strategy.md).

Los logs van a `stderr`; los artefactos de datos van a ficheros o `stdout` según
el script. El nivel y el formato se fijan una única vez, en el *composition
root* de cada CLI, mediante `setup_logging(...)`. Nunca se usa `print()` para
diagnóstico ni se registran credenciales.
"""

import logging
import sys
from typing import Literal

LogFormat = Literal["text", "json"]

_TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class _JsonFormatter(logging.Formatter):
    """Formateador JSON básico (una línea por registro de log)."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: int = logging.INFO, fmt: LogFormat = "text") -> None:
    """Configura el logger raíz una única vez (composition root).

    Args:
        level: nivel mínimo de log (por defecto `logging.INFO`).
        fmt: `"text"` (legible) o `"json"` (una línea JSON por registro).
    """
    handler = logging.StreamHandler(stream=sys.stderr)
    formatter: logging.Formatter = (
        _JsonFormatter() if fmt == "json" else logging.Formatter(_TEXT_FORMAT)
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
