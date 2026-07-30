# ProfeIA - Frontend (Kivy / KivyMD)

## Arranque rapido en Windows (PyCharm)

```bash
cd frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Tambien se puede usar el script de desarrollo desde la raiz del proyecto:

```powershell
.\scripts\run_frontend_dev.ps1
```

Ese script define `KIVY_HOME` dentro de la carpeta del proyecto para que los
logs de Kivy no dependan de permisos en el perfil de Windows.

Por defecto, `utils/cliente_api.py` apunta a `http://127.0.0.1:8001`, que es
donde corre el backend FastAPI en desarrollo local (ver `backend/README.md`).
Tambien puede leer `api_config.json`, que es lo recomendado para compilar un
APK que apunte a la IP LAN de la PC.

## Probar en un dispositivo Android fisico (durante desarrollo)

Si vas a probar la app compilada en un celular fisico contra el backend que
corre en tu PC, configura `frontend/api_config.json` con:

```json
{
  "api_url": "http://192.168.0.X:8001"
}
```

Tambien podes usar el script desde la raiz del proyecto:

```powershell
.\scripts\set_android_api_url.ps1 -ApiUrl "http://192.168.0.X:8001"
```

y asegurate de correr el backend con `--host 0.0.0.0` para que acepte
conexiones desde otros dispositivos de la red:

```powershell
.\scripts\run_backend_lan.ps1
```

## Compilar el APK (WSL2 Ubuntu + Buildozer)

Mismo flujo que usamos en Legal App:

```bash
# Dentro de WSL2, dentro de la carpeta frontend/
buildozer -v android debug
```

El APK resultante queda en `frontend/bin/`.

### IMPORTANTE - versiones pineadas

`buildozer.spec` ya tiene pineadas las versiones que sabemos que funcionan
bien en Android:

- Kivy `2.2.1`
- KivyMD `1.1.1`
- NDK `25b`, API `33`, minAPI `26`

**No actualizar estas versiones sin probar a fondo.** En Legal App,
versiones mas nuevas de Kivy (2.3.1+) rompieron el comportamiento de
`TextInput` y el teclado predictivo en Android.

## Estructura de pantallas (MVP 1.0)

| Pantalla | Archivo | Descripcion |
|---|---|---|
| 1 | `screens/pantalla_inicio.py` | Prompt + duracion + edad + materia |
| 2 | `screens/pantalla_historial.py` | Historial local de clases de la sesion |
| 3 | `screens/pantalla_contenido.py` | Contenido generado, editable (tambien se reusa para re-editar desde la pantalla 6) |
| 4 | `screens/pantalla_adaptar.py` | Adaptacion opcional para atencion/TDAH, TEA/autismo, lectura facil y pausas |
| 5 | `screens/pantalla_apoyo.py` | Vista de apoyos generados: rutina visual, consignas, pausas y adaptaciones |
| 6 | `screens/pantalla_recursos.py` | Seleccion de recursos a generar |
| 7 | `screens/pantalla_voz.py` | Configuracion de voz (TTS) |
| 8 | `screens/pantalla_video.py` | Estructura del video (informativa en MVP 1.0) |
| 9 | `screens/pantalla_exportar.py` | Exportar PDF / PowerPoint + boton "Editar clase" |

Todo el diseno visual (layout, widgets KivyMD) vive en `profeia.kv`.

### Editar la clase en cualquier momento

Desde la Pantalla 6 (Exportar), el boton **"EDITAR CLASE"** lleva de vuelta
a la Pantalla 2 con el contenido actual cargado. Al guardar, vuelve
automaticamente a la Pantalla 6 (en vez de seguir el flujo de
creacion hacia la Pantalla 3). Esto se controla con
`EstadoApp.pantalla_retorno_edicion` en `utils/estado_app.py`.

### Adaptar la clase

Despues de revisar/guardar el contenido generado, el flujo pasa por
`PantallaAdaptar`. El docente puede generar apoyos pedagogicos para estudiantes
que necesitan mas estructura, previsibilidad, pausas o consignas simples. Este
paso es opcional: se puede saltar y continuar directo a recursos.
