"""照明类标准（ICS 29.140）参数检测规则。

场景：配光曲线、光度参数、色温、显色指数。
"""

from . import CategoryRules, RuleTier, register

LIGHTING: CategoryRules = {
    "P0": RuleTier(
        keywords=[
            "配光性能", "配光曲线", "光度参数",
            "测试点", "位置(°)", "位置（°）",
            "光分布", "配光要求",
        ],
        weight=1.0,
    ),
    "P1": RuleTier(
        keywords=[
            "照度", "亮度", "光通量", "色温",
            "色品坐标", "显色指数", "色度",
            "cd", "lm", "lx", "K", "nm",
        ],
        weight=0.5,
    ),
    "P2": RuleTier(
        keywords=[
            "最小值", "最大值", "公差", "限值",
            "要求", "参数", "表",
        ],
        weight=0.2,
    ),
}

register("lighting", LIGHTING)
