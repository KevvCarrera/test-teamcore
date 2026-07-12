# Guía de los dos primeros "botones" ya encendidos, explicada sin jerga

> Complementa a [01](01-estructura-del-proyecto.md), [02](02-codigo-explicado.md),
> [03](03-dominio-explicado.md) y [04](04-infraestructura-explicada.md). Hasta
> la Fase 4, todas las piezas (el cerebro y los conectores) estaban listas
> pero nadie las había conectado entre sí, y los "botones" (`cli/`) solo
> mostraban un cartel de "en construcción". En la Fase 5 se hizo la conexión
> real: **`generar_datos.py` y `calcular_kpi.py` ya funcionan de verdad**,
> exactamente con los comandos que pide el enunciado del ejercicio.

## Lo que cambia con esta fase

Antes de esta fase, cada pieza sabía hacer su trabajo por separado (el
cerebro sabía calcular, los conectores sabían leer/escribir archivos), pero
nadie las había presentado entre sí. Esta fase agrega **los organizadores**:
código que dice "primero llama a esto, con el resultado llama a esto otro, y
si algo sale mal, hazlo así".

## 1. El organizador de "generar datos"

Cuando se ejecuta `python generar_datos.py --n_registros 500 --salida
out/datos.jsonl --seed 42`, pasa esto, en orden:

1. Se valida que `--n_registros` sea mayor que cero. Si no lo es, el programa
   **se detiene ahí mismo**, sin haber tocado ningún archivo todavía, y
   termina con el código de salida **2** (error de configuración) — mejor
   frenar antes de hacer nada que a mitad de camino.
2. Se le pide a la "máquina de inventar datos" (el cerebro, guía 03) que
   genere esa cantidad de registros, usando la fecha y hora actuales como
   punto de partida y la semilla indicada.
3. Se le entregan esos registros al "guardián del cuaderno" (el conector de
   la guía 04) para que los escriba en el archivo indicado.
4. Si todo salió bien, el programa termina con código **0**. Si hubo un
   problema al escribir el archivo (por ejemplo, la carpeta de destino no se
   pudo crear), termina con código **1**, con un mensaje que explica qué
   pasó.

## 2. El organizador de "calcular KPIs"

Cuando se ejecuta `python calcular_kpi.py --input out/datos.jsonl --output
out/kpi_por_endpoint_dia.csv`, pasa esto:

1. Se le pide al "guardián del cuaderno" que lea el archivo de entrada.
2. Con todos los registros leídos (los que estaban bien escritos; los que
   estaban rotos ya se descartaron con su aviso, ver guía 04), se le pide al
   cerebro que calcule las estadísticas agrupadas (guía 03).
3. **Si no quedó ningún registro válido para calcular nada** (el archivo
   estaba vacío, o todas sus líneas estaban rotas), el programa **no genera
   una hoja de cálculo vacía como si nada** — se detiene con un aviso claro y
   código de salida **1**. Es preferible avisar del problema a entregar un
   resultado silenciosamente incompleto.
4. Si hay al menos un registro válido, se calculan las estadísticas y se le
   piden al "guardián de la hoja de cálculo" que las escriba. Código de
   salida **0**.

## 3. Qué son los "golden files" y por qué se agregaron ahora

Se crearon dos archivos nuevos en `tests/data/`:

- `bitacora_min.jsonl`: una bitácora de ejemplo, pequeña (20 registros) y
  fija — no cambia nunca entre ejecuciones de las pruebas.
- `kpi_expected.csv`: el resultado exacto y correcto que se espera al
  procesar esa bitácora de ejemplo.

La idea es como un examen con la hoja de respuestas correctas ya escrita
detrás: cada vez que se ejecutan las pruebas automáticas, el programa procesa
`bitacora_min.jsonl` de verdad y se compara, letra por letra, contra
`kpi_expected.csv`. Si algún cambio futuro en el código altera aunque sea un
solo número del resultado, la prueba lo detecta de inmediato.

## 4. Verificación manual (no solo pruebas automáticas)

Además de las pruebas automáticas, se ejecutaron los dos comandos **tal cual
los escribiría un evaluador**, uno detrás del otro, desde la carpeta
principal del proyecto — y ambos terminaron sin errores, generando los
archivos esperados con el conteo correcto de líneas.

Un detalle importante que se confirmó en esa verificación: si se ejecuta
`generar_datos.py` dos veces con la misma semilla pero en momentos distintos
del día, **el archivo no sale idéntico byte por byte** — porque el punto de
partida temporal es "ahora mismo", que cambia con cada ejecución real. Esto
no es un error: así lo pide el propio enunciado del ejercicio. La
reproducibilidad exacta y comprobable ("mismos datos, siempre") se garantiza
y se prueba a un nivel más profundo del código (el "cerebro" de la guía 03),
donde sí se puede fijar también el instante de partida — algo que no tendría
sentido exponer como una opción de línea de comandos, porque el enunciado no
la pide.

## En resumen

Con esta fase, **las primeras dos terceras partes de la Parte 1 del
enunciado ya están terminadas y funcionando**: generar la bitácora sintética
y calcular sus estadísticas, con los mismos comandos exactos que pide el
documento original, manejo de errores claro, y una red de 13 pruebas
automáticas nuevas (además de las ya existentes) que verifican que todo
sigue funcionando así en el futuro.
