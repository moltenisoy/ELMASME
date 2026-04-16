"""
Módulo para manejo de documentos.
Re-exporta desde document_pdf, document_editor y document_viewer para compatibilidad.
"""
from document_pdf import PDF_EXTENSIONS, extract_pdf_text  # noqa: F401
from document_editor import (  # noqa: F401
    read_text_file,
    save_text_file,
    is_editable,
    TextEditorToolbar,
)
from document_viewer import (  # noqa: F401
    TEXT_DOCUMENT_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    EDITABLE_EXTENSIONS,
    TYPE_NAMES,
    get_document_info,
    DocumentViewer,
)
