# SUGERENCIAS Y GUÍA DEL PROYECTO — ELMASME (Universal Viewer)

---

## PARTE 1: 10 SUGERENCIAS DE MEJORAS DE ACCESIBILIDAD Y FUNCIONES NUEVAS

### 1. Atajos de teclado configurables
Permitir al usuario personalizar los atajos de teclado (play/pause, siguiente, anterior, zoom, etc.) desde un panel de configuración.

### 2. Soporte de lector de pantalla (screen reader)
Agregar `accessibleName` y `accessibleDescription` a todos los widgets interactivos para compatibilidad con lectores de pantalla como NVDA o JAWS.

### 3. Modo de alto contraste
Agregar un tema de alto contraste con bordes gruesos, texto grande y colores fuertemente diferenciados para usuarios con baja visión.

### 4. Navegación completa por teclado
Implementar un orden de tabulación (Tab order) lógico en todos los paneles para que la interfaz sea 100% navegable sin mouse.

### 5. Subtítulos y soporte de archivos SRT/VTT
En el reproductor de video, permitir cargar archivos de subtítulos (.srt, .vtt) y mostrarlos superpuestos sobre el video.

### 6. Barra de búsqueda de archivos
Agregar una barra de búsqueda rápida que filtre los archivos cargados en la pestaña activa o en la playlist por nombre.

### 7. Vista previa en miniatura (thumbnails)
Generar y mostrar miniaturas de los archivos en la lista de reproducción y en la navegación de carpetas.

### 8. Ecualizador de audio
Agregar un ecualizador gráfico básico (graves, medios, agudos) para el reproductor de audio.

### 9. Historial de archivos recientes
Mantener un listado de los últimos 20 archivos abiertos, accesible desde el menú o footer, para reapertura rápida.

### 10. Zoom por gestos de trackpad
Soportar gestos de pinch-to-zoom en trackpads para el visor de imágenes y documentos PDF.

---

## PARTE 2: GUÍA TÉCNICA DE COMPOSICIÓN DEL PROYECTO

### Punto de entrada

| Archivo | Función |
|---------|---------|
| `main.py` | Punto de entrada. Crea QApplication, resuelve ruta inicial de argv, instancia UniversalViewerWindow. |

### Ventana principal y UI

| Archivo | Función |
|---------|---------|
| `app_window.py` | Ventana principal (QMainWindow). Maneja pestañas (QTabWidget), footer con navegación, botones de Archivo/Integración, selector de tema. Contiene _build_footer, _build_ui, lógica de drag&drop, diálogos de apertura y navegación. |
| `content_viewers.py` | ViewerHost: QStackedWidget que aloja ImageViewer, AudioViewer, VideoViewer y DocumentViewer. Detecta tipo de archivo y muestra el visor correcto. También gestiona cambios no guardados de documentos. |
| `file_navigation.py` | FileNavigator: clase pura que mantiene lista de archivos compatibles en una carpeta y gestiona anterior/siguiente. |
| `themes.py` | Define 4 temas (Oscuro, Claro, Cyberpunk 2038, Retro Terminal) como stylesheets completas de Qt. Función get_theme(name) retorna el stylesheet. |

### Visores específicos por tipo de contenido

| Archivo | Función |
|---------|---------|
| `image_viewer.py` | ImageViewer: visor de imágenes con zoom, pan (arrastre), pantalla completa, redimensionamiento. Usa PanLabel para arrastre y QScrollArea. |
| `video_player.py` | VideoViewer: reproductor de video con QMediaPlayer + QVideoWidget. Controles play/pause/stop/volumen en overlay flotante con auto-ocultar y botón de fijar. Botón "Edición" con dropdown para Convertir, Convertir playlist, Recortar. Incluye ClickableVideoWidget con mouse tracking. |
| `audio_player.py` | AudioViewer: reproductor de audio con QMediaPlayer. Placeholder visual con info del archivo. Overlay flotante de controles con auto-ocultar. Botón "Edición" con dropdown para Convertir, Convertir playlist, Recortar. |
| `document_viewer.py` | DocumentViewer: visor de documentos (PDF y texto). Usa QStackedWidget para alternar entre QPdfView y QTextEdit. Incluye toolbar de edición y zoom para PDF. |

### Conversión y edición de medios

| Archivo | Función |
|---------|---------|
| `image_converter.py` | Conversión y redimensionamiento de imágenes. Define IMAGE_EXTENSIONS, FORMAT_NAMES. Contiene ImageResizeDialog, funciones save_image, resize_image. |
| `audio_converter.py` | Conversión de audio vía ffmpeg. Define AUDIO_EXTENSIONS, FORMAT_NAMES. Contiene AudioConverterDialog, AudioBatchConverterDialog, AudioTrimDialog, funciones convert_audio, is_ffmpeg_available. |
| `video_converter.py` | Conversión de video vía ffmpeg. Define VIDEO_EXTENSIONS, FORMAT_NAMES, FORMAT_CODECS. Contiene VideoConverterDialog, VideoBatchConverterDialog, VideoTrimDialog, funciones convert_video, is_ffmpeg_available. |
| `document_editor.py` | TextEditorToolbar: barra de herramientas para edición de texto (negrita, cursiva, fuentes, colores, alineación, guardar). Funciones read_text_file, save_text_file. |
| `document_pdf.py` | Funciones específicas de PDF. Define PDF_EXTENSIONS. Función extract_pdf_text extrae texto de QPdfDocument. |

### Playlists

| Archivo | Función |
|---------|---------|
| `audio_playlist.py` | AudioPlaylistWidget: gestión de lista de reproducción de audio. Agregar/quitar archivos, ordenar (nombre/fecha/tamaño/aleatorio), guardar/cargar como JSON, drag & drop. |
| `video_playlist.py` | VideoPlaylistWidget: idéntico a AudioPlaylistWidget pero para archivos de video. |

### Utilidades y re-exportaciones

| Archivo | Función |
|---------|---------|
| `formats.py` | Módulo central de formatos. Importa extensiones de todos los handlers. Funciones: get_content_type, is_supported, display_type, supported_extensions. |
| `windows_integration.py` | Integración con Windows: registro/desregistro de asociaciones de archivos en HKEY_CURRENT_USER, apertura de configuración de apps predeterminadas. |
| `progress_bar.py` | ConversionProgressBar: barra de progreso flotante (frameless, roja) para conversiones. Se muestra centrada en pantalla. |
| `image_handler.py` | Re-exporta desde image_converter e image_viewer. |
| `audio_handler.py` | Re-exporta desde audio_converter, audio_player y audio_playlist. |
| `video_handler.py` | Re-exporta desde video_converter, video_player y video_playlist. |
| `document_handler.py` | Re-exporta desde document_pdf, document_editor y document_viewer. |

### Guía de adjuntar archivos a un agente de código

Para un cambio puntual, adjunta SOLO los archivos que correspondan según esta tabla:

| Si el cambio es en... | Adjunta estos archivos |
|---|---|
| Ventana principal, pestañas, footer, navegación | `app_window.py`, `content_viewers.py`, `file_navigation.py` |
| Temas visuales, estilos | `themes.py`, `app_window.py` |
| Visor de imágenes | `image_viewer.py`, `image_converter.py` |
| Reproductor de video | `video_player.py`, `video_converter.py`, `video_playlist.py` |
| Reproductor de audio | `audio_player.py`, `audio_converter.py`, `audio_playlist.py` |
| Visor/editor de documentos | `document_viewer.py`, `document_editor.py`, `document_pdf.py` |
| Conversión de archivos | El `*_converter.py` correspondiente + `progress_bar.py` |
| Playlists | El `*_playlist.py` correspondiente |
| Formatos soportados | `formats.py` + el `*_handler.py` y `*_converter.py` correspondiente |
| Integración con Windows | `windows_integration.py`, `formats.py` |
| Punto de entrada / inicio | `main.py`, `app_window.py` |
