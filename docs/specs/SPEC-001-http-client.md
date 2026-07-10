# SPEC-001 · Cliente HTTP Automatizado

- **ID:** SPEC-001
- **Estado:** Aprobado
- **Requisitos cubiertos:** FR-01…FR-08, FR-11, NFR-03, NFR-10, NFR-14
- **Contratos:** [artefactos del cliente HTTP](../contracts/data-contracts.md#artefactos-del-cliente-http)
- **Decisiones:** [ADR-0004](../adr/0004-http-requests-over-browser-automation.md),
  [ADR-0007](../adr/0007-error-handling-retries-idempotency.md)

## 1. Objetivo

Interactuar con endpoints de `httpbin.org` para cubrir seis escenarios de scraping/
consumo de APIs, produciendo los artefactos `datos.json`, `datos.xml` y
`titulo.html`, con manejo robusto de errores y una única sesión compartida.

## 2. Entradas y salidas

- **Configuración:** constantes en `config.py` (URL base, credenciales de prueba,
  datos de formulario, timeout, reintentos, backoff) con los valores del enunciado.
- **CLI:** `python cliente_http.py` (sin parámetros inventados; el enunciado no define
  script ni flags para la Parte 0).
- **Salidas:** `datos.json`, `datos.xml`, `titulo.html` (nombres exactos del
  enunciado) en `out/`; un **resumen** (log + código de salida) con el estado por
  escenario.

## 3. Comportamiento

Orquestado por `application/http_scenarios.py` sobre `HttpPort`
(`RequestsHttpClient`). Se usa **una sola `requests.Session`** para que las cookies
persistan entre escenarios. Cada escenario es independiente: su fallo se registra y
**no** interrumpe a los demás; el resumen final refleja OK/errores.

| # | Escenario | Acción | Resultado esperado |
|---|---|---|---|
| FR-01 | Auth básica | `GET /basic-auth/usuario_test/clave123` con `HTTPBasicAuth` | `200`, `authenticated=true` |
| FR-02 | Cookies/sesión | `GET /cookies/set?session=activa` → `GET /cookies` | `cookies.session == "activa"` |
| FR-03 | Restricción 403 | `GET /status/403` con reintentos+backoff | `403` detectado, registrado; `AccessForbiddenError` tras agotar reintentos |
| FR-04 | JSON | `GET /get` | `datos.json` con la respuesta |
| FR-05 | XML | `GET /xml` + parseo (`lxml`) | `datos.xml` bien formado |
| FR-06 | HTML | `GET /html` + extracción de título (`bs4`) | `titulo.html` con el título |
| FR-07 | Formulario | `POST /post` con los 4 campos | eco de `form` con los datos |
| FR-08 | Redirección | `GET /redirect-to?url=/get` (`allow_redirects=True`) | respuesta final de `/get`, `history` no vacío |

## 4. Interfaz pública (diseño)

```python
# infrastructure/http/client.py
class RequestsHttpClient:  # implementa HttpPort
    def __init__(self, base_url: str, *, timeout: float, max_retries: int,
                 backoff_factor: float, session: requests.Session | None = None) -> None: ...
    def get(self, path: str, *, auth: tuple[str, str] | None = None,
            allow_redirects: bool = True) -> HttpResponse: ...
    def post(self, path: str, *, data: Mapping[str, str]) -> HttpResponse: ...

# application/http_scenarios.py
@dataclass(frozen=True)
class TaskResult:
    name: str
    ok: bool
    detail: str

def run_all(http: HttpPort, writer: ArtifactWriter, cfg: HttpConfig,
            out_dir: Path) -> list[TaskResult]: ...
```

## 5. Manejo de errores

- `403` (FR-03): reintentos con backoff; al agotarlos, `AccessForbiddenError`
  (registrada, escenario marcado fallido). Ver [ADR-0007](../adr/0007-error-handling-retries-idempotency.md).
- Timeouts / errores de conexión: reintentos; si persisten, `HttpTaskError` en ese
  escenario, sin abortar el resto.
- Escritura de artefactos: errores de E/S ⇒ mensaje accionable con la ruta.
- Credenciales **nunca** se registran (NFR-14).
- Código de salida: `0` si todos los escenarios *obligatorios* fueron OK; `3` si
  hubo fallo de red no recuperable en alguno.

## 6. Criterios de aceptación (Gherkin)

```gherkin
Feature: Autenticación básica (FR-01)
  Scenario: Credenciales válidas
    Given un cliente HTTP configurado con usuario_test/clave123
    When solicita GET /basic-auth/usuario_test/clave123
    Then la respuesta es 200 y authenticated es true

  Scenario: Credenciales inválidas
    Given credenciales incorrectas
    When solicita el endpoint de auth básica
    Then recibe 401 y el escenario se marca fallido sin abortar los demás

Feature: Cookies y sesión (FR-02)
  Scenario: La cookie de sesión persiste
    Given una única sesión HTTP
    When fija /cookies/set?session=activa y luego consulta /cookies
    Then /cookies devuelve session igual a "activa"

Feature: Restricción de acceso 403 (FR-03)
  Scenario: 403 se detecta y reintenta
    Given max_retries = 3 y backoff configurado
    When solicita /status/403
    Then se realizan 3 reintentos, se registra el error y se lanza AccessForbiddenError

Feature: Extracción de datos (FR-04, FR-05, FR-06)
  Scenario: JSON de /get
    When solicita /get
    Then se escribe datos.json con JSON válido equivalente a la respuesta
  Scenario: XML de /xml
    When solicita /xml
    Then se escribe datos.xml bien formado
  Scenario: Título de /html
    When solicita /html
    Then titulo.html contiene el texto del título de la página

Feature: Envío de formulario (FR-07)
  Scenario: POST con datos del formulario
    When envía POST /post con Nombre, Apellido, Correo y Mensaje
    Then la respuesta refleja esos cuatro campos en form

Feature: Redirecciones (FR-08)
  Scenario: Seguir redirección a /get
    When solicita /redirect-to?url=/get
    Then la respuesta final corresponde a /get y history no está vacío
```

## 7. Pruebas asociadas

- `tests/integration/test_http_tasks.py` (con `responses`, sin red): un test por
  escenario (FR-01…FR-08) + credenciales inválidas + agotamiento de reintentos.
- `tests/integration/test_artifacts.py`: `datos.json`/`datos.xml`/`titulo.html` se
  escriben con el contenido correcto en `tmp_path`.
- `tests/network/test_http_live.py` (`@network`, opcional): humo contra httpbin real.

## 8. Trazabilidad

FR-01…FR-08, FR-11, NFR-03/10/14 → ver
[RTM](../requirements/requirements-traceability-matrix.md).
