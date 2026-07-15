"""
验证工具 — 对比定位器产出与人工标注的真值。

使用方式：
    python3 validate.py

迭代流程：
    1. 编辑 yaml/{category}.yaml → 加/删关键词
    2. python3 validate.py       → 看查全/查准变化
    3. 重复直到满意
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent

# 人工标注的真值（你需要标注实际有参数表的页码）
# 格式: {"filename": [page_numbers]}
# 只标注你已经确认的，未标注的文件不参与验证
GROUND_TRUTH: dict[str, list[int]] = {
    "GB_4599-2024.pdf": [13, 15, 17, 18, 19, 21, 22],
    # 标注更多 PDF 后将自动纳入验证
    # "GB_19152-2025.pdf": [11, 14, 21, 25, 30],
    # "GB_13954-2009.pdf": [...],
}


def load_index() -> dict:
    path = BASE_DIR / "output" / "index.json"
    if not path.exists():
        raise FileNotFoundError(f"请先运行 python3 -m locator.index --mode text 生成 {path}")
    with open(path) as f:
        return json.load(f)


def main():
    index = load_index()

    total_hit = 0
    total_actual = 0
    total_found = 0
    total_fp = 0
    reports: list[str] = []

    for result in index["results"]:
        filename = result["filename"]
        gt = GROUND_TRUTH.get(filename)
        if gt is None:
            continue  # 未标注真值，跳过验证

        found = set(result["summary"].get("pages_found", []))
        actual = set(gt)

        hit = found & actual
        missed = actual - found
        fp = found - actual

        total_hit += len(hit)
        total_actual += len(actual)
        total_found += len(found)
        total_fp += len(fp)

        report = (
            f"  {filename}\n"
            f"    ✅ 正确: {sorted(hit)}\n"
            f"    ❌ 漏检: {sorted(missed)}\n"
            f"    ⚠️ 误报: {sorted(fp)}"
        )
        reports.append(report)

    print("=" * 50)
    print("📊 验证报告")
    print("=" * 50)
    print()
    print("\n\n".join(reports))
    print()
    print("-" * 50)

    recall = total_hit / total_actual * 100 if total_actual else 0
    precision = total_hit / total_found * 100 if total_found else 0

    print(f"   查全率 (Recall):    {total_hit}/{total_actual} = {recall:.1f}%")
    print(f"   查准率 (Precision): {total_hit}/{total_found} = {precision:.1f}%")
    print(f"   误报数:             {total_fp}")
    print()

    if recall >= 95 and precision >= 80:
        print("✅ 规则质量达标")
    elif recall >= 95:
        print("⚠️ 查全达标，查准偏低 — 考虑收紧规则")
    elif precision >= 80:
        print("⚠️ 查准达标，查全偏低 — 考虑扩展关键词")
    else:
        print("🔧 两者均未达标 — 需要调整规则")


if __name__ == "__main__":
    main()
