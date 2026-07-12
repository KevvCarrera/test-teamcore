"""Capa `domain`: lógica de negocio pura (sin E/S, sin red, sin CLI).

Ver docs/architecture/architecture-overview.md — la regla de dependencia exige
que nada en este paquete importe `requests`, `pandas`, `matplotlib`, `bs4`,
`lxml` ni `argparse`. Verificado por tests/unit/test_architecture_layering.py.
"""
