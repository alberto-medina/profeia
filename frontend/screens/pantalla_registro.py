"""
Pantalla de registro docente, separada del login.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from utils import cliente_api


class PantallaRegistro(Screen):
    """Alta de una cuenta docente nueva."""

    def on_pre_enter(self, *args):
        if "etiqueta_error" in self.ids:
            self.ids.etiqueta_error.text = ""

    def al_presionar_volver(self):
        MDApp.get_running_app().root.current = "login"

    def al_presionar_crear_cuenta(self):
        nombre = self.ids.campo_nombre.text.strip()
        email = self.ids.campo_email.text.strip().lower()
        password = self.ids.campo_password.text.strip()
        if len(nombre) < 2:
            self.ids.etiqueta_error.text = "Ingresa tu nombre."
            return
        if not email or len(password) < 6:
            self.ids.etiqueta_error.text = "Usa email y clave de al menos 6 caracteres."
            return

        self._bloquear(True, "Creando cuenta...")
        cliente_api.registrar_docente(
            datos_docente={
                "nombre": nombre,
                "email": email,
                "password": password,
                "materia_principal": None,
            },
            callback_exito=self._al_autenticado,
            callback_error=self._al_error,
        )

    def _bloquear(self, bloqueado: bool, mensaje: str = ""):
        self.ids.boton_crear_cuenta.disabled = bloqueado
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
        app.estado.guardar_sesion()
        self._bloquear(False)
        self.ids.campo_password.text = ""
        app.root.current = "inicio"

    def _al_error(self, error):
        self._bloquear(False)
        self.ids.etiqueta_error.text = "No se pudo crear la cuenta. Revisa los datos."
        print(f"[PantallaRegistro] error registro docente: {error}")
