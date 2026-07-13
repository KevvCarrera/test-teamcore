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
7. **[06b-adaptador-selenium-explicado.md](06b-adaptador-selenium-explicado.md)** —
   una unidad no planificada originalmente: un segundo "mensajero" basado en
   un navegador Chrome real (Selenium), agregado a pedido explícito, sin
   tocar el que ya funcionaba.
8. **[07-reporte-explicado.md](07-reporte-explicado.md)** — la Fase 7: el
   reporte HTML final, y un problema real que se encontró y corrigió al
   conectar las piezas.
9. **[08-etl-pdi-explicado.md](08-etl-pdi-explicado.md)** — la Fase 8: el
   ETL de Pentaho, probado con una instalación real, y tres problemas
   reales encontrados y corregidos en el proceso.
10. **[09-verificacion-endurecimiento-explicado.md](09-verificacion-endurecimiento-explicado.md)** —
    la Fase 9: se llenaron los huecos de pruebas que la matriz de
    trazabilidad ya exigía (idempotencia real, logging, volumen, secretos
    fuera de los logs); no se encontraron bugs, solo faltaba comprobación.
11. **[10-cierre-final-explicado.md](10-cierre-final-explicado.md)** — la
    Fase 10: cierre documental (README final, nota de traspaso del CSV para
    PDI, trazabilidad 100 % verificada) y qué queda pendiente (una decisión
    de versión, no una tarea técnica).
12. **[11-validacion-y-correcciones-explicado.md](11-validacion-y-correcciones-explicado.md)** —
    revisión final contra la lista de criterios del enunciado: dos problemas
    reales encontrados y corregidos (el reporte no usaba `pandas` como pide
    el enunciado; una "ficha de error" preparada pero no conectada), y una
    guía nueva de pruebas paso a paso.

Con esto, el proyecto completo está documentado, implementado y verificado
de punta a punta.

## Qué NO vas a encontrar aquí

- Detalles de implementación pensados para desarrolladores (eso vive en
  `docs/` y en el propio código).
- Decisiones ya cerradas y su porqué técnico exhaustivo — para eso están los
  ADR en `docs/adr/`. Aquí se explica el "qué" y un "por qué" simplificado.
