#!/usr/bin/env python3
"""PDF text extraction benchmark — run all extractors on test set, measure, report."""

import csv
import json
import os
import time
import resource
from pathlib import Path

from extractors import EXTRACTORS

BENCH_DIR = Path(__file__).parent
DATASETS_DIR = BENCH_DIR / "datasets"
OUTPUTS_DIR = BENCH_DIR / "outputs"
SOURCES_CSV = DATASETS_DIR / "sources.csv"


def read_sources(path: Path) -> list[dict]:
    """Read sources.csv and return list of file metadata."""
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["pages"] = int(row["pages"])
            row["pdfplumber_chars"] = int(row["pdfplumber_chars"])
            rows.append(row)
    return rows


def run_extractor(name: str, fn, pdf_path: Path) -> dict:
    """Run a single extractor on a single PDF, return metrics."""
    import gc
    gc.collect()
    start_time = time.perf_counter()

    try:
        text = fn(str(pdf_path))
    except Exception as e:
        return {"extractor": name, "file": pdf_path.name, "status": "error", "error": str(e)}

    elapsed = time.perf_counter() - start_time
    gc.collect()
    max_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    # Save output
    out_dir = OUTPUTS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / pdf_path.with_suffix(".txt").name
    out_path.write_text(text, encoding="utf-8")

    return {
        "extractor": name,
        "file": pdf_path.name,
        "status": "ok",
        "chars": len(text),
        "time_s": round(elapsed, 4),
        "max_rss_kb": max_rss_kb,
    }


def main():
    sources = read_sources(SOURCES_CSV)
    print(f"📋 Test set: {len(sources)} files")
    print(f"🔧 Extractors: {', '.join(EXTRACTORS.keys())}")
    print()

    all_results: list[dict] = []

    for row in sources:
        filename = row["filename"]
        pdf_path = DATASETS_DIR / filename
        if not pdf_path.exists():
            print(f"  ⚠️  {filename} — file not found, skipping")
            continue
        print(f"  📄 {filename} ({row['pages']}p, {row['category']})")
        for ext_name, (_, ext_fn) in EXTRACTORS.items():
            result = run_extractor(ext_name, ext_fn, pdf_path)
            all_results.append(result)
            status_mark = "✅" if result["status"] == "ok" else "❌"
            print(f"    {status_mark} {ext_name:12s} {result.get('chars', 0):>8} chars  "
                  f"{result.get('time_s', 0):>7.3f}s  "
                  f"{result.get('max_rss_kb', 0)//1024:>5} MB", end="")
            if "error" in result:
                print(f"  {result['error']}")
            else:
                print()
        print()

    # Save results
    results_path = OUTPUTS_DIR / "results.json"
    results_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📊 Full results saved to {results_path}")

    # Summary table
    print()
    print("=" * 80)
    print("SUMMARY — chars extracted per file per extractor")
    print("=" * 80)
    print(f"{'File':30s}", end="")
    for ext_name in EXTRACTORS:
        print(f"{ext_name:>14s}", end="")
    print()

    # Group results by file
    by_file: dict[str, dict[str, dict]] = {}
    for r in all_results:
        by_file.setdefault(r["file"], {})[r["extractor"]] = r

    for row in sources:
        fname = row["filename"]
        label = f"{fname} ({row['category']})"
        print(f"{label:30s}", end="")
        for ext_name in EXTRACTORS:
            r = by_file.get(fname, {}).get(ext_name, {})
            if r.get("status") == "ok":
                print(f"{r['chars']:>10,d}", end="")
                # print(f"{r['time_s']:>7.3f}s", end="")
            else:
                print(f"{'ERROR':>14s}", end="")
        print()

    print()
    print("TIMING (seconds)")
    print(f"{'File':30s}", end="")
    for ext_name in EXTRACTORS:
        print(f"{ext_name:>14s}", end="")
    print()
    for row in sources:
        fname = row["filename"]
        label = f"{fname} ({row['category']})"
        print(f"{label:30s}", end="")
        for ext_name in EXTRACTORS:
            r = by_file.get(fname, {}).get(ext_name, {})
            if r.get("status") == "ok":
                print(f"{r['time_s']:>13.3f}s", end="")
            else:
                print(f"{'ERROR':>14s}", end="")
        print()


if __name__ == "__main__":
    main()
