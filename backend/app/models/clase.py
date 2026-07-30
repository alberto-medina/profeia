"""
Modelos Pydantic (schemas) para clases y contenido pedagogico.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


DuracionMinutos = Literal[3, 5, 8, 15]

EstadoClase = Literal["borrador", "generada", "editada", "finalizada"]


class ContenidoPedagogico(BaseModel):
    """Estructura del contenido generado por la IA para una clase."""

    titulo: str
    objetivo: str
    introduccion: str
    explicacion: str
    ejemplos: list[str] = Field(default_factory=list)
    actividad: str
    preguntas: list[str] = Field(default_factory=list)
    cuestionario: list[str] = Field(default_factory=list)
    tarea_hogar: Optional[str] = None
    resumen: str
    sugerencia_imagen: Optional[str] = None


class SolicitudCrearClase(BaseModel):
    """Lo que el frontend envia para crear una clase nueva."""

    prompt_original: str = Field(..., min_length=5)
    duracion_minutos: DuracionMinutos
    edad_publico: str
    materia: str


class ClaseRespuesta(BaseModel):
    """Lo que el backend devuelve al frontend tras crear/consultar una clase."""

    id: UUID
    docente_id: UUID
    titulo: Optional[str] = None
    prompt_original: str
    duracion_minutos: int
    edad_publico: Optional[str] = None
    materia: Optional[str] = None
    contenido_json: Optional[ContenidoPedagogico] = None
    codigo_publico: Optional[str] = None
    estado: EstadoClase
    creado_en: datetime
    actualizado_en: datetime


class SolicitudEditarClase(BaseModel):
    """Edicion manual del contenido pedagogico por parte del docente."""

    contenido_json: ContenidoPedagogico
