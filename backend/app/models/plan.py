"""
Modelos Pydantic para planes, cuotas y capacidades comerciales.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


PlanId = Literal["gratis", "docente", "pro", "institucion"]


class CuotasPlan(BaseModel):
    """Limites mensuales incluidos en cada plan."""

    clases: int
    imagenes: int
    voces: int
    videos: int
    minutos_grabacion: int
    clonaciones_voz: int
    exportaciones_pdf: int
    exportaciones_pptx: int
    apoyos_accesibilidad: int


class CapacidadesPlan(BaseModel):
    """Flags de funciones disponibles por plan."""

    contenido_ia: bool = True
    imagenes_clase: bool = False
    voz_narrada: bool = False
    clonacion_voz: bool = False
    grabacion_docente: bool = False
    video_automatico: bool = False
    apoyos_tdah: bool = False
    apoyos_tea: bool = False
    lectura_facil: bool = False
    soporte_institucional: bool = False


class PlanRespuesta(BaseModel):
    """Descripcion publica de un plan comercial."""

    id: PlanId
    nombre: str
    descripcion: str
    publico_objetivo: str
    precio_referencia_usd: float | None = None
    cuotas: CuotasPlan
    capacidades: CapacidadesPlan


class UsoPlanRespuesta(BaseModel):
    """Uso mensual estimado de un docente contra su plan actual."""

    docente_id: UUID
    plan_id: PlanId
    usado: dict[str, int] = Field(default_factory=dict)
    limites: CuotasPlan
    restante: dict[str, int] = Field(default_factory=dict)
