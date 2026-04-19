# ESTRUCTURA ACTUALIZADA DEL PROYECTO ELMASME

## Descripción General

**ELMASME** es un visor/editor universal de archivos multimedia y documentos para Windows (10 y 11).
Está construido con **Python 3** y **PySide6** (Qt 6). Es una aplicación de escritorio que soporta
imágenes, audio, video, documentos de texto, PDF, hojas de cálculo, presentaciones, archivos
comprimidos y libros electrónicos.

---

## Punto de Entrada

| Archivo | Descripción |
|---------|-------------|
| `main.py` (30 líneas) | Punto de entrada. Crea `QApplication`, resuelve ruta de archivo desde `sys.argv`, instancia `UniversalViewerWindow` y ejecuta el event loop. |

---

## Ventana Principal y UI

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `app_window.py` | ~743 | Ventana principal (`UniversalViewerWindow`). Maneja pestañas (`QTabWidget`), navegación de archivos, footer con ruta completa, menú Archivo, diálogo de ajustes (temas, integración Windows, reproducción), diálogo de bienvenida al primer inicio, drag & drop, atajos de teclado. |
| `content_viewers.py` | ~127 | `ViewerHost` — widget contenedor con `QStackedWidget` que aloja todos los viewers (imagen, audio, video, documento, archivo, hoja, presentación, ebook). Enruta `load_file()` al viewer apropiado según tipo. |
| `themes.py` | ~390 | Define 4 temas visuales: Oscuro, Claro, Cyberpunk, Retro. Cada tema es un stylesheet CSS-Qt completo. |

---

## Navegación y Formatos

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `file_navigation.py` | ~86 | `FileNavigator` — carga archivos compatibles de una carpeta, proporciona `previous()`, `next()`, `current()` para navegación secuencial. |
| `formats.py` | ~116 | Centraliza todas las extensiones soportadas. Define `ALL_SUPPORTED_EXTENSIONS`, `ASSOCIATION_EXTENSIONS`, funciones `get_content_type()`, `is_supported()`, `display_type()`. Importa extensiones desde cada handler. |

---

## Configuración y Persistencia

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `settings.py` | ~42 | Guarda/carga configuración en JSON (`%APPDATA%/ELMASME/settings.json`). Claves: `theme_index`, `no_multi_playback`, `show_welcome`. |

---

## Integración con Windows

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `windows_integration.py` | ~203 | Registra asociaciones de archivos en el registro de Windows (`HKCU\Software\Classes`). Soporta "Abrir con" (contexto y doble clic), icono personalizado (`icons/elmasme.ico`), `RegisteredApplications` para Win10/11, notificación al shell (`SHChangeNotify`). |

---

## Directorio de Recursos

| Carpeta/Archivo | Descripción |
|-----------------|-------------|
| `icons/elmasme.ico` | Icono de la aplicación (multi-resolución: 16, 32, 48, 64, 128, 256px). Se usa para asociaciones de archivos y la ventana. |

---

## Viewers de Contenido

### Imágenes

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `image_handler.py` | ~17 | Define `IMAGE_EXTENSIONS` y la clase proxy `ImageViewer`. |
| `image_viewer.py` | ~609 | Visor de imágenes completo. Toolbar estilo Paint (zoom, pantalla completa, redimensionar, rotar, voltear). Canvas con `QGraphicsView`. Soporta modo anotaciones. |
| `image_annotations.py` | ~388 | `AnnotationOverlay` — permite dibujar flechas, rectángulos, círculos, texto y trazo libre sobre imágenes. Método `burn_to_image()` para guardar anotaciones permanentemente. |
| `image_converter.py` | ~912 | Conversión de imágenes entre formatos (PNG, JPEG, BMP, WEBP, TIFF, etc.). Incluye ajuste de calidad, resolución, y procesamiento batch. |

### Audio

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `audio_handler.py` | ~13 | Define `AUDIO_EXTENSIONS` y la clase proxy `AudioViewer`. |
| `audio_player.py` | ~379 | Reproductor de audio con barra fija inferior (play/pause, volumen, seek bar, herramientas). |
| `audio_playlist.py` | ~366 | Gestor de playlist de audio. Permite añadir, eliminar, reordenar pistas. |
| `audio_converter.py` | ~729 | Conversión de audio entre formatos (MP3, WAV, OGG, FLAC, etc.) con ajuste de bitrate y sample rate. |

### Video

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `video_handler.py` | ~16 | Define `VIDEO_EXTENSIONS` y la clase proxy `VideoViewer`. |
| `video_player.py` | ~1054 | Reproductor de video completo. Controles en barra fija inferior, fullscreen con ventana dedicada, overlay con `eventFilter`. |
| `video_playlist.py` | ~366 | Gestor de playlist de video. Funcionalidad similar a audio_playlist. |
| `video_converter.py` | ~801 | Conversión de video entre formatos (MP4, AVI, MKV, WEBM, etc.) con ajuste de resolución, codec y bitrate. |

### Documentos

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `document_handler.py` | ~20 | Define `PDF_EXTENSIONS`, `TEXT_DOCUMENT_EXTENSIONS`, `DOCX_EXTENSIONS`, `DOCUMENT_EXTENSIONS` y la clase proxy `DocumentViewer`. |
| `document_viewer.py` | ~959 | Visor de documentos. Soporta texto plano, DOCX (via zipfile+xml), EPUB, RTF, ODT. Tiene barra de estado con zoom, búsqueda, alto contraste. Integra editor PDF via toggle. |
| `document_editor.py` | ~991 | `TextEditorToolbar` — barra de herramientas tipo Word para edición de texto enriquecido (negrita, cursiva, listas, alineación, fuente, tamaño, color, insertar imagen/tabla). |
| `document_pdf.py` | ~14 | Utilidad mínima para importación de PDF. |

### PDF

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `pdf_editor.py` | ~1000 | `PdfEditorWidget` — editor visual de PDF con PyMuPDF (fitz) + QGraphicsScene/View. Soporta insertar/mover texto, imágenes, hipervínculos, anotaciones highlight. |
| `pdf_tools.py` | ~373 | Herramientas PDF: merge, split, extraer texto, extraer imágenes. Integrado en DocumentViewer. |

### Otros Formatos

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `archive_viewer.py` | ~365 | Visor de archivos comprimidos (ZIP, TAR, GZ, BZ2, XZ, RAR, 7z). Lista contenidos y permite extracción. |
| `spreadsheet_viewer.py` | ~445 | Visor de hojas de cálculo (XLSX, XLS, ODS, CSV). Muestra en tabla Qt. |
| `presentation_viewer.py` | ~369 | Visor de presentaciones (PPTX, ODP). Renderiza diapositivas. |
| `ebook_viewer.py` | ~384 | Visor de libros electrónicos (EPUB, MOBI). |

---

## Utilidades

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `diff_viewer.py` | ~291 | Comparador de documentos lado a lado. |
| `progress_bar.py` | ~101 | Barra de progreso reutilizable para operaciones largas (conversiones, etc.). |

---

## Flujo General de la Aplicación

1. `main.py` → crea `QApplication` → parsea argv → crea `UniversalViewerWindow(start_path)`
2. `UniversalViewerWindow.__init__()`:
   - Carga settings desde `settings.py`
   - Construye UI con pestañas, footer, atajos
   - Si hay `start_path`, abre en nueva pestaña
   - Si es primera vez (`show_welcome=True`), muestra diálogo de bienvenida
3. Cada pestaña contiene un `ViewerHost` con `QStackedWidget`
4. Al cargar un archivo: `formats.get_content_type()` determina el tipo → `ViewerHost.load_file()` muestra el viewer apropiado
5. `FileNavigator` permite navegar entre archivos de la misma carpeta
6. Los botones ◀/▶ del footer navegan, la barra central muestra la ruta completa del archivo activo
7. Integración Windows: registro en `HKCU\Software\Classes` para "Abrir con" y doble clic

---

## Dependencias Principales

- **PySide6** — Framework Qt 6 para la interfaz gráfica
- **PyMuPDF (fitz)** — Renderizado y edición de PDF
- **Pillow** — Procesamiento de imágenes
- **FFmpeg** (externo) — Conversión de audio/video (invocado via subprocess)

---

# SUGERENCIAS DE FUNCIONES

## 10 Sugerencias para el Gestor de Imágenes

1. **Recorte inteligente con proporciones fijas** — Permitir recortar imágenes con proporciones preestablecidas (1:1, 4:3, 16:9) además de recorte libre.
2. **Filtros y efectos rápidos** — Aplicar filtros como blanco y negro, sepia, negativo, desenfoque gaussiano, nitidez con un clic.
3. **Ajuste de brillo/contraste/saturación en tiempo real** — Deslizadores para ajustar estas propiedades con vista previa instantánea.
4. **Marca de agua personalizable** — Insertar texto o imagen como marca de agua con posición, opacidad y tamaño configurables.
5. **Conversión batch de formatos** — Convertir múltiples imágenes seleccionadas de un formato a otro en una sola operación.
6. **Comparación antes/después con slider** — Mostrar la imagen original y la editada lado a lado con un deslizador interactivo.
7. **Histograma RGB en tiempo real** — Mostrar un gráfico del histograma de colores de la imagen actual.
8. **OCR (reconocimiento óptico de caracteres)** — Extraer texto de imágenes usando Tesseract OCR.
9. **Slideshow automático** — Presentación de diapositivas con las imágenes de la carpeta, con intervalo configurable y transiciones.
10. **Exportar a PDF** — Generar un PDF con las imágenes seleccionadas (útil para escaneos o álbumes).

## 10 Sugerencias para el Gestor de Video

1. **Captura de fotograma (screenshot)** — Exportar el cuadro actual del video como imagen PNG/JPEG.
2. **Extracción de audio** — Extraer la pista de audio del video a MP3/WAV/FLAC.
3. **Subtítulos externos** — Cargar y mostrar archivos .srt/.vtt superpuestos en el video.
4. **Control de velocidad de reproducción** — Ajustar velocidad de 0.25x a 4x con un slider.
5. **Marcadores de tiempo** — Permitir guardar marcadores en puntos específicos del video para saltar rápidamente.
6. **Picture-in-Picture** — Modo ventana flotante pequeña que permanece sobre otras ventanas.
7. **Recorte de video (trim)** — Seleccionar punto de inicio y fin para exportar un segmento del video.
8. **Ajuste de brillo/contraste/saturación en tiempo real** — Aplicar filtros visuales al video durante la reproducción.
9. **Rotación y volteo** — Rotar 90°/180°/270° y voltear horizontal/verticalmente.
10. **Generación de miniaturas** — Crear automáticamente una cuadrícula de miniaturas del video en intervalos regulares.

## 10 Sugerencias para el Gestor de Audio

1. **Ecualizador gráfico** — Ecualizador de 10 bandas para ajustar frecuencias en tiempo real.
2. **Visualización de forma de onda** — Mostrar el waveform completo del audio con posición de reproducción.
3. **Normalización de volumen** — Ajustar automáticamente el volumen a un nivel estándar.
4. **Fade in/out** — Aplicar efectos de entrada y salida gradual al inicio y fin de la pista.
5. **Detección de BPM** — Analizar y mostrar el tempo (beats por minuto) de la pista.
6. **Editor de metadatos ID3** — Editar artista, álbum, género, año, carátula directamente desde la app.
7. **Grabación de audio** — Grabar audio desde el micrófono del sistema.
8. **Espectrograma en tiempo real** — Mostrar la representación visual frecuencia/tiempo del audio.
9. **Unión de archivos de audio** — Concatenar múltiples archivos de audio en secuencia.
10. **Sleep timer** — Temporizador para detener la reproducción automáticamente después de un tiempo.

## 10 Sugerencias para el Gestor de Documentos

1. **Resaltado de sintaxis** — Colorear código fuente en archivos .py, .js, .html, .css, etc. automáticamente.
2. **Buscar y reemplazar con regex** — Buscar texto con expresiones regulares y reemplazar en todo el documento.
3. **Numeración de líneas** — Mostrar números de línea en el margen izquierdo del editor de texto.
4. **Modo lectura sin distracciones** — Pantalla completa solo con el texto, sin toolbars ni menús.
5. **Auto-guardado periódico** — Guardar automáticamente cada X minutos para prevenir pérdida de datos.
6. **Plantillas de documento** — Crear nuevos documentos desde plantillas predefinidas (carta, informe, acta).
7. **Contador de palabras avanzado** — Mostrar palabras, caracteres, párrafos, tiempo estimado de lectura.
8. **Exportar a PDF** — Convertir el documento de texto actual a formato PDF.
9. **Soporte Markdown** — Renderizar archivos .md con formato visual (encabezados, listas, enlaces, código).
10. **Comparación de documentos** — Mejorar el diff viewer existente con merge interactivo y resolución de conflictos.

## 10 Sugerencias para el Gestor de PDF

1. **Firma digital** — Permitir insertar una firma manuscrita (dibujar o imagen) en el PDF.
2. **Anotaciones con notas adhesivas** — Agregar notas tipo "sticky note" en cualquier posición de la página.
3. **Rellenar formularios PDF** — Detectar y permitir completar campos de formulario interactivos.
4. **Protección con contraseña** — Cifrar/descifrar PDFs con contraseña.
5. **Reorganizar páginas** — Arrastrar y soltar para reordenar las páginas del PDF visualmente.
6. **Marca de agua en PDF** — Insertar texto o imagen como marca de agua en todas las páginas.
7. **Comprimir PDF** — Reducir el tamaño del archivo optimizando imágenes y contenido.
8. **Exportar páginas como imágenes** — Convertir páginas individuales o rangos a PNG/JPEG.
9. **Búsqueda avanzada en PDF** — Buscar texto con resaltado de resultados y navegación entre coincidencias.
10. **Comparación de PDFs** — Comparar dos PDFs lado a lado resaltando diferencias en texto e imágenes.

## 10 Sugerencias para el Programa en Sí

1. **Historial de archivos recientes** — Mantener una lista de los últimos 20 archivos abiertos, accesible desde el menú.
2. **Plugins/extensiones** — Sistema básico de plugins para que usuarios avanzados puedan agregar funcionalidad.
3. **Atajos de teclado configurables** — Permitir al usuario personalizar todos los atajos de teclado.
4. **Barra de búsqueda rápida** — Buscar y filtrar archivos por nombre dentro de la carpeta actual.
5. **Modo multi-monitor** — Permitir abrir viewers en ventanas separadas para aprovechar múltiples pantallas.
6. **Vista previa en miniatura** — Mostrar thumbnails de los archivos en la navegación de carpeta.
7. **Auto-actualización** — Verificar si hay versiones nuevas del programa y ofrecer actualización.
8. **Localización multi-idioma** — Soportar inglés y español (y ser extensible a otros idiomas) via archivos de traducción.
9. **Accesibilidad mejorada** — Agregar `accessibleName` a todos los widgets, soporte de lectores de pantalla, y navegación completa por teclado.
10. **Perfil de rendimiento** — Optimizar el tiempo de carga inicial reduciendo imports pesados (lazy loading de viewers que no se usan).
