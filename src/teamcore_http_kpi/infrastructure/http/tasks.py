"""Los 6 escenarios contra httpbin.org: auth básica, cookies, 403, extracciones
JSON/XML/HTML, formulario y redirección.
"""

from html import escape
from pathlib import Path

from bs4 import BeautifulSoup
from lxml import etree

from teamcore_http_kpi.application.ports import ArtifactWriter, HttpPort
from teamcore_http_kpi.config import Settings
from teamcore_http_kpi.domain.errors import AccessForbiddenError, HttpTaskError


def basic_auth(http: HttpPort, settings: Settings) -> str:
    """Autenticación básica contra `/basic-auth/{user}/{pass}` (FR-01)."""
    path = f"/basic-auth/{settings.basic_auth_user}/{settings.basic_auth_password}"
    response = http.get(path, auth=(settings.basic_auth_user, settings.basic_auth_password))
    payload = response.json()
    if response.status_code != 200 or payload.get("authenticated") is not True:
        raise HttpTaskError(f"Autenticación básica falló: status={response.status_code}")
    return f"autenticado como {payload.get('user')}"


def set_and_get_cookies(http: HttpPort) -> str:
    """Fija una cookie de sesión y confirma que la misma sesión la conserva (FR-02)."""
    http.get("/cookies/set?session=activa")
    response = http.get("/cookies")
    session = response.json().get("cookies", {}).get("session")
    if session != "activa":
        raise HttpTaskError(f"La cookie de sesión no persistió (valor recibido: {session!r})")
    return "cookie de sesión confirmada: session=activa"


def simulate_forbidden(http: HttpPort) -> str:
    """Provoca un 403 en `/status/403` y confirma que se maneja correctamente (FR-03).

    Aquí el "éxito" del escenario es justamente que, tras agotar los
    reintentos configurados, el cliente lo detecte y avise con
    `AccessForbiddenError` — por eso esa excepción se atrapa aquí mismo en
    vez de dejarla subir como un fallo genérico.
    """
    try:
        http.get("/status/403")
    except AccessForbiddenError:
        return "403 detectado y manejado tras agotar los reintentos configurados"
    raise HttpTaskError("Se esperaba un 403 en /status/403 y no se recibió")


def extract_json(http: HttpPort, writer: ArtifactWriter, out_dir: Path) -> str:
    """Extrae el JSON de `/get` y lo guarda en `datos.json` (FR-04)."""
    response = http.get("/get")
    writer.write_json(response.json(), out_dir / "datos.json")
    return "datos.json escrito"


def extract_xml(http: HttpPort, writer: ArtifactWriter, out_dir: Path) -> str:
    """Parsea el XML de `/xml` y lo guarda, bien formado, en `datos.xml` (FR-05).

    Se reserializa en vez de escribir `response.content` tal cual, para
    validar el XML y normalizar declaración/encoding.
    """
    response = http.get("/xml")
    root = etree.fromstring(response.content)
    sample = root.get("title", root.tag)
    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    writer.write_xml(xml_bytes, out_dir / "datos.xml")
    return f"datos.xml escrito (dato representativo: {sample!r})"


def extract_html_title(http: HttpPort, writer: ArtifactWriter, out_dir: Path) -> str:
    """Extrae el título (o el encabezado principal, como fallback) de `/html` (FR-06).

    Se escapa antes de escribirlo: viene de una fuente externa no confiable.
    """
    response = http.get("/html")
    soup = BeautifulSoup(response.text, "lxml")

    title = soup.title.string if soup.title and soup.title.string else None
    if title is None:
        heading = soup.find("h1")
        title = heading.get_text(strip=True) if heading else None
    if title is None:
        raise HttpTaskError("No se encontró título ni encabezado principal en /html")

    writer.write_text(f"<title>{escape(title)}</title>", out_dir / "titulo.html")
    return f"titulo.html escrito (título: {title!r})"


def submit_form(http: HttpPort, settings: Settings) -> str:
    """Envía el formulario de prueba a `/post` y confirma el eco de sus 4 campos (FR-07)."""
    form_data = settings.form_data
    form = {
        "nombre": form_data.nombre,
        "apellido": form_data.apellido,
        "correo": form_data.correo,
        "mensaje": form_data.mensaje,
    }
    response = http.post("/post", data=form)
    echoed = response.json().get("form", {})
    if echoed != form:
        raise HttpTaskError(f"El formulario no se reflejó igual en la respuesta: {echoed}")
    return "formulario reflejado correctamente en la respuesta"


def follow_redirect(http: HttpPort) -> str:
    """Sigue `/redirect-to?url=/get` hasta la respuesta final (FR-08)."""
    response = http.get("/redirect-to?url=/get")
    if response.status_code != 200 or not response.history:
        raise HttpTaskError("La redirección no llegó a /get o no dejó historial")
    return f"redirección seguida ({len(response.history)} salto(s)) hasta /get"
