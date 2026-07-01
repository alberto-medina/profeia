"""
Integracion de pagos para suscripciones.
"""

import hashlib
import hmac
from uuid import UUID

import httpx
from fastapi import HTTPException, Request, status

from app.core.config import obtener_configuracion
from app.models.plan import PlanId
from app.services.servicio_planes import obtener_plan

MERCADO_PAGO_API = "https://api.mercadopago.com"
PRECIOS_MERCADO_PAGO_ARS: dict[PlanId, float] = {
    "gratis": 0,
    "docente": 9000,
    "pro": 19000,
    "institucion": 0,
}


def _token_configurado(valor: str) -> bool:
    return bool(valor and valor.strip() and not valor.strip().startswith("TU_"))


def _estado_local_desde_mp(estado_mp: str | None) -> str:
    estados = {
        "authorized": "activa",
        "active": "activa",
        "approved": "activa",
        "pending": "pendiente",
        "paused": "pausada",
        "cancelled": "cancelada",
        "canceled": "cancelada",
        "rejected": "cancelada",
        "expired": "vencida",
    }
    return estados.get((estado_mp or "").lower(), "pendiente")


def _parsear_external_reference(valor: str | None) -> tuple[UUID | None, PlanId | None]:
    if not valor or ":" not in valor:
        return None, None
    docente_texto, plan_id = valor.split(":", 1)
    if plan_id not in {"gratis", "docente", "pro", "institucion"}:
        return None, None
    try:
        return UUID(docente_texto), plan_id  # type: ignore[return-value]
    except ValueError:
        return None, None


def _detalle_error_mercado_pago(error: httpx.HTTPStatusError) -> str:
    try:
        datos = error.response.json()
    except ValueError:
        return error.response.text[:500] or str(error)
    mensaje = datos.get("message") or datos.get("error") or "Error de Mercado Pago"
    causa = datos.get("cause")
    if isinstance(causa, list) and causa:
        detalles = []
        for item in causa:
            if isinstance(item, dict):
                detalles.append(str(item.get("description") or item.get("code") or item))
            else:
                detalles.append(str(item))
        return f"{mensaje}: {' | '.join(detalles)}"
    return str(mensaje)


def _guardar_suscripcion_local(
    cliente,
    docente_id: UUID,
    plan_id: PlanId,
    proveedor_subscription_id: str | None,
    estado: str,
    proveedor_customer_id: str | None = None,
) -> dict:
    existentes = []
    if proveedor_subscription_id:
        existentes = (
            cliente.table("suscripciones_docentes")
            .select("*")
            .eq("proveedor_subscription_id", proveedor_subscription_id)
            .execute()
            .data
            or []
        )

    registro = {
        "docente_id": str(docente_id),
        "plan": plan_id,
        "estado": estado,
        "proveedor_pago": "mercado_pago",
        "proveedor_customer_id": proveedor_customer_id,
        "proveedor_subscription_id": proveedor_subscription_id,
    }

    if existentes:
        resultado = (
            cliente.table("suscripciones_docentes")
            .update(registro)
            .eq("id", existentes[0]["id"])
            .execute()
        )
        return resultado.data[0] if resultado.data else {**existentes[0], **registro}

    resultado = cliente.table("suscripciones_docentes").insert(registro).execute()
    return resultado.data[0] if resultado.data else registro


def _actualizar_plan_docente(cliente, docente_id: UUID, plan_id: PlanId, estado: str) -> None:
    plan_final = plan_id if estado == "activa" else "gratis"
    cliente.table("docentes").update({"plan": plan_final}).eq("id", str(docente_id)).execute()


async def crear_suscripcion_mercado_pago(
    cliente,
    docente_id: UUID,
    plan_id: PlanId,
    email: str,
) -> dict:
    """
    Crea una suscripcion recurrente en Mercado Pago.

    Sin access token real devuelve un checkout demo para poder probar el flujo
    visual sin cobrar.
    """
    plan = obtener_plan(plan_id)
    configuracion = obtener_configuracion()
    precio = PRECIOS_MERCADO_PAGO_ARS.get(plan_id, 0)

    if plan_id == "gratis" or precio <= 0:
        _guardar_suscripcion_local(cliente, docente_id, plan_id, None, "activa")
        _actualizar_plan_docente(cliente, docente_id, plan_id, "activa")
        return {
            "checkout_url": "",
            "proveedor_subscription_id": None,
            "estado": "activa",
            "modo": "gratis",
        }

    if not _token_configurado(configuracion.mercado_pago_access_token):
        demo_id = f"demo-{docente_id}-{plan_id}"
        _guardar_suscripcion_local(cliente, docente_id, plan_id, demo_id, "pendiente")
        return {
            "checkout_url": f"https://www.mercadopago.com.ar/subscriptions/checkout?preapproval_id={demo_id}",
            "proveedor_subscription_id": demo_id,
            "estado": "pendiente",
            "modo": "demo",
        }

    payload = {
        "reason": f"ProfeIA - Plan {plan.nombre}",
        "external_reference": f"{docente_id}:{plan_id}",
        "payer_email": email,
        "back_url": configuracion.mercado_pago_back_url,
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": float(precio),
            "currency_id": "ARS",
        },
    }
    headers = {
        "Authorization": f"Bearer {configuracion.mercado_pago_access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            respuesta = await client.post(
                f"{MERCADO_PAGO_API}/preapproval",
                json=payload,
                headers=headers,
            )
            respuesta.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Mercado Pago rechazo el checkout: {_detalle_error_mercado_pago(error)}",
            ) from error
        datos = respuesta.json()

    proveedor_subscription_id = datos.get("id")
    estado = _estado_local_desde_mp(datos.get("status"))
    _guardar_suscripcion_local(
        cliente,
        docente_id,
        plan_id,
        proveedor_subscription_id,
        estado,
        datos.get("payer_id"),
    )
    _actualizar_plan_docente(cliente, docente_id, plan_id, estado)

    return {
        "checkout_url": datos.get("init_point") or datos.get("sandbox_init_point") or "",
        "proveedor_subscription_id": proveedor_subscription_id,
        "estado": estado,
        "modo": "mercado_pago",
    }


def activar_suscripcion_demo(cliente, docente_id: UUID, plan_id: PlanId) -> dict:
    """Activa un plan en modo desarrollo sin esperar Mercado Pago real."""
    demo_id = f"demo-{docente_id}-{plan_id}"
    suscripcion = _guardar_suscripcion_local(
        cliente,
        docente_id,
        plan_id,
        demo_id,
        "activa",
    )
    _actualizar_plan_docente(cliente, docente_id, plan_id, "activa")
    return suscripcion


def _extraer_id_notificacion(payload: dict, request: Request) -> str | None:
    data = payload.get("data")
    if isinstance(data, dict) and data.get("id"):
        return str(data["id"])
    if payload.get("id"):
        return str(payload["id"])
    return request.query_params.get("data.id") or request.query_params.get("id")


def _extraer_tipo_notificacion(payload: dict, request: Request) -> str:
    return str(
        payload.get("type")
        or payload.get("topic")
        or request.query_params.get("type")
        or request.query_params.get("topic")
        or ""
    )


def _validar_firma_webhook(request: Request, data_id: str | None) -> None:
    configuracion = obtener_configuracion()
    secret = configuracion.mercado_pago_webhook_secret.strip()
    if not _token_configurado(secret):
        return

    firma = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")
    partes = {
        clave.strip(): valor.strip()
        for item in firma.split(",")
        if "=" in item
        for clave, valor in [item.split("=", 1)]
    }
    ts = partes.get("ts")
    v1 = partes.get("v1")
    if not data_id or not request_id or not ts or not v1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma de Mercado Pago incompleta",
        )

    manifiesto = f"id:{data_id};request-id:{request_id};ts:{ts};"
    esperado = hmac.new(
        secret.encode("utf-8"),
        manifiesto.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(esperado, v1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma de Mercado Pago invalida",
        )


async def _consultar_preapproval_mercado_pago(preapproval_id: str) -> dict:
    configuracion = obtener_configuracion()
    if not _token_configurado(configuracion.mercado_pago_access_token):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mercado Pago no esta configurado",
        )
    headers = {"Authorization": f"Bearer {configuracion.mercado_pago_access_token}"}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            respuesta = await client.get(
                f"{MERCADO_PAGO_API}/preapproval/{preapproval_id}",
                headers=headers,
            )
            respuesta.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"No se pudo consultar Mercado Pago: {_detalle_error_mercado_pago(error)}",
            ) from error
        return respuesta.json()


async def _consultar_pago_autorizado_mercado_pago(payment_id: str) -> dict:
    configuracion = obtener_configuracion()
    if not _token_configurado(configuracion.mercado_pago_access_token):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mercado Pago no esta configurado",
        )
    headers = {"Authorization": f"Bearer {configuracion.mercado_pago_access_token}"}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            respuesta = await client.get(
                f"{MERCADO_PAGO_API}/authorized_payments/{payment_id}",
                headers=headers,
            )
            respuesta.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"No se pudo consultar Mercado Pago: {_detalle_error_mercado_pago(error)}",
            ) from error
        return respuesta.json()


async def _preapproval_desde_notificacion(tipo: str, data_id: str) -> tuple[str, dict]:
    if tipo in {"subscription_preapproval", "preapproval"}:
        return data_id, await _consultar_preapproval_mercado_pago(data_id)

    if tipo == "subscription_authorized_payment":
        pago = await _consultar_pago_autorizado_mercado_pago(data_id)
        preapproval_id = (
            pago.get("preapproval_id")
            or pago.get("preapproval")
            or pago.get("subscription_id")
        )
        if not preapproval_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Pago autorizado sin preapproval_id",
            )
        return str(preapproval_id), await _consultar_preapproval_mercado_pago(str(preapproval_id))

    raise HTTPException(
        status_code=status.HTTP_202_ACCEPTED,
        detail="Tipo de webhook ignorado",
    )


async def procesar_webhook_mercado_pago(cliente, payload: dict, request: Request) -> dict:
    """Procesa webhooks de suscripciones y activa/cancela el plan local."""
    data_id = _extraer_id_notificacion(payload, request)
    tipo = _extraer_tipo_notificacion(payload, request)
    _validar_firma_webhook(request, data_id)

    if not data_id:
        return {"procesado": False, "motivo": "sin data.id", "tipo": tipo}

    if tipo not in {"subscription_preapproval", "preapproval", "subscription_authorized_payment"}:
        return {"procesado": False, "motivo": "tipo ignorado", "tipo": tipo}

    preapproval_id, datos_mp = await _preapproval_desde_notificacion(tipo, data_id)
    docente_id, plan_id = _parsear_external_reference(datos_mp.get("external_reference"))
    if not docente_id or not plan_id:
        return {
            "procesado": False,
            "motivo": "external_reference invalida",
            "tipo": tipo,
            "preapproval_id": preapproval_id,
        }

    estado = _estado_local_desde_mp(datos_mp.get("status"))
    suscripcion = _guardar_suscripcion_local(
        cliente,
        docente_id,
        plan_id,
        datos_mp.get("id") or preapproval_id,
        estado,
        datos_mp.get("payer_id"),
    )
    _actualizar_plan_docente(cliente, docente_id, plan_id, estado)

    return {
        "procesado": True,
        "tipo": tipo,
        "preapproval_id": preapproval_id,
        "docente_id": str(docente_id),
        "plan_id": plan_id,
        "estado": estado,
        "suscripcion_id": suscripcion.get("id"),
    }
