# Research: Mejorar clase y vista alumno

## Decision: Keep local generation as the mandatory baseline

The local content generator remains the baseline for the feature. Paid AI may
improve quality, but the product must pass the random-topic validation matrix
with AI unavailable.

**Rationale**: The constitution requires the teacher flow to work without paid
AI. The current `servicio_contenido.py` already has local generation,
subject profiles, special cases for multiplication tables/fracciones, and
Wikipedia enrichment. Extending that path is lower risk than introducing a new
provider dependency.

**Alternatives considered**:

- Require OpenAI for all high-quality classes: rejected because the user has no
  paid API credits now and the MVP must remain usable.
- Build a large embedded content library: rejected for now because the topic
  surface is too broad; targeted profiles plus web/free enrichment are faster.

## Decision: Use strict topic extraction and materia correction before generation

Class generation should derive a clean topic from prompt + selected materia +
edad/grado, stripping boilerplate such as "crear una clase" and destinatario
phrases before building title, examples, image queries, or Wikipedia queries.

**Rationale**: The observed failures were topic drift and repeated prompt
boilerplate. A single cleaned topic used across content, image search, exports,
and student view reduces incoherence.

**Alternatives considered**:

- Let the teacher prompt be used verbatim: rejected because it caused repeated
  "crear clase" text and irrelevant content.
- Force only dropdown topics: rejected because teachers need arbitrary topics.

## Decision: Prefer fewer relevant images over many uncertain images

Free image search should score candidate results and skip low-relevance items.
When confidence is low, the app should use a local visual aid or clear message
instead of attaching unrelated imagery.

**Rationale**: Wrong images damage trust more than missing images. The current
Wikimedia path can be improved with query variants, score thresholds, metadata,
and replacement of previous free image results.

**Alternatives considered**:

- Always accept the first Wikimedia results: rejected after user feedback that
  generated images were unrelated.
- Only use local generated images: rejected because free web images can add
  real value when relevant and attributable.

## Decision: Student package is the source for student-safe display

The student view should render only `PaqueteAlumnoRespuesta` fields and must
include core lesson blocks: introduction, explanation, examples, activity,
questions, summary, questionnaire, homework, resources, and supports.

**Rationale**: A class code should open a study experience, not a teacher/admin
experience. The backend package gives one controlled contract for both direct
student access and in-app preview.

**Alternatives considered**:

- Reuse teacher edit content directly in the frontend: rejected because it
  risks leaking edit controls and implementation details.
- Build a separate student database entity immediately: rejected because the
  existing class content plus resources already provide the needed material.

## Decision: Exports should consume the same content shape as student view

PDF/ZIP exports should include the same educational blocks and image resources
that are visible to the student where possible.

**Rationale**: Teachers often share files instead of app codes. Inconsistency
between student view and exported material creates confusion.

**Alternatives considered**:

- Keep exports text-only: rejected because images and full lesson blocks are
  important to the promised teaching package.
- Make exports depend on remote URLs only: rejected because local demos and
  offline ZIP sharing are part of the MVP.
