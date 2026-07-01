"""
Catalogo de planes y helpers de cuotas.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.models.plan import CapacidadesPlan, CuotasPlan, PlanId, PlanRespuesta, UsoPlanRespuesta


PLANES: dict[PlanId, PlanRespuesta] = {
    "gratis": PlanRespuesta(
        id="gratis",
        nombre="Gratis",
        descripcion="Para probar el flujo y crear las primeras clases.",
        publico_objetivo="Docentes que quieren evaluar ProfeIA.",
        precio_referencia_usd=0,
        cuotas=CuotasPlan(
            clases=3,
            imagenes=6,
            voces=3,
            videos=0,
            minutos_grabacion=10,
            clonaciones_voz=0,
            exportaciones_pdf=10,
            exportaciones_pptx=10,
            apoyos_accesibilidad=6,
        ),
        capacidades=CapacidadesPlan(
            imagenes_clase=True,
            voz_narrada=True,
            grabacion_docente=True,
            apoyos_tdah=True,
            apoyos_tea=True,
            lectura_facil=True,
        ),
    ),
    "docente": PlanRespuesta(
        id="docente",
        nombre="Docente",
        descripcion="Para uso individual mensual con clases, imagenes y voz.",
        publico_objetivo="Docentes independientes.",
        precio_referencia_usd=9,
        cuotas=CuotasPlan(
            clases=50,
            imagenes=200,
            voces=80,
            videos=10,
            minutos_grabacion=180,
            clonaciones_voz=1,
            exportaciones_pdf=200,
            exportaciones_pptx=200,
            apoyos_accesibilidad=120,
        ),
        capacidades=CapacidadesPlan(
            imagenes_clase=True,
            voz_narrada=True,
            clonacion_voz=True,
            grabacion_docente=True,
            video_automatico=True,
            apoyos_tdah=True,
            apoyos_tea=True,
            lectura_facil=True,
        ),
    ),
    "pro": PlanRespuesta(
        id="pro",
        nombre="Pro",
        descripcion="Para docentes que publican contenido o preparan muchas clases.",
        publico_objetivo="Docentes creadores, tutores y equipos chicos.",
        precio_referencia_usd=19,
        cuotas=CuotasPlan(
            clases=200,
            imagenes=900,
            voces=300,
            videos=60,
            minutos_grabacion=600,
            clonaciones_voz=3,
            exportaciones_pdf=800,
            exportaciones_pptx=800,
            apoyos_accesibilidad=500,
        ),
        capacidades=CapacidadesPlan(
            imagenes_clase=True,
            voz_narrada=True,
            clonacion_voz=True,
            grabacion_docente=True,
            video_automatico=True,
            apoyos_tdah=True,
            apoyos_tea=True,
            lectura_facil=True,
        ),
    ),
    "institucion": PlanRespuesta(
        id="institucion",
        nombre="Institucion",
        descripcion="Para colegios, institutos y equipos con administracion centralizada.",
        publico_objetivo="Instituciones educativas.",
        precio_referencia_usd=None,
        cuotas=CuotasPlan(
            clases=2000,
            imagenes=8000,
            voces=2500,
            videos=500,
            minutos_grabacion=5000,
            clonaciones_voz=25,
            exportaciones_pdf=8000,
            exportaciones_pptx=8000,
            apoyos_accesibilidad=5000,
        ),
        capacidades=CapacidadesPlan(
            imagenes_clase=True,
            voz_narrada=True,
            clonacion_voz=True,
            grabacion_docente=True,
            video_automatico=True,
            apoyos_tdah=True,
            apoyos_tea=True,
            lectura_facil=True,
            soporte_institucional=True,
        ),
    ),
}


def listar_planes() -> list[PlanRespuesta]:
    return list(PLANES.values())


def obtener_plan(plan_id: PlanId) -> PlanRespuesta:
    return PLANES[plan_id]


def _periodo_actual() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _normalizar_plan(plan_id: str | None) -> PlanId:
    return plan_id if plan_id in PLANES else "gratis"  # type: ignore[return-value]


def obtener_plan_docente(cliente, docente_id: UUID | str) -> PlanId:
    """Devuelve el plan activo del docente, priorizando suscripcion activa."""
    suscripciones = (
        cliente.table("suscripciones_docentes")
        .select("*")
        .eq("docente_id", str(docente_id))
        .eq("estado", "activa")
        .order("creado_en", desc=True)
        .execute()
        .data
        or []
    )
    if suscripciones:
        return _normalizar_plan(suscripciones[0].get("plan"))

    resultado = (
        cliente.table("docentes")
        .select("*")
        .eq("id", str(docente_id))
        .maybe_single()
        .execute()
    )
    docente = getattr(resultado, "data", None) if resultado else None
    return _normalizar_plan((docente or {}).get("plan"))


def _uso_vacio(docente_id: UUID | str, periodo: str) -> dict:
    return {
        "docente_id": str(docente_id),
        "periodo": periodo,
        "clases": 0,
        "imagenes": 0,
        "voces": 0,
        "videos": 0,
        "minutos_grabacion": 0,
        "clonaciones_voz": 0,
        "exportaciones_pdf": 0,
        "exportaciones_pptx": 0,
        "apoyos_accesibilidad": 0,
    }


def obtener_uso_mensual(cliente, docente_id: UUID | str, periodo: str | None = None) -> dict:
    """Obtiene los contadores del mes actual, sin crear filas innecesarias."""
    periodo = periodo or _periodo_actual()
    resultado = (
        cliente.table("uso_mensual_docentes")
        .select("*")
        .eq("docente_id", str(docente_id))
        .eq("periodo", periodo)
        .maybe_single()
        .execute()
    )
    uso = getattr(resultado, "data", None) if resultado else None
    return uso or _uso_vacio(docente_id, periodo)


def _guardar_uso_mensual(cliente, uso: dict) -> dict:
    payload = {
        clave: uso[clave]
        for clave in (
            "clases",
            "imagenes",
            "voces",
            "videos",
            "minutos_grabacion",
            "clonaciones_voz",
            "exportaciones_pdf",
            "exportaciones_pptx",
            "apoyos_accesibilidad",
        )
    }
    payload["actualizado_en"] = datetime.now(timezone.utc).isoformat()

    if uso.get("id"):
        resultado = (
            cliente.table("uso_mensual_docentes")
            .update(payload)
            .eq("id", uso["id"])
            .execute()
        )
        return resultado.data[0] if resultado.data else uso

    nuevo_uso = {
        **_uso_vacio(uso["docente_id"], uso["periodo"]),
        **payload,
    }
    resultado = cliente.table("uso_mensual_docentes").insert(nuevo_uso).execute()
    return resultado.data[0] if resultado.data else nuevo_uso


def _restante_para_plan(uso: dict, plan: PlanRespuesta) -> dict[str, int]:
    limites_dict = plan.cuotas.model_dump()
    restante = {
        clave: max(limites_dict[clave] - int(uso.get(clave, 0)), 0)
        for clave in limites_dict
    }
    return restante


def obtener_uso_docente(cliente, docente_id: UUID, plan_id: PlanId | None = None) -> UsoPlanRespuesta:
    """Devuelve uso mensual real contra el plan actual o indicado."""
    plan_actual = plan_id or obtener_plan_docente(cliente, docente_id)
    plan = obtener_plan(plan_actual)
    uso = obtener_uso_mensual(cliente, docente_id)
    usado = {
        clave: int(uso.get(clave, 0))
        for clave in plan.cuotas.model_dump()
    }

    return UsoPlanRespuesta(
        docente_id=docente_id,
        plan_id=plan_actual,
        usado=usado,
        limites=plan.cuotas,
        restante=_restante_para_plan(uso, plan),
    )


def validar_cupo_docente(
    cliente,
    docente_id: UUID | str,
    consumos: dict[str, int],
) -> None:
    """Corta una accion si excede las cuotas del plan del docente."""
    plan_id = obtener_plan_docente(cliente, docente_id)
    plan = obtener_plan(plan_id)
    uso = obtener_uso_mensual(cliente, docente_id)
    limites = plan.cuotas.model_dump()

    for clave, cantidad in consumos.items():
        if cantidad <= 0:
            continue
        limite = limites.get(clave)
        if limite is None:
            continue
        usado = int(uso.get(clave, 0))
        if usado + cantidad > limite:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Llegaste al limite mensual de {clave} del plan "
                    f"{plan.nombre}. Revisa Mi plan para ampliar tu cupo."
                ),
            )


def registrar_consumo_docente(
    cliente,
    docente_id: UUID | str,
    consumos: dict[str, int],
) -> dict:
    """Suma consumo mensual despues de completar una accion exitosamente."""
    uso = obtener_uso_mensual(cliente, docente_id)
    for clave, cantidad in consumos.items():
        if cantidad > 0:
            uso[clave] = int(uso.get(clave, 0)) + cantidad
    return _guardar_uso_mensual(cliente, uso)
