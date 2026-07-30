"""
Pantalla 1 - "Que queres ensenar hoy?"

El docente escribe el prompt, elige duracion, edad y materia, y dispara la
generacion de la clase.
"""

from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.chip import MDChip

from utils import cliente_api, voz_nativa


PLANTILLAS_CLASE = {
    "explicacion": (
        "Crea una clase clara y breve sobre {tema}. Inclui una introduccion "
        "con pregunta disparadora, explicacion paso a paso, ejemplos cotidianos, "
        "una actividad simple y preguntas de cierre."
    ),
    "practica": (
        "Crea una clase de practica guiada sobre {tema}. Inclui repaso inicial, "
        "ejercicios graduados de facil a dificil, errores comunes, trabajo en "
        "parejas y una mini puesta en comun."
    ),
    "evaluacion": (
        "Crea una clase con evaluacion corta sobre {tema}. Inclui objetivo, "
        "repaso breve, cinco preguntas o consignas, criterios de correccion y "
        "una devolucion simple para estudiantes."
    ),
}


PREFIJOS_PLANTILLAS = [
    "Crea una clase clara y breve sobre ",
    "Crea una clase de practica guiada sobre ",
    "Crea una clase con evaluacion corta sobre ",
]


SUGERENCIAS_PREDICTIVAS = [
    {
        "clave": "matematica",
        "texto": "Explicar con ejemplos cotidianos y ejercicios paso a paso.",
    },
    {
        "clave": "fracciones",
        "texto": "Incluir dibujos mentales, reparto de comida y comparacion de partes.",
    },
    {
        "clave": "tablas",
        "texto": "Agregar practica oral, patrones y un juego rapido de repaso.",
    },
    {
        "clave": "lengua",
        "texto": "Incluir lectura breve, vocabulario clave y produccion escrita corta.",
    },
    {
        "clave": "ciencias",
        "texto": "Usar una pregunta disparadora, observacion y ejemplo del entorno.",
    },
    {
        "clave": "historia",
        "texto": "Ordenar la explicacion en linea de tiempo y relacionar causas y consecuencias.",
    },
    {
        "clave": "geografia",
        "texto": "Usar mapa mental, ubicacion espacial y ejemplos cercanos.",
    },
    {
        "clave": "ingles",
        "texto": "Incluir vocabulario, pronunciacion simple y practica oral guiada.",
    },
    {
        "clave": "tdah",
        "texto": "Dividir la clase en bloques cortos con pausas y consignas simples.",
    },
    {
        "clave": "tea",
        "texto": "Agregar rutina visual, anticipacion y lenguaje concreto.",
    },
]


class PantallaInicio(Screen):
    """Pantalla inicial donde el docente describe la clase que necesita."""

    def on_pre_enter(self, *args):
        self._actualizar_sugerencias()
        self._actualizar_valores_recientes()

    def al_presionar_escuchar_ayuda(self):
        """Lee en voz alta como usar esta pantalla (ayuda de accesibilidad,
        solo funciona en Android; en Windows/Linux no hace nada)."""
        voz_nativa.leer_texto(
            "Describi que clase queres crear, elegi la duracion, "
            "completa la edad o grado y la materia, y toca generar clase."
        )

    def _actualizar_valores_recientes(self):
        """Muestra como chips tocables los valores de edad/materia que el
        docente ya uso antes, para que no tenga que volver a escribirlos.
        """
        if "contenedor_edades_recientes" not in self.ids:
            return
        app = MDApp.get_running_app()

        edades = app.estado.obtener_valores_recientes("edad_publico")
        materias = app.estado.obtener_valores_recientes("materia")

        self._poblar_chips_recientes(
            self.ids.contenedor_edades_recientes, edades, self.ids.campo_edad
        )
        self._poblar_chips_recientes(
            self.ids.contenedor_materias_recientes, materias, self.ids.campo_materia
        )
        self.ids.etiqueta_recientes.text = (
            "Usados antes: toca para completar" if (edades or materias) else ""
        )

    def _poblar_chips_recientes(self, contenedor, valores, campo_destino):
        contenedor.clear_widgets()
        for valor in valores:
            chip = MDChip(text=valor)
            chip.bind(
                on_release=lambda _chip, valor=valor: setattr(campo_destino, "text", valor)
            )
            contenedor.add_widget(chip)

    def al_presionar_plantilla(self, tipo: str):
        prompt_actual = self.ids.campo_prompt.text.strip()
        materia = self.ids.campo_materia.text.strip() or "la materia"
        tema = self._extraer_tema_base(prompt_actual) or f"un tema de {materia}"
        plantilla = PLANTILLAS_CLASE.get(tipo)
        if not plantilla:
            return
        self.ids.campo_prompt.text = plantilla.format(tema=tema)
        self.ids.etiqueta_error.text = ""
        self._actualizar_sugerencias()

    def _extraer_tema_base(self, texto: str) -> str:
        tema = " ".join((texto or "").split()).strip(" .")
        for prefijo in PREFIJOS_PLANTILLAS:
            if tema.lower().startswith(prefijo.lower()):
                tema = tema[len(prefijo) :]
                break
        for corte in [
            " Inclui ",
            " Incluye ",
            " Agregar ",
            " Agrega ",
            " Necesito ",
        ]:
            posicion = tema.lower().find(corte.lower())
            if posicion > 0:
                tema = tema[:posicion]
        return tema.strip(" .")

    def al_cambiar_prompt(self, texto: str):
        _ = texto
        self._actualizar_sugerencias()

    def _actualizar_sugerencias(self):
        if "etiqueta_sugerencias" not in self.ids:
            return
        texto_base = " ".join(
            [
                self.ids.campo_prompt.text,
                self.ids.campo_materia.text,
                self.ids.campo_edad.text,
            ]
        ).lower()
        sugerencias = [
            sugerencia["texto"]
            for sugerencia in SUGERENCIAS_PREDICTIVAS
            if sugerencia["clave"] in texto_base
        ]
        if not sugerencias:
            sugerencias = [
                "Sumar ejemplos cotidianos.",
                "Agregar una actividad breve.",
                "Cerrar con preguntas de comprension.",
            ]
        self.ids.etiqueta_sugerencias.text = "\n".join(
            f"- {sugerencia}" for sugerencia in sugerencias[:3]
        )

    def al_presionar_usar_sugerencias(self):
        sugerencias = self.ids.etiqueta_sugerencias.text.strip()
        if not sugerencias:
            return
        texto_limpio = sugerencias.replace("- ", "").replace("\n", " ")
        prompt_actual = self.ids.campo_prompt.text.strip()
        separador = " " if prompt_actual else ""
        self.ids.campo_prompt.text = f"{prompt_actual}{separador}{texto_limpio}".strip()
        self.ids.etiqueta_error.text = ""

    def al_presionar_generar_clase(self):
        """Callback del boton GENERAR CLASE."""
        app = MDApp.get_running_app()
        estado = app.estado

        campo_prompt = self.ids.campo_prompt
        prompt_texto = campo_prompt.text.strip()

        if len(prompt_texto) < 5:
            self.ids.etiqueta_error.text = "Escribi una descripcion un poco mas detallada."
            return

        edad_publico = self.ids.campo_edad.text.strip()
        materia = self.ids.campo_materia.text.strip()
        if not edad_publico:
            self.ids.etiqueta_error.text = "Completa la edad o grado para adaptar la clase."
            return
        if not materia:
            self.ids.etiqueta_error.text = "Completa la materia para enfocar mejor el tema."
            return

        self.ids.etiqueta_error.text = ""
        self.ids.boton_generar.disabled = True
        self.ids.indicador_carga.active = True

        estado.registrar_valor_reciente("edad_publico", edad_publico)
        estado.registrar_valor_reciente("materia", materia)

        duracion_minutos = int(self.ids.grupo_duracion.selected.text.replace(" min", ""))

        datos_prompt = {
            "prompt_original": prompt_texto,
            "duracion_minutos": duracion_minutos,
            "edad_publico": edad_publico,
            "materia": materia,
        }

        cliente_api.crear_clase(
            docente_id=estado.docente_id or "00000000-0000-0000-0000-000000000000",
            datos_prompt=datos_prompt,
            callback_exito=self._al_generar_exito,
            callback_error=self._al_generar_error,
        )

    def _al_generar_exito(self, respuesta_clase):
        app = MDApp.get_running_app()
        estado = app.estado

        estado.clase_id = str(respuesta_clase.get("id", ""))
        estado.codigo_publico = respuesta_clase.get("codigo_publico")
        estado.contenido_actual = respuesta_clase.get("contenido_json", {}) or {}
        # Flujo normal: tras editar el contenido recien generado, hay que
        # seguir hacia la adaptacion opcional (no es una re-edicion).
        estado.pantalla_retorno_edicion = "adaptar"

        self.ids.boton_generar.disabled = False
        self.ids.indicador_carga.active = False

        app.root.current = "contenido"

    def _al_generar_error(self, error):
        self.ids.boton_generar.disabled = False
        self.ids.indicador_carga.active = False
        self.ids.etiqueta_error.text = cliente_api.mensaje_error(error)
        print(f"[PantallaInicio] error al generar clase: {error}")
