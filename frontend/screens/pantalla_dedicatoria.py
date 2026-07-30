"""
Pantalla de dedicatoria: se muestra al abrir la app, antes de la pantalla
de entrada. Se queda el tiempo suficiente para leerla tranquilo, pero se
puede tocar en cualquier momento para continuar antes.
"""

from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

SEGUNDOS_AUTOAVANCE = 11


class PantallaDedicatoria(Screen):
    """Primera pantalla de la app: una dedicatoria antes de entrar."""

    _evento_autoavance = None

    def on_enter(self, *args):
        self._evento_autoavance = Clock.schedule_once(self._avanzar, SEGUNDOS_AUTOAVANCE)

    def on_leave(self, *args):
        if self._evento_autoavance:
            self._evento_autoavance.cancel()
            self._evento_autoavance = None

    def al_tocar_pantalla(self, *args):
        self._avanzar()

    def _avanzar(self, *args):
        app = MDApp.get_running_app()
        if app.root.current != self.name:
            return
        app.root.current = "inicio" if app.estado.docente_id else "entrada"
