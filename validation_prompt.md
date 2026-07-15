# 参数提取验证 Prompt

> 用途：验证 pymupdf4llm / pdfplumber 的 Markdown 输出是否能被 LLM 正确提取参数。
> 方法：将 Markdown 输出贴到此 prompt 下方，LLM 返回结构化结果，人工核对。

---

## 任务

你是一个参数提取助手。以下是某份中国国家标准（GB）部分内容的 Markdown 格式输出。请从中提取以下参数，按 JSON 格式返回。

## 提取目标

```json
{
  "standard_no": "对应的标准号，如 GB 4599-2024",
  "parameters": [
    {
      "name": "参数名称",
      "value": "数值+单位",
      "condition": "适用的条件，如远光/近光"
    }
  ]
}
```

## 注意

- 参数值请保留原始数值和单位，不要换算
- 如果某个参数在文本中不存在，返回 null
- 如果表格与文字描述冲突，以表格数据为准

## Markdown 内容

```
【在此粘贴 pymupdf4llm 或 pdfplumber 的 Markdown 输出】
```
