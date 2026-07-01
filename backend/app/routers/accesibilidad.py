"""
Router de apoyos pedagogicos de accesibilidad.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.supabase_client import obtener_cliente_supabase
from app.models.accesibilidad import (
    ApoyoAccesibilidadRespuesta,
    SolicitudApoyosAccesibilidad,
)
from app.services.servicio_accesibilidad import generar_apoyos_accesibilidad
from app.services.servicio_planes import registrar_consumo_docente, validar_cupo_docente

router = APIRouter(prefix="/clases/{clase_id}/accesibilidad", tags=["accesibilidad"])


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


@router.post(
    "/apoyos",
    response_model=ApoyoAccesibilidadRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def generar_apoyos_clase(
    clase_id: UUID,
    solicitud: SolicitudApoyosAccesibilidad,
):
    """Genera apoyos educativos para atencion, TEA y lectura facil."""
    cliente = obtener_cliente_supabase()
    clase = _obtener_clase_o_404(cliente, clase_id)
    validar_cupo_docente(cliente, clase["docente_id"], {"apoyos_accesibilidad": 1})

    apoyo = generar_apoyos_accesibilidad(clase.get("contenido_json") or {}, solicitud)
    nuevo_apoyo = {
        "clase_id": str(clase_id),
        "docente_id": clase["docente_id"],
        "necesidades": solicitud.necesidades,
        "apoyo_json": apoyo.model_dump(),
    }

    resultado = cliente.table("apoyos_accesibilidad").insert(nuevo_apoyo).execute()
    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar el apoyo de accesibilidad",
        )

    registrar_consumo_docente(cliente, clase["docente_id"], {"apoyos_accesibilidad": 1})
    return resultado.data[0]
