"""
Router de generacion multimedia para una clase ya creada: voz, imagenes y
estructura de slides.
"""

from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.supabase_client import obtener_cliente_supabase
from app.models.recurso import (
    PaqueteAlumnoRespuesta,
    RecursoGeneradoRespuesta,
    SolicitudAdjuntarRecurso,
    SolicitudGenerarImagenes,
    SolicitudGenerarVoz,
)
from app.services.servicio_multimedia import (
    buscar_imagenes_wikimedia,
    generar_estructura_slides,
    generar_imagenes,
    generar_opciones_imagenes,
    generar_voz,
)
from app.services.servicio_planes import registrar_consumo_docente, validar_cupo_docente
from app.services.servicio_storage import guardar_recurso_docente

router = APIRouter(prefix="/clases/{clase_id}", tags=["multimedia"])


def _obtener_clase_o_404(cliente, clase_id: UUID) -> dict:
    resultado = (
        cliente.table("clases")
        .select("*")
        .eq("id", str(clase_id))
        .maybe_single()
        .execute()
    )
    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )
    return resultado.data


def _guardar_recurso(cliente, clase_id: UUID, tipo: str, url_storage: str, metadata: dict):
    nuevo_recurso = {
        "clase_id": str(clase_id),
        "tipo": tipo,
        "url_storage": url_storage,
        "metadata_json": metadata,
    }
    resultado = cliente.table("recursos_generados").insert(nuevo_recurso).execute()
    return resultado.data[0] if resultado.data else nuevo_recurso


def _listar_recursos(cliente, clase_id: UUID, tipo: str | None = None) -> list[dict]:
    consulta = (
        cliente.table("recursos_generados")
        .select("*")
        .eq("clase_id", str(clase_id))
        .order("creado_en", desc=True)
    )
    if tipo:
        consulta = consulta.eq("tipo", tipo)
    return consulta.execute().data or []


def _reemplazar_imagenes_gratis(cliente, clase_id: UUID) -> None:
    """Quita imagenes gratis anteriores para no mezclar resultados irrelevantes."""
    for recurso in _listar_recursos(cliente, clase_id, "imagen"):
        metadata = recurso.get("metadata_json") or {}
        if metadata.get("origen") not in {"wikimedia_commons", "local"}:
            continue
        recurso_id = recurso.get("id")
        if recurso_id:
            cliente.table("recursos_generados").delete().eq("id", recurso_id).execute()


def _reemplazar_opciones_imagenes(cliente, clase_id: UUID) -> None:
    """Quita opciones anteriores antes de guardar nuevas alternativas."""
    for recurso in _listar_recursos(cliente, clase_id, "imagen"):
        metadata = recurso.get("metadata_json") or {}
        if metadata.get("origen") != "opcion_imagen":
            continue
        recurso_id = recurso.get("id")
        if recurso_id:
            cliente.table("recursos_generados").delete().eq("id", recurso_id).execute()


def _ultimo_apoyo(cliente, clase_id: UUID) -> dict | None:
    resultado = (
        cliente.table("apoyos_accesibilidad")
        .select("*")
        .eq("clase_id", str(clase_id))
        .order("creado_en", desc=True)
        .execute()
    )
    apoyos = resultado.data or []
    return apoyos[0].get("apoyo_json") if apoyos else None


def construir_paquete_alumno(cliente, clase: dict) -> PaqueteAlumnoRespuesta:
    clase_id = UUID(str(clase["id"]))
    contenido = clase.get("contenido_json") or {}

    voces = _listar_recursos(cliente, clase_id, "voz")
    imagenes = _listar_recursos(cliente, clase_id, "imagen")
    audios_docente = _listar_recursos(cliente, clase_id, "audio_docente")

    return PaqueteAlumnoRespuesta(
        clase_id=clase_id,
        titulo=contenido.get("titulo") or clase.get("titulo") or "Clase",
        introduccion=contenido.get("introduccion", ""),
        explicacion=contenido.get("explicacion", ""),
        ejemplos=contenido.get("ejemplos", []),
        actividad=contenido.get("actividad", ""),
        preguntas=contenido.get("preguntas", []),
        resumen=contenido.get("resumen", ""),
        cuestionario=contenido.get("cuestionario", []),
        tarea_hogar=contenido.get("tarea_hogar"),
        audio_resumen=voces[0] if voces else None,
        imagenes=imagenes,
        audios_docente=audios_docente,
        apoyos=_ultimo_apoyo(cliente, clase_id),
        codigo_publico=clase.get("codigo_publico"),
    )


@router.post("/voz", response_model=RecursoGeneradoRespuesta, status_code=status.HTTP_201_CREATED)
async def generar_voz_clase(clase_id: UUID, parametros: SolicitudGenerarVoz):
    """Genera el audio narrado de la clase a partir de su guion."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    validar_cupo_docente(cliente, clase["docente_id"], {"voces": 1})

    contenido = clase.get("contenido_json") or {}
    guion_texto = contenido.get("explicacion", "")

    url_storage = await generar_voz(cliente, clase_id, guion_texto, parametros)
    registrar_consumo_docente(cliente, clase["docente_id"], {"voces": 1})

    return _guardar_recurso(
        cliente, clase_id, "voz", url_storage, parametros.model_dump()
    )


@router.post("/recursos", response_model=RecursoGeneradoRespuesta, status_code=status.HTTP_201_CREATED)
async def adjuntar_recurso_clase(clase_id: UUID, solicitud: SolicitudAdjuntarRecurso):
    """Adjunta una imagen o audio propio del docente a una clase."""
    cliente = obtener_cliente_supabase()
    _obtener_clase_o_404(cliente, clase_id)

    return _guardar_recurso(
        cliente,
        clase_id,
        solicitud.tipo,
        solicitud.url_storage,
        {
            "origen": "docente",
            "nombre": solicitud.nombre,
            "descripcion": solicitud.descripcion,
        },
    )


@router.post(
    "/recursos/upload",
    response_model=RecursoGeneradoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def subir_recurso_clase(
    clase_id: UUID,
    tipo: str = Form(...),
    descripcion: str | None = Form(None),
    archivo: UploadFile = File(...),
):
    """Sube una imagen/audio del docente a Storage y lo adjunta a la clase."""
    if tipo not in {"imagen", "audio_docente"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tipo de recurso no permitido",
        )

    cliente = obtener_cliente_supabase()
    _obtener_clase_o_404(cliente, clase_id)
    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Archivo vacio",
        )

    resultado_storage = await guardar_recurso_docente(
        cliente=cliente,
        clase_id=clase_id,
        nombre_archivo=archivo.filename or "recurso.bin",
        contenido=contenido,
        content_type=archivo.content_type,
    )

    return _guardar_recurso(
        cliente,
        clase_id,
        tipo,
        resultado_storage["url"],
        {
            "origen": "docente",
            "nombre": archivo.filename,
            "descripcion": descripcion,
            "bucket": resultado_storage["bucket"],
            "path": resultado_storage["path"],
            "modo_storage": resultado_storage["modo"],
            "content_type": archivo.content_type,
        },
    )


@router.post(
    "/imagenes",
    response_model=list[RecursoGeneradoRespuesta],
    status_code=status.HTTP_201_CREATED,
)
async def generar_imagenes_clase(clase_id: UUID, parametros: SolicitudGenerarImagenes):
    """Genera imagenes de apoyo para la clase."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    validar_cupo_docente(cliente, clase["docente_id"], {"imagenes": parametros.cantidad})

    contenido = clase.get("contenido_json") or {}
    descripcion_visual = ". ".join(
        parte
        for parte in [
            contenido.get("titulo", ""),
            contenido.get("objetivo", ""),
            contenido.get("resumen", ""),
        ]
        if parte
    )
    sugerencia_imagen = contenido.get("sugerencia_imagen")

    urls = await generar_imagenes(
        cliente, clase_id, descripcion_visual, parametros, sugerencia_imagen
    )
    registrar_consumo_docente(cliente, clase["docente_id"], {"imagenes": len(urls)})

    return [
        _guardar_recurso(cliente, clase_id, "imagen", url, parametros.model_dump())
        for url in urls
    ]


@router.post(
    "/imagenes/opciones",
    status_code=status.HTTP_200_OK,
)
async def generar_opciones_imagenes_clase(clase_id: UUID, parametros: SolicitudGenerarImagenes):
    """
    Genera UNA imagen con cada proveedor disponible EN PARALELO (OpenAI,
    Hugging Face, Pollinations, etc.) para que el docente elija cual usar.

    A diferencia de POST /imagenes, esta ruta NO guarda las opciones como
    recursos definitivos de la clase todavia: solo las deja disponibles en
    Storage para previsualizar. Una vez que el docente elige una, el
    frontend debe llamar a POST /clases/{clase_id}/recursos con la url de
    la opcion elegida (tipo="imagen") para persistirla como recurso final
    de la clase.

    Devuelve una lista de opciones:
        [{"url": ..., "proveedor": ..., "metadata": {...}}, ...]
    """
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    # Cada opcion cuenta como 1 imagen generada a fines de cupo, sin
    # importar cuantos proveedores respondieron con exito.
    validar_cupo_docente(cliente, clase["docente_id"], {"imagenes": 1})

    contenido = clase.get("contenido_json") or {}
    descripcion_visual = ". ".join(
        parte
        for parte in [
            contenido.get("titulo", ""),
            contenido.get("objetivo", ""),
            contenido.get("resumen", ""),
        ]
        if parte
    )
    sugerencia_imagen = contenido.get("sugerencia_imagen")

    _reemplazar_opciones_imagenes(cliente, clase_id)
    opciones = await generar_opciones_imagenes(
        cliente, clase_id, descripcion_visual, parametros, sugerencia_imagen
    )
    registrar_consumo_docente(cliente, clase["docente_id"], {"imagenes": 1})

    recursos = []
    for opcion in opciones:
        metadata = {
            "origen": "opcion_imagen",
            "proveedor": opcion.get("proveedor"),
            **(opcion.get("metadata") or {}),
        }
        recursos.append(_guardar_recurso(cliente, clase_id, "imagen", opcion["url"], metadata))
    return recursos


@router.post(
    "/imagenes/buscar-web",
    response_model=list[RecursoGeneradoRespuesta],
    status_code=status.HTTP_201_CREATED,
)
async def buscar_imagenes_web_clase(clase_id: UUID, cantidad: int = 3):
    """Busca imagenes gratuitas en Wikimedia Commons y las adjunta a la clase."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    contenido = clase.get("contenido_json") or {}
    cantidad_segura = max(1, min(cantidad, 5))
    validar_cupo_docente(cliente, clase["docente_id"], {"imagenes": cantidad_segura})
    _reemplazar_imagenes_gratis(cliente, clase_id)

    recursos = await buscar_imagenes_wikimedia(
        cliente=cliente,
        clase_id=clase_id,
        contenido_json=contenido,
        cantidad=cantidad_segura,
    )
    registrar_consumo_docente(cliente, clase["docente_id"], {"imagenes": len(recursos)})
    return [
        _guardar_recurso(cliente, clase_id, "imagen", recurso["url"], recurso["metadata"])
        for recurso in recursos
    ]


@router.post("/slides", status_code=status.HTTP_201_CREATED)
async def generar_slides_clase(clase_id: UUID):
    """Genera la estructura de diapositivas a partir del contenido pedagogico."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)

    contenido = clase.get("contenido_json") or {}
    estructura = await generar_estructura_slides(clase_id, contenido)

    recurso = _guardar_recurso(
        cliente,
        clase_id,
        "slide",
        f"storage://profeia/slides/{clase_id}.json",
        estructura,
    )
    return recurso


@router.get("/alumno/paquete", response_model=PaqueteAlumnoRespuesta)
async def obtener_paquete_alumno(clase_id: UUID):
    """
    Devuelve contenido pensado para una vista alumno: resumen, audio e imagenes.
    """
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    return construir_paquete_alumno(cliente, clase)
