# ADR-0005 · Configuración por constantes (valores del enunciado)

- **Estado:** Aceptado
- **Fecha:** 2026-07-10

## Contexto

El enunciado provee valores fijos y no sensibles: credenciales de prueba
(`usuario_test` / `clave123`), datos del formulario (Juan, Pérez, correo, mensaje) y
la URL base (`httpbin.org`). No pide un sistema de configuración por entorno. Para
ceñirnos al enunciado (sin invenciones), se evita cualquier maquinaria de `.env` /
variables de entorno.

## Decisión

- **Configuración como constantes tipadas** en `config.py`: un dataclass congelado
  `Settings` cuyos valores por defecto son exactamente los del enunciado (URL base,
  credenciales de prueba, datos del formulario, timeout, reintentos, backoff).
- **Sin `.env`, sin variables de entorno, sin loader propio ni `python-dotenv`.**
- **Overrides por construcción** (no por entorno): las pruebas instancian
  `Settings(...)` con los valores que necesiten; la aplicación usa los defaults.
- **Credenciales:** son las de prueba del enunciado, **no sensibles**, por lo que
  vivir como constantes documentadas es aceptable para este ejercicio. En un escenario
  con secretos reales, estos se inyectarían por construcción desde una fuente segura,
  nunca hardcodeados.
- **Nunca** se registran credenciales en logs ni en mensajes de error.

## Consecuencias

- (+) Ceñido al enunciado; cero infraestructura de configuración inventada (KISS).
- (+) Tipado, inmutable y testeable (overrides explícitos en pruebas).
- (+) Sin dependencias extra.
- (−) Cambiar un valor requiere editar `config.py` (o construir `Settings` con otro
  valor). Aceptable dado que el enunciado fija esos valores.

## Alternativas consideradas

- **Configuración por entorno / `.env` (12-factor):** descartada por invención no
  pedida por el enunciado y por añadir maquinaria innecesaria para valores fijos.
- **Hardcodear valores dispersos en el código:** descartado; se centralizan en
  `config.py` para orden y reutilización (DRY).
