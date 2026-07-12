# ADR-0014 · Adaptador Selenium real como alternativa a `requests`

- **Estado:** Aceptado
- **Fecha:** 2026-07-12
- **Relacionado:** complementa [ADR-0004](0004-http-requests-over-browser-automation.md) (no lo revierte)

## Contexto

El enunciado permite `selenium`/`playwright`, y el criterio de evaluación
*"uso apropiado de las bibliotecas permitidas"* puede leerse como una
expectativa de ejercitar realmente alguna de ellas, no solo dejarlas
documentadas como punto de extensión. Se solicitó explícitamente añadir un
adaptador Selenium **real y funcional**, sin arriesgar la solución ya
implementada y probada (`RequestsHttpClient`, Fase 6: 118 pruebas, verificada
también contra `httpbin.org` en vivo).

El razonamiento técnico de [ADR-0004](0004-http-requests-over-browser-automation.md)
sigue siendo válido: los endpoints usados son estáticos y no requieren
renderizado de JavaScript, por lo que `requests` sigue siendo la opción
técnicamente más simple y adecuada como cliente **por defecto**. Este ADR no
lo contradice; añade una alternativa real, aislada, que demuestra el uso
correcto de Selenium sin sustituir lo que ya funciona.

### Limitación técnica de Selenium a resolver

El *WebDriver* clásico de Selenium **no expone códigos de estado HTTP ni el
cuerpo crudo de la respuesta** — está diseñado para interactuar con el DOM
renderizado, no para inspeccionar la red. Dos maneras de sortear esto:

1. Leer el "performance log" de Chrome (`Network.responseReceived` vía CDP) —
   funciona, pero es específico de Chrome/Chromium, fràgil ante cambios de
   versión, y no da acceso limpio al cuerpo de la respuesta.
2. Ejecutar `fetch()` **dentro del navegador real**, vía
   `driver.execute_async_script(...)`, y leer el resultado (`status`, texto
   del cuerpo, si hubo redirección) desde Python.

Se eligió la opción 2: sigue siendo Selenium controlando un navegador real
(el `fetch` corre en el motor JavaScript del navegador, con su propia pila de
red, cookies y redirecciones), pero evita el problema de que Chrome/Edge
*re-renderizan* JSON y XML en un visor propio cuando se navega directamente a
esas URLs (lo que corrompería el contenido crudo que se necesita parsear).

## Decisión

- Nuevo módulo **`infrastructure/http/selenium_client.py`** con
  `SeleniumHttpClient`, que implementa el mismo puerto `HttpPort` que
  `RequestsHttpClient` (mismos métodos `get`/`post`, misma política de
  reintentos con backoff y el mismo manejo de `403`/`5xx` vía
  `AccessForbiddenError`/`HttpTaskError`). Al compartir el puerto, **las
  mismas funciones de `infrastructure/http/tasks.py` funcionan sin cambios**
  con cualquiera de los dos adaptadores — esa es la promesa de *ports &
  adapters* que ya traía la arquitectura.
- **No se cambia el adaptador por defecto.** `cliente_http.py` sigue usando
  `RequestsHttpClient`; no se agregan parámetros de CLI nuevos (el enunciado
  no los define para esta parte, ver [ADR-0008](0008-cli-design-and-parameters.md)).
- Autenticación básica: no se embebe usuario/contraseña en la URL (el
  estándar `fetch()` lo bloquea por seguridad); se envía como cabecera
  `Authorization: Basic ...`, construida igual que lo haría cualquier
  cliente HTTP.
- Cookies: se navega una vez a la URL base al construir el cliente, para que
  las llamadas de `fetch()` compartan el mismo origen y su propia bandeja de
  cookies real del navegador — el escenario de "cookies y sesión" queda
  cubierto con el comportamiento genuino de un navegador, no simulado.
- `selenium` pasa de "permitida pero no usada" a **dependencia de runtime
  real**, usada por este módulo. Se actualiza
  [ADR-0012](0012-dependency-boundary-allowed-libraries.md) en consecuencia.

### Limitaciones documentadas (honestas, no ocultas)

- `headers` de la respuesta no está disponible (el `fetch` no expone las
  cabeceras de forma consistente entre orígenes sin configuración CORS
  adicional del servidor); se devuelve un mapa vacío.
- `history` (cadena de redirecciones) no es la lista completa de saltos como
  en `requests`: `fetch()` solo informa si *hubo* una redirección
  (`response.redirected`), no cada salto intermedio. Se representa como una
  entrada sintética única cuando aplica — suficiente para los criterios de
  aceptación de FR-08, pero no una reconstrucción fiel del historial.
- `allow_redirects=False` tiene soporte parcial: el modo `redirect: "manual"`
  de `fetch()` da una respuesta "opaca" (sin estado ni cuerpo legibles), una
  restricción de seguridad del propio navegador, no un descuido de esta
  implementación.
- Requiere un navegador Chrome/Edge instalado; Selenium 4 resuelve el driver
  automáticamente (*Selenium Manager*), sin instalación manual adicional.

## Consecuencias

- (+) Se demuestra un uso real y correcto de Selenium, con las mismas reglas
  de negocio (`tasks.py`) que ya están implementadas y probadas.
- (+) La solución por defecto (`requests`, Fase 6) no se toca ni se
  arriesga: 118 pruebas existentes siguen intactas.
- (+) Pruebas del adaptador Selenium rápidas y deterministas: se inyecta un
  doble del *driver* (mismo principio que `responses` para `requests`), sin
  necesidad de abrir un navegador real en la suite por defecto.
- (−) Código y superficie de mantenimiento adicionales para una
  funcionalidad que, técnicamente, no aporta nada nuevo sobre `requests`
  para estos endpoints (ver ADR-0004). Se acepta ese costo porque así se
  solicitó explícitamente.
- (−) Las limitaciones documentadas arriba (`headers`, `history` parcial)
  son inherentes a usar un navegador para esto, no defectos corregibles.

## Alternativas consideradas

- **Reemplazar `RequestsHttpClient` por completo:** rechazada — regresión
  innecesaria de velocidad/robustez ya verificada, sin beneficio técnico
  real (ver ADR-0004).
- **`selenium-wire` u otra librería de interceptación de red:** rechazada —
  no está en la lista de librerías permitidas por el enunciado.
- **Leer el performance log de Chrome (CDP) en vez de `fetch()`:**
  descartada por ser específica de Chrome/Chromium y más frágil ante
  cambios de versión del navegador; `fetch()` es estándar y funciona igual
  en cualquier navegador que soporte Selenium 4.
