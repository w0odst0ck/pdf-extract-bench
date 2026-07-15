# Parameter Page Locator

在 108 个国标 PDF 中自动定位参数所在页，人工精确提取数值。

---

## 目的

**定位优先于提取。**  
精确的参数提取需要人工确认，但定位参数在哪一页可以自动化——把人从"翻 59 页找参数"降到"看 5 页参数页"。

## 适用场景

所有需从标准 PDF 提取配光曲线、光度参数、色度坐标等表格数据的场景。

---

## 路线

```
                ┌─ 文字层 PDF ──→ 全文提取 → 关键词匹配 → 标记参数页
108 个 PDF ────┤
                └─ 扫描件 PDF ──→ OCR → 文本 → 同一套关键词 → 标记参数页
```

不追求 OCR 能精确提取数值，只要求关键词+页码定位准。

---

## 测试集

7 份 PDF 覆盖三类场景：

| 文件 | 类型 | 页数 | 路线 | 参数类型 |
|------|------|------|------|---------|
| `GB_4599-2024.pdf` | 前照灯配光 | 59 | text | 配光曲线、照度值 |
| `GB_13954-2009.pdf` | 警示灯光度 | 18 | text | 光度参数、色度 |
| `GB_19152-2025.pdf` | 摩托车照明 | 55 | text | 配光曲线 |
| `GB_4785-2019.pdf` | 信号灯安装 | 82 | text | 编码异常PDF |
| `GB_23826-2025.pdf` | 混合 | 35 | hybrid | 文字+扫描混合 |
| `GB_T_5700-2023.pdf` | 照明测量 | 52 | ocr | 测量数据表 |
| `GB_T_7922-2023.pdf` | 光色测量 | 17 | ocr | 色度坐标表 |

---

## 产出

```json
{
  "filename": "GB_4599-2024.pdf",
  "total_pages": 59,
  "param_pages": 5,
  "need_review": 5,
  "pages": [
    {"page": 13, "title": "近光配光性能要求", "confidence": "high"},
    {"page": 15, "title": "近光生产一致性要求", "confidence": "high"},
    {"page": 17, "title": "远光配光性能", "confidence": "high"},
    {"page": 21, "title": "前雾灯配光性能", "confidence": "high"},
    {"page": 31, "title": "LED模块光度参数", "confidence": "medium"}
  ]
}
```

---

## 未来模型接入

`locator/model_hook.py` 定义了 `PageDetector` 抽象基类。  
当前实现为规则匹配（关键词+正则），未来可无缝替换为：

- 分类模型（判断"这一页是否有参数表"）
- 视觉模型（YOLO 检测表格区域）
- LLM（直接问"这一页在讲什么参数"）

详见 `pipeline.md`。

---

## 项目结构

```
pdf-extract-bench/
├── README.md
├── pipeline.md                       ← 完整设计文档
├── .gitignore
├── datasets/
│   ├── sources.csv
│   ├── GB_4599-2024.pdf              ← 7 个测试 PDF
│   └── ...
├── locator/
│   ├── __init__.py
│   ├── patterns.py                   ← 参数规则库
│   ├── text_detector.py              ← 文字层检测
│   ├── ocr_detector.py               ← OCR 检测
│   ├── hybrid_detector.py            ← 混合策略
│   ├── model_hook.py                 ← 未来模型接口
│   └── index.py                      ← 汇总产出
├── cache/                            ← OCR 文本缓存
└── output/
    └── index.json                    ← 最终产出
```
