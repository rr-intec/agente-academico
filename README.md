# Agente Supervisor Académico — Maple Collège

Agente 3 del ecosistema Maple (junto a Sofía/admisiones, Community Manager y
Engagement). Es un **mentor pedagógico para los DOCENTES**: revisa sus
**planeaciones de clase**, evalúa qué tan bien aplican la **metodología Maple**,
da retroalimentación pedagógica concreta y responde dudas. **No** trabaja con
alumnos, calificaciones ni asistencia. Toda su retroalimentación pasa por
**revisión humana** (dirección académica) antes de llegar al maestro.

## Estado

**Andamiaje técnico listo.** Copia la base probada de Sofía (FastAPI + Anthropic
tool-use + Supabase/asyncpg). Lo que funciona hoy:

- Tablas en Supabase (`veic`): `docentes`, `planeaciones`, `revisiones_academicas`,
  `academico_mensajes` (ver `migrations/001_schema_academico.sql`).
- Loop del agente con tools (`leer_planeacion`, `guardar_retroalimentacion`).
- API: `POST /academico/planeaciones`, `POST /academico/planeaciones/{id}/evaluar`,
  `POST /academico/chat`, `GET /healthz`, `GET /readyz`.
- El panel (`maple-platform-v3` → `/supervision-academica`) ya lee estas tablas en vivo.

**Pieza bloqueante** (`app/core/metodologia.py`): la **metodología Maple documentada**
(modelo BEAR, principios) para cargarla al RAG. Es la pregunta crítica #1 de
`DEFINICION_Agente_Academico.md`, pendiente de que la dirección académica (Cecilia)
entregue el material. Mientras tanto el agente es honesto sobre la limitación y solo
da buenas prácticas generales.

## Arquitectura

Idéntico principio a Sofía: **modelo = conversación, tools = datos**. El agente nunca
inventa el contenido de una planeación ni citas de la metodología; los lee con tools.

```
app/
  config.py                 settings (misma Supabase que Sofía)
  main.py                   FastAPI entrypoint (puerto 8010)
  adapters/
    anthropic_client.py     cliente Claude con prompt caching
    postgres_client.py      pool asyncpg → Supabase veic
  core/
    agente_academico.py     loop de agente + tools + system prompt (mentor pedagógico)
    metodologia.py          ⚠️ PLACEHOLDER — enchufar aquí la metodología Maple
    repository.py           acceso a docentes/planeaciones/revisiones/mensajes
  api/
    academico.py            endpoints (X-Admin-Key)
    health.py               /healthz, /readyz
migrations/
  001_schema_academico.sql  ya aplicada en veic
```

## Correr local

```bash
cp .env.example .env    # y completar claves
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

## Próximos pasos

1. **Metodología Maple** → cargar en `metodologia.py` (o al RAG compartido). Desbloquea
   la evaluación real.
2. **Captura de planeaciones**: flujo para que los docentes suban sus planeaciones
   (panel o WhatsApp), y extracción de texto de PDF/Word.
3. **Cola de revisión humana** en el panel: aprobar/ajustar cada revisión antes de
   compartirla con el docente.
4. **Deploy** a EasyPanel como servicio nuevo en paralelo (mismo patrón que sofia-pro).
