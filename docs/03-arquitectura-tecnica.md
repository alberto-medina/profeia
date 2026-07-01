# 03 - Arquitectura Tecnica

## Diagrama de capas

```
Kivy (KivyMD)  -- Frontend Android / Windows / Linux
     |
     v
FastAPI         -- Backend / orquestador
     |
     v
Supabase        -- Auth + Postgres + Storage
     |
     v
Motor IA
     |
     |-- GPT          (planificacion y guion de la clase)
     |-- TTS           (narracion natural / voz clonada)
     |-- Imagenes       (ilustraciones y diapositivas)
     |-- Slides         (armado de presentaciones)
     |-- PDF            (material imprimible)
     |-- PowerPoint     (exportacion .pptx)
     |-- Video          (ensamblado de escenas: voz + imagenes + texto)
```

## Frontend (Kivy / KivyMD)

Mismo stack que Legal App, con las mismas reglas tecnicas ya validadas:

- `BoxLayout` con `on_touch_down` / `collide_point` en lugar de `Button` como
  contenedor cuando se necesita un area clickeable compleja.
- `height: self.minimum_height` para layouts dinamicos.
- `Image` (no `AsyncImage`) para archivos locales.
- `App.get_running_app()` en lugar de `self.manager.parent`.
- Base de datos / cache local en una ruta absoluta fija usando
  `os.path.dirname(os.path.abspath(__file__))`.
- `Clock.schedule_once` para actualizaciones de UI thread-safe desde hilos
  secundarios (llamadas a la IA, descargas, generacion de archivos).

### Stack de build Android (igual que Legal App)

| Componente | Version |
|---|---|
| Python | 3.11.9 |
| Kivy | 2.2.1 (pineado en buildozer.spec) |
| KivyMD | 1.1.1 (pineado en buildozer.spec) |
| NDK | r25b |
| API objetivo | 33 |
| minAPI | 26 |

Importante: si no se pinean las versiones de Kivy/KivyMD en `buildozer.spec`,
Buildozer compila versiones mas nuevas (ej. 2.3.1) que rompen el
comportamiento de `TextInput` y el teclado predictivo en Android. Esta leccion
ya la aprendimos con Legal App; se aplica igual aca.

## Backend (FastAPI)

Responsable de:

- Autenticacion (puede delegar en Supabase Auth o usar JWT propio).
- Orquestar las llamadas al motor de IA (GPT, TTS, imagenes, video).
- Persistir clases, recursos generados y metadata en Supabase.
- Servir archivos generados (o generar URLs firmadas de Supabase Storage).
- Exponer endpoints REST que el frontend Kivy consume.

### Routers principales (ver `backend/app/routers/`)

- `auth.py` - login / registro / perfil docente
- `clases.py` - CRUD de clases generadas
- `generacion.py` - orquesta la generacion de contenido pedagogico (texto)
- `multimedia.py` - orquesta la generacion de voz, imagenes, slides, video
- `exportacion.py` - genera PDF / PPTX y links de exportacion a redes

## Base de datos (Supabase / Postgres)

Ver detalle completo en `docs/07-modelo-de-datos-supabase.md`. Tablas
principales: `docentes`, `clases`, `recursos_generados`, `exportaciones`,
`suscripciones`.

## Motor de IA - consideraciones

- **GPT**: genera el contenido pedagogico estructurado (JSON) a partir del
  prompt del docente, parametrizado por edad, materia y duracion.
- **TTS**: convierte el guion en audio narrado. Soporta velocidad ajustable y,
  en el plan pago, clonado de voz del propio docente.
- **Imagenes**: genera ilustraciones simples para apoyar la explicacion y
  para las diapositivas.
- **Video**: ensambla voz + imagenes + texto en escenas (intro, desarrollo,
  ejemplos, actividad, cierre) en formato vertical y horizontal.
- **PDF / PPTX**: se generan a partir del mismo contenido estructurado, sin
  necesidad de pasar por el motor de video.

Todos estos servicios se integran como proveedores intercambiables detras de
una interfaz comun en `backend/app/services/`, para poder cambiar de
proveedor sin tocar el resto del sistema.

## Principios de diseno

1. Separacion clara entre "generacion de contenido pedagogico" (texto/JSON) y
   "generacion multimedia" (voz/imagen/video). El docente puede editar el
   contenido antes de generar los recursos pesados.
2. Cada proveedor de IA externo se abstrae detras de una interfaz propia
   (patron adapter) para poder reemplazarlo sin reescribir la logica de
   negocio.
3. Archivos generados pesados (audio, video, imagenes) viven en Supabase
   Storage, nunca en la base de datos relacional.
4. Todo el codigo fuente ASCII-clean (sin acentos ni emojis) para evitar
   problemas de encoding en Windows/PowerShell, igual que en Legal App.
