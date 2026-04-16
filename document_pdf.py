from PySide6.QtPdf import QPdfDocument

PDF_EXTENSIONS = {".pdf"}

def extract_pdf_text(pdf_document: QPdfDocument) -> str:
    text_parts = []
    page_count = pdf_document.pageCount()

    for page_num in range(page_count):
        text_parts.append(f"[Página {page_num + 1}]")

    return "\n\n".join(text_parts) if text_parts else "[Contenido del PDF - edición limitada]"
