# PDF → Markdown → Parameter Extraction Benchmark

一份聚焦 **PDF→Markdown 表格保真度** 的对比基准。  
目的不是"谁提取的字符多"，而是"谁能把配光曲线表完整带到 LLM 面前"。

---

## 定位

实际场景：

```
PDF (配光曲线表) → Markdown (Pipe Table) → LLM → {照度值, 光型参数, ...}
```

benchmark 设计为可复用——换一批学术论文、财务报表、技术规格书的 PDF，就能测自己场景下的参数提取管线。

---

## 测试集

| # | 文件 | 类型 | 页数 | 含参类型 | 说明 |
|---|------|------|------|---------|------|
| 1 | `GB_4599-2024.pdf` | 前照灯配光 | 59 | 远光/近光最大照度、配光分布 | 文本+表格，主测试用例 |
| 2 | `GB_13954-2009.pdf` | 特种车辆警示灯 | 18 | 光度参数、色度坐标 | 文本+表格，不同表结构 |
| 3 | `GB_19152-2025.pdf` | 摩托车照明 | 55 | 配光曲线、照度阈值 | 文本+表格，类似结构 |
| 4 | `GB_4785-2019.pdf` | 信号灯安装 | 82 | 光度参数 | **编码异常**，考察容错 |
| 5 | `GB_23826-2025.pdf` | — | 35 | — | **文字+扫描混合**，考察兜底 |

---

## 对比工具

| 工具 | 策略 | 安装 | 许可 | Markdown 输出 | 表格支持 |
|------|------|------|------|-------------|---------|
| **pymupdf4llm** | PyMuPDF 官方 PDF→Markdown | `pip install pymupdf4llm` | AGPL | ✅ 原生 Pipe Table | ✅ 线条表格 |
| **pdfplumber** | 布局感知表格提取 + 手拼 | ✅ 已有 | MIT | ⚠️ 需序列化 | ✅ `extract_tables()` |

> Marker 等含 OCR 的 PDF→Markdown 工具因安装较重，不纳入主对比，详见 REPORT 附录。

---

## 评估维度

| 维度 | 测量方式 | 权重 |
|------|---------|------|
| **表格保真度** | 配光曲线表在 Markdown 中是否保留行列结构 | ★★★★★ |
| **参数可提取率** | 用 `validation_prompt.md` 喂 LLM，提取 3 个核心参数的正确率 | ★★★★★ |
| **中文正确率** | 抽查 5 处参数值（如"照度≥0.3 lx"）是否乱码 | ★★★★ |
| **阅读顺序** | 多栏排版是否交错 | ★★★ |
| **耗时** | `time.perf_counter()` 每文件处理时间 | ★★ |

---

## 验证方式

```bash
# 1. 生成 Markdown
python3 benchmark.py

# 2. 用 validation_prompt.md 喂 LLM 提取参数
# 3. 人工比对提取值与标准原文
```

详见 `validation_prompt.md`。

---

## 项目结构

```
pdf-extract-bench/
├── README.md
├── .gitignore
├── validation_prompt.md          ← LLM 参数提取验证 prompt
├── datasets/
│   ├── sources.csv                ← 元数据（含 parameters_present / table_types）
│   ├── GB_4599-2024.pdf           ← 🔗 core: 前照灯配光
│   ├── GB_13954-2009.pdf          ← 🔗 core: 警示灯光度
│   ├── GB_19152-2025.pdf          ← 🔗 core: 摩托车配光
│   ├── GB_4785-2019.pdf           ← 🔗 edge: 编码异常
│   └── GB_23826-2025.pdf          ← 🔗 edge: 文字+扫描混合
├── markdown_outputs/              ← Markdown 产出（.gitkeep 占位）
├── extractors.py                  ← pymupdf4llm + pdfplumber 封装
├── benchmark.py                   ← 统一入口
└── REPORT.md                      ← 博客体报告（最终产出）
```

---

## 复用指南

```bash
# 换自己的 PDF 测试集
cp ~/your-docs/*.pdf ./datasets/
# 更新 datasets/sources.csv 的 parameters_present / table_types
# 更新 validation_prompt.md 的目标参数
# 跑 benchmark.py
```
