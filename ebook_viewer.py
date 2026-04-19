"""Visor de archivos de libros electrónicos (EPUB, MOBI)."""

from __future__ import annotations

import html
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

EBOOK_EXTENSIONS = {".epub", ".mobi"}

_BTN_STYLE = """
    QPushButton {
        background: rgba(59,130,246,0.2);
        border: 1px solid rgba(59,130,246,0.4);
        border-radius: 6px;
        padding: 4px 14px;
        color: #60a5fa;
        font-weight: 500;
    }
    QPushButton:hover { background: rgba(59,130,246,0.35); }
    QPushButton:disabled { opacity: 0.4; color: #475569; }
"""

_COMBO_STYLE = """
    QComboBox {
        background: #1e293b;
        color: #e5e7eb;
        border: 1px solid rgba(148,163,184,0.3);
        border-radius: 6px;
        padding: 4px 8px;
        min-width: 160px;
    }
    QComboBox:hover { border: 1px solid rgba(59,130,246,0.5); }
    QComboBox QAbstractItemView {
        background: #1e293b;
        color: #e5e7eb;
        selection-background-color: rgba(59,130,246,0.3);
    }
"""

_TEXT_STYLE = """
    QTextEdit {
        background: #111827;
        color: #e5e7eb;
        border: 1px solid rgba(148,163,184,0.2);
        border-radius: 8px;
        padding: 16px;
        font-family: 'Georgia', 'Calibri', serif;
        font-size: 12pt;
        line-height: 1.6;
    }
"""

_LABEL_STYLE = "color: #94a3b8; font-size: 12px;"

_escape = html.escape

_MIN_FONT_SIZE = 8
_MAX_FONT_SIZE = 24
_DEFAULT_FONT_SIZE = 12

_RE_TAGS = re.compile(r"<[^>]+>")

# ── EPUB parsing helpers ──────────────────────────────────────────────

_NS_CONTAINER = "urn:oasis:names:tc:opendocument:xmlns:container"
_NS_OPF = "http://www.idpf.org/2007/opf"
_NS_DC = "http://purl.org/dc/elements/1.1/"


def _strip_html(text: str) -> str:
    """Remove HTML/XML tags and normalise whitespace."""
    text = _RE_TAGS.sub("", text)
    text = html.unescape(text)
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _parse_epub(path: str) -> list[tuple[str, str]]:
    """Parse an EPUB file and return a list of (title, content) tuples."""
    chapters: list[tuple[str, str]] = []

    with zipfile.ZipFile(path, "r") as zf:
        # 1. Find the root OPF file via container.xml
        try:
            container_xml = zf.read("META-INF/container.xml")
        except KeyError:
            raise ValueError("No se encontró META-INF/container.xml en el archivo EPUB.")

        container_tree = ET.fromstring(container_xml)
        rootfile_el = container_tree.find(
            f".//{{{_NS_CONTAINER}}}rootfile"
        )
        if rootfile_el is None:
            raise ValueError("No se encontró el archivo OPF raíz en container.xml.")
        opf_path = rootfile_el.get("full-path", "")
        if not opf_path:
            raise ValueError("El atributo full-path está vacío en container.xml.")

        opf_dir = str(PurePosixPath(opf_path).parent)

        # 2. Parse the OPF file
        opf_xml = zf.read(opf_path)
        opf_tree = ET.fromstring(opf_xml)

        # Build manifest id→href mapping
        manifest: dict[str, str] = {}
        for item in opf_tree.findall(f".//{{{_NS_OPF}}}item"):
            item_id = item.get("id", "")
            item_href = item.get("href", "")
            item_media = item.get("media-type", "")
            if item_id and item_href:
                manifest[item_id] = (item_href, item_media)

        # 3. Read spine order
        spine_ids: list[str] = []
        for itemref in opf_tree.findall(f".//{{{_NS_OPF}}}itemref"):
            idref = itemref.get("idref", "")
            if idref:
                spine_ids.append(idref)

        if not spine_ids:
            raise ValueError("No se encontraron elementos en el <spine> del OPF.")

        # 4. Extract text from each spine item
        for idx, idref in enumerate(spine_ids, 1):
            if idref not in manifest:
                continue
            href, media_type = manifest[idref]

            # Only process HTML/XHTML content
            if "html" not in media_type and "xml" not in media_type:
                continue

            # Resolve relative path within the ZIP
            if opf_dir and opf_dir != ".":
                full_path = f"{opf_dir}/{href}"
            else:
                full_path = href

            try:
                raw = zf.read(full_path).decode("utf-8", errors="replace")
            except KeyError:
                continue

            text = _strip_html(raw)
            if not text.strip():
                continue

            # Try to extract a title from the first line or <title> tag
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", raw, re.IGNORECASE)
            if title_match:
                title = html.unescape(title_match.group(1)).strip()
            else:
                first_line = text.strip().split("\n")[0][:80]
                title = first_line if first_line else f"Capítulo {idx}"

            chapters.append((title, text))

    return chapters


def _load_mobi(path: str) -> list[tuple[str, str]]:
    """Attempt basic text extraction from a MOBI file."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ValueError(f"No se pudo leer el archivo MOBI: {exc}") from exc

    # MOBI files start with a PalmDOC header. Try to extract readable text.
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = raw.decode("latin-1", errors="replace")

    # Strip any HTML-like tags that may be embedded
    text = _strip_html(text)

    # Filter to only printable lines
    lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        # Skip lines with excessive non-printable characters
        if cleaned and sum(c.isprintable() for c in cleaned) / max(len(cleaned), 1) > 0.7:
            lines.append(cleaned)

    content = "\n".join(lines)
    if not content.strip():
        raise ValueError(
            "No se pudo extraer texto legible del archivo MOBI.\n"
            "Para archivos MOBI, se recomienda convertirlos a EPUB."
        )

    return [("Contenido MOBI", content)]


# ── Viewer widget ─────────────────────────────────────────────────────


class EbookViewer(QWidget):
    """Visor de libros electrónicos con navegación por capítulos."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_path: str = ""
        self._chapters: list[tuple[str, str]] = []
        self._current_index: int = 0
        self._font_size: int = _DEFAULT_FONT_SIZE
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(6)

        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.setFixedHeight(28)
        self.prev_btn.setStyleSheet(_BTN_STYLE)
        self.prev_btn.clicked.connect(self._prev_chapter)
        toolbar.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Siguiente ▶")
        self.next_btn.setFixedHeight(28)
        self.next_btn.setStyleSheet(_BTN_STYLE)
        self.next_btn.clicked.connect(self._next_chapter)
        toolbar.addWidget(self.next_btn)

        toolbar.addSpacing(8)

        self.chapter_combo = QComboBox()
        self.chapter_combo.setFixedHeight(28)
        self.chapter_combo.setStyleSheet(_COMBO_STYLE)
        self.chapter_combo.currentIndexChanged.connect(self._on_combo_changed)
        toolbar.addWidget(self.chapter_combo)

        toolbar.addStretch(1)

        # Font size controls
        self.font_down_btn = QPushButton("A−")
        self.font_down_btn.setFixedHeight(28)
        self.font_down_btn.setFixedWidth(36)
        self.font_down_btn.setStyleSheet(_BTN_STYLE)
        self.font_down_btn.setToolTip("Reducir tamaño de fuente")
        self.font_down_btn.clicked.connect(self._font_decrease)
        toolbar.addWidget(self.font_down_btn)

        self.font_up_btn = QPushButton("A+")
        self.font_up_btn.setFixedHeight(28)
        self.font_up_btn.setFixedWidth(36)
        self.font_up_btn.setStyleSheet(_BTN_STYLE)
        self.font_up_btn.setToolTip("Aumentar tamaño de fuente")
        self.font_up_btn.clicked.connect(self._font_increase)
        toolbar.addWidget(self.font_up_btn)

        toolbar.addSpacing(8)

        self.chapter_label = QLabel("Capítulo 0 / 0")
        self.chapter_label.setStyleSheet(_LABEL_STYLE)
        self.chapter_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        toolbar.addWidget(self.chapter_label)

        layout.addLayout(toolbar)

        # Text view
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setStyleSheet(_TEXT_STYLE)
        layout.addWidget(self.text_view)

        self._update_buttons()

    # ── Public API ────────────────────────────────────────────────────

    def load_file(self, path: str) -> None:
        """Carga y muestra el contenido de un libro electrónico."""
        self.current_path = path
        self._chapters.clear()
        self._current_index = 0
        self._font_size = _DEFAULT_FONT_SIZE
        self.text_view.clear()
        self.chapter_combo.clear()

        ext = Path(path).suffix.lower()

        try:
            if ext == ".epub":
                self._chapters = _parse_epub(path)
            elif ext == ".mobi":
                self._chapters = _load_mobi(path)
            else:
                self._show_error("Formato de archivo no reconocido.")
                return
        except zipfile.BadZipFile:
            self._show_error(
                "El archivo está dañado o no es un archivo EPUB válido."
            )
            return
        except ValueError as exc:
            self._show_error(str(exc))
            return
        except Exception as exc:
            self._show_error(f"Error al leer el archivo:\n{exc}")
            return

        if not self._chapters:
            self._show_error("No se encontró contenido legible en el archivo.")
            return

        # Populate the chapter combo box
        self.chapter_combo.blockSignals(True)
        for title, _ in self._chapters:
            self.chapter_combo.addItem(title)
        self.chapter_combo.blockSignals(False)

        self._show_chapter(0)

    # ── Navigation ────────────────────────────────────────────────────

    def _prev_chapter(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._show_chapter(self._current_index)

    def _next_chapter(self) -> None:
        if self._current_index < len(self._chapters) - 1:
            self._current_index += 1
            self._show_chapter(self._current_index)

    def _on_combo_changed(self, index: int) -> None:
        if 0 <= index < len(self._chapters):
            self._current_index = index
            self._show_chapter(index)

    def _show_chapter(self, index: int) -> None:
        if not self._chapters or index < 0 or index >= len(self._chapters):
            return

        self._current_index = index
        title, content = self._chapters[index]

        header = (
            f"<h2 style='color:#60a5fa; margin-bottom:12px;'>"
            f"{_escape(title)}</h2>"
        )
        body = _escape(content).replace("\n", "<br>")
        self.text_view.setHtml(
            f"<div style='font-size:{self._font_size}pt; "
            f"line-height:1.6; color:#e5e7eb;'>"
            f"{header}{body}</div>"
        )
        self.text_view.verticalScrollBar().setValue(0)

        self.chapter_combo.blockSignals(True)
        self.chapter_combo.setCurrentIndex(index)
        self.chapter_combo.blockSignals(False)

        self._update_buttons()

    def _update_buttons(self) -> None:
        total = len(self._chapters)
        current = self._current_index + 1 if total else 0
        self.chapter_label.setText(f"Capítulo {current} / {total}")
        self.prev_btn.setEnabled(self._current_index > 0)
        self.next_btn.setEnabled(self._current_index < total - 1)
        self.font_down_btn.setEnabled(self._font_size > _MIN_FONT_SIZE)
        self.font_up_btn.setEnabled(self._font_size < _MAX_FONT_SIZE)

    # ── Font size ─────────────────────────────────────────────────────

    def _font_decrease(self) -> None:
        if self._font_size > _MIN_FONT_SIZE:
            self._font_size -= 1
            self._refresh_display()

    def _font_increase(self) -> None:
        if self._font_size < _MAX_FONT_SIZE:
            self._font_size += 1
            self._refresh_display()

    def _refresh_display(self) -> None:
        self._update_buttons()
        if self._chapters:
            self._show_chapter(self._current_index)

    # ── Error handling ────────────────────────────────────────────────

    def _show_error(self, msg: str) -> None:
        self.text_view.setHtml(
            f"<p style='color:#f87171; font-size:13pt;'>⚠️ {_escape(msg)}</p>"
        )
        self.chapter_label.setText("Capítulo 0 / 0")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        QMessageBox.warning(self, "Error", msg)
