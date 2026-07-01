"""
Pantalla 3 - Elegir que recursos generar (voz, slides, imagenes, video, PDF, PPT).
"""

from pathlib import Path

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton

from utils import cliente_api


class PantallaRecursos(Screen):
    """Checkboxes para elegir que recursos generar a partir del contenido."""

    def on_pre_enter(self, *args):
        self.ids.etiqueta_estado.text = ""
        self.ids.indicador_carga.active = False
        self.ids.boton_continuar.disabled = False

    def al_presionar_buscar_imagen(self):
        self._abrir_selector_archivo(
            tipo="imagen",
            titulo="Elegir imagen",
            filtros=["*.png", "*.jpg", "*.jpeg", "*.webp"],
        )

    def al_presionar_buscar_audio(self):
        self._abrir_selector_archivo(
            tipo="audio_docente",
            titulo="Elegir audio",
            filtros=["*.mp3", "*.wav", "*.m4a", "*.ogg"],
        )

    def _abrir_selector_archivo(self, tipo: str, titulo: str, filtros: list[str]):
        layout = BoxLayout(orientation="vertical", spacing=8)
        selector = FileChooserListView(filters=filtros)
        acciones = BoxLayout(size_hint_y=None, height=48, spacing=8)
        popup = Popup(title=titulo, content=layout, size_hint=(0.92, 0.88))

        def seleccionar_archivo(*args):
            if not selector.selection:
                return
            ruta = selector.selection[0]
            if tipo == "imagen":
                self.ids.campo_imagen_docente.text = ruta
            else:
                self.ids.campo_audio_docente.text = ruta
            popup.dismiss()

        acciones.add_widget(MDFlatButton(text="CANCELAR", on_release=lambda *args: popup.dismiss()))
        acciones.add_widget(MDRectangleFlatButton(text="USAR ARCHIVO", on_release=seleccionar_archivo))
        layout.add_widget(selector)
        layout.add_widget(acciones)
        popup.open()

    def al_presionar_adjuntar_imagen(self):
        self._adjuntar_recurso_desde_campo("imagen", "campo_imagen_docente")

    def al_presionar_adjuntar_audio(self):
        self._adjuntar_recurso_desde_campo("audio_docente", "campo_audio_docente")

    def al_presionar_buscar_imagenes_web(self):
        app = MDApp.get_running_app()
        if not app.estado.clase_id:
            self.ids.etiqueta_estado.text = "Primero crea una clase."
            return

        self.ids.boton_continuar.disabled = True
        self.ids.indicador_carga.active = True
        self.ids.etiqueta_estado.text = "Buscando imagenes gratis..."
        cliente_api.buscar_imagenes_web(
            clase_id=app.estado.clase_id,
            cantidad=3,
            callback_exito=self._al_buscar_imagenes_web_exito,
            callback_error=self._al_generar_recurso_error,
        )

    def _al_buscar_imagenes_web_exito(self, recursos_generados):
        app = MDApp.get_running_app()
        app.estado.recursos_generados["imagenes"] = recursos_generados
        origenes = {
            (recurso.get("metadata_json") or {}).get("origen")
            for recurso in recursos_generados
        }
        if "wikimedia_commons" in origenes:
            self.ids.etiqueta_estado.text = (
                f"Imagenes gratis agregadas: {len(recursos_generados)}. "
                "Se reemplazaron busquedas gratis anteriores."
            )
        elif "local" in origenes:
            self.ids.etiqueta_estado.text = (
                "No encontre imagenes web confiables; agregue laminas locales "
                "sin costo para esta clase."
            )
        else:
            self.ids.etiqueta_estado.text = f"Imagenes agregadas: {len(recursos_generados)}"
        self.ids.boton_continuar.disabled = False
        self.ids.indicador_carga.active = False

    def _adjuntar_recurso_desde_campo(self, tipo: str, id_campo: str):
        app = MDApp.get_running_app()
        ruta = Path(self.ids[id_campo].text.strip().strip('"'))
        if not app.estado.clase_id:
            self.ids.etiqueta_estado.text = "Primero crea una clase."
            return
        if not ruta.exists() or not ruta.is_file():
            self.ids.etiqueta_estado.text = "Selecciona un archivo valido."
            return

        self.ids.boton_continuar.disabled = True
        self.ids.indicador_carga.active = True
        self.ids.etiqueta_estado.text = "Subiendo recurso..."
        cliente_api.subir_recurso(
            clase_id=app.estado.clase_id,
            tipo=tipo,
            ruta_archivo=str(ruta),
            callback_exito=self._al_adjuntar_recurso_exito,
            callback_error=self._al_generar_recurso_error,
        )

    def _al_adjuntar_recurso_exito(self, recurso_generado):
        app = MDApp.get_running_app()
        tipo = recurso_generado.get("tipo")
        if tipo == "imagen":
            app.estado.recursos_generados["imagenes"].append(recurso_generado)
        elif tipo == "audio_docente":
            app.estado.recursos_generados["audios_docente"].append(recurso_generado)

        metadata = recurso_generado.get("metadata_json") or {}
        nombre = metadata.get("nombre") or Path(recurso_generado.get("url_storage", "")).name
        self.ids.etiqueta_estado.text = f"Recurso adjuntado: {nombre}"
        self.ids.boton_continuar.disabled = False
        self.ids.indicador_carga.active = False

    def al_presionar_continuar(self):
        """Guarda la seleccion de recursos y genera los recursos previos."""
        app = MDApp.get_running_app()
        estado = app.estado

        estado.recursos_seleccionados = {
            "voz": self.ids.check_voz.active,
            "slides": self.ids.check_slides.active,
            "imagenes": self.ids.check_imagenes.active,
            "video": self.ids.check_video.active,
            "pdf": self.ids.check_pdf.active,
            "pptx": self.ids.check_pptx.active,
        }

        tareas = []
        if estado.recursos_seleccionados["slides"]:
            tareas.append(("slides", self._generar_slides))
        if estado.recursos_seleccionados["imagenes"]:
            tareas.append(("imagenes", self._generar_imagenes))

        self._tareas_pendientes = tareas
        if not self._tareas_pendientes:
            self._avanzar_al_siguiente_paso()
            return

        self.ids.boton_continuar.disabled = True
        self.ids.indicador_carga.active = True
        self._procesar_siguiente_tarea()

    def _procesar_siguiente_tarea(self):
        if not self._tareas_pendientes:
            self.ids.boton_continuar.disabled = False
            self.ids.indicador_carga.active = False
            self._avanzar_al_siguiente_paso()
            return

        nombre_tarea, funcion_tarea = self._tareas_pendientes.pop(0)
        self.ids.etiqueta_estado.text = f"Generando {nombre_tarea}..."
        funcion_tarea()

    def _generar_slides(self):
        app = MDApp.get_running_app()
        cliente_api.generar_slides(
            clase_id=app.estado.clase_id,
            callback_exito=self._al_generar_slides_exito,
            callback_error=self._al_generar_recurso_error,
        )

    def _generar_imagenes(self):
        app = MDApp.get_running_app()
        cliente_api.generar_imagenes(
            clase_id=app.estado.clase_id,
            parametros_imagenes={"cantidad": 3, "estilo": "claro y educativo"},
            callback_exito=self._al_generar_imagenes_exito,
            callback_error=self._al_generar_recurso_error,
        )

    def _al_generar_slides_exito(self, recurso_generado):
        app = MDApp.get_running_app()
        app.estado.recursos_generados["slides"] = recurso_generado
        self._procesar_siguiente_tarea()

    def _al_generar_imagenes_exito(self, recursos_generados):
        app = MDApp.get_running_app()
        app.estado.recursos_generados["imagenes"] = recursos_generados
        self._procesar_siguiente_tarea()

    def _al_generar_recurso_error(self, error):
        self.ids.boton_continuar.disabled = False
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_estado.text = (
            cliente_api.mensaje_error(error)
            + " Si el problema es de imagenes gratis, podes continuar sin ellas o adjuntar una imagen propia."
        )
        print(f"[PantallaRecursos] error al generar recurso: {error}")

    def _avanzar_al_siguiente_paso(self):
        app = MDApp.get_running_app()
        estado = app.estado

        if estado.recursos_seleccionados["voz"]:
            app.root.current = "voz"
        elif estado.recursos_seleccionados["video"]:
            app.root.current = "video"
        else:
            app.root.current = "exportar"
