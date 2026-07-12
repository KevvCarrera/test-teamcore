#!/usr/bin/env python
"""Atajo para poder ejecutar `python cliente_http.py` desde la raíz del repo."""

from teamcore_http_kpi.cli.cliente_http import main

if __name__ == "__main__":
    raise SystemExit(main())
