# Contract: Free Image Search

## Purpose

Attach relevant free or local visual resources to a generated class.

## Actor

Teacher.

## Input

- `clase_id`
- Optional `cantidad`, clamped to the supported safe range.
- Existing class `contenido_json`, materia, edad/grado and title.

## Expected Output

A list of `RecursoGenerado` records with:

- `tipo`: `imagen`
- `url_storage`: local path or remote/public storage URL.
- `metadata_json.origen`: `wikimedia_commons` or `local`.
- `metadata_json.consulta`: query used.
- Optional source metadata: title, source URL, author, license, relevance score, storage mode.

## Contract Rules

- Search must derive keywords from the real class topic, not raw prompt boilerplate.
- Search must prefer relevant images and reject low-confidence results.
- If no relevant free image is available, do not attach unrelated images.
- Re-running free image search replaces previous free/local image-search results but keeps teacher-uploaded images.
- Storage failure must fall back to local resource persistence when possible.
- Backend image quotas must be respected.

## Error/Empty States

- If Wikimedia is unavailable, the app uses local fallback images or a clear teacher-facing message.
- If a resource is remote-only and cannot be previewed, student and teacher views show a clear unavailable state.
