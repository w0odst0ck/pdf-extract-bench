"""汇总索引 — 对单份 PDF 的检测结果合并为 index.json。"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PageEntry:
    """索引中的单页条目。"""
    page: int
    signals: list[str]
    table_title: str = ""
    confidence: str = "medium"  # "high" | "medium" | "low"


@dataclass
class PdfIndex:
    """一份 PDF 的索引。"""
    filename: str
    category: str
    route: str           # "text" | "ocr" | "hybrid"
    total_pages: int
    status: str          # "success" | "error"
    parameter_pages: list[PageEntry] = field(default_factory=list)
    error: str | None = None

    @property
    def summary(self) -> dict:
        return {
            "param_pages": len(self.parameter_pages),
            "total_pages": self.total_pages,
            "savings_pct": round(
                (1 - len(self.parameter_pages) / self.total_pages) * 100, 1
            ) if self.total_pages else 0,
        }


@dataclass
class Index:
    """完整索引。"""
    metadata: dict
    results: list[dict] = field(default_factory=list)

    def add_pdf(self, pdf_index: PdfIndex) -> None:
        self.results.append(asdict(pdf_index))

    def to_json(self, path: str) -> None:
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
