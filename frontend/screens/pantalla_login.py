"""
Pantalla de login docente, separada del registro.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from utils import cliente_api


class PantallaLogin(Screen):
    """Login del docente con email y clave."""

    def on_pre_enter(self, *args):
        if "etiqueta_error" in self.ids:
            self.ids.etiqueta_error.text = ""

    def al_presionar_volver(self):
        MDApp.get_running_app().root.current = "entrada"

    def al_presionar_ir_a_registro(self):
        MDApp.get_running_app().root.current = "registro"

    def al_presionar_ingresar(self):
        email = self.ids.campo_email.text.strip().lower()
        password = self.ids.campo_password.text.strip()
        if not email or not password:
            self.ids.etiqueta_error.text = "Ingresa email y clave."
            return

        self._bloquear(True, "Ingresando...")
        cliente_api.iniciar_sesion_docente(
            credenciales={"email": email, "password": password},
            callback_exito=self._al_autenticado,
            callback_error=self._al_error,
        )

    def _bloquear(self, bloqueado: bool, mensaje: str = ""):
        self.ids.boton_ingresar.disabled = bloqueado
        self.ids.etiqueta_error.text = mensaje

    def _al_autenticado(self, docente):
        app = MDApp.get_running_app()
        app.estado.docente_id = str(docente.get("id", ""))
        app.estado.docente_nombre = docente.get("nombre")
        app.estado.docente_email = docente.get("email")
        app.estado.docente_plan = docente.get("plan") or "gratis"
        app.estado.docente_materia_principal = docente.get("materia_principal")
        app.estado.docente_creado_en = docente.get("creado_en")
        app.estado.modo_actual = "docente"
        self._bloquear(False)
        self.ids.campo_password.text = ""
        app.root.current = "inicio"

    def _al_error(self, error):
        self._bloquear(False)
        self.ids.etiqueta_error.text = "No se pudo ingresar. Revisa email y clave."
        print(f"[PantallaLogin] error auth docente: {error}")
