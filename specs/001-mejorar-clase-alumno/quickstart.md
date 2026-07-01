# Quickstart: Mejorar clase y vista alumno

## Prerequisites

- Backend and frontend dependencies installed.
- Local development mode available.
- OpenAI keys may be absent or out of quota; this quickstart must still work.
- PowerShell execution policy can be bypassed for project scripts.

## Start Backend

```powershell
cd C:\profeia
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend_dev.ps1
```

Expected:

- FastAPI starts on `127.0.0.1:8000`.
- No startup error.

## Start Frontend

In another PowerShell:

```powershell
cd C:\profeia
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend_dev.ps1
```

Expected:

- ProfeIA opens.
- Student entry is available before teacher flow.
- Teacher login opens the class builder.

## Scenario A: Random Topic Coherence

Generate at least these local/no-paid-AI classes:

1. Materia: Educacion Fisica, Edad: 10 anos, Tema: futbol pases y tiros.
2. Materia: Ciencias Naturales, Edad: 9 anos, Tema: partes de la planta.
3. Materia: Matematica, Edad: 10 anos, Tema: fracciones con ejemplos.
4. Materia: Ingles, Edad: 8 anos, Tema: saludos y presentaciones.
5. Materia: Ciencias Sociales, Edad: 11 anos, Tema: provincias argentinas.

Expected:

- Title and body stay on selected materia and topic.
- Prompt boilerplate such as "crear una clase" is not repeated as subject.
- Each class includes explanation, examples, activity, questions, questionnaire,
  homework when relevant, and summary.

## Scenario B: Free Images

For two generated classes, open Recursos and use "Buscar imagenes gratis".

Expected:

- Images are related to the lesson topic, or the app uses local fallback / clear message.
- Re-running free image search does not keep old irrelevant free images.
- Teacher-uploaded images remain attached.

## Scenario C: Student Code View

Copy the class code and enter as student.

Expected:

- Student lands directly on the class view after entering code.
- Student sees introduction, explanation, examples, activity, questions,
  questionnaire, homework/summary, resources and supports when present.
- Student does not see teacher edit, payment, plan, generation, or export controls
  except student-safe package download if available.

## Scenario D: Export Consistency

Export PDF and ZIP after generating content and images.

Expected:

- PDF includes the same core lesson blocks visible to the student.
- PDF/ZIP include local/free image resources when available.
- Export failure is shown as a recoverable message.

## Validation Commands

After implementation, run compile validation for edited modules, for example:

```powershell
cd C:\profeia
python -m compileall backend/app frontend
```

Expected:

- No compile errors in edited Python files.

## Local Smoke Validation

To validate the backend flow without Supabase real, paid AI, or the Kivy UI:

```powershell
cd C:\profeia
python scripts\validar_flujo_local.py
```

Expected:

- A local class is generated.
- A student code is generated.
- Local image resources are attached.
- Student package data includes the core class blocks and images.
- PDF and ZIP files are created in `backend/generated/exportaciones`.

To also try Wikimedia before local fallback:

```powershell
cd C:\profeia
python scripts\validar_flujo_local.py --web
```
