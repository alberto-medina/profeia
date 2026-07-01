"""
Modelos para pagos y suscripciones.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.plan import PlanId


class SolicitudSuscripcion(BaseModel):
    """Solicitud para crear una suscripcion de Mercado Pago."""

    docente_id: UUID
    plan_id: PlanId
    email: str


class SuscripcionCheckoutRespuesta(BaseModel):
    """Respuesta con el enlace de pago para que el docente confirme."""

    docente_id: UUID
    plan_id: PlanId
    proveedor: str = "mercado_pago"
    checkout_url: str
    proveedor_subscription_id: Optional[str] = None
    estado: str
    modo: str
