"""PDF text extractors — unified interface for benchmark."""

from typing import Callable


def extract_pymupdf(path: str) -> str:
    """Extract text using PyMuPDF (fitz). Fast C-based engine. Supports CJK."""
    import fitz
    doc = fitz.open(path)
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "".join(parts)


def extract_pdfplumber(path: str) -> str:
    """Extract text using pdfplumber. Layout-aware, good for tables."""
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        parts: list[str] = []
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                parts.append(txt)
    return "".join(parts)


def extract_pdfminer(path: str) -> str:
    """Extract text using pdfminer.six. Pure Python, stable."""
    from pdfminer.high_level import extract_text
    return extract_text(path)


def extract_pypdfium2(path: str) -> str:
    """Extract text using pypdfium2 (PDFium C engine). Chromium's PDF renderer."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(path)
    parts: list[str] = []
    for i in range(len(doc)):
        page = doc[i]
        textpage = page.get_textpage()
        parts.append(textpage.get_text_range())
        textpage.close()
        page.close()
    doc.close()
    return "".join(parts)


# Registry: name -> (extractor_fn, is_available_check)
EXTRACTORS: dict[str, tuple[str, Callable[[str], str]]] = {}


def _register():
    """Register available extractors at module load time."""
    registry: dict[str, tuple[str, Callable[[str], str]]] = {}

    candidates = [
        ("pymupdf", "fitz", extract_pymupdf),
        ("pdfplumber", "pdfplumber", extract_pdfplumber),
        ("pdfminer", "pdfminer.high_level", extract_pdfminer),
        ("pypdfium2", "pypdfium2", extract_pypdfium2),
    ]

    for name, modname, fn in candidates:
        try:
            __import__(modname)
            registry[name] = (modname, fn)
        except ImportError:
            pass

    return registry


EXTRACTORS = _register()
