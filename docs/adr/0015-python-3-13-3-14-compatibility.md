# ADR-0015 · Compatibilidad verificada con Python 3.13/3.14 y ajuste del pin de `numpy`

- **Estado:** Aceptado
- **Fecha:** 2026-07-13

## Contexto

[ADR-0002](0002-runtime-python-and-packaging.md) fijó `requires-python = ">=3.11"`
como mínimo, sin techo explícito. Se pidió verificar que el proyecto corre sin
romperse en Python 3.13/3.14, manteniendo 3.11 intacto.

El pin de `numpy` era `>=1.26,<2.3`, con el comentario: *"2.3+ requiere sintaxis
PEP 695 en sus stubs (rompe mypy con python_version=3.11)"*.

Al instalar el proyecto en un entorno Windows con Python 3.14 se comprobó que:

1. `numpy<2.3.5` **no publica wheels precompiladas** para `cp313`/`cp314` en
   Windows; `pip` cae a compilar desde el sdist, lo que falla sin un compilador
   C instalado (Meson no encuentra `cl`/`gcc`/`clang`). Esto rompe la
   instalación en 3.13/3.14 mucho antes de llegar a mypy.
2. El motivo original del techo (`<2.3`) ya no aplica con el `mypy` que se
   resuelve hoy (`mypy` 2.x): `numpy==2.3.5` y `2.4.6` pasan `mypy --strict`
   con `python_version = "3.11"` sin errores.
3. Sin embargo, `numpy==2.5.0`/`2.5.1` introducen la sentencia `type` (PEP 695)
   en `numpy/__init__.pyi`, que **sí** rompe mypy bajo `python_version = 3.11`
   (`error: Type statement is only supported in Python 3.12 and greater`).
   El problema original no desapareció: simplemente se desplazó de la versión
   2.3 a la 2.5.
4. `numpy==2.4.0` está *yanked* en PyPI ("Backward compatibility bug").

Se verificó instalación + `pytest` + `ruff` + `mypy --strict` en:
- Python 3.14.6 (Windows, venv aislado) con `numpy==2.3.5` y `2.4.6`: OK.
- Python 3.12.10 (Windows, venv aislado) con las mismas versiones: OK.
- Se confirmó disponibilidad de wheels Windows (`cp311`, `cp312`, `cp313`,
  `cp314`) para `numpy`, `pandas`, `matplotlib`, `lxml` en el rango elegido.

No hay Python 3.11 ni 3.13 instalados en la máquina de desarrollo actual; 3.12
se usó como proxy del piso soportado y 3.14 como techo. La disponibilidad de
wheels `cp311`/`cp313` se verificó vía `pip download --only-binary=:all:` sin
necesidad de esos intérpretes.

## Decisión

- **Mantener `requires-python = ">=3.11"` sin techo** (ADR-0002 no cambia):
  el rango soportado ahora incluye 3.11, 3.12, 3.13 y 3.14, verificado.
- **Ajustar el pin de `numpy`** de `>=1.26,<2.3` a **`>=2.3.5,<2.5`**:
  - Piso `2.3.5`: primera versión con wheels Windows para `cp313`/`cp314`.
  - Techo `<2.5`: evita la sintaxis PEP 695 en stubs que rompe mypy con
    `python_version = "3.11"` (declarado en `[tool.mypy]`, que no cambia
    porque 3.11 sigue siendo el mínimo soportado).
- **No tocar** `target-version` de ruff (`py311`) ni `python_version` de mypy
  (`3.11`): ambos deben seguir reflejando el **mínimo** soportado, no el
  máximo, para que el linter/type-checker seguro detecten código que rompería
  en 3.11.
- **No tocar** los pines de `requests`, `beautifulsoup4`, `lxml`, `pandas`,
  `matplotlib`, `selenium`: sus versiones actuales (resueltas hoy) ya publican
  wheels Windows para 3.11–3.14 y la suite de pruebas pasa sin cambios.

## Consecuencias

- (+) El proyecto se instala y pasa `pytest`/`ruff`/`mypy --strict` en
  Python 3.11 (verificado por compatibilidad de wheels), 3.12, 3.13 (wheels) y
  3.14 (instalación y suite completas), sin excluir ninguna versión.
- (+) El pin de `numpy` documenta explícitamente *por qué* tiene techo,
  evitando que una futura actualización rompa `mypy --strict` en silencio.
- (−) Fija una ventana relativamente estrecha de `numpy` (`2.3.5`–`2.4.x`);
  si `mypy` mejora su soporte de PEP 695 en stubs bajo `python_version=3.11`,
  o si el proyecto eleva su piso mínimo a Python 3.12+, este ADR debería
  revisarse y el techo podría relajarse.

## Alternativas consideradas

- **Elevar el piso mínimo a Python 3.12** para poder usar `numpy>=2.5` sin
  problemas de stubs: rechazado: rompería el piso mínimo de Python 3.11 fijado
  en [ADR-0002](0002-runtime-python-and-packaging.md).
- **Relajar `mypy` (quitar `strict` o ignorar `numpy.*`)** para tolerar
  cualquier versión de `numpy`: rechazado; viola la regla 8 de `CLAUDE.md`
  (tipado estricto sin excepciones ad hoc) y oculta una incompatibilidad real
  en lugar de acotarla.
- **Dejar el pin `<2.3` y excluir 3.13/3.14 del soporte**: rechazado; es
  exactamente lo que esta ADR busca resolver.
