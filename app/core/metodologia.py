"""Metodología Maple — la base de conocimiento contra la que el agente evalúa.

⚠️  PIEZA BLOQUEANTE (pregunta crítica #1 de DEFINICION_Agente_Academico.md):
    ¿Existe la metodología Maple documentada (modelo BEAR, principios pedagógicos)
    para cargarla al RAG? Hasta que Cecilia entregue ese material, esta capa es un
    PLACEHOLDER. El resto del andamiaje (API, DB, loop del agente, tono) ya funciona;
    solo falta enchufar aquí el contenido real.

Cuando llegue la metodología, hay dos caminos:
  A) Documento acotado (<~15k tokens): se cachea como bloque de system, igual que
     la KB de Sofía. Rellenar `metodologia_texto()`.
  B) Corpus grande: Sistema RAG compartido (embeddings + retrieval). Rellenar
     `buscar_metodologia()` con la llamada al RAG (settings.metodologia_rag_url).
"""

from __future__ import annotations

# TODO(metodología): reemplazar por el texto real de la metodología Maple.
_PLACEHOLDER = (
    "La metodología Maple aún no está cargada. "
    "El agente debe dar retroalimentación pedagógica general de buenas prácticas "
    "y aclarar explícitamente que la evaluación contra la metodología Maple estará "
    "disponible cuando la dirección académica entregue el material."
)


def metodologia_disponible() -> bool:
    """¿Ya tenemos el contenido real de la metodología cargado?"""
    return False


def metodologia_texto() -> str:
    """Texto de la metodología para cachear como bloque de system (camino A).

    Mientras `metodologia_disponible()` sea False, devuelve el placeholder que
    obliga al agente a ser honesto sobre la limitación.
    """
    return _PLACEHOLDER


async def buscar_metodologia(consulta: str, k: int = 5) -> list[str]:
    """Retrieval contra el RAG de la metodología (camino B). Stub por ahora."""
    return []
