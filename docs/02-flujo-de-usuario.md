# 02 - Flujo de Usuario

## Diagrama de flujo general

```
Profesor
   |
   v
Escribe un prompt
   |
   v
IA crea el contenido
   |
   |-- Objetivos
   |-- Guion
   |-- Ejemplos
   |-- Preguntas
   |-- Actividades
   |-- Evaluacion
   |
   v
Generador multimedia
   |
   |-- Voz IA
   |-- Slides
   |-- Imagenes
   |-- Video vertical
   |-- Video horizontal
   |
   v
Editor rapido
   |
   v
Exportar
   |
   |-- YouTube
   |-- TikTok
   |-- Instagram
   |-- WhatsApp
   |-- PDF
   |-- PPTX
```

## Pantallas del MVP 1.0

### Pantalla 1 - Que queres ensenar hoy?

Campos:

- Prompt (texto libre, multilinea)
- Duracion: 3 / 5 / 8 / 15 minutos (radio buttons)
- Edad del publico (dropdown, ej. "10 anos")
- Materia (dropdown, ej. "Matematica")
- Boton: **GENERAR CLASE**

### Pantalla 2 - Contenido generado

La IA devuelve, todo editable en campos de texto:

- Titulo (ej. "Las Fracciones")
- Objetivo
- Introduccion
- Explicacion
- Ejemplos
- Actividad
- Preguntas
- Resumen

### Pantalla 3 - Elegir recursos a generar

Checkboxes:

- [ ] Voz
- [ ] Slides
- [ ] Imagenes
- [ ] Video
- [ ] PDF
- [ ] PowerPoint

### Pantalla 4 - Configuracion de voz

- Seleccion de voz: Clonar mi voz / Voz masculina / Voz femenina / Voz infantil
- Idioma: Espanol (por defecto, expandible)
- Velocidad: slider, ej. 0.9x

### Pantalla 5 - Estructura del video

La IA muestra el armado automatico de escenas:

- Intro
- Desarrollo
- Ejemplos
- Actividad
- Cierre

### Pantalla 6 - Exportar

Checkboxes de destino:

- [ ] TikTok
- [ ] Instagram
- [ ] YouTube Shorts
- [ ] Facebook
- [ ] WhatsApp
- [ ] Moodle
- [ ] Google Classroom
- [ ] PDF
- [ ] PPT

## Flujo real de ejemplo (caso de uso completo)

1. El profesor abre ProfeIA y escribe: "Crea una clase de 8 minutos sobre
   fracciones para ninos de 10 anos. Explica como si fueras un profesor
   paciente y divertido. Incluye ejemplos cotidianos."
2. La app genera: guion estructurado, voz narrada (clonada o similar),
   sugerencia de slides/imagenes, descripcion lista para YouTube/TikTok/
   Instagram con hashtags.
3. El profesor revisa el resultado (opcional, rapido).
4. Descarga el audio/video y lo sube a TikTok, YouTube Shorts, Instagram
   Reels o lo comparte por WhatsApp.
5. Los alumnos lo ven en casa como repaso.
6. En el colegio, el profesor da la clase presencial normalmente, resuelve
   dudas puntuales y hace las actividades practicas.

Resultado: el profesor multiplica su alcance (mas alumnos, mas seguidores,
posibilidad de cobrar por clases extra o cursos) y ahorra horas de
preparacion semanal.
