"""
Router de exportacion: genera PDF, PPTX y ZIP a partir de una clase ya generada.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.supabase_client import obtener_cliente_supabase
from app.models.recurso import RecursoGeneradoRespuesta
from app.services.servicio_exportacion import exportar_paquete_zip, exportar_pdf, exportar_pptx
from app.services.servicio_planes import registrar_consumo_docente, validar_cupo_docente

router = APIRouter(prefix="/clases/{clase_id}/exportar", tags=["exportacion"])


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


def _guardar_recurso(cliente, clase_id: UUID, tipo: str, url_storage: str):
    nuevo_recurso = {
        "clase_id": str(clase_id),
        "tipo": tipo,
        "url_storage": url_storage,
        "metadata_json": {},
    }
    resultado = cliente.table("recursos_generados").insert(nuevo_recurso).execute()
    return resultado.data[0] if resultado.data else nuevo_recurso


def _contenido_con_ultimo_apoyo(cliente, clase: dict) -> dict:
    contenido = dict(clase.get("contenido_json") or {})
    resultado = (
        cliente.table("apoyos_accesibilidad")
        .select("*")
        .eq("clase_id", str(clase["id"]))
        .order("creado_en", desc=True)
        .execute()
    )
    apoyos = resultado.data or []
    if apoyos:
        contenido["apoyo_accesibilidad"] = apoyos[0].get("apoyo_json") or {}
    return contenido


def _listar_recursos(cliente, clase_id: UUID) -> list[dict]:
    resultado = (
        cliente.table("recursos_generados")
        .select("*")
        .eq("clase_id", str(clase_id))
        .execute()
    )
    return resultado.data or []


@router.post("/pdf", response_model=RecursoGeneradoRespuesta, status_code=status.HTTP_201_CREATED)
async def exportar_clase_pdf(clase_id: UUID):
    """Genera y devuelve la URL del PDF de la clase."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    validar_cupo_docente(cliente, clase["docente_id"], {"exportaciones_pdf": 1})

    contenido = _contenido_con_ultimo_apoyo(cliente, clase)
    recursos = _listar_recursos(cliente, clase_id)
    url_storage = await exportar_pdf(clase_id, contenido, recursos)

    recurso = _guardar_recurso(cliente, clase_id, "pdf", url_storage)
    registrar_consumo_docente(cliente, clase["docente_id"], {"exportaciones_pdf": 1})
    return recurso


@router.post("/pptx", response_model=RecursoGeneradoRespuesta, status_code=status.HTTP_201_CREATED)
async def exportar_clase_pptx(clase_id: UUID):
    """Genera y devuelve la URL del PowerPoint de la clase."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    validar_cupo_docente(cliente, clase["docente_id"], {"exportaciones_pptx": 1})

    contenido = _contenido_con_ultimo_apoyo(cliente, clase)
    url_storage = await exportar_pptx(clase_id, contenido)

    recurso = _guardar_recurso(cliente, clase_id, "pptx", url_storage)
    registrar_consumo_docente(cliente, clase["docente_id"], {"exportaciones_pptx": 1})
    return recurso


@router.post("/zip", response_model=RecursoGeneradoRespuesta, status_code=status.HTTP_201_CREATED)
async def exportar_clase_zip(clase_id: UUID):
    """Genera un paquete ZIP descargable con los materiales de la clase."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    validar_cupo_docente(
        cliente,
        clase["docente_id"],
        {"exportaciones_pdf": 1, "exportaciones_pptx": 1},
    )
    contenido = _contenido_con_ultimo_apoyo(cliente, clase)

    recursos_existentes = [
        recurso
        for recurso in _listar_recursos(cliente, clase_id)
        if recurso.get("tipo") not in {"pdf", "pptx", "zip"}
    ]
    ruta_pdf = await exportar_pdf(clase_id, contenido, recursos_existentes)
    _guardar_recurso(cliente, clase_id, "pdf", ruta_pdf)
    ruta_pptx = await exportar_pptx(clase_id, contenido)
    _guardar_recurso(cliente, clase_id, "pptx", ruta_pptx)

    recursos = [
        recurso
        for recurso in _listar_recursos(cliente, clase_id)
        if recurso.get("tipo") != "zip"
    ]
    url_storage = await exportar_paquete_zip(
        clase_id=clase_id,
        contenido_json=contenido,
        recursos=recursos,
        codigo_publico=clase.get("codigo_publico"),
        ruta_pdf=ruta_pdf,
        ruta_pptx=ruta_pptx,
    )

    recurso = _guardar_recurso(cliente, clase_id, "zip", url_storage)
    registrar_consumo_docente(
        cliente,
        clase["docente_id"],
        {"exportaciones_pdf": 1, "exportaciones_pptx": 1},
    )
    return recurso
