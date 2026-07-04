"""Endpoints del Agente Supervisor Académico.

Protegidos con X-Admin-Key (mismo patrón que el /admin de Sofía). El panel
(maple-platform-v3) será el cliente de estos endpoints una vez que el flujo
de captura de planeaciones esté listo.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.core.agente_academico import evaluar_planeacion, procesar_turno
from app.core.repository import get_repository

router = APIRouter(prefix="/academico", tags=["academico"])


def _auth(x_admin_key: str | None) -> None:
    settings = get_settings()
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="No autorizado")


class PlaneacionIn(BaseModel):
    titulo: str
    docente_id: int | None = None
    grado: str | None = None
    materia: str | None = None
    contenido: str | None = None
    archivo_url: str | None = None
    evaluar: bool = False  # si True, el agente la revisa al crearla


class ChatIn(BaseModel):
    mensaje: str
    session_id: str
    docente_id: int | None = None


@router.post("/planeaciones")
async def crear_planeacion(body: PlaneacionIn, x_admin_key: str | None = Header(default=None)) -> dict:
    _auth(x_admin_key)
    repo = get_repository()
    planeacion_id = await repo.crear_planeacion(
        titulo=body.titulo,
        docente_id=body.docente_id,
        grado=body.grado,
        materia=body.materia,
        contenido=body.contenido,
        archivo_url=body.archivo_url,
    )
    resultado: dict = {"planeacion_id": planeacion_id}
    if body.evaluar:
        resultado["evaluacion"] = await evaluar_planeacion(planeacion_id)
    return resultado


@router.post("/planeaciones/{planeacion_id}/evaluar")
async def evaluar(planeacion_id: int, x_admin_key: str | None = Header(default=None)) -> dict:
    _auth(x_admin_key)
    return await evaluar_planeacion(planeacion_id)


@router.post("/chat")
async def chat(body: ChatIn, x_admin_key: str | None = Header(default=None)) -> dict:
    _auth(x_admin_key)
    respuesta = await procesar_turno(body.mensaje, body.session_id, body.docente_id)
    return {"respuesta": respuesta}
