#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C 段探针：多目标 build/test、native 文件 API 检索、发布限制检索。

用法:
  python probes/probe_targets.py
输出:
  probes/logs/target-*.log       原始命令输出
  probes/logs/idedoc-*.log       moon ide doc 原始输出
  probes/logs/publish-help.log   moon publish --help 原始输出
  probes/results/targets.json   结构化结果
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "probes" / "embed-probe"
LOGS = ROOT / "probes" / "logs"
RESULTS = ROOT / "probes" / "results"
MOON = Path(r"C:\Users\Administrator\.moon\bin\moon.exe")
NODE = "node"

TARGETS = ["native", "wasm-gc", "js"]
API_QUERIES = [
    "@fs",
    "moonbitlang/x",
    "read_file",
    "File",
    "open_file",
]


def run(cmd: list[str], cwd: Path, log_name: str) -> dict:
    # 本机 PATH 上的 node.cmd 指向不存在的 D:\nvm4w\nodejs\bun；
    # 用 probes/bin/node.cmd（指向真实 bun）前置，保证 js 目标有可用运行时。
    env = {**os.environ, "PATH": f"{ROOT / 'probes' / 'bin'};" + os.environ.get("PATH", "")}
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900)
    elapsed = time.perf_counter() - started
    out, err, code = proc.stdout, proc.stderr, proc.returncode
    (LOGS / log_name).write_text(
        f"$ {' '.join(str(c) for c in cmd)}\n(cwd: {cwd})\n"
        f"exit={code} wall_seconds={elapsed:.3f}\n--- stdout ---\n{out}\n--- stderr ---\n{err}\n",
        encoding="utf-8",
    )
    return {"cmd": [str(c) for c in cmd], "log": str((LOGS / log_name).relative_to(ROOT).as_posix()),
            "exit_code": code, "wall_seconds": round(elapsed, 3),
            "stdout": out, "stderr": err}

def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    record: dict = {"targets": {}, "api": {}, "publish": {}, "node": {}}
    RESULTS.mkdir(parents=True, exist_ok=True)

    # 固定探针数据形态：55 语言 flat 编码（与 measure_scale.py --mode flat --langs all 一致）
    run(["python", str(ROOT / "probes" / "gen_mbt.py"), "--mode", "flat", "--langs", "all"],
        ROOT, "target-00-gen.log")
    (PROBE / "lib" / "data" / "moon.pkg").write_text(
        'import {\n  "moonbitlang/core/string",\n}\n', encoding="utf-8")



    # node 可用性
    try:
        node = run([NODE, "--version"], PROBE, "target-node-version.log")
        keep = [ln for ln in (node["stdout"] + "\n" + node["stderr"]).splitlines() if ln.strip()]
        node["key_lines"] = keep
        del node["stdout"], node["stderr"]
    except OSError as exc:
        node = {"cmd": [NODE, "--version"], "error": f"OSError {exc.errno}: {exc.strerror}",
                "key_lines": [f"OSError {exc.errno}: {exc.strerror}"],
                "exit_code": None}
    record["node"]["version"] = node

    for target in TARGETS:
        entry: dict = {}
        # 每个目标冷编译一份：清干净后 build
        run([str(MOON), "clean"], PROBE, f"target-{target}-00-clean.log")
        entry["build"] = run([str(MOON), "build", "--target", target], PROBE,
                             f"target-{target}-01-build.log")
        entry["test"] = run([str(MOON), "test", "--target", target], PROBE,
                            f"target-{target}-02-test.log")
        for key in ("build", "test"):
            r = entry[key]
            keep = [ln for ln in (r["stdout"] + "\n" + r["stderr"]).splitlines() if ln.strip()]
            r["key_lines"] = keep[-14:]
            del r["stdout"], r["stderr"]
        record["targets"][target] = entry

    # native 侧文件/IO API 检索
    for query in API_QUERIES:
        try:
            r = run([str(MOON), "ide", "doc", query], PROBE, f"idedoc-{query.replace('@','at-')}.log")
            keep = [ln for ln in (r["stdout"] + "\n" + r["stderr"]).splitlines() if ln.strip()]
            r["key_lines"] = keep[:30]
            del r["stdout"], r["stderr"]
        except Exception as exc:  # noqa: BLE001
            r = {"error": repr(exc)}
        record["api"][query] = r

    # 发布体积/文件数限制
    try:
        r = run([str(MOON), "publish", "--help"], PROBE, "publish-help.log")
        keep = [ln for ln in (r["stdout"] + "\n" + r["stderr"]).splitlines() if ln.strip()]
        r["key_lines"] = keep
        del r["stdout"], r["stderr"]
    except Exception as exc:  # noqa: BLE001
        r = {"error": repr(exc)}
    record["publish"]["moon publish --help"] = r

    try:
        r = run(["mooncake", "--help"], PROBE, "mooncake-help.log")
        keep = [ln for ln in (r["stdout"] + "\n" + r["stderr"]).splitlines() if ln.strip()]
        r["key_lines"] = keep[:20]
        del r["stdout"], r["stderr"]
    except Exception as exc:  # noqa: BLE001
        r = {"error": repr(exc)}
    record["publish"]["mooncake --help"] = r

    path = RESULTS / "targets.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT).as_posix()}")
    for t, e in record["targets"].items():
        print(t, "build_exit=", e["build"]["exit_code"], "test_exit=", e["test"]["exit_code"])
    for q, r in record["api"].items():
        print("api", q, "exit=", r.get("exit_code", "n/a"), "lines=", len(r.get("key_lines", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
