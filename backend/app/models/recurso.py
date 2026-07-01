"""
Modelos Pydantic (schemas) para recursos generados (voz, imagen, slide, etc).
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


TipoRecurso = Literal["voz", "imagen", "slide", "video", "pdf", "pptx", "zip", "audio_docente"]


class SolicitudGenerarVoz(BaseModel):
    """Parametros para generar el audio narrado de una clase."""

    voz: Literal["clonada", "masculina", "femenina", "infantil"] = "femenina"
    idioma: str = "es"
    velocidad: float = 0.9


class SolicitudGenerarImagenes(BaseModel):
    """Parametros para generar imagenes de apoyo de una clase."""

    cantidad: int = 3
    estilo: Optional[str] = None


class SolicitudAdjuntarRecurso(BaseModel):
    """Recurso externo subido o vinculado por el docente."""

    tipo: Literal["imagen", "audio_docente"]
    nombre: str
    url_storage: str
    descripcion: Optional[str] = None


class PaqueteAlumnoRespuesta(BaseModel):
    """Material listo para una vista de estudiante."""

    clase_id: UUID
    codigo_publico: Optional[str] = None
    titulo: str
    introduccion: str = ""
    explicacion: str = ""
    ejemplos: list[str] = []
    actividad: str = ""
    preguntas: list[str] = []
    resumen: str
    cuestionario: list[str] = []
    tarea_hogar: Optional[str] = None
    audio_resumen: Optional[dict] = None
    imagenes: list[dict] = []
    audios_docente: list[dict] = []
    apoyos: Optional[dict] = None


class RecursoGeneradoRespuesta(BaseModel):
    """Lo que el backend devuelve tras generar (o consultar) un recurso."""

    id: UUID
    clase_id: UUID
    tipo: TipoRecurso
    url_storage: str
    metadata_json: Optional[dict] = None
    creado_en: datetime
