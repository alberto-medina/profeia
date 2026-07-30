# Demo en celular Android

Esta guia sirve para instalar un APK debug de ProfeIA en un celular fisico y
probarlo contra el backend FastAPI corriendo en la PC.

## Requisitos

- Celular Android y PC conectados a la misma red WiFi.
- Backend instalado con sus dependencias.
- WSL2 Ubuntu para compilar con Buildozer.
- Depuracion USB activada en el celular si se instala por cable.

## 1. Obtener la IP LAN de la PC

En PowerShell:

```powershell
ipconfig
```

Buscar la direccion IPv4 del adaptador WiFi. Ejemplo:

```text
192.168.0.11
```

## 2. Configurar la app para hablar con esa IP

Desde la raiz del proyecto:

```powershell
.\scripts\set_android_api_url.ps1 -ApiUrl "http://192.168.0.11:8001"
```

Esto actualiza `frontend/api_config.json`, que se incluye dentro del APK.

## 3. Levantar el backend para la red local

Desde la raiz del proyecto:

```powershell
.\scripts\run_backend_lan.ps1
```

Probar desde el navegador del celular:

```text
http://192.168.0.11:8001/
```

Tiene que responder con estado `ok`. Si no responde, revisar firewall de
Windows, que PC y celular esten en la misma red, y que la IP sea la correcta.

## 4. Compilar el APK debug

En WSL2, dentro de la carpeta del proyecto:

```bash
bash scripts/build_android_debug_wsl.sh
```

El APK queda en:

```text
frontend/bin/
```

## 5. Instalar en el celular

Opcion A, con ADB:

```bash
adb install -r frontend/bin/*.apk
```

Opcion B, manual:

- Copiar el APK al celular.
- Abrirlo desde Archivos.
- Permitir instalar apps desconocidas si Android lo pide.

## Prueba sugerida

1. Registrar o iniciar sesion con un docente demo.
2. Crear una clase corta, por ejemplo: `fracciones para 5to grado`.
3. Revisar el contenido generado.
4. Probar adaptaciones, recursos y exportacion.

Para demo sin claves reales, el backend usa almacenamiento local de desarrollo
y generadores fallback cuando corresponde.
