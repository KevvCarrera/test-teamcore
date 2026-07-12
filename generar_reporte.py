#!/usr/bin/env python
"""Shim raíz: delega en `teamcore_http_kpi.cli.generar_reporte:main` (ver ADR-0008)."""

from teamcore_http_kpi.cli.generar_reporte import main

if __name__ == "__main__":
    raise SystemExit(main())
