"""参数页检测器 — 统一入口。

使用方式：
    from locator.detector import detect
    result = detect("path/to/GB_4599-2024.pdf", category="lighting", mode="text")
"""

from dataclasses import dataclass, field
import os
import subprocess

from locator.patterns import match_page

def _normalize(text: str) -> str:
    """Normalize extracted text: collapse whitespace for keyword matching."""
    import re
    # Replace newlines with spaces to handle fragmented table headers
    return re.sub(r'[\n\r]+', ' ', text).strip()


@dataclass
class MatchSignal:
    keyword: str
    tier: str
    confidence: float


@dataclass
class PageResult:
    page: int
    signals: list[MatchSignal] = field(default_factory=list)
    page_text_preview: str = ""

    @property
    def is_parameter_page(self) -> bool:
        return len(self.signals) > 0 and any(s.tier == "P0" for s in self.signals)

    @property
    def confidence(self) -> str:
        if any(s.tier == "P0" for s in self.signals):
            return "high"
        p1 = sum(1 for s in self.signals if s.tier == "P1")
        p2 = sum(1 for s in self.signals if s.tier == "P2")
        if p1 >= 3:
            return "medium"
        if p1 >= 1 and p2 >= 2:
            return "medium"
        return "low"


@dataclass
class DetectorResult:
    filename: str
    total_pages: int
    mode: str
    pages: list[PageResult] = field(default_factory=list)
    error: str | None = None

    @property
    def parameter_pages(self) -> list[PageResult]:
        return [p for p in self.pages if p.is_parameter_page]


# ---------- text extraction ----------

def _extract_text(path: str) -> list[tuple[int, str]]:
    """Extract text from a text-layer PDF page by page.
    Returns list of (page_number_1based, page_text).
    """
    import fitz
    doc = fitz.open(path)
    pages: list[tuple[int, str]] = []
    for i in range(len(doc)):
        text = doc[i].get_text()
        pages.append((i + 1, text))
    doc.close()
    return pages


# ---------- OCR extraction ----------

def _ocr_page(path: str, page_num: int, dpi: int = 200) -> str:
    """OCR a single page from a PDF. Returns extracted text.
    Requires: tesseract binary + chi_sim traineddata in PATH/tessdata.
    """
    import fitz
    doc = fitz.open(path)
    page = doc[page_num - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    doc.close()

    tmp_png = f"/tmp/_locator_ocr_{os.getpid()}_{page_num}.png"
    pix.save(tmp_png)

    try:
        result = subprocess.run(
            ["tesseract", tmp_png, "stdout", "-l", "chi_sim", "--psm", "6"],
            capture_output=True, text=True, timeout=120,
        )
        text = result.stdout
    except FileNotFoundError:
        text = ""
    finally:
        try:
            os.remove(tmp_png)
        except OSError:
            pass
    return text


# ---------- main detect ----------

def detect(path: str, category: str, mode: str = "text",
           cache_dir: str | None = None) -> DetectorResult:
    """检测一份 PDF 中哪些页包含参数。

    Args:
        path: PDF 文件路径。
        category: 标准类别（如 "lighting", "automotive"），用于选择规则。
        mode: "text" | "ocr" | "auto"
            - text: 仅文字层提取
            - ocr:  仅 OCR 提取
            - auto: 先文字，文字不够再 OCR（混合策略）
        cache_dir: OCR 文本缓存目录。None 则不缓存。

    Returns:
        DetectorResult
    """
    filename = os.path.basename(path)
    result = DetectorResult(filename=filename, total_pages=0, mode=mode)

    if mode == "text":
        try:
            pages = _extract_text(path)
        except Exception as e:
            result.error = str(e)
            return result
    elif mode == "ocr":
        import fitz
        try:
            tmp_doc = fitz.open(path)
            total = len(tmp_doc)
            tmp_doc.close()
        except Exception as e:
            result.error = str(e)
            return result
        pages = [(i + 1, "") for i in range(total)]
        for i in range(total):
            pn = i + 1
            text = _ocr_page(path, pn)
            pages[i] = (pn, text)
    elif mode == "auto":
        # Try text first
        text_pages = _extract_text(path)
        total_chars = sum(len(t) for _, t in text_pages)
        if total_chars > 500:
            pages = text_pages
        else:
            # Fallback to OCR
            import fitz
            tmp_doc = fitz.open(path)
            total = len(tmp_doc)
            tmp_doc.close()
            pages = [(i + 1, "") for i in range(total)]
            for i in range(total):
                pn = i + 1
                text = _ocr_page(path, pn)
                pages[i] = (pn, text)
    else:
        result.error = f"Unknown mode: {mode}"
        return result

    result.total_pages = len(pages)

    for page_num, text in pages:
        normalized = _normalize(text)
        signals_raw, is_param, conf = match_page(normalized, category)
        signals = [
            MatchSignal(keyword=s["keyword"], tier=s["tier"], confidence=s["confidence"])
            for s in signals_raw
        ]
        page_result = PageResult(
            page=page_num,
            signals=signals,
            page_text_preview=normalized[:100],
        )
        result.pages.append(page_result)

    return result
