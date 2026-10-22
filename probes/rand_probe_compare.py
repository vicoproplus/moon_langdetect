# -*- coding: utf-8 -*-
"""逐阶段比对 CPython 随机数管线 golden 与 MoonBit 探针输出（按 IEEE-754 位型）。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe probes/rand_probe_compare.py

流程:
    1. 调用 `moon build --target native`（cwd = probes/rand-probe）；
    2. 运行 `_build/native/debug/build/cmd/main/main.exe`，解析 stdout；
    3. 读 docs/port/golden/rand/*.json，逐值比较 hex；
    4. 打印逐阶段统计（总对数 / 逐位一致数 / 首个不一致位置及两侧 hex），
       并写 docs/port/golden/rand/compare_report.json。

只读 langdetect/，不修改任何上游文件。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "docs" / "port" / "golden" / "rand"
PROBE = ROOT / "probes" / "rand-probe"
MOON = Path.home() / ".moon" / "bin" / "moon.exe"
EXE = PROBE / "_build" / "native" / "debug" / "build" / "cmd" / "main" / "main.exe"


def build_and_run() -> dict:
    build = subprocess.run(
        [str(MOON), "build", "--target", "native"],
        cwd=PROBE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if build.returncode != 0:
        raise SystemExit("moon build 失败:\n" + build.stdout + build.stderr)
    run = subprocess.run(
        [str(EXE)], cwd=PROBE, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if run.returncode != 0:
        raise SystemExit("探针执行失败:\n" + run.stdout + run.stderr)

    mt: dict[str, list[str]] = {}
    rnd: dict[str, list[str]] = {}
    gb: dict[str, list[dict]] = {}
    rb: dict[str, list[str]] = {}
    gauss: list[str] = []
    gparts: dict[str, dict[str, str]] = {}
    mixg: list[str] = []
    mixc: list[str] = []
    mixa: list[str] = []
    gausss: dict[str, list[str]] = {}
    gaussm: dict[str, list[str]] = {}
    mf: dict[str, dict[str, list[str]]] = {}
    sweep: dict[str, list[list[str]]] = {}
    mixmeta: dict = {}
    for line in run.stdout.splitlines():
        parts = line.split(" ")
        tag = parts[0]
        if tag == "MT":
            mt.setdefault(parts[1], []).append(parts[3][-8:])
        elif tag == "RND":
            rnd.setdefault(parts[1], []).append(parts[3])
        elif tag == "GB":
            gb.setdefault(parts[1], []).append({"hex": parts[3], "dec": parts[4]})
        elif tag == "RB":
            rb.setdefault(parts[1], []).append(parts[3])
        elif tag == "GAUSS":
            gauss.append(parts[2])
        elif tag == "GPART":
            gparts.setdefault(parts[1], {})[parts[2]] = parts[3]
        elif tag == "MIXG":
            mixg.append(parts[2])
        elif tag == "MIXA":
            mixa.append(parts[2])
        elif tag == "MIXC":
            mixc.append(parts[2])
        elif tag == "GAUSSM":
            gaussm.setdefault(parts[1], []).append(parts[3])
        elif tag == "GAUSSS":
            gausss.setdefault(parts[1], []).append(parts[3])
        elif tag == "MF":
            mf.setdefault(parts[1], {}).setdefault(parts[3], []).append(parts[4])
        elif tag == "SW":
            sweep.setdefault(parts[1], []).append(parts[2:])
        elif tag == "MIXMETA":
            mixmeta["ngram_count"] = int(parts[1])
    return {
        "mt": mt,
        "rnd": rnd,
        "gb": gb,
        "rb": rb,
        "gauss": gauss,
        "gparts": gparts,
        "mixg": mixg,
        "mixc": mixc,
        "mixa": mixa,
        "mixmeta": mixmeta,
        "gausss": gausss,
        "gaussm": gaussm,
        "mf": mf,
        "sweep": sweep,
        "stdout_lines": len(run.stdout.splitlines()),
    }


def cmp_series(name: str, py: list[str], mb: list[str], total_expected: int) -> dict:
    n = min(len(py), len(mb))
    same = 0
    first = None
    for i in range(n):
        if py[i] == mb[i]:
            same += 1
        elif first is None:
            first = {"index": i, "python": py[i], "moonbit": mb[i]}
    if first is None and len(py) != len(mb):
        first = {
            "index": n,
            "python": py[n] if n < len(py) else "<missing>",
            "moonbit": mb[n] if n < len(mb) else "<missing>",
        }
    return {
        "stage": name,
        "pairs": n,
        "expected_pairs": total_expected,
        "identical": same,
        "mismatched": n - same,
        "length_python": len(py),
        "length_moonbit": len(mb),
        "first_mismatch": first,
        "all_identical": same == n == len(py) == len(mb),
    }


def sweep_vs_cpython(sweep: dict) -> dict:
    """扫描项：MoonBit 的 @math.ln/cos/sin 与 CPython math 模块逐值比较。

    log 项额外记录 libm `log` 与 @math.ln 的分歧（MoonBit 侧已同时输出两者）。
    """
    import math as pymath

    stages = []
    for kind in ("log", "cos", "sin", "sqrt"):
        rows = sweep.get(kind, [])
        py = []
        mb_moon = []
        mb_libm = []
        for row in rows:
            k = int(row[0])
            x = float.fromhex(row[1]) if "p" in row[1] else None
            if x is None:
                import struct as _struct

                x = _struct.unpack(">d", bytes.fromhex(row[1]))[0]
            if kind == "log":
                py.append(_bits(pymath.log(x)))
                mb_libm.append(row[2])
                mb_moon.append(row[3])
            elif kind == "cos":
                py.append(_bits(pymath.cos(x)))
                mb_moon.append(row[2])
            elif kind == "sin":
                py.append(_bits(pymath.sin(x)))
                mb_moon.append(row[2])
            else:
                py.append(_bits(pymath.sqrt(x)))
                mb_moon.append(row[2])
        if kind == "log":
            stages.append(cmp_series("sweep libm log vs CPython", py, mb_libm, len(py)))
            stages.append(cmp_series("sweep @math.ln vs CPython", py, mb_moon, len(py)))
        else:
            stages.append(cmp_series(f"sweep {kind} vs CPython", py, mb_moon, len(py)))
    return {"stages": stages}


def _bits(x: float) -> str:
    import struct as _struct

    return _struct.pack(">d", x).hex()


def main() -> int:
    mb = build_and_run()
    golden = {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(GOLDEN.glob("*.json"))
        if p.stem != "compare_report"
    }

    stages: list[dict] = []

    # 阶段 1: MT19937 原始 32 位字
    mt = golden["mt19937"]
    for seed in ("0", "42"):
        py = mt["series"][seed]["hex"]
        stages.append(cmp_series(f"MT19937 raw32 seed={seed}", py, mb["mt"].get(seed, []), 64))

    # 阶段 2: random() double
    rd = golden["random_double"]
    for seed in ("0", "42"):
        py = [v["hex"] for v in rd["series"][seed]]
        stages.append(cmp_series(f"random() double seed={seed}", py, mb["rnd"].get(seed, []), 64))

    # 阶段 3: getrandbits(k)
    gb = golden["getrandbits"]
    for k in ("1", "2", "3", "12", "16", "32", "33"):
        py = [v["hex"] for v in gb["series"][k]]
        stages.append(
            cmp_series(f"getrandbits({k})", py, [v["hex"] for v in mb["gb"].get(k, [])], 32)
        )

    # 阶段 4: _randbelow(n)
    rbg = golden["randbelow"]
    for n in ("1", "2", "3", "5", "7", "55", "1000"):
        py = [str(v) for v in rbg["series"][n]]
        stages.append(cmp_series(f"_randbelow({n})", py, mb["rb"].get(n, []), 32))

    # 阶段 5: gauss(0,1)
    ga = golden["gauss"]
    py = [v["hex"] for v in ga["values"]]
    stages.append(cmp_series("gauss(0,1) x64", py, mb["gauss"], 64))

    # 阶段 5b: gauss 内部中间量（定位差异来源）
    gp = golden["gauss_parts"]
    for field in (
        "x2pi",
        "y",
        "ln_arg",
        "ln_result",
        "g2rad",
        "cos_x2pi",
        "sin_x2pi",
        "z",
        "gauss_next",
    ):
        py = [call[field]["hex"] for call in gp["calls"]]
        mbs = [mb["gparts"].get(str(i), {}).get(field, "") for i in range(len(py))]
        stages.append(cmp_series(f"gauss internal {field} x8", py, mbs, len(py)))

    # 阶段 6: 模拟上游混合调用序列
    mx = golden["mixed_sequence"]
    py_g = [v["hex"] for v in mx["gauss_per_round"]]
    stages.append(cmp_series("mixed: gauss per round x7", py_g, mb["mixg"], 7))
    stages.append(
        cmp_series(
            "mixed: alpha=0.5+g*0.05 x7",
            [v["hex"] for v in mx["alpha_per_round"]],
            mb["mixa"],
            7,
        )
    )
    stages.append(
        cmp_series(
            "mixed: choice index x357",
            [str(v) for v in mx["choice_indices"]],
            mb["mixc"],
            357,
        )
    )

    # 阶段 7: 压力序列
    if "gauss_stress" in golden:
        gs = golden["gauss_stress"]
        for seed in sorted(gs["series"], key=int):
            py = [v["hex"] for v in gs["series"][seed]]
            stages.append(
                cmp_series(f"gauss(0,1) x{len(py)} seed={seed}", py, mb["gausss"].get(seed, []), len(py))
            )
    if "gauss_stress" in golden:
        gs = golden["gauss_stress"]
        for seed in sorted(gs["series"], key=int):
            py = [v["hex"] for v in gs["series"][seed]]
            stages.append(
                cmp_series(
                    f"[对照] gauss(@math.ln) x{len(py)} seed={seed}",
                    py,
                    mb["gaussm"].get(seed, []),
                    len(py),
                )
            )
    if "mathfunc" in golden:
        mj = golden["mathfunc"]
        for seed in sorted(mj["series"], key=int):
            for field in ("x2pi", "ln_arg", "log", "cos", "sin"):
                py = [c[field]["hex"] for c in mj["series"][seed]]
                got = mb["mf"].get(seed, {}).get(field, [])
                stages.append(cmp_series(f"mathfunc {field} x{len(py)} seed={seed}", py, got, len(py)))
            py_log = [c["log"]["hex"] for c in mj["series"][seed]]
            got_ln = mb["mf"].get(seed, {}).get("moonmath_ln", [])
            stages.append(
                cmp_series(
                    f"[对照] @math.ln ({len(py_log)}) seed={seed}",
                    py_log,
                    got_ln,
                    len(py_log),
                )
            )

    # 阶段 8: 广域函数扫描（MoonBit 侧 @math 与 libm 自比，CPython 侧另用 math 模块核对）
    sw_report = sweep_vs_cpython(mb["sweep"])
    stages.extend(sw_report["stages"])

    report = {
        "generator": "probes/rand_probe_compare.py",
        "moonbit_stdout_lines": mb["stdout_lines"],
        "moonbit_meta": mb["mixmeta"],
        "python_meta": golden["meta"],
        "stages": stages,
        "all_identical": all(s["all_identical"] for s in stages),
    }
    (GOLDEN / "compare_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print(f"{'stage':44s} {'pairs':>6s} {'same':>6s}  first mismatch")
    print("-" * 110)
    for s in stages:
        fm = s["first_mismatch"]
        detail = ""
        if fm:
            detail = f"#{fm['index']} py={fm['python']} mb={fm['moonbit']}"
        print(f"{s['stage']:44s} {s['pairs']:6d} {s['identical']:6d}  {detail}")
    print("-" * 110)
    ok = sum(1 for s in stages if s["all_identical"])
    print(f"阶段全一致: {ok}/{len(stages)}")
    print("report ->", GOLDEN / "compare_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
