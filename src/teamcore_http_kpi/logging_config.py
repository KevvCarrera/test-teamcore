"""Configuración de logging. Los logs van a `stderr` para no mezclarse con los
datos que cada script escribe en `stdout`/ficheros.
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
