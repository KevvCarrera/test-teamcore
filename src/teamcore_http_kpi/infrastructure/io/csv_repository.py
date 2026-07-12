"""`CsvKpiRepository`: lee y escribe el CSV de estadísticas por endpoint y día."""

import csv
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from teamcore_http_kpi.domain.errors import InputFileNotFoundError
from teamcore_http_kpi.domain.models import KpiRow

_FIELDNAMES = (
    "date_utc",
    "endpoint_base",
    "requests_total",
    "success_2xx",
    "client_4xx",
    "server_5xx",
    "parse_errors",
    "avg_elapsed_ms",
    "p90_elapsed_ms",
)


class CsvKpiRepository:
    """Adaptador de `KpiRepository` sobre CSV UTF-8 con encabezado."""

    def write(self, rows: Sequence[KpiRow], destination: Path) -> None:
        """Escribe encabezado + filas en `destination`, reemplazando el archivo si ya existía.

        No reordena nada: `domain.kpi.aggregate` ya entrega las filas en el
        orden correcto.
        """
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="\n") as fh:
            writer = csv.DictWriter(fh, fieldnames=_FIELDNAMES)
            writer.writeheader()
            for row in rows:
                writer.writerow(_to_payload(row))

    def read(self, source: Path) -> list[KpiRow]:
        """Carga el CSV completo en memoria. Lanza `InputFileNotFoundError` si no existe."""
        if not source.exists():
            raise InputFileNotFoundError(source)

        with source.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            return [_from_payload(record) for record in reader]


def _to_payload(row: KpiRow) -> dict[str, str]:
    return {
        "date_utc": row.date_utc.isoformat(),
        "endpoint_base": row.endpoint_base,
        "requests_total": str(row.requests_total),
        "success_2xx": str(row.success_2xx),
        "client_4xx": str(row.client_4xx),
        "server_5xx": str(row.server_5xx),
        "parse_errors": str(row.parse_errors),
        "avg_elapsed_ms": str(row.avg_elapsed_ms),
        "p90_elapsed_ms": str(row.p90_elapsed_ms),
    }


def _from_payload(record: dict[str, str]) -> KpiRow:
    return KpiRow(
        date_utc=date.fromisoformat(record["date_utc"]),
        endpoint_base=record["endpoint_base"],
        requests_total=int(record["requests_total"]),
        success_2xx=int(record["success_2xx"]),
        client_4xx=int(record["client_4xx"]),
        server_5xx=int(record["server_5xx"]),
        parse_errors=int(record["parse_errors"]),
        avg_elapsed_ms=float(record["avg_elapsed_ms"]),
        p90_elapsed_ms=float(record["p90_elapsed_ms"]),
    )
