"""Turn an uploaded resume file into plain text (PB-18).

Supported: PDF (.pdf), Word (.docx) and plain text (.txt). Only the text is kept.
"""
import io
import re
import zipfile
from xml.etree import ElementTree

SUPPORTED = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}


class ResumeFileError(ValueError):
    """The file can't be used; the message is safe to show to the user."""


def file_kind(filename: str) -> str:
    name = (filename or "").lower()
    for ext, kind in SUPPORTED.items():
        if name.endswith(ext):
            return kind
    raise ResumeFileError("Upload a PDF, Word (.docx) or plain-text (.txt) file.")


def _from_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency listed in requirements.txt
        raise ResumeFileError("PDF support isn't installed on the server (pip install pypdf).") from exc
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ResumeFileError("This PDF is password-protected. Remove the password and upload it again.")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ResumeFileError:
        raise
    except Exception as exc:
        raise ResumeFileError("This PDF couldn't be read. Try exporting it again, or upload a .docx file.") from exc


def _from_docx(data: bytes) -> str:
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ResumeFileError("This Word file couldn't be read. Make sure it's a .docx (not .doc) file.") from exc
    root = ElementTree.fromstring(xml)
    paragraphs = []
    for paragraph in root.iter(f"{namespace}p"):
        parts = []
        for node in paragraph.iter():
            if node.tag == f"{namespace}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{namespace}tab":
                parts.append("\t")
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs)


def _from_txt(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ResumeFileError("This text file uses an unsupported encoding.")  # pragma: no cover


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_text(filename: str, data: bytes, max_bytes: int, max_chars: int) -> tuple[str, str]:
    """Return (kind, text) or raise ResumeFileError with a clear message."""
    kind = file_kind(filename)
    if not data:
        raise ResumeFileError("The file is empty.")
    if len(data) > max_bytes:
        raise ResumeFileError(f"The file is larger than {max_bytes // (1024 * 1024)} MB.")
    text = clean_text({"pdf": _from_pdf, "docx": _from_docx, "txt": _from_txt}[kind](data))
    if len(text) < 50:
        raise ResumeFileError(
            "We couldn't find enough text in this file. If it's a scanned image, paste your resume text instead."
        )
    return kind, text[:max_chars]
