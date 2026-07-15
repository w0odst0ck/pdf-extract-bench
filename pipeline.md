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
├── __init__.py                 ← 统一入口
├── patterns.py                 ← 参数关键词+正则库（唯一需要维护的文件）
├── text_detector.py            ← Route A: 文字层 PDF → 全文 → 匹配
├── ocr_detector.py             ← Route B: 扫件 PDF → OCR → 全文 → 匹配
├── hybrid_detector.py          ← 混合策略：先文字层，不够再 OCR
├── model_hook.py               ← 🆕 预留接口：未来替换/增强检测引擎
└── index.py                    ← 汇总产出 index.json
```

### 各模块职责

| 模块 | 职责 | 产出 |
|------|------|------|
| `patterns.py` | 定义参数关键词和正则规则 | 规则集合 |
| `text_detector.py` | 对文字层 PDF 逐页提取+匹配 | 匹配结果列表 |
| `ocr_detector.py` | 对扫描件 PDF 逐页 OCR+匹配 | 匹配结果列表 |
| `hybrid_detector.py` | 先文字后 OCR，兜底策略 | 匹配结果列表 |
| `model_hook.py` | 定义接口，预留模型接入 | 抽象基类 |
| `index.py` | 合并结果，产出最终索引 | `index.json` |

---

## 三、参数检测规则（patterns.py）

### 关键词匹配层

按优先级分组：

```
P0 — 强信号（命中几乎必是参数表）:
  "配光性能要求"  "配光性能"  "光度参数"  "色度参数"
  "测试点"       "位置(°)"   "位置（°）"

P1 — 中信号（需组合验证）:
  "照度" "亮度" "色温" "色品坐标" "显色指数" "光通量"
  "cd"   "lm"   "lx"  "W/sr"    "K"        "nm"

P2 — 弱信号（需 2+ 命中）:
  "最小值" "最大值" "公差"  "限值"  "要求" "参数"
  "表1" "表2" "表3"（如果前面有"配光"等词）
```

### 判定规则

```
单页判定逻辑:
  P0 命中 ≥1 → ✅ 参数页
  P1 命中 ≥3 → ✅ 参数页（多个参数共存）
  P1 命中 ≥1 + P2 命中 ≥2 → ✅ 参数页（组合证据）
  其他 → ❌ 非参数页
```

### 正则匹配层（辅助）

```
数值+单位模式:
  [数值]\s*[单位]    → 如 "0.3 lx"  "6500 K"  "≥0.5 cd"
  
表格特征模式:
  ┌──┬──┬──┐  或  +--+--+--+  或  | 列 | 列 |
  
参数范围模式:
  [最小值]\s*~\s*[最大值]  → 如 "0.3~0.5 lx"
```

---

## 四、输出格式（index.json）

```json
{
  "metadata": {
    "project": "pdf-extract-bench",
    "generated_at": "2026-07-15T15:30:00+08:00",
    "total_pdfs": 108,
    "detection_version": "v1"
  },
  "results": [
    {
      "filename": "GB_4599-2024.pdf",
      "category": "core",
      "route": "text",
      "total_pages": 59,
      "status": "success",
      "parameter_pages": [
        {
          "page": 13,
          "signals": ["P0:配光性能要求", "P0:测试点", "P1:cd"],
          "table_title": "近光配光性能要求",
          "confidence": "high"
        },
        {
          "page": 15,
          "signals": ["P0:配光性能", "P0:测试点", "P1:lx"],
          "table_title": "近光生产一致性要求",
          "confidence": "high"
        },
        {
          "page": 31,
          "signals": ["P1:光度参数", "P2:要求"],
          "table_title": "LED模块光度参数",
          "confidence": "medium"
        }
      ],
      "summary": {
        "param_pages": 5,
        "need_review": 5,
        "savings_pct": 91.5
      }
    }
  ]
}
```

confidence 字段说明：

| 等级 | 含义 | 处理 |
|------|------|------|
| high | P0 命中，几乎确定 | 人工优先看 |
| medium | P1×2+ 或 P1+P2，大概率是 | 人工需要验证 |
| low | 仅有 P2，可能是边缘行文 | 人工可选看 |

---

## 五、预留模型接入接口（model_hook.py）

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ParamSignal:
    page: int
    signal_type: str        # "keyword" | "regex" | "model"
    signal_value: str       # 具体的匹配内容
    confidence: float       # 0.0 ~ 1.0

class PageDetector(ABC):
    """参数页检测器基类。
    
    当前实现：RuleBasedDetector（关键词+正则）
    未来实现：MLDetector（分类模型） / LLMDetector（大模型）
    """
    
    @abstractmethod
    def detect_page(self, text: str, page_num: int) -> list[ParamSignal]:
        """检测单页是否包含参数表。"""
        pass
    
    @abstractmethod
    def batch_detect(self, pages: list[tuple[int, str]]) -> list[ParamSignal]:
        """批量检测。"""
        pass
```

替换时只需要：

```python
# 当前
from locator.text_detector import RuleBasedDetector
detector = RuleBasedDetector()

# 未来（无缝替换）
from locator.model_hook import MLDetector
detector = MLDetector(model_path="...")
```

---

## 六、全量 108 PDF 处理策略

```
输入: 108 PDFs
  │
  ├── 按 route（文字层/扫描件）分组
  │
  ├── Route A（51个文字层PDF）
  │   └── 按 patterns.py 匹配 → 产出单文件索引
  │
  ├── Route B（57个扫描件PDF）
  │   └── OCR 逐页 → 按同一套 patterns 匹配 → 产出单文件索引
  │
  └── 合并 → index.json
```

批量执行命令：

```bash
python3 -m locator.index --input datasets/ --output output/index.json
```

### 缓存策略

为避免重复 OCR，扫描件的 OCR 文本缓存到 `cache/ocr_texts/{filename}/page_{n}.txt`。

---

## 七、验证方案

用 GB 4599 做 ground truth（已知哪些页有参数表）：

| 指标 | 计算方式 | 目标值 |
|------|---------|--------|
| 查全率 | 找到的参数页 / 实际参数页 | ≥95% |
| 查准率 | 标记的页中真正有参数的 / 标记总数 | ≥80% |
| P0 精度 | P0 标记的页中真正有参数的占比 | 目标 100% |
| 节约率 | 需人工看的页数 / 总页数 | — |

## 八、目录结构

```
pdf-extract-bench/
├── README.md
├── pipeline.md                    ← 本文档
├── .gitignore
├── datasets/
│   ├── sources.csv
│   ├── GB_4599-2024.pdf           ← 7 个测试 PDF
│   └── ...
├── locator/
│   ├── __init__.py
│   ├── patterns.py                ← 参数规则库
│   ├── text_detector.py           ← 文字层检测
│   ├── ocr_detector.py            ← OCR 检测
│   ├── hybrid_detector.py         ← 混合策略
│   ├── model_hook.py              ← 未来模型接口
│   └── index.py                   ← 汇总产出
├── cache/                         ← OCR 文本缓存 (.gitignored)
├── output/
│   └── index.json                 ← 最终产出
└── REPORT.md
```
