"""
Pantalla 2 - Contenido generado por la IA, editable por el docente.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from utils import cliente_api


class PantallaContenido(Screen):
    """Muestra y permite editar el contenido pedagogico generado."""

    def on_pre_enter(self, *args):
        """Carga el contenido actual del estado global cada vez que se entra
        a esta pantalla, ya sea por primera vez (recien generada) o porque
        el docente volvio a editar una clase ya exportada."""
        app = MDApp.get_running_app()
        self.cargar_contenido(app.estado.contenido_actual)

        es_reedicion = app.estado.pantalla_retorno_edicion == "exportar"
        self.ids.boton_cancelar.opacity = 1 if es_reedicion else 0
        self.ids.boton_cancelar.disabled = not es_reedicion

    def cargar_contenido(self, contenido: dict):
        """Llena los campos de la pantalla con el contenido recibido del backend."""
        self.ids.campo_titulo.text = contenido.get("titulo", "")
        self.ids.campo_objetivo.text = contenido.get("objetivo", "")
        self.ids.campo_introduccion.text = contenido.get("introduccion", "")
        self.ids.campo_explicacion.text = contenido.get("explicacion", "")
        self.ids.campo_ejemplos.text = "\n".join(contenido.get("ejemplos", []))
        self.ids.campo_actividad.text = contenido.get("actividad", "")
        self.ids.campo_preguntas.text = "\n".join(contenido.get("preguntas", []))
        self.ids.campo_cuestionario.text = "\n".join(contenido.get("cuestionario", []))
        self.ids.campo_tarea_hogar.text = contenido.get("tarea_hogar", "") or ""
        self.ids.campo_resumen.text = contenido.get("resumen", "")

    def _construir_contenido_desde_campos(self) -> dict:
        return {
            "titulo": self.ids.campo_titulo.text.strip(),
            "objetivo": self.ids.campo_objetivo.text.strip(),
            "introduccion": self.ids.campo_introduccion.text.strip(),
            "explicacion": self.ids.campo_explicacion.text.strip(),
            "ejemplos": [
                linea.strip()
                for linea in self.ids.campo_ejemplos.text.split("\n")
                if linea.strip()
            ],
            "actividad": self.ids.campo_actividad.text.strip(),
            "preguntas": [
                linea.strip()
                for linea in self.ids.campo_preguntas.text.split("\n")
                if linea.strip()
            ],
            "cuestionario": [
                linea.strip()
                for linea in self.ids.campo_cuestionario.text.split("\n")
                if linea.strip()
            ],
            "tarea_hogar": self.ids.campo_tarea_hogar.text.strip(),
            "resumen": self.ids.campo_resumen.text.strip(),
        }

    def al_presionar_continuar(self):
        """Guarda la edicion (si hubo cambios) y avanza segun el flujo actual:
        a la seleccion de recursos (primera vez) o de vuelta a exportar
        (si se entro a re-editar una clase ya generada)."""
        app = MDApp.get_running_app()
        estado = app.estado

        contenido_editado = self._construir_contenido_desde_campos()
        estado.contenido_actual = contenido_editado

        self.ids.boton_continuar.disabled = True

        cliente_api.editar_clase(
            clase_id=estado.clase_id,
            contenido_json=contenido_editado,
            callback_exito=self._al_guardar_exito,
            callback_error=self._al_guardar_error,
        )

    def al_presionar_cancelar(self):
        """Descarta los cambios no guardados y vuelve a la pantalla de origen
        sin tocar el contenido ya guardado en el backend. Solo visible cuando
        se entra a re-editar una clase ya generada (no en el flujo inicial)."""
        app = MDApp.get_running_app()
        app.root.current = app.estado.pantalla_retorno_edicion

    def _al_guardar_exito(self, respuesta_clase):
        app = MDApp.get_running_app()
        self.ids.boton_continuar.disabled = False
        app.root.current = app.estado.pantalla_retorno_edicion

    def _al_guardar_error(self, error):
        self.ids.boton_continuar.disabled = False
        print(f"[PantallaContenido] error al guardar edicion: {error}")
        # Aun si falla el guardado remoto, dejamos avanzar con el contenido
        # local para no bloquear al docente.
        app = MDApp.get_running_app()
        app.root.current = app.estado.pantalla_retorno_edicion
