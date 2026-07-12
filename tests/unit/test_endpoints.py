"""Pruebas de normalización de endpoints (FR-10).

Tabla de casos según docs/contracts/data-contracts.md#normalización-de-endpoints.
"""

import pytest

from teamcore_http_kpi.domain.endpoints import normalize_endpoint


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/get", "/get"),
        ("/post", "/post"),
        ("/status/403", "/status"),
        ("/basic-auth", "/basic-auth"),
        ("/basic-auth/usuario_test/clave123", "/basic-auth"),
        ("/cookies", "/cookies"),
        ("/xml", "/xml"),
        ("/html", "/html"),
        ("/status/500", "/status"),
        ("/cookies/set", "/cookies"),
        ("/cookies/set?session=activa", "/cookies"),
        ("/get/", "/get"),
        ("/get#fragmento", "/get"),
    ],
)
def test_normalize_endpoint_table(raw: str, expected: str) -> None:
    assert normalize_endpoint(raw) == expected


@pytest.mark.unit
@pytest.mark.parametrize("raw", ["", "/"])
def test_normalize_endpoint_rejects_empty(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_endpoint(raw)
