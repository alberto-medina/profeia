"""
Pantalla de bienvenida: primer contacto con la app.

Separa el camino del alumno (ingresa un codigo de clase) del camino del
docente (va a las pantallas de login / registro, cada una independiente).
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp


class PantallaEntrada(Screen):
    """Primera pantalla de la app: elegir alumno o docente."""

    def on_pre_enter(self, *args):
        if "etiqueta_error" in self.ids:
            self.ids.etiqueta_error.text = ""
        if "campo_codigo" in self.ids:
            self.ids.campo_codigo.text = ""

    def al_presionar_entrar_alumno(self):
        app = MDApp.get_running_app()
        codigo = self.ids.campo_codigo.text.strip().upper()
        if not codigo:
            self.ids.etiqueta_error.text = "Ingresa el codigo de la clase."
            return

        app.estado.clase_id = None
        app.estado.codigo_publico = codigo
        app.estado.modo_actual = "alumno"
        app.root.current = "alumno"

    def al_presionar_soy_docente(self):
        app = MDApp.get_running_app()
        app.root.current = "login"
