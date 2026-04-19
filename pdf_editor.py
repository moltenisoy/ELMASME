
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

import fitz

from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSizeF
from PySide6.QtGui import (
    QImage, QPixmap, QFont, QColor, QPainter, QPen, QBrush,
    QKeySequence, QAction, QTextDocument, QCursor,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsScene, QGraphicsView,
    QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsItem,
    QPushButton, QToolButton, QLabel, QFrame, QFileDialog,
    QColorDialog, QFontComboBox, QComboBox, QMessageBox,
    QInputDialog, QDialog, QDialogButtonBox, QLineEdit,
    QSpinBox, QScrollArea, QMenu, QApplication,
)


class _MovableTextItem(QGraphicsRectItem):

    def __init__(self, text: str, font: QFont, color: QColor,
                 rect: QRectF, page_index: int, parent=None):
        super().__init__(rect, parent)
        self.page_index = page_index
        self._text = text
        self._font = QFont(font)
        self._color = QColor(color)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setPen(QPen(QColor(100, 160, 250, 180), 1, Qt.DashLine))
        self.setBrush(QBrush(QColor(255, 255, 255, 40)))
        self.setCursor(QCursor(Qt.SizeAllCursor))

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self.update()

    @property
    def font(self) -> QFont:
        return self._font

    @font.setter
    def font(self, value: QFont):
        self._font = QFont(value)
        self.update()

    @property
    def color(self) -> QColor:
        return self._color

    @color.setter
    def color(self, value: QColor):
        self._color = QColor(value)
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setFont(self._font)
        painter.setPen(self._color)
        text_rect = self.rect().adjusted(4, 2, -4, -2)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.TextWordWrap, self._text)


class _MovableImageItem(QGraphicsPixmapItem):

    def __init__(self, pixmap: QPixmap, page_index: int, parent=None):
        super().__init__(pixmap, parent)
        self.page_index = page_index
        self._source_path: Optional[str] = None
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setCursor(QCursor(Qt.SizeAllCursor))


class _MovableLinkItem(QGraphicsRectItem):

    def __init__(self, url: str, rect: QRectF, page_index: int, parent=None):
        super().__init__(rect, parent)
        self.page_index = page_index
        self._url = url
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setPen(QPen(QColor(30, 120, 255, 200), 2, Qt.DashDotLine))
        self.setBrush(QBrush(QColor(30, 120, 255, 35)))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(url)

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, value: str):
        self._url = value
        self.setToolTip(value)


class _MovableHighlightItem(QGraphicsRectItem):

    def __init__(self, rect: QRectF, page_index: int, color: QColor = None, parent=None):
        super().__init__(rect, parent)
        self.page_index = page_index
        self._color = color or QColor(255, 255, 0, 80)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(self._color))
        self.setCursor(QCursor(Qt.SizeAllCursor))

    @property
    def highlight_color(self) -> QColor:
        return self._color

    @highlight_color.setter
    def highlight_color(self, value: QColor):
        self._color = value
        self.setBrush(QBrush(value))


class _InsertTextDialog(QDialog):

    def __init__(self, parent=None, initial_text: str = "",
                 initial_font: QFont = None, initial_color: QColor = None):
        super().__init__(parent)
        self.setWindowTitle("Insertar / Editar texto")
        self.setMinimumSize(420, 280)
        self._color = initial_color or QColor(0, 0, 0)
        self._build_ui(initial_text, initial_font)

    def _build_ui(self, initial_text, initial_font):
        layout = QVBoxLayout(self)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Fuente:"))
        self.font_combo = QFontComboBox()
        if initial_font:
            self.font_combo.setCurrentFont(initial_font)
        font_row.addWidget(self.font_combo)

        font_row.addWidget(QLabel("Tamaño:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 120)
        self.size_spin.setValue(initial_font.pointSize() if initial_font and initial_font.pointSize() > 0 else 12)
        font_row.addWidget(self.size_spin)

        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setCheckable(True)
        if initial_font:
            self.bold_btn.setChecked(initial_font.bold())
        bf = self.bold_btn.font()
        bf.setBold(True)
        self.bold_btn.setFont(bf)
        font_row.addWidget(self.bold_btn)

        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setCheckable(True)
        if initial_font:
            self.italic_btn.setChecked(initial_font.italic())
        ifnt = self.italic_btn.font()
        ifnt.setItalic(True)
        self.italic_btn.setFont(ifnt)
        font_row.addWidget(self.italic_btn)

        self.color_btn = QPushButton("Color")
        self.color_btn.clicked.connect(self._pick_color)
        self._update_color_btn()
        font_row.addWidget(self.color_btn)
        layout.addLayout(font_row)

        from PySide6.QtWidgets import QTextEdit
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        self.text_edit.setMinimumHeight(120)
        layout.addWidget(self.text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pick_color(self):
        c = QColorDialog.getColor(self._color, self, "Color de texto")
        if c.isValid():
            self._color = c
            self._update_color_btn()

    def _update_color_btn(self):
        self.color_btn.setStyleSheet(
            f"color: {self._color.name()}; font-weight: bold;"
        )

    def get_result(self):
        font = self.font_combo.currentFont()
        font.setPointSize(self.size_spin.value())
        font.setBold(self.bold_btn.isChecked())
        font.setItalic(self.italic_btn.isChecked())
        return self.text_edit.toPlainText(), font, self._color


class _InsertLinkDialog(QDialog):
    def __init__(self, parent=None, initial_url: str = "https://"):
        super().__init__(parent)
        self.setWindowTitle("Insertar / Editar hipervínculo")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("URL del hipervínculo:"))
        self.url_edit = QLineEdit(initial_url)
        layout.addWidget(self.url_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_url(self) -> str:
        return self.url_edit.text().strip()


class PdfEditorToolbar(QFrame):

    add_text_requested = Signal()
    add_image_requested = Signal()
    add_link_requested = Signal()
    add_highlight_requested = Signal()
    add_signature_requested = Signal()
    delete_selected_requested = Signal()
    edit_selected_requested = Signal()
    save_requested = Signal()
    save_as_requested = Signal()
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    page_prev_requested = Signal()
    page_next_requested = Signal()
    undo_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 8px;
                padding: 2px 4px;
            }
            QToolButton, QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
                color: #e5e7eb;
            }
            QToolButton:hover, QPushButton:hover {
                background: rgba(59, 130, 246, 0.2);
                border-color: rgba(96, 165, 250, 0.4);
            }
            QToolButton:pressed, QPushButton:pressed {
                background: rgba(59, 130, 246, 0.4);
            }
            QLabel { color: #94a3b8; font-size: 11px; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 2, 6, 4)
        main_layout.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.text_btn = QToolButton()
        self.text_btn.setText("📝 Texto")
        self.text_btn.setToolTip("Insertar cuadro de texto")
        self.text_btn.setFixedHeight(36)
        self.text_btn.clicked.connect(self.add_text_requested)
        row1.addWidget(self.text_btn)

        self.image_btn = QToolButton()
        self.image_btn.setText("🖼️ Imagen")
        self.image_btn.setToolTip("Insertar imagen")
        self.image_btn.setFixedHeight(36)
        self.image_btn.clicked.connect(self.add_image_requested)
        row1.addWidget(self.image_btn)

        self.link_btn = QToolButton()
        self.link_btn.setText("🔗 Hipervínculo")
        self.link_btn.setToolTip("Insertar hipervínculo")
        self.link_btn.setFixedHeight(36)
        self.link_btn.clicked.connect(self.add_link_requested)
        row1.addWidget(self.link_btn)

        self.highlight_btn = QToolButton()
        self.highlight_btn.setText("🖍️ Resaltar")
        self.highlight_btn.setToolTip("Resaltar área en el PDF")
        self.highlight_btn.setFixedHeight(36)
        self.highlight_btn.clicked.connect(self.add_highlight_requested)
        row1.addWidget(self.highlight_btn)

        self.signature_btn = QToolButton()
        self.signature_btn.setText("✍️ Firma")
        self.signature_btn.setToolTip("Insertar firma manuscrita o imagen de firma")
        self.signature_btn.setFixedHeight(36)
        self.signature_btn.clicked.connect(self.add_signature_requested)
        row1.addWidget(self.signature_btn)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: rgba(148,163,184,0.3);")
        sep1.setFixedWidth(2)
        row1.addWidget(sep1)

        self.edit_btn = QToolButton()
        self.edit_btn.setText("✏️ Editar")
        self.edit_btn.setToolTip("Editar elemento seleccionado")
        self.edit_btn.setFixedHeight(36)
        self.edit_btn.clicked.connect(self.edit_selected_requested)
        row1.addWidget(self.edit_btn)

        self.delete_btn = QToolButton()
        self.delete_btn.setText("🗑️ Eliminar")
        self.delete_btn.setToolTip("Eliminar elemento seleccionado")
        self.delete_btn.setFixedHeight(36)
        self.delete_btn.clicked.connect(self.delete_selected_requested)
        row1.addWidget(self.delete_btn)

        self.undo_btn = QToolButton()
        self.undo_btn.setText("↩️ Deshacer")
        self.undo_btn.setToolTip("Deshacer última acción")
        self.undo_btn.setFixedHeight(36)
        self.undo_btn.clicked.connect(self.undo_requested)
        row1.addWidget(self.undo_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color: rgba(148,163,184,0.3);")
        sep2.setFixedWidth(2)
        row1.addWidget(sep2)

        self.prev_page_btn = QToolButton()
        self.prev_page_btn.setText("◀")
        self.prev_page_btn.setToolTip("Página anterior")
        self.prev_page_btn.setFixedSize(32, 36)
        self.prev_page_btn.clicked.connect(self.page_prev_requested)
        row1.addWidget(self.prev_page_btn)

        self.page_label = QLabel("Página 1 / 1")
        self.page_label.setStyleSheet("color: #e5e7eb; font-size: 12px; padding: 0 4px;")
        row1.addWidget(self.page_label)

        self.next_page_btn = QToolButton()
        self.next_page_btn.setText("▶")
        self.next_page_btn.setToolTip("Página siguiente")
        self.next_page_btn.setFixedSize(32, 36)
        self.next_page_btn.clicked.connect(self.page_next_requested)
        row1.addWidget(self.next_page_btn)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setStyleSheet("color: rgba(148,163,184,0.3);")
        sep3.setFixedWidth(2)
        row1.addWidget(sep3)

        self.zoom_out_btn = QToolButton()
        self.zoom_out_btn.setText("Zoom −")
        self.zoom_out_btn.setFixedHeight(36)
        self.zoom_out_btn.clicked.connect(self.zoom_out_requested)
        row1.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #e5e7eb; font-size: 12px; padding: 0 4px;")
        row1.addWidget(self.zoom_label)

        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setText("Zoom +")
        self.zoom_in_btn.setFixedHeight(36)
        self.zoom_in_btn.clicked.connect(self.zoom_in_requested)
        row1.addWidget(self.zoom_in_btn)

        row1.addStretch()

        self.save_btn = QPushButton("💾 Guardar PDF")
        self.save_btn.setToolTip("Guardar cambios en el PDF")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34,197,94,0.2);
                border: 1px solid rgba(34,197,94,0.4);
                border-radius: 6px; padding: 4px 12px;
                color: #4ade80; font-weight: 500;
            }
            QPushButton:hover { background: rgba(34,197,94,0.3); }
        """)
        self.save_btn.clicked.connect(self.save_requested)
        row1.addWidget(self.save_btn)

        self.save_as_btn = QPushButton("💾 Guardar como…")
        self.save_as_btn.setToolTip("Guardar como otro archivo PDF")
        self.save_as_btn.setFixedHeight(36)
        self.save_as_btn.setStyleSheet("""
            QPushButton {
                background: rgba(234,179,8,0.2);
                border: 1px solid rgba(234,179,8,0.4);
                border-radius: 6px; padding: 4px 12px;
                color: #facc15; font-weight: 500;
            }
            QPushButton:hover { background: rgba(234,179,8,0.3); }
        """)
        self.save_as_btn.clicked.connect(self.save_as_requested)
        row1.addWidget(self.save_as_btn)

        main_layout.addLayout(row1)

    def update_page_label(self, current: int, total: int):
        self.page_label.setText(f"Página {current} / {total}")

    def update_zoom_label(self, percent: int):
        self.zoom_label.setText(f"{percent}%")


_RENDER_DPI = 150
_PAGE_GAP = 20
_DEFAULT_FONT_SIZE = 12


class PdfEditorWidget(QWidget):

    modified_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc: Optional[fitz.Document] = None
        self._path: Optional[str] = None
        self._page_items: List[QGraphicsPixmapItem] = []
        self._overlay_items: List[QGraphicsItem] = []
        self._undo_stack: list = []
        self._current_page = 0
        self._zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        self._zoom_index = 2
        self._modified = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.toolbar = PdfEditorToolbar(self)
        layout.addWidget(self.toolbar)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setStyleSheet("""
            QGraphicsView {
                background: #374151;
                border: 1px solid rgba(148,163,184,0.2);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.view, 1)

        self.toolbar.add_text_requested.connect(self._add_text)
        self.toolbar.add_image_requested.connect(self._add_image)
        self.toolbar.add_link_requested.connect(self._add_link)
        self.toolbar.add_highlight_requested.connect(self._add_highlight)
        self.toolbar.add_signature_requested.connect(self._add_signature)
        self.toolbar.edit_selected_requested.connect(self._edit_selected)
        self.toolbar.delete_selected_requested.connect(self._delete_selected)
        self.toolbar.undo_requested.connect(self._undo)
        self.toolbar.save_requested.connect(self.save)
        self.toolbar.save_as_requested.connect(self.save_as)
        self.toolbar.zoom_in_requested.connect(self._zoom_in)
        self.toolbar.zoom_out_requested.connect(self._zoom_out)
        self.toolbar.page_prev_requested.connect(self._page_prev)
        self.toolbar.page_next_requested.connect(self._page_next)

        del_action = QAction(self)
        del_action.setShortcut(QKeySequence.Delete)
        del_action.triggered.connect(self._delete_selected)
        self.addAction(del_action)


    def load_file(self, path: str) -> bool:
        try:
            doc = fitz.open(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el PDF:\n{exc}")
            return False

        self._close_doc()
        self._doc = doc
        self._path = path
        self._current_page = 0
        self._modified = False
        self._undo_stack.clear()
        self._render_all_pages()
        self._update_toolbar_state()
        return True

    def save(self):
        if not self._doc or not self._path:
            return
        self._apply_overlays_to_doc()
        try:
            self._doc.save(self._path, incremental=True, encryption=0)
            self._set_modified(False)
            self._clear_overlays()
            self._render_all_pages()
            QMessageBox.information(self, "Guardado", "PDF guardado correctamente.")
        except Exception:
            QMessageBox.warning(
                self, "Aviso",
                "No se pudo guardar de forma incremental.\n"
                "Se abrirá el diálogo «Guardar como» para guardar una copia."
            )
            self.save_as()

    def save_as(self):
        if not self._doc:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF como…", "", "PDF (*.pdf)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"
        self._apply_overlays_to_doc()
        try:
            self._doc.save(file_path)
            self._path = file_path
            self._set_modified(False)
            self._clear_overlays()
            self._render_all_pages()
            QMessageBox.information(self, "Guardado", f"PDF guardado en:\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{exc}")

    def is_modified(self) -> bool:
        return self._modified

    def close_editor(self):
        self._close_doc()


    def _render_all_pages(self):
        self.scene.clear()
        self._page_items.clear()
        self._overlay_items.clear()
        if not self._doc:
            return

        zoom = self._zoom_levels[self._zoom_index]
        mat = fitz.Matrix(zoom * _RENDER_DPI / 72, zoom * _RENDER_DPI / 72)
        y_offset = 0.0

        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = QImage(pix.samples, pix.width, pix.height,
                         pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            item = QGraphicsPixmapItem(pixmap)
            item.setPos(0, y_offset)
            PAGE_INDEX_ROLE = 0
            item.setData(PAGE_INDEX_ROLE, page_num)
            item.setZValue(-1)
            self.scene.addItem(item)
            self._page_items.append(item)

            y_offset += pixmap.height() + _PAGE_GAP

        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))
        self._scroll_to_page(self._current_page)

    def _scroll_to_page(self, page_index: int):
        if 0 <= page_index < len(self._page_items):
            item = self._page_items[page_index]
            self.view.centerOn(item)

    def _page_rect(self, page_index: int) -> QRectF:
        if 0 <= page_index < len(self._page_items):
            item = self._page_items[page_index]
            return QRectF(item.pos(), QSizeF(item.pixmap().size()))
        return QRectF()


    def _apply_overlays_to_doc(self):
        if not self._doc:
            return

        zoom = self._zoom_levels[self._zoom_index]
        scale = 72.0 / (_RENDER_DPI * zoom)

        for item in list(self._overlay_items):
            page_index = getattr(item, "page_index", None)
            if page_index is None or page_index >= len(self._doc):
                continue
            page = self._doc[page_index]
            page_origin = self._page_items[page_index].pos()

            if isinstance(item, _MovableTextItem):
                scene_rect = item.mapToScene(item.rect()).boundingRect()
                x = (scene_rect.x() - page_origin.x()) * scale
                y = (scene_rect.y() - page_origin.y()) * scale
                w = scene_rect.width() * scale
                h = scene_rect.height() * scale
                pdf_rect = fitz.Rect(x, y, x + w, y + h)
                fontsize = item.font.pointSize() * zoom
                if fontsize <= 0:
                    fontsize = _DEFAULT_FONT_SIZE
                color_tuple = (
                    item.color.redF(),
                    item.color.greenF(),
                    item.color.blueF(),
                )
                try:
                    fontname = "helv"
                    page.insert_textbox(
                        pdf_rect,
                        item.text,
                        fontsize=fontsize,
                        fontname=fontname,
                        color=color_tuple,
                        align=fitz.TEXT_ALIGN_LEFT,
                    )
                except Exception:
                    try:
                        page.insert_text(
                            fitz.Point(x, y + fontsize),
                            item.text,
                            fontsize=fontsize,
                            fontname="helv",
                            color=color_tuple,
                        )
                    except Exception:
                        pass

            elif isinstance(item, _MovableImageItem):
                scene_pos = item.mapToScene(QPointF(0, 0))
                pix_w = item.pixmap().width()
                pix_h = item.pixmap().height()
                x = (scene_pos.x() - page_origin.x()) * scale
                y = (scene_pos.y() - page_origin.y()) * scale
                w = pix_w * scale
                h = pix_h * scale
                pdf_rect = fitz.Rect(x, y, x + w, y + h)
                src = getattr(item, "_source_path", None)
                if src and os.path.isfile(src):
                    try:
                        page.insert_image(pdf_rect, filename=src)
                    except Exception:
                        pass
                else:
                    try:
                        from PySide6.QtCore import QBuffer, QIODevice
                        buf = QBuffer()
                        buf.open(QIODevice.WriteOnly)
                        item.pixmap().save(buf, "PNG")
                        png_data = bytes(buf.data())
                        buf.close()
                        page.insert_image(pdf_rect, stream=png_data)
                    except Exception:
                        pass

            elif isinstance(item, _MovableLinkItem):
                scene_rect = item.mapToScene(item.rect()).boundingRect()
                x = (scene_rect.x() - page_origin.x()) * scale
                y = (scene_rect.y() - page_origin.y()) * scale
                w = scene_rect.width() * scale
                h = scene_rect.height() * scale
                pdf_rect = fitz.Rect(x, y, x + w, y + h)
                try:
                    link = {
                        "kind": fitz.LINK_URI,
                        "from": pdf_rect,
                        "uri": item.url,
                    }
                    page.insert_link(link)
                except Exception:
                    pass

            elif isinstance(item, _MovableHighlightItem):
                scene_rect = item.mapToScene(item.rect()).boundingRect()
                x = (scene_rect.x() - page_origin.x()) * scale
                y = (scene_rect.y() - page_origin.y()) * scale
                w = scene_rect.width() * scale
                h = scene_rect.height() * scale
                pdf_rect = fitz.Rect(x, y, x + w, y + h)
                try:
                    annot = page.add_highlight_annot(pdf_rect)
                    if annot:
                        c = item.highlight_color
                        annot.set_colors(stroke=(c.redF(), c.greenF(), c.blueF()))
                        annot.set_opacity(c.alphaF())
                        annot.update()
                except Exception:
                    try:
                        c = item.highlight_color
                        shape = page.new_shape()
                        shape.draw_rect(pdf_rect)
                        shape.finish(
                            color=None,
                            fill=(c.redF(), c.greenF(), c.blueF()),
                            fill_opacity=c.alphaF(),
                        )
                        shape.commit()
                    except Exception:
                        pass

    def _clear_overlays(self):
        for item in self._overlay_items:
            if item.scene():
                self.scene.removeItem(item)
        self._overlay_items.clear()


    def _add_text(self):
        if not self._doc:
            return
        dlg = _InsertTextDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        text, font, color = dlg.get_result()
        if not text.strip():
            return

        page_rect = self._page_rect(self._current_page)
        if page_rect.isNull():
            return

        center = self.view.mapToScene(self.view.viewport().rect().center())
        cx = max(page_rect.x() + 20, min(center.x(), page_rect.right() - 200))
        cy = max(page_rect.y() + 20, min(center.y(), page_rect.bottom() - 80))

        rect = QRectF(0, 0, 250, 80)
        item = _MovableTextItem(text, font, color, rect, self._current_page)
        item.setPos(cx, cy)
        self.scene.addItem(item)
        self._overlay_items.append(item)
        self._push_undo("add", item)
        self._set_modified(True)

    def _add_image(self):
        if not self._doc:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.svg);;Todos (*.*)"
        )
        if not file_path:
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen.")
            return

        page_rect = self._page_rect(self._current_page)
        max_w = page_rect.width() * 0.6 if not page_rect.isNull() else 400
        max_h = page_rect.height() * 0.4 if not page_rect.isNull() else 300
        if pixmap.width() > max_w or pixmap.height() > max_h:
            pixmap = pixmap.scaled(
                int(max_w), int(max_h),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        item = _MovableImageItem(pixmap, self._current_page)
        item._source_path = file_path

        center = self.view.mapToScene(self.view.viewport().rect().center())
        if not page_rect.isNull():
            cx = max(page_rect.x() + 10, min(center.x() - pixmap.width() / 2, page_rect.right() - pixmap.width()))
            cy = max(page_rect.y() + 10, min(center.y() - pixmap.height() / 2, page_rect.bottom() - pixmap.height()))
        else:
            cx, cy = center.x(), center.y()
        item.setPos(cx, cy)

        self.scene.addItem(item)
        self._overlay_items.append(item)
        self._push_undo("add", item)
        self._set_modified(True)

    def _add_link(self):
        if not self._doc:
            return
        dlg = _InsertLinkDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        url = dlg.get_url()
        if not url:
            return

        page_rect = self._page_rect(self._current_page)
        center = self.view.mapToScene(self.view.viewport().rect().center())
        cx = max(page_rect.x() + 20, min(center.x(), page_rect.right() - 200)) if not page_rect.isNull() else center.x()
        cy = max(page_rect.y() + 20, min(center.y(), page_rect.bottom() - 40)) if not page_rect.isNull() else center.y()

        rect = QRectF(0, 0, 200, 30)
        item = _MovableLinkItem(url, rect, self._current_page)
        item.setPos(cx, cy)
        self.scene.addItem(item)
        self._overlay_items.append(item)
        self._push_undo("add", item)
        self._set_modified(True)

    def _add_highlight(self):
        if not self._doc:
            return
        color = QColorDialog.getColor(
            QColor(255, 255, 0, 80), self, "Color de resaltado"
        )
        if not color.isValid():
            return
        color.setAlpha(80)

        page_rect = self._page_rect(self._current_page)
        center = self.view.mapToScene(self.view.viewport().rect().center())
        cx = max(page_rect.x() + 20, min(center.x(), page_rect.right() - 250)) if not page_rect.isNull() else center.x()
        cy = max(page_rect.y() + 20, min(center.y(), page_rect.bottom() - 40)) if not page_rect.isNull() else center.y()

        rect = QRectF(0, 0, 200, 25)
        item = _MovableHighlightItem(rect, self._current_page, color)
        item.setPos(cx, cy)
        self.scene.addItem(item)
        self._overlay_items.append(item)
        self._push_undo("add", item)
        self._set_modified(True)


    def _edit_selected(self):
        items = self.scene.selectedItems()
        if not items:
            QMessageBox.information(self, "Editar", "Seleccione un elemento para editar.")
            return
        item = items[0]

        if isinstance(item, _MovableTextItem):
            dlg = _InsertTextDialog(
                self,
                initial_text=item.text,
                initial_font=item.font,
                initial_color=item.color,
            )
            if dlg.exec() == QDialog.Accepted:
                text, font, color = dlg.get_result()
                item.text = text
                item.font = font
                item.color = color
                self._set_modified(True)

        elif isinstance(item, _MovableLinkItem):
            dlg = _InsertLinkDialog(self, initial_url=item.url)
            if dlg.exec() == QDialog.Accepted:
                item.url = dlg.get_url()
                self._set_modified(True)

        elif isinstance(item, _MovableImageItem):
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Reemplazar imagen", "",
                "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.svg);;Todos (*.*)"
            )
            if file_path:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    page_rect = self._page_rect(item.page_index)
                    max_w = page_rect.width() * 0.6 if not page_rect.isNull() else 400
                    max_h = page_rect.height() * 0.4 if not page_rect.isNull() else 300
                    if pixmap.width() > max_w or pixmap.height() > max_h:
                        pixmap = pixmap.scaled(
                            int(max_w), int(max_h),
                            Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                    item.setPixmap(pixmap)
                    item._source_path = file_path
                    self._set_modified(True)

    def _delete_selected(self):
        items = self.scene.selectedItems()
        for item in items:
            if item in self._overlay_items:
                self._push_undo("delete", item)
                self._overlay_items.remove(item)
                self.scene.removeItem(item)
                self._set_modified(True)


    def _push_undo(self, action_type: str, item):
        self._undo_stack.append((action_type, item))

    def _undo(self):
        if not self._undo_stack:
            return
        action_type, item = self._undo_stack.pop()
        if action_type == "add":
            if item in self._overlay_items:
                self._overlay_items.remove(item)
            if item.scene():
                self.scene.removeItem(item)
        elif action_type == "delete":
            self.scene.addItem(item)
            self._overlay_items.append(item)
        self._set_modified(bool(self._overlay_items))


    def _page_prev(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._scroll_to_page(self._current_page)
            self._update_toolbar_state()

    def _page_next(self):
        if self._doc and self._current_page < len(self._doc) - 1:
            self._current_page += 1
            self._scroll_to_page(self._current_page)
            self._update_toolbar_state()

    def _zoom_in(self):
        if self._zoom_index < len(self._zoom_levels) - 1:
            self._zoom_index += 1
            self._rerender()

    def _zoom_out(self):
        if self._zoom_index > 0:
            self._zoom_index -= 1
            self._rerender()

    def _rerender(self):
        if not self._doc:
            return
        old_page_origins = {}
        for idx, pi in enumerate(self._page_items):
            old_page_origins[idx] = pi.pos()

        overlay_state = []
        for item in self._overlay_items:
            overlay_state.append((item, item.pos()))
            if item.scene():
                self.scene.removeItem(item)

        self._render_all_pages()

        new_page_origins = {}
        for idx, pi in enumerate(self._page_items):
            new_page_origins[idx] = pi.pos()

        for item, old_pos in overlay_state:
            pi = getattr(item, "page_index", 0)
            old_origin = old_page_origins.get(pi, QPointF(0, 0))
            new_origin = new_page_origins.get(pi, QPointF(0, 0))
            delta = new_origin - old_origin
            item.setPos(old_pos + delta)
            self.scene.addItem(item)

        self._overlay_items = [it for it, _ in overlay_state]
        self._update_toolbar_state()

    def _update_toolbar_state(self):
        if self._doc:
            total = len(self._doc)
            self.toolbar.update_page_label(self._current_page + 1, total)
        zoom_pct = int(self._zoom_levels[self._zoom_index] * 100)
        self.toolbar.update_zoom_label(zoom_pct)


    def _set_modified(self, val: bool):
        if self._modified != val:
            self._modified = val
            self.modified_changed.emit(val)

    def _close_doc(self):
        self._clear_overlays()
        self.scene.clear()
        self._page_items.clear()
        self._undo_stack.clear()
        if self._doc:
            self._doc.close()
            self._doc = None
        self._path = None
        self._modified = False

    def _add_signature(self):
        if not self._doc:
            return

        dialog = SignatureDrawDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        sig_image = dialog.get_signature_image()
        if sig_image is None or sig_image.isNull():
            return

        pixmap = QPixmap.fromImage(sig_image)
        page_rect = self._page_rect(self._current_page)
        max_w = page_rect.width() * 0.4 if not page_rect.isNull() else 300
        max_h = page_rect.height() * 0.2 if not page_rect.isNull() else 100
        if pixmap.width() > max_w or pixmap.height() > max_h:
            pixmap = pixmap.scaled(
                int(max_w), int(max_h),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        center = self.view.mapToScene(self.view.viewport().rect().center())
        cx = center.x() - pixmap.width() / 2
        cy = center.y() - pixmap.height() / 2
        if not page_rect.isNull():
            cx = max(page_rect.x() + 10, min(cx, page_rect.right() - pixmap.width() - 10))
            cy = max(page_rect.y() + 10, min(cy, page_rect.bottom() - pixmap.height() - 10))

        item = _MovableImageItem(pixmap, self._current_page)
        item._source_path = None
        item._signature_image = sig_image
        item.setPos(cx, cy)
        self.scene.addItem(item)
        self._overlay_items.append(item)
        self._push_undo("add", item)
        self._set_modified(True)


class _SignatureCanvas(QLabel):
    """Canvas widget for drawing a freehand signature."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage(600, 200, QImage.Format_ARGB32)
        self._image.fill(QColor(255, 255, 255, 255))
        self._drawing = False
        self._last_point = None
        self._pen_color = QColor(0, 0, 0)
        self._pen_width = 3
        self.setPixmap(QPixmap.fromImage(self._image))
        self.setFixedSize(600, 200)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setStyleSheet("border: 2px solid #475569; border-radius: 4px;")

    def set_pen_color(self, color):
        self._pen_color = color

    def set_pen_width(self, width):
        self._pen_width = width

    def clear_canvas(self):
        self._image.fill(QColor(255, 255, 255, 255))
        self.setPixmap(QPixmap.fromImage(self._image))

    def get_signature_image(self):
        return self._image.copy()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drawing = True
            self._last_point = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self._drawing and self._last_point is not None:
            painter = QPainter(self._image)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(self._pen_color, self._pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            current = event.position().toPoint()
            painter.drawLine(self._last_point, current)
            painter.end()
            self._last_point = current
            self.setPixmap(QPixmap.fromImage(self._image))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drawing = False
            self._last_point = None


class SignatureDrawDialog(QDialog):
    """Dialog for drawing a signature or loading a signature image."""

    _DIALOG_STYLE = """
        QDialog { background: #1e293b; }
        QLabel  { color: #e5e7eb; }
        QPushButton {
            background: rgba(59,130,246,0.2);
            border: 1px solid rgba(59,130,246,0.4);
            border-radius: 6px;
            padding: 6px 16px;
            color: #60a5fa;
            font-weight: 500;
        }
        QPushButton:hover { background: rgba(59,130,246,0.35); }
        QSpinBox {
            background: #0f172a;
            color: #e5e7eb;
            border: 1px solid rgba(148,163,184,0.3);
            border-radius: 4px;
            padding: 2px 4px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Firma digital")
        self.setMinimumSize(660, 380)
        self._signature_image = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(self._DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Dibuje su firma en el recuadro:"))

        self._canvas = _SignatureCanvas()
        layout.addWidget(self._canvas, 0, Qt.AlignCenter)

        options = QHBoxLayout()

        options.addWidget(QLabel("Grosor:"))
        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 10)
        self._width_spin.setValue(3)
        self._width_spin.valueChanged.connect(self._canvas.set_pen_width)
        options.addWidget(self._width_spin)

        color_btn = QPushButton("Color de tinta")
        color_btn.clicked.connect(self._choose_color)
        options.addWidget(color_btn)

        clear_btn = QPushButton("🗑️ Limpiar")
        clear_btn.clicked.connect(self._canvas.clear_canvas)
        options.addWidget(clear_btn)

        options.addStretch()

        load_btn = QPushButton("📂 Cargar imagen de firma")
        load_btn.clicked.connect(self._load_image)
        options.addWidget(load_btn)

        layout.addLayout(options)

        buttons = QHBoxLayout()
        buttons.addStretch()

        accept_btn = QPushButton("✔ Insertar firma")
        accept_btn.clicked.connect(self._on_accept)
        buttons.addWidget(accept_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

    def _choose_color(self):
        color = QColorDialog.getColor(QColor(0, 0, 0), self, "Color de la firma")
        if color.isValid():
            self._canvas.set_pen_color(color)

    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Cargar imagen de firma", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Todos (*.*)"
        )
        if not path:
            return
        img = QImage(path)
        if img.isNull():
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen.")
            return
        self._signature_image = img
        self.accept()

    def _on_accept(self):
        self._signature_image = self._canvas.get_signature_image()
        self.accept()

    def get_signature_image(self):
        return self._signature_image
