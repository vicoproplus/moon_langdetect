#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 probes/results/*.json 汇总成 Markdown 表格（数字全部来自测量文件）。

用法:
  python tools/summarize_probes.py
输出:
  analysis/probe-tables.md
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "probes" / "results"
OUT = ROOT / "analysis" / "probe-tables.md"

SCALES = [
    ("s1-map", "1 (so)", "map"),
    ("s5-map", "5 (so,sw,tl,af,en)", "map"),
    ("s55-map", "55 (全部)", "map"),
    ("s1-flat", "1 (so)", "flat"),
    ("s5-flat", "5 (so,sw,tl,af,en)", "flat"),
    ("s55-flat", "55 (全部)", "flat"),
]


def load(label: str) -> dict | None:
    path = RESULTS / f"{label}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_range(values: list[float]) -> str:
    if not values:
        return "—"
    lo, hi = min(values), max(values)
    return f"{lo:.3f}" if lo == hi else f"{lo:.3f}–{hi:.3f}"



def log_key_line(entry: dict) -> str:
    """从原始日志中挑出结论行（Total tests / exit code / 运行时缺失），避免被警告刷屏淹没。"""
    rel = entry.get("log") or ""
    if rel.startswith(("probes/", "analysis/", "tools/")):
        log = ROOT / rel
    else:
        log = (RESULTS.parent / "logs" / Path(rel).name) if rel else ROOT / "nonexistent"
    if log.exists():
        text = log.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in text:
            if line.startswith("Total tests"):
                return line.strip().replace("|", "\\|")
        for line in text:
            if "exit code" in line or "The system cannot find" in line:
                return line.strip().replace("|", "\\|")
        for line in text:
            if line.startswith("Error"):
                return line.strip().replace("|", "\\|")
    return key_line(entry)


def key_line(entry: dict) -> str:
    """取最有信息量的一行输出：优先 Total tests / exit code / Error，否则非 warning 行。"""
    lines = entry.get("key_lines") or entry.get("tail") or []
    for line in lines:
        if line.startswith("Total tests") or "exit code" in line:
            return line.strip().replace("|", "\\|")
    for line in lines:
        if line.startswith("Error") or "failed to run" in line:
            return line.strip().replace("|", "\\|")
    for line in lines:
        if "创建库" not in line and "Warning" not in line and "───" not in line and "│" not in line:
            return line.strip().replace("|", "\\|")
    for line in reversed(lines):
        if "Warning" not in line and "creating library" not in line.lower():
            return line.strip().replace("|", "\\|")
    return "—"


def test_cell(record: dict) -> str:
    runs = record.get("test_runs") or []
    if not runs:
        return "未测"
    run = runs[0]
    if run.get("timed_out"):
        return "超时"
    out = "\n".join(run.get("output_tail", []))
    if run["exit_code"] == 0:
        for line in run.get("output_tail", []):
            if line.startswith("Total tests"):
                return f"通过：{line}"
        return "通过"
    for line in reversed(run.get("output_tail", [])):
        if "exit code" in line:
            return f"失败：`{line.strip()}`"
    return f"失败：exit={run['exit_code']}"


def main() -> int:
    lines: list[str] = ["# 探针数据汇总（脚本生成）", "",
                        "由 `python tools/summarize_probes.py` 从 `probes/results/*.json` 生成。", ""]

    lines += ["## B. 内嵌规模测量", "",
              "| 标签 | 编码 | 语言数 | 条目数 | 生成 data.mbt 字节 | 冷编译耗时(s) | 可执行文件字节 | _build 总字节 | moon test |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for label, scale, mode in SCALES:
        rec = load(label)
        if rec is None:
            lines.append(f"| {label} | {mode} | {scale} | 未测 | 未测 | 未测 | 未测 | 未测 | 未测 |")
            continue
        times = [r["wall_seconds"] for r in rec.get("build_runs", [])]
        lines.append(
            f"| {label} | {mode} | {rec['languages']} | {rec['entries']} | {rec['data_mbt_bytes']} | "
            f"{fmt_range(times)} | {rec.get('exe_bytes') or '—'} | {rec.get('build_dir_bytes') or '—'} | "
            f"{test_cell(rec)} |"
        )

    lines += ["", "### 逐次冷编译耗时", "",
              "| 标签 | 第 1 次 | 第 2 次 | 第 3 次 | 退出码 |",
              "| --- | ---: | ---: | ---: | --- |"]
    for label, scale, mode in SCALES:
        rec = load(label)
        if rec is None:
            lines.append(f"| {label} | 未测 | 未测 | 未测 | 未测 |")
            continue
        runs = rec.get("build_runs", [])
        cells = [f"{r['wall_seconds']:.3f}" for r in runs] + ["—"] * (3 - len(runs))
        codes = ",".join(str(r["exit_code"]) for r in runs)
        lines.append(f"| {label} | {cells[0]} | {cells[1]} | {cells[2]} | {codes} |")

    lines += ["", "## C. 三目标（55 语言 flat 数据 + 56 条断言）", "",
              "| 目标 | build 退出码 | build 秒 | test 退出码 | test 秒 | 关键输出 |",
              "| --- | ---: | ---: | ---: | ---: | --- |"]
    targets = load("targets")
    if targets:
        for target in ("native", "wasm-gc", "js"):
            entry = targets["targets"][target]
            b, t = entry["build"], entry["test"]
            tail = log_key_line(t)
            lines.append(
                f"| {target} | {b['exit_code']} | {b['wall_seconds']:.3f} | {t['exit_code']} | "
                f"{t['wall_seconds']:.3f} | {tail} |")
    else:
        lines.append("| native | 未测 | 未测 | 未测 | 未测 | 未测 |")
        lines.append("| wasm-gc | 未测 | 未测 | 未测 | 未测 | 未测 |")
        lines.append("| js | 未测 | 未测 | 未测 | 未测 | 未测 |")

    tiny = load("tinyprobe-targets")
    lines += ["", "### 空工程对照（probes/tiny-probe，1 条断言，无大数据）", "",
              "| 目标 | test 退出码 | 关键输出 |", "| --- | ---: | --- |"]
    if tiny:
        for target in ("native", "wasm-gc", "js"):
            entry = dict(tiny[target])
            entry["log"] = f"probes/logs/tinyprobe-test-{target}.log"
            tail = log_key_line(entry)
            lines.append(f"| {target} | {entry['exit']} | {tail} |")
    else:
        lines.append("| native | 未测 | 未测 |")
        lines.append("| wasm-gc | 未测 | 未测 |")
        lines.append("| js | 未测 | 未测 |")

    lines += ["", "## 产物体积（55 语言 flat，按目标）", "",
              "| 目标 | 全部文件字节 | 最大文件 |", "| --- | ---: | --- |"]
    artifacts = load("artifacts")
    if artifacts:
        for target in ("native", "wasm-gc", "js"):
            entry = artifacts[target]
            top = entry["top5"][0]
            lines.append(f"| {target} | {entry['total_bytes']} | `{top[0]}` ({top[1]}) |")
    else:
        lines.append("| native | 未测 | 未测 |")

    lines += ["", "## 紧凑编码相对 map 的比值（55 语言）", ""]
    m, f = load("s55-map"), load("s55-flat")
    if m and f:
        def ratio(a, b):
            return f"{a / b:.4f}"
        lines += ["| 指标 | map | flat | flat/map |", "| --- | ---: | ---: | ---: |"]
        lines.append(f"| 生成字节 | {m['data_mbt_bytes']} | {f['data_mbt_bytes']} | "
                     f"{ratio(f['data_mbt_bytes'], m['data_mbt_bytes'])} |")
        lines.append(f"| 冷编译秒(最小) | {min(r['wall_seconds'] for r in m['build_runs']):.3f} | "
                     f"{min(r['wall_seconds'] for r in f['build_runs']):.3f} | "
                     f"{ratio(min(r['wall_seconds'] for r in f['build_runs']), min(r['wall_seconds'] for r in m['build_runs']))} |")
        lines.append(f"| 可执行文件字节 | {m['exe_bytes']} | {f['exe_bytes']} | {ratio(f['exe_bytes'], m['exe_bytes'])} |")
        lines.append(f"| _build 字节 | {m['build_dir_bytes']} | {f['build_dir_bytes']} | "
                     f"{ratio(f['build_dir_bytes'], m['build_dir_bytes'])} |")
    else:
        lines.append("未测")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
