"""
Modelos para apoyos pedagogicos de accesibilidad.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


NecesidadApoyo = Literal[
    "tdah",
    "tea",
    "lectura_facil",
    "ansiedad",
    "dificultad_lectora",
    "baja_vision",
]


class SolicitudApoyosAccesibilidad(BaseModel):
    """Pedido del docente para adaptar una clase."""

    necesidades: list[NecesidadApoyo] = Field(default_factory=list)
    incluir_rutina_visual: bool = True
    incluir_pausas: bool = True
    incluir_consignas_cortas: bool = True
    nivel_apoyo: Literal["leve", "medio", "alto"] = "medio"


class ApoyosAccesibilidad(BaseModel):
    """Adaptaciones educativas sugeridas para una clase."""

    resumen_docente: str
    consigna_simple: str
    rutina_visual: list[str] = Field(default_factory=list)
    pausas_sugeridas: list[str] = Field(default_factory=list)
    adaptaciones: list[str] = Field(default_factory=list)
    apoyos_sensoriales: list[str] = Field(default_factory=list)
    verificacion_comprension: list[str] = Field(default_factory=list)
    evaluacion_flexible: list[str] = Field(default_factory=list)


class ApoyoAccesibilidadRespuesta(BaseModel):
    """Respuesta persistida de apoyos generados."""

    id: UUID
    clase_id: UUID
    docente_id: UUID
    necesidades: list[NecesidadApoyo]
    apoyo_json: ApoyosAccesibilidad
    creado_en: datetime
