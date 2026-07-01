# ProfeIA

**El copiloto de IA para docentes argentinos y latinoamericanos.**

> "Escribi una idea. Cinco minutos despues, tenes la clase lista para ensenar y publicar."

## Que es ProfeIA

ProfeIA no es "otra app de generar videos con IA". Es un asistente integral para
docentes: a partir de un prompt simple, genera la planificacion completa de una
clase (objetivos, guion, ejemplos, actividades, evaluacion) y despues produce los
recursos multimedia (voz, imagenes, slides, video, PDF, PPTX) listos para usar en
el aula o publicar en redes sociales.

El valor no es el video. El valor es que el profesor se ahorra horas de
preparacion y multiplica su alcance.

## Estructura de este repositorio

```
ProfeIA/
├── README.md                  <- este archivo
├── docs/
│   ├── 01-vision-y-producto.md
│   ├── 02-flujo-de-usuario.md
│   ├── 03-arquitectura-tecnica.md
│   ├── 04-mvp-1.0.md
│   ├── 05-mvp-2.0.md
│   ├── 06-mvp-3.0.md
│   └── 07-modelo-de-datos-supabase.md
├── frontend/                  <- esqueleto Kivy/KivyMD (Android + Windows)
│   ├── main.py
│   ├── profeia.kv
│   ├── screens/
│   ├── widgets/
│   └── utils/
├── backend/                   <- esqueleto FastAPI
│   └── app/
│       ├── main.py
│       ├── core/
│       ├── models/
│       ├── routers/
│       └── services/
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql
└── assets/
    ├── icons/
    └── images/
```

## Stack tecnologico

Mismo stack que venimos usando en Legal App, para reutilizar conocimiento y
herramientas ya probadas:

| Capa | Tecnologia |
|------|-----------|
| Frontend movil/desktop | Python + KivyMD (Android, Windows, Linux) |
| Backend | FastAPI |
| Base de datos | Supabase (Postgres + Auth + Storage) |
| IA - contenido | GPT (planificacion y guion de la clase) |
| IA - voz | Servicio TTS (narracion natural, clonado de voz opcional) |
| IA - imagenes | Generador de imagenes para ilustraciones y slides |
| IA - video | Motor de ensamblado de escenas (voz + imagenes + texto) |
| Compilacion Android | Buildozer (WSL2 Ubuntu), Kivy 2.2.1 pineado, KivyMD 1.1.1 pineado |

## Hoja de ruta (3 MVPs)

1. **MVP 1.0** - Generador de clases: prompt -> contenido pedagogico completo ->
   voz + imagenes + slides -> exportar PDF/PPTX.
2. **MVP 2.0** - Plataforma docente: editor visual, banco de clases, biblioteca de
   imagenes, historial, compartir con otros docentes, publicacion directa en
   redes (cuando las APIs lo permitan).
3. **MVP 3.0** - "Profesor IA" semanal: generar la semana completa de una materia
   (5 clases, 5 videos, 5 cuestionarios, 5 tareas, 5 PDFs, 5 presentaciones, 5
   audios) desde un unico prompt.

Ver el detalle de cada etapa en `docs/04-mvp-1.0.md`, `docs/05-mvp-2.0.md` y
`docs/06-mvp-3.0.md`.

## Metodologia de trabajo

Igual que en Legal App:

- Un archivo a la vez, completo (nunca snippets parciales).
- No romper lo que ya funciona.
- Todo probado antes de avanzar.
- Codigo limpio, ASCII-clean (sin acentos ni emojis en el codigo fuente, para
  evitar errores de encoding en Windows/PowerShell).
- Pensado desde el dia uno para escalar a Android, Windows y Web.
