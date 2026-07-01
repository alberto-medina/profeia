"""
Estado global simple compartido entre pantallas de la app.

Se usa App.get_running_app() para acceder a esta instancia desde cualquier
pantalla, siguiendo el mismo patron que en Legal App (en vez de
self.manager.parent).
"""


class EstadoApp:
    """Contiene los datos de la clase que se esta creando en el flujo actual."""

    def __init__(self):
        self.docente_id: str | None = None
        self.docente_nombre: str | None = None
        self.docente_email: str | None = None
        self.docente_plan: str = "gratis"
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
        self.modo_actual = "entrada"
        self.reiniciar_flujo_clase()
        self.modo_actual = "entrada"
