# 08 - Resumen de avance y objetivos

## Vision general

ProfeIA es una app para docentes que transforma una idea simple en una clase
lista para usar. El objetivo no es solo generar texto con IA, sino ayudar al
docente a preparar, adaptar, narrar, exportar y eventualmente publicar sus
clases con menos esfuerzo.

La app apunta a docentes argentinos y latinoamericanos, con lenguaje claro,
herramientas practicas y foco en el aula real.

## Objetivo principal de la app

Permitir que un docente escriba que quiere ensenar y reciba una clase completa,
editable y exportable, con opcion de:

- Generar contenido pedagogico estructurado.
- Generar cuestionarios breves y tarea para el hogar junto con la clase.
- Adaptar la clase para estudiantes con necesidades de atencion, TDAH, TEA,
  lectura facil u otras necesidades de apoyo.
- Generar recursos multimedia: imagenes, voz, slides y video.
- Adjuntar recursos propios del docente, como imagenes o audios.
- Crear una vista alumno para ver imagenes y escuchar audios/resumen.
- Compartir una clase con codigo corto para que el alumno entre sin editar.
- Exportar materiales en PDF y PowerPoint.
- Exportar un paquete ZIP descargable para compartir la clase completa por
  archivo.
- Ahorrar tiempo de preparacion.
- Mejorar la claridad y accesibilidad de las clases.
- Escalar el trabajo del docente hacia contenido digital o institucional.

## Idea de producto

El flujo deseado es:

1. El docente escribe una idea de clase.
2. El docente puede marcar apoyos educativos desde el inicio si la clase debe
   contemplar TDAH, TEA/autismo, lectura facil, ansiedad, rutina visual o pausas.
3. ProfeIA genera una planificacion completa.
4. El docente revisa y edita el contenido.
5. La app ofrece adaptar la clase para distintos perfiles de estudiantes, ya
   con las preferencias iniciales precargadas.
6. El docente elige recursos: imagenes, voz, slides, PDF, PowerPoint y video.
7. La app genera los materiales.
8. El docente usa la clase en el aula, la comparte o la publica.

Flujo alumno:

1. El alumno abre la app.
2. Ingresa el codigo corto de la clase.
3. Accede directamente al resumen, audios, imagenes y apoyos disponibles.

## Avance actual

### Backend

- FastAPI funcionando.
- Modo desarrollo sin Supabase real, usando almacenamiento local persistente
  en `backend/generated/dev_db.json`.
- Registro/login local de docentes para MVP, con hash de clave en backend.
- Endpoint para crear clases desde prompt.
- Generador local de contenido pedagogico mas completo.
- El contenido pedagogico incluye cuestionario editable y tarea para el hogar.
- Integracion opcional con OpenAI para generar contenido real si se configura
  `IA_CONTENIDO_API_KEY`.
- Integracion opcional con OpenAI Images para generar imagenes reales si se
  configura `IA_IMAGENES_API_KEY`; sin key mantiene imagenes simuladas para
  desarrollo.
- Integracion opcional con OpenAI TTS para voz narrada real si se configura
  `IA_VOZ_API_KEY`; sin key mantiene audio simulado para desarrollo.
- Integracion opcional con ElevenLabs TTS para voz clonada cuando existe una
  voz ya creada y se configuran `IA_VOZ_CLONADA_API_KEY` y
  `IA_VOZ_CLONADA_VOICE_ID`.
- Endpoints para editar clase.
- Endpoints de recursos: voz, imagenes, slides.
- Endpoint para adjuntar imagenes o audios propios del docente a una clase.
- Endpoint para subir imagenes/audios propios a Supabase Storage.
- Endpoint de paquete alumno con resumen, audio, imagenes, audios del docente
  y apoyos educativos.
- Codigo publico corto generado al crear una clase.
- Endpoint publico `GET /publico/clases/{codigo}` para acceder a la vista
  alumno.
- Exportacion real a PDF local.
- Exportacion real a PowerPoint local.
- Exportacion de paquete ZIP local con PDF, PowerPoint, manifiesto, codigo
  alumno y recursos asociados.
- Endpoint publico para generar el paquete ZIP desde el codigo de alumno,
  pensado para familias o estudiantes que necesitan descargar la clase.
- PDF y PowerPoint incluyen la ultima adaptacion educativa generada para la
  clase cuando existe.
- PDF, PowerPoint, ZIP y vista alumno incluyen cuestionario y tarea para el
  hogar cuando estan disponibles.
- Carpeta local de exportaciones:
  `backend/generated/exportaciones`.
- Planes y cuotas:
  - Gratis
  - Docente
  - Pro
  - Institucion
- Endpoint para consultar planes.
- Endpoint para consultar uso mensual real del docente contra su plan.
- Control de cuotas por plan en backend antes de crear clases, generar imagenes,
  voz, apoyos y exportar PDF/PowerPoint/ZIP.
- Registro de consumo mensual en `uso_mensual_docentes` despues de acciones
  exitosas.
- Endpoint de checkout de suscripcion con Mercado Pago, con modo demo local
  cuando no hay access token configurado.
- Webhook de Mercado Pago para suscripciones recurrentes, con validacion de
  firma cuando `MERCADO_PAGO_WEBHOOK_SECRET` esta configurado.
- Activacion automatica del plan del docente al recibir una suscripcion
  autorizada desde Mercado Pago.
- Endpoint demo para activar planes en desarrollo sin depender del webhook real.
- Backend de apoyos educativos de accesibilidad.
- Migracion Supabase para planes, suscripciones, uso mensual y apoyos.

### Frontend

- App Kivy/KivyMD funcionando en Windows.
- Pantalla inicial para escribir la clase.
- Plantillas rapidas en la pantalla inicial: explicacion rapida, practica
  guiada y evaluacion corta.
- Texto predictivo simple en la pantalla inicial, con sugerencias segun tema,
  materia, edad y palabras clave como TDAH/TEA.
- Selector inicial de apoyos para estudiantes, para marcar TDAH, TEA/autismo,
  lectura facil, ansiedad, rutina visual y pausas antes de generar la clase.
- Pantalla de entrada separa alumno/docente: el alumno ingresa codigo apenas
  abre la app y el docente entra al constructor de clases.
- Entrada docente con email y clave antes de crear clases.
- Pantalla Mi plan con plan actual, uso mensual estimado, limites y planes
  disponibles.
- Baja de cuenta docente desde Mi plan, con confirmacion por clave antes de
  borrar el perfil y sus datos asociados.
- Cierre de sesion docente desde Inicio y Mi plan, limpiando la sesion local y
  la clave visible al volver a la pantalla de entrada.
- Botones para iniciar suscripcion Mercado Pago de plan Docente o Pro.
- Pantalla de historial local de clases de la sesion.
- Pantalla de contenido generado editable, incluyendo cuestionario y tarea para
  el hogar.
- Pantalla opcional para adaptar la clase.
- Pantalla para ver apoyos generados.
- Pantalla de vista alumno con resumen, reproduccion de audios locales, vista
  de imagenes locales y apoyos.
- Vista alumno puede descargar temporalmente imagenes/audios remotos para
  previsualizar o reproducir dentro de la app.
- Vista alumno con tarjetas visuales para resumen, apoyos, audios e imagenes,
  pensada para que el estudiante encuentre rapido que leer, escuchar o ver.
- Vista alumno con boton para descargar el paquete completo de la clase por
  codigo y abrir la carpeta cuando queda listo.
- Entrada de codigo de clase en vista alumno.
- Pantalla de recursos permite elegir y adjuntar imagenes o audios locales del
  docente.
- Los recursos del docente se suben como archivos reales al backend/Storage en
  vez de guardar solo una ruta local.
- Flujo completo conectado: generar clase -> editar -> adaptar o saltar ->
  recursos -> voz -> exportar.
- Pantalla de seleccion de recursos.
- Pantalla de voz.
- Pantalla de video informativa.
- Pantalla de exportacion PDF/PowerPoint/ZIP.
- Acciones para copiar el codigo alumno y compartirlo por WhatsApp.
- Boton para abrir carpeta de exportaciones.
- Exportaciones con nombre corto en pantalla y archivos reales en disco.
- Ajuste basico de PowerPoint para que titulos largos no se salgan de la
  diapositiva.
- Historial de clases mas util para docentes: muestra tarjetas con materia,
  duracion, fecha, codigo alumno y accesos directos a editar, exportar, vista
  alumno y copiar codigo.
- Historial con busqueda por tema, materia, edad, codigo o prompt original,
  para funcionar como primer banco personal de clases del docente.
- Primera base visual inspirada en mockup profesional: fondo calido, azul
  profundo, textos sobrios y botones mas consistentes.

## Log de avance

### 2026-06-26

- Se reviso el proyecto inicial y se confirmo stack FastAPI + KivyMD +
  Supabase.
- Se agrego modo desarrollo en memoria para poder probar sin Supabase real.
- Se conecto el flujo base de creacion de clases.
- Se generaron PDF reales locales.
- Se generaron PowerPoint reales locales.
- Se agrego boton para abrir carpeta de exportaciones.
- Se mejoro el generador local de contenido pedagogico.
- Se dejo integracion opcional con OpenAI para contenido real.
- Se agregaron planes y cuotas al backend.
- Se agregaron apoyos pedagogicos para TDAH, TEA/autismo, lectura facil,
  ansiedad, dificultad lectora y baja vision.
- Se agrego pantalla frontend para adaptar la clase.
- Se agrego pantalla frontend para ver apoyos generados.
- Se hizo que PDF y PowerPoint incluyan las adaptaciones educativas.
- Se documento la vision, objetivos y roadmap vivo de ProfeIA.
- Se agrego historial local de clases para reabrir clases creadas durante la
  sesion.
- Se agrego backend para adjuntar imagenes/audios propios del docente.
- Se agrego paquete alumno con resumen, audio, imagenes, audios docentes y
  apoyos.
- Se agrego pantalla frontend de vista alumno dentro de la app actual.
- Se agrego codigo publico de clase y endpoint publico para vista alumno por
  codigo.
- Se agrego exportacion de paquete ZIP descargable con PDF, PowerPoint,
  manifiesto, codigo alumno y recursos de la clase.
- Se corrigio el desborde de titulos largos en las diapositivas PowerPoint.
- Se agrego selector local para adjuntar imagenes y audios propios del docente
  desde la pantalla de recursos.
- Se tomo como referencia visual un mockup sobrio para docentes y se empezo a
  trasladar esa identidad a la app.
- Se agrego reproduccion local de audio y apertura/vista previa de imagenes en
  la vista alumno.
- Se corrigio la arquitectura de entrada: el alumno ya no navega como profesor,
  entra con codigo desde la primera pantalla.
- Se agrego registro/login local para docentes como seguridad inicial de
  entrada al constructor.
- Se agrego copia del codigo alumno y mensaje para compartir por WhatsApp.
- Se agrego persistencia local de desarrollo para no perder docentes, clases,
  codigos y recursos al reiniciar el backend.
- Se agrego pantalla Mi plan para que el docente vea cuotas y planes.
- Se preparo integracion inicial de suscripciones con Mercado Pago.
- Se agrego subida de recursos a Supabase Storage con bucket `recursos-clases`.
- Se mejoro la vista alumno para abrir recursos remotos de Storage dentro de la
  app cuando sea posible.
- Se mejoro el historial docente para reabrir clases guardadas, copiar el
  codigo alumno y saltar directo a exportacion o vista alumno.
- Se mejoro la vista alumno con tarjetas para resumen, apoyos y recursos,
  dejando mas claro que puede escuchar audios, ver imagenes o abrir recursos.
- Se agrego descarga de paquete ZIP desde la vista alumno usando el codigo
  publico de la clase.
- Se agrego control real de cuotas mensuales por plan: el backend valida cupo
  antes de consumir funciones y registra uso despues de cada accion exitosa.
- Se actualizo Mi plan para leer el uso mensual real y se mejoraron los
  mensajes cuando se alcanza un limite.
- Se completo el flujo de Mercado Pago: checkout, estado pendiente, webhook
  firmado opcional, consulta de preapproval y activacion/cancelacion del plan
  del docente.
- Se agrego activacion demo desde Mi plan para probar planes pagos sin token
  real de Mercado Pago.
- Se agrego buscador al historial para encontrar clases guardadas por tema,
  materia, publico o codigo alumno.
- Se agrego eliminacion de cuenta docente con confirmacion de clave y limpieza
  de sesion al finalizar.
- Se agrego cierre de sesion docente para salir de la cuenta sin cerrar la app.
- Se agregaron plantillas rapidas para que el docente pueda iniciar una clase
  desde una estructura prearmada y editable.
- Se agrego texto predictivo con sugerencias aplicables al prompt para acelerar
  la creacion de clases.
- Se agrego cuestionario y tarea para el hogar al contenido generado, edicion,
  vista alumno y exportaciones.
- Se integro la eleccion de apoyos educativos en la pantalla inicial y se
  precarga esa seleccion en la pantalla de adaptacion de clase.
- Se compacto la pantalla inicial: el prompt queda primero, las plantillas se
  muestran como acciones rapidas cortas, edad/materia comparten fila y los
  apoyos aparecen en grilla para reducir scroll.
- Se conecto el backend de imagenes reales: cuando hay `IA_IMAGENES_API_KEY`,
  genera PNG con OpenAI Images, lo guarda en Storage/local y lo registra como
  recurso de la clase; sin key conserva el modo simulado.
- Se conecto el backend de voz real: OpenAI TTS para voces narradas comunes y
  ElevenLabs para una voz clonada preexistente con `voice_id`; sin keys conserva
  el modo simulado.
- Se limpio el generador local para extraer el tema real del pedido docente y
  evitar repetir textos como "Crea una clase..." en titulo, objetivo, preguntas
  y resumen cuando OpenAI no esta disponible.
- Se evito que las plantillas rapidas del frontend se encadenen entre si al
  presionarlas varias veces.
- Se mejoro el espaciado de listas en PDF para que ejemplos, preguntas y
  adaptaciones no queden pegados al exportar o copiar texto.
- Se agrego generacion local gratuita de laminas visuales PNG para clases de
  tablas/multiplicacion, sin depender de IA paga.
- El PDF ahora puede generarse como documento visual y agregar una pagina con
  lamina de tablas del 1 al 9 cuando detecta ese tema.
- Storage ahora tiene fallback local: si Supabase Storage no responde, guarda
  el recurso en disco para no frenar el flujo de desarrollo.
- Se agrego busqueda de imagenes gratuitas en Wikimedia Commons desde Recursos:
  la app extrae palabras clave de la clase, descarga imagenes con metadata de
  fuente/licencia y las adjunta a la clase; si no hay internet, cae a imagenes
  locales sin costo.
- La pantalla de Recursos ahora ofrece dos caminos: imagenes IA/locales y
  "Buscar imagenes gratis" para trabajar sin pagar IA.
- Se mejoro fuerte el generador local gratuito: limpia typos y pedidos
  genericos, detecta duracion escrita en el prompt, evita repetir "crear una
  clase" y agrega rutas pedagogicas especificas para tablas de multiplicar y
  fracciones con ejemplos, preguntas, cuestionario y tarea mas completos.
- Se agrego una primera base local por materias argentinas: Matematica, Lengua,
  Ciencias Naturales, Ciencias Sociales, Ingles y Educacion Artistica. Cada
  perfil aporta eje pedagogico, situacion de aula, estrategia, actividad y
  producto esperado para que la app no dependa de IA paga.
- Se agrego enriquecimiento local con Wikipedia: cuando no se usa OpenAI, la app
  intenta buscar un resumen abierto del tema, incorpora contexto y fuente en la
  clase, y si no hay internet vuelve al generador local sin cortar el flujo.
- Se endurecio la limpieza de temas para quitar destinatarios como "para
  primaria" o "cuarto grado" antes de buscar en Wikipedia, y se valida que el
  resultado encontrado sea relevante antes de incorporarlo a la clase.
- Se mejoro la salida en espanol del generador local y el PDF visual ahora usa
  fuentes Unicode de Windows para conservar caracteres como ñ y acentos.
- Se reforzaron los filtros de entrada: edad/grado y materia pasan a ser
  obligatorios en la pantalla inicial, se elimina el default "Matematica" y el
  backend puede corregir la materia por palabras clave (por ejemplo futbol,
  pases o tiros -> Educacion Fisica).
- Se ordeno la busqueda de imagenes gratuitas con mas filtros por materia,
  tema y palabras clave para evitar recursos incoherentes; si no encuentra una
  imagen confiable, avisa y usa fallback local sin costo.
- Se alineo el flujo de exportacion con la vista alumno: PDF y ZIP usan los
  mismos bloques centrales de la clase, incorporan recursos locales cuando
  estan disponibles y el manifiesto del ZIP indica el archivo interno de cada
  recurso.
- Se agrego un validador local de flujo completo en
  `scripts/validar_flujo_local.py` para probar sin Supabase real ni IA paga:
  genera clase, recursos, vista alumno, PDF y ZIP desde backend.

## Matriz de IA recomendada

- Texto pedagogico: OpenAI Responses API con `gpt-4o-mini` para MVP por costo,
  velocidad y salida JSON estructurada.
- Imagenes: OpenAI Images con `gpt-image-1` para MVP, con fallback local si
  la API devuelve limite, modelo no disponible o error temporal.
- Voz narrada comun: OpenAI TTS con `gpt-4o-mini-tts`, suficiente para resumen
  de clase y audio alumno.
- Voz clonada: ElevenLabs con voice_id y consentimiento explicito del docente.
  La clonacion/creacion de la voz debe ser un flujo separado con autorizacion.
- Video: dejar para etapa posterior; conviene ensamblar primero escenas propias
  con texto, imagenes y audio ya generados antes de pagar generacion de video.

## Adaptaciones educativas

La app debe ofrecer apoyos pedagogicos, no diagnosticos medicos. La idea es que
el docente pueda adaptar una clase para que sea mas clara, previsible y facil
de seguir.

Apoyos incluidos actualmente:

- Atencion / TDAH.
- TEA / autismo.
- Lectura facil.
- Ansiedad o participacion gradual.
- Rutina visual.
- Pausas breves.
- Consignas simples.
- Verificacion de comprension.
- Evaluacion flexible.

## Multimedia deseada

La app debe crecer hacia:

- Imagenes generadas para explicar la clase.
- Imagenes propias subidas por el docente.
- Slides automaticas.
- Voz narrada.
- Audio propio del docente leyendo el resumen o explicando la clase.
- Clonacion de voz del docente con consentimiento explicito.
- Grabacion de clase desde la casa del docente.
- Generacion de video automatico.
- Edicion simple de escenas.
- Exportacion ZIP para entregar una clase completa por archivo.
- Exportacion para redes sociales.

## Planes y monetizacion

La app no debe prometer uso ilimitado de IA, porque cada generacion puede tener
costo. El modelo recomendado es por planes o creditos.

Planes pensados:

- Gratis: pocas clases para probar.
- Docente: uso individual mensual.
- Pro: docentes que generan mucho contenido o publican.
- Institucion: colegios, academias o equipos docentes.

Cada plan puede limitar:

- Cantidad de clases.
- Imagenes.
- Voces.
- Videos.
- Minutos de grabacion.
- Clonaciones de voz.
- PDF/PPTX.
- Adaptaciones de accesibilidad.

## Principios importantes

- La IA debe ayudar al docente, no reemplazarlo.
- El docente siempre debe poder editar.
- Las adaptaciones para TDAH/TEA deben ser respetuosas, pedagogicas y no
  clinicas.
- La voz clonada debe requerir consentimiento claro.
- La cuenta docente debe usar Supabase Auth en produccion; el login local es
  solo para el MVP de desarrollo.
- El gasto de IA debe estar controlado por backend.
- La app debe funcionar primero como MVP local y luego conectarse a Supabase.
- El valor principal es ahorrar tiempo y mejorar la calidad del material.
- La estetica debe sentirse profesional, clara y confiable: fondo calido,
  superficies blancas, azul profundo como accion principal y bordes discretos.
- El alumno debe tener un acceso simple y separado del docente: abrir app,
  escribir codigo y ver la clase.

## Ideas para incluir despues

- Historial de clases.
- Banco de clases por materia y edad.
- Busqueda de clases anteriores.
- Plantillas por nivel educativo.
- Modo "clase de 5 minutos".
- Modo "semana completa".
- Rubricas de evaluacion.
- Cuestionarios automaticos.
- Tareas para el hogar.
- Actividades diferenciadas por nivel.
- Version para imprimir.
- Version para presentar en pantalla.
- Version para estudiantes con lectura facil.
- Version para audio.
- Biblioteca de imagenes generadas.
- Editor visual de slides.
- Pulido visual general de la app cuando el flujo funcional este mas cerrado.
- Generador de video vertical para redes.
- Publicacion directa a YouTube, TikTok, Instagram o WhatsApp si las APIs lo
  permiten.
- Panel institucional para directivos.
- Estadisticas de uso por docente.
- Control de creditos y costos.
- Suscripciones con Mercado Pago para planes pagos.
- Mercado de clases compartidas entre docentes.

## Proximos pasos sugeridos

1. Probar Mercado Pago con comprador de prueba y luego configurar webhook publico.
2. Reemplazar login local docente por Supabase Auth real.
3. Agregar descarga/uso offline del paquete alumno.
4. Mejorar vista previa integrada de recursos remotos dentro de la app.
5. Probar imagenes reales con API key configurada y revisar costo/calidad.
6. Probar voz real con API key configurada y revisar calidad/costo.
7. Disenar flujo de grabacion del docente.
8. Crear banco de plantillas por nivel, materia y tipo de clase.
9. Agregar rubricas, cuestionarios y tareas para el hogar.
10. Pulido visual general antes de la prueba completa.
