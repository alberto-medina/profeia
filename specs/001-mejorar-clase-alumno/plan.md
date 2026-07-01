# Implementation Plan: Mejorar clase y vista alumno

**Branch**: `master` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-mejorar-clase-alumno/spec.md`

## Summary

Improve ProfeIA's core lesson flow so teachers can generate coherent classes
for arbitrary subjects without paid AI, attach/search relevant free images, and
share a student-safe class view that explains the lesson with the same core
blocks included in exports. The technical approach is to extend existing
FastAPI services and Kivy screens instead of adding new subsystems: tighten
topic/materia/age extraction in `servicio_contenido`, score/filter free image
search in `servicio_multimedia`, ensure `PaqueteAlumnoRespuesta` and export
services expose the full lesson structure, and validate end-to-end with local
fallbacks.

## Technical Context

**Language/Version**: Python 3.11 backend/frontend runtime, PowerShell dev scripts

**Primary Dependencies**: FastAPI, Kivy/KivyMD, Pydantic, Pillow, python-pptx, httpx, Supabase/Postgres, Mercado Pago, optional AI providers

**Storage**: Supabase/Postgres and Supabase Storage in production; local JSON/files in development fallback under `backend/generated`

**Testing**: `python -m compileall` for edited Python modules; manual quickstart matrix for random lesson topics and student/export flows

**Target Platform**: Windows development, FastAPI backend, Kivy desktop/mobile-oriented frontend

**Project Type**: FastAPI service plus Kivy app

**Performance Goals**: teacher can complete create -> resources -> student view -> export locally without blocking on paid AI availability

**Constraints**: preserve local dev fallback, guard paid provider usage, keep student flow separate from teacher tools, keep changes scoped to existing modules

**Scale/Scope**: MVP for individual teachers first, extensible to paid plans and institutional use

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Aula real**: PASS. The feature directly improves class usefulness for teachers and students.
- **Student/teacher separation**: PASS. Student view remains read-only and code-based.
- **No-paid-AI fallback**: PASS. Local generation and free/local image fallback are explicit requirements.
- **Accessibility responsibility**: PASS. Existing support aids remain pedagogical and editable.
- **Cost/backend control**: PASS. Quota-bound resources continue through backend plan checks.
- **Export/share impact**: PASS. PDF/ZIP/student package consistency is in scope.
- **Data/storage parity**: PASS. Supabase and local fallback behavior are both considered.

## Project Structure

### Documentation (this feature)

```text
specs/001-mejorar-clase-alumno/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── clase-generation.md
│   ├── imagenes-gratis.md
│   └── paquete-alumno.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
backend/app/
├── models/
│   ├── clase.py
│   └── recurso.py
├── routers/
│   ├── clases.py
│   ├── multimedia.py
│   ├── exportacion.py
│   └── publico.py
├── services/
│   ├── servicio_contenido.py
│   ├── servicio_multimedia.py
│   ├── servicio_exportacion.py
│   └── servicio_storage.py
└── core/

frontend/
├── screens/
│   ├── pantalla_inicio.py
│   ├── pantalla_recursos.py
│   ├── pantalla_alumno.py
│   └── pantalla_exportar.py
├── utils/
│   ├── cliente_api.py
│   └── estado_app.py
└── profeia.kv

docs/
└── 08-resumen-avance-y-objetivos.md
```

**Structure Decision**: Use the existing FastAPI router/service/model split and
Kivy screen/KV layout split. No new top-level app or persistence layer is
needed for this feature.

## Complexity Tracking

No constitution violations or additional complexity exceptions are needed.

## Phase 0: Research

See [research.md](./research.md).

## Phase 1: Design & Contracts

See [data-model.md](./data-model.md), [contracts/](./contracts/), and
[quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- **Aula real**: PASS. Data model and contracts require full lesson blocks and random-topic validation.
- **Student/teacher separation**: PASS. Contracts explicitly separate `PaqueteAlumno` from teacher editing.
- **No-paid-AI fallback**: PASS. Research and quickstart require OpenAI-disabled validation.
- **Accessibility responsibility**: PASS. `ApoyoAccesibilidad` stays supportive and editable.
- **Cost/backend control**: PASS. Existing quota checks stay in backend resource endpoints.
- **Export/share impact**: PASS. Contracts include PDF/ZIP consistency.
- **Data/storage parity**: PASS. Quickstart validates local fallback; contracts allow Supabase/local URLs.
