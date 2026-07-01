[app]

title = ProfeIA
package.name = profeia
package.domain = com.beto77am.profeia

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.1.0

# CRITICO: pinear Kivy y KivyMD. Sin estas versiones exactas, Buildozer
# compila Kivy 2.3.1+ y rompe TextInput/teclado predictivo en Android
# (misma leccion aprendida en Legal App).
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests==2.32.3,pillow

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/../assets/icons/icon.png

[buildozer]

log_level = 2
warn_on_root = 1

[app:android]

android.permissions = INTERNET
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Nombre del paquete Python para el punto de entrada
android.entrypoint = org.kivy.android.PythonActivity
