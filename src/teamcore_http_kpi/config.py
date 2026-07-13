"""Configuración del proyecto, como constantes tipadas en lugar de `.env`."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormData:
    """Los datos que se envían al simular el formulario de `/post`."""

    nombre: str = "Juan"
    apellido: str = "Pérez"
    correo: str = "juan.perez@example.com"
    mensaje: str = "Este es un mensaje de prueba."


@dataclass(frozen=True)
class Settings:
    """Configuración del cliente HTTP: URL base, credenciales de prueba (no
    secretos reales) y política de reintentos.
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
