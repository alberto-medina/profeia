"""
Pantalla de lectura de apoyos de accesibilidad generados.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp


class PantallaApoyo(Screen):
    """Muestra la adaptacion generada antes de elegir recursos."""

    def on_pre_enter(self, *args):
        app = MDApp.get_running_app()
        respuesta = app.estado.apoyo_accesibilidad_actual or {}
        apoyo = respuesta.get("apoyo_json", {})

        self.ids.etiqueta_resumen.text = apoyo.get("resumen_docente", "")
        self.ids.etiqueta_consigna.text = apoyo.get("consigna_simple", "")
        self.ids.etiqueta_rutina.text = "\n".join(apoyo.get("rutina_visual", []))
        self.ids.etiqueta_pausas.text = "\n".join(apoyo.get("pausas_sugeridas", []))
        self.ids.etiqueta_adaptaciones.text = "\n".join(
            f"- {item}" for item in apoyo.get("adaptaciones", [])
        )

    def al_presionar_continuar(self):
        app = MDApp.get_running_app()
        app.root.current = "recursos"

    def al_presionar_volver(self):
        app = MDApp.get_running_app()
        app.root.current = "adaptar"
