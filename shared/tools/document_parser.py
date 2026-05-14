"""Parse text content from attachments (TXT/MD natively; PDF/DOCX via optional libs)."""
from __future__ import annotations

import os
from pathlib import Path

from langchain_core.tools import tool

_PLAIN_SUFFIXES = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}


def _read_plain(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    try:
        import pypdf  # type: ignore
        reader = pypdf.PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    except ImportError:
        return (
            f"[document_parser] Cannot read PDF '{path.name}': "
            "install 'pypdf' (pip install pypdf) to enable PDF parsing."
        )


def _read_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return (
            f"[document_parser] Cannot read DOCX '{path.name}': "
            "install 'python-docx' (pip install python-docx) to enable DOCX parsing."
        )


@tool
def document_parser(file_path: str) -> str:
    """Extract text from a file attachment.

    Supports:
    - Plain text (.txt, .md, .csv, .json, .yaml)
    - PDF (.pdf) — requires 'pypdf' package
    - Word (.docx) — requires 'python-docx' package

    Args:
        file_path: Absolute or relative path to the file.

    Returns extracted text, or an error message if the format is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        return f"[document_parser] File not found: {file_path}"

    suffix = path.suffix.lower()

    if suffix in _PLAIN_SUFFIXES:
        return _read_plain(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)

    # Attempt to read as UTF-8 text anyway
    try:
        return _read_plain(path)
    except Exception as exc:
        return (
            f"[document_parser] Unsupported file type '{suffix}' and could not read as text: {exc}"
        )
