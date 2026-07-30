"""
Pantalla de plan y cuotas del docente.
"""

import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from utils import cliente_api


ETIQUETAS_CUOTAS = {
    "clases": "Clases",
    "imagenes": "Imagenes",
    "voces": "Voces",
    "videos": "Videos",
    "minutos_grabacion": "Min. grabacion",
    "clonaciones_voz": "Clonaciones voz",
    "exportaciones_pdf": "PDF",
    "exportaciones_pptx": "PowerPoint",
    "apoyos_accesibilidad": "Apoyos educativos",
}


class PantallaPlan(Screen):
    """Muestra plan actual, uso y planes disponibles."""

    def on_pre_enter(self, *args):
        app = MDApp.get_running_app()
        self.ids.etiqueta_perfil_nombre.text = f"Nombre: {app.estado.docente_nombre or '-'}"
        self.ids.etiqueta_perfil_email.text = f"Email: {app.estado.docente_email or '-'}"
        self.ids.etiqueta_perfil_materia.text = (
            f"Materia principal: {app.estado.docente_materia_principal or 'No especificada'}"
        )
        self.ids.etiqueta_perfil_miembro_desde.text = (
            f"Miembro desde: {self._formatear_fecha(app.estado.docente_creado_en)}"
        )
        self.ids.etiqueta_estado.text = "Cargando plan..."
        self.ids.etiqueta_uso.text = ""
        self.ids.etiqueta_planes.text = ""
        self.ids.indicador_carga.active = True
        self._planes = []
        self._uso = None
        self._plan_checkout_pendiente = None
        cliente_api.listar_planes(
            callback_exito=self._al_cargar_planes,
            callback_error=self._al_error,
        )

    def _formatear_fecha(self, fecha_iso: str | None) -> str:
        if not fecha_iso:
            return "-"
        try:
            from datetime import datetime

            fecha = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
            return fecha.strftime("%d/%m/%Y")
        except ValueError:
            return fecha_iso

    def _al_cargar_planes(self, planes):
        self._planes = planes
        app = MDApp.get_running_app()
        if not app.estado.docente_id:
            self._al_error("Docente no autenticado")
            return
        cliente_api.obtener_uso_plan(
            docente_id=app.estado.docente_id,
            plan_id=None,
            callback_exito=self._al_cargar_uso,
            callback_error=self._al_error,
        )

    def _al_cargar_uso(self, uso):
        self._uso = uso
        self.ids.indicador_carga.active = False
        self._renderizar()

    def _renderizar(self):
        app = MDApp.get_running_app()
        plan_actual_id = (self._uso or {}).get("plan_id") or app.estado.docente_plan or "gratis"
        app.estado.docente_plan = plan_actual_id
        plan_actual = next(
            (plan for plan in self._planes if plan.get("id") == plan_actual_id),
            None,
        )

        if plan_actual:
            precio = plan_actual.get("precio_referencia_usd")
            precio_texto = "gratis" if precio == 0 else (f"USD {precio}/mes" if precio else "a medida")
            self.ids.etiqueta_estado.text = (
                f"Plan actual: {plan_actual.get('nombre')} ({precio_texto})"
            )
        else:
            self.ids.etiqueta_estado.text = f"Plan actual: {plan_actual_id}"

        usado = self._uso.get("usado", {}) if self._uso else {}
        limites = self._uso.get("limites", {}) if self._uso else {}
        restante = self._uso.get("restante", {}) if self._uso else {}
        lineas_uso = []
        for clave, etiqueta in ETIQUETAS_CUOTAS.items():
            lineas_uso.append(
                f"{etiqueta}: {usado.get(clave, 0)} / {limites.get(clave, 0)} "
                f"(restan {restante.get(clave, 0)})"
            )
        self.ids.etiqueta_uso.text = "\n".join(lineas_uso)

        lineas_planes = []
        for plan in self._planes:
            precio = plan.get("precio_referencia_usd")
            precio_texto = "gratis" if precio == 0 else (f"USD {precio}/mes" if precio else "a medida")
            marca = "Actual - " if plan.get("id") == plan_actual_id else ""
            cuotas = plan.get("cuotas", {})
            lineas_planes.append(
                f"{marca}{plan.get('nombre')} ({precio_texto})\n"
                f"{plan.get('descripcion')}\n"
                f"Clases: {cuotas.get('clases')} | Imagenes: {cuotas.get('imagenes')} | "
                f"Voces: {cuotas.get('voces')} | Videos: {cuotas.get('videos')}"
            )
        self.ids.etiqueta_planes.text = "\n\n".join(lineas_planes)

    def _al_error(self, error):
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_estado.text = "No se pudo cargar el plan."
        print(f"[PantallaPlan] error: {error}")

    def al_presionar_suscribirse(self, plan_id: str):
        app = MDApp.get_running_app()
        if not app.estado.docente_id or not app.estado.docente_email:
            self.ids.etiqueta_estado_pago.text = "Inicia sesion como docente."
            return
        self._plan_checkout_pendiente = plan_id
        self.ids.etiqueta_estado_pago.text = "Creando checkout..."
        self.ids.boton_plan_docente.disabled = True
        self.ids.boton_plan_pro.disabled = True
        cliente_api.crear_checkout_suscripcion(
            datos_suscripcion={
                "docente_id": app.estado.docente_id,
                "plan_id": plan_id,
                "email": app.estado.docente_email,
            },
            callback_exito=self._al_checkout_exito,
            callback_error=self._al_checkout_error,
        )

    def _al_checkout_exito(self, respuesta):
        self.ids.boton_plan_docente.disabled = False
        self.ids.boton_plan_pro.disabled = False
        checkout_url = respuesta.get("checkout_url")
        modo = respuesta.get("modo", "")
        if modo == "demo":
            self.ids.etiqueta_estado_pago.text = "Activando plan demo..."
            self._activar_plan_demo()
            return
        if checkout_url:
            os.startfile(checkout_url)  # noqa: S606 - accion explicita del usuario en Windows
            self.ids.etiqueta_estado_pago.text = (
                "Abriendo Mercado Pago..." if modo != "demo" else "Abriendo checkout demo..."
            )
        else:
            self.ids.etiqueta_estado_pago.text = "Plan actualizado."

    def _al_checkout_error(self, error):
        self.ids.boton_plan_docente.disabled = False
        self.ids.boton_plan_pro.disabled = False
        self.ids.etiqueta_estado_pago.text = cliente_api.mensaje_error(error)
        print(f"[PantallaPlan] error checkout: {error}")

    def _activar_plan_demo(self):
        app = MDApp.get_running_app()
        cliente_api.activar_suscripcion_demo(
            datos_suscripcion={
                "docente_id": app.estado.docente_id,
                "plan_id": self._plan_checkout_pendiente,
                "email": app.estado.docente_email,
            },
            callback_exito=self._al_activar_demo_exito,
            callback_error=self._al_activar_demo_error,
        )

    def _al_activar_demo_exito(self, respuesta):
        app = MDApp.get_running_app()
        app.estado.docente_plan = respuesta.get("plan_id") or app.estado.docente_plan
        self.ids.etiqueta_estado_pago.text = "Plan demo activado."
        self.on_pre_enter()

    def _al_activar_demo_error(self, error):
        self.ids.etiqueta_estado_pago.text = cliente_api.mensaje_error(error)
        print(f"[PantallaPlan] error demo: {error}")

    def al_presionar_borrar_cuenta(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=12)
        popup = Popup(
            title="Eliminar cuenta",
            content=layout,
            size_hint=(0.92, 0.46),
        )

        mensaje = MDLabel(
            text=(
                "Esta accion borra tu cuenta docente y las clases asociadas. "
                "Ingresa tu clave para confirmar."
            ),
            size_hint_y=None,
            height=82,
            text_size=(340, None),
            theme_text_color="Secondary",
        )
        campo_password = MDTextField(
            hint_text="Clave docente",
            password=True,
            mode="rectangle",
            size_hint_y=None,
            height=56,
        )
        etiqueta_error = MDLabel(
            text="",
            size_hint_y=None,
            height=34,
            halign="center",
            theme_text_color="Error",
        )
        acciones = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=48)

        def confirmar(*args):
            password = campo_password.text.strip()
            if not password:
                etiqueta_error.text = "Ingresa tu clave."
                return
            self._popup_borrar_cuenta = popup
            self._etiqueta_borrar_cuenta = etiqueta_error
            self._eliminar_cuenta(password)

        acciones.add_widget(MDFlatButton(text="CANCELAR", on_release=lambda *args: popup.dismiss()))
        acciones.add_widget(MDRectangleFlatButton(text="ELIMINAR", on_release=confirmar))

        layout.add_widget(mensaje)
        layout.add_widget(campo_password)
        layout.add_widget(etiqueta_error)
        layout.add_widget(acciones)
        popup.open()

    def _eliminar_cuenta(self, password: str):
        app = MDApp.get_running_app()
        if not app.estado.docente_id:
            self.ids.etiqueta_estado_pago.text = "No hay docente autenticado."
            return
        cliente_api.eliminar_cuenta_docente(
            datos_eliminacion={
                "docente_id": app.estado.docente_id,
                "password": password,
            },
            callback_exito=self._al_eliminar_cuenta_exito,
            callback_error=self._al_eliminar_cuenta_error,
        )

    def _al_eliminar_cuenta_exito(self, respuesta):
        _ = respuesta
        popup = getattr(self, "_popup_borrar_cuenta", None)
        if popup:
            popup.dismiss()
        app = MDApp.get_running_app()
        app.estado.cerrar_sesion()
        app.root.current = "entrada"

    def _al_eliminar_cuenta_error(self, error):
        etiqueta = getattr(self, "_etiqueta_borrar_cuenta", None)
        mensaje = cliente_api.mensaje_error(error)
        if etiqueta:
            etiqueta.text = mensaje
        else:
            self.ids.etiqueta_estado_pago.text = mensaje
        print(f"[PantallaPlan] error eliminar cuenta: {error}")

    def al_presionar_cerrar_sesion(self):
        """Pide confirmacion antes de cerrar sesion, para que un toque
        accidental no saque al docente de la app sin querer (mas importante
        cuanto menos comoda es la navegacion tactil para el usuario)."""
        layout = BoxLayout(orientation="vertical", spacing=12, padding=(16, 8))
        popup = Popup(
            title="Cerrar sesion",
            content=layout,
            size_hint=(0.85, 0.32),
        )

        mensaje = MDLabel(
            text="Seguro que queres cerrar tu sesion?",
            size_hint_y=None,
            height=48,
            text_size=(300, None),
            theme_text_color="Secondary",
        )
        acciones = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=48)

        def confirmar(*args):
            popup.dismiss()
            app = MDApp.get_running_app()
            app.estado.cerrar_sesion()
            app.root.current = "entrada"

        acciones.add_widget(MDFlatButton(text="CANCELAR", on_release=lambda *args: popup.dismiss()))
        acciones.add_widget(MDRectangleFlatButton(text="CERRAR SESION", on_release=confirmar))

        layout.add_widget(mensaje)
        layout.add_widget(acciones)
        popup.open()

    def al_presionar_volver(self):
        MDApp.get_running_app().root.current = "inicio"
