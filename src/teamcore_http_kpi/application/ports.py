"""Los "enchufes" entre `application` e `infrastructure`.

Se definen como `Protocol` (tipado estructural): cualquier clase que tenga
estos mismos métodos encaja como adaptador, sin necesidad de heredar de nada.
Así se puede cambiar, por ejemplo, cómo se guarda el CSV sin tocar el resto
del sistema, siempre que el reemplazo respete esta misma forma.
"""

from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from teamcore_http_kpi.domain.models import BitacoraRecord, GlobalMetrics, KpiRow


class HttpResponse(Protocol):
    """Lo mínimo que necesitamos de una respuesta HTTP, sin atarnos a `requests`."""

    status_code: int
    text: str

    def json(self) -> Any: ...

    @property
    def headers(self) -> Mapping[str, str]: ...

    @property
    def history(self) -> Sequence["HttpResponse"]: ...


class HttpPort(Protocol):
    """Un cliente HTTP con sesión y reintentos."""

    def get(
        self, path: str, *, auth: tuple[str, str] | None = None, allow_redirects: bool = True
    ) -> HttpResponse: ...

    def post(self, path: str, *, data: Mapping[str, str]) -> HttpResponse: ...


class BitacoraRepository(Protocol):
    """Leer y escribir la bitácora `datos.jsonl`."""

    def write(self, records: Iterable[BitacoraRecord], destination: Path) -> int: ...

    def read(self, source: Path) -> Iterator[BitacoraRecord]: ...


class KpiRepository(Protocol):
    """Leer y escribir el CSV de KPIs."""

    def write(self, rows: Sequence[KpiRow], destination: Path) -> None: ...

    def read(self, source: Path) -> list[KpiRow]: ...


class ArtifactWriter(Protocol):
    """Escribir los tres artefactos que produce el cliente HTTP."""

    def write_json(self, payload: Any, destination: Path) -> None: ...

    def write_xml(self, xml_bytes: bytes, destination: Path) -> None: ...

    def write_text(self, text: str, destination: Path) -> None: ...


class ChartRenderer(Protocol):
    """Dibujar los dos gráficos del reporte, como PNG."""

    def bar_requests_by_endpoint(self, rows: Sequence[KpiRow]) -> bytes: ...

    def p90_by_endpoint(self, rows: Sequence[KpiRow]) -> bytes: ...


class ReportRenderer(Protocol):
    """Armar el HTML final del reporte, autocontenido."""

    def render(
        self,
        metrics: GlobalMetrics,
        rows: Sequence[KpiRow],
        charts: Mapping[str, bytes],
        umbral_p90: float,
    ) -> str: ...
