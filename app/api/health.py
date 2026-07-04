"""Health / readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.adapters.anthropic_client import get_anthropic
from app.adapters.postgres_client import get_postgres
from app.core.metodologia import metodologia_disponible

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@router.get("/readyz")
async def readyz() -> dict[str, object]:
    pg = await get_postgres().health_check()
    anthropic = await get_anthropic().health_check()
    ready = pg["status"] in ("ok", "skip") and anthropic["status"] in ("ok", "skip")
    return {
        "ready": ready,
        "postgres": pg,
        "anthropic": anthropic,
        "metodologia_cargada": metodologia_disponible(),
    }
