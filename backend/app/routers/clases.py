"""
Router de clases: creacion desde prompt, listado, detalle y edicion.
"""

import secrets
import string
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.supabase_client import obtener_cliente_supabase
from app.models.clase import (
    ClaseRespuesta,
    SolicitudCrearClase,
    SolicitudEditarClase,
)
from app.services.servicio_contenido import generar_contenido_pedagogico
from app.services.servicio_planes import registrar_consumo_docente, validar_cupo_docente

router = APIRouter(prefix="/clases", tags=["clases"])


def _generar_codigo_publico(longitud: int = 6) -> str:
    alfabeto = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(longitud))


def _codigo_disponible(cliente, codigo: str) -> bool:
    resultado = (
        cliente.table("clases")
        .select("*")
        .eq("codigo_publico", codigo)
        .maybe_single()
        .execute()
    )
    datos = getattr(resultado, "data", None) if resultado else None
    return not datos


def _generar_codigo_unico(cliente) -> str:
    for _ in range(10):
        codigo = _generar_codigo_publico()
        if _codigo_disponible(cliente, codigo):
            return codigo
    raise RuntimeError("No se pudo generar un codigo publico unico")


@router.post("", response_model=ClaseRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_clase(solicitud: SolicitudCrearClase, docente_id: UUID):
    """
    Crea una clase nueva a partir de un prompt y genera el contenido
    pedagogico completo usando el servicio de IA configurado.
    """
    cliente = obtener_cliente_supabase()
    validar_cupo_docente(cliente, docente_id, {"clases": 1})
    contenido = await generar_contenido_pedagogico(solicitud)
    codigo_publico = _generar_codigo_unico(cliente)
    nueva_clase = {
        "docente_id": str(docente_id),
        "titulo": contenido.titulo,
        "prompt_original": solicitud.prompt_original,
        "duracion_minutos": solicitud.duracion_minutos,
        "edad_publico": solicitud.edad_publico,
        "materia": solicitud.materia,
        "contenido_json": contenido.model_dump(),
        "codigo_publico": codigo_publico,
        "estado": "generada",
    }

    resultado = cliente.table("clases").insert(nueva_clase).execute()

    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear la clase",
        )

    registrar_consumo_docente(cliente, docente_id, {"clases": 1})
    return resultado.data[0]


@router.get("", response_model=list[ClaseRespuesta])
async def listar_clases(docente_id: UUID):
    """Lista todas las clases de un docente, ordenadas por fecha descendente."""
    cliente = obtener_cliente_supabase()
    resultado = (
        cliente.table("clases")
        .select("*")
        .eq("docente_id", str(docente_id))
        .order("creado_en", desc=True)
        .execute()
    )
    return resultado.data or []


@router.get("/{clase_id}", response_model=ClaseRespuesta)
async def obtener_clase(clase_id: UUID):
    """Devuelve el detalle de una clase puntual."""
    cliente = obtener_cliente_supabase()
    resultado = (
        cliente.table("clases")
        .select("*")
        .eq("id", str(clase_id))
        .maybe_single()
        .execute()
    )

    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

    return resultado.data


@router.put("/{clase_id}", response_model=ClaseRespuesta)
async def editar_clase(clase_id: UUID, solicitud: SolicitudEditarClase):
    """Guarda la edicion manual que hizo el docente sobre el contenido generado."""
    cliente = obtener_cliente_supabase()

    actualizacion = {
        "contenido_json": solicitud.contenido_json.model_dump(),
        "estado": "editada",
    }

    resultado = (
        cliente.table("clases")
        .update(actualizacion)
        .eq("id", str(clase_id))
        .execute()
    )

    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

    return resultado.data[0]
