"""
Pantalla de entrada: separa el camino del alumno y del docente.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from utils import cliente_api


class PantallaEntrada(Screen):
    """Primera pantalla de la app, antes del flujo docente."""

    def on_pre_enter(self, *args):
        if "etiqueta_error" in self.ids:
            self.ids.etiqueta_error.text = ""
        if "campo_password_docente" in self.ids:
            self.ids.campo_password_docente.text = ""

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

    def al_presionar_entrar_docente(self):
        email = self.ids.campo_email_docente.text.strip().lower()
        password = self.ids.campo_password_docente.text.strip()
        if not email or not password:
            self.ids.etiqueta_error.text = "Ingresa email y clave docente."
            return

        self._bloquear_docente(True, "Ingresando...")
        cliente_api.iniciar_sesion_docente(
            credenciales={"email": email, "password": password},
            callback_exito=self._al_docente_autenticado,
            callback_error=self._al_auth_error,
        )

    def al_presionar_crear_cuenta_docente(self):
        nombre = self.ids.campo_nombre_docente.text.strip()
        email = self.ids.campo_email_docente.text.strip().lower()
        password = self.ids.campo_password_docente.text.strip()
        if len(nombre) < 2:
            self.ids.etiqueta_error.text = "Ingresa tu nombre docente."
            return
        if not email or len(password) < 6:
            self.ids.etiqueta_error.text = "Usa email y clave de al menos 6 caracteres."
            return

        self._bloquear_docente(True, "Creando cuenta...")
        cliente_api.registrar_docente(
            datos_docente={
                "nombre": nombre,
                "email": email,
                "password": password,
                "materia_principal": None,
            },
            callback_exito=self._al_docente_autenticado,
            callback_error=self._al_auth_error,
        )

    def _bloquear_docente(self, bloqueado: bool, mensaje: str = ""):
        self.ids.boton_login_docente.disabled = bloqueado
        self.ids.boton_registro_docente.disabled = bloqueado
        self.ids.etiqueta_error.text = mensaje

    def _al_docente_autenticado(self, docente):
        app = MDApp.get_running_app()
        app.estado.docente_id = str(docente.get("id", ""))
        app.estado.docente_nombre = docente.get("nombre")
        app.estado.docente_email = docente.get("email")
        app.estado.docente_plan = docente.get("plan") or "gratis"
        app.estado.modo_actual = "docente"
        self._bloquear_docente(False)
        app.root.current = "inicio"

    def _al_auth_error(self, error):
        self._bloquear_docente(False)
        self.ids.etiqueta_error.text = "No se pudo ingresar. Revisa email y clave."
        print(f"[PantallaEntrada] error auth docente: {error}")
