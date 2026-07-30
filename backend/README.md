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

El generador de clases es IA-first. Si hay proveedores configurados, prueba en
cadena hasta conseguir una respuesta pedagogica en JSON:

1. OpenAI Responses API.
2. DeepSeek compatible con chat completions.
3. OpenRouter compatible con chat completions.
4. Groq compatible con chat completions.

Si todos fallan y `IA_CONTENIDO_FALLBACK_LOCAL=false`, el backend devuelve un
error claro para no entregar una clase local floja como si fuera contenido
vendible. El generador local queda para desarrollo o demo.

Para activar IA real, copiar `.env.example` a `.env` y completar uno o varios:

```env
IA_CONTENIDO_API_KEY=sk-...
IA_CONTENIDO_MODELO=gpt-4o-mini

IA_CONTENIDO_DEEPSEEK_API_KEY=...
IA_CONTENIDO_DEEPSEEK_MODELO=deepseek-chat

IA_CONTENIDO_OPENROUTER_API_KEY=...
IA_CONTENIDO_OPENROUTER_MODELO=deepseek/deepseek-chat

IA_CONTENIDO_GROQ_API_KEY=...
IA_CONTENIDO_GROQ_MODELO=llama-3.3-70b-versatile

IA_CONTENIDO_FALLBACK_LOCAL=false
```

Despues reiniciar `uvicorn`.

Imagenes reales tambien pueden usar una cadena simple: OpenAI Images primero y,
si se configura, un proveedor secundario compatible con el endpoint de
generacion de imagenes.

```env
IA_IMAGENES_API_KEY=sk-...
IA_IMAGENES_MODELO=gpt-image-1

IA_IMAGENES_SECUNDARIO_API_KEY=...
IA_IMAGENES_SECUNDARIO_MODELO=...
IA_IMAGENES_SECUNDARIO_URL=https://proveedor.example/v1/images/generations
```

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

El contenido pedagogico ya tiene integracion opcional con varios proveedores de
IA y fallback local controlado para demo. Las exportaciones PDF y PPTX se generan como archivos reales en
`backend/generated/exportaciones`.

Los servicios multimedia (`servicio_multimedia.py`) pueden generar voz e
imagenes reales si hay credenciales; si no, usan placeholders funcionales para
que el flujo se pueda probar sin depender de APIs externas.

## Cambios recientes (julio 2026)

### Calidad de contenido pedagogico generado por IA

`app/services/servicio_contenido.py` recibio dos mejoras importantes:

1. **Normalizacion de respuestas de proveedores no estrictos (Groq, DeepSeek,
   OpenRouter).** A diferencia de OpenAI (que usa `json_schema` con
   `strict: true`), estos proveedores a veces devuelven los campos de lista
   (`ejemplos`, `preguntas`, `cuestionario`) como objetos
   `{"pregunta": ..., "respuesta": ...}` en vez de strings simples. Esto
   rompia la validacion de Pydantic (`ContenidoPedagogico`) y hacia que el
   backend descartara una respuesta de IA perfectamente buena, cayendo al
   generador local sin ningun log de error visible salvo el traceback de
   validacion.

   Se agrego `_normalizar_datos_pedagogicos()` (con sus helpers
   `_texto_desde_valor()` y `_normalizar_lista_strings()`), que aplana
   cualquier forma inesperada antes de pasar los datos a
   `ContenidoPedagogico.model_validate()`. Se aplica tanto en
   `_generar_con_openai()` como en `_generar_con_chat_compatible()`.

2. **Prompt reforzado para pedir contenido "de clase real", no un resumen.**
   `construir_prompt_sistema()` y `_instruccion_json_pedagogico()` ahora
   piden explicitamente:
   - Una `explicacion` extensa (5-7+ oraciones) con datos concretos, causas/
     consecuencias y algun dato curioso, en vez de una definicion generica.
   - Que `preguntas` (repaso oral simple) y `cuestionario` (evaluacion:
     comparar, justificar, resolver un caso nuevo) sean claramente
     diferentes entre si, no reformulaciones de lo mismo.
   - `ejemplos` con informacion especifica (nombres, numeros, lugares), no
     repeticiones de la definicion con otras palabras.

   Se subio tambien `max_tokens`/`max_output_tokens` (2200->3500 en el flujo
   chat-compatible, 1800->3000 en OpenAI) para que el contenido mas rico no
   se corte.

3. **Modelo de Groq recomendado:** se paso de `llama-3.1-8b-instant` a
   `llama-3.3-70b-versatile`. El modelo de 8B es rapido pero tiende a
   ignorar reglas de prompt mas finas (como diferenciar `preguntas` de
   `cuestionario`) y a cometer imprecisiones factuales (ej. errores de
   geografia). El modelo de 70B sigue instrucciones complejas con mas
   fidelidad, sigue siendo gratuito en el tier de Groq, y solo agrega
   latencia marginal.

   Config recomendada en `.env`:
   ```env
   IA_CONTENIDO_GROQ_MODELO=llama-3.3-70b-versatile
   ```

### Troubleshooting: procesos "zombie" de uvicorn en Windows

Se detecto que, en desarrollo con `--reload` en Windows, a veces queda un
proceso `python` viejo escuchando en el puerto configurado (8000 por
default) despues de cerrar la consola o de un crash del reloader. Windows
a veces no libera el socket de inmediato aunque el proceso ya no exista
(`Stop-Process` puede fallar con "no se encuentra ningun proceso" mientras
`netstat` sigue mostrando el puerto ocupado).

Sintoma tipico: el backend "no refleja" cambios de codigo ni de `.env`
por mas que se reinicie, porque el cliente (la app Kivy) sigue hablando
con el proceso viejo, no con el nuevo.

Como diagnosticar:

```powershell
netstat -ano | findstr :8000
Get-Process -Id <PID_DEVUELTO>
```

Como resolver:

```powershell
Stop-Process -Id <PID> -Force
```

Si el puerto sigue "fantasma" despues de matar el proceso (Windows no lo
libero), la salida mas rapida es correr el backend en otro puerto:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

y actualizar `URL_BASE_API` en `frontend/utils/cliente_api.py` para que
apunte al nuevo puerto. Un reinicio de Windows tambien libera el socket
fantasma de forma definitiva si el problema persiste.

**Recomendacion:** antes de reportar un bug de "no cambia nada pese al
fix", verificar primero que no haya un proceso viejo ocupando el puerto,
y verificar que la ventana de consola que se esta mirando sea realmente
la del backend (`INFO:     Uvicorn running on ...`) y no la del frontend
Kivy (logs con formato `[DEBUG  ] [http ...]`), ya que ambas pueden quedar
abiertas simultaneamente y son faciles de confundir.



Ver `docs/04-mvp-1.0.md` en la raiz del proyecto para el detalle completo.