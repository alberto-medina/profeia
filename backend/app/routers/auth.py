"""
Router de autenticacion y perfil de docente.

La autenticacion delega en Supabase Auth: el frontend Kivy llama
directamente a Supabase Auth (signUp / signInWithPassword) usando la
anon_key, y luego envia el token resultante al backend en el header
Authorization para las llamadas que requieren identificar al docente.

Este router expone el perfil del docente, que SI vive en nuestra propia
tabla 'docentes' (no en Supabase Auth).
"""

import hashlib
import hmac
import secrets
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.core.supabase_client import obtener_cliente_supabase
from app.models.auth import (
    DocenteSesionRespuesta,
    SolicitudEliminarDocente,
    SolicitudLoginDocente,
    SolicitudRegistroDocente,
)

router = APIRouter(prefix="/perfil", tags=["perfil"])


def _normalizar_email(email: str) -> str:
    return email.strip().lower()


def _crear_hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def _password_valida(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        algoritmo, salt, digest_guardado = password_hash.split("$", 2)
    except ValueError:
        return False
    if algoritmo != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return hmac.compare_digest(digest, digest_guardado)


def _buscar_docente_por_email(cliente, email: str) -> dict | None:
    resultado = (
        cliente.table("docentes")
        .select("*")
        .eq("email", _normalizar_email(email))
        .maybe_single()
        .execute()
    )
    return getattr(resultado, "data", None) if resultado else None


def _buscar_docente_por_id(cliente, docente_id: str) -> dict | None:
    resultado = (
        cliente.table("docentes")
        .select("*")
        .eq("id", str(docente_id))
        .maybe_single()
        .execute()
    )
    return getattr(resultado, "data", None) if resultado else None


def _eliminar_datos_docente(cliente, docente_id: str) -> None:
    clases = (
        cliente.table("clases")
        .select("*")
        .eq("docente_id", str(docente_id))
        .execute()
        .data
        or []
    )
    for clase in clases:
        cliente.table("recursos_generados").delete().eq("clase_id", clase["id"]).execute()

    cliente.table("apoyos_accesibilidad").delete().eq("docente_id", str(docente_id)).execute()
    cliente.table("suscripciones_docentes").delete().eq("docente_id", str(docente_id)).execute()
    cliente.table("uso_mensual_docentes").delete().eq("docente_id", str(docente_id)).execute()
    cliente.table("clases").delete().eq("docente_id", str(docente_id)).execute()
    cliente.table("docentes").delete().eq("id", str(docente_id)).execute()


@router.post("/registro", response_model=DocenteSesionRespuesta, status_code=status.HTTP_201_CREATED)
async def registrar_docente(solicitud: SolicitudRegistroDocente):
    """
    Crea una cuenta docente para el MVP local.

    En produccion este flujo se reemplaza por Supabase Auth; el backend mantiene
    el perfil docente y nunca deberia recibir la clave en texto plano.
    """
    cliente = obtener_cliente_supabase()
    email = _normalizar_email(solicitud.email)

    if _buscar_docente_por_email(cliente, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta docente con ese email",
        )

    nuevo_docente = {
        "auth_user_id": str(uuid4()),
        "nombre": solicitud.nombre.strip(),
        "email": email,
        "materia_principal": solicitud.materia_principal,
        "password_hash": _crear_hash_password(solicitud.password),
        "plan": "gratis",
    }
    resultado = cliente.table("docentes").insert(nuevo_docente).execute()
    docente = resultado.data[0] if resultado.data else nuevo_docente
    return docente


@router.post("/login", response_model=DocenteSesionRespuesta)
async def iniciar_sesion_docente(solicitud: SolicitudLoginDocente):
    """Valida credenciales y devuelve el perfil docente."""
    cliente = obtener_cliente_supabase()
    docente = _buscar_docente_por_email(cliente, solicitud.email)
    if not docente or not _password_valida(solicitud.password, docente.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o clave incorrectos",
        )
    return docente


@router.post("/eliminar", status_code=status.HTTP_200_OK)
async def eliminar_cuenta_docente(solicitud: SolicitudEliminarDocente):
    """
    Elimina la cuenta docente del MVP local.

    Requiere la clave actual y borra el perfil junto con sus clases y recursos
    asociados. Cuando se migre a Supabase Auth real, este endpoint tambien
    debera eliminar/desactivar el usuario de Auth.
    """
    cliente = obtener_cliente_supabase()
    docente = _buscar_docente_por_id(cliente, str(solicitud.docente_id))
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta docente no encontrada",
        )
    if not _password_valida(solicitud.password, docente.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave incorrecta. No se elimino la cuenta.",
        )

    _eliminar_datos_docente(cliente, str(solicitud.docente_id))
    return {"eliminada": True}


@router.get("")
async def obtener_perfil(auth_user_id: str):
    """
    Devuelve el perfil del docente asociado a un auth_user_id de Supabase.

    NOTA: en una implementacion completa, auth_user_id se extrae del token
    JWT enviado en el header Authorization (via una dependencia de FastAPI),
    no como query param. Se deja explicito como query param en este
    esqueleto para simplificar las pruebas iniciales.
    """
    cliente = obtener_cliente_supabase()
    resultado = (
        cliente.table("docentes")
        .select("*")
        .eq("auth_user_id", auth_user_id)
        .maybe_single()
        .execute()
    )

    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontro un perfil de docente para este usuario",
        )

    return resultado.data


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_perfil(
    auth_user_id: str,
    nombre: str,
    email: str,
    materia_principal: str | None = None,
):
    """Crea el perfil de docente luego de registrarse en Supabase Auth."""
    cliente = obtener_cliente_supabase()

    nuevo_docente = {
        "auth_user_id": auth_user_id,
        "nombre": nombre,
        "email": email,
        "materia_principal": materia_principal,
    }

    resultado = cliente.table("docentes").insert(nuevo_docente).execute()
    return resultado.data[0] if resultado.data else nuevo_docente
