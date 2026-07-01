<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- PRINCIPLE_1_NAME -> I. Aula Real Primero
- PRINCIPLE_2_NAME -> II. Alumno y Docente Separados
- PRINCIPLE_3_NAME -> III. Funciona Sin IA Paga
- PRINCIPLE_4_NAME -> IV. Accesibilidad Pedagogica Responsable
- PRINCIPLE_5_NAME -> V. Exportacion, Costos y Datos Bajo Control
Added sections:
- Alcance Tecnico
- Flujo de Desarrollo
Removed sections:
- Placeholder sections from the Spec Kit template
Templates requiring updates:
- .specify/templates/plan-template.md: updated
- .specify/templates/spec-template.md: updated
- .specify/templates/tasks-template.md: updated
Follow-up deferred items: none
-->

# ProfeIA Constitution

## Core Principles

### I. Aula Real Primero

ProfeIA MUST produce material usable by docentes argentinos y latinoamericanos
in a classroom or tutoring context. Every generated class MUST include a clear
objective, introduction, explanation, examples, activity, questions,
questionnaire, homework when relevant, and a concise summary. Features MUST
prioritize teacher time savings and student comprehension over novelty or
decorative AI output.

Rationale: the product value is not "AI text"; it is a ready-to-use teaching
package that a real teacher can edit, export, share, and teach.

### II. Alumno y Docente Separados

Student flows MUST be separate from teacher flows. A student MUST enter with a
class code and see only student-safe material: explanation, summary, images,
audio, activity, questions, questionnaire, homework, and support aids. A
student MUST NOT see teacher account screens, plan management, generation
tools, editing controls, payment flows, or internal resource management.

Teacher flows MUST keep every generated class editable before export or share.

Rationale: ProfeIA serves two audiences in one app; mixing their controls makes
the product confusing and unsafe for classroom use.

### III. Funciona Sin IA Paga

Every core lesson flow MUST keep a local/free fallback when paid AI services
are missing, out of quota, or failing. The app MUST still allow a teacher to
create a class, adapt it, attach resources, search free images where possible,
generate local visual aids when possible, and export PDF/PPTX/ZIP.

Paid AI integrations SHOULD improve quality, speed, voice, images, or future
video, but they MUST NOT be the only path for the MVP teacher workflow.

Rationale: teachers may test the product before paying for AI credits, and the
business must control provider costs.

### IV. Accesibilidad Pedagogica Responsable

Accessibility features MUST be framed as pedagogical supports, not medical
diagnosis or treatment. Supports for TDAH, TEA/autismo, lectura facil,
ansiedad, rutina visual, pausas, consignas simples, and flexible assessment
MUST use respectful language and remain editable by the teacher.

Voice cloning MUST require explicit teacher consent and MUST be treated as a
separate high-trust flow before production use.

Rationale: the app should make classes clearer and more inclusive without
pretending to replace professional clinical judgment.

### V. Exportacion, Costos y Datos Bajo Control

PDF, PowerPoint, ZIP, and class-code sharing MUST remain reliable outputs of
the app. Backend limits MUST control paid or costly operations such as AI text,
images, voice, video, exports, and subscriptions. Production authentication and
storage SHOULD use Supabase; local development fallbacks MUST remain available
for fast iteration and demos.

User data, class resources, generated materials, and payment status MUST be
handled through backend services, not trusted only to frontend state.

Rationale: ProfeIA must be commercially viable, testable locally, and safe to
operate with subscriptions and generated educational content.

## Alcance Tecnico

The current product uses FastAPI for backend services, Kivy/KivyMD for the
desktop/mobile-oriented frontend, Supabase/Postgres for production data and
storage, local generated files for development fallback, and Mercado Pago for
Latin American subscriptions.

New work MUST preserve the existing repository structure:

- `backend/app`: routers, models, services, configuration, and app setup.
- `frontend`: Kivy screens, KV layout, widgets, and API client helpers.
- `supabase/migrations`: database and storage schema changes.
- `docs`: product, architecture, and roadmap documentation.

API contract changes MUST keep backend models, routers, frontend API helpers,
screens, docs, and Supabase migrations aligned.

## Flujo de Desarrollo

Each feature MUST start from a user journey and define how it is verified. Work
SHOULD be delivered in small increments that can be tested independently.

Before implementation, plans MUST pass these checks:

- Teacher and student experiences are clearly separated.
- The feature has a local/free fallback when it touches AI or external services.
- Paid provider usage is gated by backend limits or explicit configuration.
- Student-facing material is pedagogically clear and age/materia aware.
- Accessibility language remains supportive, respectful, and editable.
- Export/share behavior is considered when the feature affects class content.
- Supabase production behavior and local development fallback are both stated
  when data or storage is involved.

Before finishing a change, run the relevant validation command for the touched
area. At minimum, Python backend/frontend changes MUST compile with
`python -m compileall` for the edited modules.

## Governance

This constitution supersedes ad-hoc implementation preferences for ProfeIA.
Specs, plans, tasks, code reviews, and future roadmap decisions MUST check
against these principles.

Amendments require:

- A documented reason for the change.
- An update to this file with semantic versioning.
- Review of affected Spec Kit templates and project docs.
- A migration or follow-up note when existing behavior is affected.

Versioning policy:

- MAJOR: removes or redefines a core principle.
- MINOR: adds a principle or materially expands governance.
- PATCH: clarifies wording without changing obligations.

**Version**: 1.0.0 | **Ratified**: 2026-07-01 | **Last Amended**: 2026-07-01
