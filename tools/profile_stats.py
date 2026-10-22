#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计 langdetect profiles 的量化事实，输出 CSV 与中文 Markdown。

用法:
    python tools/profile_stats.py
输入(只读):
    langdetect/langdetect/profiles/*  (无扩展名的单行 JSON 文件)
输出:
    analysis/profile-facts.csv
    analysis/profile-facts.md
所有数字均由本脚本计算，不做人工填写。
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "langdetect" / "langdetect" / "profiles"
OUT_DIR = ROOT / "analysis"


def key_len(key: str) -> int:
    """按 Unicode 码点计长度（不是 UTF-16 码元）。"""
    return len(key)


def has_non_bmp(key: str) -> bool:
    return any(ord(ch) > 0xFFFF for ch in key)


def load_profile(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        obj = json.load(fh)
    if "freq" not in obj or not isinstance(obj["freq"], dict):
        raise ValueError(f"{path.name}: 缺少 freq 对象")
    return obj


def top_keys(freq: dict, n: int = 10) -> list[tuple[str, int]]:
    return sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def fmt_key(key: str) -> str:
    """把键渲染成可读形式：可见 ASCII 原样，其余用 U+XXXX 转义。"""
    out = []
    for ch in key:
        code = ord(ch)
        if 0x20 <= code <= 0x7E and ch not in "\\|`":
            out.append(ch)
        else:
            out.append(f"U+{code:04X}")
    return "".join(out)


def main() -> int:
    files = sorted(p for p in PROFILE_DIR.iterdir() if p.is_file())
    if not files:
        print(f"未找到档案文件: {PROFILE_DIR}", file=sys.stderr)
        return 1

    rows = []
    len_dist: Counter[int] = Counter()
    total_entries = 0
    total_bytes = 0

    for path in files:
        obj = load_profile(path)
        freq = obj["freq"]
        raw = path.read_bytes()
        lens = Counter(key_len(k) for k in freq)
        bad_len = {k: v for k, v in lens.items() if k not in (1, 2, 3)}
        non_bmp = sum(1 for k in freq if has_non_bmp(k))
        counts = list(freq.values())
        rows.append(
            {
                "language": path.name,
                "bytes": len(raw),
                "entries": len(freq),
                "len1": lens.get(1, 0),
                "len2": lens.get(2, 0),
                "len3": lens.get(3, 0),
                "other_len_keys": sum(bad_len.values()),
                "other_len_detail": ";".join(f"{k}:{v}" for k, v in sorted(bad_len.items())),
                "non_bmp_entries": non_bmp,
                "count_sum": sum(counts),
                "count_max": max(counts) if counts else 0,
                "top10": " | ".join(f"{fmt_key(k)}={v}" for k, v in top_keys(freq)),
                "n_words": obj.get("n_words", ""),
                "name": obj.get("name", ""),
            }
        )
        len_dist.update(lens)
        total_entries += len(freq)
        total_bytes += len(raw)

    rows.sort(key=lambda r: r["language"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUT_DIR / "profile-facts.csv"
    fields = [
        "language",
        "bytes",
        "entries",
        "len1",
        "len2",
        "len3",
        "other_len_keys",
        "other_len_detail",
        "non_bmp_entries",
        "count_sum",
        "count_max",
        "n_words",
        "name",
        "top10",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fields})

    by_entries = sorted(rows, key=lambda r: (-r["entries"], r["language"]))
    by_bytes = sorted(rows, key=lambda r: (-r["bytes"], r["language"]))
    max_entries = by_entries[0]
    min_entries = by_entries[-1]
    max_bytes = by_bytes[0]
    min_bytes = by_bytes[-1]
    total_len = sum(len_dist.values())
    bad_total = sum(v for k, v in len_dist.items() if k not in (1, 2, 3))
    nonbmp_total = sum(r["non_bmp_entries"] for r in rows)
    count_sum_total = sum(r["count_sum"] for r in rows)

    md = []
    md.append("# langdetect 档案量化事实")
    md.append("")
    md.append("由 `python tools/profile_stats.py` 自动生成；请勿手工修改数字。")
    md.append("")
    md.append(f"- 输入目录：`{PROFILE_DIR.relative_to(ROOT).as_posix()}/`")
    md.append(f"- 文件数：{len(rows)}")
    md.append("- 键长度按 Unicode 码点计数（Python `len`）。")
    md.append("- `其他长度键` 指长度不为 1/2/3 的键条目数；`非 BMP` 指键中含码点 > U+FFFF 的条目数。")
    md.append("")
    md.append("## 汇总")
    md.append("")
    md.append("| 指标 | 数值 |")
    md.append("| --- | ---: |")
    md.append(f"| 文件数 | {len(rows)} |")
    md.append(f"| 总字节 | {total_bytes} |")
    md.append(f"| 条目总数 | {total_entries} |")
    md.append(f"| count 总和 | {count_sum_total} |")
    md.append(f"| 条目数最多 | {max_entries['language']} ({max_entries['entries']}) |")
    md.append(f"| 条目数最少 | {min_entries['language']} ({min_entries['entries']}) |")
    md.append(f"| 字节数最多 | {max_bytes['language']} ({max_bytes['bytes']}) |")
    md.append(f"| 字节数最少 | {min_bytes['language']} ({min_bytes['bytes']}) |")
    md.append(f"| 含非 BMP 字符的条目总数 | {nonbmp_total} |")
    md.append(f"| 长度不为 1/2/3 的条目总数 | {bad_total} |")
    md.append("")
    md.append("### 键长分布（全部文件合计）")
    md.append("")
    md.append("| 键长（码点） | 条目数 | 占比 |")
    md.append("| ---: | ---: | ---: |")
    for length in sorted(len_dist):
        n = len_dist[length]
        pct = (n / total_len * 100) if total_len else 0.0
        md.append(f"| {length} | {n} | {pct:.4f}% |")
    md.append(f"| 合计 | {total_len} | 100% |")
    md.append("")
    md.append("## 分语言明细")
    md.append("")
    md.append(
        "| 文件 | 字节 | 条目 | 1 字符 | 2 字符 | 3 字符 | 其他长度 | 非 BMP 条目 | count 总和 | count 最大 |"
    )
    md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in rows:
        other = row["other_len_keys"]
        other_cell = str(other) if other == 0 else f"{other} ({row['other_len_detail']})"
        md.append(
            f"| {row['language']} | {row['bytes']} | {row['entries']} | {row['len1']} | "
            f"{row['len2']} | {row['len3']} | {other_cell} | {row['non_bmp_entries']} | "
            f"{row['count_sum']} | {row['count_max']} |"
        )
    md.append("")
    md.append("## 前 10 高频键")
    md.append("")
    md.append("键按 `count` 降序、同值按键名升序；非可打印字符以 `U+XXXX` 表示。")
    md.append("")
    md.append("| 文件 | 前 10 高频键 |")
    md.append("| --- | --- |")
    for row in rows:
        md.append(f"| {row['language']} | {row['top10']} |")
    md.append("")

    md_path = OUT_DIR / "profile-facts.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"files={len(rows)}")
    print(f"total_bytes={total_bytes}")
    print(f"total_entries={total_entries}")
    print(f"len_dist={dict(sorted(len_dist.items()))}")
    print(f"non_bmp_total={nonbmp_total}")
    print(f"max_entries={max_entries['language']}:{max_entries['entries']}")
    print(f"min_entries={min_entries['language']}:{min_entries['entries']}")
    print(f"max_bytes={max_bytes['language']}:{max_bytes['bytes']}")
    print(f"min_bytes={min_bytes['language']}:{min_bytes['bytes']}")
    print(f"wrote {csv_path.relative_to(ROOT).as_posix()}")
    print(f"wrote {md_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
