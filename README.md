# PDF Text Extraction Benchmark

一份轻量、可复用的 PDF 文本提取器对比基准，覆盖中文国标、英文学术论文和扫描件场景。

---

## 定位

不是论文级评测。目标是快速回答一个实际问题：

> **我的文档类型下，哪个提取器又快又准？**

benchmark 设计为可复用——换一批 PDF 即可跑其他项目的场景。

---

## 测试集

| # | 文件 | 类型 | 页数 | 提取字符（pdfplumber） | 来源 |
|---|------|------|------|----------------------|------|
| 1 | `GB_4599-2024.pdf` | 中文国标（配光曲线表） | 59 | ~46KB | BriefNexus 标准库 |
| 2 | `GB_4785-2019.pdf` | 中文国标（长篇） | 82 | ~148KB | BriefNexus 标准库 |
| 3 | `GB_T_34446-2017.pdf` | **扫描件**（0 字符可提取） | 12 | 0 | BriefNexus 标准库 |
| 4 | `darkdriving_2603.18067.pdf` | 英文学术论文（双栏） | 8 | ~37KB | arXiv |
| 5 | `hawkdrive_2404.04653.pdf` | 英文学术论文（双栏） | 6 | ~28KB | arXiv |

> `sources.csv` 记录了每份 PDF 的完整元数据。

---

## 对比提取器

| 提取器 | 策略 | 安装 | 许可 | 备注 |
|--------|------|------|------|------|
| **PyMuPDF (fitz)** | 通用首选 | `pip install PyMuPDF` | AGPL | C 引擎 |
| **pdfplumber** | 表格专项 | ✅ 已有 | MIT | 纯 Python |
| **pdfminer.six** | 高可配置 | ✅ 已有 | MIT | 最稳定 |
| **pypdfium2** | C 引擎（PDFium） | ✅ 已有 | Apache 2.0 | Chromium 内核 |

> 扫描件（#3）各提取器将返回 0 字符，benchmark 仅记录这一事实，不做 OCR 评估。

---

## 评估维度

| 维度 | 测量方式 |
|------|---------|
| **字符召回率** | 提取字符数（对各提取器横向对比） |
| **中文正确性** | 手动抽查 5 处字段是否乱码 |
| **表格结构** | GB 4599 配光曲线表能否正确解析为行列 |
| **阅读顺序** | 双栏/多节文档是否左右栏交错 |
| **耗时** | `time.perf_counter()` 每文件累计处理时间 |
| **峰值内存** | `/usr/bin/time -v` 追踪 |

---

## 使用方式

```bash
# 1. 安装缺失依赖
pip install PyMuPDF

# 2. 运行 benchmark
cd /home/zzz/workspace/projects/pdf-extraction-benchmark
python3 benchmark.py

# 3. 产出在 outputs/{extractor_name}/{pdf_basename}.txt
# 例如: outputs/pymupdf/GB_4599-2024.txt
```

---

## 产出物

```
outputs/
├── pymupdf/
│   ├── GB_4599-2024.txt
│   ├── GB_4785-2019.txt
│   ├── darkdriving_2603.18067.txt
│   └── hawkdrive_2404.04653.txt
├── pdfplumber/
│   └── ... (同上)
├── pdfminer/
│   └── ... (同上)
├── pypdfium2/
│   └── ... (同上)
└── results.json             ← 汇总表格 + 指标
```

---

## 复用指南

```bash
# 换一份你自己的 PDF 测试集
cp -r ~/your-project/pdfs ./datasets/
# 更新 datasets/sources.csv
# 跑 benchmark.py
```

---

## 项目结构

```
pdf-extraction-benchmark/
├── README.md
├── sources.csv → datasets/     ← 测试集清单（顶层快捷入口）
├── .gitignore                  ← 大文件/产出物排除追踪
├── datasets/
│   ├── sources.csv              ← 元数据（类别/页数/pdfplumber字符数/备注）
│   ├── GB_4599-2024.pdf         ← 🔗 中文国标 59页 含表格
│   ├── GB_4785-2019.pdf         ← 🔗 中文国标 82页 长篇
│   ├── GB_T_34446-2017.pdf      ← 🔗 扫描件 12页 0字符
│   ├── darkdriving_2603.18067.pdf ← 📥 英文论文 8页 双栏
│   └── hawkdrive_2404.04653.pdf   ← 📥 英文论文 6页 双栏
├── outputs/                     ← 提取结果（.gitkeep 占位，不被追踪）
├── extractors.py                ← 提取器封装
├── benchmark.py                 ← 统一入口
└── REPORT.md                    ← 博客体报告（最终产出）
```
