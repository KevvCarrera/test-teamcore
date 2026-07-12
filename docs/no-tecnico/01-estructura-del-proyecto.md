# Guía de la estructura del proyecto (sin lenguaje técnico)

> Este documento explica, en palabras simples, **qué es cada carpeta** que se ha
> creado hasta ahora y **por qué existe**. No es una especificación técnica (esas
> están en el resto de `docs/`); es una guía de orientación para cualquier persona
> del equipo que no programe.

## La idea general

Este proyecto es un programa que hace tres cosas, en orden:

1. **Habla con una página web de pruebas** (`httpbin.org`) simulando tareas típicas
   de un robot que consulta información en internet (iniciar sesión, leer datos,
   rellenar un formulario, etc.).
2. **Genera un archivo de datos de ejemplo** (como si fuera un registro de
   llamadas) y calcula estadísticas sobre él (cuántas llamadas hubo, cuánto
   tardaron, cuántas fallaron...).
3. **Produce un reporte visual** (una página web con tablas y gráficos) a partir
   de esas estadísticas.

Para que todo esto sea ordenado, fácil de revisar y fácil de corregir si algo
falla, el código **no se mete todo en un único archivo gigante**. Se reparte en
carpetas, cada una con una responsabilidad clara — como en una empresa, donde no
todo el mundo hace de todo: hay un departamento que decide las reglas, otro que
ejecuta las tareas, y otro que habla con el exterior.

---

## Carpeta por carpeta

### 📁 `src/teamcore_http_kpi/` — el programa en sí

Es donde vive todo el código de la aplicación. Se llama así porque en Python es
buena práctica meter el programa dentro de una carpeta `src` ("source" = código
fuente), para evitar confusiones al instalarlo y probarlo. Dentro se organiza en
cuatro "departamentos":

#### 📁 `domain/` — "el cerebro" (las reglas del negocio)

Aquí van las reglas puras del problema: cómo se calculan las estadísticas, cómo
se decide a qué categoría pertenece cada llamada, etc. Es la parte más
importante porque **no depende de nada externo** — no sabe qué es internet, ni
un archivo, ni una pantalla. Solo sabe de reglas y cálculos.

**¿Por qué separarla?** Porque así se puede comprobar que las reglas son
correctas con pruebas rápidas y sencillas, sin necesitar conexión a internet ni
archivos reales. Es como tener la fórmula de un cálculo escrita aparte, en una
pizarra, en vez de mezclada con el resto del trabajo.

*(Ahora mismo estos archivos existen pero están vacíos — son los "cajones"
preparados; el contenido real se añadirá en la próxima etapa de trabajo, Fase 3.)*

#### 📁 `application/` — "el coordinador" (qué hacer y en qué orden)

Aquí se decide **la secuencia de pasos** de cada tarea: por ejemplo, "primero lee
el archivo, luego aplica las reglas del cerebro (`domain`), luego guarda el
resultado". No contiene las reglas en sí (esas están en `domain`), solo
organiza el orden de trabajo.

**¿Por qué separarla?** Para poder cambiar "cómo se guarda el resultado" (por
ejemplo, pasar de un archivo a una base de datos) sin tocar las reglas de
negocio ni la orquestación general.

#### 📁 `infrastructure/` — "los brazos y los conectores" (hablar con el mundo exterior)

Aquí vive todo lo que se conecta con algo externo al programa: enviar y recibir
información por internet, leer y escribir archivos, dibujar gráficos. Tiene tres
sub-carpetas:

- `http/` — habla con la página web de pruebas (`httpbin.org`).
- `io/` — lee y escribe los archivos de datos (JSON, CSV...).
- `reporting/` — dibuja los gráficos y arma la página del reporte final.

**¿Por qué separarla?** Porque es la parte más "frágil" (depende de cosas que
pueden fallar: la red, el disco, formatos de archivo) y conviene aislarla del
resto para que un problema ahí no contamine las reglas de negocio.

#### 📁 `cli/` — "los botones" (cómo se ejecuta cada tarea)

CLI significa "interfaz de línea de comandos": son los archivos que se ejecutan
directamente, como `python generar_datos.py`. Cada uno es, en esencia, el botón
que enciende una tarea: junta las piezas de `application` e `infrastructure` y
las pone a funcionar con los parámetros que el usuario indique.

---

### 📁 Los 4 archivos "botón" en la raíz del proyecto

`cliente_http.py`, `generar_datos.py`, `calcular_kpi.py`, `generar_reporte.py`

Son atajos de una sola línea en la carpeta principal del proyecto. Existen
porque el enunciado del ejercicio pide ejecutar los comandos exactamente así
(`python generar_datos.py ...`), y estos archivos simplemente redirigen esa
orden hacia el código real que vive dentro de `src/`. Es como un cartel que
dice "la entrada es por aquí" apuntando a la puerta verdadera.

---

### 📁 `tests/` — "el control de calidad"

Aquí viven las pruebas automáticas: pequeños programas que ejecutan el código y
comprueban que el resultado es el esperado, sin intervención humana. Así, si en
el futuro alguien cambia algo por error, las pruebas "avisan" antes de que el
error llegue a producción.

- `tests/conftest.py`: piezas reutilizables que varias pruebas necesitan (por
  ejemplo, una carpeta temporal para no ensuciar el proyecto real).
- `tests/unit/`: pruebas del "cerebro" (`domain`), las más rápidas y numerosas.
- `tests/integration/` (aparecerá más adelante): pruebas de los "conectores"
  (`infrastructure`).
- `tests/e2e/` (aparecerá más adelante): pruebas que ejecutan un "botón"
  completo de principio a fin, como lo haría una persona.

Ya existe una primera prueba: comprueba que el "cerebro" (`domain`) no se ha
mezclado por error con las partes que hablan de internet o archivos — es decir,
vigila que el orden que se explicó arriba se respete.

---

### 📁 `etl_pdi/` — la parte de Pentaho (todavía vacía, llegará en una fase posterior)

Esta carpeta está reservada para los archivos de una herramienta externa
llamada **Pentaho Data Integration**, que el enunciado también pide usar para
cargar las estadísticas en una base de datos. Es un tipo de archivo distinto
(no es código Python), por eso vive aparte. Aún no tiene contenido: se llenará
en una fase más adelante del plan.

### 📁 `out/` — la carpeta de resultados

Aquí es donde el programa **dejará** los archivos que genere cuando se ejecute
(el archivo de datos de ejemplo, el CSV de estadísticas, el reporte HTML...).
Está vacía a propósito: se llena cada vez que se ejecuta el programa, y no se
guarda en el control de versiones (en Git) porque son resultados, no código
fuente — igual que no se guarda una fotocopia, solo el documento original.

---

### 📁 Carpetas y archivos que ya existían (no creados ahora)

- **`docs/`**: toda la documentación técnica del proyecto (para desarrolladores).
- **`spec/`**: el enunciado original del ejercicio, tal como se entregó.
- **`pyproject.toml`**: la "ficha técnica" del proyecto (qué versión de Python
  usa, qué herramientas externas necesita).
- **`Makefile`**: una lista de atajos para tareas repetitivas (ej. "revisar que
  todo esté bien" con un solo comando).
- **`.venv/`** *(nueva, no se sube a Git)*: un espacio aislado en tu ordenador
  donde se instalan las herramientas necesarias para ejecutar y probar el
  programa, sin mezclarlas con el resto de tu sistema — como un taller separado
  para no ensuciar el resto de la casa.

---

## En una frase

**Cada carpeta representa una responsabilidad distinta**, para que un problema
en una parte (por ejemplo, que internet falle) no obligue a tocar las reglas de
negocio, y para que se pueda comprobar automáticamente que cada pieza funciona
por separado antes de unirlas todas.

## ¿Y por qué todavía muchos archivos están "vacíos"?

El proyecto se desarrolla en fases (ver [TODO.md](../TODO.md)). La fase actual
solo construyó **el esqueleto** — las carpetas y archivos con su propósito
documentado, pero sin la lógica de negocio todavía. Eso llega en la siguiente
fase (Fase 3), donde se rellena el "cerebro" (`domain`) con las reglas reales,
acompañado de sus pruebas.
