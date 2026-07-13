"""Cómo se agrupan los endpoints para calcular los KPIs."""


def normalize_endpoint(raw: str) -> str:
    """Reduce un endpoint a su categoría base (p. ej. `/status/403` -> `/status`).

    Lanza `ValueError` si no queda nada tras normalizar.
    """
    without_fragment = raw.split("#", 1)[0]
    without_query = without_fragment.split("?", 1)[0]
    trimmed = without_query.strip("/")
    if not trimmed:
        raise ValueError(f"Endpoint inválido (vacío tras normalizar): {raw!r}")
    first_segment = trimmed.split("/")[0]
    return f"/{first_segment}"
