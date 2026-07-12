# Guía del reporte final (Fase 7), explicada sin jerga

> Complementa a las guías [01](01-estructura-del-proyecto.md) a
> [06b](06b-adaptador-selenium-explicado.md). Con esta fase se completó el
> **tercer y último comando** que pide el enunciado: `generar_reporte.py`,
> el que convierte la hoja de estadísticas en una página web con métricas y
> gráficos.

## Lo que hace `generar_reporte.py`

Toma el archivo de estadísticas (el CSV que produce `calcular_kpi.py`, ver
guía 05) y arma una única página HTML con:

- **Los números grandes de arriba**: cuántas solicitudes hubo en total, qué
  porcentaje fueron exitosas, qué porcentaje fallaron, y un percentil 90
  "global" aproximado (ver guía 03 para qué es el percentil 90).
- **Una tabla**, con una fila por cada tipo de endpoint (sumando todas las
  fechas juntas).
- **Dos gráficos** (los que ya se habían construido en la Fase 4): uno
  comparando el total de solicitudes por endpoint, y otro comparando el
  percentil 90 de latencia.
- **Alertas en rojo**: cualquier celda de percentil 90 que supere el umbral
  indicado (300 milisegundos, por defecto) se pinta de rojo, para que salte
  a la vista de inmediato.

Como las piezas que dibujan los gráficos y arman el HTML ya se habían
construido y probado en la Fase 4, esta fase fue sobre todo **conectar los
cables**: leer el archivo correcto, calcular los números que faltaban, y
guardar el resultado — el mismo patrón de "organizador" que ya se vio en la
Fase 5 (guía 05) para los otros dos comandos.

## Un problema real que apareció al conectar las piezas

Al construir esta fase, se encontró algo que no se había notado antes: si el
archivo de estadísticas viniera con una columna faltante (por ejemplo,
alguien lo editó a mano y borró una columna por error), el programa **no
avisaba con claridad** — dejaba pasar un error técnico interno, en vez de
decir algo como "falta la columna X". Esto va justo en contra de lo que pide
el enunciado para este tipo de casos (avisar con un mensaje claro y terminar
de forma controlada). Se corrigió para que ahora sí lo detecte y lo informe
como corresponde, con una prueba automática que lo comprueba.

## Verificación completa

Se ejecutaron, uno detrás de otro, los tres comandos exactos que pide el
enunciado — generar la bitácora, calcular las estadísticas, y armar el
reporte — y se revisó el archivo final resultante: contenía el total
correcto de solicitudes (500, igual a la cantidad generada), una fila por
cada uno de los 7 tipos de endpoint, los dos gráficos incrustados
correctamente, y las alertas en rojo donde correspondía según el umbral.

## En resumen

Con esta fase, **las tres partes principales del enunciado (0, 1 y 3) ya
funcionan de punta a punta**: el cliente HTTP, la generación y cálculo de
datos, y el reporte final. Solo queda pendiente la parte de Pentaho/PDI
(Fase 8), que es un tipo de archivo distinto (no es código Python) y se
valida de otra manera, según ya se explicó en la documentación técnica.
