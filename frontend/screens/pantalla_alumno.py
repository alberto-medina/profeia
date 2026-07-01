"""
Vista alumno: resumen, imagenes, audios y apoyos simples.
"""

import os
import tempfile
import threading
from functools import partial
from pathlib import Path

import requests
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from utils import cliente_api


class PantallaAlumno(Screen):
    """Muestra el paquete preparado para el estudiante."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._audio_actual = None
        self._descargas_temporales: list[Path] = []
        self._ruta_zip_alumno: Path | None = None

    def on_pre_enter(self, *args):
        app = MDApp.get_running_app()
        if app.estado.codigo_publico:
            self.ids.campo_codigo.text = app.estado.codigo_publico
        self._actualizar_barra_codigo()

        if app.estado.modo_actual == "alumno" and app.estado.codigo_publico:
            self._cargar_por_codigo(app.estado.codigo_publico)
        else:
            self._cargar_por_clase_actual()

    def _actualizar_barra_codigo(self):
        app = MDApp.get_running_app()
        codigo_listo = bool(app.estado.modo_actual == "alumno" and app.estado.codigo_publico)
        barra_codigo = self.ids.get("barra_codigo")
        if not barra_codigo:
            return
        barra_codigo.height = 0 if codigo_listo else dp(48)
        barra_codigo.opacity = 0 if codigo_listo else 1
        barra_codigo.disabled = codigo_listo

    def _texto_o_vacio(self, texto: str | None, vacio: str) -> str:
        texto_limpio = str(texto or "").strip()
        return texto_limpio if texto_limpio else vacio

    def _lista_o_vacio(self, items: list, vacio: str) -> str:
        valores = [str(item).strip() for item in (items or []) if str(item).strip()]
        return "\n".join(f"- {item}" for item in valores) if valores else vacio

    def _limpiar_estado_carga(self):
        self.ids.etiqueta_titulo.text = "Cargando clase..."
        self.ids.etiqueta_introduccion.text = ""
        self.ids.etiqueta_explicacion.text = ""
        self.ids.etiqueta_ejemplos.text = ""
        self.ids.etiqueta_actividad.text = ""
        self.ids.etiqueta_preguntas.text = ""
        self.ids.etiqueta_resumen.text = ""
        self.ids.etiqueta_cuestionario.text = ""
        self.ids.etiqueta_tarea_hogar.text = ""
        self.ids.etiqueta_apoyos.text = ""
        self.ids.etiqueta_estado_descarga.text = ""
        self.ids.contenedor_audios.clear_widgets()
        self.ids.contenedor_imagenes.clear_widgets()
        self.ids.indicador_carga.active = True
        self._ruta_zip_alumno = None
        self.ids.boton_abrir_paquete.disabled = True
        self.ids.boton_abrir_paquete.opacity = 0

    def _cargar_por_clase_actual(self):
        self._limpiar_estado_carga()
        app = MDApp.get_running_app()
        if app.estado.clase_id:
            cliente_api.obtener_paquete_alumno(
                clase_id=app.estado.clase_id,
                callback_exito=self._al_cargar_exito,
                callback_error=self._al_cargar_error,
            )
        elif app.estado.codigo_publico:
            self._cargar_por_codigo(app.estado.codigo_publico)
        else:
            self.ids.indicador_carga.active = False
            self.ids.etiqueta_titulo.text = "Ingresa un codigo de clase."

    def al_presionar_buscar_codigo(self):
        codigo = self.ids.campo_codigo.text.strip().upper()
        if not codigo:
            self.ids.etiqueta_titulo.text = "Ingresa el codigo que te dio tu docente."
            return
        self._cargar_por_codigo(codigo)

    def _cargar_por_codigo(self, codigo):
        self._limpiar_estado_carga()
        cliente_api.obtener_paquete_alumno_por_codigo(
            codigo_publico=codigo,
            callback_exito=self._al_cargar_exito,
            callback_error=self._al_cargar_error,
        )

    def _al_cargar_exito(self, paquete):
        app = MDApp.get_running_app()
        app.estado.paquete_alumno_actual = paquete
        app.estado.codigo_publico = paquete.get("codigo_publico") or app.estado.codigo_publico
        if app.estado.modo_actual != "alumno":
            app.estado.clase_id = paquete.get("clase_id") or app.estado.clase_id
        self.ids.indicador_carga.active = False

        self.ids.etiqueta_titulo.text = paquete.get("titulo", "Clase")
        self.ids.etiqueta_introduccion.text = self._texto_o_vacio(
            paquete.get("introduccion"),
            "Esta clase todavia no tiene una introduccion cargada.",
        )
        self.ids.etiqueta_explicacion.text = self._texto_o_vacio(
            paquete.get("explicacion"),
            "Esta clase todavia no tiene una explicacion cargada.",
        )
        ejemplos = paquete.get("ejemplos", []) or []
        self.ids.etiqueta_ejemplos.text = self._lista_o_vacio(
            ejemplos,
            "Esta clase todavia no tiene ejemplos cargados.",
        )
        self.ids.etiqueta_actividad.text = self._texto_o_vacio(
            paquete.get("actividad"),
            "Esta clase todavia no tiene una actividad cargada.",
        )
        preguntas = paquete.get("preguntas", []) or []
        self.ids.etiqueta_preguntas.text = self._lista_o_vacio(
            preguntas,
            "Esta clase todavia no tiene preguntas cargadas.",
        )
        self.ids.etiqueta_resumen.text = self._texto_o_vacio(
            paquete.get("resumen"),
            "Esta clase todavia no tiene resumen cargado.",
        )
        cuestionario = paquete.get("cuestionario", []) or []
        self.ids.etiqueta_cuestionario.text = self._lista_o_vacio(
            cuestionario,
            "Esta clase todavia no tiene cuestionario cargado.",
        )
        self.ids.etiqueta_tarea_hogar.text = (
            self._texto_o_vacio(paquete.get("tarea_hogar"), "Sin tarea para el hogar cargada.")
        )

        audio_resumen = paquete.get("audio_resumen")
        audios_docente = paquete.get("audios_docente", [])
        if audio_resumen:
            self._agregar_fila_audio(audio_resumen, "Audio generado")
        for audio in audios_docente:
            self._agregar_fila_audio(audio, "Audio docente")
        if not audio_resumen and not audios_docente:
            self._agregar_mensaje(self.ids.contenedor_audios, "No hay audios para esta clase todavia.")

        imagenes = paquete.get("imagenes", [])
        for imagen in imagenes:
            self._agregar_fila_imagen(imagen)
        if not imagenes:
            self._agregar_mensaje(self.ids.contenedor_imagenes, "No hay imagenes para esta clase todavia.")

        apoyos = paquete.get("apoyos") or {}
        rutina = apoyos.get("rutina_visual", [])
        consigna = apoyos.get("consigna_simple", "")
        texto_apoyos = []
        if consigna:
            texto_apoyos.append(consigna)
        if rutina:
            texto_apoyos.append("\n".join(rutina))
        self.ids.etiqueta_apoyos.text = "\n\n".join(texto_apoyos) or "Sin apoyos especiales para esta clase."

    def _al_cargar_error(self, error):
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_titulo.text = cliente_api.mensaje_error(error)
        print(f"[PantallaAlumno] error al cargar paquete alumno: {error}")

    def _nombre_recurso(self, recurso: dict, prefijo: str = "Recurso") -> str:
        metadata = recurso.get("metadata_json") or {}
        return (
            metadata.get("nombre")
            or metadata.get("titulo")
            or Path(str(recurso.get("url_storage") or "")).name
            or prefijo
        )

    def _ruta_local(self, recurso: dict) -> Path | None:
        url_storage = str(recurso.get("url_storage") or "")
        if not url_storage or url_storage.startswith(("storage://", "http://", "https://")):
            return None
        ruta = Path(url_storage)
        return ruta if ruta.exists() and ruta.is_file() else None

    def _url_remota(self, recurso: dict) -> str | None:
        url_storage = str(recurso.get("url_storage") or "")
        if url_storage.startswith(("http://", "https://")):
            return url_storage
        return None

    def _agregar_mensaje(self, contenedor, texto: str):
        contenedor.add_widget(self._crear_tarjeta_mensaje(texto))

    def _crear_tarjeta_base(self, altura: int = 92) -> MDCard:
        app = MDApp.get_running_app()
        return MDCard(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(6),
            size_hint_y=None,
            height=dp(altura),
            radius=[dp(8)],
            elevation=1,
            md_bg_color=app.color_superficie,
        )

    def _crear_etiqueta_recurso(self, texto: str, alto: int = 30) -> MDLabel:
        app = MDApp.get_running_app()
        etiqueta = MDLabel(
            text=texto,
            size_hint_y=None,
            height=dp(alto),
            theme_text_color="Custom",
            text_color=app.color_texto,
        )
        etiqueta.bind(
            width=lambda instancia, ancho: setattr(instancia, "text_size", (ancho, None))
        )
        return etiqueta

    def _crear_tarjeta_mensaje(self, texto: str) -> MDCard:
        app = MDApp.get_running_app()
        tarjeta = self._crear_tarjeta_base(58)
        tarjeta.add_widget(
            MDLabel(
                text=texto,
                size_hint_y=None,
                height=dp(34),
                theme_text_color="Custom",
                text_color=app.color_texto_secundario,
            )
        )
        return tarjeta

    def _agregar_fila_audio(self, recurso: dict, prefijo: str):
        nombre = self._nombre_recurso(recurso, prefijo)
        ruta = self._ruta_local(recurso)
        url = self._url_remota(recurso)

        fila = self._crear_tarjeta_base(102)
        fila.add_widget(self._crear_etiqueta_recurso(f"{prefijo}: {nombre}"))

        acciones = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))
        boton_reproducir = MDRectangleFlatButton(
            text="ESCUCHAR",
            disabled=(ruta is None and url is None),
            on_release=partial(self._reproducir_audio, ruta, url),
        )
        boton_detener = MDFlatButton(text="DETENER", on_release=lambda *args: self._detener_audio())
        boton_abrir = MDFlatButton(
            text="ABRIR",
            disabled=(ruta is None and url is None),
            on_release=partial(self._abrir_recurso, ruta, url),
        )
        acciones.add_widget(boton_reproducir)
        acciones.add_widget(boton_detener)
        acciones.add_widget(boton_abrir)
        fila.add_widget(acciones)
        self.ids.contenedor_audios.add_widget(fila)

        if ruta is None and url is None:
            self._agregar_mensaje(self.ids.contenedor_audios, "Audio no disponible.")

    def _reproducir_audio(self, ruta: Path | None, url: str | None = None, *args):
        if ruta is not None:
            self._reproducir_audio_local(ruta)
            return
        if url:
            self._descargar_recurso_temporal(url, self._reproducir_audio_local)

    def _reproducir_audio_local(self, ruta: Path):
        self._detener_audio()
        self._audio_actual = SoundLoader.load(str(ruta))
        if self._audio_actual:
            self._audio_actual.play()

    def _detener_audio(self):
        if self._audio_actual:
            self._audio_actual.stop()
            self._audio_actual = None

    def _agregar_fila_imagen(self, recurso: dict):
        nombre = self._nombre_recurso(recurso, "Imagen")
        ruta = self._ruta_local(recurso)
        url = self._url_remota(recurso)

        fila = self._crear_tarjeta_base(102)
        fila.add_widget(self._crear_etiqueta_recurso(f"Imagen: {nombre}"))

        acciones = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))
        acciones.add_widget(
            MDRectangleFlatButton(
                text="VER",
                disabled=(ruta is None and url is None),
                on_release=partial(self._ver_imagen, ruta, url),
            )
        )
        acciones.add_widget(
            MDFlatButton(
                text="ABRIR",
                disabled=(ruta is None and url is None),
                on_release=partial(self._abrir_recurso, ruta, url),
            )
        )
        fila.add_widget(acciones)
        self.ids.contenedor_imagenes.add_widget(fila)

        if ruta is None and url is None:
            self._agregar_mensaje(self.ids.contenedor_imagenes, "Imagen no disponible.")

    def _ver_imagen(self, ruta: Path | None, url: str | None = None, *args):
        if ruta is not None:
            self._ver_imagen_local(ruta)
            return
        if url:
            self._descargar_recurso_temporal(url, self._ver_imagen_local)

    def _ver_imagen_local(self, ruta: Path):
        imagen = Image(source=str(ruta), allow_stretch=True, keep_ratio=True)
        Popup(
            title=ruta.name,
            content=imagen,
            size_hint=(0.92, 0.82),
        ).open()

    def _descargar_recurso_temporal(self, url: str, callback_exito):
        def tarea():
            try:
                respuesta = requests.get(url, timeout=20)
                respuesta.raise_for_status()
                extension = Path(url.split("?", 1)[0]).suffix or ".bin"
                destino = Path(tempfile.gettempdir()) / f"profeia-recurso-{len(self._descargas_temporales)}{extension}"
                destino.write_bytes(respuesta.content)
                self._descargas_temporales.append(destino)
                Clock.schedule_once(lambda dt: callback_exito(destino))
            except Exception as error:  # noqa: BLE001 - feedback simple para recurso remoto
                Clock.schedule_once(lambda dt: self._mostrar_error_recurso(error))

        threading.Thread(target=tarea, daemon=True).start()

    def _mostrar_error_recurso(self, error):
        self.ids.etiqueta_estado_descarga.text = "No se pudo abrir el recurso."
        print(f"[PantallaAlumno] error recurso remoto: {error}")

    def _abrir_recurso(self, ruta: Path | None, url: str | None, *args):
        if ruta is not None:
            os.startfile(ruta)  # noqa: S606 - accion explicita del usuario en Windows
            return
        if url:
            os.startfile(url)  # noqa: S606 - accion explicita del usuario en Windows

    def al_presionar_descargar_paquete(self):
        codigo = self.ids.campo_codigo.text.strip().upper()
        if not codigo:
            app = MDApp.get_running_app()
            codigo = app.estado.codigo_publico or ""
        if not codigo:
            self.ids.etiqueta_estado_descarga.text = "Primero ingresa un codigo de clase."
            return

        self.ids.boton_descargar_paquete.disabled = True
        self.ids.boton_abrir_paquete.disabled = True
        self.ids.boton_abrir_paquete.opacity = 0
        self.ids.etiqueta_estado_descarga.text = "Preparando paquete ZIP..."

        cliente_api.exportar_zip_por_codigo(
            codigo_publico=codigo,
            callback_exito=self._al_descargar_paquete_exito,
            callback_error=self._al_descargar_paquete_error,
        )

    def _al_descargar_paquete_exito(self, recurso_generado):
        self.ids.boton_descargar_paquete.disabled = False
        ruta = Path(recurso_generado.get("url_storage", ""))
        self._ruta_zip_alumno = ruta
        self.ids.etiqueta_estado_descarga.text = "Paquete ZIP listo."
        self.ids.boton_abrir_paquete.disabled = False
        self.ids.boton_abrir_paquete.opacity = 1

    def _al_descargar_paquete_error(self, error):
        self.ids.boton_descargar_paquete.disabled = False
        self.ids.etiqueta_estado_descarga.text = cliente_api.mensaje_error(error)
        print(f"[PantallaAlumno] error ZIP alumno: {error}")

    def al_presionar_abrir_paquete(self):
        if not self._ruta_zip_alumno:
            return
        carpeta = self._ruta_zip_alumno.parent
        if carpeta.exists():
            os.startfile(carpeta)  # noqa: S606 - accion explicita del usuario en Windows

    def al_presionar_volver(self):
        self._detener_audio()
        app = MDApp.get_running_app()
        if app.estado.modo_actual == "alumno":
            app.estado.codigo_publico = None
            app.estado.paquete_alumno_actual = None
            self.ids.campo_codigo.text = ""
            self._actualizar_barra_codigo()
            app.root.current = "entrada"
        else:
            app.root.current = "exportar"
