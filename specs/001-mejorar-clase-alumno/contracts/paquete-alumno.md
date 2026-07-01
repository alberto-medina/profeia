# Contract: Student Package

## Purpose

Return a student-safe read-only package for a class code or current class
preview.

## Actor

Student, family member, or teacher previewing student view.

## Input

- Public class code, or teacher-owned class id for preview.

## Expected Output

`PaqueteAlumno` with:

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

## Contract Rules

- Student package must not include teacher account, plan, payment, edit, or generation controls.
- Student view must show clear sections for studying the class.
- Missing images, audio, homework, or supports must show clear empty states.
- Supports must use simple pedagogical language and avoid diagnosis/treatment wording.
- ZIP export from public code should include the same core lesson content and available local resources.

## Error/Empty States

- Invalid code returns a clear "codigo no encontrado" message.
- Missing resources do not block the student from reading the class.
- Remote resource preview failure is recoverable and does not close the class view.
