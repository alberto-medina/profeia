-- ProfeIA - Planes, cuotas y apoyos de accesibilidad
-- Convencion: nombres en minuscula, snake_case, sin acentos en identificadores.

-- Ampliar planes disponibles.
alter table docentes drop constraint if exists docentes_plan_check;
alter table docentes add constraint docentes_plan_check
    check (plan in ('gratis', 'docente', 'pro', 'institucion'));

-- Suscripcion actual del docente. En MVP local puede ser espejo de docentes.plan,
-- pero queda lista para integrar pagos externos.
create table if not exists suscripciones_docentes (
    id uuid primary key default gen_random_uuid(),
    docente_id uuid not null references docentes(id) on delete cascade,
    plan text not null check (plan in ('gratis', 'docente', 'pro', 'institucion')),
    estado text not null default 'activa' check (
        estado in ('activa', 'pausada', 'cancelada', 'vencida')
    ),
    proveedor_pago text,
    proveedor_customer_id text,
    proveedor_subscription_id text,
    inicio_periodo timestamptz not null default now(),
    fin_periodo timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create index if not exists idx_suscripciones_docente_id
    on suscripciones_docentes(docente_id);

-- Contadores mensuales por docente. Esto evita recalcular todo y permite
-- cortar consumo antes de llamar APIs externas costosas.
create table if not exists uso_mensual_docentes (
    id uuid primary key default gen_random_uuid(),
    docente_id uuid not null references docentes(id) on delete cascade,
    periodo text not null,
    clases int not null default 0,
    imagenes int not null default 0,
    voces int not null default 0,
    videos int not null default 0,
    minutos_grabacion int not null default 0,
    clonaciones_voz int not null default 0,
    exportaciones_pdf int not null default 0,
    exportaciones_pptx int not null default 0,
    apoyos_accesibilidad int not null default 0,
    actualizado_en timestamptz not null default now(),
    unique (docente_id, periodo)
);

create index if not exists idx_uso_mensual_docente_periodo
    on uso_mensual_docentes(docente_id, periodo);

-- Apoyos pedagogicos para TDAH, TEA, lectura facil, etc.
create table if not exists apoyos_accesibilidad (
    id uuid primary key default gen_random_uuid(),
    clase_id uuid not null references clases(id) on delete cascade,
    docente_id uuid not null references docentes(id) on delete cascade,
    necesidades text[] not null default '{}',
    apoyo_json jsonb not null,
    creado_en timestamptz not null default now()
);

create index if not exists idx_apoyos_accesibilidad_clase_id
    on apoyos_accesibilidad(clase_id);

create index if not exists idx_apoyos_accesibilidad_docente_id
    on apoyos_accesibilidad(docente_id);

alter table suscripciones_docentes enable row level security;
alter table uso_mensual_docentes enable row level security;
alter table apoyos_accesibilidad enable row level security;

create policy suscripciones_select_propias on suscripciones_docentes
    for select using (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

create policy uso_mensual_select_propio on uso_mensual_docentes
    for select using (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

create policy apoyos_select_propios on apoyos_accesibilidad
    for select using (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

create policy apoyos_insert_propios on apoyos_accesibilidad
    for insert with check (
        docente_id in (select id from docentes where auth_user_id = auth.uid())
    );

-- Permitir audios propios del docente como recurso asociado a la clase.
alter table recursos_generados drop constraint if exists recursos_generados_tipo_check;
alter table recursos_generados add constraint recursos_generados_tipo_check
    check (tipo in ('voz', 'imagen', 'slide', 'video', 'pdf', 'pptx', 'zip', 'audio_docente'));

-- Codigo corto para que el alumno acceda a la vista de clase.
alter table clases add column if not exists codigo_publico text;
create unique index if not exists idx_clases_codigo_publico
    on clases(codigo_publico)
    where codigo_publico is not null;
