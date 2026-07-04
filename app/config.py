"""Configuración tipada cargada desde .env vía pydantic-settings.

Base heredada de sofia-pro (misma Supabase `veic`, mismo patrón de settings).
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Entorno ---
    env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8010  # distinto de Sofía (8000) para correr en paralelo local

    # --- LLM ---
    anthropic_api_key: str = ""
    # El agente pedagógico razona sobre planeaciones: modelo capaz por defecto.
    anthropic_model_principal: str = "claude-sonnet-4-6"

    # --- Supabase (MISMA base que Sofía/Panel: veic...) ---
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_db_url: str = ""

    # --- RAG de metodología Maple (pendiente de definir) ---
    # Cuando exista el Sistema RAG compartido, aquí irá su endpoint/config.
    metodologia_rag_url: str = ""

    # --- Admin / seguridad ---
    admin_api_key: str = ""

    # --- Feature flags ---
    enable_prompt_caching: bool = True

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
