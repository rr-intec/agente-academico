"""Cliente Anthropic con soporte de prompt caching y health check.

Copia de la base probada de sofia-pro/app/adapters/anthropic_client.py.
"""

from __future__ import annotations

import logging
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import Message

from app.config import Settings, get_settings

log = logging.getLogger(__name__)


class AnthropicAdapter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: AsyncAnthropic | None = None

    @property
    def client(self) -> AsyncAnthropic:
        if self._client is None:
            if not self.settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY no está configurada.")
            self._client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        return self._client

    def is_configured(self) -> bool:
        return bool(self.settings.anthropic_api_key)

    async def chat(
        self,
        system_blocks: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.4,
    ) -> Message:
        kwargs: dict[str, Any] = {
            "model": model or self.settings.anthropic_model_principal,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_blocks,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        return await self.client.messages.create(**kwargs)

    async def health_check(self) -> dict[str, Any]:
        if not self.is_configured():
            return {"status": "skip", "detail": "no api key configured"}
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as http:
                resp = await http.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": self.settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
            if resp.status_code == 200:
                return {"status": "ok"}
            if resp.status_code in (401, 403):
                return {"status": "unauthorized", "detail": f"HTTP {resp.status_code}"}
            return {"status": "unreachable", "detail": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"status": "unreachable", "detail": str(exc)}


_singleton: AnthropicAdapter | None = None


def get_anthropic() -> AnthropicAdapter:
    global _singleton
    if _singleton is None:
        _singleton = AnthropicAdapter()
    return _singleton
