"""Configuración del proyecto como constantes tipadas.

Sin `.env` ni variables de entorno (ver docs/adr/0005-configuration-and-secrets.md).
Los valores por defecto son exactamente los fijados por el enunciado
(`spec/Test Tecnico.md`): URL base, credenciales de prueba y datos de formulario.
Las pruebas construyen `Settings(...)` con overrides explícitos cuando lo necesiten.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormData:
    """Datos de formulario para el escenario POST /post (FR-07)."""

    nombre: str = "Juan"
    apellido: str = "Pérez"
    correo: str = "juan.perez@example.com"
    mensaje: str = "Este es un mensaje de prueba."


@dataclass(frozen=True)
class Settings:
    """Configuración del cliente HTTP y de los escenarios (FR-01…FR-08).

    Los valores por defecto son los del enunciado. No hay secretos reales:
    las credenciales son de prueba y no sensibles (NFR-14).
    """

    base_url: str = "https://httpbin.org"
    basic_auth_user: str = "usuario_test"
    basic_auth_password: str = "clave123"
    form_data: FormData = FormData()
    timeout_seconds: float = 10.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    retry_on_403: bool = True


DEFAULT_SETTINGS = Settings()
