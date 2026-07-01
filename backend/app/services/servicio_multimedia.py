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
WIKIMEDIA_HEADERS = {
    "User-Agent": "ProfeIA/0.1 educativo-local (contacto: desarrollo@profeia.local)"
}


def _valor_configurado(valor: str | None) -> bool:
    if not valor:
        return False
    return valor.strip() not in {"", "TU_API_KEY", "TU_ACCESS_TOKEN"}


def _construir_prompt_imagen(descripcion_visual: str, estilo: str | None) -> str:
    estilo_final = estilo or "ilustracion educativa clara, simple y amigable"
    return (
        "Genera una imagen educativa para una clase escolar. "
        "Debe ser clara, apta para estudiantes, sin texto legible dentro de la imagen, "
        "con composicion simple y buen contraste. "
        f"Tema de la clase: {descripcion_visual}. "
        f"Estilo visual: {estilo_final}."
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


def _crear_imagen_local_generica(descripcion_visual: str) -> bytes:
    ancho, alto = 1200, 800
    imagen = Image.new("RGB", (ancho, alto), "#f4f1ea")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rounded_rectangle((40, 40, ancho - 40, alto - 40), radius=24, fill="#ffffff", outline="#d5d1c8", width=3)
    dibujo.text((90, 90), "Recurso visual ProfeIA", fill="#1f3a52", font=_fuente(44, True))
    dibujo.text((90, 165), "Imagen local sin costo de IA", fill="#6c6961", font=_fuente(26))
    texto = descripcion_visual[:220] or "Clase generada"
    lineas = []
    palabras = texto.split()
    linea = ""
    for palabra in palabras:
        candidato = f"{linea} {palabra}".strip()
        if len(candidato) > 52:
            lineas.append(linea)
            linea = palabra
        else:
            linea = candidato
    if linea:
        lineas.append(linea)
    y = 260
    for linea_texto in lineas[:7]:
        dibujo.text((110, y), linea_texto, fill="#232320", font=_fuente(30))
        y += 48
    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()


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
    for palabra, traduccion in TRADUCCIONES_BUSQUEDA.items():
        if palabra in texto_normalizado:
            consultas.append(f"{traduccion} education")
    if "tabla" in texto_normalizado or "multiplica" in texto_normalizado:
        consultas.insert(0, "multiplication table education")
    if "futbol" in texto_normalizado or "pases" in texto_normalizado or "tiros" in texto_normalizado:
        consultas.insert(0, "soccer passing shooting training")
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
    palabras_consulta = _palabras_importantes(consulta)
    claves = set(palabras_clave[:8] + palabras_consulta[:8])
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
                    if not url or not mime.startswith("image/") or mime == "image/svg+xml":
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
            OPENAI_IMAGES_URL,
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


async def generar_imagenes(
    cliente,
    clase_id: UUID,
    descripcion_visual: str,
    parametros: SolicitudGenerarImagenes,
) -> list[str]:
    """
    Genera imagenes de apoyo para la clase.
    Si no hay API key configurada, conserva el modo simulado para desarrollo.
    """
    configuracion = obtener_configuracion()
    if not _valor_configurado(configuracion.ia_imagenes_api_key):
        return await _generar_imagenes_locales(
            cliente,
            clase_id,
            descripcion_visual,
            parametros.cantidad,
        )

    prompt = _construir_prompt_imagen(descripcion_visual, parametros.estilo)
    urls = []
    try:
        for indice in range(parametros.cantidad):
            contenido = await _generar_imagen_openai(
                configuracion.ia_imagenes_api_key,
                configuracion.ia_imagenes_modelo,
                prompt,
            )
            resultado_storage = await guardar_recurso_docente(
                cliente=cliente,
                clase_id=clase_id,
                nombre_archivo=f"imagen-ia-{indice + 1}.png",
                contenido=contenido,
                content_type="image/png",
            )
            urls.append(resultado_storage["url"])
    except httpx.HTTPStatusError as error:
        detalle = error.response.text[:300]
        print(
            "[servicio_multimedia] OpenAI Images no disponible "
            f"(HTTP {error.response.status_code}); usando imagenes simuladas. "
            f"Detalle: {detalle}"
        )
        return await _generar_imagenes_locales(
            cliente,
            clase_id,
            descripcion_visual,
            parametros.cantidad,
        )
    except (httpx.RequestError, ValueError, RuntimeError) as error:
        print(
            "[servicio_multimedia] Error al generar imagenes reales; "
            f"usando imagenes simuladas. Detalle: {error}"
        )
        return await _generar_imagenes_locales(
            cliente,
            clase_id,
            descripcion_visual,
            parametros.cantidad,
        )
    return urls


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
