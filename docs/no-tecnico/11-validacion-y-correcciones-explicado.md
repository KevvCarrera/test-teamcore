# Guía de la validación final contra el enunciado, explicada sin jerga

> Esta unidad de trabajo no fue una fase nueva del plan original, sino un
> pedido explícito: revisar todo el proyecto contra la lista de
> "indicaciones de desarrollo" y "criterios de evaluación" del documento
> original, y corregir lo que hiciera falta.

## ¿Qué se revisó?

Se comparó, punto por punto, cada cosa que el enunciado pedía (qué librerías
usar, que el código esté organizado en piezas pequeñas, que se expliquen
ciertas partes clave, que se manejen los errores comunes, que el README
tenga ejemplos) contra lo que el código realmente hace hoy. El resultado
completo queda en
[docs/project-plan/validacion-criterios-enunciado.md](../project-plan/validacion-criterios-enunciado.md).

## Los dos problemas reales que apareció, y cómo se corrigieron

1. **El reporte HTML no usaba `pandas` para cargar el CSV de KPIs**, aunque
   el enunciado lo pide de forma explícita para esa parte concreta ("Utiliza
   pandas para cargar el CSV... matplotlib y pandas son suficientes"). El
   código anterior leía el CSV con la librería estándar (`csv`), que
   funcionaba bien pero no era la herramienta que el enunciado nombra para
   ese paso. Se corrigió: ahora `generar_reporte.py` carga el CSV con
   `pandas`, sin cambiar nada del resto del comportamiento (los mismos
   errores se siguen detectando igual: archivo ausente, columnas faltantes,
   valores inválidos).
2. **Había una "ficha de error" (`MalformedRecordError`) preparada para las
   líneas corruptas de la bitácora, pero el código real no la estaba usando**
   — en su lugar, manejaba el problema con mensajes genéricos de Python. No
   era un error de comportamiento (las líneas corruptas ya se descartaban
   correctamente), pero era una inconsistencia: había una pieza diseñada y
   probada que nunca se usaba de verdad. Se corrigió conectándola donde
   corresponde.

Al corregir el primer punto, también salió a la luz una prueba nueva (de la
unidad de trabajo anterior) que a veces fallaba sin motivo aparente: dependía
del reloj de la computadora en el momento exacto de ejecutarse, en vez de un
tiempo fijo. Se corrigió para que siempre use un tiempo de referencia fijo,
como manda la regla del proyecto.

## Lo nuevo que se agregó, más allá de las correcciones

- **Una guía de pruebas paso a paso**
  ([docs/testing/guia-de-pruebas-por-paso.md](../testing/guia-de-pruebas-por-paso.md)):
  para cada sección del documento original (cliente HTTP, generación de
  datos, cálculo de KPIs, ETL de Pentaho, reporte), explica qué prueba
  automatizada la respalda y qué comandos ejecutar a mano para comprobarlo
  uno mismo, con ejemplos reales (incluida una verificación cruzada del
  percentil 90 calculado a mano contra el que calcula el programa).
- Comentarios ampliados en el código donde una decisión no era obvia a
  simple vista (por qué el título HTML tiene un plan B, por qué el XML se
  vuelve a armar en vez de guardarse tal cual, por qué el percentil del
  resumen del reporte es una aproximación).
- Se corrigió una guía de operación (`operations-runbook.md`) que todavía
  decía que el ETL de Pentaho "no se había probado" — desactualizado desde
  que sí se probó de verdad en una fase anterior — y un comando de Windows
  que tenía la sintaxis incorrecta.

## En resumen

El proyecto ya cumplía casi todo lo pedido; esta revisión encontró y corrigió
dos detalles concretos (uno de "qué herramienta usar", otro de "código
preparado pero no conectado"), arregló una prueba que fallaba de forma
intermitente, y dejó una guía nueva para que cualquiera pueda comprobar, paso
a paso, que cada parte del enunciado funciona como se pide.
