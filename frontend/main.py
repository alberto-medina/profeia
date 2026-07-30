"""
Punto de entrada de la app ProfeIA (Kivy / KivyMD).

Mismo patron que Legal App: ScreenManager con pantallas registradas, estilo
KivyMD, y configuracion de ventana solo para desarrollo en Windows
(no afecta a Android).
"""

import os

from kivy.config import Config

# Tamano de ventana de referencia para pruebas en Windows/Linux.
# En Android esto no tiene efecto.
Config.set("graphics", "width", "420")
Config.set("graphics", "height", "780")

from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

# En Android, sin esto la ventana no se reacomoda cuando aparece el
# teclado: el teclado queda flotando encima y tapa el campo que el
# usuario esta llenando (mas grave en pantallas largas con ScrollView,
# donde el campo enfocado puede quedar bien abajo). "below_target" corre
# la ventana para que el campo con foco quede siempre visible arriba del
# teclado. En Windows/Linux no tiene efecto (no hay teclado en pantalla).
Window.softinput_mode = "below_target"

from screens.pantalla_inicio import PantallaInicio
from screens.pantalla_adaptar import PantallaAdaptar
from screens.pantalla_alumno import PantallaAlumno
from screens.pantalla_apoyo import PantallaApoyo
from screens.pantalla_contenido import PantallaContenido
from screens.pantalla_dedicatoria import PantallaDedicatoria
from screens.pantalla_entrada import PantallaEntrada
from screens.pantalla_login import PantallaLogin
from screens.pantalla_registro import PantallaRegistro
from screens.pantalla_historial import PantallaHistorial
from screens.pantalla_plan import PantallaPlan
from screens.pantalla_recursos import PantallaRecursos
from screens.pantalla_voz import PantallaVoz
from screens.pantalla_video import PantallaVideo
from screens.pantalla_exportar import PantallaExportar
from utils.estado_app import EstadoApp

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_FUENTES = os.path.join(RUTA_BASE, "assets", "fonts")

# Reemplaza la familia "Roboto" (la que usan por defecto Kivy y KivyMD en
# todos los widgets) por Poppins, para no tener que tocar font_name en
# cada pantalla del .kv.
LabelBase.register(
    name="Roboto",
    fn_regular=os.path.join(RUTA_FUENTES, "Poppins-Regular.ttf"),
    fn_bold=os.path.join(RUTA_FUENTES, "Poppins-Bold.ttf"),
)
LabelBase.register(
    name="RobotoLight",
    fn_regular=os.path.join(RUTA_FUENTES, "Poppins-Regular.ttf"),
)
LabelBase.register(
    name="RobotoMedium",
    fn_regular=os.path.join(RUTA_FUENTES, "Poppins-Medium.ttf"),
)


class ProfeIAApp(MDApp):
    """Aplicacion principal de ProfeIA."""

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.accent_palette = "Amber"
        self.color_fondo = [0.957, 0.949, 0.925, 1]
        self.color_superficie = [1, 1, 1, 1]
        self.color_borde = [0.847, 0.835, 0.8, 1]
        self.color_azul = [0.122, 0.227, 0.322, 1]
        self.color_texto = [0.102, 0.102, 0.094, 1]
        self.color_texto_secundario = [0.42, 0.412, 0.384, 1]
        self.color_exito = [0.373, 0.49, 0.227, 1]

        self.title = "ProfeIA"

        # Estado global accesible desde cualquier pantalla via
        # MDApp.get_running_app().estado
        self.estado = EstadoApp()
        self.estado.cargar_sesion()

        gestor_pantallas = ScreenManager()
        gestor_pantallas.add_widget(PantallaDedicatoria(name="dedicatoria"))
        gestor_pantallas.add_widget(PantallaEntrada(name="entrada"))
        gestor_pantallas.add_widget(PantallaLogin(name="login"))
        gestor_pantallas.add_widget(PantallaRegistro(name="registro"))
        gestor_pantallas.add_widget(PantallaInicio(name="inicio"))
        gestor_pantallas.add_widget(PantallaPlan(name="configuracion"))
        gestor_pantallas.add_widget(PantallaHistorial(name="historial"))
        gestor_pantallas.add_widget(PantallaContenido(name="contenido"))
        gestor_pantallas.add_widget(PantallaAdaptar(name="adaptar"))
        gestor_pantallas.add_widget(PantallaApoyo(name="apoyo"))
        gestor_pantallas.add_widget(PantallaAlumno(name="alumno"))
        gestor_pantallas.add_widget(PantallaRecursos(name="recursos"))
        gestor_pantallas.add_widget(PantallaVoz(name="voz"))
        gestor_pantallas.add_widget(PantallaVideo(name="video"))
        gestor_pantallas.add_widget(PantallaExportar(name="exportar"))

        return gestor_pantallas


if __name__ == "__main__":
    ProfeIAApp().run()
