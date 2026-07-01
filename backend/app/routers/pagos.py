"""
Router de pagos y suscripciones.
"""

from fastapi import APIRouter, Request, status

from app.core.supabase_client import obtener_cliente_supabase
from app.models.pago import SolicitudSuscripcion, SuscripcionCheckoutRespuesta
from app.services.servicio_pagos import (
    activar_suscripcion_demo,
    crear_suscripcion_mercado_pago,
    procesar_webhook_mercado_pago,
)

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.post(
    "/suscripciones/mercado-pago",
    response_model=SuscripcionCheckoutRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def crear_checkout_suscripcion(solicitud: SolicitudSuscripcion):
    """Crea una suscripcion y devuelve el enlace de checkout."""
    cliente = obtener_cliente_supabase()
    resultado = await crear_suscripcion_mercado_pago(
        cliente=cliente,
        docente_id=solicitud.docente_id,
        plan_id=solicitud.plan_id,
        email=solicitud.email,
    )
    return {
        "docente_id": solicitud.docente_id,
        "plan_id": solicitud.plan_id,
        "proveedor": "mercado_pago",
        **resultado,
    }


@router.post("/suscripciones/demo/activar", status_code=status.HTTP_200_OK)
async def activar_checkout_demo(solicitud: SolicitudSuscripcion):
    """Activa un plan en desarrollo sin depender del webhook real de Mercado Pago."""
    cliente = obtener_cliente_supabase()
    suscripcion = activar_suscripcion_demo(
        cliente=cliente,
        docente_id=solicitud.docente_id,
        plan_id=solicitud.plan_id,
    )
    return {
        "docente_id": solicitud.docente_id,
        "plan_id": solicitud.plan_id,
        "estado": "activa",
        "modo": "demo",
        "suscripcion": suscripcion,
    }


@router.post("/mercadopago/webhook", status_code=status.HTTP_200_OK)
async def recibir_webhook_mercado_pago(request: Request):
    """
    Recibe notificaciones de Mercado Pago.

    Si MERCADO_PAGO_WEBHOOK_SECRET esta configurado, valida la firma oficial.
    Luego consulta el recurso notificado y actualiza suscripciones/docente.plan.
    """
    cliente = obtener_cliente_supabase()
    payload = await request.json()
    resultado = await procesar_webhook_mercado_pago(cliente, payload, request)
    return {"recibido": True, **resultado}


@router.get("/mercadopago/retorno")
async def retorno_mercado_pago():
    """Destino simple tras volver del checkout en desarrollo."""
    return {"estado": "ok", "mensaje": "Volve a ProfeIA para continuar."}
