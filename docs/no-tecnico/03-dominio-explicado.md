# Guía del "cerebro" del programa (`domain`), explicada sin jerga

> Complementa a [01-estructura-del-proyecto.md](01-estructura-del-proyecto.md)
> y [02-codigo-explicado.md](02-codigo-explicado.md). En la Fase 2 la carpeta
> `domain/` (el "cerebro" del programa, ver guía 01) estaba vacía — solo
> cajones preparados. En la Fase 3 se rellenó con las reglas de negocio
> reales. Este documento explica esas reglas, archivo por archivo, sin dar
> por hecho que sabes programar.

## Repaso rápido: ¿qué es `domain`?

Es la parte del programa que **solo sabe de reglas**, no de internet, ni de
archivos, ni de pantallas. Como el departamento de cálculo de una empresa: le
dan números, aplica las fórmulas acordadas, y devuelve un resultado — no le
importa si esos números llegaron por correo, por teléfono o por fax.

---

## 1. `domain/errors.py` — el árbol de "tipos de problema"

Cuando algo falla, el programa necesita poder decir **qué tipo** de problema
fue, no solo "algo salió mal". Este archivo define una familia de "etiquetas
de problema", organizadas como un árbol genealógico:

```
TeamcoreError                     (el problema más general: "algo falló")
├── ConfigError                   (le diste al programa un parámetro inválido)
├── HttpTaskError                 (falló al hablar con la página web de prueba)
│   └── AccessForbiddenError      (la web dijo "acceso denegado" y ya no insistió más)
├── DataInputError                (problema con los datos de entrada)
│   ├── InputFileNotFoundError    (el archivo que le pediste leer no existe)
│   └── MalformedRecordError      (una línea del archivo está mal escrita)
└── ReportError                   (falló al construir el reporte final)
```

**¿Por qué organizarlo así, en árbol?** Porque permite reaccionar con la
precisión que haga falta. Por ejemplo, se puede decir "si falla cualquier cosa
relacionada con los datos de entrada (`DataInputError`), avisa con el código de
salida 1", sin tener que enumerar una por una todas las formas específicas en
que los datos pueden fallar — el árbol ya las agrupa.

Dos de las etiquetas llevan además información extra pegada, para que el
mensaje de error sea útil y no genérico:

- `InputFileNotFoundError` guarda la **ruta exacta** del archivo que faltaba,
  así el mensaje dice "no se encontró: `out/datos.jsonl`" en vez de un genérico
  "archivo no encontrado".
- `MalformedRecordError` guarda el **número de línea** y el motivo, así el
  mensaje señala exactamente dónde está el dato roto, para poder ir a
  revisarlo.

---

## 2. `domain/models.py` — las tres "fichas" del proyecto

Aquí se definen tres moldes de ficha (ver la guía 02 para qué es un "molde" en
este sentido):

- **`BitacoraRecord`** — una ficha por **cada llamada** simulada: cuándo
  ocurrió, a qué endpoint, con qué resultado, cuánto tardó, si se pudo
  interpretar bien o no. Es la versión "en memoria" de cada línea del archivo
  `datos.jsonl`.
- **`KpiRow`** — una ficha por **cada fila del resumen estadístico** (una
  combinación de fecha + tipo de endpoint): cuántas llamadas hubo, cuántas
  fueron exitosas, cuántas fallaron, tiempos promedio y "de cola" (ver el
  percentil 90 más abajo).
- **`GlobalMetrics`** — una única ficha con los **números globales** que
  aparecerán arriba del todo en el reporte final (total de llamadas, % de
  éxito, % de error, percentil 90 global).

Nota curiosa: en la documentación original también se mencionaba una cuarta
ficha, `FormData` (los datos del formulario de prueba). Se decidió **no
duplicarla aquí** porque ya existe, con el mismo propósito, dentro de
`config.py` (ver guía 02, sección 1) — tener dos fichas iguales en dos sitios
distintos habría sido redundante y una fuente de confusión futura.

---

## 3. `domain/endpoints.py` — la regla de "simplificar la dirección"

Cuando el programa registra una llamada, guarda la dirección exacta, por
ejemplo `/status/403` (una especie de "pasillo 7, estante 3" de una tienda).
Pero para hacer estadísticas **agrupadas**, conviene simplificar esa dirección
a su categoría general — como agrupar todas las ventas de "pasillo 7" sin
importar el estante exacto.

```python
def normalize_endpoint(raw: str) -> str:
    without_fragment = raw.split("#", 1)[0]
    without_query = without_fragment.split("?", 1)[0]
    trimmed = without_query.strip("/")
    if not trimmed:
        raise ValueError(f"Endpoint inválido (vacío tras normalizar): {raw!r}")
    first_segment = trimmed.split("/")[0]
    return f"/{first_segment}"
```

Explicado paso a paso, con el ejemplo `/status/403`:

1. **Quita cualquier "anotación" extra al final.** Algunas direcciones traen
   partes añadidas como `?session=activa` (parámetros) o `#seccion`
   (fragmentos) — se descartan, porque no cambian la categoría general.
2. **Quita las barras `/` sobrantes al principio y al final.** De
   `/status/403` queda `status/403`.
3. **Se queda solo con la primera palabra del camino.** De `status/403` se
   queda con `status`, y le vuelve a poner la barra inicial: `/status`.
4. **Si no queda nada** (alguien mandó una dirección vacía o solo `/`), el
   programa **se niega a adivinar** y avisa del error, en vez de inventar una
   categoría — mejor un aviso claro que un dato silenciosamente incorrecto.

Resultado con ejemplos reales del proyecto:

| Dirección original | Categoría simplificada |
|---|---|
| `/status/403` | `/status` |
| `/status/500` | `/status` |
| `/cookies/set?session=activa` | `/cookies` |
| `/get` | `/get` |

Así, todas las llamadas a `/status/403` y `/status/500` terminan sumándose
juntas bajo la misma categoría `/status` en las estadísticas, en vez de
aparecer como cosas distintas.

---

## 4. `domain/kpi.py` — el percentil 90 y el resumen estadístico

### ¿Qué es el "percentil 90"?

Imagina una carrera con 100 corredores, y anotas el tiempo de cada uno. El
**percentil 90** es el tiempo tal que **90 de los 100 corredores** lo
igualaron o lo superaron (llegaron en ese tiempo o antes). No es el tiempo
promedio — es un valor que dice "así de lento (o rápido) es el 90 % de los
casos", ignorando a los pocos corredores excepcionalmente lentos que podrían
"engañar" al promedio.

Se usa aquí para medir la velocidad de respuesta del sistema: el
`p90_elapsed_ms` de un grupo de llamadas dice "el 90 % de esas llamadas
respondió en este tiempo o menos". Es una medida más realista que el promedio
simple, porque un par de llamadas muy lentas no la distorsionan tanto.

```python
def percentile_90(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("No se puede calcular el percentil 90 de una secuencia vacía")
    return float(np.percentile(values, 90))
```

Esta función delega el cálculo exacto en una herramienta muy usada y confiable
(`numpy`, una librería de cálculo numérico), en vez de reinventar la fórmula
matemática — así se reduce el riesgo de errores de cálculo. Antes de calcular,
comprueba que haya al menos un dato: no tiene sentido "el percentil de la
nada".

### La función que arma el resumen (`aggregate`)

```python
def aggregate(records: Iterable[BitacoraRecord]) -> list[KpiRow]:
    groups: dict[tuple[date, str], list[BitacoraRecord]] = defaultdict(list)
    for record in records:
        key = (record.timestamp_utc.date(), normalize_endpoint(record.endpoint))
        groups[key].append(record)

    rows = [
        _aggregate_group(date_utc, endpoint_base, group)
        for (date_utc, endpoint_base), group in groups.items()
    ]
    rows.sort(key=lambda row: (row.date_utc, row.endpoint_base))
    return rows
```

Esto funciona como una **tabla dinámica** (si has usado Excel/Sheets, la idea
es idéntica a "agrupar y resumir"):

1. Recorre todas las llamadas, una por una.
2. Para cada una, calcula su "etiqueta de grupo": la fecha (sin la hora) más
   la categoría simplificada de la dirección (usando la regla explicada
   arriba).
3. Va guardando cada llamada en el "montón" que le corresponde según esa
   etiqueta — todas las llamadas del mismo día y la misma categoría terminan
   en el mismo montón.
4. Por cada montón, calcula sus estadísticas (ver `_aggregate_group` abajo).
5. **Ordena el resultado** por fecha y luego por categoría — así, si se
   ejecuta dos veces con los mismos datos, el archivo de salida sale
   **exactamente igual** ambas veces (esto es importante: se llama
   "determinismo", y evita sorpresas al comparar resultados).

```python
def _aggregate_group(date_utc, endpoint_base, group):
    requests_total = len(group)
    success_2xx = sum(1 for r in group if 200 <= r.status_code <= 299)
    client_4xx = sum(1 for r in group if 400 <= r.status_code <= 499)
    server_5xx = sum(1 for r in group if 500 <= r.status_code <= 599)
    parse_errors = sum(1 for r in group if r.parse_result != "ok")
    elapsed = [r.elapsed_ms for r in group]
    avg_elapsed_ms = round(sum(elapsed) / len(elapsed), 2)
    p90_elapsed_ms = round(percentile_90(elapsed), 2)
    return KpiRow(...)
```

Para cada montón (grupo), cuenta:
- **Cuántas llamadas hay en total.**
- **Cuántas fueron "éxito"** (códigos de respuesta entre 200 y 299 — en el
  mundo de internet, los números que empiezan con 2 significan "todo salió
  bien").
- **Cuántas fueron "error del que pregunta"** (códigos 400 a 499, como el
  clásico "404: no encontrado").
- **Cuántas fueron "error del servidor"** (códigos 500 a 599, un fallo del
  lado que respondía).
- **Cuántas no se pudieron interpretar bien** (`parse_errors`).
- El **tiempo promedio** de respuesta y el **percentil 90**, ambos redondeados
  a 2 decimales para que el reporte final sea legible.

---

## 5. `domain/generation.py` — la máquina de generar datos de ejemplo

Como todavía no hay un historial real de llamadas, el programa **inventa** uno
de mentira, pero de forma controlada, para poder practicar los cálculos de
estadísticas sobre él. La clave es que ese invento **no sea realmente
al azar** — tiene que poder repetirse exactamente igual cuando se le pide,
para poder comprobar que todo funciona de forma consistente.

### La idea de la "semilla" (`seed`)

Es como una receta de cocina: si dos personas usan **la misma receta, en el
mismo orden, con los mismos ingredientes**, obtienen el mismo pastel. Aquí, la
"receta" es siempre igual (el código), y la "semilla" es el número que arranca
el generador de números al azar de forma predecible. Con la misma semilla,
sale siempre la misma secuencia de valores "aleatorios" — parecen al azar, pero
son reproducibles a voluntad.

```python
CATALOG: tuple[str, ...] = (
    "/get", "/post", "/status/403", "/basic-auth", "/cookies", "/xml", "/html",
)
```
La lista de las 7 direcciones posibles que puede tener una llamada inventada
— exactamente las que pide el enunciado del ejercicio.

```python
def generate_records(n, *, seed, ref_utc):
    rng = np.random.default_rng(seed)
    endpoints = rng.choice(CATALOG, size=n)
    offset_days = rng.uniform(0.0, 3.0, size=n)
    elapsed_ms = np.round(rng.uniform(50.0, 800.0, size=n), 1)
    status_roll = rng.random(n)
    parse_roll = rng.random(n)

    for i in range(n):
        ...
        yield BitacoraRecord(...)
```

Se preparan, de una sola vez, todas las "tiradas de dados" que van a hacer
falta para las `n` llamadas que se van a inventar:
- **`endpoints`**: a qué dirección corresponde cada llamada (elegida al azar
  entre las 7 posibles).
- **`offset_days`**: cuánto tiempo atrás en el pasado ocurrió cada llamada
  (entre 0 y 3 días atrás, tal como pide el enunciado: "dentro de los últimos
  3 días").
- **`elapsed_ms`**: cuánto tardó cada llamada, un número entre 50 y 800
  (milisegundos), redondeado a 1 decimal.
- **`status_roll`** y **`parse_roll`**: dos "tiradas de dados" adicionales que
  se usan para decidir, con las probabilidades correctas, si la llamada tuvo
  éxito o no y si se pudo interpretar bien o no (ver más abajo).

Luego, una por una, se arma la ficha (`BitacoraRecord`) de cada llamada usando
esas tiradas ya calculadas. Es importante que **siempre se pidan las tiradas
en el mismo orden** (primero direcciones, luego días, luego duración,
luego los dos dados de resultado) — así, con la misma semilla, sale siempre
exactamente la misma secuencia.

### Cómo se decide el resultado de cada llamada

```python
def _status_code_for(endpoint, roll):
    if endpoint == "/status/403":
        return 403
    if roll < 0.90:
        return 200
    if roll < 0.90 + 0.06:
        return 500
    return 404
```

Aquí está la regla de negocio que pedía el enunciado: *"`/status/403` siempre
403; el resto, mayoritariamente 200"*. En números concretos: si la dirección es
`/status/403`, el resultado es siempre 403 (sin excepciones). Para cualquier
otra dirección, se tira un "dado" del 0 al 1: el 90 % de las veces sale
"200 - todo bien", un 6 % sale "500 - error del servidor", y el 4 % restante
sale "404 - no encontrado" — para que las estadísticas tengan algo de
variedad realista en vez de ser siempre perfectas.

De forma parecida, el resultado de "¿se pudo interpretar bien esta llamada?"
usa otra tirada de dado con un 5 % de probabilidad de decir "error" (tal como
pide el enunciado), y el resto de las veces dice "ok".

---

## En resumen

Esta fase construyó **las cuatro piezas de razonamiento** que el resto del
programa usará constantemente:

1. **`errors.py`** — el vocabulario para hablar de qué salió mal.
2. **`models.py`** — las fichas con las que se representa cada dato.
3. **`endpoints.py`** — la regla para agrupar direcciones parecidas.
4. **`kpi.py`** — las fórmulas de las estadísticas (incluido el percentil 90).
5. **`generation.py`** — la máquina que inventa datos de ejemplo reproducibles.

Todo esto se comprobó con **44 pruebas automáticas** que verifican, entre
otras cosas: que la simplificación de direcciones da los resultados
esperados, que el percentil 90 coincide con el cálculo de la librería
`numpy`, que las estadísticas se agrupan y ordenan correctamente, y que
generar los mismos datos dos veces con la misma "semilla" da exactamente el
mismo resultado.
