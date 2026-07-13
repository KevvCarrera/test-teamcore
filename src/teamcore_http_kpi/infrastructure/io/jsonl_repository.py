"""`JsonlBitacoraRepository`: lee y escribe `datos.jsonl`, una línea por registro."""

import json
import logging
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path

from teamcore_http_kpi.domain.errors import InputFileNotFoundError, MalformedRecordError
from teamcore_http_kpi.domain.models import BitacoraRecord

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ("timestamp_utc", "endpoint", "status_code", "elapsed_ms", "parse_result")
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class JsonlBitacoraRepository:
    """Adaptador de `BitacoraRepository` sobre archivos JSON Lines (UTF-8)."""

    def write(self, records: Iterable[BitacoraRecord], destination: Path) -> int:
        """Escribe `records` en `destination`, una línea JSON por registro
        (reemplaza el archivo si ya existía). Devuelve cuántos se escribieron.
        """
        destination.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with destination.open("w", encoding="utf-8", newline="\n") as fh:
            for record in records:
                fh.write(json.dumps(_to_payload(record), ensure_ascii=False))
                fh.write("\n")
                count += 1
        return count

    def read(self, source: Path) -> Iterator[BitacoraRecord]:
        """Lee `source` línea por línea (sin cargar todo en memoria).

        Lanza `InputFileNotFoundError` si no existe. Líneas mal formadas se
        registran con `WARNING` y se saltan, en vez de abortar.
        """
        if not source.exists():
            raise InputFileNotFoundError(source)

        with source.open("r", encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield _from_payload(stripped)
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                    error = MalformedRecordError(line_number, str(exc))
                    logger.warning("%s (archivo: %s)", error, source)


def _to_payload(record: BitacoraRecord) -> dict[str, str | int | float]:
    return {
        "timestamp_utc": record.timestamp_utc.astimezone(UTC).strftime(_TIMESTAMP_FORMAT),
        "endpoint": record.endpoint,
        "status_code": record.status_code,
        "elapsed_ms": record.elapsed_ms,
        "parse_result": record.parse_result,
    }


def _from_payload(line: str) -> BitacoraRecord:
    payload: object = json.loads(line)
    if not isinstance(payload, dict):
        raise ValueError("la línea no es un objeto JSON")
    missing = [field for field in _REQUIRED_FIELDS if field not in payload]
    if missing:
        raise KeyError(f"faltan campos: {missing}")

    timestamp_raw = payload["timestamp_utc"]
    if not isinstance(timestamp_raw, str):
        raise TypeError("timestamp_utc debe ser texto")
    timestamp = datetime.strptime(timestamp_raw, _TIMESTAMP_FORMAT).replace(tzinfo=UTC)

    return BitacoraRecord(
        timestamp_utc=timestamp,
        endpoint=str(payload["endpoint"]),
        status_code=int(payload["status_code"]),
        elapsed_ms=float(payload["elapsed_ms"]),
        parse_result=str(payload["parse_result"]),
    )
