"""汽车类标准（ICS 43.xxx）参数检测规则。

场景：信号灯光度、汽车前照灯、制动灯、转向灯。
"""

from . import CategoryRules, RuleTier, register

AUTOMOTIVE: CategoryRules = {
    "P0": RuleTier(
        keywords=[
            "配光性能", "光度参数", "信号灯",
            "测试点", "位置(°)", "位置（°）",
            "发光强度", "光分布",
        ],
        weight=1.0,
    ),
    "P1": RuleTier(
        keywords=[
            "照度", "亮度", "色度", "色温",
            "cd", "lm", "lx", "K",
            "制动灯", "转向灯", "前照灯", "雾灯",
        ],
        weight=0.5,
    ),
    "P2": RuleTier(
        keywords=[
            "最小值", "最大值", "公差",
            "要求", "参数", "表",
            "安装位置", "可见角度",
        ],
        weight=0.2,
    ),
}

register("automotive", AUTOMOTIVE)
