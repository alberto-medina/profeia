"""
Servicio de generacion multimedia: voz (TTS), imagenes y slides.
"""

import base64
import re
import unicodedata
from io import BytesIO
from uuid import UUID

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.core.config import obtener_configuracion
from app.models.recurso import SolicitudGenerarImagenes, SolicitudGenerarVoz
from app.services.servicio_storage import guardar_recurso_docente


OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt/{prompt}"
HUGGINGFACE_INFERENCE_URL = "https://router.huggingface.co/hf-inference/models/{modelo}"
WIKIMEDIA_HEADERS = {
    "User-Agent": "ProfeIA/0.1 educativo-local (contacto: desarrollo@profeia.local)"
}


def _valor_configurado(valor: str | None) -> bool:
    if not valor:
        return False
    return valor.strip() not in {"", "TU_API_KEY", "TU_ACCESS_TOKEN"}


def _construir_prompt_imagen(
    descripcion_visual: str,
    estilo: str | None,
    sugerencia_imagen: str | None = None,
) -> str:
    """
    Arma el prompt final para el modelo de imagen.

    Si sugerencia_imagen esta disponible (generada por la IA de contenido,
    que ya entendio el tema en profundidad), se usa como la descripcion
    principal de la escena: es mucho mas especifica que descripcion_visual
    generico (que suele ser solo el titulo/tema de la clase). De todas
    formas se mantiene la regla general de composicion como red de
    seguridad, por si la sugerencia no llego a cubrir bien el caso de
    multiples categorias a separar.
    """
    estilo_final = estilo or "ilustracion educativa clara, simple y amigable"
    escena = (sugerencia_imagen or "").strip() or descripcion_visual

    return (
        "Genera una imagen educativa para una clase escolar.\n\n"
        "REGLA DE COMPOSICION (muy importante, aplica a cualquier tema): "
        "si el tema involucra VARIOS elementos, categorias, tipos o etapas "
        "DISTINTAS que se estan comparando, clasificando o diferenciando "
        "entre si (por ejemplo: distintos tipos de relieve, distintos "
        "animales o grupos de animales, distintas etapas de un proceso, "
        "distintos objetos o conceptos), NO los mezcles todos juntos en una "
        "sola escena abarrotada tipo collage. En su lugar, organiza la "
        "imagen en zonas o secciones CLARAMENTE SEPARADAS entre si (por "
        "ejemplo en columnas, filas, o regiones bien delimitadas de la "
        "imagen), dejando espacio visual vacio entre cada seccion, de modo "
        "que cada elemento o categoria se vea como algo individual y "
        "distinguible, no fusionado con los demas.\n"
        "Si en cambio el tema es UN SOLO concepto, objeto o proceso (sin "
        "necesidad de comparar varias cosas distintas), mostralo con una "
        "unica escena central, clara y enfocada, sin necesidad de dividir "
        "la imagen en secciones.\n\n"
        "Ademas: debe ser clara, apta para estudiantes, SIN texto legible "
        "dentro de la imagen (nada de letras, palabras ni numeros escritos, "
        "ya que los modelos de imagen no los generan de forma legible), "
        "con buen contraste y composicion ordenada, sin elementos que se "
        "superpongan entre si de forma confusa.\n\n"
        f"Escena a ilustrar: {escena}.\n"
        f"Estilo visual: {estilo_final}."
    )


def _construir_prompt_imagen_simple(
    descripcion_visual: str,
    estilo: str | None,
    sugerencia_imagen: str | None = None,
) -> str:
    """
    Version corta del prompt, para modelos que no siguen bien instrucciones
    largas (como el que usa Pollinations). El prompt completo de
    _construir_prompt_imagen() esta pensado para modelos con buen seguimiento
    de instrucciones (OpenAI Images); con Pollinations, ese mismo prompt
    largo y lleno de reglas de composicion hace que el modelo ignore la
    escena pedida y devuelva imagenes genericas sin relacion con el tema.
    Una descripcion corta y directa de la escena si funciona bien.
    """
    estilo_final = estilo or "ilustracion educativa clara, simple y amigable"
    escena = (sugerencia_imagen or "").strip() or descripcion_visual
    return (
        f"Ilustracion educativa clara y simple sobre: {escena}. "
        f"Estilo: {estilo_final}, apta para estudiantes, sin texto ni letras."
    )


def _fuente(tamano: int, negrita: bool = False):
    nombres = ["arialbd.ttf", "arial.ttf"] if negrita else ["arial.ttf"]
    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def _crear_imagen_tablas(descripcion_visual: str) -> bytes:
    ancho, alto = 1400, 1000
    imagen = Image.new("RGB", (ancho, alto), "#f4f1ea")
    dibujo = ImageDraw.Draw(imagen)

    azul = "#1f3a52"
    texto = "#232320"
    borde = "#d5d1c8"
    celda = "#ffffff"

    dibujo.rounded_rectangle((40, 35, ancho - 40, alto - 35), radius=24, fill="#ffffff", outline=borde, width=3)
    dibujo.text((80, 70), "Tablas de multiplicar del 1 al 9", fill=azul, font=_fuente(44, True))
    dibujo.text(
        (80, 130),
        "Lamina visual generada localmente por ProfeIA, sin costo de IA.",
        fill="#6c6961",
        font=_fuente(24),
    )

    inicio_x, inicio_y = 80, 200
    ancho_columna, alto_fila = 135, 62
    for tabla in range(1, 10):
        x = inicio_x + ((tabla - 1) % 3) * 420
        y = inicio_y + ((tabla - 1) // 3) * 245
        dibujo.rounded_rectangle((x, y, x + 360, y + 210), radius=18, fill="#f9f8f4", outline=borde, width=2)
        dibujo.text((x + 22, y + 14), f"Tabla del {tabla}", fill=azul, font=_fuente(26, True))

        for multiplicador in range(1, 10):
            fila = (multiplicador - 1) // 3
            columna = (multiplicador - 1) % 3
            cx = x + 22 + columna * ancho_columna
            cy = y + 58 + fila * alto_fila
            dibujo.rounded_rectangle((cx, cy, cx + 116, cy + 42), radius=10, fill=celda, outline=borde)
            dibujo.text(
                (cx + 12, cy + 10),
                f"{tabla}x{multiplicador}={tabla * multiplicador}",
                fill=texto,
                font=_fuente(19, True),
            )

    if "0" in descripcion_visual or "10" in descripcion_visual:
        dibujo.text(
            (80, 940),
            "Tip: para extenderla, suma la tabla del 10 como desafio final.",
            fill="#6c6961",
            font=_fuente(22),
        )

    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()


def _lineas_texto(texto: str, max_caracteres: int) -> list[str]:
    palabras = (texto or "").split()
    lineas = []
    linea = ""
    for palabra in palabras:
        candidato = f"{linea} {palabra}".strip()
        if len(candidato) > max_caracteres and linea:
            lineas.append(linea)
            linea = palabra
        else:
            linea = candidato
    if linea:
        lineas.append(linea)
    return lineas


def _dibujar_texto_multilinea(
    dibujo: ImageDraw.ImageDraw,
    posicion: tuple[int, int],
    texto: str,
    fuente,
    color: str,
    max_caracteres: int,
    alto_linea: int,
    max_lineas: int = 4,
) -> int:
    x, y = posicion
    for linea in _lineas_texto(texto, max_caracteres)[:max_lineas]:
        dibujo.text((x, y), linea, fill=color, font=fuente)
        y += alto_linea
    return y


def _dibujar_tarjeta(
    dibujo: ImageDraw.ImageDraw,
    caja: tuple[int, int, int, int],
    titulo: str,
    detalle: str,
    color: str,
) -> None:
    x1, y1, x2, y2 = caja
    dibujo.rounded_rectangle(caja, radius=22, fill="#ffffff", outline="#d5d1c8", width=3)
    dibujo.rounded_rectangle((x1 + 18, y1 + 18, x1 + 84, y1 + 84), radius=18, fill=color)
    dibujo.text((x1 + 105, y1 + 24), titulo, fill="#1f3a52", font=_fuente(26, True))
    _dibujar_texto_multilinea(
        dibujo,
        (x1 + 26, y1 + 105),
        detalle,
        _fuente(23),
        "#232320",
        30,
        32,
        4,
    )


def _tema_lamina_local(descripcion_visual: str) -> tuple[str, list[tuple[str, str, str]]]:
    _ = descripcion_visual
    return (
        "Apoyo visual de emergencia",
        [
            ("1", "Idea central de la clase.", "#79b7d8"),
            ("2", "Ejemplo o imagen de referencia.", "#83bf7a"),
            ("3", "Actividad breve para practicar.", "#f0b35a"),
            ("4", "Cierre con palabras propias.", "#d884b7"),
        ],
    )


def _crear_lamina_conceptual(descripcion_visual: str) -> bytes:
    ancho, alto = 1400, 950
    imagen = Image.new("RGB", (ancho, alto), "#f4f1ea")
    dibujo = ImageDraw.Draw(imagen)
    azul = "#1f3a52"
    gris = "#6c6961"
    borde = "#d5d1c8"

    titulo, tarjetas = _tema_lamina_local(descripcion_visual)
    dibujo.rounded_rectangle((40, 35, ancho - 40, alto - 35), radius=24, fill="#ffffff", outline=borde, width=3)
    dibujo.text((80, 70), titulo[:58], fill=azul, font=_fuente(44, True))
    dibujo.text(
        (80, 130),
        "Lamina educativa local para acompanar la explicacion de la clase.",
        fill=gris,
        font=_fuente(24),
    )

    cajas = [
        (80, 210, 660, 470),
        (740, 210, 1320, 470),
        (80, 540, 660, 800),
        (740, 540, 1320, 800),
    ]
    for caja, tarjeta in zip(cajas, tarjetas):
        _dibujar_tarjeta(dibujo, caja, tarjeta[0], tarjeta[1], tarjeta[2])

    dibujo.rounded_rectangle((80, 835, 1320, 895), radius=18, fill="#f9f8f4", outline=borde, width=2)
    cierre = "Usar esta lamina para observar, conversar, resolver una consigna y cerrar con una explicacion oral."
    dibujo.text((110, 853), cierre, fill=gris, font=_fuente(24))

    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()


def _crear_imagen_local_generica(descripcion_visual: str) -> bytes:
    return _crear_lamina_conceptual(descripcion_visual)


TRADUCCIONES_BUSQUEDA = {
    "futbol": "football soccer",
    "football": "football soccer",
    "soccer": "football soccer",
    "pases": "passing training",
    "tiros": "shooting training",
    "deporte": "sports training",
    "plantas": "plants botany",
    "planta": "plant botany",
    "raiz": "plant root",
    "tallo": "plant stem",
    "hojas": "plant leaves",
    "flor": "flower plant",
    "multiplicacion": "multiplication",
    "multiplicar": "multiplication",
    "tablas": "multiplication table",
    "fracciones": "fractions",
    "animales": "animals",
    "cuerpo": "human body",
    "sistema": "system",
    "solar": "solar system",
    "mapa": "map",
    "provincias": "argentina provinces map",
    "argentina": "argentina",
    "ingles": "english language",
    "saludos": "greetings english",
    "presentaciones": "introductions english",
}


MATERIAS_BUSQUEDA = {
    "matematica": "mathematics education",
    "matemática": "mathematics education",
    "lengua": "reading writing education",
    "ciencias naturales": "science education",
    "ciencias sociales": "social studies education",
    "ingles": "english language education",
    "inglés": "english language education",
    "educacion artistica": "art education",
    "educación artística": "art education",
    "educacion fisica": "physical education",
    "educación física": "physical education",
}


PALABRAS_PENALIZADAS = {
    "logo",
    "icon",
    "coat of arms",
    "flag",
    "portrait",
    "statue",
    "building",
    "mapa mundi",
    "volcano",
    "lava",
    "movie",
    "album",
}


def _sin_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", str(texto))
    return "".join(caracter for caracter in normalizado if not unicodedata.combining(caracter))


def _palabras_importantes(texto: str) -> list[str]:
    stopwords = {
        "para",
        "sobre",
        "del",
        "las",
        "los",
        "una",
        "uno",
        "con",
        "que",
        "clase",
        "crear",
        "crea",
        "genera",
        "generar",
        "minuto",
        "minutos",
        "estudiantes",
        "alumnos",
        "ninos",
        "anos",
        "grado",
        "publico",
        "comprendan",
        "idea",
        "central",
        "puedan",
        "explicarla",
        "propias",
        "palabras",
        "situacion",
        "simple",
        "actividad",
        "preguntas",
        "evaluacion",
        "corta",
        "matematica",
        "matematicas",
        "lengua",
        "ciencias",
        "sociales",
        "naturales",
        "historia",
        "geografia",
        "educacion",
        "fisica",
    }
    palabras = [
        palabra
        for palabra in re.findall(r"[a-zA-Z0-9]+", _sin_acentos(texto).lower())
        if len(palabra) > 2 and palabra not in stopwords
    ]
    ordenadas = []
    for palabra in palabras:
        if palabra not in ordenadas:
            ordenadas.append(palabra)
    return ordenadas


def _tema_visual(contenido_json: dict) -> str:
    texto = " ".join(
        str(contenido_json.get(clave, ""))
        for clave in ["titulo", "objetivo", "resumen", "explicacion"]
    )
    palabras = _palabras_importantes(texto)
    return " ".join(palabras[:8])


def _consultas_imagen(contenido_json: dict) -> list[str]:
    texto = " ".join(
        str(contenido_json.get(clave, ""))
        for clave in ["titulo", "objetivo", "resumen", "explicacion"]
    )
    texto_normalizado = _sin_acentos(texto).lower()
    palabras = _palabras_importantes(texto_normalizado)
    materia_visible = str(contenido_json.get("titulo", "")).split(":", 1)[0]
    materia = _sin_acentos(materia_visible).lower()

    consultas = []
    tema = " ".join(palabras[:6])
    if tema:
        consultas.append(f"{tema} education")
    # Las traducciones/atajos de palabra clave son un apoyo secundario, no la
    # busqueda principal: si una clase de fracciones menciona "futbol" como
    # un ejemplo cotidiano mas (entre cocina, musica, etc.), no significa que
    # la clase sea SOBRE futbol. Por eso van al final de la lista (no al
    # frente) y usan coincidencia de palabra completa (\b) en vez de
    # substring, para que "pases" no matchee dentro de "compases".
    for palabra, traduccion in TRADUCCIONES_BUSQUEDA.items():
        if re.search(rf"\b{re.escape(palabra)}\b", texto_normalizado):
            consultas.append(f"{traduccion} education")
    if re.search(r"\b(tabla|multiplica\w*)\b", texto_normalizado):
        consultas.append("multiplication table education")
    if re.search(r"\b(futbol|pases|tiros)\b", texto_normalizado):
        consultas.append("soccer passing shooting training education")
    materia_consulta = MATERIAS_BUSQUEDA.get(materia)
    if materia_consulta and tema:
        consultas.append(f"{tema} {materia_consulta}")
    if materia and palabras:
        consultas.append(f"{palabras[0]} {materia} school")

    consultas_limpias = []
    for consulta in consultas:
        consulta = " ".join(consulta.split())
        if consulta and consulta not in consultas_limpias:
            consultas_limpias.append(consulta)
    return consultas_limpias or ["education school"]


def _puntuar_resultado_imagen(pagina: dict, consulta: str, palabras_clave: list[str]) -> int:
    imageinfo = (pagina.get("imageinfo") or [{}])[0]
    metadata = imageinfo.get("extmetadata") or {}
    texto = " ".join(
        [
            str(pagina.get("title", "")),
            str((metadata.get("ImageDescription") or {}).get("value", "")),
            str((metadata.get("ObjectName") or {}).get("value", "")),
        ]
    )
    texto = _sin_acentos(re.sub(r"<[^>]+>", " ", texto)).lower()
    # Importante: la relevancia se juzga SOLO contra las palabras del tema
    # real de la clase (palabras_clave), nunca contra las palabras de la
    # consulta de busqueda en si. Si se incluyeran las palabras de la
    # consulta (ej. "soccer" al probar una busqueda de respaldo por
    # "futbol"), la puntuacion se vuelve circular: cualquier resultado que
    # matchee la busqueda "aprueba" el filtro de relevancia aunque no tenga
    # nada que ver con el tema real (asi es como una clase de fracciones
    # terminaba con una foto de una cancha de futbol).
    claves = set(palabras_clave[:8])
    puntaje = 0
    for palabra in claves:
        variantes = {palabra}
        if palabra.endswith("s") and len(palabra) > 4:
            variantes.add(palabra[:-1])
        else:
            variantes.add(f"{palabra}s")
        if palabra.endswith("ies") and len(palabra) > 5:
            variantes.add(palabra[:-3] + "y")
        if any(variante in texto for variante in variantes):
            puntaje += 2
    if "diagram" in texto or "illustration" in texto or "training" in texto:
        puntaje += 1
    for palabra in PALABRAS_PENALIZADAS:
        if palabra in texto and palabra not in consulta:
            puntaje -= 2
    return puntaje


def _umbral_relevancia(palabras_clave: list[str]) -> int:
    return 3 if len(palabras_clave) >= 3 else 2


def extraer_palabras_clave(contenido_json: dict, max_palabras: int = 6) -> str:
    texto = " ".join(
        str(contenido_json.get(clave, ""))
        for clave in ["titulo", "objetivo", "resumen", "explicacion"]
    ).lower()
    ordenadas = _palabras_importantes(texto)
    if "tabla" in texto or "multiplica" in texto:
        return "multiplication table education"
    return " ".join(ordenadas[:max_palabras]) or "education"


async def buscar_imagenes_wikimedia(
    cliente,
    clase_id: UUID,
    contenido_json: dict,
    cantidad: int = 3,
) -> list[dict]:
    """
    Busca imagenes gratuitas en Wikimedia Commons y las guarda como recursos.
    Conserva autor/licencia/fuente en metadata para atribucion.
    """
    consultas = _consultas_imagen(contenido_json)
    consulta = consultas[0]
    palabras_clave = _palabras_importantes(_tema_visual(contenido_json))
    umbral = _umbral_relevancia(palabras_clave)

    resultados = []
    try:
        async with httpx.AsyncClient(timeout=30, headers=WIKIMEDIA_HEADERS) as cliente_http:
            for consulta_actual in consultas[:4]:
                params = {
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": consulta_actual,
                    "gsrnamespace": 6,
                    "gsrlimit": max(cantidad * 8, 12),
                    "prop": "imageinfo",
                    "iiprop": "url|mime|extmetadata",
                    "iiurlwidth": 1200,
                    "origin": "*",
                }
                respuesta = await cliente_http.get(WIKIMEDIA_API_URL, params=params)
                respuesta.raise_for_status()
                paginas = (respuesta.json().get("query") or {}).get("pages") or {}
                paginas_ordenadas = sorted(
                    paginas.values(),
                    key=lambda pagina: _puntuar_resultado_imagen(
                        pagina,
                        consulta_actual,
                        palabras_clave,
                    ),
                    reverse=True,
                )

                for pagina in paginas_ordenadas:
                    puntaje = _puntuar_resultado_imagen(pagina, consulta_actual, palabras_clave)
                    if puntaje < umbral and palabras_clave:
                        continue

                    imageinfo = (pagina.get("imageinfo") or [{}])[0]
                    mime = imageinfo.get("mime") or ""
                    url = imageinfo.get("thumburl") or imageinfo.get("url")
                    # Wikimedia Commons registra escaneos de libros/documentos
                    # (paginas .djvu/.pdf) bajo mimes que empiezan con
                    # "image/" (ej. "image/vnd.djvu"), pero no son fotos ni
                    # ilustraciones utilizables como apoyo visual.
                    mimes_no_ilustrables = {"image/svg+xml", "image/vnd.djvu"}
                    if not url or not mime.startswith("image/") or mime in mimes_no_ilustrables:
                        continue

                    try:
                        respuesta_imagen = await cliente_http.get(url)
                        respuesta_imagen.raise_for_status()
                    except httpx.HTTPError:
                        continue

                    metadata = imageinfo.get("extmetadata") or {}
                    titulo = pagina.get("title", "imagen-wikimedia").replace("File:", "")
                    extension = ".jpg" if "jpeg" in mime else ".png" if "png" in mime else ".webp"
                    resultado_storage = await guardar_recurso_docente(
                        cliente=cliente,
                        clase_id=clase_id,
                        nombre_archivo=f"wikimedia-{len(resultados) + 1}{extension}",
                        contenido=respuesta_imagen.content,
                        content_type=mime,
                    )
                    resultados.append(
                        {
                            "url": resultado_storage["url"],
                            "metadata": {
                                "origen": "wikimedia_commons",
                                "consulta": consulta_actual,
                                "titulo": titulo,
                                "fuente": imageinfo.get("descriptionurl"),
                                "autor": (metadata.get("Artist") or {}).get("value"),
                                "licencia": (metadata.get("LicenseShortName") or {}).get("value"),
                                "puntaje_relevancia": puntaje,
                                "umbral_relevancia": umbral,
                                "uso": "imagen gratuita encontrada en Wikimedia Commons; revisar atribucion antes de publicar",
                                "bucket": resultado_storage["bucket"],
                                "path": resultado_storage["path"],
                                "modo_storage": resultado_storage["modo"],
                                "content_type": mime,
                            },
                        }
                    )
                    if len(resultados) >= cantidad:
                        break
                if len(resultados) >= cantidad:
                    break
    except httpx.HTTPStatusError as error:
        print(
            "[servicio_multimedia] Wikimedia no disponible "
            f"(HTTP {error.response.status_code}); usando imagenes locales."
        )
    except (httpx.RequestError, ValueError) as error:
        print(
            "[servicio_multimedia] Error buscando en Wikimedia; "
            f"usando imagenes locales. Detalle: {error}"
        )

    if resultados:
        return resultados

    urls_locales = await _generar_imagenes_locales(
        cliente,
        clase_id,
        " ".join([contenido_json.get("titulo", ""), contenido_json.get("objetivo", "")]),
        cantidad,
    )
    return [
        {
            "url": url,
            "metadata": {
                "origen": "local",
                "consulta": consulta,
                "consultas_intentadas": consultas,
                "uso": "fallback local sin costo; no se encontraron imagenes gratuitas suficientemente relevantes",
                "motivo": "sin_resultados_relevantes",
            },
        }
        for url in urls_locales
    ]


async def _generar_imagenes_locales(
    cliente,
    clase_id: UUID,
    descripcion_visual: str,
    cantidad: int,
) -> list[str]:
    urls = []
    for indice in range(cantidad):
        descripcion = descripcion_visual.lower()
        if "tabla" in descripcion or "multiplica" in descripcion:
            contenido = _crear_imagen_tablas(descripcion_visual)
            nombre = f"lamina-tablas-{indice + 1}.png"
        else:
            contenido = _crear_imagen_local_generica(descripcion_visual)
            nombre = f"recurso-visual-local-{indice + 1}.png"
        resultado_storage = await guardar_recurso_docente(
            cliente=cliente,
            clase_id=clase_id,
            nombre_archivo=nombre,
            contenido=contenido,
            content_type="image/png",
        )
        urls.append(resultado_storage["url"])
    return urls


def _url_voz_simulada(clase_id: UUID) -> str:
    return f"storage://profeia/audios/{clase_id}.mp3"


def _voz_openai(voz: str) -> str:
    voces = {
        "femenina": "alloy",
        "masculina": "verse",
        "infantil": "shimmer",
        "clonada": "alloy",
    }
    return voces.get(voz, "alloy")


async def _generar_voz_openai(
    api_key: str,
    modelo: str,
    texto: str,
    parametros: SolicitudGenerarVoz,
) -> bytes:
    payload = {
        "model": modelo,
        "voice": _voz_openai(parametros.voz),
        "input": texto,
        "response_format": "mp3",
        "speed": parametros.velocidad,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90) as cliente_http:
        respuesta = await cliente_http.post(
            OPENAI_SPEECH_URL,
            headers=headers,
            json=payload,
        )
        respuesta.raise_for_status()
    return respuesta.content


async def _generar_voz_elevenlabs(
    api_key: str,
    voice_id: str,
    texto: str,
    parametros: SolicitudGenerarVoz,
) -> bytes:
    payload = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    _ = parametros

    async with httpx.AsyncClient(timeout=90) as cliente_http:
        respuesta = await cliente_http.post(
            ELEVENLABS_TTS_URL.format(voice_id=voice_id),
            headers=headers,
            json=payload,
        )
        respuesta.raise_for_status()
    return respuesta.content


async def generar_voz(
    cliente,
    clase_id: UUID,
    guion_texto: str,
    parametros: SolicitudGenerarVoz,
) -> str:
    """
    Genera el audio narrado a partir del guion de la clase.
    Si no hay API key configurada, conserva el modo simulado para desarrollo.
    """
    configuracion = obtener_configuracion()
    texto = guion_texto.strip()
    if not texto:
        texto = "Clase generada con ProfeIA."

    try:
        if parametros.voz == "clonada" and _valor_configurado(
            configuracion.ia_voz_clonada_api_key
        ) and _valor_configurado(configuracion.ia_voz_clonada_voice_id):
            contenido = await _generar_voz_elevenlabs(
                configuracion.ia_voz_clonada_api_key,
                configuracion.ia_voz_clonada_voice_id,
                texto,
                parametros,
            )
        elif _valor_configurado(configuracion.ia_voz_api_key):
            contenido = await _generar_voz_openai(
                configuracion.ia_voz_api_key,
                configuracion.ia_voz_modelo,
                texto,
                parametros,
            )
        else:
            return _url_voz_simulada(clase_id)
    except httpx.HTTPStatusError as error:
        detalle = error.response.text[:300]
        print(
            "[servicio_multimedia] TTS no disponible "
            f"(HTTP {error.response.status_code}); usando voz simulada. "
            f"Detalle: {detalle}"
        )
        return _url_voz_simulada(clase_id)
    except (httpx.RequestError, ValueError, RuntimeError) as error:
        print(
            "[servicio_multimedia] Error al generar voz real; "
            f"usando voz simulada. Detalle: {error}"
        )
        return _url_voz_simulada(clase_id)

    resultado_storage = await guardar_recurso_docente(
        cliente=cliente,
        clase_id=clase_id,
        nombre_archivo="voz-ia.mp3",
        contenido=contenido,
        content_type="audio/mpeg",
    )
    return resultado_storage["url"]


async def _generar_imagen_openai(
    api_key: str,
    modelo: str,
    prompt: str,
    url: str = OPENAI_IMAGES_URL,
) -> bytes:
    payload = {
        "model": modelo,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90) as cliente_http:
        respuesta = await cliente_http.post(
            url or OPENAI_IMAGES_URL,
            headers=headers,
            json=payload,
        )
        respuesta.raise_for_status()

    datos = respuesta.json()
    imagen_b64 = datos.get("data", [{}])[0].get("b64_json")
    if imagen_b64:
        return base64.b64decode(imagen_b64)

    imagen_url = datos.get("data", [{}])[0].get("url")
    if imagen_url:
        async with httpx.AsyncClient(timeout=90) as cliente_http:
            respuesta_imagen = await cliente_http.get(imagen_url)
            respuesta_imagen.raise_for_status()
        return respuesta_imagen.content

    raise RuntimeError("La API de imagenes no devolvio contenido usable.")


async def _generar_imagen_pollinations(prompt: str, semilla: int | None = None) -> bytes:
    """
    Genera una imagen con Pollinations.ai: servicio gratuito, sin necesidad
    de API key ni registro. Devuelve la imagen directamente como bytes.
    """
    import urllib.parse

    prompt_codificado = urllib.parse.quote(prompt)
    url = POLLINATIONS_IMAGE_URL.format(prompt=prompt_codificado)
    params = {"width": 1024, "height": 1024, "nologo": "true"}
    if semilla is not None:
        params["seed"] = semilla

    async with httpx.AsyncClient(timeout=90) as cliente_http:
        respuesta = await cliente_http.get(url, params=params)
        respuesta.raise_for_status()

    content_type = respuesta.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise RuntimeError(
            f"Pollinations no devolvio una imagen valida (content-type: {content_type})"
        )
    return respuesta.content


def _proveedores_opciones_imagenes(configuracion) -> list[dict]:
    """
    Lista de proveedores para generar VARIAS opciones de imagen en paralelo
    (a diferencia de _proveedores_imagenes, que arma una cadena de fallback
    secuencial para quedarse con el primero que responda).
    """
    proveedores = []
    if configuracion.ia_imagenes_openai_habilitado and _valor_configurado(
        configuracion.ia_imagenes_api_key
    ):
        proveedores.append(
            {
                "nombre": "OpenAI Images",
                "tipo": "openai",
                "api_key": configuracion.ia_imagenes_api_key,
                "modelo": configuracion.ia_imagenes_modelo,
                "url": configuracion.ia_imagenes_url,
            }
        )
    if _valor_configurado(configuracion.ia_imagenes_secundario_api_key) and _valor_configurado(
        configuracion.ia_imagenes_secundario_url
    ):
        proveedores.append(
            {
                "nombre": "Proveedor secundario",
                "tipo": "openai",
                "api_key": configuracion.ia_imagenes_secundario_api_key,
                "modelo": configuracion.ia_imagenes_secundario_modelo,
                "url": configuracion.ia_imagenes_secundario_url,
            }
        )
    if _valor_configurado(configuracion.ia_imagenes_huggingface_api_key):
        proveedores.append(
            {
                "nombre": "Hugging Face",
                "tipo": "huggingface",
                "api_key": configuracion.ia_imagenes_huggingface_api_key,
                "modelo": configuracion.ia_imagenes_huggingface_modelo,
            }
        )
    # Pollinations siempre esta disponible: no requiere API key ni registro.
    proveedores.append({"nombre": "Pollinations", "tipo": "pollinations"})
    return proveedores


async def _generar_una_opcion(
    proveedor: dict,
    prompt: str,
    indice: int,
    prompt_simple: str | None = None,
) -> bytes:
    """Genera una sola imagen con el proveedor indicado."""
    if proveedor["tipo"] == "openai":
        return await _generar_imagen_openai(
            proveedor["api_key"],
            proveedor["modelo"],
            prompt,
            proveedor["url"],
        )
    if proveedor["tipo"] == "huggingface":
        # Al igual que Pollinations, el modelo servido por hf-inference no
        # sigue bien el prompt largo con reglas de composicion (pensado
        # para OpenAI); con el prompt corto respeta mucho mejor el tema.
        return await _generar_imagen_huggingface(
            proveedor["api_key"],
            proveedor["modelo"],
            prompt_simple or prompt,
        )
    if proveedor["tipo"] == "pollinations":
        # Semilla distinta por indice para que, si se pide mas de una opcion
        # de Pollinations, no salgan todas identicas. Usa el prompt corto:
        # el largo (con reglas de composicion) hace que este modelo ignore
        # la escena pedida y devuelva imagenes genericas.
        return await _generar_imagen_pollinations(prompt_simple or prompt, semilla=indice)
    raise ValueError(f"Tipo de proveedor desconocido: {proveedor['tipo']}")


async def generar_opciones_imagenes(
    cliente,
    clase_id: UUID,
    descripcion_visual: str,
    parametros: SolicitudGenerarImagenes,
    sugerencia_imagen: str | None = None,
) -> list[dict]:
    """
    Genera UNA imagen con cada proveedor disponible EN PARALELO (en vez de
    una cadena de fallback secuencial) y devuelve todas las opciones para
    que el docente elija cual usar en su clase.

    A diferencia de generar_imagenes() (que devuelve solo list[str] con la
    primera que funciono), esta funcion devuelve list[dict] con:
        {"url": ..., "proveedor": ..., "metadata": {...}}
    para que el frontend pueda mostrar un selector visual.

    sugerencia_imagen (opcional): descripcion especifica de la escena,
    generada por la IA de contenido junto con el resto de la clase
    (contenido_json["sugerencia_imagen"]). Si se provee, se usa en vez de
    descripcion_visual generico para armar un prompt de imagen mas preciso.

    Si ningun proveedor externo responde, cae a la imagen local generica
    (igual que el resto del sistema) para no dejar al docente sin nada.
    """
    import asyncio

    configuracion = obtener_configuracion()
    proveedores = _proveedores_opciones_imagenes(configuracion)
    prompt = _construir_prompt_imagen(
        descripcion_visual, parametros.estilo, sugerencia_imagen
    )
    prompt_simple = _construir_prompt_imagen_simple(
        descripcion_visual, parametros.estilo, sugerencia_imagen
    )

    async def _intentar(proveedor: dict, indice: int) -> dict | None:
        try:
            contenido = await _generar_una_opcion(proveedor, prompt, indice, prompt_simple)
        except httpx.HTTPStatusError as error:
            detalle = error.response.text[:300]
            print(
                f"[servicio_multimedia] {proveedor['nombre']} no disponible "
                f"(HTTP {error.response.status_code}) generando opcion; "
                f"Detalle: {detalle}"
            )
            return None
        except (httpx.RequestError, ValueError, RuntimeError) as error:
            print(
                f"[servicio_multimedia] Error con {proveedor['nombre']} "
                f"generando opcion. Detalle: {error}"
            )
            return None

        resultado_storage = await guardar_recurso_docente(
            cliente=cliente,
            clase_id=clase_id,
            nombre_archivo=f"opcion-imagen-{proveedor['nombre'].lower().replace(' ', '-')}.png",
            contenido=contenido,
            content_type="image/png",
        )
        return {
            "url": resultado_storage["url"],
            "proveedor": proveedor["nombre"],
            "metadata": {
                "origen": proveedor["tipo"],
                "prompt": prompt,
            },
        }

    tareas = [_intentar(proveedor, indice) for indice, proveedor in enumerate(proveedores)]
    resultados_crudos = await asyncio.gather(*tareas)
    opciones = [resultado for resultado in resultados_crudos if resultado is not None]

    if not opciones:
        print(
            "[servicio_multimedia] Ningun proveedor genero opciones de imagen; "
            "usando imagen local como unica opcion."
        )
        urls_locales = await _generar_imagenes_locales(
            cliente,
            clase_id,
            descripcion_visual,
            1,
        )
        opciones = [
            {
                "url": url,
                "proveedor": "Local (sin IA)",
                "metadata": {"origen": "local", "prompt": prompt},
            }
            for url in urls_locales
        ]

    return opciones


async def _generar_imagen_huggingface(api_key: str, modelo: str, prompt: str) -> bytes:
    """
    Genera una imagen usando la Inference API gratuita de Hugging Face.
    Requiere una cuenta gratuita y un token con permiso de "Inferencia".

    Nota: si el modelo no esta "caliente" en la infraestructura de HF, la
    primera llamada puede devolver 503 con un JSON indicando
    estimated_time (segundos hasta que este listo). En ese caso reintenta
    una vez despues de esperar ese tiempo.
    """
    url = HUGGINGFACE_INFERENCE_URL.format(modelo=modelo)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"inputs": prompt}

    async with httpx.AsyncClient(timeout=120) as cliente_http:
        respuesta = await cliente_http.post(url, headers=headers, json=payload)

        if respuesta.status_code == 503:
            import asyncio as _asyncio

            try:
                info = respuesta.json()
                espera = min(float(info.get("estimated_time", 20)), 30)
            except ValueError:
                espera = 20
            await _asyncio.sleep(espera)
            respuesta = await cliente_http.post(url, headers=headers, json=payload)

        respuesta.raise_for_status()

    content_type = respuesta.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise RuntimeError(
            f"Hugging Face no devolvio una imagen valida "
            f"(content-type: {content_type}). Body: {respuesta.text[:200]}"
        )
    return respuesta.content


def _proveedores_imagenes(configuracion) -> list[dict]:
    proveedores = []
    if configuracion.ia_imagenes_openai_habilitado and _valor_configurado(
        configuracion.ia_imagenes_api_key
    ):
        proveedores.append(
            {
                "nombre": "OpenAI Images",
                "tipo": "openai",
                "api_key": configuracion.ia_imagenes_api_key,
                "modelo": configuracion.ia_imagenes_modelo,
                "url": configuracion.ia_imagenes_url,
            }
        )
    if _valor_configurado(configuracion.ia_imagenes_secundario_api_key) and _valor_configurado(
        configuracion.ia_imagenes_secundario_url
    ):
        proveedores.append(
            {
                "nombre": "Imagenes secundario",
                "tipo": "openai",
                "api_key": configuracion.ia_imagenes_secundario_api_key,
                "modelo": configuracion.ia_imagenes_secundario_modelo,
                "url": configuracion.ia_imagenes_secundario_url,
            }
        )
    if _valor_configurado(configuracion.ia_imagenes_huggingface_api_key):
        proveedores.append(
            {
                "nombre": "Hugging Face",
                "tipo": "huggingface",
                "api_key": configuracion.ia_imagenes_huggingface_api_key,
                "modelo": configuracion.ia_imagenes_huggingface_modelo,
            }
        )
    # Pollinations siempre esta disponible (gratis, sin API key) y ya se
    # usa como ultimo recurso en _proveedores_opciones_imagenes(). Antes
    # faltaba aca, asi que si OpenAI/HuggingFace fallaban (limite de
    # facturacion, modelo dado de baja, etc.) se caia directo a la lamina
    # local generica que ignora el tema pedido, en vez de intentar una
    # imagen real generada acorde al contenido de la clase.
    proveedores.append({"nombre": "Pollinations", "tipo": "pollinations"})
    return proveedores


async def _generar_con_proveedor(
    proveedor: dict,
    prompt: str,
    indice: int = 0,
    prompt_simple: str | None = None,
) -> bytes:
    """Genera una imagen despachando al proveedor correcto segun su tipo."""
    if proveedor["tipo"] == "openai":
        return await _generar_imagen_openai(
            proveedor["api_key"],
            proveedor["modelo"],
            prompt,
            proveedor["url"],
        )
    if proveedor["tipo"] == "huggingface":
        # Igual que Pollinations: el prompt corto respeta mucho mejor el
        # tema pedido que el prompt largo con reglas de composicion.
        return await _generar_imagen_huggingface(
            proveedor["api_key"],
            proveedor["modelo"],
            prompt_simple or prompt,
        )
    if proveedor["tipo"] == "pollinations":
        # Semilla distinta por indice para que, si se piden varias
        # imagenes, no salgan todas identicas. Usa el prompt corto (ver
        # _construir_prompt_imagen_simple): el largo hace que este modelo
        # ignore la escena pedida y devuelva imagenes genericas.
        return await _generar_imagen_pollinations(prompt_simple or prompt, semilla=indice)
    raise ValueError(f"Tipo de proveedor desconocido: {proveedor['tipo']}")


async def generar_imagenes(
    cliente,
    clase_id: UUID,
    descripcion_visual: str,
    parametros: SolicitudGenerarImagenes,
    sugerencia_imagen: str | None = None,
) -> list[str]:
    """
    Genera imagenes de apoyo para la clase.
    Si no hay API key configurada, conserva el modo simulado para desarrollo.

    sugerencia_imagen (opcional): descripcion especifica de la escena,
    generada por la IA de contenido (contenido_json["sugerencia_imagen"]).
    """
    configuracion = obtener_configuracion()
    proveedores = _proveedores_imagenes(configuracion)
    if not proveedores:
        return await _generar_imagenes_locales(
            cliente,
            clase_id,
            descripcion_visual,
            parametros.cantidad,
        )

    prompt = _construir_prompt_imagen(
        descripcion_visual, parametros.estilo, sugerencia_imagen
    )
    prompt_simple = _construir_prompt_imagen_simple(
        descripcion_visual, parametros.estilo, sugerencia_imagen
    )
    for proveedor in proveedores:
        urls = []
        try:
            for indice in range(parametros.cantidad):
                contenido = await _generar_con_proveedor(proveedor, prompt, indice, prompt_simple)
                resultado_storage = await guardar_recurso_docente(
                    cliente=cliente,
                    clase_id=clase_id,
                    nombre_archivo=f"imagen-ia-{indice + 1}.png",
                    contenido=contenido,
                    content_type="image/png",
                )
                urls.append(resultado_storage["url"])
            return urls
        except httpx.HTTPStatusError as error:
            detalle = error.response.text[:300]
            print(
                f"[servicio_multimedia] {proveedor['nombre']} no disponible "
                f"(HTTP {error.response.status_code}); probando siguiente proveedor. "
                f"Detalle: {detalle}"
            )
        except (httpx.RequestError, ValueError, RuntimeError) as error:
            print(
                f"[servicio_multimedia] Error con {proveedor['nombre']}; "
                f"probando siguiente proveedor. Detalle: {error}"
            )

    print(
        "[servicio_multimedia] Ningun proveedor de imagenes respondio; "
        "usando imagenes locales."
    )
    return await _generar_imagenes_locales(
        cliente,
        clase_id,
        descripcion_visual,
        parametros.cantidad,
    )


async def generar_estructura_slides(clase_id: UUID, contenido_json: dict) -> dict:
    """
    Genera la estructura de diapositivas (slides) a partir del contenido
    pedagogico ya generado. No depende de un proveedor externo de IA: es
    una transformacion del contenido_json en una estructura de slides.
    """
    _ = clase_id

    return {
        "slides": [
            {"orden": 1, "tipo": "intro", "titulo": contenido_json.get("titulo", "")},
            {"orden": 2, "tipo": "objetivo", "texto": contenido_json.get("objetivo", "")},
            {"orden": 3, "tipo": "explicacion", "texto": contenido_json.get("explicacion", "")},
            {"orden": 4, "tipo": "ejemplos", "items": contenido_json.get("ejemplos", [])},
            {"orden": 5, "tipo": "actividad", "texto": contenido_json.get("actividad", "")},
            {"orden": 6, "tipo": "cierre", "texto": contenido_json.get("resumen", "")},
        ]
    }
