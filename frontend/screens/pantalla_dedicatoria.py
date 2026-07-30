"""
Pantalla de dedicatoria: se muestra al abrir la app, antes de la pantalla
de entrada. Se queda ahi hasta que se toque dos veces la pantalla, para
que cada quien la lea con la calma que quiera sin sentir apuro, y para
que un toque accidental (por ejemplo, para que no se apague la pantalla)
no la salte de casualidad.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp


class PantallaDedicatoria(Screen):
    """Primera pantalla de la app: una dedicatoria antes de entrar."""

    def al_tocar_pantalla(self, touch):
        if not touch.is_double_tap:
            return
        app = MDApp.get_running_app()
        if app.root.current != self.name:
            return
        app.root.current = "inicio" if app.estado.docente_id else "entrada"
