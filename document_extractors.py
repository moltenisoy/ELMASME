import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional


def _extract_docx_text(path: str) -> Optional[str]:
    try:
        ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        with zipfile.ZipFile(path, "r") as z:
            if "word/document.xml" not in z.namelist():
                return None
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                paragraphs = []
                for p in root.iter(f"{{{ns}}}p"):
                    texts = []
                    for t in p.iter(f"{{{ns}}}t"):
                        if t.text:
                            texts.append(t.text)
                    paragraphs.append("".join(texts))
                return "\n".join(paragraphs)
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None


def _extract_epub_text(path: str) -> Optional[str]:
    try:
        with zipfile.ZipFile(path, "r") as z:
            container_path = "META-INF/container.xml"
            if container_path not in z.namelist():
                return None
            with z.open(container_path) as cf:
                container = ET.parse(cf)
                ns_container = "urn:oasis:names:tc:opendocument:xmlns:container"
                rootfile_el = container.find(f".//{{{ns_container}}}rootfile")
                if rootfile_el is None:
                    rootfile_el = container.find(".//{http://www.idpf.org/2007/opf}rootfile")
                if rootfile_el is None:
                    for el in container.iter():
                        if el.tag.endswith("rootfile") and el.get("full-path"):
                            rootfile_el = el
                            break
                if rootfile_el is None:
                    return None
                opf_path = rootfile_el.get("full-path")
            if not opf_path or opf_path not in z.namelist():
                return None
            opf_dir = os.path.dirname(opf_path)
            with z.open(opf_path) as opf_file:
                opf_tree = ET.parse(opf_file)
                opf_root = opf_tree.getroot()
            manifest = {}
            for item in opf_root.iter():
                if item.tag.endswith("}item") or item.tag == "item":
                    item_id = item.get("id", "")
                    href = item.get("href", "")
                    media_type = item.get("media-type", "")
                    manifest[item_id] = (href, media_type)
            spine_items = []
            for itemref in opf_root.iter():
                if itemref.tag.endswith("}itemref") or itemref.tag == "itemref":
                    idref = itemref.get("idref", "")
                    if idref in manifest:
                        spine_items.append(manifest[idref])
            if not spine_items:
                for item_id, (href, media_type) in manifest.items():
                    if "html" in media_type or "xhtml" in media_type:
                        spine_items.append((href, media_type))
            all_text = []
            tag_re = re.compile(r"<[^>]+>")
            for href, media_type in spine_items:
                full_path = os.path.join(opf_dir, href).replace("\\", "/")
                if full_path.startswith("/"):
                    full_path = full_path[1:]
                if full_path not in z.namelist():
                    continue
                with z.open(full_path) as html_file:
                    raw = html_file.read()
                    try:
                        html_content = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        html_content = raw.decode("latin-1", errors="replace")
                    text = tag_re.sub("", html_content)
                    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
                    text = text.replace("&lt;", "<").replace("&gt;", ">")
                    text = text.replace("&quot;", '"').replace("&apos;", "'")
                    lines = [line.strip() for line in text.splitlines()]
                    cleaned = "\n".join(line for line in lines if line)
                    if cleaned:
                        all_text.append(cleaned)
            return "\n\n".join(all_text) if all_text else None
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None


def _extract_rtf_text(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            rtf_content = f.read()
        if not rtf_content.startswith("{\\rtf"):
            return None
        rtf_content = re.sub(r"\\[a-z]+\d*\s?", " ", rtf_content)
        rtf_content = re.sub(r"\{[^}]*\}", "", rtf_content)
        rtf_content = rtf_content.replace("{", "").replace("}", "")
        rtf_content = re.sub(r"\\[\'\\]([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), rtf_content)
        rtf_content = rtf_content.replace("\\\n", "\n").replace("\\par", "\n")
        lines = [line.strip() for line in rtf_content.splitlines()]
        return "\n".join(lines)
    except (OSError, UnicodeDecodeError):
        return None


def _extract_odt_text(path: str) -> Optional[str]:
    try:
        ns_text = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        with zipfile.ZipFile(path, "r") as z:
            if "content.xml" not in z.namelist():
                return None
            with z.open("content.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                paragraphs = []
                for elem in root.iter():
                    if elem.tag in (f"{{{ns_text}}}p", f"{{{ns_text}}}h"):
                        text_parts = []
                        if elem.text:
                            text_parts.append(elem.text)
                        for child in elem:
                            if child.text:
                                text_parts.append(child.text)
                            if child.tail:
                                text_parts.append(child.tail)
                        paragraphs.append("".join(text_parts))
                return "\n".join(paragraphs)
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None


def _extract_ods_text(path: str) -> Optional[str]:
    try:
        ns_table = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
        ns_text = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        with zipfile.ZipFile(path, "r") as z:
            if "content.xml" not in z.namelist():
                return None
            with z.open("content.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                rows = []
                for row in root.iter(f"{{{ns_table}}}table-row"):
                    cells = []
                    for cell in row.iter(f"{{{ns_table}}}table-cell"):
                        cell_texts = []
                        for p in cell.iter(f"{{{ns_text}}}p"):
                            parts = []
                            if p.text:
                                parts.append(p.text)
                            for child in p:
                                if child.text:
                                    parts.append(child.text)
                                if child.tail:
                                    parts.append(child.tail)
                            cell_texts.append("".join(parts))
                        cells.append(" ".join(cell_texts))
                    if any(c.strip() for c in cells):
                        rows.append("\t".join(cells))
                return "\n".join(rows) if rows else None
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None
