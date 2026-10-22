# -*- coding: utf-8 -*-
"""辅助测量：alpha 扰动对上游 detect_langs 概率位型的影响阈值。

背景：`gauss` 若差 1 ulp，会让 `alpha = 0.5 + gauss*0.05` 差约 1e-17 量级。
本脚本用真实上游测量「alpha 偏移多少才会改变输出概率的 hex 位型」，
用于判断 1 ulp 差异是否实际影响 detect_langs 结果。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe probes/rand_alpha_sensitivity.py

只读 langdetect/，不修改任何上游文件（仅运行时 monkeypatch）。
"""
from __future__ import annotations

import json
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG_PARENT = ROOT / "langdetect"
CASES = ROOT / "docs" / "port" / "golden" / "cases.jsonl"
OUT = ROOT / "docs" / "port" / "golden" / "rand" / "alpha_sensitivity.json"


def bits(x: float) -> str:
    return struct.pack(">d", x).hex()


def main() -> int:
    if str(PKG_PARENT) not in sys.path:
        sys.path.insert(0, str(PKG_PARENT))
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines()][:20]
    factory = DetectorFactory()
    factory.load_profile(str(PROFILES_DIRECTORY))

    def run(case, delta: float):
        f = DetectorFactory()
        f.langlist = list(factory.langlist)
        f.word_lang_prob_map = factory.word_lang_prob_map
        f.seed = case.get("seed", 0)
        detector = f.create()
        detector.append(case["text"])
        orig = random.Random.gauss

        def gauss(self, *args):
            return orig(self, *args) + delta

        random.Random.gauss = gauss
        try:
            detector._detect_block()
        except Exception:
            return None
        finally:
            random.Random.gauss = orig
        return [bits(p.prob) for p in detector.get_probabilities()]

    deltas = [0.0, 1e-15, 1e-12, 1e-9, 1e-6, 1e-3]
    results = []
    for delta in deltas:
        changed = 0
        total = 0
        for case in cases:
            base = run(case, 0.0)
            if base is None:
                continue
            total += 1
            if run(case, delta) != base:
                changed += 1
        results.append({"delta": delta, "changed_cases": changed, "cases": total})
        print(f"delta={delta:g}  changed={changed}/{total}")

    payload = {
        "generator": "probes/rand_alpha_sensitivity.py",
        "note": (
            "对真实上游 langdetect 的 random.Random.gauss 加常数 delta 后重跑 _detect_block，"
            "比较 detect_langs 概率的 IEEE-754 hex 位型是否变化。仅前 20 个案例。"
        ),
        "case_count": len(cases),
        "results": results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
