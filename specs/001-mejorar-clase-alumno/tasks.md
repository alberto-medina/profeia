# Tasks: Mejorar clase y vista alumno

**Input**: Design documents from `specs/001-mejorar-clase-alumno/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: No formal TDD requested. Include compile validation and manual quickstart scenarios.

**Organization**: Tasks are grouped by user story so each story can be delivered and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Maps to user stories from `spec.md`.
- Every task includes exact file paths.

## Path Conventions

- **Backend**: `backend/app/models/`, `backend/app/routers/`, `backend/app/services/`, `backend/app/core/`
- **Frontend**: `frontend/screens/`, `frontend/utils/`, `frontend/widgets/`, `frontend/profeia.kv`
- **Database/storage**: `supabase/migrations/`
- **Docs/product**: `docs/`
- **Dev scripts**: `scripts/`

## Phase 1: Setup

**Purpose**: Confirm the current app state before touching implementation.

- [ ] T001 Review current generation flow in `backend/app/services/servicio_contenido.py`
- [ ] T002 Review current image search/resource flow in `backend/app/services/servicio_multimedia.py` and `backend/app/routers/multimedia.py`
- [ ] T003 Review current student package and student screen flow in `backend/app/routers/multimedia.py`, `backend/app/routers/publico.py`, `frontend/screens/pantalla_alumno.py`, and `frontend/profeia.kv`
- [ ] T004 Review current export flow in `backend/app/services/servicio_exportacion.py` and `backend/app/routers/exportacion.py`

---

## Phase 2: Foundational

**Purpose**: Shared prerequisites that support all user stories.

**Critical**: Complete before story work.

- [ ] T005 Confirm `ContenidoPedagogico` and `PaqueteAlumnoRespuesta` contain every required class block in `backend/app/models/clase.py` and `backend/app/models/recurso.py`
- [ ] T006 Confirm frontend API helpers expose class generation, free image search, student package, and export calls in `frontend/utils/cliente_api.py`
- [ ] T007 Confirm plan quota checks remain backend-owned for class generation, images, and exports in `backend/app/routers/clases.py`, `backend/app/routers/multimedia.py`, and `backend/app/routers/exportacion.py`
- [ ] T008 Confirm local development fallback remains available for content/resources in `backend/app/core/supabase_client.py`, `backend/app/services/servicio_storage.py`, and `backend/generated/`

---

## Phase 3: User Story 1 - Docente genera una clase coherente (Priority: P1) MVP

**Goal**: A teacher can generate a class that stays on selected materia, edad/grado, and topic without paid AI.

**Independent Test**: Generate classes for futbol, plantas, fracciones, ingles basico, and ciencias sociales; verify each output stays on topic and includes full lesson blocks.

### Implementation for User Story 1

- [ ] T009 [US1] Strengthen prompt boilerplate cleanup and destinatario removal in `backend/app/services/servicio_contenido.py`
- [ ] T010 [US1] Strengthen materia correction by selected subject plus keywords in `backend/app/services/servicio_contenido.py`
- [ ] T011 [US1] Expand local subject profiles for common Argentine school subjects and ambiguous prompts in `backend/app/services/servicio_contenido.py`
- [ ] T012 [US1] Ensure local generation fills objective, introduction, explanation, examples, activity, questions, questionnaire, homework, and summary in `backend/app/services/servicio_contenido.py`
- [ ] T013 [US1] Ensure OpenAI failure and quota errors fall back to local generation where safe in `backend/app/services/servicio_contenido.py`
- [ ] T014 [US1] Improve teacher-facing validation messages for missing materia/edad in `frontend/screens/pantalla_inicio.py`
- [ ] T015 [US1] Run compile validation for generation changes with `python -m compileall backend/app/services/servicio_contenido.py frontend/screens/pantalla_inicio.py`
- [ ] T016 [US1] Manually validate Scenario A from `specs/001-mejorar-clase-alumno/quickstart.md`

**Checkpoint**: User Story 1 works independently and is the first MVP stop.

---

## Phase 4: User Story 3 - Alumno entiende la clase desde el codigo (Priority: P1)

**Goal**: A student enters a code and sees a student-safe study view with complete lesson sections.

**Independent Test**: Open a class by code and confirm the student sees class sections/resources without teacher controls.

### Implementation for User Story 3

- [ ] T017 [US3] Ensure `construir_paquete_alumno` maps every required lesson block in `backend/app/routers/multimedia.py`
- [ ] T018 [US3] Ensure public code lookup returns only student-safe package data in `backend/app/routers/publico.py`
- [ ] T019 [US3] Refine student screen state loading and empty states in `frontend/screens/pantalla_alumno.py`
- [ ] T020 [US3] Refine student section layout for introduction, explanation, examples, activity, questions, questionnaire, homework, summary, resources, and supports in `frontend/profeia.kv`
- [ ] T021 [US3] Confirm student mode cannot navigate into teacher editing, plan, payment, or generation flows in `frontend/screens/pantalla_alumno.py` and `frontend/main.py`
- [ ] T022 [US3] Run compile validation with `python -m compileall backend/app/routers/multimedia.py backend/app/routers/publico.py frontend/screens/pantalla_alumno.py frontend/main.py`
- [ ] T023 [US3] Manually validate Scenario C from `specs/001-mejorar-clase-alumno/quickstart.md`

**Checkpoint**: Student view is complete and independently usable.

---

## Phase 5: User Story 2 - Docente obtiene imagenes gratis relevantes (Priority: P2)

**Goal**: A teacher can attach free/local images that match the class topic, or get a safe fallback/message.

**Independent Test**: Search free images for five topics and verify relevance or clear fallback.

### Implementation for User Story 2

- [ ] T024 [US2] Strengthen topic keyword extraction for image queries in `backend/app/services/servicio_multimedia.py`
- [ ] T025 [US2] Improve query variants and translation hints for common school subjects in `backend/app/services/servicio_multimedia.py`
- [ ] T026 [US2] Tighten relevance scoring and low-confidence rejection in `backend/app/services/servicio_multimedia.py`
- [ ] T027 [US2] Ensure repeated free-image searches replace only previous free/local image-search resources in `backend/app/routers/multimedia.py`
- [ ] T028 [US2] Improve teacher-facing free-image status/error messages in `frontend/screens/pantalla_recursos.py`
- [ ] T029 [US2] Confirm teacher-uploaded images remain attached after free-image replacement in `backend/app/routers/multimedia.py`
- [ ] T030 [US2] Run compile validation with `python -m compileall backend/app/services/servicio_multimedia.py backend/app/routers/multimedia.py frontend/screens/pantalla_recursos.py`
- [ ] T031 [US2] Manually validate Scenario B from `specs/001-mejorar-clase-alumno/quickstart.md`

**Checkpoint**: Free image flow is useful even when web results are weak.

---

## Phase 6: User Story 4 - Docente exporta un paquete consistente (Priority: P2)

**Goal**: PDF/ZIP exports reflect the same core class content and available image resources as the student view.

**Independent Test**: Generate a class, add images, view as student, then export PDF/ZIP and compare core content.

### Implementation for User Story 4

- [ ] T032 [US4] Confirm PDF line generation includes every core lesson block in `backend/app/services/servicio_exportacion.py`
- [ ] T033 [US4] Confirm PDF visual generation includes local image resources with metadata when available in `backend/app/services/servicio_exportacion.py`
- [ ] T034 [US4] Confirm export routers pass relevant resources into PDF/ZIP generation in `backend/app/routers/exportacion.py` and `backend/app/routers/publico.py`
- [ ] T035 [US4] Improve export screen status messages for included resources and recoverable failures in `frontend/screens/pantalla_exportar.py`
- [ ] T036 [US4] Run compile validation with `python -m compileall backend/app/services/servicio_exportacion.py backend/app/routers/exportacion.py backend/app/routers/publico.py frontend/screens/pantalla_exportar.py`
- [ ] T037 [US4] Manually validate Scenario D from `specs/001-mejorar-clase-alumno/quickstart.md`

**Checkpoint**: Exported materials are consistent with student-facing content.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature and update documentation.

- [ ] T038 Run full compile validation with `python -m compileall backend/app frontend`
- [ ] T039 Execute the full quickstart matrix in `specs/001-mejorar-clase-alumno/quickstart.md`
- [ ] T040 Update progress notes in `docs/08-resumen-avance-y-objetivos.md`
- [ ] T041 Review `git diff` to confirm changes stay within the planned feature scope

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundation; first MVP.
- **US3 (Phase 4)**: Depends on Foundation and benefits from US1 content quality.
- **US2 (Phase 5)**: Depends on Foundation and benefits from US1 topic cleanup.
- **US4 (Phase 6)**: Depends on US3 and US2 for complete package/export parity.
- **Polish (Phase 7)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1**: Independent MVP and should be completed first.
- **US3**: Can be implemented after Foundation, but validates best with US1 output.
- **US2**: Can be implemented after Foundation, but uses the same cleaned topic concepts as US1.
- **US4**: Should follow US2/US3 to compare student view and exports.

### Parallel Opportunities

- T001-T004 can be reviewed in parallel.
- T005-T008 can be checked in parallel after Setup.
- US3 frontend layout tasks T019-T020 can proceed in parallel with backend mapping T017-T018.
- US2 frontend status task T028 can proceed in parallel with backend image scoring tasks T024-T026.
- US4 export screen task T035 can proceed in parallel with backend export checks T032-T034.

## Parallel Example

```text
US3:
- T017 [US3] backend package mapping
- T019 [US3] frontend screen state loading
- T020 [US3] KV section layout
```

```text
US2:
- T024 [US2] backend keyword extraction
- T025 [US2] backend query variants
- T028 [US2] frontend status messages
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1.
3. Stop and validate Scenario A.
4. Commit the coherent local generation improvement.

### Incremental Delivery

1. US1 improves class generation.
2. US3 makes the student view truly useful.
3. US2 improves relevant free images.
4. US4 aligns export outputs with student content.
5. Polish runs compile and quickstart validation.

### Commit Strategy

- Commit after each completed user story or logical slice.
- Keep generated docs and implementation changes separate when practical.
- Avoid unrelated visual polish until the feature passes quickstart validation.
