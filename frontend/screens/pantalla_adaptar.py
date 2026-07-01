"""
Pantalla opcional para adaptar la clase a necesidades de atencion y accesibilidad.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from utils import cliente_api


class PantallaAdaptar(Screen):
    """Permite generar apoyos para TDAH, TEA/autismo y lectura facil."""

    def on_pre_enter(self, *args):
        app = MDApp.get_running_app()
        preferencias = getattr(app.estado, "preferencias_apoyo", {}) or {}

        self.ids.check_tdah.active = preferencias.get("tdah", False)
        self.ids.check_tea.active = preferencias.get("tea", False)
        self.ids.check_lectura.active = preferencias.get("lectura_facil", False)
        self.ids.check_ansiedad.active = preferencias.get("ansiedad", False)
        self.ids.check_rutina.active = preferencias.get("rutina_visual", False)
        self.ids.check_pausas.active = preferencias.get("pausas", False)

        if any(preferencias.values()):
            self.ids.etiqueta_estado.text = "Preferencias cargadas desde el inicio."
        else:
            self.ids.etiqueta_estado.text = ""
        self.ids.indicador_carga.active = False
        self.ids.boton_generar.disabled = False
        self.ids.boton_saltar.disabled = False

    def al_presionar_generar_apoyos(self):
        necesidades = []
        if self.ids.check_tdah.active:
            necesidades.append("tdah")
        if self.ids.check_tea.active:
            necesidades.append("tea")
        if self.ids.check_lectura.active:
            necesidades.append("lectura_facil")
        if self.ids.check_ansiedad.active:
            necesidades.append("ansiedad")

        if not necesidades:
            self.ids.etiqueta_estado.text = "Elegi al menos una adaptacion o salta este paso."
            return

        app = MDApp.get_running_app()
        parametros = {
            "necesidades": necesidades,
            "incluir_rutina_visual": self.ids.check_rutina.active,
            "incluir_pausas": self.ids.check_pausas.active,
            "incluir_consignas_cortas": True,
            "nivel_apoyo": "medio",
        }

        self.ids.boton_generar.disabled = True
        self.ids.boton_saltar.disabled = True
        self.ids.indicador_carga.active = True
        self.ids.etiqueta_estado.text = "Adaptando la clase..."

        cliente_api.generar_apoyos_accesibilidad(
            clase_id=app.estado.clase_id,
            parametros_apoyo=parametros,
            callback_exito=self._al_generar_exito,
            callback_error=self._al_generar_error,
        )

    def al_presionar_saltar(self):
        app = MDApp.get_running_app()
        app.root.current = "recursos"

    def _al_generar_exito(self, respuesta_apoyo):
        app = MDApp.get_running_app()
        app.estado.apoyo_accesibilidad_actual = respuesta_apoyo

        self.ids.boton_generar.disabled = False
        self.ids.boton_saltar.disabled = False
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_estado.text = "Clase adaptada."
        app.root.current = "apoyo"

    def _al_generar_error(self, error):
        self.ids.boton_generar.disabled = False
        self.ids.boton_saltar.disabled = False
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_estado.text = cliente_api.mensaje_error(error)
        print(f"[PantallaAdaptar] error al generar apoyos: {error}")
