"""
Lectura en voz alta usando el motor de texto a voz NATIVO del celular
(android.speech.tts.TextToSpeech via pyjnius), pensada como ayuda de
accesibilidad para leer instrucciones cortas de pantalla.

Se usa el TTS nativo (no el TTS de IA del backend) a proposito: el de IA
esta pensado para narrar el contenido completo de una clase y depende de
red + un proveedor externo, lo cual es lento y con costo para algo tan
chico como leer una instruccion de pantalla. El TTS nativo es instantaneo,
gratis y funciona incluso sin conexion.

En Windows/Linux (desarrollo) esto no hace nada: se detecta que no es
Android y se ignora en silencio, para no romper la app fuera de Android.
"""

from kivy.utils import platform

_motor_tts = None


def _obtener_motor():
    global _motor_tts
    if platform != "android":
        return None
    if _motor_tts is not None:
        return _motor_tts

    try:
        from jnius import autoclass, PythonJavaClass, java_method

        TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Locale = autoclass("java.util.Locale")

        class _ListenerInicializacion(PythonJavaClass):
            __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
            __javacontext__ = "app"

            def __init__(self):
                super().__init__()
                self.motor = None

            @java_method("(I)V")
            def onInit(self, status):
                if status == 0 and self.motor is not None:
                    try:
                        self.motor.setLanguage(Locale("spa", "ARG"))
                    except Exception as error:  # noqa: BLE001
                        print(f"[voz_nativa] No se pudo fijar idioma: {error}")

        listener = _ListenerInicializacion()
        motor = TextToSpeech(PythonActivity.mActivity, listener)
        listener.motor = motor
        _motor_tts = motor
        return _motor_tts
    except Exception as error:  # noqa: BLE001 - cualquier fallo nativo, no debe tumbar la app
        print(f"[voz_nativa] TTS nativo no disponible: {error}")
        return None


def leer_texto(texto: str) -> bool:
    """
    Lee un texto en voz alta con el TTS nativo del dispositivo.
    Devuelve True si se pudo disparar la lectura, False si no esta
    disponible (por ejemplo en Windows/Linux, donde no hace nada).
    """
    texto_limpio = (texto or "").strip()
    if not texto_limpio:
        return False

    motor = _obtener_motor()
    if motor is None:
        return False

    try:
        from jnius import autoclass

        TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
        motor.speak(texto_limpio, TextToSpeech.QUEUE_FLUSH, None, "profeia-lectura")
        return True
    except Exception as error:  # noqa: BLE001
        print(f"[voz_nativa] Error al leer texto: {error}")
        return False


def detener():
    """Corta la lectura en curso, si hay una."""
    if _motor_tts is not None:
        try:
            _motor_tts.stop()
        except Exception:  # noqa: BLE001
            pass
