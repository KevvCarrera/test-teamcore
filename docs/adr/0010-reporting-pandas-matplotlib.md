# ADR-0010 · Reporte con pandas + matplotlib

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

FR-13 pide un reporte HTML con métricas globales, tabla por endpoint y dos gráficos,
usando `pandas` (carga CSV) y `matplotlib` (gráficos), sin librerías externas
adicionales y sin llamadas HTTP.

## Decisión

- **Carga:** `pandas.read_csv` con tipos explícitos (según el contrato del CSV).
- **Gráficos:** `matplotlib` con backend **`Agg`** (sin display, apto para CI/
  servidores). Dos figuras: barra horizontal de `requests_total` y barra/línea de
  `p90_elapsed_ms` por endpoint.
- **HTML autocontenido:** los PNG se **embeben en base64** dentro del HTML ⇒ un solo
  fichero portable, sin dependencias de rutas relativas a imágenes.
- **Plantilla propia** (f-strings/`string.Template`) para el HTML, con escape de
  valores; sin motor de plantillas externo (KISS, frontera de deps).
- **Alerta por umbral:** las celdas de `p90_elapsed_ms` que superan `--umbral_p90`
  reciben una clase CSS que las pinta de **rojo**.
- **Estilos accesibles:** contraste suficiente, títulos y etiquetas descriptivas
  (NFR: claridad).

## Consecuencias

- (+) Reporte de un solo archivo, abrible en cualquier navegador, sin servidor.
- (+) Sin dependencias fuera de las permitidas.
- (−) Embeber PNG en base64 agranda el HTML; irrelevante para este volumen.

## Alternativas consideradas

- **Plotly/altair (HTML interactivo):** fuera de la frontera de dependencias.
- **Jinja2:** cómodo, pero innecesario para una plantilla simple; añade dependencia.
- **Imágenes como ficheros aparte:** rechazado; complica la portabilidad del reporte.
