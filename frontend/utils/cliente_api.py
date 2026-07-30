"""
Cliente HTTP simple para comunicarse con el backend de ProfeIA (FastAPI).

Usa requests de forma sincrona pero envuelta en hilos (threading), siguiendo
el mismo patron que en Legal App: las llamadas de red nunca deben bloquear
el hilo principal de Kivy, y las actualizaciones de UI resultantes se
despachan con Clock.schedule_once.
"""

import json
import os
import threading
from pathlib import Path

import requests
from kivy.clock import Clock

URL_BASE_API_PREDETERMINADA = "http://127.0.0.1:8001"


def _cargar_url_base_api() -> str:
    """Carga la URL del backend desde env o api_config.json."""
    url_env = os.environ.get("PROFEIA_API_URL", "").strip()
    if url_env:
        return url_env.rstrip("/")

    ruta_config = Path(__file__).resolve().parents[1] / "api_config.json"
    if ruta_config.exists():
        try:
            datos_config = json.loads(ruta_config.read_text(encoding="utf-8-sig"))
            url_config = str(datos_config.get("api_url", "")).strip()
            if url_config:
                return url_config.rstrip("/")
        except (OSError, json.JSONDecodeError):
            pass

    return URL_BASE_API_PREDETERMINADA


# URL base del backend. Para Android se configura con scripts/set_android_api_url.ps1.
URL_BASE_API = _cargar_url_base_api()

TIMEOUT_SEGUNDOS = 30
# Llamadas que disparan generacion con IA (contenido, voz, imagenes) pueden
# tardar bastante mas que una consulta comun: encadenan varios proveedores
# de fallback y, en el caso de Hugging Face, a veces esperan a que el
# modelo "despierte" antes de generar. Un timeout corto (30s) cortaba la
# conexion del lado del celular mientras el backend seguia trabajando (y
# el docente terminaba viendo un error aunque el recurso se generara bien
# igual, solo que tarde para enterarse).
TIMEOUT_GENERACION_SEGUNDOS = 120


def mensaje_error(error) -> str:
    """Extrae un mensaje legible desde errores HTTP del backend."""
    respuesta = getattr(error, "response", None)
    if respuesta is not None:
        try:
            detalle = respuesta.json().get("detail")
            if isinstance(detalle, str) and detalle:
                return detalle
        except ValueError:
            pass
    return str(error)


def _ejecutar_en_hilo(funcion_objetivo, callback_exito, callback_error):
    """Ejecuta una funcion de red en un hilo y despacha el resultado al hilo de UI."""

    def tarea():
        try:
            resultado = funcion_objetivo()
            Clock.schedule_once(lambda dt: callback_exito(resultado))
        except Exception as error:  # noqa: BLE001 - error de red generico
            Clock.schedule_once(lambda dt, error=error: callback_error(error))

    threading.Thread(target=tarea, daemon=True).start()


def crear_clase(docente_id: str, datos_prompt: dict, callback_exito, callback_error):
    """POST /clases - crea una clase nueva a partir de un prompt."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases",
            params={"docente_id": docente_id},
            json=datos_prompt,
            timeout=TIMEOUT_GENERACION_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def listar_clases(docente_id: str, callback_exito, callback_error):
    """GET /clases - lista clases del docente."""

    def llamada():
        respuesta = requests.get(
            f"{URL_BASE_API}/clases",
            params={"docente_id": docente_id},
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def registrar_docente(datos_docente: dict, callback_exito, callback_error):
    """POST /perfil/registro - crea cuenta docente local."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/perfil/registro",
            json=datos_docente,
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def iniciar_sesion_docente(credenciales: dict, callback_exito, callback_error):
    """POST /perfil/login - inicia sesion docente local."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/perfil/login",
            json=credenciales,
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def eliminar_cuenta_docente(datos_eliminacion: dict, callback_exito, callback_error):
    """POST /perfil/eliminar - elimina la cuenta docente."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/perfil/eliminar",
            json=datos_eliminacion,
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def listar_planes(callback_exito, callback_error):
    """GET /planes - lista planes disponibles."""

    def llamada():
        respuesta = requests.get(
            f"{URL_BASE_API}/planes",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def obtener_uso_plan(docente_id: str, plan_id: str | None, callback_exito, callback_error):
    """GET /planes/docentes/{id}/uso - uso del docente contra un plan."""

    def llamada():
        params = {}
        if plan_id:
            params["plan_id"] = plan_id
        respuesta = requests.get(
            f"{URL_BASE_API}/planes/docentes/{docente_id}/uso",
            params=params,
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def crear_checkout_suscripcion(datos_suscripcion: dict, callback_exito, callback_error):
    """POST /pagos/suscripciones/mercado-pago - checkout de suscripcion."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/pagos/suscripciones/mercado-pago",
            json=datos_suscripcion,
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def activar_suscripcion_demo(datos_suscripcion: dict, callback_exito, callback_error):
    """POST /pagos/suscripciones/demo/activar - activa plan demo."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/pagos/suscripciones/demo/activar",
            json=datos_suscripcion,
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def editar_clase(clase_id: str, contenido_json: dict, callback_exito, callback_error):
    """PUT /clases/{id} - guarda la edicion manual del contenido."""

    def llamada():
        respuesta = requests.put(
            f"{URL_BASE_API}/clases/{clase_id}",
            json={"contenido_json": contenido_json},
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def generar_voz(clase_id: str, parametros_voz: dict, callback_exito, callback_error):
    """POST /clases/{id}/voz - genera el audio narrado."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/voz",
            json=parametros_voz,
            timeout=TIMEOUT_GENERACION_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def generar_imagenes(clase_id: str, parametros_imagenes: dict, callback_exito, callback_error):
    """POST /clases/{id}/imagenes - genera imagenes de apoyo."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/imagenes",
            json=parametros_imagenes,
            timeout=TIMEOUT_GENERACION_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def generar_opciones_imagenes(clase_id: str, parametros_imagenes: dict, callback_exito, callback_error):
    """POST /clases/{id}/imagenes/opciones - genera alternativas de imagen."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/imagenes/opciones",
            json=parametros_imagenes,
            timeout=TIMEOUT_GENERACION_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def buscar_imagenes_web(clase_id: str, cantidad: int, callback_exito, callback_error):
    """POST /clases/{id}/imagenes/buscar-web - busca imagenes gratuitas."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/imagenes/buscar-web",
            params={"cantidad": cantidad},
            timeout=TIMEOUT_GENERACION_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def generar_slides(clase_id: str, callback_exito, callback_error):
    """POST /clases/{id}/slides - genera la estructura de diapositivas."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/slides",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def adjuntar_recurso(clase_id: str, datos_recurso: dict, callback_exito, callback_error):
    """POST /clases/{id}/recursos - adjunta imagen o audio del docente."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/recursos",
            json=datos_recurso,
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def subir_recurso(clase_id: str, tipo: str, ruta_archivo: str, callback_exito, callback_error):
    """POST /clases/{id}/recursos/upload - sube imagen/audio del docente."""

    def llamada():
        with open(ruta_archivo, "rb") as archivo:
            respuesta = requests.post(
                f"{URL_BASE_API}/clases/{clase_id}/recursos/upload",
                data={
                    "tipo": tipo,
                    "descripcion": "Recurso subido desde la app.",
                },
                files={
                    "archivo": (Path(ruta_archivo).name, archivo),
                },
                timeout=TIMEOUT_SEGUNDOS,
            )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def generar_apoyos_accesibilidad(
    clase_id: str,
    parametros_apoyo: dict,
    callback_exito,
    callback_error,
):
    """POST /clases/{id}/accesibilidad/apoyos - adapta la clase."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/accesibilidad/apoyos",
            json=parametros_apoyo,
            timeout=TIMEOUT_GENERACION_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def obtener_paquete_alumno(clase_id: str, callback_exito, callback_error):
    """GET /clases/{id}/alumno/paquete - vista alumno."""

    def llamada():
        respuesta = requests.get(
            f"{URL_BASE_API}/clases/{clase_id}/alumno/paquete",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def obtener_paquete_alumno_por_codigo(codigo_publico: str, callback_exito, callback_error):
    """GET /publico/clases/{codigo} - vista alumno por codigo."""

    def llamada():
        respuesta = requests.get(
            f"{URL_BASE_API}/publico/clases/{codigo_publico.strip().upper()}",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def exportar_zip_por_codigo(codigo_publico: str, callback_exito, callback_error):
    """POST /publico/clases/{codigo}/exportar/zip - paquete alumno por codigo."""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/publico/clases/{codigo_publico.strip().upper()}/exportar/zip",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def exportar_pdf(clase_id: str, callback_exito, callback_error):
    """POST /clases/{id}/exportar/pdf"""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/exportar/pdf",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def exportar_pptx(clase_id: str, callback_exito, callback_error):
    """POST /clases/{id}/exportar/pptx"""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/exportar/pptx",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)


def exportar_zip(clase_id: str, callback_exito, callback_error):
    """POST /clases/{id}/exportar/zip"""

    def llamada():
        respuesta = requests.post(
            f"{URL_BASE_API}/clases/{clase_id}/exportar/zip",
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    _ejecutar_en_hilo(llamada, callback_exito, callback_error)
