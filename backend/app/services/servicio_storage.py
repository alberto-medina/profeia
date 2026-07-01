"""
Servicio de almacenamiento para recursos del docente.
"""

from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import obtener_configuracion
from app.core.supabase_client import ClienteMemoriaDesarrollo


RUTA_UPLOADS_LOCALES = Path(__file__).resolve().parents[2] / "generated" / "uploads"


def _nombre_seguro(nombre: str) -> str:
    permitido = []
    for caracter in nombre:
        if caracter.isalnum() or caracter in {".", "-", "_"}:
            permitido.append(caracter)
        else:
            permitido.append("-")
    return "".join(permitido).strip("-") or "recurso.bin"


async def guardar_recurso_docente(
    cliente,
    clase_id: UUID,
    nombre_archivo: str,
    contenido: bytes,
    content_type: str | None,
) -> dict:
    """
    Guarda un archivo en Supabase Storage si esta disponible.
    Si el backend esta en modo memoria/local, lo guarda en disco.
    """
    nombre_final = f"{uuid4().hex}-{_nombre_seguro(nombre_archivo)}"
    ruta_storage = f"clases/{clase_id}/{nombre_final}"
    configuracion = obtener_configuracion()

    def guardar_local() -> dict:
        carpeta = RUTA_UPLOADS_LOCALES / str(clase_id)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_local = carpeta / nombre_final
        ruta_local.write_bytes(contenido)
        return {
            "url": str(ruta_local),
            "path": str(ruta_local),
            "bucket": "local",
            "modo": "local",
        }

    if isinstance(cliente, ClienteMemoriaDesarrollo) or not hasattr(cliente, "storage"):
        return guardar_local()

    bucket = configuracion.supabase_storage_bucket
    try:
        cliente.storage.from_(bucket).upload(
            ruta_storage,
            contenido,
            file_options={
                "content-type": content_type or "application/octet-stream",
                "upsert": "true",
            },
        )
        url_publica = cliente.storage.from_(bucket).get_public_url(ruta_storage)
        return {
            "url": url_publica,
            "path": ruta_storage,
            "bucket": bucket,
            "modo": "supabase",
        }
    except Exception as error:
        print(
            "[servicio_storage] No se pudo subir a Storage; "
            f"guardando local. Detalle: {error}"
        )
        return guardar_local()
