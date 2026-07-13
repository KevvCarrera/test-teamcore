"""`CsvKpiRepository`: lee y escribe el CSV de estadísticas por endpoint y día."""

import csv
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import pandas as pd

from teamcore_http_kpi.domain.errors import DataInputError, InputFileNotFoundError
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
        """Carga el CSV completo con `pandas` (tal como pide el enunciado para el reporte).

        Lanza `InputFileNotFoundError` si no existe, y `DataInputError` si el
        archivo está vacío, le falta alguna columna del contrato o trae un
        valor que no se puede convertir al tipo esperado.
        """
        if not source.exists():
            raise InputFileNotFoundError(source)

        try:
            # dtype=str + keep_default_na=False: todo se lee como texto plano,
            # sin que pandas adivine tipos ni convierta celdas vacías a NaN;
            # la conversión real a int/float/date la hace `_from_payload`.
            frame = pd.read_csv(source, dtype=str, keep_default_na=False)
        except pd.errors.EmptyDataError as exc:
            raise DataInputError(f"El CSV de KPIs está vacío: {source}") from exc

        missing_columns = [name for name in _FIELDNAMES if name not in frame.columns]
        if missing_columns:
            raise DataInputError(
                f"Falta(n) columna(s) del contrato en el CSV de KPIs: {missing_columns}"
            )

        records: list[dict[str, str]] = frame[list(_FIELDNAMES)].to_dict(orient="records")
        return [_from_payload(record) for record in records]


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
    # `read()` ya garantiza que todas las columnas de _FIELDNAMES existen antes
    # de llegar aquí; lo único que puede fallar por fila es un valor inválido.
    try:
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
    except ValueError as exc:
        raise DataInputError(f"Valor inválido en el CSV de KPIs: {exc}") from exc
