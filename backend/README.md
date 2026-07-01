# ProfeIA - Backend (FastAPI)

## Arranque rapido (desarrollo local)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac/WSL

pip install -r requirements.txt

copy .env.example .env          # Windows
# cp .env.example .env          # Linux/Mac/WSL
# Opcional: completar .env con credenciales reales de Supabase y proveedores de IA

uvicorn app.main:app --reload --port 8000
```

Tambien se puede usar el script de desarrollo desde la raiz del proyecto:

```powershell
.\scripts\run_backend_dev.ps1
```

La documentacion interactiva queda disponible en:

- http://127.0.0.1:8000/docs (Swagger UI)
- http://127.0.0.1:8000/redoc (Redoc)

Si `ENTORNO=desarrollo` y no hay credenciales reales de Supabase, el backend usa
un almacenamiento en memoria. Esto permite probar el flujo completo
`prompt -> clase -> edicion -> recursos -> exportacion` sin configurar servicios
externos. Los datos se pierden al reiniciar el servidor.

## Generacion de contenido con IA

El generador de clases funciona en dos modos:

- Sin `IA_CONTENIDO_API_KEY`: usa un generador local de desarrollo, suficiente
  para probar el flujo completo con contenido pedagogico editable.
- Con `IA_CONTENIDO_API_KEY`: llama a OpenAI Responses API y pide una respuesta
  JSON estructurada con titulo, objetivo, introduccion, explicacion, ejemplos,
  actividad, preguntas y resumen.

Para activar IA real, copiar `.env.example` a `.env` y completar:

```env
IA_CONTENIDO_API_KEY=sk-...
IA_CONTENIDO_MODELO=gpt-4o-mini
```

Despues reiniciar `uvicorn`.

## Planes y cuotas

El backend expone `/planes` con planes `gratis`, `docente`, `pro` e
`institucion`. Cada plan define limites para clases, imagenes, voz, video,
grabaciones, clonacion de voz, exportaciones y apoyos de accesibilidad.

Tambien existe:

- `GET /planes/{plan_id}`
- `GET /planes/docentes/{docente_id}/uso?plan_id=gratis`

La migracion `supabase/migrations/002_planes_y_accesibilidad.sql` prepara
tablas para suscripciones, uso mensual y apoyos educativos.

## Mercado Pago

El flujo de suscripciones usa:

- `POST /pagos/suscripciones/mercado-pago`: crea el checkout.
- `POST /pagos/mercadopago/webhook`: recibe webhooks de Mercado Pago.
- `POST /pagos/suscripciones/demo/activar`: activa un plan en desarrollo.
- `GET /pagos/mercadopago/retorno`: retorno simple despues del checkout.

Variables:

```env
MERCADO_PAGO_ACCESS_TOKEN=APP_USR...
MERCADO_PAGO_WEBHOOK_SECRET=...
MERCADO_PAGO_BACK_URL=https://tu-backend.com/pagos/mercadopago/retorno
```

En Mercado Pago configurar el webhook publico apuntando a:

```text
https://tu-backend.com/pagos/mercadopago/webhook
```

Eventos recomendados para suscripciones:

- `subscription_preapproval`
- `subscription_authorized_payment`

La migracion `supabase/migrations/004_mercado_pago_flujo.sql` habilita el estado
`pendiente` y agrega indice por `proveedor_subscription_id`.

## Accesibilidad educativa

`POST /clases/{clase_id}/accesibilidad/apoyos` genera adaptaciones educativas
para atencion, TEA/autismo, lectura facil, ansiedad, dificultad lectora y baja
vision. Son sugerencias pedagogicas para el docente; no diagnostican ni
reemplazan orientacion profesional.

## Antes de usar contra Supabase real

1. Crear un proyecto en Supabase.
2. Correr la migracion `supabase/migrations/001_initial_schema.sql` desde el
   SQL Editor de Supabase (o via `supabase db push` si usas la CLI).
3. Copiar `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` al archivo `.env`.

## Estado actual (MVP 1.0)

El contenido pedagogico ya tiene integracion opcional con OpenAI y fallback
local. Las exportaciones PDF y PPTX se generan como archivos reales en
`backend/generated/exportaciones`.

Los servicios multimedia (`servicio_multimedia.py`) todavia usan placeholders
funcionales para voz, imagenes y video, de modo que el flujo se pueda probar
sin depender de APIs externas.

## Endpoints disponibles

Ver `docs/04-mvp-1.0.md` en la raiz del proyecto para el detalle completo.
