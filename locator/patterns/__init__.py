"""参数检测规则库 — 按标准类别分文件。

使用方式：
    from locator.patterns import get_rules
    rules = get_rules(category="lighting")
"""

from typing import TypedDict


class RuleTier(TypedDict):
    """单级规则。
    weight 用于组合判定时的置信度计算。
    """
    keywords: list[str]
    weight: float  # P0=1.0, P1=0.5, P2=0.2


class CategoryRules(TypedDict):
    """一个类别的全套规则。"""
    P0: RuleTier
    P1: RuleTier
    P2: RuleTier


_RULES: dict[str, CategoryRules] = {}


def register(name: str, rules: CategoryRules) -> None:
    _RULES[name] = rules


def get_rules(category: str) -> CategoryRules | None:
    """按类别获取规则。找不到时返回 None（调用方 fallback 到通用规则）。"""
    return _RULES.get(category)


def list_categories() -> list[str]:
    return list(_RULES.keys())
