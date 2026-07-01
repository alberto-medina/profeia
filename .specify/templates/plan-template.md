# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11 backend/frontend runtime, PowerShell dev scripts

**Primary Dependencies**: FastAPI, Kivy/KivyMD, Supabase/Postgres, Mercado Pago, optional AI providers

**Storage**: Supabase/Postgres and Supabase Storage in production; local JSON/files in development fallback

**Testing**: `python -m compileall` for edited Python modules; add focused tests when risk justifies it

**Target Platform**: Windows development, FastAPI backend, Kivy desktop/mobile-oriented frontend

**Project Type**: FastAPI service plus Kivy app

**Performance Goals**: teacher can complete the primary class flow without blocking on paid AI availability

**Constraints**: preserve local dev fallback, guard paid provider usage, keep student flow separate from teacher tools

**Scale/Scope**: MVP for individual teachers first, extensible to paid plans and institutional use

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Aula real**: Does the feature improve a real teacher/student workflow, not just add novelty?
- **Student/teacher separation**: Are student-facing screens free of teacher controls and payment/admin flows?
- **No-paid-AI fallback**: If AI/web/provider access fails, is there a usable local or free fallback?
- **Accessibility responsibility**: Are TDAH/TEA/reading supports pedagogical, respectful, and editable?
- **Cost/backend control**: Are paid or quota-bound operations validated by backend limits/configuration?
- **Export/share impact**: If class content changes, are PDF/PPTX/ZIP/student package impacts considered?
- **Data/storage parity**: Are Supabase production behavior and local development fallback both addressed?

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
backend/app/
├── models/
├── routers/
├── services/
└── core/

frontend/
├── screens/
├── utils/
├── widgets/
└── profeia.kv

supabase/migrations/
docs/
scripts/
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
