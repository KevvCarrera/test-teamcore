"""Cómo se agrupan los endpoints para calcular los KPIs."""


def normalize_endpoint(raw: str) -> str:
    """Reduce un endpoint a su categoría base, para poder agruparlo en los KPIs.

    La idea: `/status/403` y `/status/500` son, a efectos de estadísticas,
    "lo mismo" — ambos son el endpoint `/status` con un código distinto. Por
    eso se normaliza así: se quita cualquier `?query` o `#fragmento`, se
    recortan las barras sobrantes y se toma solo el primer segmento de la
    ruta. `/cookies/set?session=activa` termina siendo `/cookies`, `/get`
    se queda igual.

    Si no queda nada después de recortar (alguien pasó `""` o `"/"`), se
    lanza un error en vez de adivinar una categoría — es un dato de entrada
    inválido, no algo que debamos normalizar en silencio.
    """
    without_fragment = raw.split("#", 1)[0]
    without_query = without_fragment.split("?", 1)[0]
    trimmed = without_query.strip("/")
    if not trimmed:
        raise ValueError(f"Endpoint inválido (vacío tras normalizar): {raw!r}")
    first_segment = trimmed.split("/")[0]
    return f"/{first_segment}"
