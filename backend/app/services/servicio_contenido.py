"""
Servicio de generacion de contenido pedagogico.

Este modulo abstrae el proveedor de IA (GPT u otro) detras de una funcion
simple, para poder cambiar de proveedor sin tocar los routers ni la logica
de negocio.
"""

import json
import re

import httpx
from fastapi import HTTPException, status

from app.core.config import obtener_configuracion
from app.models.clase import ContenidoPedagogico, SolicitudCrearClase


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
WIKIPEDIA_API_URL = "https://es.wikipedia.org/w/api.php"
WIKIPEDIA_HEADERS = {
    "User-Agent": "ProfeIA/0.1 educativo-local (contacto: desarrollo@profeia.local)"
}


PERFILES_MATERIA = {
    "matematica": {
        "eje": "resolucion de problemas y razonamiento",
        "situacion": "una compra, un juego con puntajes, medidas de una receta o una organizacion de grupos",
        "estrategia": "usar dibujos, calculos intermedios, estimacion y explicacion del procedimiento",
        "actividad": "resolver una situacion en parejas, comparar estrategias y explicar el camino elegido",
        "producto": "un procedimiento explicado paso a paso",
    },
    "lengua": {
        "eje": "comprension lectora, vocabulario y produccion escrita",
        "situacion": "un cuento breve, una noticia escolar, una carta o una descripcion de un personaje",
        "estrategia": "leer con proposito, subrayar ideas clave, conversar interpretaciones y escribir una respuesta breve",
        "actividad": "leer un texto corto, identificar informacion explicita e inferir una idea no dicha directamente",
        "producto": "un parrafo propio con inicio, desarrollo y cierre",
    },
    "ciencias naturales": {
        "eje": "observacion, explicacion de fenomenos y cuidado del ambiente o del cuerpo",
        "situacion": "una experiencia simple, un objeto del aula, una planta, el agua, la luz o el cuerpo humano",
        "estrategia": "observar, formular hipotesis, registrar datos y explicar con vocabulario cientifico simple",
        "actividad": "hacer una observacion guiada, completar un cuadro y sacar una conclusion",
        "producto": "un registro con dibujo, palabras clave y conclusion",
    },
    "ciencias sociales": {
        "eje": "tiempo historico, espacio geografico, convivencia y vida social",
        "situacion": "un mapa, una linea de tiempo, una fuente historica, una norma de convivencia o una situacion barrial",
        "estrategia": "ubicar en tiempo y espacio, comparar antes/ahora, reconocer actores sociales y causas",
        "actividad": "analizar una imagen o texto breve, ordenar hechos y explicar relaciones",
        "producto": "una linea de tiempo, mapa simple o cuadro comparativo",
    },
    "ingles": {
        "eje": "vocabulario, comprension simple y produccion oral guiada",
        "situacion": "saludos, objetos del aula, familia, colores, animales, comida o rutinas",
        "estrategia": "presentar palabras con imagenes, repetir pronunciacion, usar frases modelo y practicar en parejas",
        "actividad": "escuchar/repetir vocabulario, completar una frase y hacer una mini conversacion",
        "producto": "tres frases simples usando el vocabulario nuevo",
    },
    "educacion artistica": {
        "eje": "exploracion, expresion y apreciacion de producciones visuales o sonoras",
        "situacion": "colores, formas, ritmos, texturas, obras, canciones o producciones propias",
        "estrategia": "observar, describir, probar materiales y justificar decisiones expresivas",
        "actividad": "analizar una obra o ejemplo y crear una produccion breve con una consigna clara",
        "producto": "una produccion personal con breve explicacion",
    },
    "educacion fisica": {
        "eje": "habilidades motrices, juego limpio, coordinacion y toma de decisiones",
        "situacion": "un juego reducido, una posta, un circuito, una practica de pases o una situacion de equipo",
        "estrategia": "demostrar el gesto, practicar de forma progresiva, dar feedback breve y cerrar con juego aplicado",
        "actividad": "realizar una entrada en calor, practicar la habilidad por estaciones y aplicarla en un juego corto",
        "producto": "una mejora observable en la tecnica y una explicacion breve de la regla o estrategia usada",
    },
}

ALIAS_MATERIAS = {
    "matematica": "matematica",
    "matematicas": "matematica",
    "matemática": "matematica",
    "matemáticas": "matematica",
    "lengua": "lengua",
    "practicas del lenguaje": "lengua",
    "prácticas del lenguaje": "lengua",
    "ciencias naturales": "ciencias naturales",
    "naturales": "ciencias naturales",
    "biologia": "ciencias naturales",
    "biología": "ciencias naturales",
    "ciencias sociales": "ciencias sociales",
    "sociales": "ciencias sociales",
    "historia": "ciencias sociales",
    "geografia": "ciencias sociales",
    "geografía": "ciencias sociales",
    "ingles": "ingles",
    "inglés": "ingles",
    "english": "ingles",
    "educacion artistica": "educacion artistica",
    "educación artística": "educacion artistica",
    "artistica": "educacion artistica",
    "artística": "educacion artistica",
    "arte": "educacion artistica",
    "musica": "educacion artistica",
    "música": "educacion artistica",
    "educacion fisica": "educacion fisica",
    "educación física": "educacion fisica",
    "fisica": "educacion fisica",
    "física": "educacion fisica",
    "deportes": "educacion fisica",
}


def construir_prompt_sistema() -> str:
    """Prompt de sistema usado para guiar a la IA generadora de contenido."""
    return (
        "Sos un disenador instruccional experto. Tu tarea es generar el "
        "contenido completo de una clase a partir de un pedido de un "
        "docente. Devolves SOLO un JSON con las claves: titulo, objetivo, "
        "introduccion, explicacion, ejemplos (lista), actividad, preguntas "
        "(lista), cuestionario (lista), tarea_hogar, resumen. El tono debe ser claro, paciente y adecuado a la "
        "edad indicada. Los ejemplos deben ser cotidianos y locales "
        "(Argentina) cuando sea posible."
    )


def _valor_configurado(valor: str) -> bool:
    valor_limpio = (valor or "").strip()
    return bool(valor_limpio) and not valor_limpio.startswith("TU_")


def _schema_contenido_pedagogico() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "titulo": {"type": "string"},
            "objetivo": {"type": "string"},
            "introduccion": {"type": "string"},
            "explicacion": {"type": "string"},
            "ejemplos": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 5,
            },
            "actividad": {"type": "string"},
            "preguntas": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 6,
            },
            "cuestionario": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 8,
            },
            "tarea_hogar": {"type": "string"},
            "resumen": {"type": "string"},
        },
        "required": [
            "titulo",
            "objetivo",
            "introduccion",
            "explicacion",
            "ejemplos",
            "actividad",
            "preguntas",
            "cuestionario",
            "tarea_hogar",
            "resumen",
        ],
    }


def _instruccion_json_pedagogico() -> str:
    return (
        "Devolve solamente JSON valido, sin markdown ni texto extra. "
        "Usa exactamente estas claves: titulo, objetivo, introduccion, "
        "explicacion, ejemplos, actividad, preguntas, cuestionario, "
        "tarea_hogar, resumen. "
        "La clase debe ser concreta, lista para aula argentina, con ejemplos "
        "claros, una explicacion didactica, actividad aplicable, preguntas, "
        "cuestionario breve y tarea. No repitas literalmente el pedido del "
        "docente como contenido."
    )


def _construir_prompt_usuario(solicitud: SolicitudCrearClase) -> str:
    return (
        "Genera una clase completa con estos datos:\n"
        f"- Pedido docente: {solicitud.prompt_original}\n"
        f"- Materia: {solicitud.materia}\n"
        f"- Edad o publico: {solicitud.edad_publico}\n"
        f"- Duracion: {solicitud.duracion_minutos} minutos\n\n"
        "Necesito contenido listo para editar y exportar: claro, aplicable "
        "en aula, con ejemplos cotidianos, preguntas de repaso, cuestionario "
        "breve y tarea para el hogar."
    )


def _limpiar_json_modelo(texto: str) -> str:
    texto_limpio = (texto or "").strip()
    if texto_limpio.startswith("```"):
        texto_limpio = re.sub(r"^```(?:json)?", "", texto_limpio, flags=re.IGNORECASE).strip()
        texto_limpio = re.sub(r"```$", "", texto_limpio).strip()
    inicio = texto_limpio.find("{")
    fin = texto_limpio.rfind("}")
    if inicio >= 0 and fin > inicio:
        return texto_limpio[inicio : fin + 1]
    return texto_limpio


def _normalizar_espacios(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip(" .")


def _restaurar_espanol(texto: str) -> str:
    reemplazos = {
        "ninos": "niños",
        "nino": "niño",
        "anos": "años",
        "ano": "año",
        "pizarron": "pizarrón",
        "explicacion": "explicación",
        "situacion": "situación",
        "comprension": "comprensión",
        "produccion": "producción",
        "relacion": "relación",
        "relacionen": "relacionen",
        "fenomenos": "fenómenos",
        "observacion": "observación",
        "Observacion": "Observación",
        "demostracion": "demostración",
        "Demostracion": "Demostración",
        "coordinacion": "coordinación",
        "tecnica": "técnica",
        "tecnico": "técnico",
        "caracteristicas": "características",
        "historico": "histórico",
        "geografico": "geográfico",
        "ubicacion": "ubicación",
        "linea": "línea",
        "decision": "decisión",
        "aplicacion": "aplicación",
        "fraccion": "fracción",
        "cuantos": "cuántos",
        "precision": "precisión",
        "oposicion": "oposición",
        "companero": "compañero",
        "companeros": "compañeros",
        "intencion": "intención",
        "definicion": "definición",
        "homogenea": "homogénea",
        "homogeneas": "homogéneas",
        "heterogenea": "heterogénea",
        "heterogeneas": "heterogéneas",
        "azucar": "azúcar",
        "eleccion": "elección",
        "funcion": "función",
        "reproduccion": "reproducción",
        "justificacion": "justificación",
        "Organizacion": "Organización",
        "organizacion": "organización",
        "oracion": "oración",
        "conversacion": "conversación",
        "pronunciacion": "pronunciación",
        "conclusion": "conclusión",
        "evaluacion": "evaluación",
        "practica": "práctica",
        "rapida": "rápida",
        "tambien": "también",
        "habra": "habrá",
        "sera": "será",
        "tendra": "tendrá",
        "mas": "más",
        "facil": "fácil",
        "dificil": "difícil",
        "calculos": "cálculos",
        "calculo": "cálculo",
        "matematica": "matemática",
        "artistica": "artística",
        "ingles": "inglés",
        "Acompanhar": "Acompañar",
        "acompanhar": "acompañar",
    }
    texto_final = texto
    for original, reemplazo in reemplazos.items():
        texto_final = re.sub(rf"\b{original}\b", reemplazo, texto_final)
    return texto_final


def _normalizar_contenido_espanol(contenido: ContenidoPedagogico) -> ContenidoPedagogico:
    datos = contenido.model_dump()
    for clave, valor in list(datos.items()):
        if isinstance(valor, str):
            datos[clave] = _restaurar_espanol(valor)
        elif isinstance(valor, list):
            datos[clave] = [
                _restaurar_espanol(item) if isinstance(item, str) else item
                for item in valor
            ]
    return ContenidoPedagogico.model_validate(datos)


def _sin_acentos_basico(texto: str) -> str:
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }
    resultado = texto.lower()
    for original, reemplazo in reemplazos.items():
        resultado = resultado.replace(original, reemplazo)
    return resultado


def _corregir_texto_docente(texto: str) -> str:
    correcciones = {
        "uan": "una",
        "cclase": "clase",
        "clas ": "clase ",
        "matematica": "matematica",
        "multiplicar": "multiplicar",
        "inlges": "ingles",
        "ingels": "ingles",
        "caulquiera": "cualquiera",
    }
    texto_corregido = texto
    for original, reemplazo in correcciones.items():
        texto_corregido = re.sub(
            rf"\b{re.escape(original)}\b",
            reemplazo,
            texto_corregido,
            flags=re.IGNORECASE,
        )
    return texto_corregido


def _extraer_duracion_desde_prompt(prompt_original: str, duracion_actual: int) -> int:
    coincidencia = re.search(r"\b(3|5|8|15)\s*(min|minutos)\b", prompt_original, flags=re.IGNORECASE)
    if coincidencia:
        return int(coincidencia.group(1))
    return duracion_actual


def _es_pedido_generico(texto: str) -> bool:
    texto_limpio = _normalizar_espacios(texto).lower()
    texto_limpio = re.sub(r"\b(3|5|8|15)\s*(min|minutos)\b", "", texto_limpio)
    texto_limpio = re.sub(
        r"\b(crea|crear|genera|generar|arma|armar|clase|actividad|una|un|de|sobre|para|en|con)\b",
        "",
        texto_limpio,
    )
    return len(_normalizar_espacios(texto_limpio)) < 5


def _limpiar_destinatario_en_tema(texto: str) -> str:
    patrones = [
        r"\bpara\s+(nivel\s+)?primaria\b.*$",
        r"\bpara\s+ni(?:n|ñ)os?\s+de\s+\d+\s+a(?:n|ñ)os?\b.*$",
        r"\bpara\s+chicos?\s+de\s+\d+\s+a(?:n|ñ)os?\b.*$",
        r"\bpara\s+\d+\s+a(?:n|ñ)os?\b.*$",
        r"\bpara\s+(primer|segundo|tercer|cuarto|quinto|sexto|septimo|séptimo)\s+grado\b.*$",
        r"\bde\s+(primer|segundo|tercer|cuarto|quinto|sexto|septimo|séptimo)\s+grado\b.*$",
        r"\bpara\s+grado\s+\d+\b.*$",
    ]
    texto_limpio = texto
    for patron in patrones:
        texto_limpio = re.sub(patron, "", texto_limpio, flags=re.IGNORECASE).strip(" .")
    return _normalizar_espacios(texto_limpio)


def _extraer_tema_desde_prompt(prompt_original: str, materia: str) -> str:
    """
    Convierte pedidos largos o plantillas encadenadas en un tema usable.

    En modo local no queremos repetir literalmente "Crea una clase..." en cada
    parrafo. Esta funcion intenta quedarse con el nucleo pedagogico del pedido.
    """
    texto = _normalizar_espacios(_corregir_texto_docente(prompt_original))
    if not texto:
        return materia or "la clase"

    patrones_inicio = [
        r"^necesito\s+",
        r"^quiero\s+",
        r"^hacer\s+",
        r"^armar\s+",
        r"^genera(?:r)?\s+",
        r"^crea una clase con evaluacion corta sobre\s+",
        r"^crea una clase clara y breve sobre\s+",
        r"^crea una clase de practica guiada sobre\s+",
        r"^crea(?:r)? una clase de\s+(3|5|8|15)\s*(min|minutos)\s+sobre\s+",
        r"^crea(?:r)? una clase de\s+(3|5|8|15)\s*(min|minutos)\s+de\s+",
        r"^crea una clase completa sobre\s+",
        r"^crea una clase de\s+",
        r"^crear una clase de\s+",
        r"^crea una clase sobre\s+",
        r"^crear una clase sobre\s+",
        r"^una clase de\s+",
        r"^una clase sobre\s+",
        r"^clase de\s+",
        r"^sobre\s+",
        r"^clase sobre\s+",
        r"^tema random sobre\s+",
        r"^tema al azar sobre\s+",
        r"^tema cualquiera sobre\s+",
    ]

    anterior = None
    while anterior != texto:
        anterior = texto
        for patron in patrones_inicio:
            texto = re.sub(patron, "", texto, flags=re.IGNORECASE).strip(" .")

    cortes = [
        " Inclui ",
        " Incluye ",
        " Agrega ",
        " Agregar ",
        " Necesito ",
        " Explicar con ",
        " Incluir ",
    ]
    for corte in cortes:
        posicion = texto.lower().find(corte.lower())
        if posicion > 0:
            texto = texto[:posicion]

    texto = _normalizar_espacios(texto)
    texto = re.sub(r"\b(3|5|8|15)\s*(min|minutos)\b", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b(con\s+)?evaluacion\s+corta\b", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b(practica\s+guiada|explicacion\s+rapida|clara\s+y\s+breve)\b", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bpara\s+(explicar|trabajar|ensenar|enseñar)(\s+con\s+ejemplos)?\b.*$", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b(para|con|sobre|de)\s*$", "", texto, flags=re.IGNORECASE)
    texto = _limpiar_destinatario_en_tema(texto)
    texto = _normalizar_espacios(texto)
    if _es_pedido_generico(texto):
        if materia.lower().startswith("mat"):
            return "resolucion de problemas matematicos"
        return f"tema de {materia}"

    if len(texto) > 90:
        texto = texto[:90].rsplit(" ", 1)[0].strip(" .")

    return texto or materia or "la clase"


def _tema_en_frase(tema: str) -> str:
    tema_limpio = _normalizar_espacios(tema)
    if tema_limpio.lower().startswith("el "):
        return "del " + tema_limpio[3:]
    if tema_limpio.lower().startswith("la "):
        return "de " + tema_limpio
    if " y " in tema_limpio or tema_limpio.lower().endswith("s"):
        return "sobre " + tema_limpio
    return "de " + tema_limpio


def _es_tema_tablas(prompt_original: str, tema: str) -> bool:
    texto = f"{prompt_original} {tema}".lower()
    return "tabla" in texto or "multiplica" in texto


def _es_tema_fracciones(prompt_original: str, tema: str) -> bool:
    texto = f"{prompt_original} {tema}".lower()
    return "fraccion" in texto or "fracciones" in texto


def _normalizar_clave_materia(materia: str) -> str | None:
    materia_limpia = _normalizar_espacios(_sin_acentos_basico(materia))
    return ALIAS_MATERIAS.get(materia_limpia)


def _clave_materia(materia: str, prompt_original: str) -> str:
    materia_normalizada = _normalizar_clave_materia(materia)
    if materia_normalizada:
        return materia_normalizada

    texto = f"{materia} {prompt_original}".lower()
    if (
        "futbol" in texto
        or "fútbol" in texto
        or "deporte" in texto
        or "pases" in texto
        or "tiros" in texto
        or "educacion fisica" in texto
        or "educación física" in texto
    ):
        return "educacion fisica"
    if "natural" in texto or "biologia" in texto or "cuerpo humano" in texto or "ambiente" in texto:
        return "ciencias naturales"
    if "social" in texto or "historia" in texto or "geografia" in texto or "mapa" in texto:
        return "ciencias sociales"
    if "lengua" in texto or "literatura" in texto or "cuento" in texto or "lectura" in texto:
        return "lengua"
    if "ingles" in texto or "inglés" in texto or "english" in texto:
        return "ingles"
    if "artistica" in texto or "artística" in texto or "arte" in texto or "musica" in texto:
        return "educacion artistica"
    if "matemat" in texto or "numero" in texto or "calculo" in texto or "tabla" in texto or "fraccion" in texto:
        return "matematica"
    return "matematica"


def _perfil_materia(materia: str, prompt_original: str) -> dict:
    return PERFILES_MATERIA.get(_clave_materia(materia, prompt_original), PERFILES_MATERIA["matematica"])


def _nombre_materia_visible(materia: str, prompt_original: str) -> str:
    nombres = {
        "matematica": "Matemática",
        "lengua": "Lengua",
        "ciencias naturales": "Ciencias Naturales",
        "ciencias sociales": "Ciencias Sociales",
        "ingles": "Inglés",
        "educacion artistica": "Educación Artística",
        "educacion fisica": "Educación Física",
    }
    return nombres.get(_clave_materia(materia, prompt_original), materia or "Clase")


def _consulta_wikipedia(solicitud: SolicitudCrearClase, tema: str) -> str:
    if _es_pedido_generico(solicitud.prompt_original):
        return ""
    materia = _nombre_materia_visible(solicitud.materia, solicitud.prompt_original)
    texto = _sin_acentos_basico(tema)
    if "mezcla" in texto and ("homogene" in texto or "heterogene" in texto):
        return "mezcla homogénea mezcla heterogénea"
    if "planta" in texto or "raiz" in texto or "tallo" in texto or "hoja" in texto:
        return "partes de la planta raíz tallo hojas flor"
    if "vertebrado" in texto or "invertebrado" in texto:
        return "animal vertebrado animal invertebrado"
    if "colonial" in texto:
        return "época colonial vida cotidiana"
    return _normalizar_espacios(f"{tema} {materia}")


def _raiz_relevancia(palabra: str) -> str:
    palabra = _sin_acentos_basico(palabra)
    for sufijo in ["ciones", "cion", "es", "s"]:
        if len(palabra) > len(sufijo) + 3 and palabra.endswith(sufijo):
            return palabra[: -len(sufijo)]
    return palabra


def _terminos_relevantes(consulta: str) -> list[str]:
    ignorar = {
        "para",
        "con",
        "sobre",
        "clase",
        "primaria",
        "grado",
        "ninos",
        "niños",
        "anos",
        "años",
        "tema",
        "educacion",
        "fisica",
        "ciencias",
        "naturales",
        "sociales",
        "lengua",
        "ingles",
        "matematica",
    }
    terminos = []
    for palabra in re.findall(r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+", consulta):
        palabra_limpia = _sin_acentos_basico(palabra)
        if len(palabra_limpia) < 4 or palabra_limpia in ignorar:
            continue
        raiz = _raiz_relevancia(palabra_limpia)
        if raiz not in terminos:
            terminos.append(raiz)
    return terminos


def _contexto_wikipedia_relevante(consulta: str, titulo: str, extracto: str) -> bool:
    terminos = _terminos_relevantes(consulta)
    if not terminos:
        return False
    texto = _sin_acentos_basico(f"{titulo} {extracto}")
    encontrados = [termino for termino in terminos if termino in texto]
    if "homogene" in terminos and "heterogene" in terminos:
        return "homogene" in encontrados and "heterogene" in encontrados
    if len(terminos) >= 3:
        return len(encontrados) >= 2
    return bool(encontrados)


def _puntuar_contexto_web(consulta: str, titulo: str, extracto: str) -> int:
    terminos = _terminos_relevantes(consulta)
    texto_titulo = _sin_acentos_basico(titulo)
    texto_extracto = _sin_acentos_basico(extracto)
    puntaje = 0
    for termino in terminos:
        if termino in texto_titulo:
            puntaje += 3
        if termino in texto_extracto:
            puntaje += 1
    penalizadas = ["desambiguacion", "apellido", "album", "pelicula", "cancion"]
    if any(palabra in texto_titulo for palabra in penalizadas):
        puntaje -= 3
    return puntaje


def _recortar_oracion(texto: str, maximo: int = 230) -> str:
    texto_limpio = _normalizar_espacios(texto)
    if len(texto_limpio) <= maximo:
        return texto_limpio
    return texto_limpio[:maximo].rsplit(" ", 1)[0].strip(" ,;") + "."


def _oraciones_contexto(resumen: str, cantidad: int = 3) -> list[str]:
    partes = re.split(r"(?<=[.!?])\s+", _normalizar_espacios(resumen))
    oraciones = []
    for parte in partes:
        parte = parte.strip()
        if len(parte) < 35:
            continue
        if parte not in oraciones:
            oraciones.append(_recortar_oracion(parte))
        if len(oraciones) >= cantidad:
            break
    return oraciones


async def _buscar_contexto_wikipedia(consulta: str) -> dict | None:
    if not consulta:
        return None

    params_busqueda = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": consulta,
        "srlimit": 5,
        "origin": "*",
    }
    try:
        async with httpx.AsyncClient(timeout=12, headers=WIKIPEDIA_HEADERS) as cliente:
            respuesta = await cliente.get(WIKIPEDIA_API_URL, params=params_busqueda)
            respuesta.raise_for_status()
            resultados = (respuesta.json().get("query") or {}).get("search") or []
            if not resultados:
                return None

            mejor_contexto = None
            mejor_puntaje = 0

            for resultado in resultados:
                titulo = resultado.get("title")
                if not titulo:
                    continue
                snippet = re.sub("<.*?>", " ", str(resultado.get("snippet") or ""))
                if not _contexto_wikipedia_relevante(consulta, titulo, snippet):
                    continue

                params_extracto = {
                    "action": "query",
                    "format": "json",
                    "prop": "extracts|info",
                    "exintro": "1",
                    "explaintext": "1",
                    "inprop": "url",
                    "titles": titulo,
                    "origin": "*",
                }
                respuesta_extracto = await cliente.get(WIKIPEDIA_API_URL, params=params_extracto)
                respuesta_extracto.raise_for_status()
                paginas = (respuesta_extracto.json().get("query") or {}).get("pages") or {}
                pagina = next(iter(paginas.values()), {})
                extracto = _normalizar_espacios(pagina.get("extract", ""))
                if not extracto:
                    continue
                titulo_final = pagina.get("title") or titulo
                puntaje = _puntuar_contexto_web(consulta, titulo_final, extracto)
                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_contexto = {
                        "titulo": titulo_final,
                        "resumen": extracto,
                        "url": pagina.get("fullurl"),
                        "puntaje": puntaje,
                    }

            if not mejor_contexto or not _contexto_wikipedia_relevante(
                consulta,
                mejor_contexto["titulo"],
                mejor_contexto["resumen"],
            ):
                print(
                    "[servicio_contenido] Wikipedia devolvio un resultado poco "
                    f"relevante para '{consulta}'; se descarta."
                )
                return None
            extracto = mejor_contexto["resumen"]
            if len(extracto) > 650:
                extracto = extracto[:650].rsplit(" ", 1)[0].strip() + "."
            mejor_contexto["resumen"] = extracto
            mejor_contexto["ideas"] = _oraciones_contexto(extracto)
            return mejor_contexto
    except (httpx.HTTPError, ValueError) as error:
        print(
            "[servicio_contenido] Wikipedia no disponible; "
            f"usando solo generador local. Detalle: {error}"
        )
        return None


def _aplicar_contexto_web(
    contenido: ContenidoPedagogico,
    contexto: dict | None,
) -> ContenidoPedagogico:
    if not contexto:
        return contenido

    datos = contenido.model_dump()
    resumen = contexto.get("resumen", "")
    titulo = contexto.get("titulo", "")
    url = contexto.get("url")
    ideas = contexto.get("ideas") or _oraciones_contexto(resumen)
    idea_principal = ideas[0] if ideas else resumen

    datos["explicacion"] = (
        datos["explicacion"].rstrip()
        + "\n\nFuente abierta consultada para enriquecer la clase: "
        + _recortar_oracion(idea_principal, 420)
    )
    ejemplos_web = [
        f"Idea de fuente abierta: {idea}"
        for idea in ideas[:2]
    ]
    datos["ejemplos"] = (datos.get("ejemplos") or [])[:3] + ejemplos_web + [
        f"Trabajo con fuente: leer el resumen de {titulo}, subrayar tres palabras clave y explicar como se conectan con la actividad."
    ]
    datos["preguntas"] = (datos.get("preguntas") or [])[:4] + [
        f"Que dato de la fuente sobre {titulo} ayuda a entender mejor el tema?",
        "Que ejemplo propio podrias armar usando esa informacion?",
    ]
    datos["cuestionario"] = (datos.get("cuestionario") or [])[:4] + [
        "Escribe una idea tomada de la fuente abierta y relacionala con el ejemplo trabajado.",
        "Anota una palabra clave de la fuente, su significado y una oracion propia.",
    ]
    datos["tarea_hogar"] = (
        str(datos.get("tarea_hogar") or "").rstrip()
        + f" Ademas, revisar la fuente sugerida sobre {titulo} y copiar una idea que sirva para explicar mejor el tema."
    )
    fuente = f" Fuente sugerida: {url}" if url else ""
    datos["resumen"] = datos["resumen"] + fuente
    return _normalizar_contenido_espanol(ContenidoPedagogico.model_validate(datos))


def _generar_contenido_tablas(
    materia: str,
    publico: str,
    duracion: int,
    rango: str = "1 al 9",
) -> ContenidoPedagogico:
    return ContenidoPedagogico(
        titulo=f"{materia}: tablas de multiplicar del {rango}",
        objetivo=(
            f"Que los estudiantes de {publico} comprendan que multiplicar es sumar "
            "grupos iguales, reconozcan patrones en las tablas y resuelvan calculos "
            "simples usando estrategias de memoria y razonamiento."
        ),
        introduccion=(
            f"Inicio de {min(2, duracion)} minutos: preguntar 'Si tengo 3 bolsas con "
            "4 caramelos en cada una, cuantos caramelos hay en total?'. Escribir "
            "4 + 4 + 4 = 12 y mostrar que tambien se puede pensar como 3 x 4 = 12. "
            "Presentar la clase como una busqueda de patrones, no como una lista para memorizar."
        ),
        explicacion=(
            "La multiplicacion sirve para contar grupos iguales mas rapido. En las "
            "tablas del 1 al 9 hay patrones que ayudan: la tabla del 2 avanza de dos "
            "en dos, la del 5 termina en 0 o 5, la del 9 tiene cifras que se compensan "
            "(9, 18, 27, 36) y cambiar el orden no cambia el resultado: 3 x 4 da lo "
            "mismo que 4 x 3. Trabajar primero con dibujos o puntos, luego con sumas "
            "repetidas y finalmente con el calculo multiplicativo."
        ),
        ejemplos=[
            "Tabla del 2: 2 x 6 significa 6 grupos de 2. Se puede resolver como 2 + 2 + 2 + 2 + 2 + 2 = 12.",
            "Tabla del 5: 5 x 7 = 35. Los resultados alternan terminacion 5 y 0: 5, 10, 15, 20, 25...",
            "Tabla del 9: 9 x 4 = 36. Una estrategia es pensar 10 x 4 = 40 y restar 4: queda 36.",
            "Propiedad conmutativa: si se sabe 6 x 8 = 48, tambien se sabe 8 x 6 = 48.",
        ],
        actividad=(
            "Actividad guiada: entregar o dibujar una grilla del 1 al 9. Primero, "
            "cada estudiante completa las tablas del 2, 5 y 10 como entrada en calor. "
            "Luego elige tres resultados dificiles y escribe una estrategia para cada uno "
            "(suma repetida, doble, mitad, tabla cercana o 10 veces menos un grupo). "
            "Cierre rapido: en parejas se preguntan cinco calculos y explican uno en voz alta."
        ),
        preguntas=[
            "Que significa 4 x 6 usando grupos iguales?",
            "Como podrias resolver 9 x 7 sin repetir la tabla de memoria?",
            "Por que 3 x 8 y 8 x 3 dan el mismo resultado?",
            "Que tabla te resulta mas facil y que patron encontraste?",
            "Que calculo te cuesta mas y que estrategia podrias usar?",
        ],
        cuestionario=[
            "Completa: 6 x 4 = ____ y explica con una suma repetida.",
            "Resuelve 9 x 5 usando la estrategia de 10 x 5 menos 5.",
            "Une los calculos equivalentes: 3 x 7, 8 x 2, 7 x 3, 2 x 8.",
            "Escribe un problema cotidiano que se resuelva con 4 x 6.",
            "Marca el error: '5 x 8 = 45'. Corrige y explica.",
        ],
        tarea_hogar=(
            "Tarea para el hogar: elegir tres objetos de casa que formen grupos "
            "iguales (por ejemplo paquetes, filas, vasos o figuritas), escribir la "
            "multiplicacion que representan y resolverla. Traer tambien dos calculos "
            "de las tablas del 1 al 9 que quieras practicar."
        ),
        resumen=(
            "Hoy trabajamos las tablas del 1 al 9 como una forma rapida de contar "
            "grupos iguales. Vimos patrones, estrategias para calculos dificiles y "
            "la idea de que multiplicar no es solo memorizar: tambien es razonar."
        ),
    )


def _generar_contenido_fracciones(
    materia: str,
    publico: str,
    duracion: int,
) -> ContenidoPedagogico:
    return ContenidoPedagogico(
        titulo=f"{materia}: fracciones con ejemplos cotidianos",
        objetivo=(
            f"Que los estudiantes de {publico} comprendan que una fraccion representa "
            "una parte de un entero o de un grupo, puedan leer fracciones simples y "
            "compararlas usando dibujos o situaciones concretas."
        ),
        introduccion=(
            f"Inicio de {min(2, duracion)} minutos: mostrar una pizza, una barra de "
            "chocolate o una hoja dividida. Preguntar: 'Si compartimos esto entre "
            "4 personas y tomamos 1 parte, como lo escribimos?'. Presentar 1/4 como "
            "una forma de nombrar una parte de cuatro partes iguales."
        ),
        explicacion=(
            "Una fraccion tiene numerador y denominador. El denominador indica en "
            "cuantas partes iguales se divide el entero; el numerador indica cuantas "
            "partes tomamos. Para entenderlas conviene dibujar, sombrear y comparar. "
            "Por ejemplo, 1/2 es una de dos partes iguales, y 2/4 tambien representa "
            "la mitad si las cuatro partes son iguales."
        ),
        ejemplos=[
            "Si una pizza se divide en 4 partes iguales y comemos 1, comimos 1/4.",
            "Si una barra de chocolate tiene 8 cuadraditos y comemos 4, comimos 4/8, que equivale a la mitad.",
            "Comparacion: 1/2 es mayor que 1/4 porque una mitad es mas grande que un cuarto del mismo entero.",
            "En una bolsa con 10 figuritas, si 3 son repetidas, 3/10 de la bolsa son repetidas.",
        ],
        actividad=(
            "Actividad: dibujar tres rectangulos iguales. Dividir el primero en 2, "
            "el segundo en 4 y el tercero en 8 partes iguales. Sombrear 1/2, 2/4 y "
            "4/8. Comparar los dibujos y escribir que tienen en comun."
        ),
        preguntas=[
            "Que indica el denominador de una fraccion?",
            "Que indica el numerador?",
            "Por que las partes deben ser iguales?",
            "Cual es mayor: 1/2 o 1/4? Explica con un dibujo.",
            "Que fraccion representa comer 3 de 6 porciones iguales?",
        ],
        cuestionario=[
            "Dibuja un entero dividido en 4 partes iguales y sombrea 3/4.",
            "Escribe la fraccion: 2 partes tomadas de 5 partes iguales.",
            "Marca cual es mayor: 1/3 o 1/6, y explica.",
            "Completa: en 2/8, el denominador es ____ y el numerador es ____.",
            "Inventa un ejemplo de fraccion con comida, juguetes o figuritas.",
        ],
        tarea_hogar=(
            "Tarea para el hogar: buscar una situacion de casa donde aparezcan "
            "fracciones (comida, vasos, piezas, figuritas). Dibujarla, escribir la "
            "fraccion y explicar que representa el numerador y el denominador."
        ),
        resumen=(
            "Hoy aprendimos que una fraccion nombra partes iguales de un entero o "
            "de un grupo. Practicamos numerador, denominador, dibujos y comparaciones "
            "simples para entenderlas mejor."
        ),
    )


def _ejemplos_por_materia(clave_materia: str, tema: str, perfil: dict) -> list[str]:
    tema_limpio = tema[:1].lower() + tema[1:]
    if clave_materia == "educacion fisica":
        return [
            f"Demostracion: practicar {tema_limpio} primero sin oposicion, cuidando postura, mirada y control del movimiento.",
            "Ejercicio 1: en parejas, realizar 10 intentos suaves y contar cuantos salen con precision.",
            "Ejercicio 2: armar estaciones de practica con conos o marcas y rotar cada 3 minutos.",
            "Juego aplicado: usar la habilidad en un partido reducido y detener una jugada para explicar una decision.",
        ]
    if clave_materia == "ciencias naturales":
        return [
            f"Observacion guiada: mirar un objeto, imagen o experiencia relacionada con {tema_limpio} y nombrar tres caracteristicas.",
            "Ejemplo cotidiano: conectar el tema con algo que los estudiantes puedan ver en casa, la escuela o el barrio.",
            "Registro: completar un cuadro con 'veo', 'pienso' y 'me pregunto'.",
            "Explicacion cientifica simple: usar dos palabras clave del tema en una conclusion breve.",
        ]
    if clave_materia == "ciencias sociales":
        return [
            f"Ubicacion: marcar en un mapa, linea de tiempo o cuadro donde aparece {tema_limpio}.",
            "Comparacion: analizar que cambia y que permanece entre dos momentos, lugares o grupos.",
            "Fuente breve: observar una imagen o texto y responder quien participa, que ocurre y por que importa.",
            "Relacion: unir una causa con una consecuencia usando una frase propia.",
        ]
    if clave_materia == "lengua":
        return [
            f"Lectura breve: leer un texto corto vinculado con {tema_limpio} y subrayar dos ideas importantes.",
            "Vocabulario: elegir tres palabras clave, explicar su significado y usarlas en una oracion.",
            "Produccion: escribir un parrafo de 5 lineas con inicio, desarrollo y cierre.",
            "Revision: intercambiar producciones y mejorar una frase para que sea mas clara.",
        ]
    if clave_materia == "ingles":
        return [
            f"Vocabulary: presentar 5 palabras o frases sobre {tema_limpio} con imagen o gesto.",
            "Model sentence: practicar una estructura simple, por ejemplo 'I can...', 'This is...' o 'My name is...'.",
            "Pair practice: repetir en parejas una mini conversacion de dos turnos.",
            "Exit ticket: cada estudiante dice o escribe una frase corta usando el vocabulario.",
        ]
    if clave_materia == "educacion artistica":
        return [
            f"Observacion: mirar una obra, sonido o produccion relacionada con {tema_limpio} y describir colores, formas, ritmo o textura.",
            "Exploracion: probar dos materiales o recursos expresivos y comparar el efecto que producen.",
            "Produccion: crear una pieza breve siguiendo una consigna clara.",
            "Apreciacion: explicar una decision propia usando vocabulario de la materia.",
        ]
    return [
        f"Ejemplo 1: usar {perfil['situacion']} para presentar {tema_limpio} con lenguaje simple.",
        f"Ejemplo 2: resolver un caso guiado aplicando esta estrategia: {perfil['estrategia']}.",
        "Ejemplo 3: mostrar una produccion o respuesta incompleta y mejorarla entre todos.",
        "Ejemplo 4: pedir a un estudiante que explique con sus palabras y a otro que agregue una pregunta.",
    ]


def _detalles_tema(clave_materia: str, tema: str, perfil: dict) -> dict:
    tema_limpio = tema[:1].lower() + tema[1:]
    texto = _sin_acentos_basico(tema)

    if "futbol" in texto or "pase" in texto or "tiro" in texto:
        return {
            "definicion": (
                "En futbol, un pase sirve para entregar la pelota a un companero "
                "con control, y un tiro busca enviar la pelota hacia el arco. "
                "La diferencia central es la intencion: conservar y avanzar con "
                "el pase, o finalizar una jugada con el tiro."
            ),
            "pasos": [
                "mirar antes de recibir para elegir a quien pasar",
                "usar el borde interno del pie para pases cortos y precisos",
                "acompanar la pelota con el cuerpo orientado al objetivo",
                "en el tiro, apoyar el pie al costado de la pelota y terminar el movimiento hacia el arco",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: dos estudiantes se ubican a cinco metros. El primero "
                "hace un pase con borde interno al pie del companero; el segundo controla "
                "y devuelve. Luego repiten apuntando a un cono como si fuera el arco."
            ),
            "practica": (
                "Circuito de practica: estacion 1 pases cortos entre parejas; estacion 2 "
                "pase y desplazamiento; estacion 3 tiro suave a un arco marcado con conos. "
                "Cada estacion dura dos minutos y se evalua precision, no fuerza."
            ),
            "producto": "una mejora observable en la precision del pase o tiro y una explicacion breve de la decision tomada",
        }

    if "planta" in texto or "raiz" in texto or "tallo" in texto or "hoja" in texto or "flor" in texto:
        return {
            "definicion": (
                "Una planta es un ser vivo que necesita agua, luz, aire y nutrientes. "
                "Sus partes cumplen funciones distintas: la raiz absorbe agua, el tallo "
                "sostiene y transporta, las hojas fabrican alimento y la flor participa "
                "en la reproduccion."
            ),
            "pasos": [
                "observar una imagen o planta real",
                "nombrar cada parte visible",
                "relacionar cada parte con su funcion",
                "dibujar una planta y rotular raiz, tallo, hojas y flor",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: mostrar una planta en maceta. Preguntar que pasaria "
                "si no tuviera raiz, luego explicar que no podria absorber agua ni "
                "sostenerse bien en la tierra."
            ),
            "practica": (
                "Actividad guiada: entregar una imagen de planta sin nombres. Los "
                "estudiantes completan las etiquetas y escriben una funcion para cada parte."
            ),
            "producto": "un dibujo rotulado con funciones simples de cada parte",
        }

    if "vertebrado" in texto or "invertebrado" in texto:
        return {
            "definicion": (
                "Los animales vertebrados tienen columna vertebral o esqueleto interno; "
                "los invertebrados no tienen columna vertebral. Esta diferencia ayuda "
                "a clasificarlos y comparar como se mueven, se protegen y viven."
            ),
            "pasos": [
                "mirar imagenes de animales conocidos",
                "preguntar si tienen columna vertebral",
                "separarlos en dos grupos",
                "justificar la clasificacion con una caracteristica observable",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: perro y pez son vertebrados porque tienen columna; "
                "mariposa y caracol son invertebrados porque no tienen columna vertebral."
            ),
            "practica": (
                "Clasificacion en tarjetas: cada grupo recibe seis animales, arma dos "
                "columnas y explica una decision al resto de la clase."
            ),
            "producto": "un cuadro comparativo con ejemplos y una justificacion",
        }

    if "mezcla" in texto and ("homogene" in texto or "heterogene" in texto):
        return {
            "definicion": (
                "Una mezcla homogenea se ve uniforme, como agua con sal disuelta. "
                "Una mezcla heterogenea permite distinguir sus componentes, como agua "
                "con arena o una ensalada."
            ),
            "pasos": [
                "observar dos mezclas",
                "decidir si se distinguen sus componentes",
                "clasificar como homogenea o heterogenea",
                "explicar la decision con una frase",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: agua con azucar parece una sola sustancia cuando se "
                "disuelve, por eso es homogenea; agua con aceite muestra dos partes, "
                "por eso es heterogenea."
            ),
            "practica": (
                "Experiencia simple: comparar sal en agua, arroz con lentejas y agua "
                "con aceite. Registrar observacion, tipo de mezcla y justificacion."
            ),
            "producto": "una tabla de observacion con clasificacion y justificacion",
        }

    if "volcan" in texto:
        return {
            "definicion": (
                "Un volcan es una abertura de la corteza terrestre por donde pueden "
                "salir magma, gases y cenizas desde el interior de la Tierra. Cuando "
                "el magma llega a la superficie se llama lava."
            ),
            "pasos": [
                "ubicar las partes principales del volcan",
                "diferenciar magma, lava, gases y cenizas",
                "explicar que ocurre durante una erupcion",
                "relacionar el fenomeno con cambios en el relieve",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: dibujar un volcan en corte y senalar camara magmatica, "
                "chimenea, crater y lava. Luego explicar el recorrido del magma hasta salir."
            ),
            "practica": (
                "Actividad guiada: completar un esquema de volcan con nombres y escribir "
                "en tres pasos que pasa antes, durante y despues de una erupcion."
            ),
            "producto": "un esquema rotulado de volcan con una explicacion breve de la erupcion",
        }

    if "colonial" in texto or "epoca colonial" in texto:
        return {
            "definicion": (
                "La vida en la epoca colonial se organizaba de manera diferente a la "
                "actual: habia otros trabajos, transportes, viviendas, formas de comprar "
                "y grupos sociales con derechos desiguales."
            ),
            "pasos": [
                "ubicar la epoca colonial antes de la independencia",
                "observar una imagen o relato breve",
                "comparar vida cotidiana colonial y actual",
                "reconocer cambios y permanencias",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: comparar una pulperia colonial con un comercio actual. "
                "Preguntar que se vendia, quienes iban y como circulaban las noticias."
            ),
            "practica": (
                "Trabajo con fuente visual: mirar una escena colonial y completar: "
                "personas, objetos, trabajos, diferencias con la actualidad."
            ),
            "producto": "un cuadro de comparacion entre vida colonial y vida actual",
        }

    if "interrogacion" in texto or "exclamacion" in texto:
        return {
            "definicion": (
                "Los signos de interrogacion se usan para escribir preguntas. Los signos "
                "de exclamacion se usan para expresar sorpresa, alegria, enojo o una orden "
                "con fuerza. En espanol se colocan al abrir y al cerrar la oracion."
            ),
            "pasos": [
                "leer la oracion en voz alta",
                "decidir si pregunta o expresa emocion",
                "colocar signo de apertura",
                "colocar signo de cierre",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: 'Donde esta mi cuaderno' se transforma en "
                "'¿Donde esta mi cuaderno?'. 'Que lindo dia' se transforma en "
                "'¡Que lindo dia!'."
            ),
            "practica": (
                "Reescritura: entregar seis oraciones sin signos. Los estudiantes colocan "
                "interrogacion o exclamacion y leen una justificando la eleccion."
            ),
            "producto": "oraciones corregidas con signos de apertura y cierre",
        }

    if "porcentaje" in texto or "descuento" in texto:
        return {
            "definicion": (
                "Un porcentaje representa una parte de cada 100. En descuentos, indica "
                "cuanto se resta del precio original. Por ejemplo, 10% de 100 pesos son "
                "10 pesos."
            ),
            "pasos": [
                "identificar precio original",
                "calcular el porcentaje como parte de 100",
                "restar el descuento",
                "escribir precio final",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: una remera cuesta 2000 pesos y tiene 25% de descuento. "
                "25% de 2000 es 500, entonces el precio final es 1500 pesos."
            ),
            "practica": (
                "Simulacion de tienda: cada grupo recibe tres precios y tarjetas de "
                "descuento. Calculan descuento y precio final con procedimiento escrito."
            ),
            "producto": "tres calculos de descuento con procedimiento y precio final",
        }

    if clave_materia == "ingles" and ("color" in texto or "aula" in texto or "objet" in texto):
        return {
            "definicion": (
                "En ingles, los colores y objetos del aula sirven para describir lo que "
                "vemos: red pencil, blue book, green chair. La estructura simple es "
                "'It is a...' o 'This is a...'."
            ),
            "pasos": [
                "presentar vocabulario con imagen o gesto",
                "repetir pronunciacion",
                "unir color y objeto",
                "decir una frase corta",
            ],
            "ejemplo_modelado": (
                "Ejemplo modelado: mostrar un lapiz rojo y decir 'This is a red pencil'. "
                "Luego mostrar un libro azul y decir 'It is a blue book'."
            ),
            "practica": (
                "Busqueda en el aula: cada estudiante elige un objeto, nombra color y "
                "objeto en ingles y arma una frase con ayuda del modelo."
            ),
            "producto": "tres frases cortas en ingles con color y objeto",
        }

    return {
        "definicion": (
            f"{tema_limpio} es el contenido central de la clase. Para trabajarlo, "
            "conviene presentarlo como una idea clara, mostrar un caso concreto, "
            "practicar con una consigna breve y cerrar con una explicacion en palabras propias."
        ),
        "pasos": [
            "nombrar la idea principal",
            "mirar un ejemplo concreto",
            "resolver una consigna guiada",
            "explicar que se aprendio con palabras propias",
        ],
        "ejemplo_modelado": (
            f"Ejemplo modelado: el docente presenta una situacion breve sobre {tema_limpio}, "
            "piensa en voz alta como resolverla y marca las palabras clave que ayudan "
            "a entender el tema."
        ),
        "practica": (
            "Practica guiada: los estudiantes resuelven una version parecida del ejemplo, "
            "primero con ayuda y luego de manera mas autonoma."
        ),
        "producto": perfil["producto"],
    }


def _actividad_por_materia(clave_materia: str, perfil: dict, detalle: dict | None = None) -> str:
    if detalle:
        return (
            f"Actividad principal: {detalle['practica']} "
            "Organizacion sugerida: 2 minutos de explicacion, 3 minutos de practica "
            "guiada, 2 minutos de produccion y 1 minuto de cierre oral."
        )
    if clave_materia == "educacion fisica":
        return (
            "Actividad principal: entrada en calor breve, demostracion tecnica, "
            "practica por estaciones y juego reducido. El docente observa una "
            "habilidad concreta, da feedback corto y cierra con una pregunta sobre "
            "la regla, la decision o la estrategia usada."
        )
    if clave_materia == "ingles":
        return (
            "Actividad principal: presentar vocabulario con apoyo visual, repetir "
            "pronunciacion, practicar una frase modelo en parejas y cerrar con una "
            "mini produccion oral o escrita individual."
        )
    return (
        f"Actividad principal: {perfil['actividad']}. Primero se hace un ejemplo "
        "entre todos, luego trabajan en parejas o pequenos grupos y finalmente "
        f"cada grupo entrega {perfil['producto']}. Cerrar revisando una produccion "
        "correcta y una que necesite mejora."
    )


def _generar_contenido_local(solicitud: SolicitudCrearClase) -> ContenidoPedagogico:
    """Generador local para demo cuando no hay API key configurada."""
    clave_materia = _clave_materia(solicitud.materia, solicitud.prompt_original)
    materia = _nombre_materia_visible(solicitud.materia.strip(), solicitud.prompt_original)
    tema = _extraer_tema_desde_prompt(solicitud.prompt_original, materia)
    publico = solicitud.edad_publico.strip() or "estudiantes"
    duracion = _extraer_duracion_desde_prompt(solicitud.prompt_original, solicitud.duracion_minutos)
    tema_minuscula = tema[:1].lower() + tema[1:]
    tema_frase = _tema_en_frase(tema_minuscula)
    perfil = _perfil_materia(materia, solicitud.prompt_original)
    detalle = _detalles_tema(clave_materia, tema, perfil)
    ejemplos = [
        detalle["ejemplo_modelado"],
        *[f"Paso {indice + 1}: {paso}." for indice, paso in enumerate(detalle["pasos"])],
    ]
    actividad = _actividad_por_materia(clave_materia, perfil, detalle)

    if _es_tema_tablas(solicitud.prompt_original, tema):
        return _normalizar_contenido_espanol(
            _generar_contenido_tablas(materia, publico, duracion)
        )
    if _es_tema_fracciones(solicitud.prompt_original, tema):
        return _normalizar_contenido_espanol(
            _generar_contenido_fracciones(materia, publico, duracion)
        )

    return _normalizar_contenido_espanol(ContenidoPedagogico(
        titulo=f"{materia}: {tema[:55]}",
        objetivo=(
            f"Que los estudiantes de {publico} comprendan la idea central {tema_frase}, "
            f"la relacionen con {perfil['eje']} y produzcan "
            f"{perfil['producto']}."
        ),
        introduccion=(
            f"Inicio de la clase ({duracion} minutos en total): presentar una situacion "
            f"cercana vinculada con {perfil['situacion']}. Preguntar que saben sobre "
            f"{tema_minuscula}, anotar dos ideas previas en el pizarron y anticipar "
            "que la clase tendra explicacion breve, ejemplo guiado, practica y cierre."
        ),
        explicacion=(
            f"{detalle['definicion']} "
            f"El foco de la materia sera {perfil['eje']}. "
            "Para que la clase no quede solo en una definicion, conviene trabajarla "
            "en cuatro momentos: observar o escuchar una situacion, identificar la "
            "idea importante, practicar con ayuda y explicar el resultado. "
            "Si aparecen dudas, volver al ejemplo y separar la consigna en pasos."
        ),
        ejemplos=ejemplos,
        actividad=actividad,
        preguntas=[
            f"Que significa {tema_minuscula} con tus propias palabras?",
            "Que observamos o usamos en el ejemplo guiado?",
            f"Como se relaciona con {perfil['eje']}?",
            f"Donde podrias encontrar algo parecido en {perfil['situacion']}?",
            "Que parte te resulto mas facil y cual necesitarias practicar mas?",
        ],
        cuestionario=[
            f"Explica en una oracion la idea principal de {tema_minuscula}.",
            f"Escribe un ejemplo concreto sobre {tema_minuscula} y justifica por que corresponde.",
            f"Ordena estos pasos de trabajo: {', '.join(detalle['pasos'][:3])}.",
            f"Produce {detalle['producto']} sobre el tema trabajado.",
            "Escribe una duda o una idea que quieras seguir practicando.",
        ],
        tarea_hogar=(
            f"Tarea para el hogar: buscar un ejemplo de {tema_minuscula} en casa o en "
            "el barrio, escribirlo en tres oraciones y traer una pregunta para "
            "compartir en la proxima clase."
        ),
        resumen=(
            f"Hoy trabajamos {tema_frase} a partir de una explicacion simple, un "
            "ejemplo modelado y una practica guiada. Lo importante es que cada "
            f"estudiante pueda reconocer la idea central, dar un ejemplo y producir "
            f"{detalle['producto']}."
        ),
    ))


def _extraer_texto_respuesta_openai(respuesta_json: dict) -> str:
    if respuesta_json.get("output_text"):
        return respuesta_json["output_text"]

    partes_texto = []
    for item in respuesta_json.get("output", []):
        for contenido in item.get("content", []):
            if contenido.get("type") in {"output_text", "text"}:
                partes_texto.append(contenido.get("text", ""))
    return "".join(partes_texto)


async def _generar_con_openai(
    solicitud: SolicitudCrearClase,
    api_key: str,
    modelo: str,
    url: str = OPENAI_RESPONSES_URL,
) -> ContenidoPedagogico:
    payload = {
        "model": modelo,
        "input": [
            {"role": "system", "content": construir_prompt_sistema()},
            {"role": "user", "content": _construir_prompt_usuario(solicitud)},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "contenido_pedagogico",
                "schema": _schema_contenido_pedagogico(),
                "strict": True,
            }
        },
        "max_output_tokens": 1800,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45) as cliente:
        respuesta = await cliente.post(
            url or OPENAI_RESPONSES_URL,
            headers=headers,
            json=payload,
        )
        respuesta.raise_for_status()

    texto = _extraer_texto_respuesta_openai(respuesta.json())
    datos = json.loads(_limpiar_json_modelo(texto))
    return ContenidoPedagogico.model_validate(datos)


def _extraer_texto_respuesta_chat(respuesta_json: dict) -> str:
    opciones = respuesta_json.get("choices") or []
    if not opciones:
        return ""
    mensaje = opciones[0].get("message") or {}
    contenido = mensaje.get("content") or ""
    if isinstance(contenido, list):
        partes = []
        for item in contenido:
            if isinstance(item, dict):
                partes.append(str(item.get("text") or item.get("content") or ""))
            else:
                partes.append(str(item))
        return "".join(partes)
    return str(contenido)


async def _generar_con_chat_compatible(
    solicitud: SolicitudCrearClase,
    api_key: str,
    modelo: str,
    url: str,
) -> ContenidoPedagogico:
    payload = {
        "model": modelo,
        "messages": [
            {
                "role": "system",
                "content": f"{construir_prompt_sistema()} {_instruccion_json_pedagogico()}",
            },
            {"role": "user", "content": _construir_prompt_usuario(solicitud)},
        ],
        "temperature": 0.35,
        "max_tokens": 2200,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as cliente:
        respuesta = await cliente.post(url, headers=headers, json=payload)
        respuesta.raise_for_status()

    texto = _extraer_texto_respuesta_chat(respuesta.json())
    datos = json.loads(_limpiar_json_modelo(texto))
    return ContenidoPedagogico.model_validate(datos)


def _proveedores_contenido(configuracion) -> list[dict]:
    proveedores = []
    if _valor_configurado(configuracion.ia_contenido_api_key):
        proveedores.append(
            {
                "nombre": "OpenAI",
                "tipo": "responses",
                "api_key": configuracion.ia_contenido_api_key,
                "modelo": configuracion.ia_contenido_modelo,
                "url": configuracion.ia_contenido_openai_url,
            }
        )
    if _valor_configurado(configuracion.ia_contenido_deepseek_api_key):
        proveedores.append(
            {
                "nombre": "DeepSeek",
                "tipo": "chat",
                "api_key": configuracion.ia_contenido_deepseek_api_key,
                "modelo": configuracion.ia_contenido_deepseek_modelo,
                "url": configuracion.ia_contenido_deepseek_url,
            }
        )
    if _valor_configurado(configuracion.ia_contenido_openrouter_api_key):
        proveedores.append(
            {
                "nombre": "OpenRouter",
                "tipo": "chat",
                "api_key": configuracion.ia_contenido_openrouter_api_key,
                "modelo": configuracion.ia_contenido_openrouter_modelo,
                "url": configuracion.ia_contenido_openrouter_url,
            }
        )
    if _valor_configurado(configuracion.ia_contenido_groq_api_key):
        proveedores.append(
            {
                "nombre": "Groq",
                "tipo": "chat",
                "api_key": configuracion.ia_contenido_groq_api_key,
                "modelo": configuracion.ia_contenido_groq_modelo,
                "url": configuracion.ia_contenido_groq_url,
            }
        )
    return proveedores


async def _generar_con_proveedor(
    solicitud: SolicitudCrearClase,
    proveedor: dict,
) -> ContenidoPedagogico:
    if proveedor["tipo"] == "responses":
        return await _generar_con_openai(
            solicitud,
            proveedor["api_key"],
            proveedor["modelo"],
            proveedor["url"],
        )
    return await _generar_con_chat_compatible(
        solicitud,
        proveedor["api_key"],
        proveedor["modelo"],
        proveedor["url"],
    )


async def generar_contenido_pedagogico(
    solicitud: SolicitudCrearClase,
) -> ContenidoPedagogico:
    """
    Genera el contenido pedagogico completo de una clase.
    """
    configuracion = obtener_configuracion()

    def _error_ia_no_disponible(mensaje: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"{mensaje}. La generacion local queda solo para modo demo; "
                "para crear clases vendibles hace falta credito/API de IA activa."
            ),
        )

    async def generar_local_con_web() -> ContenidoPedagogico:
        contenido_local = _generar_contenido_local(solicitud)
        tema = _extraer_tema_desde_prompt(solicitud.prompt_original, solicitud.materia)
        consulta = _consulta_wikipedia(solicitud, tema)
        contexto = await _buscar_contexto_wikipedia(consulta)
        return _aplicar_contexto_web(contenido_local, contexto)

    proveedores = _proveedores_contenido(configuracion)
    errores = []
    for proveedor in proveedores:
        try:
            contenido = await _generar_con_proveedor(solicitud, proveedor)
            return _normalizar_contenido_espanol(contenido)
        except httpx.HTTPStatusError as error:
            codigo = error.response.status_code
            detalle = error.response.text[:220].replace("\n", " ")
            errores.append(f"{proveedor['nombre']} HTTP {codigo}: {detalle}")
            print(
                f"[servicio_contenido] {proveedor['nombre']} no disponible "
                f"(HTTP {codigo}); probando siguiente proveedor."
            )
            continue
        except (httpx.RequestError, json.JSONDecodeError, ValueError) as error:
            errores.append(f"{proveedor['nombre']}: {error}")
            print(
                f"[servicio_contenido] Error con {proveedor['nombre']}; "
                "probando siguiente proveedor. "
                f"Detalle: {error}"
            )
            continue

    if proveedores and not configuracion.ia_contenido_fallback_local:
        detalle = " | ".join(errores[-3:]) if errores else "sin detalle"
        raise _error_ia_no_disponible(
            "Ningun proveedor de IA pudo generar la clase "
            f"({detalle})"
        )

    if proveedores:
        print(
            "[servicio_contenido] Ningun proveedor de IA respondio; "
            "usando generador local porque IA_CONTENIDO_FALLBACK_LOCAL=true."
        )

    return await generar_local_con_web()
