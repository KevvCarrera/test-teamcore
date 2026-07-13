# Guía de la Fase 9 (verificación y endurecimiento), explicada sin jerga

> Complementa a las guías anteriores. Esta fase no construyó nada nuevo de cara
> al usuario final — no hay un comando nuevo ni un archivo de salida nuevo.
> Fue una fase de "cerrar huecos": revisar que todo lo prometido en los
> documentos de requisitos estuviera de verdad comprobado con una prueba, no
> solo dicho de palabra.

## ¿Qué se encontró al revisar?

Al repasar la matriz de trazabilidad (el documento que dice, para cada
requisito, qué prueba lo comprueba), aparecieron tres promesas que aún no
tenían una prueba real detrás:

1. **Que reejecutar el generador de datos con los mismos parámetros da
   siempre el mismo resultado** (no solo que "sobrescribe", que ya estaba
   probado, sino que el contenido es idéntico byte por byte).
2. **Que el sistema de registro de eventos (logging) funciona como se
   documentó**: que los mensajes van al canal correcto, que se puede subir o
   bajar el nivel de detalle, y que hay dos formatos disponibles.
3. **Que el sistema aguanta un volumen grande de datos** (no solo los 500
   registros del ejemplo del enunciado, sino unos 100 000) sin tardar minutos
   ni comportarse de forma rara.

También se agregó una prueba extra, no estrictamente pedida pero relevante
dado que este proyecto maneja credenciales de prueba: comprobar, con código,
que **la contraseña nunca aparece en un mensaje de registro**, incluso cuando
un escenario falla (que es cuando más tentador es "loguear todo" para
depurar).

## ¿Se encontraron bugs?

No. A diferencia de fases anteriores (donde probar de verdad sí destapó
errores reales), aquí la revisión del código de manejo de errores y logging
de los cuatro comandos confirmó que ya estaba bien hecho desde el principio.
Esta fase fue, sobre todo, de **llenar huecos de pruebas**, no de corregir
código.

## ¿Qué tan rápido es "rápido"?

Se probó con 100 000 registros (200 veces más que el ejemplo del enunciado) y
todo el proceso — generar los datos y calcular los KPIs — tardó unos 5-6
segundos en una máquina normal. Es una diferencia enorme de margen respecto a
lo que el documento original pedía ("segundos, no minutos").

## En resumen

Con esta fase, cada requisito del proyecto (17 funcionales + 14 de calidad)
queda no solo implementado, sino con una prueba automatizada que lo respalda
— así, si alguien cambia el código en el futuro por accidente y rompe algo,
la suite de pruebas lo va a detectar sola. Solo queda pendiente la Fase 10:
cerrar la documentación final del proyecto.
