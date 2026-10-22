#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复核 js / wasm-gc 测试运行时：核对 PATH 中的 node、尝试以 bun 兜底。

用法:
  python probes/probe_js_runner.py
输出:
  probes/logs/jsrunner-*.log     原始输出
  probes/results/jsrunner.json   结构化结果
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "probes" / "embed-probe"
LOGS = ROOT / "probes" / "logs"
RESULTS = ROOT / "probes" / "results"
MOON = Path(r"C:\Users\Administrator\.moon\bin\moon.exe")
SHIM = ROOT / "probes" / "bin"


def dump(name: str, cmd: list[str], cwd: Path, env: dict | None = None) -> dict:
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900)
    (LOGS / name).write_text(
        f"$ {' '.join(cmd)}\n(cwd: {cwd})\nenv[PATH] head={((env or {}).get('PATH', os.environ.get('PATH', ''))).split(';')[:2]}\n"
        f"exit={proc.returncode}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n",
        encoding="utf-8",
    )
    return {"cmd": cmd, "log": str((LOGS / name).relative_to(ROOT).as_posix()),
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout.strip()[-800:], "stderr_tail": proc.stderr.strip()[-800:]}


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    record: dict = {}

    record["which_node"] = {"shutil.which('node')": shutil.which("node"),
                            "shutil.which('node.cmd')": shutil.which("node.cmd"),
                            "shutil.which('bun')": shutil.which("bun")}

    # 用 bun 冒充 node 的 shim 再跑 js 测试
    bun = shutil.which("bun")
    shim_result = {"bun_path": bun}
    if bun:
        SHIM.mkdir(parents=True, exist_ok=True)
        (SHIM / "node.cmd").write_text('@echo off\r\n"%s" %%*\r\n' % bun, encoding="utf-8")
        # moon 若走 shell 解析，仍需 node；此处尝试用 cmd 显式调用 node.cmd
        shim_result["shim_self_test"] = dump(
            "jsrunner-shim-node-version.log", ["node.cmd", "--version"], SHIM,
            env={**os.environ, "PATH": f"{SHIM};{os.environ['PATH']}"})
        shim_result["moon_test_js_with_shim"] = dump(
            "jsrunner-moon-test-js.log",
            [str(MOON), "test", "--target", "js"], PROBE,
            env={**os.environ, "PATH": f"{SHIM};{os.environ['PATH']}"})
    record["shim"] = shim_result

    # wasm-gc: 找出 moon 如何运行 wasm（尝试 moonrun）
    wasm = PROBE / "_build" / "wasm-gc" / "debug" / "test" / "embed-probe.blackbox_test.wasm"
    if wasm.exists():
        record["moonrun_on_wasm_test"] = dump(
            "jsrunner-moonrun-wasm.log", [str(MOON.parent / "moonrun.exe"), str(wasm)], PROBE)

    path = RESULTS / "jsrunner.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT).as_posix()}")
    print(json.dumps(record["which_node"], ensure_ascii=False))
    for key in ("shim_self_test", "moon_test_js_with_shim", "moonrun_on_wasm_test"):
        item = record.get("shim", {}).get(key) or record.get(key)
        if item:
            print(key, "exit=", item["exit_code"], "stderr_tail=", item["stderr_tail"][-200:].replace("\n", " | "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
