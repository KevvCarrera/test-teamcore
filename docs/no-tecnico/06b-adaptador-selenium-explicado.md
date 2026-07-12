# Guía del adaptador Selenium, explicada sin jerga

> Complementa a la guía [06](06-cliente-http-explicado.md). Esta unidad de
> trabajo **no estaba en el plan original** — se agregó porque, al revisar
> otra vez el enunciado, se notó que menciona explícitamente herramientas de
> navegador (Chrome, Firefox, Edge) para Selenium o Playwright, y uno de los
> criterios de evaluación es "uso apropiado de las bibliotecas permitidas".
> Se decidió, entonces, agregar un uso real de Selenium — sin arriesgar nada
> de lo que ya funcionaba.

## ¿Por qué no se había usado Selenium desde el principio?

Como se explicó en la guía 06, las tareas de esta parte del ejercicio
(iniciar sesión, leer datos, rellenar un formulario) son, en esencia,
conversaciones de datos con un sitio web — no requieren ver ni interactuar
con una página visualmente. Para ese tipo de tarea, el "mensajero" que ya
existía (basado en la librería `requests`, ver guía 04) es más rápido, más
confiable y más simple. Usar un navegador real ahí no aportaba nada técnico.

Pero el enunciado sí *permite* usar un navegador, y menciona explícitamente
las herramientas necesarias para hacerlo. Para no dejar dudas sobre si el
proyecto "sabe" usar esa herramienta cuando se le pide, se agregó un segundo
mensajero — este sí, un navegador Chrome real, controlado por Selenium.

## Cómo conviven los dos mensajeros

Gracias a que el proyecto ya estaba diseñado con "enchufes intercambiables"
(ver guía 04, sección 0), agregar un segundo mensajero fue mucho más simple
de lo que hubiera sido si todo estuviera mezclado en un solo bloque de
código: **las mismas 6 tareas (autenticación, cookies, etc.) funcionan igual
sin cambiar ni una línea**, sin importar cuál de los dos mensajeros se use.

Eso sí — **el mensajero que realmente usa el programa por defecto (`python
cliente_http.py`) sigue siendo el basado en `requests`**, el mismo que ya se
probó exhaustivamente en la fase anterior (118 pruebas, incluida una
verificación en vivo). El navegador Selenium queda disponible y demostrado,
pero no reemplaza al que ya funciona bien.

## Un detalle técnico interesante (resuelto con cuidado, no de cualquier forma)

Aquí apareció algo que vale la pena explicar, porque muestra por qué
"simplemente usar Selenium" no es tan directo como parece: **un navegador no
te dice, de forma sencilla, si una página respondió bien o mal.** Un
navegador está diseñado para *mostrarte* páginas, no para informarte
detalles técnicos como "esto respondió con el código 403" — esa información
normalmente se queda "detrás de escena".

Además, si le pides a un navegador que abra directamente una dirección que
devuelve datos JSON o XML (en vez de una página normal), Chrome y Edge los
**redibujan a su manera** — con colores, flechitas para expandir/contraer,
etc. — lo cual es cómodo para un humano que mira la pantalla, pero arruina
el contenido si lo que se necesita es el dato *exacto y original*, para
poder interpretarlo con el programa.

La solución que se implementó: en vez de decirle al navegador "anda a esta
página", se le pide que **haga la petición él mismo, con su propio motor de
red interno** (una técnica llamada `fetch`, disponible en cualquier
navegador moderno), y que devuelva el resultado tal cual, sin redibujarlo.
Sigue siendo el navegador real haciendo el trabajo — con sus propias cookies,
sus propias reglas de seguridad — solo que se lee el resultado de una forma
que no lo distorsiona.

## Limitaciones que se documentaron con honestidad

No todo se puede recuperar igual de bien a través de un navegador que a
través de un mensajero HTTP directo. Se documentaron dos limitaciones reales,
en vez de esconderlas:

- No se puede obtener el detalle completo de "encabezados" de la respuesta
  (información técnica adicional que normalmente no le importa a un
  navegador común).
- Si una petición fue redirigida a otra dirección, se sabe *que* hubo una
  redirección, pero no el detalle completo de cada salto intermedio (el
  navegador tampoco expone eso con facilidad).

Ninguna de las dos limitaciones afecta lo que pide el enunciado — se
documentan porque es mejor ser claro sobre lo que una herramienta puede y no
puede hacer bien, que fingir que hace algo que en realidad no hace.

## Cómo se comprobó que funciona

Igual que con el mensajero basado en `requests`, se hicieron dos tipos de
comprobación:

1. **23 pruebas automáticas rápidas**, con un "doble" del navegador (no abre
   Chrome de verdad, contesta lo que se le programa) — así la suite completa
   del proyecto sigue corriendo en segundos.
2. **Pruebas con un Chrome real**, aparte y opcionales (no corren solas, hay
   que pedirlas explícitamente) — al ejecutarlas, se confirmó que el
   navegador efectivamente se abre y hace las peticiones. En el momento de
   probar, `httpbin.org` (el sitio de pruebas público) estaba respondiendo
   con errores de "servicio no disponible" — el mismo problema externo que ya
   se había documentado en la Fase 6 — pero el programa lo manejó
   correctamente: avisó del problema con claridad, sin caerse.

## En resumen

Se agregó un segundo "mensajero", basado en un navegador Chrome real y
controlado por Selenium, que demuestra un uso genuino y correcto de esa
herramienta — resolviendo con cuidado una limitación técnica real de los
navegadores (no exponer códigos de estado ni contenido crudo con facilidad)
en vez de simular que funciona. Todo esto sin tocar ni arriesgar el
mensajero que ya estaba funcionando y probado desde la fase anterior.
