# Feature Specification: Mejorar clase y vista alumno

**Feature Branch**: `001-mejorar-clase-alumno`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Mejorar la generacion de clase para que sea coherente para cualquier materia/edad, mejorar imagenes gratis con filtros, y hacer que la vista alumno explique la clase con resumen, explicacion, ejemplos, actividad, preguntas, cuestionario y tarea."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Docente genera una clase coherente (Priority: P1)

Un docente ingresa tema, materia y edad/grado. ProfeIA genera una clase completa
que respeta esos datos y no se va a otro tema, incluso cuando no hay IA paga
disponible.

**Why this priority**: Es el valor principal del producto. Si la clase sale
incoherente, todo lo demas pierde utilidad.

**Independent Test**: Crear clases con temas distintos, por ejemplo futbol,
plantas, fracciones, ingles basico y ciencias sociales. Cada clase debe
mantener materia, edad y tema correctos, con explicacion y ejemplos relevantes.

**Acceptance Scenarios**:

1. **Given** un docente selecciona materia "Educacion Fisica", edad "10 anos" y tema "futbol: pases y tiros", **When** genera la clase, **Then** la clase trata de futbol escolar y no de matematica, volcanes u otro tema.
2. **Given** un docente selecciona materia "Ciencias Naturales", edad "9 anos" y tema "partes de la planta", **When** genera la clase sin IA paga, **Then** la explicacion, ejemplos, actividad y preguntas se relacionan con plantas.
3. **Given** el docente escribe un prompt con frases como "crear una clase de 8 minutos", **When** se genera el contenido, **Then** esas frases no se repiten como tema en titulo, parrafos o preguntas.

---

### User Story 2 - Docente obtiene imagenes gratis relevantes (Priority: P2)

Un docente puede buscar imagenes gratis para la clase. ProfeIA debe priorizar
imagenes relacionadas con el tema real y evitar adjuntar resultados que no
tengan relacion clara.

**Why this priority**: Las imagenes son utiles solo si ayudan a explicar la
clase; imagenes equivocadas reducen confianza en la app.

**Independent Test**: Buscar imagenes gratis para al menos cinco temas de
materias distintas y revisar que las imagenes agregadas tengan relacion visible
con el tema o que la app use un recurso local seguro cuando no encuentra algo
confiable.

**Acceptance Scenarios**:

1. **Given** una clase de "tablas del 1 al 9", **When** se buscan imagenes gratis, **Then** aparecen laminas, diagramas o recursos relacionados con multiplicacion.
2. **Given** una clase de "futbol: pases y tiros", **When** se buscan imagenes gratis, **Then** las imagenes se relacionan con futbol, entrenamiento, pases o tiros.
3. **Given** no se encuentran imagenes gratis confiables, **When** termina la busqueda, **Then** la app no agrega imagenes fuera de tema y ofrece una alternativa local o un mensaje claro.

---

### User Story 3 - Alumno entiende la clase desde el codigo (Priority: P1)

Un alumno ingresa el codigo de clase y ve una experiencia pensada para estudiar:
de que trata la clase, explicacion, ejemplos, actividad, preguntas,
cuestionario, tarea, audios, imagenes y apoyos.

**Why this priority**: La vista alumno no debe parecer una pantalla de profesor;
debe permitir estudiar o repasar la clase sin editar ni configurar nada.

**Independent Test**: Ingresar con un codigo publico y verificar que el alumno
puede leer la clase completa sin navegar por pantallas docentes ni depender de
opciones administrativas.

**Acceptance Scenarios**:

1. **Given** un alumno abre la app, **When** ingresa un codigo valido, **Then** ve directamente el contenido de la clase en secciones claras.
2. **Given** la clase tiene imagenes o audios, **When** el alumno entra con codigo, **Then** puede ver o escuchar esos recursos desde la vista alumno.
3. **Given** la clase tiene apoyos TDAH/TEA/lectura facil, **When** el alumno abre la clase, **Then** ve apoyos en lenguaje simple y no diagnostico.

---

### User Story 4 - Docente exporta un paquete consistente (Priority: P2)

Un docente exporta PDF, PowerPoint o ZIP despues de generar o ajustar la clase.
Los materiales exportados reflejan el mismo contenido que ve el alumno.

**Why this priority**: El docente necesita entregar materiales confiables por
archivo, WhatsApp, aula virtual o impresion.

**Independent Test**: Generar una clase, buscar imagenes, entrar como alumno y
exportar PDF/ZIP. El contenido principal debe coincidir entre vista alumno y
exportacion.

**Acceptance Scenarios**:

1. **Given** una clase con explicacion, ejemplos, actividad, cuestionario y tarea, **When** se exporta a PDF, **Then** esos bloques aparecen en el PDF.
2. **Given** una clase con imagenes gratis o locales, **When** se exporta a PDF/ZIP, **Then** las imagenes se incluyen o se informa claramente si no pudieron incluirse.

### Edge Cases

- OpenAI no tiene credito, responde con limite o no esta configurado.
- Wikimedia no encuentra resultados confiables o no hay conexion.
- Supabase Storage no responde y debe usarse almacenamiento local.
- El docente escribe el tema con errores ortograficos o mezcla tema, edad y duracion en el prompt.
- El tema existe en varias materias y debe priorizar la materia seleccionada.
- El alumno abre una clase sin imagenes, sin audio o sin apoyos.
- El docente alcanza el limite de imagenes, exportaciones o clases de su plan.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST require or obtain materia and edad/grado before generating a class.
- **FR-002**: System MUST generate class content that preserves the selected materia, edad/grado and topic.
- **FR-003**: System MUST avoid repeating prompt boilerplate such as "crear una clase" as lesson subject matter.
- **FR-004**: System MUST include objective, introduction, explanation, examples, activity, questions, questionnaire, homework when relevant, and summary in generated class content.
- **FR-005**: System MUST support a local/free generation path when paid AI is unavailable.
- **FR-006**: Student-facing behavior MUST be stated separately from teacher-facing behavior.
- **FR-007**: Student view MUST show student-safe sections without teacher editing, plan, payment or generation controls.
- **FR-008**: Features touching AI, web search, payments, or storage MUST define a local/free fallback.
- **FR-009**: Free image search MUST use topic-specific keywords and reject or avoid obviously unrelated images.
- **FR-010**: If no trustworthy free image is available, System MUST avoid adding unrelated images and use a local visual aid or clear message.
- **FR-011**: Features changing class content MUST state impact on PDF, PowerPoint, ZIP, and student package.
- **FR-012**: Exported PDF/ZIP MUST include the same core educational blocks shown to the student when available.
- **FR-013**: Paid or quota-bound operations MUST be controlled by backend configuration and plan limits.
- **FR-014**: Accessibility support MUST use pedagogical, respectful, teacher-editable language.
- **FR-015**: Teacher MUST be able to review and edit generated content before sharing or exporting.

### Key Entities *(include if feature involves data)*

- **Clase**: Generated lesson content, code, teacher ownership, materia, edad/grado and editable pedagogical structure.
- **RecursoGenerado**: PDF, PPTX, ZIP, image, audio, voice, slide, or teacher-provided asset attached to a class.
- **PaqueteAlumno**: Student-safe view of a class accessed by public code, containing content sections and resources.
- **Docente/Plan/UsoMensual**: Teacher account, subscription level, and quota consumption for generation/export operations.
- **ApoyoAccesibilidad**: Pedagogical adaptation for attention, TEA/autismo, lectura facil, anxiety, visual routine or pauses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a manual test of 10 random topics across at least 5 materias, at least 8 generated classes stay on the selected materia, edad/grado and topic without paid AI.
- **SC-002**: A teacher can complete the affected class flow locally without paid AI credits.
- **SC-003**: A student can understand the class from the code view without seeing teacher tools.
- **SC-004**: For a class with full content, student view displays at least introduction, explanation, examples, activity, questions, questionnaire, homework or summary.
- **SC-005**: In 5 free-image searches, no more than 1 result set contains images clearly unrelated to the lesson topic; otherwise the app must use fallback or show a clear message.
- **SC-006**: Exported/shareable outputs remain accurate after the feature is used.

## Assumptions

- The first production-quality improvement focuses on Spanish-language lessons for Argentina/LatAm.
- Local/free generation is acceptable as a fallback even if paid AI later improves quality.
- The teacher is responsible for final review before using materials with students.
- Student view is read-only for this feature.
- Video generation is out of scope for this feature.
