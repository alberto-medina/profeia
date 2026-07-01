"""
Valida el flujo principal de ProfeIA en modo local, sin Supabase real ni IA paga.

Uso:
    python scripts/validar_flujo_local.py
    python scripts/validar_flujo_local.py --web

Por defecto genera imagenes locales deterministicas. Con --web intenta usar
Wikimedia Commons y cae a fallback local si no hay internet o no hay resultados.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def _forzar_modo_local() -> None:
    os.environ["SUPABASE_URL"] = ""
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
    os.environ["IA_CONTENIDO_API_KEY"] = ""
    os.environ["IA_IMAGENES_API_KEY"] = ""
    os.environ["IA_VOZ_API_KEY"] = ""
    os.environ["IA_VOZ_CLONADA_API_KEY"] = ""
    os.environ["ENTORNO"] = "desarrollo"


def _assert(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise AssertionError(mensaje)


def _insertar_docente_demo(cliente) -> UUID:
    docente_id = uuid4()
    cliente.table("docentes").insert(
        {
            "id": str(docente_id),
            "email": f"validacion-{docente_id.hex[:8]}@profeia.local",
            "nombre": "Docente validacion",
            "password_hash": "validacion-local",
            "plan": "pro",
        }
    ).execute()
    return docente_id


async def validar_flujo(usar_web: bool) -> None:
    _forzar_modo_local()

    from app.core.supabase_client import obtener_cliente_supabase
    from app.models.clase import SolicitudCrearClase
    from app.models.recurso import SolicitudGenerarImagenes
    from app.routers.clases import crear_clase
    from app.routers.exportacion import exportar_clase_pdf, exportar_clase_zip
    from app.routers.multimedia import (
        buscar_imagenes_web_clase,
        construir_paquete_alumno,
        generar_imagenes_clase,
    )
    from app.routers.publico import obtener_clase_publica

    cliente = obtener_cliente_supabase()
    docente_id = _insertar_docente_demo(cliente)

    solicitud = SolicitudCrearClase(
        prompt_original="futbol pases y tiros con ejemplos practicos",
        duracion_minutos=8,
        edad_publico="10 anos",
        materia="Educacion Fisica",
    )
    clase = await crear_clase(solicitud, docente_id=docente_id)
    clase_id = UUID(str(clase["id"]))
    contenido = clase["contenido_json"]

    _assert(clase.get("codigo_publico"), "La clase no genero codigo publico")
    _assert("futbol" in contenido["titulo"].lower(), "El titulo no conserva el tema")
    _assert(contenido.get("explicacion"), "La clase no tiene explicacion")
    _assert(contenido.get("ejemplos"), "La clase no tiene ejemplos")
    _assert(contenido.get("cuestionario"), "La clase no tiene cuestionario")

    if usar_web:
        recursos_imagen = await buscar_imagenes_web_clase(clase_id, cantidad=2)
    else:
        recursos_imagen = await generar_imagenes_clase(
            clase_id,
            SolicitudGenerarImagenes(cantidad=2, estilo="lamina educativa"),
        )
    _assert(len(recursos_imagen) >= 1, "No se generaron recursos de imagen")

    paquete = construir_paquete_alumno(cliente, clase)
    _assert(paquete.codigo_publico == clase["codigo_publico"], "El paquete alumno no conserva codigo")
    _assert(paquete.explicacion, "La vista alumno no tiene explicacion")
    _assert(paquete.imagenes, "La vista alumno no incluye imagenes")

    paquete_publico = await obtener_clase_publica(str(clase["codigo_publico"]))
    _assert(paquete_publico.clase_id == clase_id, "El codigo publico no devuelve la clase correcta")

    recurso_pdf = await exportar_clase_pdf(clase_id)
    ruta_pdf = Path(recurso_pdf["url_storage"])
    _assert(ruta_pdf.exists(), f"No existe el PDF exportado: {ruta_pdf}")

    recurso_zip = await exportar_clase_zip(clase_id)
    ruta_zip = Path(recurso_zip["url_storage"])
    _assert(ruta_zip.exists(), f"No existe el ZIP exportado: {ruta_zip}")

    print("Validacion local OK")
    print(f"Clase: {clase_id}")
    print(f"Codigo alumno: {clase['codigo_publico']}")
    print(f"PDF: {ruta_pdf}")
    print(f"ZIP: {ruta_zip}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida el flujo local de ProfeIA.")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Intenta buscar imagenes gratis en Wikimedia antes del fallback local.",
    )
    args = parser.parse_args()
    asyncio.run(validar_flujo(usar_web=args.web))


if __name__ == "__main__":
    main()
