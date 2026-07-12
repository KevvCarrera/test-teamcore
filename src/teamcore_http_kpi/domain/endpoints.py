"""Normalización de endpoints (FR-10, NFR-05).

Convierte un `endpoint` de la bitácora en su `endpoint_base` para agrupar los
KPIs. Ver la tabla de casos y la justificación en
docs/contracts/data-contracts.md#normalización-de-endpoints.
"""


def normalize_endpoint(raw: str) -> str:
    """Normaliza `raw` a su forma base (`endpoint_base`) para agrupar KPIs.

    Regla determinista (docs/contracts/data-contracts.md#normalización-de-endpoints):
    1. Se descarta cualquier query string (`?...`) y fragmento (`#...`).
    2. Se elimina la barra final redundante.
    3. Se toma el **primer segmento** de la ruta restante como base,
       anteponiendo `/`: `"/" + path.strip("/").split("/")[0]`.

    Ejemplos: `"/status/403"` -> `"/status"`; `"/cookies/set?session=activa"`
    -> `"/cookies"`; `"/get"` -> `"/get"`.

    Args:
        raw: el valor de `endpoint` tal como aparece en la bitácora.

    Returns:
        El `endpoint_base` normalizado (siempre con un único `/` inicial).

    Raises:
        ValueError: si `raw` queda vacío tras la normalización (p. ej. `""`
            o `"/"`), que es un dato de entrada inválido (ver "casos límite"
            en el contrato).
    """
    without_fragment = raw.split("#", 1)[0]
    without_query = without_fragment.split("?", 1)[0]
    trimmed = without_query.strip("/")
    if not trimmed:
        raise ValueError(f"Endpoint inválido (vacío tras normalizar): {raw!r}")
    first_segment = trimmed.split("/")[0]
    return f"/{first_segment}"
