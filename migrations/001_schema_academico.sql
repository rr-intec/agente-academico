-- 001_schema_academico.sql
-- Esquema del Agente Supervisor Académico (Agente 3 del ecosistema Maple).
-- Vive en la MISMA Supabase que Sofía/Panel (veic...), en tablas propias.
--
-- El agente: recibe PLANEACIONES de los DOCENTES, las evalúa contra la
-- metodología Maple, y produce RETROALIMENTACIÓN pedagógica (revisiones).
-- NO trabaja con alumnos/calificaciones. La dirección académica valida.

-- Docentes (maestros) que interactúan con el agente.
CREATE TABLE IF NOT EXISTS docentes (
  id          bigserial PRIMARY KEY,
  nombre      text NOT NULL,
  email       text,
  area        text,               -- materia/área (ej. "Primaria", "Inglés")
  activo      boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Planeaciones de clase que suben los docentes (la ENTRADA del agente).
CREATE TABLE IF NOT EXISTS planeaciones (
  id          bigserial PRIMARY KEY,
  docente_id  bigint REFERENCES docentes(id) ON DELETE SET NULL,
  titulo      text NOT NULL,
  grado       text,               -- grado/nivel al que aplica
  materia     text,
  contenido   text,               -- texto de la planeación (o extraído del archivo)
  archivo_url text,               -- si el docente sube un archivo (PDF/Word)
  estado      text NOT NULL DEFAULT 'pendiente'
              CHECK (estado IN ('pendiente','revisada','archivada')),
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_planeaciones_docente ON planeaciones(docente_id);
CREATE INDEX IF NOT EXISTS idx_planeaciones_estado ON planeaciones(estado);

-- Revisiones académicas = la retroalimentación pedagógica del agente por
-- planeación. La dirección académica la aprueba/ajusta antes de que la vea el
-- docente (supervisión humana obligatoria).
CREATE TABLE IF NOT EXISTS revisiones_academicas (
  id               bigserial PRIMARY KEY,
  planeacion_id    bigint REFERENCES planeaciones(id) ON DELETE CASCADE,
  alineacion_pct   int,           -- qué tan alineada con la metodología Maple (0-100)
  retroalimentacion text,         -- el texto de feedback pedagógico
  sugerencias      jsonb NOT NULL DEFAULT '[]',   -- lista de sugerencias concretas
  estado           text NOT NULL DEFAULT 'borrador'
                   CHECK (estado IN ('borrador','aprobada','ajustada','descartada')),
  revisado_por     text,          -- dirección académica que validó
  model_used       text,
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_revisiones_planeacion ON revisiones_academicas(planeacion_id);

-- Mensajes de chat entre el docente y el agente (acompañamiento en tiempo real).
CREATE TABLE IF NOT EXISTS academico_mensajes (
  id          bigserial PRIMARY KEY,
  session_id  text NOT NULL,       -- 'docente:<id>' o similar
  role        text NOT NULL,       -- 'user' (docente) | 'assistant' (agente)
  content     text NOT NULL,
  metadata    jsonb NOT NULL DEFAULT '{}',
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_academico_mensajes_session ON academico_mensajes(session_id);

COMMENT ON TABLE docentes IS 'Maestros que interactúan con el Agente Supervisor Académico.';
COMMENT ON TABLE planeaciones IS 'Planeaciones de clase que suben los docentes (entrada del agente).';
COMMENT ON TABLE revisiones_academicas IS 'Retroalimentación pedagógica del agente por planeación (validada por dirección).';
COMMENT ON TABLE academico_mensajes IS 'Chat docente ↔ Agente Supervisor Académico.';
