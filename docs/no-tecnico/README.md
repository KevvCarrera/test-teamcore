# Documentación sin lenguaje técnico

> Esta carpeta es el equivalente de `docs/` pero escrito para personas que
> **no programan**. No sustituye a la documentación técnica (esa sigue siendo
> la fuente de verdad para desarrollo); es una traducción a lenguaje simple de
> lo mismo, para que cualquier persona del equipo entienda qué se construyó,
> por qué, y cómo está organizado.

## Cómo se mantiene

Esta carpeta se actualiza **en cada unidad de trabajo cerrada** (cada fase o
funcionalidad completada), al mismo tiempo que se actualizan `TODO.md` y
`CHANGELOG.md` en la raíz del proyecto. Nunca queda desactualizada a
propósito: si algo cambia en el código o en las carpetas, este espacio se
revisa y se corrige en el mismo cambio.

## Orden de lectura sugerido

1. **[01-estructura-del-proyecto.md](01-estructura-del-proyecto.md)** — qué es
   cada carpeta del repositorio y por qué existe.
2. **[02-codigo-explicado.md](02-codigo-explicado.md)** — qué hace, línea por
   línea, cada archivo de código de la Fase 2 (scaffolding).
3. **[03-dominio-explicado.md](03-dominio-explicado.md)** — las reglas de
   negocio de la Fase 3: el árbol de errores, las "fichas" de datos, la
   normalización de endpoints, el percentil 90 y la generación de datos de
   ejemplo.
4. **[04-infraestructura-explicada.md](04-infraestructura-explicada.md)** —
   los "conectores" de la Fase 4: lectura/escritura de archivos, el mensajero
   HTTP con reglas de reintento, y quién dibuja los gráficos y arma el
   reporte final.
5. **[05-cli-de-datos-explicada.md](05-cli-de-datos-explicada.md)** — la
   Fase 5: cómo quedaron conectados de punta a punta `generar_datos.py` y
   `calcular_kpi.py`, y qué son los "golden files".
6. **[06-cliente-http-explicado.md](06-cliente-http-explicado.md)** — la
   Fase 6: los 6 escenarios contra `httpbin.org`, cómo se comportan entre sí,
   y un bug real que se encontró y corrigió probando contra el sitio en vivo.

Según avancen las fases (ver [TODO.md](../../TODO.md)), se añadirán más
documentos numerados aquí (por ejemplo, `07-...` para el reporte HTML), cada
uno enlazado desde este índice.

## Qué NO vas a encontrar aquí

- Detalles de implementación pensados para desarrolladores (eso vive en
  `docs/` y en el propio código).
- Decisiones ya cerradas y su porqué técnico exhaustivo — para eso están los
  ADR en `docs/adr/`. Aquí se explica el "qué" y un "por qué" simplificado.
