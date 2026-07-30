"""
Pantalla 6 - Exportar la clase. En MVP 1.0 los destinos habilitados son
PDF y PowerPoint; los checkboxes de redes sociales quedan visibles pero
deshabilitados como anticipo de MVP 2.0 (ver docs/05-mvp-2.0.md).
"""

import os
from pathlib import Path
from urllib.parse import quote

from kivy.core.clipboard import Clipboard
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from utils import cliente_api


class PantallaExportar(Screen):
    """Genera y entrega los archivos finales de la clase."""

    def al_presionar_atras(self):
        app = MDApp.get_running_app()
        app.root.current = "inicio"

    def _hay_recursos_para_paquete(self) -> bool:
        app = MDApp.get_running_app()
        recursos = app.estado.recursos_generados or {}
        return any(clave not in {"pdf", "pptx", "zip"} for clave in recursos)

    def _texto_compartir_codigo(self) -> str:
        app = MDApp.get_running_app()
        codigo = app.estado.codigo_publico or ""
        titulo = app.estado.contenido_actual.get("titulo") or "clase"
        return (
            f"Hola, les comparto la clase '{titulo}' en ProfeIA.\n"
            f"Codigo alumno: {codigo}\n\n"
            "Abrir ProfeIA, ingresar ese codigo y ver la clase."
        )

    def al_presionar_copiar_codigo(self):
        app = MDApp.get_running_app()
        codigo = app.estado.codigo_publico
        if not codigo:
            self.ids.etiqueta_estado_compartir.text = "No hay codigo alumno para copiar."
            return
        Clipboard.copy(codigo)
        self.ids.etiqueta_estado_compartir.text = "Codigo copiado."

    def al_presionar_compartir_whatsapp(self):
        app = MDApp.get_running_app()
        if not app.estado.codigo_publico:
            self.ids.etiqueta_estado_compartir.text = "No hay codigo alumno para compartir."
            return
        url = f"https://wa.me/?text={quote(self._texto_compartir_codigo())}"
        os.startfile(url)  # noqa: S606 - accion explicita del usuario en Windows
        self.ids.etiqueta_estado_compartir.text = "Abriendo WhatsApp..."

    def al_presionar_exportar_pdf(self):
        app = MDApp.get_running_app()
        estado = app.estado

        self.ids.boton_exportar_pdf.disabled = True
        self.ids.etiqueta_estado_pdf.text = "Generando PDF..."
        self.ids.boton_abrir_carpeta_pdf.opacity = 0
        self.ids.boton_abrir_carpeta_pdf.disabled = True

        cliente_api.exportar_pdf(
            clase_id=estado.clase_id,
            callback_exito=self._al_exportar_pdf_exito,
            callback_error=self._al_exportar_pdf_error,
        )

    def _al_exportar_pdf_exito(self, recurso_generado):
        app = MDApp.get_running_app()
        app.estado.recursos_generados["pdf"] = recurso_generado
        self.ids.boton_exportar_pdf.disabled = False
        ruta_pdf = Path(recurso_generado.get("url_storage", ""))
        self._ruta_pdf_generado = ruta_pdf
        self._ruta_exportacion_generada = ruta_pdf
        if self._hay_recursos_para_paquete():
            self.ids.etiqueta_estado_pdf.text = "PDF listo con recursos visuales disponibles."
        else:
            self.ids.etiqueta_estado_pdf.text = "PDF listo."
        self.ids.boton_abrir_carpeta_pdf.opacity = 1
        self.ids.boton_abrir_carpeta_pdf.disabled = False

    def _al_exportar_pdf_error(self, error):
        self.ids.boton_exportar_pdf.disabled = False
        self.ids.etiqueta_estado_pdf.text = (
            f"{cliente_api.mensaje_error(error)}. Podes volver a intentar."
        )
        print(f"[PantallaExportar] error PDF: {error}")

    def al_presionar_abrir_carpeta_pdf(self):
        """Abre la carpeta donde se genero el PDF local."""
        ruta_exportacion = getattr(self, "_ruta_exportacion_generada", None)
        if not ruta_exportacion:
            return

        carpeta = ruta_exportacion.parent
        if carpeta.exists():
            os.startfile(carpeta)  # noqa: S606 - accion explicita del usuario en Windows

    def al_presionar_exportar_pptx(self):
        app = MDApp.get_running_app()
        estado = app.estado

        self.ids.boton_exportar_pptx.disabled = True
        self.ids.etiqueta_estado_pptx.text = "Generando PowerPoint..."
        self.ids.boton_abrir_carpeta_pdf.opacity = 0
        self.ids.boton_abrir_carpeta_pdf.disabled = True

        cliente_api.exportar_pptx(
            clase_id=estado.clase_id,
            callback_exito=self._al_exportar_pptx_exito,
            callback_error=self._al_exportar_pptx_error,
        )

    def _al_exportar_pptx_exito(self, recurso_generado):
        app = MDApp.get_running_app()
        app.estado.recursos_generados["pptx"] = recurso_generado
        self.ids.boton_exportar_pptx.disabled = False
        ruta_pptx = Path(recurso_generado.get("url_storage", ""))
        self._ruta_exportacion_generada = ruta_pptx
        self.ids.etiqueta_estado_pptx.text = "PowerPoint listo."
        self.ids.boton_abrir_carpeta_pdf.opacity = 1
        self.ids.boton_abrir_carpeta_pdf.disabled = False

    def _al_exportar_pptx_error(self, error):
        self.ids.boton_exportar_pptx.disabled = False
        self.ids.etiqueta_estado_pptx.text = (
            f"{cliente_api.mensaje_error(error)}. Podes volver a intentar."
        )
        print(f"[PantallaExportar] error PPTX: {error}")

    def al_presionar_exportar_zip(self):
        app = MDApp.get_running_app()
        estado = app.estado

        self.ids.boton_exportar_zip.disabled = True
        self.ids.etiqueta_estado_zip.text = "Armando paquete ZIP..."
        self.ids.boton_abrir_carpeta_pdf.opacity = 0
        self.ids.boton_abrir_carpeta_pdf.disabled = True

        cliente_api.exportar_zip(
            clase_id=estado.clase_id,
            callback_exito=self._al_exportar_zip_exito,
            callback_error=self._al_exportar_zip_error,
        )

    def _al_exportar_zip_exito(self, recurso_generado):
        app = MDApp.get_running_app()
        app.estado.recursos_generados["zip"] = recurso_generado
        self.ids.boton_exportar_zip.disabled = False
        ruta_zip = Path(recurso_generado.get("url_storage", ""))
        self._ruta_exportacion_generada = ruta_zip
        if self._hay_recursos_para_paquete():
            self.ids.etiqueta_estado_zip.text = "Paquete ZIP listo con recursos disponibles."
        else:
            self.ids.etiqueta_estado_zip.text = "Paquete ZIP listo."
        self.ids.boton_abrir_carpeta_pdf.opacity = 1
        self.ids.boton_abrir_carpeta_pdf.disabled = False

    def _al_exportar_zip_error(self, error):
        self.ids.boton_exportar_zip.disabled = False
        self.ids.etiqueta_estado_zip.text = (
            f"{cliente_api.mensaje_error(error)}. Podes volver a intentar."
        )
        print(f"[PantallaExportar] error ZIP: {error}")

    def al_presionar_editar_clase(self):
        """Lleva al docente de vuelta a la pantalla de contenido para
        modificar el texto de la clase, incluso si ya se exporto antes.
        Al guardar, vuelve aca mismo (ver pantalla_retorno_edicion)."""
        app = MDApp.get_running_app()
        app.estado.pantalla_retorno_edicion = "exportar"

        # Si ya habia exportaciones generadas, avisamos que quedaron
        # desactualizadas en cuanto el docente vuelva a esta pantalla tras
        # editar, para que sepa que tiene que volver a exportar.
        self._habia_exportaciones_previas = bool(
            self.ids.etiqueta_estado_pdf.text
            or self.ids.etiqueta_estado_pptx.text
            or self.ids.etiqueta_estado_zip.text
        )

        app.root.current = "contenido"

    def on_pre_enter(self, *args):
        """Si se volvio de una re-edicion y ya habia exportaciones previas,
        las marca como desactualizadas en lugar de dejar el texto viejo
        como si siguiera vigente."""
        app = MDApp.get_running_app()
        seleccion = app.estado.recursos_seleccionados
        recurso_pdf = app.estado.recursos_generados.get("pdf")
        recurso_pptx = app.estado.recursos_generados.get("pptx")
        recurso_zip = app.estado.recursos_generados.get("zip")
        self.ids.etiqueta_codigo_publico.text = (
            f"Codigo alumno: {app.estado.codigo_publico}"
            if app.estado.codigo_publico
            else "Codigo alumno no disponible."
        )
        self.ids.boton_copiar_codigo.disabled = not bool(app.estado.codigo_publico)
        self.ids.boton_compartir_whatsapp.disabled = not bool(app.estado.codigo_publico)

        if not hasattr(self, "_ruta_pdf_generado"):
            self._ruta_pdf_generado = None
        if not hasattr(self, "_ruta_exportacion_generada"):
            self._ruta_exportacion_generada = None

        if recurso_pdf and recurso_pdf.get("url_storage"):
            self._ruta_pdf_generado = Path(recurso_pdf["url_storage"])
            self._ruta_exportacion_generada = self._ruta_pdf_generado
            self.ids.boton_abrir_carpeta_pdf.opacity = 1
            self.ids.boton_abrir_carpeta_pdf.disabled = False
        elif recurso_pptx and recurso_pptx.get("url_storage"):
            self._ruta_exportacion_generada = Path(recurso_pptx["url_storage"])
            self.ids.boton_abrir_carpeta_pdf.opacity = 1
            self.ids.boton_abrir_carpeta_pdf.disabled = False
        elif recurso_zip and recurso_zip.get("url_storage"):
            self._ruta_exportacion_generada = Path(recurso_zip["url_storage"])
            self.ids.boton_abrir_carpeta_pdf.opacity = 1
            self.ids.boton_abrir_carpeta_pdf.disabled = False
        else:
            self.ids.boton_abrir_carpeta_pdf.opacity = 0
            self.ids.boton_abrir_carpeta_pdf.disabled = True

        pdf_seleccionado = seleccion.get("pdf", True)
        pptx_seleccionado = seleccion.get("pptx", True)

        self.ids.boton_exportar_pdf.disabled = not pdf_seleccionado
        self.ids.boton_exportar_pptx.disabled = not pptx_seleccionado

        if not pdf_seleccionado:
            self.ids.etiqueta_estado_pdf.text = "PDF no seleccionado."
            self.ids.boton_abrir_carpeta_pdf.opacity = 0
            self.ids.boton_abrir_carpeta_pdf.disabled = True
        elif self.ids.etiqueta_estado_pdf.text == "PDF no seleccionado.":
            self.ids.etiqueta_estado_pdf.text = ""

        if not pptx_seleccionado:
            self.ids.etiqueta_estado_pptx.text = "PowerPoint no seleccionado."
        elif self.ids.etiqueta_estado_pptx.text == "PowerPoint no seleccionado.":
            self.ids.etiqueta_estado_pptx.text = ""

        if getattr(self, "_habia_exportaciones_previas", False):
            if pdf_seleccionado and self.ids.etiqueta_estado_pdf.text:
                self.ids.etiqueta_estado_pdf.text = (
                    "El contenido cambio. Volve a exportar el PDF para actualizarlo."
                )
            if pptx_seleccionado and self.ids.etiqueta_estado_pptx.text:
                self.ids.etiqueta_estado_pptx.text = (
                    "El contenido cambio. Volve a exportar el PowerPoint para actualizarlo."
                )
            if self.ids.etiqueta_estado_zip.text:
                self.ids.etiqueta_estado_zip.text = (
                    "El contenido cambio. Volve a exportar el paquete ZIP para actualizarlo."
                )
            self._habia_exportaciones_previas = False

    def al_presionar_nueva_clase(self):
        """Reinicia el flujo para crear otra clase desde cero."""
        app = MDApp.get_running_app()
        app.estado.reiniciar_flujo_clase()
        self.ids.etiqueta_estado_pdf.text = ""
        self.ids.etiqueta_estado_pptx.text = ""
        self.ids.etiqueta_estado_zip.text = ""
        self.ids.etiqueta_estado_compartir.text = ""
        self._ruta_pdf_generado = None
        self._ruta_exportacion_generada = None
        self.ids.boton_abrir_carpeta_pdf.opacity = 0
        self.ids.boton_abrir_carpeta_pdf.disabled = True
        app.root.current = "inicio"
