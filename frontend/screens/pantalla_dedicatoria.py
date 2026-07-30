"""
Pantalla de dedicatoria: se muestra al abrir la app, antes de la pantalla
de entrada. Se queda ahi hasta que se toque la pantalla, para que cada
quien la lea con la calma que quiera sin sentir apuro.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp


class PantallaDedicatoria(Screen):
    """Primera pantalla de la app: una dedicatoria antes de entrar."""

    def al_tocar_pantalla(self, *args):
        app = MDApp.get_running_app()
        if app.root.current != self.name:
            return
        app.root.current = "inicio" if app.estado.docente_id else "entrada"
