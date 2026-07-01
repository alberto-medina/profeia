# Contract: Class Generation

## Purpose

Generate a coherent, editable class from teacher input while preserving
materia, edad/grado, duration, and topic.

## Actor

Teacher.

## Input

- `prompt_original`: free text topic/instruction from teacher.
- `duracion_minutos`: one of the supported duration options.
- `edad_publico`: required age or grade.
- `materia`: required subject.
- Optional accessibility support selections from the initial flow.

## Expected Output

A `Clase` with `contenido_json` containing:

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
- `codigo_publico`

## Contract Rules

- The generated topic must not be unrelated to the selected subject and prompt.
- Prompt boilerplate must be stripped from generated lesson subject matter.
- Paid AI failure must fall back to local/free generation.
- Teacher must be able to edit the result before export/share.
- Backend must enforce class-generation quota before generation and register use after success.

## Error/Empty States

- Missing materia or edad/grado returns a teacher-facing validation message.
- External provider failure returns a local generation result when possible.
- If generation cannot complete, frontend shows a recoverable error and does not navigate to student/export flow.
