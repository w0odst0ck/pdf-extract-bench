# PDF → Markdown → Parameter Extraction Benchmark

## 定位

覆盖 **108 个国标 PDF** 的完整参数提取管线测试。

一条 pipeline，两条技术路线：

```
            ┌─ 文字层 PDF ──→ pymupdf4llm / pdfplumber ──→ Markdown ──┐
108 个 PDF ─┤                                                        ├──→ LLM → 参数提取
            └─ 扫描件 PDF ──→ OCRmyPDF → 补文字层 → 同上提取器 ──→ Markdown ┘
```

benchmark 回答的核心问题：

> **给定一份 PDF，我应该走哪条路线，才能让 LLM 正确提取出配光曲线参数？**

---

## 技术路线

### Route A：文本提取（覆盖 51 个 PDF，47%）

| 工具 | 策略 | 安装 | Markdown |
|------|------|------|----------|
| **pymupdf4llm** | PDF→Markdown 一步到位 | `pip install pymupdf4llm` | ✅ 原生 Pipe Table |
| **pdfplumber** | 布局感知提取+手拼序列化 | ✅ 已有 | ⚠️ 需手拼 |

适用于有文字层的 PDF。其中：
- **15-20 个** 全文可提取（如 GB 4599 每页连续中文）
- **30+ 个** 只有封面/目次页有文字（正文扫描图）

### Route B：OCR（覆盖 57 个 PDF，53%）

| 工具 | 策略 | 安装 |
|------|------|------|
| **OCRmyPDF + Tesseract (chi_sim)** | 扫描件→文字层→再走 Route A | `apt install tesseract-ocr tesseract-ocr-chi-sim` + `pip install ocrmypdf` |
| Marker（备用） | 含 OCR 的 PDF→Markdown | `pip install marker-pdf`（较重，PyTorch） |

扫描件类型：大部分为老版标准、已废止标准的扫描存档、部分新版标准的配光曲线图页。

---

## 测试集（7 份 PDF）

| # | 文件 | 路线 | 类型 | 页数 | 说明 |
|---|------|------|------|------|------|
| 1 | `GB_4599-2024.pdf` | text | 前照灯配光 | 59 | 文本层完整，含配光曲线表 |
| 2 | `GB_13954-2009.pdf` | text | 警示灯光度 | 18 | 文本层完整，光度参数表 |
| 3 | `GB_19152-2025.pdf` | text | 摩托车照明 | 55 | 文本层稀疏，文字+表格混排 |
| 4 | `GB_4785-2019.pdf` | text | 信号灯安装 | 82 | **编码异常**，所有提取器乱码 |
| 5 | `GB_23826-2025.pdf` | both | 文字+扫描混合 | 35 | 30MB，大部分为图像，测试兜底 |
| 6 | `GB_T_5700-2023.pdf` | ocr | 照明测量方法 | 52 | **纯扫描件**，25MB，含测量数据表 |
| 7 | `GB_T_7922-2023.pdf` | ocr | 光源光色测量 | 17 | **纯扫描件**，4MB，含色度坐标表 |

---

## 评估维度

| 维度 | 测量方式 | Route A | Route B |
|------|---------|---------|---------|
| **表格保真度** | 配光曲线表在 Markdown 中是否保留行列 | ✅ | ✅ |
| **参数可提取率** | 用 validation_prompt 喂 LLM，提取 3 个参数的正确率 | ✅ | ✅ |
| **中文正确率** | 抽查 5 处参数值是否乱码 | ✅ | ✅ |
| **阅读顺序** | 多栏排版是否交错 | ✅ | ✅ |
| **耗时** | `time.perf_counter()` | ✅ | ✅ |
| **文字层可用率** | 提取字符数 / PDF 实际字符数 | ✅ | — |
| **OCR 恢复率** | OCR 后新增了多少可用文本 | — | ✅ |

---

## 验证方式

```bash
# Route A：文本提取
python3 benchmark.py --route text

# Route B：OCR 提取（先补 OCR 层）
python3 benchmark.py --route ocr

# 全量
python3 benchmark.py --route all
```

结果以 Markdown 格式输出到 `markdown_outputs/{route}/{tool}/{filename}.md`。

---

## 项目结构

```
pdf-extract-bench/
├── README.md
├── .gitignore
├── validation_prompt.md          ← LLM 参数提取验证 prompt
├── datasets/
│   ├── sources.csv                ← 含 route/parameters_present/table_types 列
│   ├── GB_4599-2024.pdf           ← 🔗 text: 前照灯配光      59p
│   ├── GB_13954-2009.pdf          ← 🔗 text: 警示灯光度      18p
│   ├── GB_19152-2025.pdf          ← 🔗 text: 摩托车配光      55p
│   ├── GB_4785-2019.pdf           ← 🔗 text: 编码异常        82p
│   ├── GB_23826-2025.pdf          ← 🔗 both: 混合           35p
│   ├── GB_T_5700-2023.pdf         ← 🔗 ocr:  照明测量       52p
│   └── GB_T_7922-2023.pdf         ← 🔗 ocr:  光色测量       17p
├── markdown_outputs/
│   ├── text/                      ← Route A 产出
│   │   ├── pymupdf4llm/
│   │   ├── pdfplumber/
│   │   └── combined/
│   └── ocr/                       ← Route B 产出
│       ├── tesseract/
│       └── combined/
├── extractors/
│   ├── __init__.py
│   ├── text.py                    ← pymupdf4llm + pdfplumber
│   └── ocr.py                     ← OCRmyPDF + Tesseract
├── benchmark.py                   ← 统一入口，--route 参数
└── REPORT.md                      ← 博客体报告（最终产出）
```
