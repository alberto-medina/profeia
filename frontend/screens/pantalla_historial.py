"""
Pantalla de historial de clases guardadas del docente.
"""

from datetime import datetime
from functools import partial

from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from utils import cliente_api


class PantallaHistorial(Screen):
    """Lista clases creadas y permite reabrirlas."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._clases: list[dict] = []

    def on_pre_enter(self, *args):
        self.ids.contenedor_clases.clear_widgets()
        self.ids.etiqueta_estado.text = "Cargando clases..."
        self.ids.indicador_carga.active = True

        app = MDApp.get_running_app()
        cliente_api.listar_clases(
            docente_id=app.estado.docente_id or "00000000-0000-0000-0000-000000000000",
            callback_exito=self._al_cargar_exito,
            callback_error=self._al_cargar_error,
        )

    def _al_cargar_exito(self, clases):
        self.ids.indicador_carga.active = False
        self._clases = clases or []
        self._renderizar_clases(self._clases)

    def _renderizar_clases(self, clases: list[dict]):
        self.ids.contenedor_clases.clear_widgets()

        if not clases:
            if self._clases and self.ids.campo_busqueda.text.strip():
                self.ids.etiqueta_estado.text = "No hay clases que coincidan con la busqueda."
                return
            self.ids.etiqueta_estado.text = "Todavia no hay clases guardadas."
            return

        self.ids.etiqueta_estado.text = f"{len(clases)} clase(s) guardada(s)."
        for clase in clases:
            self.ids.contenedor_clases.add_widget(self._crear_tarjeta_clase(clase))

    def _al_cargar_error(self, error):
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_estado.text = "No se pudo cargar el historial."
        print(f"[PantallaHistorial] error al cargar historial: {error}")

    def al_cambiar_busqueda(self, texto: str):
        termino = texto.strip().lower()
        if not termino:
            self._renderizar_clases(self._clases)
            return

        clases_filtradas = [
            clase
            for clase in self._clases
            if self._coincide_busqueda(clase, termino)
        ]
        self._renderizar_clases(clases_filtradas)

    def _coincide_busqueda(self, clase: dict, termino: str) -> bool:
        contenido = clase.get("contenido_json") or {}
        campos = [
            clase.get("titulo"),
            clase.get("materia"),
            clase.get("edad_publico"),
            clase.get("codigo_publico"),
            clase.get("prompt_original"),
            contenido.get("titulo"),
            contenido.get("objetivo"),
        ]
        return termino in " ".join(str(campo or "").lower() for campo in campos)

    def al_presionar_limpiar_busqueda(self):
        self.ids.campo_busqueda.text = ""
        self._renderizar_clases(self._clases)

    def _crear_tarjeta_clase(self, clase: dict) -> MDCard:
        app = MDApp.get_running_app()
        titulo = clase.get("titulo") or clase.get("materia") or "Clase sin titulo"
        materia = clase.get("materia") or "General"
        duracion = clase.get("duracion_minutos", "")
        codigo = clase.get("codigo_publico") or "sin codigo"
        creado_en = self._formatear_fecha(clase.get("creado_en"))

        tarjeta = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(178),
            radius=[dp(8)],
            elevation=1,
            md_bg_color=app.color_superficie,
        )

        etiqueta_titulo = MDLabel(
            text=titulo,
            bold=True,
            size_hint_y=None,
            height=dp(42),
            theme_text_color="Custom",
            text_color=app.color_texto,
        )
        etiqueta_titulo.bind(
            width=lambda instancia, ancho: setattr(instancia, "text_size", (ancho, None))
        )
        tarjeta.add_widget(etiqueta_titulo)
        tarjeta.add_widget(
            MDLabel(
                text=f"{materia} | {duracion} min | {creado_en}",
                size_hint_y=None,
                height=dp(24),
                theme_text_color="Custom",
                text_color=app.color_texto_secundario,
            )
        )

        fila_codigo = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(32))
        fila_codigo.add_widget(
            MDLabel(
                text=f"Codigo alumno: {codigo}",
                size_hint_x=1,
                theme_text_color="Custom",
                text_color=app.color_texto_secundario,
            )
        )
        fila_codigo.add_widget(
            MDFlatButton(
                text="COPIAR",
                disabled=not bool(clase.get("codigo_publico")),
                on_release=partial(self._copiar_codigo, clase),
            )
        )
        tarjeta.add_widget(fila_codigo)

        fila_acciones = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))
        fila_acciones.add_widget(
            MDRectangleFlatButton(
                text="EXPORTAR",
                on_release=partial(self._abrir_exportar, clase),
            )
        )
        fila_acciones.add_widget(
            MDFlatButton(
                text="EDITAR",
                on_release=partial(self._abrir_edicion, clase),
            )
        )
        fila_acciones.add_widget(
            MDFlatButton(
                text="ALUMNO",
                on_release=partial(self._abrir_alumno, clase),
            )
        )
        tarjeta.add_widget(fila_acciones)
        return tarjeta

    def _formatear_fecha(self, valor: str | None) -> str:
        if not valor:
            return "sin fecha"
        try:
            fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
            return fecha.strftime("%d/%m/%Y")
        except ValueError:
            return valor[:10]

    def _cargar_clase_en_estado(self, clase: dict):
        app = MDApp.get_running_app()
        estado = app.estado
        estado.clase_id = str(clase.get("id", ""))
        estado.codigo_publico = clase.get("codigo_publico")
        estado.contenido_actual = clase.get("contenido_json", {}) or {}
        estado.apoyo_accesibilidad_actual = None
        estado.paquete_alumno_actual = None
        estado.recursos_generados = {
            "voz": None,
            "slides": None,
            "imagenes": [],
            "audios_docente": [],
            "pdf": None,
            "pptx": None,
            "zip": None,
        }
        estado.pantalla_retorno_edicion = "exportar"

    def _abrir_edicion(self, clase, *args):
        app = MDApp.get_running_app()
        self._cargar_clase_en_estado(clase)
        app.root.current = "contenido"

    def _abrir_exportar(self, clase, *args):
        app = MDApp.get_running_app()
        self._cargar_clase_en_estado(clase)
        app.root.current = "exportar"

    def _abrir_alumno(self, clase, *args):
        app = MDApp.get_running_app()
        self._cargar_clase_en_estado(clase)
        app.root.current = "alumno"

    def _copiar_codigo(self, clase, *args):
        codigo = clase.get("codigo_publico")
        if not codigo:
            self.ids.etiqueta_estado.text = "Esta clase todavia no tiene codigo alumno."
            return
        Clipboard.copy(codigo)
        self.ids.etiqueta_estado.text = f"Codigo {codigo} copiado."

    def al_presionar_volver(self):
        app = MDApp.get_running_app()
        app.root.current = "inicio"
