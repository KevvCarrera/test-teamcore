#!/usr/bin/env python
"""Atajo para poder ejecutar `python calcular_kpi.py` desde la raíz del repo."""

from teamcore_http_kpi.cli.calcular_kpi import main

if __name__ == "__main__":
    raise SystemExit(main())
