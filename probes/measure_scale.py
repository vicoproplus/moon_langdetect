#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分级测量探针：生成 -> 冷编译 xN -> 测试 -> 记录产物体积。

用法:
  python probes/measure_scale.py --mode map --langs 1 --label s1-map --builds 3
  python probes/measure_scale.py --mode map --langs 5 --label s5-map --builds 3
  python probes/measure_scale.py --mode map --langs all --label s55-map --builds 2
  python probes/measure_scale.py --mode flat --langs all --label s55-flat --builds 2

每一轮 build 前都执行 moon clean，因此耗时是全量冷编译。
输出:
  probes/logs/<label>-*.log                原始 moon 输出
  probes/results/<label>.json              测量结果
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "probes" / "embed-probe"
LOGS = ROOT / "probes" / "logs"
RESULTS = ROOT / "probes" / "results"
MOON = Path(r"C:\Users\Administrator\.moon\bin\moon.exe")
TIMEOUT = 15 * 60  # 秒，单条命令上限


def run(cmd: list[str], cwd: Path, log_name: str, timeout: int = TIMEOUT) -> dict:
    started = time.perf_counter()
    timed_out = False
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
        )
        out, err, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = (exc.stderr or "") + "\nTIMEOUT"
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        code = -999
        timed_out = True
    elapsed = time.perf_counter() - started
    log_path = LOGS / log_name
    log_path.write_text(
        f"$ {' '.join(str(c) for c in cmd)}\n(cwd: {cwd})\n"
        f"exit={code} wall_seconds={elapsed:.3f} timeout={timeout}\n"
        f"--- stdout ---\n{out}\n--- stderr ---\n{err}\n",
        encoding="utf-8",
    )
    tail = [ln for ln in (out + "\n" + err).strip().splitlines() if ln.strip()]
    return {
        "cmd": [str(c) for c in cmd],
        "log": str(log_path.relative_to(ROOT).as_posix()),
        "exit_code": code,
        "wall_seconds": round(elapsed, 3),
        "timed_out": timed_out,
        "output_tail": tail[-6:],
    }


def dir_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def largest_files(path: Path, n: int = 5) -> list[dict]:
    files = [p for p in path.rglob("*") if p.is_file()]
    files.sort(key=lambda p: -p.stat().st_size)
    return [{"path": str(p.relative_to(path).as_posix()), "bytes": p.stat().st_size} for p in files[:n]]


def dump(record: dict, label: str) -> None:
    path = RESULTS / f"{label}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT).as_posix()}")
    print(json.dumps({k: record.get(k) for k in (
        "label", "mode", "languages", "entries", "data_mbt_bytes",
        "build_seconds", "exe_bytes", "build_dir_bytes", "timed_out")}, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["map", "flat"], required=True)
    ap.add_argument("--langs", default="all")
    ap.add_argument("--label", required=True)
    ap.add_argument("--builds", type=int, default=3)
    args = ap.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    # 生成前先设定数据包依赖：flat 需要 @string.parse_int，map 不需要额外包
    pkg = PROBE / "lib" / "data" / "moon.pkg"
    if args.mode == "flat":
        pkg.write_text('import {\n  "moonbitlang/core/string",\n}\n', encoding="utf-8")
    else:
        pkg.write_text("", encoding="utf-8")

    gen = run(["python", str(ROOT / "probes" / "gen_mbt.py"), "--mode", args.mode,
               "--langs", args.langs], ROOT, f"{args.label}-00-gen.log")
    print("GEN:", gen["output_tail"])
    manifest = json.loads((ROOT / "probes" / "gen-manifest.json").read_text(encoding="utf-8"))

    record: dict = {
        "label": args.label,
        "mode": args.mode,
        "langs_arg": args.langs,
        "languages": manifest["languages"],
        "entries": manifest["entries"],
        "data_mbt_bytes": manifest["data_mbt_bytes"],
        "test_mbt_bytes": manifest["test_mbt_bytes"],
        "gen_seconds": manifest["gen_seconds"],
        "gen_log": gen["log"],
        "build_runs": [],
        "test_runs": [],
        "timed_out": False,
    }

    # 冷编译 xN：每轮 clean + build
    for i in range(1, args.builds + 1):
        run([str(MOON), "clean"], PROBE, f"{args.label}-01-clean{i}.log")
        r = run([str(MOON), "build", "--target", "native"], PROBE,
                f"{args.label}-02-build{i}.log")
        record["build_runs"].append(r)
        if r["timed_out"]:
            record["timed_out"] = True
            record["timeout_at_build"] = i
            dump(record, args.label)
            return 0

    build_times = [r["wall_seconds"] for r in record["build_runs"]]
    record["build_seconds"] = [min(build_times), max(build_times)]
    record["build_exit_codes"] = [r["exit_code"] for r in record["build_runs"]]

    exe = PROBE / "_build" / "native" / "debug" / "build" / "cmd" / "main" / "main.exe"
    record["exe_bytes"] = exe.stat().st_size if exe.exists() else None
    record["build_dir_bytes"] = dir_size(PROBE / "_build")
    record["build_dir_native_bytes"] = dir_size(PROBE / "_build" / "native")
    record["largest_artifacts"] = largest_files(PROBE / "_build")

    # 运行可执行文件，确认数据真的链接进产物
    if exe.exists():
        run([str(exe)], PROBE, f"{args.label}-04-run.log")

    # 测试：clean 后全量测试，保证不是缓存命中
    run([str(MOON), "clean"], PROBE, f"{args.label}-03-clean-test.log")
    t = run([str(MOON), "test", "--target", "native"], PROBE, f"{args.label}-03-test.log")
    record["test_runs"].append(t)
    if t["timed_out"]:
        record["timed_out"] = True
        record["timeout_at_test"] = True

    dump(record, args.label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
