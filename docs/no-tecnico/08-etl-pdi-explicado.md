# Guía del ETL de Pentaho (Fase 8), explicada sin jerga

> Complementa a las guías anteriores. Esta fase construyó la **Parte 2** del
> enunciado: cargar la hoja de estadísticas a una base de datos, usando una
> herramienta distinta a Python — Pentaho Data Integration (PDI), con su
> editor visual llamado Spoon.

## Una diferencia importante con el resto del proyecto

Todo lo anterior era código Python. Esta parte **no lo es**: son dos archivos
en un formato especial (XML) que una herramienta externa (Pentaho) sabe leer
y ejecutar — como un diagrama de flujo guardado en un archivo, en vez de
instrucciones de programación tradicionales.

- **`t_load_kpi.ktr`** — la "receta" que lee el CSV, lo prepara y lo carga a
  la base de datos.
- **`j_daily_kpi.kjb`** — el "director de orquesta" que ejecuta esa receta,
  comprueba que salió bien, y anota el resultado.

## Una sorpresa buena: se pudo probar de verdad

Originalmente, el plan asumía que esta parte no se podría comprobar en este
entorno (no habría el programa Pentaho instalado). Pero resultó que **sí
estaba instalado en esta máquina** — así que, en vez de solo redactar los
archivos con el mejor conocimiento disponible y cruzar los dedos, se
pudieron **ejecutar de verdad**, con el programa real, y corregir lo que
hiciera falta hasta que funcionaran sin errores.

## Tres problemas reales que solo aparecieron al probar de verdad

1. **Un paso no cargaba.** El paso que asigna el tipo correcto a cada columna
   (fecha, número entero, decimal) tenía una etiqueta ligeramente distinta a
   la que Pentaho realmente espera internamente. Se descubrió pidiéndole al
   propio programa Pentaho que generara el formato correcto por sí mismo (en
   vez de seguir adivinando), y se corrigió.
2. **Las rutas de archivo apuntaban al lugar equivocado.** Al ejecutar el
   programa, este por defecto "se para" en su propia carpeta de instalación,
   no en la del proyecto — así que buscaba el CSV y la base de datos en el
   sitio incorrecto. Se corrigió usando una "variable" especial que le dice
   "busca esto en la misma carpeta donde está guardada esta receta", sin
   importar desde dónde se ejecute.
3. **La fecha se guardaba mal.** Al decirle a Pentaho "esta columna es una
   fecha", el programa terminaba guardándola como un número gigante (una
   cuenta de milisegundos), en vez del texto legible `2026-07-09` que pide el
   contrato. Se corrigió dejando esa columna como texto simple — total, el
   archivo de origen ya trae la fecha en el formato correcto, no hacía falta
   "traducirla" y arriesgarse a que se guardara mal.

## Cómo se comprobó que funciona

- Se cargó una hoja de estadísticas de ejemplo (28 filas) a la base de datos
  real, y se revisó fila por fila que los datos coincidieran exactamente con
  el archivo de origen.
- Se ejecutó **dos veces seguidas** y se confirmó que la segunda vez no
  duplicó nada (la base queda igual, no se van acumulando copias — esto es
  lo que en la Fase 5 se llamó "idempotencia").
- Se probó a propósito **quitando el archivo de entrada**, para confirmar que
  el "director de orquesta" detecta el fallo correctamente y anota el error
  en el registro, en vez de fallar de forma confusa o silenciosa.

## En resumen

Con esta fase, **las cuatro partes del enunciado ya están completas y
verificadas de verdad** — no solo el código Python (cliente HTTP, generación
de datos, cálculo de KPIs, reporte), sino también la parte de Pentaho, que se
pudo ejecutar con el programa real disponible en esta máquina y corregir
hasta que funcionara sin errores. Solo quedan pendientes las fases de
verificación final/endurecimiento y el cierre documental del proyecto.
