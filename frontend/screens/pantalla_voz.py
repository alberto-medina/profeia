"""
Pantalla 4 - Configuracion de voz (clonada / masculina / femenina / infantil,
idioma y velocidad).
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

from utils import cliente_api


class PantallaVoz(Screen):
    """Configura los parametros de TTS y dispara la generacion del audio."""

    def al_presionar_atras(self):
        app = MDApp.get_running_app()
        app.root.current = "recursos"

    def al_presionar_generar_voz(self):
        app = MDApp.get_running_app()
        estado = app.estado

        voz_elegida = self.ids.grupo_voz.selected.valor_interno
        velocidad = round(self.ids.slider_velocidad.value, 2)

        parametros_voz = {
            "voz": voz_elegida,
            "idioma": "es",
            "velocidad": velocidad,
        }
        estado.parametros_voz = parametros_voz

        self.ids.boton_generar_voz.disabled = True
        self.ids.indicador_carga.active = True

        cliente_api.generar_voz(
            clase_id=estado.clase_id,
            parametros_voz=parametros_voz,
            callback_exito=self._al_generar_exito,
            callback_error=self._al_generar_error,
        )

    def _al_generar_exito(self, recurso_generado):
        app = MDApp.get_running_app()
        estado = app.estado
        estado.recursos_generados["voz"] = recurso_generado

        self.ids.boton_generar_voz.disabled = False
        self.ids.indicador_carga.active = False

        if estado.recursos_seleccionados.get("video"):
            app.root.current = "video"
        else:
            app.root.current = "exportar"

    def _al_generar_error(self, error):
        self.ids.boton_generar_voz.disabled = False
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_error.text = cliente_api.mensaje_error(error)
        print(f"[PantallaVoz] error al generar voz: {error}")
