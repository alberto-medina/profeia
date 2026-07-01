"""
Modelos para entrada segura de docentes en el MVP local.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SolicitudRegistroDocente(BaseModel):
    """Datos necesarios para crear una cuenta docente local."""

    nombre: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    materia_principal: Optional[str] = None


class SolicitudLoginDocente(BaseModel):
    """Credenciales del docente."""

    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=1)


class SolicitudEliminarDocente(BaseModel):
    """Confirmacion requerida para eliminar una cuenta docente."""

    docente_id: UUID
    password: str = Field(..., min_length=1)


class DocenteSesionRespuesta(BaseModel):
    """Perfil minimo que el frontend guarda tras iniciar sesion."""

    id: UUID
    auth_user_id: UUID
    nombre: str
    email: str
    materia_principal: Optional[str] = None
    plan: str = "gratis"
    creado_en: Optional[datetime] = None
