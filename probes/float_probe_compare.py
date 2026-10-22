# -*- coding: utf-8 -*-
"""逐位比对 MoonBit(native) 浮点累加探针与 CPython 3.12 golden。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe probes/float_probe_compare.py

流程:
    1. 用 tools/gen_float_golden.py 的配方在 Python 侧重放全部输入
       （random.Random(0)，与探针同一调用顺序），并读
       docs/port/golden/float_add_python.json 的 golden 结果；
    2. `moon build --target native`（cwd = probes/rand-probe），运行
       _build/native/debug/build/cmd/float/float.exe；
    3. 逐值比较：输入 hex（先证两侧输入相同）、朴素左到右累加、Neumaier 补偿
       累加、prob/sump 归一化、langprob 7 轮状态；
    4. 打印逐场景表，写 docs/port/golden/float_add_compare.json。

只读 langdetect/，不修改任何上游文件。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "probes" / "rand-probe"
MOON = Path.home() / ".moon" / "bin" / "moon.exe"
EXE = PROBE / "_build" / "native" / "debug" / "build" / "cmd" / "float" / "float.exe"
GOLDEN = ROOT / "docs" / "port" / "golden" / "float_add_python.json"
OUT = ROOT / "docs" / "port" / "golden" / "float_add_compare.json"

sys.path.insert(0, str(ROOT / "tools"))
import gen_float_golden as G  # noqa: E402


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

    out = {"in": {}, "r": {}, "rneu": {}, "mixprob": {}, "mixprobsum": {}, "lp": {}}
    for line in run.stdout.splitlines():
        p = line.split(" ")
        tag = p[0]
        if tag == "IN":
            out["in"].setdefault(p[1], []).append(p[3])
        elif tag == "R":
            out["r"].setdefault(p[1], []).append(p[3])
        elif tag == "RNEU":
            out["rneu"].setdefault(p[1], []).append(p[3])
        elif tag == "MIXPROB":
            out["mixprob"].setdefault(p[1], []).append(p[3])
        elif tag == "MIXPROBSUM":
            out["mixprobsum"].setdefault(p[1], []).append(p[3])
        elif tag == "LP":
            out["lp"].setdefault(p[1], []).append(p[3])
    out["lines"] = len(run.stdout.splitlines())
    return out


def cmp_list(py: list[str], mb: list[str]) -> dict:
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
        "pairs": n,
        "identical": same,
        "mismatched": n - same,
        "length_python": len(py),
        "length_moonbit": len(mb),
        "first_mismatch": first,
        "all_identical": same == n == len(py) == len(mb),
    }


def main() -> int:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    inputs = G.build_all()
    mb = build_and_run()

    scenarios: dict[str, dict] = {}
    rows: list[dict] = []

    def add(name: str, kind: str, py: list[str], got: list[str], detail: str) -> None:
        res = cmp_list(py, got)
        res["kind"] = kind
        res["detail"] = detail
        scenarios.setdefault(name, {})[kind] = res
        rows.append(
            {
                "scenario": name,
                "kind": kind,
                "detail": detail,
                "pairs": res["pairs"],
                "identical": res["identical"],
                "first_mismatch": res["first_mismatch"],
                "conclusion": "逐位一致" if res["all_identical"] else "存在差异",
            }
        )

    # 输入位型：证明两侧喂给累加器的数据本身逐位相同。
    for name, sc in inputs.items():
        if name == "D-langprob7":
            continue
        flat = [G.hexd(x) for g in sc["groups"] for x in g["inputs"]]
        add(name, "input", flat, mb["in"].get(name, []), "两侧输入位型")

    # 朴素左到右累加 vs MoonBit。
    for name, sc in inputs.items():
        if name == "D-langprob7":
            continue
        py = [G.hexd(G.seq_sum(g["inputs"])) for g in sc["groups"]]
        add(name, "sum_naive", py, mb["r"].get(name, []), "MoonBit 朴素顺序累加")

    # Neumaier 补偿累加（CPython 3.12 内建 sum 语义）vs MoonBit。
    for name, sc in inputs.items():
        if name == "D-langprob7":
            continue
        py = [G.hexd(G.neumaier_sum(g["inputs"])) for g in sc["groups"]]
        add(name, "sum_neumaier", py, mb["rneu"].get(name, []), "MoonBit Neumaier 累加")

    # 归一化：prob[j]/sump，两种 sump。
    for name in ("C-negative", "E-stochastic"):
        sc = inputs[name]
        py_naive = [G.hexd(x / G.seq_sum(g["inputs"])) for g in sc["groups"] for x in g["inputs"]]
        add(name, "normalized_by_naive", py_naive, mb["mixprob"].get(name, []), "p/sump(naive)")
        py_builtin = [
            G.hexd(x / G.neumaier_sum(g["inputs"])) for g in sc["groups"] for x in g["inputs"]
        ]
        add(
            name,
            "normalized_by_builtin_sum",
            py_builtin,
            mb["mixprobsum"].get(name, []),
            "p/sump(builtin sum)",
        )

    # langprob 7 轮 `+= h/7`。
    lp = inputs["D-langprob7"]["rounds"]
    py_lp = [G.hexd(x) for rnd in lp for x in rnd]
    add("D-langprob7", "langprob_7rounds", py_lp, mb["lp"].get("D-langprob7", []), "7 轮 +=h/7")

    # golden 文件与本次重放输入必须一致（防止工具与探针配方漂移）。
    golden_inputs_ok = True
    for name, sc in golden["scenarios"].items():
        if name == "D-langprob7":
            continue
        flat = [h for g in sc["inputs"] for h in g]
        live = [G.hexd(x) for g in inputs[name]["groups"] for x in g["inputs"]]
        if flat != live:
            golden_inputs_ok = False
    golden_rounds = [h for rnd in golden["scenarios"]["D-langprob7"]["rounds"] for h in rnd]
    golden_rounds_ok = golden_rounds == py_lp

    # sum() 语义结论（来自真实运行）。
    sem = golden["sum_semantics"]
    # 逐场景统计：Python 内建 sum() 与朴素左到右循环不一致的组数，以及
    # 归一化结果因分母不同而不一致的比例。
    sum_vs_loop_stats = {}
    for name, sc in golden["scenarios"].items():
        if "sums_naive" not in sc:
            continue
        diffs = [
            {"group": i, "builtin": b, "naive": a}
            for i, (a, b) in enumerate(zip(sc["sums_naive"], sc["sums_builtin"]))
            if a != b
        ]
        entry = {
            "groups": sc["groups"],
            "sum_builtin_vs_naive_mismatched_groups": len(diffs),
            "first_mismatch": diffs[0] if diffs else None,
        }
        if "normalized_naive" in sc:
            total = sum(len(a) for a in sc["normalized_naive"])
            ndiff = sum(
                1
                for a, b in zip(sc["normalized_naive"], sc["normalized_builtin"])
                for x, y in zip(a, b)
                if x != y
            )
            entry["normalized_values"] = total
            entry["normalized_by_naive_vs_builtin_mismatched"] = ndiff
        sum_vs_loop_stats[name] = entry

    report = {
        "meta": {
            "moonbit_lines": mb["lines"],
            "golden": str(GOLDEN.relative_to(ROOT)),
            "golden_inputs_match_live_replay": golden_inputs_ok,
            "golden_langprob_match_live_replay": golden_rounds_ok,
            "python_sum_semantics": sem,
            "sum_vs_loop_per_scenario": sum_vs_loop_stats,
        },
        "scenarios": scenarios,
        "table": rows,
        "verdict": {
            "all_inputs_identical": all(
                scenarios[n]["input"]["all_identical"] for n in scenarios if "input" in scenarios[n]
            ),
            "all_naive_identical": all(
                scenarios[n]["sum_naive"]["all_identical"]
                for n in scenarios
                if "sum_naive" in scenarios[n]
            ),
            "all_neumaier_identical": all(
                scenarios[n]["sum_neumaier"]["all_identical"]
                for n in scenarios
                if "sum_neumaier" in scenarios[n]
            ),
            "all_normalized_identical": all(
                scenarios[n][k]["all_identical"]
                for n in scenarios
                for k in ("normalized_by_naive", "normalized_by_builtin_sum")
                if k in scenarios[n]
            ),
            "langprob_identical": scenarios["D-langprob7"]["langprob_7rounds"]["all_identical"],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"MoonBit stdout 行数: {mb['lines']}  ->  {OUT.relative_to(ROOT)}")
    print(f"golden 输入与本次重放一致: {golden_inputs_ok}; langprob: {golden_rounds_ok}")
    print()
    header = f"{'scenario':13s} {'kind':24s} {'pairs':>6s} {'identical':>10s}  conclusion"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['scenario']:13s} {row['kind']:24s} {row['pairs']:6d} "
            f"{row['identical']:10d}  {row['conclusion']}"
        )
        if row["first_mismatch"]:
            print(f"    first mismatch: {row['first_mismatch']}")
    print()
    print("Python 内建 sum() 与朴素左到右循环的逐场景差异（真实运行）：")
    for name, st in sum_vs_loop_stats.items():
        extra = ""
        if "normalized_values" in st:
            extra = (
                f"; 归一化 p/sump 因分母不同而不同 "
                f"{st['normalized_by_naive_vs_builtin_mismatched']}/{st['normalized_values']}"
            )
        print(
            f"  {name:13s} groups={st['groups']:4d} "
            f"sum 不一致组数={st['sum_builtin_vs_naive_mismatched_groups']:4d}{extra}"
        )
    print()
    print(
        "Python 内建 sum() vs 朴素左到右: "
        f"{sem['builtin_vs_naive_identical']}/{sem['pairs']} 一致"
    )
    print(
        "Python 内建 sum() vs Neumaier: "
        f"{sem['builtin_vs_neumaier_identical']}/{sem['pairs']} 一致"
    )
    print(f"verdict: {json.dumps(report['verdict'], ensure_ascii=False)}")
    return 0 if all(report["verdict"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
