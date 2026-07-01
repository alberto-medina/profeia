# Data Model: Mejorar clase y vista alumno

## Clase

Represents a teacher-owned generated lesson.

**Key fields**

- `id`: unique class id.
- `docente_id`: owner teacher id.
- `prompt_original`: original teacher input.
- `materia`: selected or corrected subject.
- `edad_publico`: age/grade audience.
- `duracion_minutos`: lesson length bucket.
- `titulo`: display title.
- `contenido_json`: structured lesson content.
- `codigo_publico`: student access code.
- `estado`: draft/generated/edited/finalized state.

**Validation rules**

- `materia` and `edad_publico` are required before generation.
- `contenido_json` must preserve the selected/corrected subject and audience.
- Teacher can edit `contenido_json` before sharing/exporting.

## ContenidoPedagogico

Structured body of a generated class.

**Key fields**

- `titulo`
- `objetivo`
- `introduccion`
- `explicacion`
- `ejemplos`
- `actividad`
- `preguntas`
- `cuestionario`
- `tarea_hogar`
- `resumen`

**Validation rules**

- Required text fields must be non-empty for generated classes.
- `ejemplos`, `preguntas`, and `cuestionario` should contain classroom-ready items.
- Prompt boilerplate such as "crear una clase" must not become the lesson subject.
- Content should be age/materia aware.

## RecursoGenerado

Represents an asset attached to a class.

**Key fields**

- `id`
- `clase_id`
- `tipo`: voz, imagen, slide, video, pdf, pptx, zip, audio_docente.
- `url_storage`: remote URL, local path, or storage identifier.
- `metadata_json`: origin, query, title, license, source, relevance score, or teacher metadata.
- `creado_en`

**Validation rules**

- Free image resources should include `metadata_json.origen` as `wikimedia_commons` or `local`.
- Teacher-provided resources must not be deleted when replacing free image results.
- ZIP exports include local resources when available.

## PaqueteAlumno

Student-safe read-only view returned by class id or public code.

**Key fields**

- `clase_id`
- `codigo_publico`
- `titulo`
- `introduccion`
- `explicacion`
- `ejemplos`
- `actividad`
- `preguntas`
- `resumen`
- `cuestionario`
- `tarea_hogar`
- `audio_resumen`
- `imagenes`
- `audios_docente`
- `apoyos`

**Validation rules**

- Must not expose teacher account, payment, plan, edit, or generation controls.
- Missing resources should result in clear empty states, not broken screens.
- Supports must use pedagogical language.

## ApoyoAccesibilidad

Optional support adaptation for a class.

**Key fields**

- `clase_id`
- `apoyo_json`
- `resumen_docente`
- `consigna_simple`
- `rutina_visual`
- `pausas_sugeridas`
- `adaptaciones`

**Validation rules**

- Must be editable by teacher.
- Must avoid medical diagnosis or treatment language.
- Should be safe to show in student view when written in simple supportive language.

## Docente/Plan/UsoMensual

Teacher identity, subscription plan, and quota accounting.

**Key fields**

- `docente.id`
- `docente.email`
- `plan.codigo`
- `uso_mensual_docentes` counters for classes, images, voices, supports, and exports.

**Validation rules**

- Costly actions are validated by backend plan limits before execution.
- Successful actions register usage after completion.
- Local demo mode must remain available for development.
