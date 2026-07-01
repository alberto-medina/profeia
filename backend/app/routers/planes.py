"""
Router de planes, capacidades y cuotas.
"""

from uuid import UUID

from fastapi import APIRouter

from app.core.supabase_client import obtener_cliente_supabase
from app.models.plan import PlanId, PlanRespuesta, UsoPlanRespuesta
from app.services.servicio_planes import listar_planes, obtener_plan, obtener_uso_docente

router = APIRouter(prefix="/planes", tags=["planes"])


@router.get("", response_model=list[PlanRespuesta])
async def obtener_planes():
    """Lista los planes disponibles y sus capacidades."""
    return listar_planes()


@router.get("/{plan_id}", response_model=PlanRespuesta)
async def obtener_detalle_plan(plan_id: PlanId):
    """Devuelve el detalle de un plan."""
    return obtener_plan(plan_id)


@router.get("/docentes/{docente_id}/uso", response_model=UsoPlanRespuesta)
async def obtener_uso_mensual_docente(docente_id: UUID, plan_id: PlanId | None = None):
    """Devuelve uso mensual real de un docente contra su plan."""
    cliente = obtener_cliente_supabase()
    return obtener_uso_docente(cliente, docente_id, plan_id)
