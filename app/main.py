"""Entrypoint FastAPI del Agente Supervisor Académico.

Arranca local: `uv run uvicorn app.main:app --reload --port 8010`
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.adapters.postgres_client import get_postgres
from app.api.academico import router as academico_router
from app.api.health import router as health_router
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info("starting agente-academico v%s (%s)", __version__, settings.env)
    pg = get_postgres()
    if pg.is_configured():
        try:
            await pg.connect()
        except Exception as exc:  # noqa: BLE001
            log.warning("postgres connection failed at startup: %s", exc)
    yield
    await pg.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agente Supervisor Académico — Maple Collège",
        version=__version__,
        description="Mentor pedagógico de docentes: revisa planeaciones y da retroalimentación.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    app.include_router(health_router)
    app.include_router(academico_router)
    return app


app = create_app()
