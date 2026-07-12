# Guía del cliente HTTP (Parte 0), explicada sin jerga

> Complementa a las guías [01](01-estructura-del-proyecto.md) a
> [05](05-cli-de-datos-explicada.md). Esta fase terminó la **Parte 0** del
> enunciado: los 6 escenarios que simulan tareas típicas de "hablarle a una
> página web" (autenticación, cookies, un acceso denegado a propósito,
> extraer datos en tres formatos distintos, enviar un formulario, y seguir
> una redirección). Ahora `python cliente_http.py` los ejecuta de verdad.

## Los 6 escenarios, en una frase cada uno

1. **Autenticación básica**: se conecta con usuario y contraseña de prueba, y
   confirma que el sistema lo reconoció.
2. **Cookies y sesión**: deja una "credencial temporal" y confirma que, en la
   siguiente pregunta, el sitio todavía se acuerda de ella.
3. **Restricción de acceso (403)**: pide a propósito algo que sabe que le van
   a negar, para comprobar que el programa lo detecta correctamente y no se
   cae por eso — de hecho, aquí "salir bien" significa justamente que el
   programa reconoció el rechazo tras varios intentos, no que consiguiera
   acceso.
4. **Extracción JSON**: pide datos en formato JSON y los guarda en
   `datos.json`.
5. **Extracción XML**: pide datos en formato XML, los interpreta, y los
   vuelve a guardar en `datos.xml`, ya verificado como "bien formado".
6. **Extracción de título HTML**: pide una página web y guarda su título (o,
   si no tiene título, el encabezado principal) en `titulo.html`.
7. **Envío de formulario**: manda los datos de prueba (Juan Pérez, su correo,
   su mensaje) como si se llenara un formulario, y confirma que el sitio los
   recibió exactamente igual.
8. **Redirección**: pide algo que el sitio redirige a otra dirección, y
   confirma que el programa efectivamente llega al destino final.

*(Son 8 puntos porque el escenario de "extracción de datos" del enunciado en
realidad cuenta como tres tareas distintas — JSON, XML y HTML — pero en total
siguen siendo las "6 tareas" que describe el documento original.)*

## Cómo se comportan entre sí

Los 6 escenarios se ejecutan **uno detrás de otro, con la misma sesión**
(como una sola conversación continua con el sitio, no seis llamadas
separadas que no se conocen entre sí) — así, la cookie que se deja en el
escenario 2 sigue disponible más adelante si hiciera falta.

Y lo más importante: **si uno falla, no se cancelan los demás.** Cada
escenario se ejecuta pase lo que pase con los anteriores, se anota si salió
bien o mal, y al final se muestra un resumen completo de los 8. El programa
solo termina con un código de "todo salió mal" si **ninguno** de los
escenarios tuvo éxito.

## Un bug real, encontrado probando con el sitio de verdad

Todo el trabajo anterior se había probado con una "actuación" del sitio web
(un doble que responde exactamente lo que se le programa, sin tocar
internet). Antes de dar por cerrada esta fase, se hizo algo más: se ejecutó
el programa contra el sitio real (`httpbin.org`).

Y ahí apareció un problema real: el sitio de pruebas público está,
últimamente, algo inestable — respondía "servicio no disponible" (un error
llamado 503) para casi todo. El programa reintentaba correctamente varias
veces (como estaba diseñado), pero al agotar los intentos, en vez de decir
con claridad "esto falló", intentaba seguir leyendo una respuesta que no
tenía el formato esperado — y el programa completo se caía con un mensaje de
error técnico, en vez de anotar ese escenario como fallido y seguir con los
demás.

**Se corrigió:** ahora, si un error de ese tipo persiste después de agotar
los reintentos, el programa lo reconoce con claridad, anota ese escenario
como fallido, y **sigue ejecutando el resto sin problema**. Se agregó además
una prueba automática que reproduce exactamente esta situación, para que
nunca vuelva a pasar sin que alguien se entere de inmediato.

Este hallazgo es un buen ejemplo de por qué, además de las pruebas
automáticas (que simulan situaciones controladas), vale la pena probar
también contra el servicio real de vez en cuando: hay comportamientos del
mundo real que ningún doble programado puede anticipar del todo.

## En resumen

Con esta fase, **la Parte 0 completa del enunciado ya funciona**: los 6
escenarios contra `httpbin.org`, con manejo de errores robusto (probado con
dobles y también en vivo), generando los tres archivos que pide el ejercicio
(`datos.json`, `datos.xml`, `titulo.html`). Se agregaron 26 pruebas
automáticas nuevas, y se descubrió y corrigió un problema real de manejo de
errores que solo la prueba contra el servicio real pudo revelar.
