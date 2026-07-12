#!/usr/bin/env python
"""Atajo para poder ejecutar `python generar_datos.py` desde la raíz del repo."""

from teamcore_http_kpi.cli.generar_datos import main

if __name__ == "__main__":
    raise SystemExit(main())
