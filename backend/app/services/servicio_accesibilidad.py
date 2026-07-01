"""
Generacion de apoyos pedagogicos para atencion, TEA y lectura facil.
"""

from app.models.accesibilidad import ApoyosAccesibilidad, SolicitudApoyosAccesibilidad


def generar_apoyos_accesibilidad(
    contenido_json: dict,
    solicitud: SolicitudApoyosAccesibilidad,
) -> ApoyosAccesibilidad:
    """
    Genera adaptaciones educativas, no diagnosticas ni terapeuticas.

    Estas sugerencias ayudan al docente a presentar la clase con mas claridad,
    previsibilidad y opciones de participacion.
    """
    titulo = contenido_json.get("titulo", "la clase")
    actividad = contenido_json.get("actividad", "la actividad principal")
    resumen = contenido_json.get("resumen", "el cierre de la clase")
    necesidades = set(solicitud.necesidades)

    adaptaciones = [
        "Presentar un objetivo por vez y confirmar comprension antes de avanzar.",
        "Usar ejemplos concretos y cercanos antes de pasar a una consigna abstracta.",
        "Permitir responder oralmente, por escrito o senalando una opcion.",
    ]
    apoyos_sensoriales = []

    if "tdah" in necesidades:
        adaptaciones.extend(
            [
                "Dividir la tarea en pasos de 3 a 5 minutos.",
                "Usar una senal visual para marcar inicio, mitad y cierre de la actividad.",
                "Intercalar una micro-pausa de movimiento antes de la practica.",
            ]
        )

    if "tea" in necesidades:
        adaptaciones.extend(
            [
                "Anticipar cambios de actividad con una frase clara y siempre igual.",
                "Evitar consignas ambiguas o dobles sentidos.",
                "Ofrecer un ejemplo resuelto antes de pedir produccion propia.",
            ]
        )
        apoyos_sensoriales.extend(
            [
                "Permitir auriculares o ubicacion con menos estimulos si el aula lo permite.",
                "Ofrecer una tarjeta de pausa o descanso breve acordada previamente.",
            ]
        )

    if "lectura_facil" in necesidades or "dificultad_lectora" in necesidades:
        adaptaciones.extend(
            [
                "Usar frases cortas, vocabulario directo y una idea por renglon.",
                "Acompanhar cada concepto nuevo con una palabra clave visible.",
                "Leer la consigna en voz alta y verificar que todos sepan que hacer primero.",
            ]
        )

    if "ansiedad" in necesidades:
        adaptaciones.extend(
            [
                "Avisar que habra tiempo para pensar antes de responder.",
                "Permitir practicar con un par antes de compartir con todo el grupo.",
            ]
        )

    if "baja_vision" in necesidades:
        adaptaciones.extend(
            [
                "Usar alto contraste, letra grande y evitar depender solo del color.",
                "Leer en voz alta todo texto proyectado o escrito en el pizarron.",
            ]
        )

    rutina_visual = []
    if solicitud.incluir_rutina_visual:
        rutina_visual = [
            "1. Miramos el objetivo de la clase.",
            "2. Escuchamos una explicacion breve.",
            "3. Vemos un ejemplo resuelto.",
            "4. Practicamos en parejas o individualmente.",
            "5. Cerramos con una pregunta de repaso.",
        ]

    pausas = []
    if solicitud.incluir_pausas:
        pausas = [
            "Pausa de 30 segundos para respirar antes de la actividad.",
            "Pausa breve de movimiento entre explicacion y practica.",
            "Pausa de revision: cada estudiante marca que entendio y que necesita repetir.",
        ]

    consigna = (
        f"Hoy vamos a trabajar {titulo}. Primero miramos un ejemplo, despues "
        f"hacemos esta actividad: {actividad}. Si algo no se entiende, pedimos "
        "ayuda y repetimos el paso."
    )

    return ApoyosAccesibilidad(
        resumen_docente=(
            f"Adaptacion educativa para {titulo}. Nivel de apoyo: "
            f"{solicitud.nivel_apoyo}. No reemplaza orientacion profesional; "
            "sirve como guia pedagogica para hacer la clase mas clara y previsible."
        ),
        consigna_simple=consigna,
        rutina_visual=rutina_visual,
        pausas_sugeridas=pausas,
        adaptaciones=adaptaciones,
        apoyos_sensoriales=apoyos_sensoriales,
        verificacion_comprension=[
            "Pedir que expliquen el primer paso con sus palabras.",
            "Ofrecer dos opciones y preguntar cual corresponde al ejemplo.",
            "Usar semaforo: verde entendi, amarillo necesito repetir, rojo necesito ayuda.",
        ],
        evaluacion_flexible=[
            "Aceptar respuesta oral, escrita, dibujo o seleccion de opciones.",
            f"Evaluar si puede explicar la idea central del cierre: {resumen}",
            "Dar tiempo adicional cuando la consigna tenga varios pasos.",
        ],
    )
