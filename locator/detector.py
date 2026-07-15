"""参数页检测器 — 统一入口。

使用方式：
    from locator.detector import detect
    result = detect("path/to/GB_4599-2024.pdf", mode="auto")

mode:
    "text" — 仅文字层提取
    "ocr"  — 仅 OCR 提取
    "auto" — 先文字，不够再 OCR（混合策略）

返回 DetectorResult，包含每页的匹配信号。
"""

from dataclasses import dataclass, field


@dataclass
class MatchSignal:
    """单页上的一个匹配信号。"""
    keyword: str
    tier: str          # "P0" | "P1" | "P2"
    confidence: float  # derivative from tier weight


@dataclass
class PageResult:
    """单页的检测结果。"""
    page: int
    signals: list[MatchSignal] = field(default_factory=list)
    page_text_preview: str = ""

    @property
    def is_parameter_page(self) -> bool:
        """根据 signals 判定是否为参数页。
        规则：P0*1 | P1*3 | (P1*1 + P2*2)
        """
        ...

    @property
    def confidence(self) -> str:
        """high | medium | low"""
        ...


@dataclass
class DetectorResult:
    """一份 PDF 的完整检测结果。"""
    filename: str
    total_pages: int
    mode: str          # "text" | "ocr" | "hybrid"
    pages: list[PageResult] = field(default_factory=list)
    error: str | None = None

    @property
    def parameter_pages(self) -> list[PageResult]:
        return [p for p in self.pages if p.is_parameter_page]


def detect(path: str, mode: str = "auto") -> DetectorResult:
    """检测一份 PDF 中哪些页包含参数。

   当前实现：先文字层提取 → 按 patterns 匹配
   未来改进：接入 model_hook.PageDetector
   """
    ...
