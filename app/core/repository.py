"""Acceso a datos del Agente Supervisor Académico.

Tablas (creadas en migrations/001_schema_academico.sql, en la Supabase `veic`):
  docentes, planeaciones, revisiones_academicas, academico_mensajes.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.adapters.postgres_client import get_postgres

log = logging.getLogger(__name__)


class AcademicoRepository:
    def __init__(self) -> None:
        self.pg = get_postgres()

    # --- Docentes ---
    async def get_docente(self, docente_id: int) -> dict[str, Any] | None:
        row = await self.pg.fetch_one("SELECT * FROM docentes WHERE id = $1", docente_id)
        return dict(row) if row else None

    async def upsert_docente(self, nombre: str, email: str | None = None, area: str | None = None) -> int:
        row = await self.pg.fetch_one(
            """
            INSERT INTO docentes (nombre, email, area)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            nombre,
            email,
            area,
        )
        return int(row["id"])  # type: ignore[index]

    # --- Planeaciones ---
    async def crear_planeacion(
        self,
        titulo: str,
        docente_id: int | None = None,
        grado: str | None = None,
        materia: str | None = None,
        contenido: str | None = None,
        archivo_url: str | None = None,
    ) -> int:
        row = await self.pg.fetch_one(
            """
            INSERT INTO planeaciones (docente_id, titulo, grado, materia, contenido, archivo_url)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            docente_id,
            titulo,
            grado,
            materia,
            contenido,
            archivo_url,
        )
        return int(row["id"])  # type: ignore[index]

    async def get_planeacion(self, planeacion_id: int) -> dict[str, Any] | None:
        row = await self.pg.fetch_one("SELECT * FROM planeaciones WHERE id = $1", planeacion_id)
        return dict(row) if row else None

    async def marcar_planeacion_revisada(self, planeacion_id: int) -> None:
        await self.pg.execute(
            "UPDATE planeaciones SET estado = 'revisada' WHERE id = $1", planeacion_id
        )

    # --- Revisiones (la retroalimentación del agente) ---
    async def guardar_revision(
        self,
        planeacion_id: int,
        retroalimentacion: str,
        alineacion_pct: int | None = None,
        sugerencias: list[str] | None = None,
        model_used: str | None = None,
    ) -> int:
        row = await self.pg.fetch_one(
            """
            INSERT INTO revisiones_academicas
                (planeacion_id, retroalimentacion, alineacion_pct, sugerencias, model_used)
            VALUES ($1, $2, $3, $4::jsonb, $5)
            RETURNING id
            """,
            planeacion_id,
            retroalimentacion,
            alineacion_pct,
            json.dumps(sugerencias or []),
            model_used,
        )
        return int(row["id"])  # type: ignore[index]

    # --- Chat docente ↔ agente ---
    async def guardar_mensaje(
        self, session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        await self.pg.execute(
            """
            INSERT INTO academico_mensajes (session_id, role, content, metadata)
            VALUES ($1, $2, $3, $4::jsonb)
            """,
            session_id,
            role,
            content,
            json.dumps(metadata or {}),
        )

    async def historial(self, session_id: str, limite: int = 20) -> list[dict[str, Any]]:
        rows = await self.pg.fetch_all(
            """
            SELECT role, content FROM academico_mensajes
            WHERE session_id = $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            session_id,
            limite,
        )
        return [dict(r) for r in rows]


_singleton: AcademicoRepository | None = None


def get_repository() -> AcademicoRepository:
    global _singleton
    if _singleton is None:
        _singleton = AcademicoRepository()
    return _singleton
