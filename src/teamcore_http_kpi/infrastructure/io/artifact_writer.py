"""`FileSystemArtifactWriter`: guarda `datos.json`, `datos.xml` y `titulo.html` en disco."""

import json
from pathlib import Path
from typing import Any


class FileSystemArtifactWriter:
    """No sabe de dónde vienen los datos, solo cómo guardarlos."""

    def write_json(self, payload: Any, destination: Path) -> None:
        """Guarda `payload` como JSON legible (con sangría) en `destination`."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def write_xml(self, xml_bytes: bytes, destination: Path) -> None:
        """Guarda `xml_bytes`, ya serializado, tal cual en `destination`."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(xml_bytes)

    def write_text(self, text: str, destination: Path) -> None:
        """Guarda `text` como UTF-8 en `destination`."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
