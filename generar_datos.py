#!/usr/bin/env python
"""Shim raíz: delega en `teamcore_http_kpi.cli.generar_datos:main` (ver ADR-0008)."""

from teamcore_http_kpi.cli.generar_datos import main

if __name__ == "__main__":
    raise SystemExit(main())
