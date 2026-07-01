"""
Endpoints publicos para alumnos usando codigo de clase.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.supabase_client import obtener_cliente_supabase
from app.models.recurso import PaqueteAlumnoRespuesta, RecursoGeneradoRespuesta
from app.routers.exportacion import (
    _contenido_con_ultimo_apoyo,
    _guardar_recurso,
    _listar_recursos,
)
from app.routers.multimedia import construir_paquete_alumno
from app.services.servicio_exportacion import exportar_paquete_zip, exportar_pdf, exportar_pptx
from app.services.servicio_planes import registrar_consumo_docente, validar_cupo_docente

router = APIRouter(prefix="/publico", tags=["publico"])


def _obtener_clase_por_codigo_o_404(cliente, codigo: str) -> dict:
    resultado = (
        cliente.table("clases")
        .select("*")
        .eq("codigo_publico", codigo.strip().upper())
        .maybe_single()
        .execute()
    )
    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Codigo de clase no encontrado",
        )
    return resultado.data


@router.get("/clases/{codigo_publico}", response_model=PaqueteAlumnoRespuesta)
async def obtener_clase_publica(codigo_publico: str):
    """Devuelve la vista alumno de una clase usando codigo publico."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_por_codigo_o_404(cliente, codigo_publico)
    return construir_paquete_alumno(cliente, clase)


@router.post(
    "/clases/{codigo_publico}/exportar/zip",
    response_model=RecursoGeneradoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def exportar_clase_publica_zip(codigo_publico: str):
    """Genera un ZIP de la clase usando el codigo publico del alumno."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_por_codigo_o_404(cliente, codigo_publico)
    clase_id = clase["id"]
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
    ruta_zip = await exportar_paquete_zip(
        clase_id=clase_id,
        contenido_json=contenido,
        recursos=recursos,
        codigo_publico=clase.get("codigo_publico"),
        ruta_pdf=ruta_pdf,
        ruta_pptx=ruta_pptx,
    )

    recurso = _guardar_recurso(cliente, clase_id, "zip", ruta_zip)
    registrar_consumo_docente(
        cliente,
        clase["docente_id"],
        {"exportaciones_pdf": 1, "exportaciones_pptx": 1},
    )
    return recurso
