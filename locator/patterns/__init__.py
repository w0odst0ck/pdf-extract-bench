"""参数检测规则库 — 按标准类别分文件。

使用方式：
    from locator.patterns import get_rules, match_page
    signals, is_param, confidence = match_page(text, category)
"""

import importlib
import pkgutil
from typing import TypedDict


class RuleTier(TypedDict):
    keywords: list[str]
    weight: float


class CategoryRules(TypedDict):
    P0: RuleTier
    P1: RuleTier
    P2: RuleTier


_RULES: dict[str, CategoryRules] = {}


def register(name: str, rules: CategoryRules) -> None:
    _RULES[name] = rules


def get_rules(category: str) -> CategoryRules | None:
    return _RULES.get(category)


def list_categories() -> list[str]:
    return list(_RULES.keys())


def auto_import() -> None:
    """自动加载 patterns/ 下所有规则文件，触发 register()。"""
    pkg = __import__("locator.patterns", fromlist=["_"])
    for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
        if modname != "__init__":
            importlib.import_module(f"locator.patterns.{modname}")


def match_page(text: str, category: str) -> tuple[list[dict], bool, str]:
    """对一页文本进行匹配。

    Returns:
        signals: [{"keyword": ..., "tier": ..., "confidence": ...}, ...]
        is_param_page: bool
        confidence: "high" | "medium" | "low"
    """
    rules = get_rules(category)
    if not rules:
        return [], False, "low"

    signals = []
    weighted_score = 0.0
    p0_hits = 0
    p1_hits = 0
    p2_hits = 0

    for tier_name in ("P0", "P1", "P2"):
        tier = rules[tier_name]
        weight = tier["weight"]
        for kw in tier["keywords"]:
            if kw.lower() in text.lower():
                signals.append({
                    "keyword": kw,
                    "tier": tier_name,
                    "confidence": weight,
                })
                weighted_score += weight
                if tier_name == "P0":
                    p0_hits += 1
                elif tier_name == "P1":
                    p1_hits += 1
                else:
                    p2_hits += 1

    # 判定规则
    if p0_hits >= 1:
        is_param = True
        conf = "high"
    elif p1_hits >= 3:
        is_param = True
        conf = "medium"
    elif p1_hits >= 1 and p2_hits >= 2:
        is_param = True
        conf = "medium"
    else:
        is_param = False
        conf = "low"

    return signals, is_param, conf


# Auto-import all rule modules at first import
auto_import()
