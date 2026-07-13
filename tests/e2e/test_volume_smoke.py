"""Prueba de volumen/rendimiento (NFR-13): ~10^5 registros en segundos.

No es una prueba de carga exhaustiva ni un benchmark preciso — es un *smoke
test* de que la ruta feliz de `generar_datos.py → calcular_kpi.py` no
degrada a un comportamiento cuadrático o similar al escalar de 500 a 100 000
registros. El umbral de tiempo es generoso a propósito para no volverse
inestable en máquinas más lentas que la de desarrollo (donde tarda ~5-6 s).
"""

import time
from pathlib import Path

import pytest

from teamcore_http_kpi.cli._common import EXIT_OK
from teamcore_http_kpi.cli.calcular_kpi import main as calcular_kpi_main
from teamcore_http_kpi.cli.generar_datos import main as generar_datos_main

_N_REGISTROS = 100_000
_TIMEOUT_SECONDS = 30.0


@pytest.mark.e2e
def test_volume_smoke_100k_registros_en_segundos(tmp_out: Path) -> None:
    bitacora = tmp_out / "datos.jsonl"
    kpi_csv = tmp_out / "kpi_por_endpoint_dia.csv"

    start = time.perf_counter()
    exit_gen = generar_datos_main(
        ["--n_registros", str(_N_REGISTROS), "--salida", str(bitacora), "--seed", "42"]
    )
    exit_kpi = calcular_kpi_main(["--input", str(bitacora), "--output", str(kpi_csv)])
    elapsed = time.perf_counter() - start

    assert exit_gen == EXIT_OK
    assert exit_kpi == EXIT_OK
    assert elapsed < _TIMEOUT_SECONDS, f"tardó {elapsed:.1f}s (límite {_TIMEOUT_SECONDS}s)"

    assert len(bitacora.read_text(encoding="utf-8").splitlines()) == _N_REGISTROS
    kpi_lines = kpi_csv.read_text(encoding="utf-8").splitlines()
    assert len(kpi_lines) > 1  # encabezado + al menos una fila agregada
    total_requests = sum(int(line.split(",")[2]) for line in kpi_lines[1:])
    assert total_requests == _N_REGISTROS
