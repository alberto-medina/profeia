"""
Cliente Supabase compartido por todo el backend.
Usa la service_role_key porque las llamadas pasan por el backend, no
directamente desde el cliente final. El frontend Kivy nunca debe usar la
service_role_key, solo la anon_key si llega a necesitar acceso directo.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from supabase import create_client, Client

from app.core.config import obtener_configuracion

_cliente: Client | "ClienteMemoriaDesarrollo" | None = None
RUTA_DB_DESARROLLO = Path(__file__).resolve().parents[2] / "generated" / "dev_db.json"
TABLAS_DESARROLLO = {
    "docentes": [],
    "clases": [],
    "recursos_generados": [],
    "apoyos_accesibilidad": [],
    "suscripciones_docentes": [],
    "uso_mensual_docentes": [],
}


class ConsultaMemoriaDesarrollo:
    """Subset minimo del query builder de Supabase para desarrollo local."""

    def __init__(self, cliente: "ClienteMemoriaDesarrollo", nombre_tabla: str):
        self.cliente = cliente
        self.nombre_tabla = nombre_tabla
        self.operacion = "select"
        self.payload: dict | None = None
        self.filtros: list[tuple[str, str]] = []
        self.orden_columna: str | None = None
        self.orden_desc = False
        self.devolver_unico = False

    def select(self, columnas: str):
        _ = columnas
        self.operacion = "select"
        return self

    def insert(self, payload: dict):
        self.operacion = "insert"
        self.payload = payload
        return self

    def update(self, payload: dict):
        self.operacion = "update"
        self.payload = payload
        return self

    def delete(self):
        self.operacion = "delete"
        return self

    def eq(self, columna: str, valor: str):
        self.filtros.append((columna, valor))
        return self

    def order(self, columna: str, desc: bool = False):
        self.orden_columna = columna
        self.orden_desc = desc
        return self

    def maybe_single(self):
        self.devolver_unico = True
        return self

    def execute(self):
        if self.operacion == "insert":
            return SimpleNamespace(data=[self._insertar()])
        if self.operacion == "update":
            return SimpleNamespace(data=self._actualizar())
        if self.operacion == "delete":
            return SimpleNamespace(data=self._eliminar())

        registros = self._seleccionar()
        if self.devolver_unico:
            return SimpleNamespace(data=registros[0] if registros else None)
        return SimpleNamespace(data=registros)

    def _seleccionar(self) -> list[dict]:
        registros = [
            deepcopy(registro)
            for registro in self.cliente.tablas.setdefault(self.nombre_tabla, [])
        ]

        for columna, valor in self.filtros:
            registros = [
                registro
                for registro in registros
                if str(registro.get(columna)) == str(valor)
            ]

        if self.orden_columna:
            registros.sort(
                key=lambda registro: registro.get(self.orden_columna) or "",
                reverse=self.orden_desc,
            )

        return registros

    def _insertar(self) -> dict:
        ahora = datetime.now(timezone.utc).isoformat()
        registro = deepcopy(self.payload or {})
        registro.setdefault("id", str(uuid4()))

        if self.nombre_tabla in {"clases", "docentes", "suscripciones_docentes"}:
            registro.setdefault("creado_en", ahora)
            registro.setdefault("actualizado_en", ahora)
        elif self.nombre_tabla in {"recursos_generados", "apoyos_accesibilidad"}:
            registro.setdefault("creado_en", ahora)
        elif self.nombre_tabla == "uso_mensual_docentes":
            registro.setdefault("actualizado_en", ahora)

        self.cliente.tablas.setdefault(self.nombre_tabla, []).append(registro)
        self.cliente.guardar()
        return deepcopy(registro)

    def _actualizar(self) -> list[dict]:
        registros_actualizados = []
        payload = deepcopy(self.payload or {})

        if self.nombre_tabla == "clases":
            payload["actualizado_en"] = datetime.now(timezone.utc).isoformat()

        for registro in self.cliente.tablas.setdefault(self.nombre_tabla, []):
            coincide = all(
                str(registro.get(columna)) == str(valor)
                for columna, valor in self.filtros
            )
            if coincide:
                registro.update(payload)
                registros_actualizados.append(deepcopy(registro))

        if registros_actualizados:
            self.cliente.guardar()
        return registros_actualizados

    def _eliminar(self) -> list[dict]:
        registros_restantes = []
        registros_eliminados = []

        for registro in self.cliente.tablas.setdefault(self.nombre_tabla, []):
            coincide = all(
                str(registro.get(columna)) == str(valor)
                for columna, valor in self.filtros
            )
            if coincide:
                registros_eliminados.append(deepcopy(registro))
            else:
                registros_restantes.append(registro)

        if registros_eliminados:
            self.cliente.tablas[self.nombre_tabla] = registros_restantes
            self.cliente.guardar()
        return registros_eliminados


class ClienteMemoriaDesarrollo:
    """Cliente local para probar el flujo sin Supabase ni red externa."""

    def __init__(self):
        self.ruta_db = RUTA_DB_DESARROLLO
        self.tablas: dict[str, list[dict]] = deepcopy(TABLAS_DESARROLLO)
        self.cargar()

    def table(self, nombre_tabla: str) -> ConsultaMemoriaDesarrollo:
        return ConsultaMemoriaDesarrollo(self, nombre_tabla)

    def cargar(self) -> None:
        """Carga datos persistidos del modo desarrollo si existen."""
        if not self.ruta_db.exists():
            return
        try:
            datos = json.loads(self.ruta_db.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return

        for nombre_tabla, valor_inicial in TABLAS_DESARROLLO.items():
            registros = datos.get(nombre_tabla, valor_inicial)
            self.tablas[nombre_tabla] = registros if isinstance(registros, list) else []

    def guardar(self) -> None:
        """Persiste el estado local para no perderlo al reiniciar backend."""
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_db.write_text(
            json.dumps(self.tablas, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _valor_configurado(valor: str) -> bool:
    """Indica si una variable tiene un valor real y no el placeholder del ejemplo."""
    valor_limpio = valor.strip()
    if not valor_limpio:
        return False
    return not valor_limpio.startswith("TU_") and "TU-PROYECTO" not in valor_limpio


def obtener_cliente_supabase() -> Client | ClienteMemoriaDesarrollo:
    """Devuelve una instancia unica (singleton) del cliente Supabase."""
    global _cliente
    if _cliente is None:
        configuracion = obtener_configuracion()
        credenciales_supabase = _valor_configurado(
            configuracion.supabase_url
        ) and _valor_configurado(configuracion.supabase_service_role_key)

        if not credenciales_supabase:
            if configuracion.entorno == "desarrollo":
                _cliente = ClienteMemoriaDesarrollo()
                return _cliente
            raise RuntimeError(
                "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el archivo .env"
            )
        _cliente = create_client(
            configuracion.supabase_url,
            configuracion.supabase_service_role_key,
        )
    return _cliente
