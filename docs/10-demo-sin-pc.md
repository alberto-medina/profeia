# Demo sin depender de la PC

El APK de ProfeIA es una app cliente: para generar clases, recursos y
exportaciones necesita hablar con el backend FastAPI. Para que otras personas
lo prueben sin estar en la misma WiFi que tu PC, hay que publicar el backend en
internet y compilar el APK apuntando a esa URL publica.

## Opcion recomendada para demo

1. Subir este repositorio a GitHub.
2. Crear un Web Service en Render, Railway, Fly.io o un VPS.
3. Usar el backend con Docker.
4. Configurar variables de entorno.
5. Recompilar el APK con la URL publica.

## Render

Este repo incluye `render.yaml` y `backend/Dockerfile`.

En Render:

- New + Blueprint.
- Conectar el repositorio.
- Usar el servicio `profeia-api`.
- Esperar el deploy.

Variables minimas para demo:

```text
ENTORNO=desarrollo
IA_CONTENIDO_FALLBACK_LOCAL=true
```

Con esas variables el backend puede usar almacenamiento local de desarrollo y
fallbacks para demo. Los datos no son permanentes como en Supabase real.

Cuando Render te de una URL como:

```text
https://profeia-api.onrender.com
```

probar:

```text
https://profeia-api.onrender.com/
```

Tiene que responder `estado: ok`.

## Recompilar el APK contra la URL publica

Desde Windows, en la raiz del proyecto:

```powershell
.\scripts\set_android_api_url.ps1 -ApiUrl "https://profeia-api.onrender.com"
wsl bash scripts/build_android_debug_wsl_native.sh
```

El APK nuevo queda en:

```text
frontend/bin/
```

Ese APK ya no depende de tu PC. Solo depende de que el backend publico este
prendido.
