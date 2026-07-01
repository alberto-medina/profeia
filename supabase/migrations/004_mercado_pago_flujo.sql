-- ProfeIA - Ajustes para flujo completo de Mercado Pago.

alter table suscripciones_docentes drop constraint if exists suscripciones_docentes_estado_check;
alter table suscripciones_docentes add constraint suscripciones_docentes_estado_check
    check (estado in ('pendiente', 'activa', 'pausada', 'cancelada', 'vencida'));

create index if not exists idx_suscripciones_proveedor_subscription_id
    on suscripciones_docentes(proveedor_subscription_id);
