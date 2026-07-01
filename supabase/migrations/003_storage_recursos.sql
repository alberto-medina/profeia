-- ProfeIA - Storage para recursos de clases
-- Ejecutar en Supabase SQL Editor despues del schema principal.

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
) values (
    'recursos-clases',
    'recursos-clases',
    true,
    52428800,
    array[
        'image/png',
        'image/jpeg',
        'image/webp',
        'audio/mpeg',
        'audio/wav',
        'audio/ogg',
        'audio/mp4',
        'application/octet-stream'
    ]
)
on conflict (id) do update set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists recursos_clases_public_select on storage.objects;
create policy recursos_clases_public_select on storage.objects
    for select using (bucket_id = 'recursos-clases');
