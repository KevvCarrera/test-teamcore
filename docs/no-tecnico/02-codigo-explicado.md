# Guía del código explicado línea por línea (sin jerga)

> Complementa a [01-estructura-del-proyecto.md](01-estructura-del-proyecto.md)
> (que explica las *carpetas*). Este documento explica el *contenido* de los
> archivos que ya tienen código real, línea por línea, para cualquier persona
> que no programe. Los archivos que están vacíos (los "cajones preparados" de
> `domain/`, `application/`, `infrastructure/`) no se explican aquí porque no
> tienen lógica todavía — solo un comentario que dice qué llegará y en qué fase.

Antes de empezar, tres palabras que van a aparecer todo el rato:

- **Función**: una receta con nombre. Se le dan unos ingredientes (parámetros) y
  devuelve un resultado. Se "llama" por su nombre cada vez que se necesita,
  en vez de reescribir la receta entera cada vez.
- **Clase**: un molde para crear "fichas" con la misma forma. Por ejemplo, un
  molde "Persona" con casillas Nombre/Edad; cada vez que se usa el molde se
  obtiene una ficha distinta pero con las mismas casillas.
- **Tipo** (`str`, `int`, `float`, `bool`): la etiqueta que dice qué clase de
  dato es cada casilla (texto, número entero, número decimal, sí/no). Sirve
  para que, si alguien intenta poner un texto donde debía ir un número, el
  programa avise **antes** de ejecutarse, no cuando ya esté fallando.

---

## 1. `src/teamcore_http_kpi/config.py` — la ficha de configuración

```python
from dataclasses import dataclass
```

Esta línea "importa" (trae prestada) una herramienta de Python llamada
`dataclass`, que sirve para crear fácilmente **fichas de datos fijos** sin
tener que escribir código repetitivo para cada una.

```python
@dataclass(frozen=True)
class FormData:
    """Datos de formulario para el escenario POST /post (FR-07)."""

    nombre: str = "Juan"
    apellido: str = "Pérez"
    correo: str = "juan.perez@example.com"
    mensaje: str = "Este es un mensaje de prueba."
```

- `@dataclass(frozen=True)`: la línea que empieza con `@` es una "etiqueta" que
  modifica lo que viene justo debajo. Aquí dice: "esto es una ficha de datos, y
  además está **congelada** (`frozen`)" — es decir, una vez creada, nadie puede
  cambiar sus casillas por accidente. Es como una hoja impresa, no una pizarra.
- `class FormData:` — el nombre del molde: "Datos de Formulario".
- El texto entre comillas triples justo debajo es un comentario explicativo
  (no es una orden para el programa, es una nota para quien lo lea).
- Cada línea siguiente es una casilla del molde: **nombre** de la casilla, dos
  puntos, **tipo de dato** (`str` = texto), signo igual y **valor por
  defecto**. Estos son exactamente los datos que pide el enunciado del
  ejercicio para el formulario de prueba (Juan Pérez, su correo, su mensaje).

**¿Por qué existe este bloque?** Porque el ejercicio exige enviar siempre esos
mismos datos de prueba al rellenar un formulario. En vez de escribirlos sueltos
en varias partes del código (y arriesgarse a que alguien los escriba distinto
en cada sitio), se guardan **una sola vez, en un solo lugar**.

```python
@dataclass(frozen=True)
class Settings:
    """..."""

    base_url: str = "https://httpbin.org"
    basic_auth_user: str = "usuario_test"
    basic_auth_password: str = "clave123"
    form_data: FormData = FormData()
    timeout_seconds: float = 10.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    retry_on_403: bool = True
```

Mismo patrón que arriba, pero es el molde grande de **toda la configuración**
del programa:

- `base_url`: la dirección web con la que se va a hablar.
- `basic_auth_user` / `basic_auth_password`: las credenciales de prueba del
  enunciado (no son datos sensibles reales — son fijas y públicas, así lo
  explican `docs/adr/0005-configuration-and-secrets.md`).
- `form_data: FormData = FormData()`: aquí una casilla contiene **otra ficha
  completa dentro** (la de los datos del formulario) en vez de un solo texto o
  número.
- `timeout_seconds`: cuántos segundos esperar como máximo antes de considerar
  que la web no responde.
- `max_retries` / `backoff_factor`: si algo falla, cuántas veces reintentar y
  cuánto esperar entre intento e intento (para no insistir demasiado rápido).
- `retry_on_403`: sí/no — si al recibir un "acceso denegado" (403) el programa
  debe reintentar igualmente.

```python
DEFAULT_SETTINGS = Settings()
```

Esta última línea **crea una ficha real**, usando el molde `Settings` con
todos sus valores por defecto, y le pone el nombre `DEFAULT_SETTINGS`
("configuración por defecto"). Es la que el resto del programa usará salvo que
alguna prueba decida construir una configuración distinta a propósito.

---

## 2. `src/teamcore_http_kpi/logging_config.py` — el cuaderno de bitácora

Este archivo decide **cómo se registran los mensajes de diagnóstico** del
programa (qué pasó, en qué orden, si algo falló) — como el cuaderno de bitácora
de un barco, donde se anota todo lo relevante del viaje.

```python
import logging
import sys
from typing import Literal
```

Se importan tres herramientas: `logging` (la herramienta estándar de Python
para registrar mensajes), `sys` (para poder escribir esos mensajes en el canal
correcto de la terminal) y `Literal` (para poder decir "este valor solo puede
ser una de estas dos palabras exactas", como se ve a continuación).

```python
LogFormat = Literal["text", "json"]
```

Define que, cuando alguien elija el "formato" de los mensajes, solo hay dos
opciones válidas: `"text"` (legible para una persona) o `"json"` (un formato
más ordenado para que otro programa lo pueda leer automáticamente). Si alguien
escribe una tercera opción por error, el programa lo señalará antes de
ejecutarse.

```python
_TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
```

La "plantilla" con la que se escribirá cada línea de bitácora en modo texto:
fecha y hora, nivel de gravedad (informativo, advertencia, error...), quién lo
dijo, y el mensaje.

```python
class _JsonFormatter(logging.Formatter):
    """Formateador JSON básico (una línea por registro de log)."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)
```

Este bloque crea un molde alternativo de "cómo se ve cada línea de bitácora",
pero en formato `json` (un formato de datos muy usado, parecido a una ficha con
casillas con nombre: `{"nivel": "INFO", "mensaje": "..."}`). El nombre empieza
con guion bajo (`_JsonFormatter`) por convención, para señalar "esto es una
pieza interna de este archivo, no hace falta usarla desde fuera".

- `def format(...)`: esta es la "receta" que arma la línea. Toma un registro
  (`record`, el mensaje crudo) y devuelve el texto final ya formateado.
- Dentro, se arma un diccionario (`payload`) con cuatro casillas —
  fecha/hora, nivel, nombre de quién habla, y mensaje — y se convierte a texto
  JSON con `json.dumps(...)`.

```python
def setup_logging(level: int = logging.INFO, fmt: LogFormat = "text") -> None:
    """Configura el logger raíz una única vez (composition root)."""
    handler = logging.StreamHandler(stream=sys.stderr)
    formatter: logging.Formatter = (
        _JsonFormatter() if fmt == "json" else logging.Formatter(_TEXT_FORMAT)
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
```

Esta es la función principal del archivo: **"configura la bitácora"**. Se llama
una sola vez, al arrancar cualquiera de los programas (`cliente_http.py`,
`generar_datos.py`, etc.).

- `def setup_logging(level=..., fmt=...) -> None:` — define la función, con dos
  ingredientes opcionales (si no se indican, usa los valores por defecto:
  nivel informativo y formato texto), y aclara que no devuelve ningún resultado
  (`-> None`), solo configura algo.
- `handler = logging.StreamHandler(stream=sys.stderr)`: decide que los mensajes
  van a salir por el canal de **errores/diagnóstico** de la terminal
  (`stderr`), **no** por el canal de datos normal (`stdout`). Así, si el
  programa además imprime datos "de verdad" (por ejemplo, un archivo generado),
  esos datos no se mezclan con los mensajes de diagnóstico.
- `formatter = ...`: elige qué plantilla usar (texto o JSON) según lo que se
  haya pedido.
- `handler.setFormatter(formatter)`: le dice al canal de salida "usa esta
  plantilla para escribir cada línea".
- `root = logging.getLogger()`: toma "el cuaderno de bitácora principal" del
  programa completo.
- `root.handlers.clear()`: lo deja en blanco antes de configurar (para que, si
  se llama por accidente dos veces, no se dupliquen los mensajes).
- `root.addHandler(handler)`: conecta el canal de salida que se preparó arriba.
- `root.setLevel(level)`: decide a partir de qué gravedad se registran
  mensajes (por ejemplo, "informativo" hacia arriba; los mensajes de detalle
  fino no aparecerán a menos que se pida explícitamente).

**¿Por qué no se usa simplemente `print()`?** Porque `print` no permite elegir
nivel de gravedad, ni destino, ni formato — y el enunciado y las buenas
prácticas piden algo más ordenado y configurable (ver
`docs/adr/0006-logging-strategy.md`).

---

## 3. `src/teamcore_http_kpi/cli/_common.py` — códigos de resultado compartidos

```python
EXIT_OK = 0
EXIT_DATA_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_NETWORK_ERROR = 3
```

Cuatro nombres con un número cada uno. Cuando un programa termina, deja un
"código de salida" — un número que otros programas (o una persona revisando)
pueden usar para saber si todo salió bien o qué tipo de problema hubo, sin
tener que leer el texto del mensaje. Aquí se les pone un **nombre legible** a
esos números (en vez de escribir `1` a secas en varios sitios y que nadie
recuerde qué significa), siguiendo la convención ya decidida en
`docs/adr/0007-error-handling-retries-idempotency.md`:

- `0` = todo salió bien.
- `1` = problema con los datos o el archivo de entrada.
- `2` = problema de configuración o de cómo se llamó al programa.
- `3` = problema de red/conexión que no se pudo resolver.

---

## 4. Los archivos de cada "botón" (`cli/generar_datos.py` y similares)

Los cuatro archivos (`cliente_http.py`, `generar_datos.py`, `calcular_kpi.py`,
`generar_reporte.py` dentro de `cli/`) tienen, por ahora, la misma forma.
Ejemplo con `generar_datos.py`:

```python
"""CLI `generar_datos.py`: genera la bitácora sintética (FR-09).

Pendiente de implementación en Fase 5 (ver TODO.md). Diseño en
docs/specs/SPEC-002-generar-datos.md.
"""


def main() -> int:
    """Punto de entrada de la CLI. Implementación pendiente (Fase 5)."""
    raise NotImplementedError("generar_datos.py se implementa en la Fase 5 (ver TODO.md)")
```

- El texto entre comillas triples al principio del archivo es una nota que
  explica el propósito del archivo completo (a qué requisito pertenece, en qué
  fase se completará).
- `def main() -> int:` — se define la función principal, la que se ejecutará
  cuando alguien use este "botón". Se declara que **cuando esté terminada**
  devolverá un número entero (el código de salida explicado arriba).
- `raise NotImplementedError(...)`: esto es, literalmente, un **cartel de "en
  construcción"**. Si alguien intenta ejecutar este botón ahora mismo, el
  programa se detiene y muestra ese mensaje explicando que todavía falta
  implementarlo y en qué fase se hará. Es intencional: mejor un aviso claro que
  un botón que parece funcionar pero no hace nada.

---

## 5. Los 4 archivos "atajo" en la raíz del proyecto

Ejemplo con `generar_datos.py` (el que está en la carpeta principal, no dentro
de `cli/`):

```python
#!/usr/bin/env python
"""Shim raíz: delega en `teamcore_http_kpi.cli.generar_datos:main` (ver ADR-0008)."""

from teamcore_http_kpi.cli.generar_datos import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- La primera línea (`#!/usr/bin/env python`) es una convención técnica que
  indica "este archivo se ejecuta con Python" — relevante en sistemas tipo
  Linux/Mac, inofensiva en Windows.
- El texto entre comillas explica que este archivo es un simple **atajo** (en
  inglés, a este tipo de archivo se le llama informalmente "shim", literalmente
  una "cuña" que conecta dos piezas).
- `from teamcore_http_kpi.cli.generar_datos import main`: "trae prestada" la
  función `main` real, la que vive dentro de `src/teamcore_http_kpi/cli/`.
- `if __name__ == "__main__":` — una forma estándar en Python de decir "esto se
  ejecuta solo si alguien llama a *este archivo* directamente" (y no si otro
  archivo lo usa internamente como pieza).
- `raise SystemExit(main())`: ejecuta la función real y termina el programa
  usando el número que esa función devuelva como código de salida.

**¿Por qué existen estos atajos si ya existe el archivo real dentro de
`cli/`?** Porque el enunciado del ejercicio exige poder ejecutar
`python generar_datos.py ...` **desde la carpeta principal**, tal cual. Sin
este atajo, habría que escribir una ruta más larga y menos amigable.

---

## 6. `tests/conftest.py` — herramientas compartidas para las pruebas

```python
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
```

Se importan: una etiqueta de tipo para "algo que se puede recorrer paso a
paso" (`Iterator`), herramientas para trabajar con fechas en formato universal
(`UTC`, `datetime`), una herramienta para manejar rutas de archivos de forma
segura en cualquier sistema operativo (`Path`), y la librería de pruebas
`pytest`.

```python
@pytest.fixture
def tmp_out(tmp_path: Path) -> Iterator[Path]:
    """Directorio temporal de salida para artefactos generados en pruebas."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    yield out_dir
```

- `@pytest.fixture`: una etiqueta que dice "esto no es una prueba en sí, es una
  **pieza reutilizable** que otras pruebas pueden pedir prestada".
- `tmp_path`: una carpeta temporal que `pytest` crea automáticamente y borra
  sola al terminar — así ninguna prueba ensucia el proyecto real con archivos
  de sobra.
- `out_dir = tmp_path / "out"` y `out_dir.mkdir()`: dentro de esa carpeta
  temporal, se crea una subcarpeta llamada `out` (imitando la carpeta real de
  resultados).
- `yield out_dir`: "entrega" esa carpeta a la prueba que la pidió, para que la
  use como si fuera la carpeta de resultados real.

```python
@pytest.fixture
def seed() -> int:
    """Semilla determinista por defecto para pruebas de generación."""
    return 42
```

Otra pieza reutilizable: el número `42`, usado como "semilla" para que los
datos de ejemplo generados sean siempre los mismos entre una ejecución y otra
(reproducibilidad, ver `docs/adr/0009-data-contracts-and-formats.md`).

```python
@pytest.fixture
def frozen_ref_utc() -> datetime:
    """Instante UTC de referencia fijo, inyectado a nivel de función de dominio."""
    return datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)
```

Una fecha y hora **fija** (9 de julio de 2026, mediodía) que las pruebas usarán
como "ahora mismo" simulado. Es necesario porque, si se usara la hora real del
reloj, las pruebas darían un resultado distinto cada día y sería imposible
comprobar que el resultado es siempre igual.

---

## 7. `tests/unit/test_architecture_layering.py` — el vigilante de las reglas de orden

Este es el archivo más "técnico" de todos, así que vale la pena explicarlo con
calma: **su trabajo es comprobar que nadie mezcló por error el "cerebro"
(`domain`) con las partes que hablan de internet, archivos o gráficos.**

```python
import ast
from pathlib import Path

import pytest

_FORBIDDEN_ROOTS = {"requests", "pandas", "matplotlib", "bs4", "lxml", "argparse"}
_DOMAIN_DIR = Path(__file__).resolve().parents[2] / "src" / "teamcore_http_kpi" / "domain"
```

- `ast`: una herramienta de Python que permite **leer código como si fuera un
  texto**, sin ejecutarlo, y entender su estructura (qué funciones hay, qué
  cosas importa, etc.) — como analizar la gramática de una frase sin
  necesariamente hacer lo que la frase dice.
- `_FORBIDDEN_ROOTS`: la lista de nombres de librerías **prohibidas** dentro
  del "cerebro": las que hablan de internet (`requests`), hojas de cálculo
  (`pandas`), gráficos (`matplotlib`), lectura de HTML/XML (`bs4`, `lxml`) o
  argumentos de línea de comandos (`argparse`). Si el "cerebro" necesitara
  cualquiera de estas, algo estaría mal diseñado.
- `_DOMAIN_DIR`: calcula automáticamente la ruta de la carpeta `domain/`,
  partiendo de dónde está este propio archivo de prueba (así, aunque el
  proyecto se mueva de sitio, la ruta se sigue calculando bien).

```python
def _imported_roots(source: str) -> set[str]:
    """Devuelve los nombres raíz de todos los módulos importados en `source`."""
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots
```

Esta función toma el **texto** de un archivo de código (`source`) y devuelve la
lista de nombres de librerías que ese archivo "importa" (trae prestadas),
sin ejecutar ni una sola línea de ese código — solo analiza su forma.

- `tree = ast.parse(source)`: convierte el texto en una especie de "mapa" de su
  estructura interna.
- `for node in ast.walk(tree):`: recorre ese mapa pieza por pieza.
- Las dos condiciones (`ast.Import` / `ast.ImportFrom`) cubren las dos formas
  que existen en Python de importar algo (`import x` y `from x import y`), y
  en ambos casos se queda solo con el **primer nombre** (por ejemplo, de
  `pandas.io.csv` se queda solo con `pandas`).
- Al final devuelve el conjunto de nombres encontrados.

```python
@pytest.mark.unit
def test_domain_does_not_import_infrastructure_libraries() -> None:
    """Ningún módulo de `domain` importa librerías de E/S, red o CLI."""
    domain_files = sorted(_DOMAIN_DIR.glob("*.py"))
    assert domain_files, f"No se encontraron módulos de dominio en {_DOMAIN_DIR}"

    violations: dict[str, set[str]] = {}
    for path in domain_files:
        forbidden = _imported_roots(path.read_text(encoding="utf-8")) & _FORBIDDEN_ROOTS
        if forbidden:
            violations[path.name] = forbidden

    assert not violations, f"Módulos de dominio con imports prohibidos: {violations}"
```

Esta es la prueba en sí (el nombre que empieza con `test_` es la convención que
`pytest` usa para reconocer "esto hay que ejecutarlo como comprobación").

- `domain_files = sorted(_DOMAIN_DIR.glob("*.py"))`: hace una lista de todos
  los archivos `.py` dentro de la carpeta `domain/`.
- `assert domain_files, "..."`: **comprueba** que esa lista no esté vacía (si
  no hubiera ningún archivo, sería un error de configuración, no un éxito
  vacío).
- El bucle `for path in domain_files:` revisa archivo por archivo: para cada
  uno, calcula qué librerías importa (usando la función explicada arriba) y se
  queda solo con las que estén en la lista de prohibidas.
- Si encuentra alguna, la anota en el diccionario `violations` (algo así como
  "este archivo — estas librerías prohibidas que usa").
- La última línea, `assert not violations, "..."`, es el veredicto final: si
  `violations` está vacío, la prueba pasa; si no, la prueba **falla** y muestra
  exactamente qué archivo rompió la regla y con qué librería.

**¿Por qué importa esto?** Es la manera automática de vigilar, para siempre,
que la regla explicada en la guía de estructura ("el cerebro no debe saber de
internet, archivos ni pantallas") se mantenga con el paso del tiempo, aunque
distintas personas trabajen en el proyecto en el futuro.

---

## En resumen

Todo el código escrito hasta ahora tiene uno de estos dos propósitos:

1. **Guardar valores fijos una sola vez** (`config.py`, `_common.py`) para no
   repetirlos ni arriesgarse a que no coincidan entre distintas partes del
   programa.
2. **Preparar el terreno y vigilar las reglas** (`logging_config.py`, los
   atajos, `conftest.py`, la prueba de arquitectura) para que, cuando en la
   próxima fase se escriba la lógica real (los cálculos, las conexiones a
   internet...), todo encaje en el orden ya decidido y cualquier error de
   estructura salte a la vista de inmediato.
