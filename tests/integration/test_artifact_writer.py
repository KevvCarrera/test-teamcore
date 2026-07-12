"""Pruebas de integración de `FileSystemArtifactWriter` (FR-04, FR-05, FR-06)."""

import json
from pathlib import Path

import pytest

from teamcore_http_kpi.infrastructure.io.artifact_writer import FileSystemArtifactWriter


@pytest.mark.integration
def test_write_json_creates_parent_dir_and_valid_json(tmp_out: Path) -> None:
    destination = tmp_out / "nested" / "datos.json"
    payload = {"url": "https://httpbin.org/get", "args": {}}

    FileSystemArtifactWriter().write_json(payload, destination)

    assert json.loads(destination.read_text(encoding="utf-8")) == payload


@pytest.mark.integration
def test_write_json_preserves_non_ascii_characters(tmp_out: Path) -> None:
    destination = tmp_out / "datos.json"
    FileSystemArtifactWriter().write_json({"mensaje": "Pérez"}, destination)

    assert "Pérez" in destination.read_text(encoding="utf-8")


@pytest.mark.integration
def test_write_xml_writes_bytes_verbatim(tmp_out: Path) -> None:
    destination = tmp_out / "nested" / "datos.xml"
    xml_bytes = b"<?xml version='1.0'?><root><item>1</item></root>"

    FileSystemArtifactWriter().write_xml(xml_bytes, destination)

    assert destination.read_bytes() == xml_bytes


@pytest.mark.integration
def test_write_text_writes_utf8(tmp_out: Path) -> None:
    destination = tmp_out / "nested" / "titulo.html"
    FileSystemArtifactWriter().write_text("<title>Título de prueba</title>", destination)

    assert destination.read_text(encoding="utf-8") == "<title>Título de prueba</title>"


@pytest.mark.integration
def test_writers_overwrite_existing_file(tmp_out: Path) -> None:
    destination = tmp_out / "titulo.html"
    writer = FileSystemArtifactWriter()

    writer.write_text("primero, con más texto", destination)
    writer.write_text("segundo", destination)

    assert destination.read_text(encoding="utf-8") == "segundo"
