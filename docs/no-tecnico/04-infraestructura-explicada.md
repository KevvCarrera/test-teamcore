# Guía de los "conectores" (`infrastructure`), explicada sin jerga

> Complementa a [01](01-estructura-del-proyecto.md), [02](02-codigo-explicado.md)
> y [03](03-dominio-explicado.md). En la Fase 4 se rellenó la carpeta
> `infrastructure/` (ver guía 01: "los brazos y los conectores") con el
> código real que habla con archivos, con internet y que dibuja gráficos.
> También se definieron los "enchufes" (`application/ports.py`) que conectan
> el cerebro con estos conectores.

## Repaso rápido: ¿qué hace `infrastructure`?

Si `domain` (guía 03) es el cerebro que solo sabe de reglas y cálculos,
`infrastructure` son las manos: la parte que efectivamente **toca el mundo
real** — abre archivos, los escribe, envía peticiones a una página web, dibuja
gráficos. El cerebro le dice "necesito estos datos" o "guarda este resultado",
y las manos se encargan de hacerlo, sin saber ni preocuparse de las reglas de
negocio.

---

## 0. `application/ports.py` — los "enchufes" estándar

Antes de construir las manos, se definió la **forma exacta de cada enchufe**:
qué información entra, qué información sale, para cada tipo de tarea (leer un
archivo, escribir un archivo, hablar con internet, dibujar un gráfico, armar el
reporte). Esto permite, por ejemplo, cambiar mañana "cómo se guarda el CSV de
estadísticas" por otra tecnología, sin tener que tocar el cerebro ni el resto
del programa — mientras el enchufe nuevo tenga la misma forma, encaja igual.

Este archivo no hace nada por sí mismo (no tiene "cuerpo", solo formas), así
que no aparece en las pruebas automáticas como código a comprobar — es una
lista de compromisos que el resto del código debe cumplir.

---

## 1. `infrastructure/io/jsonl_repository.py` — el guardián del cuaderno de registro

Se encarga de **leer y escribir** el archivo `datos.jsonl` (el cuaderno con
todas las llamadas simuladas, una por línea).

**Al escribir:** recorre cada ficha de llamada (`BitacoraRecord`, ver guía 03),
la convierte a una línea de texto en un formato estándar (JSON) y la agrega al
archivo. Si la carpeta de destino no existe, la crea sola. Si el archivo ya
existía de una ejecución anterior, lo **reemplaza por completo** (no se van
acumulando líneas viejas con las nuevas) — así, ejecutar el programa dos veces
seguidas dos veces da el mismo resultado limpio.

**Al leer:** recorre el archivo **línea por línea** (no lo carga todo de golpe
en la memoria de la computadora, importante si el archivo fuera enorme). Por
cada línea:
- Si está bien escrita, la convierte de vuelta en una ficha de llamada.
- Si está rota (por ejemplo, alguien la editó a mano y quedó mal escrita), el
  programa **no se detiene**: anota una advertencia con el número exacto de
  esa línea, la descarta, y sigue leyendo el resto del archivo con
  normalidad. Esto hace que el programa sea "tolerante a datos parcialmente
  dañados" sin dejar de avisar del problema.
- Si el archivo completo no existe, sí se detiene con un aviso claro ("no se
  encontró el archivo: ...") — porque ahí no hay nada que se pueda rescatar.

---

## 2. `infrastructure/io/csv_repository.py` — el guardián de la hoja de cálculo

Hace lo mismo que el anterior pero para el archivo de estadísticas
(`kpi_por_endpoint_dia.csv`, el resumen que arma el "cerebro"). Escribe
siempre con el mismo encabezado y el mismo orden de columnas (para que se
pueda abrir en Excel/Sheets y siempre se vea igual), y también reemplaza el
archivo entero en cada ejecución en vez de acumular filas viejas.

---

## 3. `infrastructure/io/artifact_writer.py` — la fotocopiadora de resultados

Este es el más simple de todos: solo sabe **escribir tres tipos de archivo**
en el disco — uno en formato JSON, uno en XML y uno de texto plano/HTML. No le
importa de dónde vinieron esos datos (eso lo decide la Fase 6, cuando se
construya el cliente que habla con la página web de prueba); su único trabajo
es "recibe esto, guárdalo ahí, y si la carpeta no existe, créala".

---

## 4. `infrastructure/http/client.py` — el mensajero con reglas de reintento

Este es el componente que realmente **hablará con internet** en la Fase 6 (la
parte de "cliente HTTP" del ejercicio). Por ahora se construyó la pieza
técnica, lista para usarse.

Funciona como un mensajero con instrucciones muy claras:
- Usa **una sola libreta de contactos compartida** (la "sesión"), así si en
  un mensaje anterior alguien le dio una "credencial temporal" (una cookie),
  el mensajero se acuerda y la vuelve a mostrar en el siguiente mensaje sin
  que se le tenga que repetir.
- Si al entregar un mensaje **nadie responde a tiempo**, o la respuesta es un
  "inténtalo más tarde" (un error del tipo "500"), el mensajero **no se rinde
  de inmediato**: espera un poquito y lo intenta de nuevo, un número limitado
  de veces, esperando cada vez un poco más entre intento e intento (para no
  insistir de forma agresiva).
- Si la respuesta es "acceso denegado" (403 — el escenario que pide
  simular el ejercicio), también puede reintentar, según se le configure. Si
  después de agotar los intentos permitidos sigue denegado, el mensajero
  **admite la derrota de forma clara**: avisa con un error específico
  ("acceso denegado, tras agotar los reintentos") en vez de quedarse
  reintentando para siempre o fallar de forma confusa.
- Si se le dice explícitamente "no reintentes ante un 403", entonces
  simplemente entrega la respuesta tal cual la recibió (denegada), sin
  quejarse ni insistir — deja que quien lo mandó decida qué hacer con esa
  información.

*(Nota técnica para quien lea el código: el tiempo de "espera entre intentos"
se puede reemplazar en las pruebas automáticas por una espera instantánea, así
las 85 pruebas de este proyecto corren en segundos y no en minutos.)*

---

## 5. `infrastructure/reporting/charts.py` — el dibujante de gráficos

Recibe la tabla de estadísticas y dibuja **dos gráficos** en formato de
imagen (PNG), tal como pide el ejercicio:

1. Una barra horizontal comparando cuántas solicitudes hubo por cada tipo de
   endpoint.
2. Una barra comparando el percentil 90 de latencia (ver guía 03) por cada
   tipo de endpoint.

Como estas imágenes se generan sin que haya una pantalla real disponible
(por ejemplo, si el programa corriera en un servidor sin monitor), se usa un
"modo de dibujo sin pantalla" (llamado `Agg` en la jerga de la librería
`matplotlib`) — dibuja igual, solo que directamente a un archivo en vez de a
una ventana visible.

---

## 6. `infrastructure/reporting/html_report.py` — el maquetador del reporte final

Este es el que arma la página web final (`kpi_diario.html`) que alguien podrá
abrir en su navegador. Toma:
- Las **métricas globales** (total de solicitudes, % de éxito, etc.).
- La **tabla de estadísticas** por tipo de endpoint (las agrupa sumando todas
  las fechas juntas, para que la tabla no tenga una fila por cada día sino
  una por cada tipo de endpoint).
- Los **dos gráficos** que dibujó la pieza anterior.
- El **umbral de alerta** que se le indique al ejecutar el programa (por
  ejemplo, "300 milisegundos").

Y con todo eso arma una única página HTML que:
- **No depende de ningún otro archivo.** Las imágenes no se guardan aparte:
  se incrustan directamente dentro del propio HTML (convertidas a un bloque
  de texto especial, "base64"), así el archivo se puede mover, enviar por
  correo o abrir en cualquier computadora sin que las imágenes "se rompan".
- **Marca en rojo** cualquier fila cuyo percentil 90 supere el umbral
  indicado — la alerta simple que pide el ejercicio.
- **Protege contra datos "raros".** Si algún dato de entrada tuviera
  caracteres que podrían confundirse con instrucciones de la propia página
  web (por ejemplo, símbolos de código), se "neutralizan" antes de
  insertarlos, para que se muestren como texto normal y no rompan ni
  manipulen la página.

---

## Una aclaración de diseño (por transparencia)

La especificación original de la parte del reporte (`SPEC-004`) sugería
guardar el cálculo de "métricas globales" en un archivo nuevo dentro del
cerebro (`domain/report.py`). Al llegar a esta fase, se notó que ese archivo
nunca se había planificado en el mapa oficial de carpetas del proyecto, y que
el diseño ya aprobado de los "enchufes" (ver sección 0) no lo necesitaba. Se
decidió, entonces, agregar ese cálculo (`compute_global_metrics`) dentro del
archivo de estadísticas que ya existía (`domain/kpi.py`), en vez de crear un
archivo nuevo — más simple y sin contradecir el mapa de carpetas ya aprobado.
Se avisó de esta decisión al cerrar la fase, como corresponde ante cualquier
ambigüedad de las especificaciones.

## En resumen

Esta fase construyó **las seis piezas técnicas** que tocan el mundo real:

1. **`ports.py`** — la forma estándar de cada "enchufe".
2. **`jsonl_repository.py`** — lee/escribe el cuaderno de registro.
3. **`csv_repository.py`** — lee/escribe la hoja de estadísticas.
4. **`artifact_writer.py`** — escribe los tres archivos de resultado del
   cliente HTTP.
5. **`http/client.py`** — el mensajero con reglas de reintento para hablar
   con internet.
6. **`reporting/charts.py`** y **`html_report.py`** — dibujan los gráficos y
   arman la página final del reporte.

Se comprobaron con **41 pruebas de integración** nuevas (85 en total en todo
el proyecto): escritura y lectura de archivos en carpetas temporales,
simulaciones de conversaciones con una página web (sin tocar internet de
verdad), gráficos que efectivamente son imágenes válidas, y un reporte HTML
que marca correctamente las alertas y no depende de archivos externos.
