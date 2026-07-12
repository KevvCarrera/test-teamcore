#!/usr/bin/env python
"""Shim raíz: delega en `teamcore_http_kpi.cli.cliente_http:main` (ver ADR-0008)."""

from teamcore_http_kpi.cli.cliente_http import main

if __name__ == "__main__":
    raise SystemExit(main())
