# PROPUESTA DE REFACTORIZACIÓN — ELMASME

## Objetivo

Dividir los archivos más grandes en módulos más pequeños y cohesivos, manteniendo
todos los archivos de cada componente en la misma carpeta raíz del proyecto.

---

## Archivos Candidatos (ordenados por tamaño)

| Archivo | Líneas | Prioridad |
|---------|--------|-----------|
| `video_player.py` | 1054 | Alta |
| `pdf_editor.py` | 1000 | Alta |
| `document_editor.py` | 991 | Alta |
| `document_viewer.py` | 959 | Alta |
| `image_converter.py` | 912 | Media |
| `video_converter.py` | 801 | Media |
| `app_window.py` | 743 | Media |
| `audio_converter.py` | 729 | Media |
| `image_viewer.py` | 609 | Baja |

---

## Esquema de Refactorización Propuesto

### 1. `video_player.py` (1054 líneas) → 4 archivos

```
video_player.py           → Archivo principal, clase VideoPlayer (UI, layout, señales)
                            ~250 líneas

video_player_controls.py  → Clase VideoPlayerControls (barra de controles: play, pause,
                            volume, seek, botones de herramientas)
                            ~250 líneas

video_player_fullscreen.py → Clase _FullscreenWindow y _FullscreenFilter (lógica de
                             pantalla completa, reparenting de widgets, escape handler)
                             ~200 líneas

video_player_overlay.py   → Clase VideoOverlay (overlay flotante con eventFilter,
                            mapTo(), cursor tracking, enter/leave events)
                            ~350 líneas
```

### 2. `pdf_editor.py` (1000 líneas) → 4 archivos

```
pdf_editor.py             → Archivo principal, clase PdfEditorWidget (QGraphicsScene/View,
                            carga/renderizado de páginas, gestión de páginas)
                            ~350 líneas

pdf_editor_items.py       → Clases de items gráficos: _MovableTextItem,
                            _MovableImageItem, _MovableHighlightItem, _MovableLinkItem
                            ~300 líneas

pdf_editor_toolbar.py     → Barra de herramientas del editor PDF (botones insertar
                            texto, imagen, link, highlight, guardar)
                            ~150 líneas

pdf_editor_save.py        → Lógica de guardado: aplicar cambios al fitz.Document,
                            gestionar anotaciones, exportar PDF modificado
                            ~200 líneas
```

### 3. `document_editor.py` (991 líneas) → 3 archivos

```
document_editor.py        → Archivo principal, clase TextEditorToolbar (barra principal,
                            layout general, gestión de acciones de formato)
                            ~350 líneas

document_editor_format.py → Funciones y lógica de formato de texto: negrita, cursiva,
                            subrayado, alineación, listas, color, fuente, tamaño
                            ~350 líneas

document_editor_insert.py → Lógica de inserción: imágenes, tablas, hipervínculos,
                            caracteres especiales, separadores
                            ~290 líneas
```

### 4. `document_viewer.py` (959 líneas) → 3 archivos

```
document_viewer.py        → Archivo principal, clase DocumentViewer (carga de archivos,
                            QStackedWidget text/pdf, navegación)
                            ~350 líneas

document_viewer_pdf.py    → Lógica específica de PDF: renderizado de páginas,
                            barra PDF (_pdf_bar), integración con PdfEditorWidget,
                            herramientas PDF (merge, split, extract)
                            ~350 líneas

document_viewer_text.py   → Lógica específica de texto: _extract_docx_text,
                            carga de EPUB/RTF/ODT, alto contraste,
                            zoom y búsqueda en texto
                            ~260 líneas
```

### 5. `image_converter.py` (912 líneas) → 3 archivos

```
image_converter.py        → Archivo principal, clase ImageConverter (UI del diálogo,
                            selección de formato, opciones de calidad)
                            ~300 líneas

image_converter_batch.py  → Lógica de conversión batch: procesamiento de múltiples
                            archivos, barra de progreso, cola de conversión
                            ~300 líneas

image_converter_engine.py → Motor de conversión: Pillow transforms, redimensionado,
                            ajuste de calidad, metadatos, formato-specific options
                            ~310 líneas
```

### 6. `video_converter.py` (801 líneas) → 3 archivos

```
video_converter.py        → Archivo principal, UI del diálogo de conversión,
                            selección de formato y opciones
                            ~280 líneas

video_converter_engine.py → Motor FFmpeg: construcción de comandos, ejecución
                            de subprocess, parsing de progreso
                            ~280 líneas

video_converter_presets.py → Presets de conversión: resoluciones predefinidas,
                            codecs recomendados, perfiles de calidad
                            ~240 líneas
```

### 7. `app_window.py` (743 líneas) → 3 archivos

```
app_window.py             → Archivo principal, clase UniversalViewerWindow
                            (init, build_ui, themes, shortcuts, close)
                            ~300 líneas

app_window_tabs.py        → Gestión de pestañas: crear, cerrar, cambiar,
                            cargar archivo en pestaña, datos por pestaña
                            ~250 líneas

app_window_dialogs.py     → Diálogos: ajustes, bienvenida, elección de apertura,
                            cambios no guardados, menú Archivo
                            ~200 líneas
```

### 8. `audio_converter.py` (729 líneas) → 3 archivos

```
audio_converter.py        → Archivo principal, UI del diálogo de conversión
                            ~250 líneas

audio_converter_engine.py → Motor FFmpeg: comandos de audio, parsing de progreso,
                            ajuste de bitrate y sample rate
                            ~250 líneas

audio_converter_presets.py → Presets de audio: formatos, bitrates recomendados,
                            sample rates, canales
                            ~230 líneas
```

### 9. `image_viewer.py` (609 líneas) → 2 archivos

```
image_viewer.py           → Archivo principal, clase ImageViewer (QGraphicsView,
                            canvas, carga de imagen, zoom, pan)
                            ~350 líneas

image_viewer_toolbar.py   → Barra de herramientas: botones de zoom, fullscreen,
                            rotar, voltear, redimensionar, modo anotaciones
                            ~260 líneas
```

---

## Diagrama de Dependencias Propuesto

```
main.py
  └── app_window.py
        ├── app_window_tabs.py
        ├── app_window_dialogs.py
        ├── content_viewers.py
        │     ├── image_viewer.py + image_viewer_toolbar.py
        │     │     └── image_annotations.py
        │     ├── audio_player.py
        │     │     └── audio_playlist.py
        │     ├── video_player.py + video_player_controls.py
        │     │     ├── video_player_fullscreen.py
        │     │     ├── video_player_overlay.py
        │     │     └── video_playlist.py
        │     ├── document_viewer.py
        │     │     ├── document_viewer_pdf.py
        │     │     │     ├── pdf_editor.py + pdf_editor_items.py
        │     │     │     │     ├── pdf_editor_toolbar.py
        │     │     │     │     └── pdf_editor_save.py
        │     │     │     └── pdf_tools.py
        │     │     ├── document_viewer_text.py
        │     │     └── document_editor.py
        │     │           ├── document_editor_format.py
        │     │           └── document_editor_insert.py
        │     ├── archive_viewer.py
        │     ├── spreadsheet_viewer.py
        │     ├── presentation_viewer.py
        │     └── ebook_viewer.py
        ├── formats.py
        ├── file_navigation.py
        ├── settings.py
        ├── themes.py
        └── windows_integration.py
```

---

## Conversores (accedidos desde viewers)

```
image_converter.py
  ├── image_converter_batch.py
  └── image_converter_engine.py

video_converter.py
  ├── video_converter_engine.py
  └── video_converter_presets.py

audio_converter.py
  ├── audio_converter_engine.py
  └── audio_converter_presets.py
```

---

## Reglas de la Refactorización

1. **Todos los archivos permanecen en la carpeta raíz** — No se crean subcarpetas.
2. **Prefijo común** — Los archivos derivados comparten prefijo con el original (ej: `video_player_controls.py` viene de `video_player.py`).
3. **Imports explícitos** — Cada archivo nuevo exporta solo las clases/funciones que otros necesitan.
4. **Sin cambios de API** — Las clases públicas mantienen la misma interfaz. Solo se mueve código interno.
5. **Orden de ejecución** — Refactorizar un archivo a la vez, ejecutando tests después de cada cambio.
6. **Archivos handler sin cambios** — Los archivos pequeños (`_handler.py`, `settings.py`, `formats.py`, etc.) no necesitan refactorización.

---

## Resultado Esperado

| Antes | Después |
|-------|---------|
| 9 archivos > 600 líneas | 0 archivos > 400 líneas |
| Archivo más grande: 1054 líneas | Archivo más grande: ~350 líneas |
| 33 archivos .py | ~48 archivos .py |
| Difícil encontrar lógica específica | Cada archivo tiene responsabilidad clara |
