"""Loop del Agente Supervisor Académico (mentor pedagógico de docentes).

Misma arquitectura que Sofía (app/core/agente.py): modelo = conversación,
tools = datos. El agente conversa con el DOCENTE, y usa tools para leer/guardar
planeaciones y revisiones en la base. La EVALUACIÓN contra la metodología Maple
depende de app/core/metodologia.py (hoy placeholder — ver ese archivo).

Estado: andamiaje funcional. La lógica de evaluación queda deliberadamente
apoyada en el placeholder de metodología hasta que Cecilia entregue el material.
"""

from __future__ import annotations

import logging
from typing import Any

from app.adapters.anthropic_client import get_anthropic
from app.core.metodologia import metodologia_disponible, metodologia_texto
from app.core.repository import get_repository

log = logging.getLogger(__name__)

SYSTEM_RULES = """Eres el Agente Supervisor Académico de Maple Collège: un MENTOR PEDAGÓGICO
para los DOCENTES (maestros). Tu trabajo es acompañarlos: revisar sus PLANEACIONES de
clase, darles retroalimentación pedagógica concreta y accionable, y responder sus dudas
sobre cómo aplicar mejor la metodología Maple.

PRINCIPIOS (no negociables):
- Acompañas, no fiscalizas. Tu tono es el de un colega experto y respetuoso, nunca el de
  un supervisor que califica. El maestro debe sentir apoyo, no vigilancia.
- NO trabajas con alumnos: no ves calificaciones, asistencia ni conducta de estudiantes.
  Tu único objeto son las planeaciones y la práctica docente.
- La decisión final es humana. Tu retroalimentación es una SUGERENCIA que la dirección
  académica revisa y aprueba/ajusta antes de llegar al maestro.
- Datos siempre desde las tools. Nunca inventes el contenido de una planeación ni citas
  de la metodología: léelos con las tools.
- Sé concreto: en vez de "mejora los objetivos", di qué objetivo y cómo reformularlo.

Hablas español de México, con voseo NO (usa "tú"), cálido y profesional."""

_METODOLOGIA_NO_DISPONIBLE = """
[LIMITACIÓN ACTUAL] La metodología Maple todavía no está cargada en tu base de
conocimiento. Por eso NO puedes evaluar formalmente contra el modelo Maple. Sé honesto
sobre esto con el docente: ofrece retroalimentación de buenas prácticas pedagógicas
generales y aclara que la evaluación alineada a la metodología Maple estará disponible
cuando la dirección académica entregue el material."""


def _build_system_blocks() -> list[dict[str, Any]]:
    """Bloques de system con caching: reglas + metodología (o aviso de limitación)."""
    blocks: list[dict[str, Any]] = [
        {"type": "text", "text": SYSTEM_RULES, "cache_control": {"type": "ephemeral"}},
    ]
    metodologia = metodologia_texto()
    if metodologia_disponible():
        blocks.append(
            {
                "type": "text",
                "text": f"METODOLOGÍA MAPLE (base de evaluación):\n\n{metodologia}",
                "cache_control": {"type": "ephemeral"},
            }
        )
    else:
        blocks.append({"type": "text", "text": _METODOLOGIA_NO_DISPONIBLE})
    return blocks


# --- Tools expuestas al modelo ---
TOOLS: list[dict[str, Any]] = [
    {
        "name": "leer_planeacion",
        "description": "Lee el contenido de una planeación por su id para poder comentarla.",
        "input_schema": {
            "type": "object",
            "properties": {"planeacion_id": {"type": "integer"}},
            "required": ["planeacion_id"],
        },
    },
    {
        "name": "guardar_retroalimentacion",
        "description": (
            "Guarda tu retroalimentación pedagógica de una planeación como REVISIÓN en "
            "estado borrador, para que la dirección académica la apruebe antes de que la "
            "vea el docente. Úsala cuando ya diste feedback concreto sobre una planeación."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planeacion_id": {"type": "integer"},
                "retroalimentacion": {"type": "string", "description": "El feedback pedagógico completo."},
                "alineacion_pct": {
                    "type": "integer",
                    "description": "0-100, qué tan alineada con la metodología Maple. Omite si la metodología no está cargada.",
                },
                "sugerencias": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de sugerencias concretas y accionables.",
                },
            },
            "required": ["planeacion_id", "retroalimentacion"],
        },
    },
]


async def _ejecutar_tool(nombre: str, args: dict[str, Any], model: str) -> str:
    repo = get_repository()
    if nombre == "leer_planeacion":
        pl = await repo.get_planeacion(int(args["planeacion_id"]))
        if not pl:
            return "No existe una planeación con ese id."
        return (
            f"Título: {pl.get('titulo')}\nGrado: {pl.get('grado')}\n"
            f"Materia: {pl.get('materia')}\nEstado: {pl.get('estado')}\n\n"
            f"Contenido:\n{pl.get('contenido') or '(sin texto capturado)'}"
        )
    if nombre == "guardar_retroalimentacion":
        rev_id = await repo.guardar_revision(
            planeacion_id=int(args["planeacion_id"]),
            retroalimentacion=str(args["retroalimentacion"]),
            alineacion_pct=args.get("alineacion_pct"),
            sugerencias=args.get("sugerencias"),
            model_used=model,
        )
        await repo.marcar_planeacion_revisada(int(args["planeacion_id"]))
        return (
            f"Retroalimentación guardada (revisión #{rev_id}) en estado borrador. "
            "La dirección académica la revisará antes de compartirla con el docente."
        )
    return f"Tool desconocida: {nombre}"


async def procesar_turno(mensaje: str, session_id: str, docente_id: int | None = None) -> str:
    """Un turno de conversación docente ↔ agente, con loop de tools."""
    repo = get_repository()
    anthropic = get_anthropic()
    model = anthropic.settings.anthropic_model_principal

    await repo.guardar_mensaje(session_id, "user", mensaje, {"docente_id": docente_id})

    historial = await repo.historial(session_id)
    messages: list[dict[str, Any]] = [{"role": m["role"], "content": m["content"]} for m in historial]

    system_blocks = _build_system_blocks()
    respuesta_texto = ""

    # Loop de tools: máximo 5 iteraciones para evitar bucles.
    for _ in range(5):
        resp = await anthropic.chat(system_blocks=system_blocks, messages=messages, tools=TOOLS)

        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        textos = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        respuesta_texto = "\n".join(textos).strip()

        if not tool_uses:
            break

        # Registrar el turno del asistente (con las tool_use) y ejecutar cada tool.
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for tu in tool_uses:
            resultado = await _ejecutar_tool(tu.name, dict(tu.input), model)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": tu.id, "content": resultado}
            )
        messages.append({"role": "user", "content": tool_results})

    if respuesta_texto:
        await repo.guardar_mensaje(session_id, "assistant", respuesta_texto, {"model": model})
    return respuesta_texto or "…"


async def evaluar_planeacion(planeacion_id: int) -> dict[str, Any]:
    """Evaluación one-shot de una planeación → guarda una revisión en borrador.

    Punto de entrada para cuando el docente sube una planeación y el agente la
    revisa automáticamente (sin chat). La calidad de la evaluación depende de que
    la metodología esté cargada (ver metodologia.py).
    """
    session_id = f"eval:planeacion:{planeacion_id}"
    instruccion = (
        f"Lee la planeación con id {planeacion_id} usando la tool, evalúala pedagógicamente "
        "y guarda tu retroalimentación con la tool guardar_retroalimentacion. Sé concreto y "
        "constructivo."
    )
    texto = await procesar_turno(instruccion, session_id=session_id)
    return {"planeacion_id": planeacion_id, "resumen": texto}
