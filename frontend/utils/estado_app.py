"""
Estado global simple compartido entre pantallas de la app.

Se usa App.get_running_app() para acceder a esta instancia desde cualquier
pantalla, siguiendo el mismo patron que en Legal App (en vez de
self.manager.parent).
"""

import json
import os

from kivy.app import App

NOMBRE_ARCHIVO_SESION = "sesion_docente.json"


class EstadoApp:
    """Contiene los datos de la clase que se esta creando en el flujo actual."""

    def __init__(self):
        self.docente_id: str | None = None
        self.docente_nombre: str | None = None
        self.docente_email: str | None = None
        self.docente_plan: str = "gratis"
        self.docente_materia_principal: str | None = None
        self.docente_creado_en: str | None = None
        self.clase_id: str | None = None
        self.codigo_publico: str | None = None
        self.modo_actual: str = "entrada"
        self.contenido_actual: dict = {}
        self.recursos_seleccionados: dict = {
            "voz": True,
            "slides": True,
            "imagenes": True,
            "video": False,
            "pdf": True,
            "pptx": True,
        }
        self.recursos_generados: dict = {
            "voz": None,
            "slides": None,
            "imagenes": [],
            "audios_docente": [],
            "pdf": None,
            "pptx": None,
            "zip": None,
        }
        self.preferencias_apoyo: dict = self._preferencias_apoyo_vacias()
        self.apoyo_accesibilidad_actual: dict | None = None
        self.paquete_alumno_actual: dict | None = None
        self.parametros_voz: dict = {
            "voz": "femenina",
            "idioma": "es",
            "velocidad": 0.9,
        }
        # Pantalla a la que hay que volver despues de guardar una edicion de
        # contenido. En el flujo normal (primera vez) es "adaptar". Si el
        # docente entra a editar la clase desde la pantalla de exportar
        # (clase ya generada/exportada), este valor pasa a "exportar" para
        # que el guardado lo devuelva ahi en lugar de reiniciar el flujo.
        self.pantalla_retorno_edicion: str = "adaptar"

    def _preferencias_apoyo_vacias(self):
        return {
            "tdah": False,
            "tea": False,
            "lectura_facil": False,
            "ansiedad": False,
            "rutina_visual": False,
            "pausas": False,
        }

    def reiniciar_flujo_clase(self):
        """Limpia el estado de la clase actual para empezar una nueva."""
        self.clase_id = None
        self.codigo_publico = None
        self.modo_actual = "docente"
        self.contenido_actual = {}
        self.preferencias_apoyo = self._preferencias_apoyo_vacias()
        self.apoyo_accesibilidad_actual = None
        self.paquete_alumno_actual = None
        self.recursos_generados = {
            "voz": None,
            "slides": None,
            "imagenes": [],
            "audios_docente": [],
            "pdf": None,
            "pptx": None,
            "zip": None,
        }
        self.pantalla_retorno_edicion = "adaptar"

    def cerrar_sesion(self):
        """Limpia datos de docente y clase para volver a la entrada."""
        self.docente_id = None
        self.docente_nombre = None
        self.docente_email = None
        self.docente_plan = "gratis"
        self.docente_materia_principal = None
        self.docente_creado_en = None
        self.modo_actual = "entrada"
        self.reiniciar_flujo_clase()
        self.modo_actual = "entrada"
        self.borrar_sesion()

    def _ruta_sesion(self) -> str | None:
        """Ruta del archivo local donde se guarda la sesion del docente.

        Usa user_data_dir de Kivy porque es la unica carpeta con permiso de
        escritura garantizado tanto en Windows como en Android.
        """
        app = App.get_running_app()
        if app is None:
            return None
        return os.path.join(app.user_data_dir, NOMBRE_ARCHIVO_SESION)

    def guardar_sesion(self):
        """Persiste la sesion actual del docente para que sobreviva a un reinicio."""
        ruta = self._ruta_sesion()
        if not ruta or not self.docente_id:
            return
        datos = {
            "docente_id": self.docente_id,
            "docente_nombre": self.docente_nombre,
            "docente_email": self.docente_email,
            "docente_plan": self.docente_plan,
            "docente_materia_principal": self.docente_materia_principal,
            "docente_creado_en": self.docente_creado_en,
        }
        try:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo)
        except OSError as error:
            print(f"[EstadoApp] No se pudo guardar la sesion: {error}")

    def cargar_sesion(self) -> bool:
        """Restaura la sesion guardada localmente, si existe. Devuelve True si habia una."""
        ruta = self._ruta_sesion()
        if not ruta or not os.path.exists(ruta):
            return False
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, ValueError) as error:
            print(f"[EstadoApp] No se pudo cargar la sesion: {error}")
            return False

        if not datos.get("docente_id"):
            return False

        self.docente_id = datos.get("docente_id")
        self.docente_nombre = datos.get("docente_nombre")
        self.docente_email = datos.get("docente_email")
        self.docente_plan = datos.get("docente_plan") or "gratis"
        self.docente_materia_principal = datos.get("docente_materia_principal")
        self.docente_creado_en = datos.get("docente_creado_en")
        self.modo_actual = "docente"
        return True

    def borrar_sesion(self):
        """Elimina la sesion persistida (usado al cerrar sesion o borrar cuenta)."""
        ruta = self._ruta_sesion()
        if ruta and os.path.exists(ruta):
            try:
                os.remove(ruta)
            except OSError as error:
                print(f"[EstadoApp] No se pudo borrar la sesion: {error}")
