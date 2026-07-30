[app]

title = ProfeIA
package.name = profeia
package.domain = com.beto77am.profeia

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf

version = 0.1.0

# CRITICO: pinear Kivy y KivyMD. Sin estas versiones exactas, Buildozer
# compila Kivy 2.3.1+ y rompe TextInput/teclado predictivo en Android
# (misma leccion aprendida en Legal App).
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests==2.32.3,pillow,pyjnius,certifi

orientation = portrait
fullscreen = 0

# Dejar sin icono custom por ahora: assets/icons/icon.png aun no existe.
# Buildozer usara el icono por defecto hasta incorporar el asset final.
# icon.filename = %(source.dir)s/../assets/icons/icon.png

android.permissions = INTERNET
android.allow_cleartext = True
android.api = 33
android.minapi = 26
android.ndk = 25b
# Demo debug para celulares actuales. Agregar armeabi-v7a solo si hace falta
# soportar telefonos Android muy antiguos de 32 bits.
android.archs = arm64-v8a

# Nombre del paquete Python para el punto de entrada
android.entrypoint = org.kivy.android.PythonActivity

# Evita python-for-android master, que hoy compila Python 3.14 y rompe
# Kivy 2.2.1/Cython por la remocion de cgi en Python 3.13+.
p4a.branch = v2024.01.21

[buildozer]

log_level = 2
warn_on_root = 1
