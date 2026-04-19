
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PRESENTATION_EXTENSIONS = {".pptx", ".odp"}

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

_BTN_GREEN_STYLE = """
    QPushButton {
        background: rgba(34,197,94,0.2);
        border: 1px solid rgba(34,197,94,0.4);
        border-radius: 6px;
        padding: 4px 14px;
        color: #4ade80;
        font-weight: 600;
    }
    QPushButton:hover { background: rgba(34,197,94,0.35); }
"""

_NS_DRAWINGML = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS_PRES = "http://schemas.openxmlformats.org/presentationml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_ODP_DRAW = "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
_NS_ODP_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"


def _parse_pptx(path: str) -> list[dict]:
    slides: list[dict] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            slide_names = _pptx_slide_order(zf)
            for name in slide_names:
                with zf.open(name) as f:
                    tree = ET.parse(f)
                slide = _pptx_extract_slide(tree.getroot())
                slides.append(slide)
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError) as exc:
        raise RuntimeError(f"No se pudo leer el archivo PPTX:\n{exc}") from exc
    return slides


def _pptx_slide_order(zf: zipfile.ZipFile) -> list[str]:
    all_slides = sorted(
        n for n in zf.namelist()
        if n.startswith("ppt/slides/slide") and n.endswith(".xml")
    )
    if not all_slides:
        return []

    if "ppt/presentation.xml" not in zf.namelist():
        return all_slides

    try:
        with zf.open("ppt/presentation.xml") as f:
            tree = ET.parse(f)
        root = tree.getroot()

        rid_map: dict[str, str] = {}
        rels_path = "ppt/_rels/presentation.xml.rels"
        if rels_path in zf.namelist():
            with zf.open(rels_path) as rf:
                rels_tree = ET.parse(rf)
            ns_rels = "http://schemas.openxmlformats.org/package/2006/relationships"
            for rel in rels_tree.getroot().iter(f"{{{ns_rels}}}Relationship"):
                rid = rel.get("Id", "")
                target = rel.get("Target", "")
                if target.startswith("slides/slide"):
                    rid_map[rid] = f"ppt/{target}"

        ordered: list[str] = []
        for sld_id in root.iter(f"{{{_NS_PRES}}}sldId"):
            rid = sld_id.get(f"{{{_NS_REL}}}id", "")
            if rid in rid_map:
                ordered.append(rid_map[rid])

        if ordered:
            return ordered
    except (ET.ParseError, KeyError):
        pass

    return all_slides


def _pptx_extract_slide(root: ET.Element) -> dict:
    title = ""
    body_parts: list[str] = []

    for sp in root.iter(f"{{{_NS_PRES}}}sp"):
        nvSpPr = sp.find(f"{{{_NS_PRES}}}nvSpPr")
        is_title = False
        if nvSpPr is not None:
            nvPr = nvSpPr.find(f"{{{_NS_PRES}}}nvPr")
            if nvPr is not None:
                ph = nvPr.find(f"{{{_NS_DRAWINGML}}}ph")
                if ph is None:
                    ph = nvPr.find(
                        f"{{{_NS_PRES}}}ph"
                    )
                if ph is not None:
                    ph_type = ph.get("type", "")
                    if ph_type in ("title", "ctrTitle"):
                        is_title = True

        texts: list[str] = []
        for paragraph in sp.iter(f"{{{_NS_DRAWINGML}}}p"):
            parts = [t.text for t in paragraph.iter(f"{{{_NS_DRAWINGML}}}t") if t.text]
            line = "".join(parts).strip()
            if line:
                texts.append(line)

        combined = "\n".join(texts)
        if is_title and not title:
            title = combined
        elif combined:
            body_parts.append(combined)

    return {"title": title, "body": "\n".join(body_parts)}


def _parse_odp(path: str) -> list[dict]:
    slides: list[dict] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            if "content.xml" not in zf.namelist():
                raise RuntimeError("No se encontró content.xml en el archivo ODP.")
            with zf.open("content.xml") as f:
                tree = ET.parse(f)

        root = tree.getroot()
        for page in root.iter(f"{{{_NS_ODP_DRAW}}}page"):
            slide = _odp_extract_page(page)
            slides.append(slide)
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError) as exc:
        raise RuntimeError(f"No se pudo leer el archivo ODP:\n{exc}") from exc
    return slides


def _odp_extract_page(page: ET.Element) -> dict:
    title = page.get(f"{{{_NS_ODP_DRAW}}}name", "")
    body_parts: list[str] = []

    for frame in page.iter(f"{{{_NS_ODP_DRAW}}}frame"):
        texts: list[str] = []
        for text_p in frame.iter(f"{{{_NS_ODP_TEXT}}}p"):
            line_parts: list[str] = []
            if text_p.text:
                line_parts.append(text_p.text)
            for span in text_p.iter(f"{{{_NS_ODP_TEXT}}}span"):
                if span.text:
                    line_parts.append(span.text)
                if span.tail:
                    line_parts.append(span.tail)
            if text_p.tail:
                line_parts.append(text_p.tail)
            line = "".join(line_parts).strip()
            if line:
                texts.append(line)
        combined = "\n".join(texts)
        if combined:
            body_parts.append(combined)

    return {"title": title, "body": "\n".join(body_parts)}


class PresentationViewer(QWidget):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_path: str | None = None
        self._slides: list[dict] = []
        self._current_index: int = 0
        self._build_ui()


    def _build_ui(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(6)

        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.setFixedHeight(28)
        self.prev_btn.setStyleSheet(_BTN_STYLE)
        self.prev_btn.clicked.connect(self._prev_slide)
        toolbar.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Siguiente ▶")
        self.next_btn.setFixedHeight(28)
        self.next_btn.setStyleSheet(_BTN_STYLE)
        self.next_btn.clicked.connect(self._next_slide)
        toolbar.addWidget(self.next_btn)

        toolbar.addStretch(1)

        self.slide_label = QLabel("Diapositiva 0 / 0")
        self.slide_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.slide_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        toolbar.addWidget(self.slide_label)

        toolbar.addStretch(1)

        self.fullscreen_btn = QPushButton("🖵 Presentación")
        self.fullscreen_btn.setFixedHeight(28)
        self.fullscreen_btn.setStyleSheet(_BTN_GREEN_STYLE)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        toolbar.addWidget(self.fullscreen_btn)

        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setStyleSheet("""
            QTextEdit {
                background: #111827;
                color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.2);
                border-radius: 8px;
                padding: 16px;
                font-family: 'Calibri', 'Arial', sans-serif;
                font-size: 12pt;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #1e293b;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #475569;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(toolbar)
        layout.addWidget(self.text_view, 1)

        self._update_buttons()


    def load_file(self, path: str) -> None:
        self.current_path = path
        self._slides.clear()
        self._current_index = 0
        self.text_view.clear()

        ext = Path(path).suffix.lower()

        try:
            if ext == ".pptx":
                self._slides = _parse_pptx(path)
            elif ext == ".odp":
                self._slides = _parse_odp(path)
            else:
                self._show_error("Formato de archivo no reconocido.")
                return
        except zipfile.BadZipFile:
            self._show_error(
                "El archivo está dañado o no es un formato de presentación válido."
            )
            return
        except Exception as exc:
            self._show_error(f"Error al leer el archivo:\n{exc}")
            return

        if not self._slides:
            self._show_error("No se encontraron diapositivas en el archivo.")
            return

        self._current_index = 0
        self._show_slide(0)


    def _prev_slide(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._show_slide(self._current_index)

    def _next_slide(self) -> None:
        if self._current_index < len(self._slides) - 1:
            self._current_index += 1
            self._show_slide(self._current_index)

    def _show_slide(self, index: int) -> None:
        if not self._slides or index < 0 or index >= len(self._slides):
            return

        slide = self._slides[index]
        num = index + 1
        title = slide.get("title", "").strip()
        body = slide.get("body", "").strip()

        header = f"Diapositiva {num}"
        if title:
            header += f" — {title}"

        html = (
            f"<h2 style='color:#60a5fa; margin-bottom:8px;'>{_escape(header)}</h2>"
            f"<hr style='border:1px solid #334155; margin-bottom:12px;'>"
        )
        if body:
            for line in body.split("\n"):
                html += f"<p style='margin:4px 0;'>{_escape(line)}</p>"
        else:
            html += (
                "<p style='color:#64748b; font-style:italic;'>"
                "(Sin contenido de texto)</p>"
            )

        self.text_view.setHtml(html)
        self._update_buttons()

    def _update_buttons(self) -> None:
        total = len(self._slides)
        current = self._current_index + 1 if total else 0
        self.slide_label.setText(f"Diapositiva {current} / {total}")
        self.prev_btn.setEnabled(self._current_index > 0)
        self.next_btn.setEnabled(self._current_index < total - 1)


    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("🖵 Presentación")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("✕ Salir")


    def _show_error(self, msg: str) -> None:
        self.text_view.setHtml(
            f"<p style='color:#f87171; font-size:13pt;'>⚠️ {_escape(msg)}</p>"
        )
        self.slide_label.setText("Diapositiva 0 / 0")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        QMessageBox.warning(self, "Error", msg)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
