"""
Pantalla 5 - Vista de la estructura automatica del video (intro, desarrollo,
ejemplos, actividad, cierre). En MVP 1.0 esta pantalla es informativa; el
ensamblado real de video se implementa en MVP 2.0 (ver docs/05-mvp-2.0.md).
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp


class PantallaVideo(Screen):
    """Muestra la estructura de escenas planificada para el video de la clase."""

    def on_pre_enter(self, *args):
        app = MDApp.get_running_app()
        contenido = app.estado.contenido_actual

        self.ids.etiqueta_intro.text = f"Intro: {contenido.get('titulo', '')}"
        self.ids.etiqueta_desarrollo.text = (
            f"Desarrollo: {contenido.get('explicacion', '')[:80]}..."
        )
        ejemplos = contenido.get("ejemplos", [])
        self.ids.etiqueta_ejemplos.text = (
            f"Ejemplos: {len(ejemplos)} ejemplo(s) cotidiano(s)"
        )
        self.ids.etiqueta_actividad.text = f"Actividad: {contenido.get('actividad', '')[:80]}..."
        self.ids.etiqueta_cierre.text = f"Cierre: {contenido.get('resumen', '')[:80]}..."

    def al_presionar_continuar(self):
        app = MDApp.get_running_app()
        app.root.current = "exportar"
