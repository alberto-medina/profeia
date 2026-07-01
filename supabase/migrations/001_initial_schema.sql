-- ProfeIA - Migracion inicial (MVP 1.0)
-- Tablas: docentes, clases, recursos_generados
-- Convencion: nombres en minuscula, snake_case, sin acentos en identificadores.

create extension if not exists "pgcrypto";

-- ============================================================
-- Tabla: docentes
-- ============================================================
create table if not exists docentes (
    id uuid primary key default gen_random_uuid(),
    auth_user_id uuid not null unique references auth.users(id) on delete cascade,
    nombre text not null,
    email text not null unique,
    materia_principal text,
    idioma text not null default 'es',
    plan text not null default 'gratis' check (plan in ('gratis', 'docente', 'institucion')),
    creado_en timestamptz not null default now()
);

comment on table docentes is 'Perfil de cada docente registrado en ProfeIA';

-- ============================================================
-- Tabla: clases
-- ============================================================
create table if not exists clases (
    id uuid primary key default gen_random_uuid(),
    docente_id uuid not null references docentes(id) on delete cascade,
    titulo text,
    prompt_original text not null,
    duracion_minutos int not null check (duracion_minutos in (3, 5, 8, 15)),
    edad_publico text,
    materia text,
    contenido_json jsonb,
    estado text not null default 'borrador' check (
        estado in ('borrador', 'generada', 'editada', 'finalizada')
    ),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

comment on table clases is 'Cada clase generada por un docente a partir de un prompt';
comment on column clases.contenido_json is 'JSON con objetivos, guion, ejemplos, actividad, evaluacion';

create index if not exists idx_clases_docente_id on clases(docente_id);
create index if not exists idx_clases_estado on clases(estado);

-- ============================================================
-- Tabla: recursos_generados
-- ============================================================
create table if not exists recursos_generados (
    id uuid primary key default gen_random_uuid(),
    clase_id uuid not null references clases(id) on delete cascade,
    tipo text not null check (
        tipo in ('voz', 'imagen', 'slide', 'video', 'pdf', 'pptx')
    ),
    url_storage text not null,
    metadata_json jsonb,
    creado_en timestamptz not null default now()
);

comment on table recursos_generados is 'Archivos multimedia/exportables generados para una clase';

create index if not exists idx_recursos_clase_id on recursos_generados(clase_id);
create index if not exists idx_recursos_tipo on recursos_generados(tipo);

-- ============================================================
-- Trigger: actualizar 'actualizado_en' en clases
-- ============================================================
create or replace function actualizar_timestamp_clases()
returns trigger as $$
begin
    new.actualizado_en = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_actualizar_timestamp_clases on clases;
create trigger trg_actualizar_timestamp_clases
    before update on clases
    for each row
    execute function actualizar_timestamp_clases();

-- ============================================================
-- Row Level Security
-- ============================================================
alter table docentes enable row level security;
alter table clases enable row level security;
alter table recursos_generados enable row level security;

-- docentes: cada usuario ve y edita solo su propio perfil
create policy docentes_select_propio on docentes
    for select using (auth.uid() = auth_user_id);

create policy docentes_update_propio on docentes
    for update using (auth.uid() = auth_user_id);

create policy docentes_insert_propio on docentes
    for insert with check (auth.uid() = auth_user_id);

-- clases: cada docente ve y edita solo sus propias clases
create policy clases_select_propias on clases
    for select using (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

create policy clases_insert_propias on clases
    for insert with check (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

create policy clases_update_propias on clases
    for update using (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

create policy clases_delete_propias on clases
    for delete using (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

-- recursos_generados: visibles solo si la clase asociada es del docente
create policy recursos_select_propios on recursos_generados
    for select using (
        clase_id in (
            select c.id from clases c
            join docentes d on d.id = c.docente_id
            where d.auth_user_id = auth.uid()
        )
    );

create policy recursos_insert_propios on recursos_generados
    for insert with check (
        clase_id in (
            select c.id from clases c
            join docentes d on d.id = c.docente_id
            where d.auth_user_id = auth.uid()
        )
    );

create policy recursos_delete_propios on recursos_generados
    for delete using (
        clase_id in (
            select c.id from clases c
            join docentes d on d.id = c.docente_id
            where d.auth_user_id = auth.uid()
        )
    );
