# ADR-0004 · `requests` en lugar de Selenium/Playwright

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El enunciado permite `requests`, `selenium` y `playwright`, y menciona controladores
de navegador. Los endpoints de httpbin involucrados (`/get`, `/post`, `/xml`,
`/html`, `/basic-auth`, `/cookies`, `/status/403`, `/redirect-to`) devuelven
**contenido estático** (JSON/XML/HTML sin renderizado JavaScript). Selenium/
Playwright aportarían peso operativo (navegador + driver), lentitud y fragilidad sin
beneficio funcional aquí.

## Decisión

Usar **las librerías que el propio test permite, escogiendo para cada tarea la que
corresponde**, sin inventar herramientas ni restricciones:

- **`requests`** (con `requests.Session` para cookies y reintentos con backoff) para
  todas las interacciones HTTP: auth, cookies, 403, `/get`, `/post`, redirecciones.
- **`beautifulsoup4`/`lxml`** para parsear el HTML de `/html` y el XML de `/xml`.

`requests`, `beautifulsoup4` y `lxml` están **explícitamente en la lista de librerías
permitidas** y cubren las tareas descritas (contenido estático, sin JavaScript).
`selenium`/`playwright` también están permitidas y **quedan disponibles**: la
abstracción `HttpPort` permite añadir un `SeleniumHttpClient`/`PlaywrightHttpClient`
si el usuario/evaluador desea ejercitar automatización de navegador, sin tocar
`application`/`domain`.

## Consecuencias

- (+) Se usa lo que el test permite, con la herramienta adecuada por tarea.
- (+) Simplicidad, velocidad y pruebas deterministas sin drivers de navegador.
- (+) Extensible a Selenium/Playwright vía el puerto, si se solicita.
- (−) La implementación por defecto no ejercita Selenium/Playwright; se deja el punto
  de extensión listo y se puede añadir bajo pedido.

## Alternativas consideradas

- **Selenium/Playwright como cliente principal:** válido y permitido; se puede
  incorporar si el evaluador quiere ver automatización de navegador. No es necesario
  para el contenido estático de estos endpoints.
- **Cliente dual desde el inicio:** disponible vía el puerto; se añade si se pide.
