# Parameter Page Locator — 设计文档

> 项目定位：自动定位 PDF 中参数所在页面，人工精确提取数值。

---

## 一、核心逻辑

```
输入 PDF
  │
  ├── 文字层检测
  │   ├── 有文字 → 全文提取 → 关键词/正则匹配 → 标记参数页
  │   └── 文字稀疏 → 判定为"疑似扫描" → 走 OCR 路线
  │
  └── OCR 路线
      ├── 全页 OCR → 文本 → 同一套匹配规则 → 标记参数页
      └── （数值精度不足，但关键词+页码是准的）
```

定位器最终产出不是参数值，而是：

```
GB_4599-2024.pdf → {参数页: [13, 15, 17, 21, 31], 节约: 91%}
```

人工只需要看这 5 页而不是 59 页。

---

## 二、架构

```
locator/
├── __init__.py
├── detector.py               ← 统一入口 （text / ocr / hybrid 三种模式）
│                               text → 文字层提取 → 匹配
│                               ocr  → OCR → 匹配
│                               auto → 先 text，不够再 ocr
├── patterns/
│   ├── __init__.py            ← 规则注册+获取
│   ├── lighting.py            ← 照明类标准（ICS 29.140）
│   └── automotive.py          ← 汽车类标准（ICS 43.xxx）
├── model_hook.py              ← PageDetector 抽象基类（预留模型接口）
└── index.py                   ← 汇总产出 index.json
```

---

## 三、参数检测规则（patterns/）

规则按类别分文件，通过 `register()` 注册。新增类别只需加文件。

### 规则分级

```
P0 — 强信号（命中几乎必是参数表）:
  "配光性能" "光度参数" "测试点" "位置(°)"

P1 — 中信号（需组合验证）:
  "照度" "亮度" "色温" "色品坐标" "cd" "lm" "lx"

P2 — 弱信号（需 2+ 命中）:
  "最小值" "最大值" "公差" "限值" "参数"
```

### 判定规则

```
单页判定逻辑:
  P0 命中 ≥1 → ✅ 参数页
  P1 命中 ≥3 → ✅ 参数页
  P1 命中 ≥1 + P2 命中 ≥2 → ✅ 参数页
  其他 → ❌ 非参数页
```

### 新增类别

```python
# locator/patterns/your_category.py
from . import CategoryRules, RuleTier, register

RULES: CategoryRules = {
    "P0": RuleTier(keywords=[...], weight=1.0),
    "P1": RuleTier(keywords=[...], weight=0.5),
    "P2": RuleTier(keywords=[...], weight=0.2),
}
register("your_category", RULES)
```

`sources.csv` 的 `category` 列自动匹配。

---

## 四、输出格式（index.json）

```json
{
  "metadata": {
    "project": "pdf-extract-bench",
    "generated_at": "2026-07-15T15:30:00+08:00",
    "total_pdfs": 108
  },
  "results": [
    {
      "filename": "GB_4599-2024.pdf",
      "category": "core",
      "route": "text",
      "total_pages": 59,
      "status": "success",
      "parameter_pages": [
        {"page": 13, "signals": ["P0:配光性能", "P0:测试点"], "confidence": "high"},
        {"page": 15, "signals": ["P0:配光性能", "P0:测试点"], "confidence": "high"},
        {"page": 31, "signals": ["P1:光度参数", "P2:参数"], "confidence": "medium"}
      ],
      "summary": {"param_pages": 5, "total_pages": 59, "savings_pct": 91.5}
    }
  ]
}
```

confidence:

| 等级 | 条件 | 处理 |
|------|------|------|
| high | P0 命中 | 人工优先看 |
| medium | P1×3+ 或 P1+P2 | 人工需验证 |
| low | 仅 P2 | 可选看 |

---

## 五、模型接入接口（model_hook.py）

```python
class PageDetector(ABC):
    @abstractmethod
    def detect_page(self, text: str, page_num: int) -> list[ParamSignal]:
        """检测单页是否包含参数表。"""
        ...
```

**替换方式**：

```python
# 当前：detector.py 内建规则匹配
# 未来：只需 DetectorResult 内部换一行
detector = RuleDetector()    # →  MLDetector(model_path="...")
```

`ParamSignal` 的 `signal_type` 字段区分来源：`keyword` | `model_classifier` | `model_vision`。后续加模型不影响 `index.py` 的合并逻辑。

---

## 六、全量 108 PDF 处理策略

```
输入: 108 PDFs → 按 sources.csv route 分组 → 逐份处理 → 合并索引
```

批量命令：

```bash
python3 -m locator.index --input datasets/ --output output/index.json
```

缓存策略：
- 扫描件的 OCR 文本缓存到 `cache/{filename}/page_{n}.txt`
- 文字层 PDF 不缓存（提取速度足够快）

---

## 七、验证方案

用 GB 4599 做 ground truth：

| 指标 | 目标 |
|------|------|
| 查全率（找到的参数页 / 实际参数页） | ≥95% |
| 查准率（标记的页中真有参数 / 总标记数） | ≥80% |
| P0 精度 | 100% |
| 节约率 | 尽可能高 |

---

## 八、OCR 环境说明

Tesseract 无法通过 `pip` 直接安装，需系统包管理。

```bash
# 方案 A（推荐）：sudo apt install
sudo apt install tesseract-ocr tesseract-ocr-chi-sim

# 方案 B（纯 pip，无系统依赖）：EasyOCR
pip install easyocr
# 注：EasyOCR 依赖 PyTorch，下载约 500MB，首次运行需下载模型
# 中文识别精度高于 Tesseract，但初始化更慢
```

当前验证环境通过解压 deb 包手动配置，不可用于脚本。写代码时需确认最终方案。
