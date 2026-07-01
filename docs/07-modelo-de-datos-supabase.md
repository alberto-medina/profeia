# 07 - Modelo de Datos (Supabase)

Este documento describe el esquema relacional pensado para los 3 MVPs.
El SQL completo de migracion inicial esta en
`supabase/migrations/001_initial_schema.sql` (incluye solo las tablas del
MVP 1.0; las tablas de MVP 2.0 y 3.0 se agregan como migraciones nuevas
cuando corresponda, sin romper el esquema existente).

## Tablas MVP 1.0

### docentes

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| auth_user_id | uuid | FK a auth.users de Supabase |
| nombre | text | |
| email | text | unico |
| materia_principal | text | nullable |
| idioma | text | default 'es' |
| plan | text | 'gratis' / 'docente' / 'institucion' |
| creado_en | timestamptz | default now() |

Nota: la migracion `002_planes_y_accesibilidad.sql` amplia `plan` a
`gratis` / `docente` / `pro` / `institucion`.

### clases

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| docente_id | uuid | FK a docentes |
| titulo | text | |
| prompt_original | text | el prompt que escribio el docente |
| duracion_minutos | int | 3 / 5 / 8 / 15 |
| edad_publico | text | ej. "10 anos" |
| materia | text | |
| contenido_json | jsonb | objetivos, guion, ejemplos, actividad, evaluacion |
| codigo_publico | text | codigo corto para vista alumno |
| estado | text | 'borrador' / 'generada' / 'editada' / 'finalizada' |
| creado_en | timestamptz | default now() |
| actualizado_en | timestamptz | default now() |

### recursos_generados

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| clase_id | uuid | FK a clases |
| tipo | text | 'voz' / 'imagen' / 'slide' / 'video' / 'pdf' / 'pptx' / 'zip' / 'audio_docente' |
| url_storage | text | ruta en Supabase Storage |
| metadata_json | jsonb | parametros usados (voz elegida, velocidad, etc) |
| creado_en | timestamptz | default now() |

## Tablas MVP 2.0 (migracion futura)

### suscripciones_docentes

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| docente_id | uuid | FK a docentes |
| plan | text | 'gratis' / 'docente' / 'pro' / 'institucion' |
| estado | text | 'activa' / 'pausada' / 'cancelada' / 'vencida' |
| proveedor_pago | text | nullable |
| proveedor_customer_id | text | nullable |
| proveedor_subscription_id | text | nullable |
| inicio_periodo | timestamptz | |
| fin_periodo | timestamptz | nullable |
| creado_en | timestamptz | default now() |
| actualizado_en | timestamptz | default now() |

### uso_mensual_docentes

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| docente_id | uuid | FK a docentes |
| periodo | text | ej. '2026-06' |
| clases | int | |
| imagenes | int | |
| voces | int | |
| videos | int | |
| minutos_grabacion | int | |
| clonaciones_voz | int | |
| exportaciones_pdf | int | |
| exportaciones_pptx | int | |
| apoyos_accesibilidad | int | |
| actualizado_en | timestamptz | |

### apoyos_accesibilidad

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| clase_id | uuid | FK a clases |
| docente_id | uuid | FK a docentes |
| necesidades | text[] | 'tdah', 'tea', 'lectura_facil', etc |
| apoyo_json | jsonb | rutina visual, pausas, consignas, evaluacion flexible |
| creado_en | timestamptz | default now() |

### biblioteca_imagenes

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| docente_id | uuid | FK a docentes |
| url_storage | text | |
| etiquetas | text[] | para busqueda |
| creado_en | timestamptz | default now() |

### clases_compartidas

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| clase_id | uuid | FK a clases |
| docente_origen_id | uuid | FK a docentes |
| docente_destino_id | uuid | nullable, FK a docentes (null = link publico) |
| token_publico | text | nullable, para links de solo lectura |
| creado_en | timestamptz | default now() |

### publicaciones

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| clase_id | uuid | FK a clases |
| red_social | text | 'youtube' / 'tiktok' / 'instagram' / etc |
| url_publicada | text | nullable hasta que se confirme |
| estado | text | 'pendiente' / 'publicada' / 'error' |
| creado_en | timestamptz | default now() |

## Tablas MVP 3.0 (migracion futura)

### planes_semanales

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| docente_id | uuid | FK a docentes |
| materia | text | |
| grado_edad | text | |
| prompt_original | text | |
| estado | text | 'generando' / 'listo' / 'parcial' |
| fecha_inicio | date | |
| creado_en | timestamptz | default now() |

### Modificacion a clases

Se agregan dos columnas nullable a la tabla `clases` existente:

| Columna | Tipo | Notas |
|---|---|---|
| plan_semanal_id | uuid | nullable, FK a planes_semanales |
| dia_numero | int | nullable, 1 a 5 |

## Row Level Security (RLS)

Todas las tablas con `docente_id` (directo o indirecto via `clase_id`) deben
tener policies de RLS en Supabase para que cada docente solo pueda ver y
modificar sus propios datos, excepto en los casos explicitos de
`clases_compartidas` con link publico o destino especifico.
