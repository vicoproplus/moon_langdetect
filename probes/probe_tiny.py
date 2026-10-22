#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""空工程对照探针：probes/tiny-probe（1 条断言，无大数据）在三目标下的 test 结果。

用法:
  python probes/probe_tiny.py
输出:
  probes/logs/tinyprobe-test-<target>.log
  probes/results/tinyprobe-targets.json
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "probes" / "tiny-probe"
LOGS = ROOT / "probes" / "logs"
RESULTS = ROOT / "probes" / "results"
MOON = Path(r"C:\Users\Administrator\.moon\bin\moon.exe")
TARGETS = ["native", "wasm-gc", "js"]


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PATH": f"{ROOT / 'probes' / 'bin'};" + os.environ.get("PATH", "")}
    out: dict = {}
    for target in TARGETS:
        proc = subprocess.run(
            [str(MOON), "test", "--target", target], cwd=PROBE, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=900,
        )
        (LOGS / f"tinyprobe-test-{target}.log").write_text(
            f"$ moon test --target {target}\n(cwd: {PROBE})\nexit={proc.returncode} "
            f"(hex={proc.returncode & 0xFFFFFFFF:#010x})\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n",
            encoding="utf-8",
        )
        tail = [ln for ln in (proc.stdout + "\n" + proc.stderr).strip().splitlines() if ln.strip()]
        out[target] = {"exit": proc.returncode, "tail": tail[-4:]}
        print(target, proc.returncode, tail[-1][:120] if tail else "")

    (RESULTS / "tinyprobe-targets.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {(RESULTS / 'tinyprobe-targets.json').relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())