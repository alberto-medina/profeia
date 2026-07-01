# AGENTS.md

## Project context
ProfeIA is an AI teaching assistant for Argentine and Latin American educators. It combines a FastAPI backend, a Kivy/KivyMD frontend, and Supabase/Postgres storage to generate lesson plans, multimedia assets, and exportable materials.

## Repository structure
- backend/app: FastAPI application, routers, services, and models
- frontend: Kivy/KivyMD screens, widgets, and API client helpers
- supabase/migrations: database schema migrations
- docs: product, architecture, and roadmap documentation

## Working rules
- Keep changes small and focused on the task at hand.
- Preserve existing behavior unless the request explicitly requires a change.
- Prefer the existing project structure and naming conventions.
- Write clean Python code and keep source files ASCII-clean (avoid accents and emoji in code).
- When editing backend endpoints, keep routers, services, and models aligned.
- When editing frontend screens, keep the Kivy layout and Python logic consistent.
- If a change affects the API contract or data model, update the related docs and migrations when appropriate.
- Before finishing, run the relevant validation command available for the change.

## Preferred approach
1. Inspect the relevant module and neighboring files first.
2. Follow the existing pattern already used in the repository.
3. Make the minimal change needed to solve the issue.
4. Verify the result with the available checks.
