# -*- coding: utf-8 -*-
"""生成 CPython 随机数管线的 golden 数据（移植可行性取证用）。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe tools/gen_rand_golden.py

产出:
    docs/port/golden/rand/mt19937.json
    docs/port/golden/rand/random_double.json
    docs/port/golden/rand/getrandbits.json
    docs/port/golden/rand/randbelow.json
    docs/port/golden/rand/gauss.json
    docs/port/golden/rand/gauss_parts.json
    docs/port/golden/rand/mixed_sequence.json
    docs/port/golden/rand/meta.json

约束:
    - 只读 langdetect/，不修改其任何文件（混合序列用运行时 monkeypatch 观测调用顺序）。
    - 所有浮点同时给 struct.pack('>d', x).hex() 与 repr，规避文本精度问题。
"""
from __future__ import annotations

import json
import math
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "port" / "golden" / "rand"
PKG_PARENT = ROOT / "langdetect"


def bits(x: float) -> str:
    return struct.pack(">d", x).hex()


def dbl(x: float) -> dict:
    return {"hex": bits(x), "repr": repr(x)}


def getrandbits_series(k: int, count: int) -> list:
    r = random.Random(0)
    return [r.getrandbits(k) for _ in range(count)]


def randbelow_series(n: int, count: int) -> list:
    r = random.Random(0)
    return [r._randbelow_with_getrandbits(n) for _ in range(count)]


def mt_words(seed: int, count: int) -> list:
    r = random.Random(seed)
    return [r.getrandbits(32) for _ in range(count)]


def random_doubles(seed: int, count: int) -> list:
    r = random.Random(seed)
    return [r.random() for _ in range(count)]


def gauss_series(seed: int, count: int) -> list:
    r = random.Random(seed)
    return [r.gauss(0.0, 1.0) for _ in range(count)]


def gauss_parts(seed: int, count: int) -> list:
    """复刻 random.gauss 内部每一步，便于把差异定位到具体 libm 调用。"""
    r = random.Random(seed)
    out = []
    for _ in range(count):
        x2pi = r.random() * math.tau
        y = r.random()
        lnarg = 1.0 - y
        lnres = math.log(lnarg)
        g2rad = math.sqrt(-2.0 * lnres)
        c = math.cos(x2pi)
        s = math.sin(x2pi)
        z = c * g2rad
        out.append(
            {
                "x2pi": dbl(x2pi),
                "y": dbl(y),
                "ln_arg": dbl(lnarg),
                "ln_result": dbl(lnres),
                "g2rad": dbl(g2rad),
                "cos_x2pi": dbl(c),
                "sin_x2pi": dbl(s),
                "z": dbl(z),
                "gauss_next": dbl(s * g2rad),
            }
        )
    return out


STRESS_SEEDS = (0, 1, 42, 12345)
STRESS_GAUSS = 512
STRESS_MATH = 256


def gauss_stress(seed: int, count: int) -> list:
    r = random.Random(seed)
    return [dbl(r.gauss(0.0, 1.0)) for _ in range(count)]


def math_stress(seed: int, count: int) -> list:
    """按 gauss 内部相同的取值顺序，记录 log/cos/sin 的输入与输出。"""
    r = random.Random(seed)
    out = []
    for _ in range(count):
        x2pi = r.random() * math.tau
        y = r.random()
        ln_arg = 1.0 - y
        out.append(
            {
                "x2pi": dbl(x2pi),
                "ln_arg": dbl(ln_arg),
                "log": dbl(math.log(ln_arg)),
                "cos": dbl(math.cos(x2pi)),
                "sin": dbl(math.sin(x2pi)),
            }
        )
    return out


def upstream_mixed_sequence(seed: int):
    """用真实上游 langdetect 观测 seed 固定时的随机调用顺序与 ngrams 长度。

    通过 monkeypatch random.Random._randbelow / gauss 记录调用顺序（不改源码文件）。
    注意：不能 patch `choice`——上游 `choice(seq)` 内部调用 `self._randbelow(len(seq))`，
    只观测 `_randbelow` 才能拿到真实的下标调用序列。
    """
    if str(PKG_PARENT) not in sys.path:
        sys.path.insert(0, str(PKG_PARENT))
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    factory = DetectorFactory()
    factory.load_profile(str(PROFILES_DIRECTORY))
    factory.seed = seed
    detector = factory.create()

    case = None
    with open(ROOT / "docs" / "port" / "golden" / "cases.jsonl", encoding="utf-8") as fh:
        for line in fh:
            c = json.loads(line)
            if c["id"] == "long-af":
                case = c
                break
    detector.append(case["text"])
    detector.cleaning_text()
    ngrams = detector._extract_ngrams()

    counts: list[int] = []
    gauss_vals: list[float] = []
    indices: list[int] = []
    cursor = {"n": 0}
    orig_randbelow = random.Random._randbelow
    orig_gauss = random.Random.gauss

    def randbelow(self, n):
        picked = orig_randbelow(self, n)
        indices.append(picked)
        cursor["n"] += 1
        return picked

    def gauss(self, *args):
        val = orig_gauss(self, *args)
        gauss_vals.append(val)
        counts.append(cursor["n"])
        cursor["n"] = 0
        return val

    random.Random._randbelow = randbelow
    random.Random.gauss = gauss
    try:
        detector._detect_block()
    finally:
        random.Random._randbelow = orig_randbelow
        random.Random.gauss = orig_gauss
    tail = cursor["n"]
    # 上游循环：每轮先 1 次 gauss，再接若干次 choice。
    # gauss 第 i 次之前，choice 次数即「第 i-1 轮」的尾量（第 0 轮前为 0）。
    per_round = counts[1:] + [tail]
    assert len(per_round) == 7, per_round
    assert len(gauss_vals) == 7, gauss_vals
    assert sum(per_round) == len(indices), (per_round, len(indices))
    return {
        "case_id": case["id"],
        "text_sha256": case["text_sha256"],
        "ngram_count": len(ngrams),
        "choice_counts_per_round": per_round,
        "gauss_per_round": gauss_vals,
        "choice_indices": indices,
    }


def simulated_mixed_sequence(seed: int, ngram_count: int, counts: list[int]) -> dict:
    """纯 random.Random(seed) 重放同一调用顺序，验证「调用顺序即契约」。

    顺序与上游一致：每轮先 1 次 `gauss(0,1)`，再 `counts[轮]` 次
    `_randbelow(ngram_count)`（等价于上游的 `choice(ngrams)`）。
    注意：上游 `choice` 内部即 `self._randbelow(len(seq))`，两者均编译为
    `_randbelow_with_getrandbits`，故此处逐值必须相等。
    """
    r = random.Random(seed)
    gauss_vals = []
    indices = []
    for c in counts:
        gauss_vals.append(r.gauss(0.0, 1.0))
        for _ in range(c):
            indices.append(r._randbelow_with_getrandbits(ngram_count))
    return {
        "gauss_per_round": gauss_vals,
        "choice_indices": indices,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mt = {
        "generator": "tools/gen_rand_golden.py",
        "note": "前 64 个 32 位原始 MT19937 输出（经 getrandbits(32)，即未做任何位裁剪）",
        "series": {
            str(seed): {
                "decimal": mt_words(seed, 64),
                "hex": [format(w, "08x") for w in mt_words(seed, 64)],
            }
            for seed in (0, 42)
        },
    }
    (OUT_DIR / "mt19937.json").write_text(
        json.dumps(mt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    rd = {
        "generator": "tools/gen_rand_golden.py",
        "note": "random.Random(seed).random() 前 64 个 double",
        "series": {
            str(seed): [dbl(x) for x in random_doubles(seed, 64)] for seed in (0, 42)
        },
    }
    (OUT_DIR / "random_double.json").write_text(
        json.dumps(rd, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    ks = [1, 2, 3, 12, 16, 32, 33]
    gb = {
        "generator": "tools/gen_rand_golden.py",
        "note": "每个 k 使用全新的 random.Random(0)，前 32 个 getrandbits(k)",
        "series": {
            str(k): [{"dec": str(v), "hex": format(v, "016x")} for v in getrandbits_series(k, 32)]
            for k in ks
        },
    }
    (OUT_DIR / "getrandbits.json").write_text(
        json.dumps(gb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    ns = [1, 2, 3, 5, 7, 55, 1000]
    rb = {
        "generator": "tools/gen_rand_golden.py",
        "note": "每个 n 使用全新的 random.Random(0)，前 32 个 _randbelow(n)",
        "series": {str(n): [str(v) for v in randbelow_series(n, 32)] for n in ns},
    }
    (OUT_DIR / "randbelow.json").write_text(
        json.dumps(rb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    ga = {
        "generator": "tools/gen_rand_golden.py",
        "note": "random.Random(0).gauss(0,1) 前 64 个值（含 gauss_next 缓存语义）",
        "values": [dbl(x) for x in gauss_series(0, 64)],
    }
    (OUT_DIR / "gauss.json").write_text(
        json.dumps(ga, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    gp = {
        "generator": "tools/gen_rand_golden.py",
        "note": "random.Random(0) 前 8 次 gauss 的内部中间量，用于把差异定位到 sqrt/log/cos/sin",
        "calls": gauss_parts(0, 8),
    }
    (OUT_DIR / "gauss_parts.json").write_text(
        json.dumps(gp, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    obs = upstream_mixed_sequence(0)
    sim = simulated_mixed_sequence(0, obs["ngram_count"], obs["choice_counts_per_round"])
    assert obs["gauss_per_round"] == sim["gauss_per_round"], "gauss 序列与上游不一致"
    assert obs["choice_indices"] == sim["choice_indices"], "choice 序列与上游不一致"
    mixed = {
        "generator": "tools/gen_rand_golden.py",
        "note": (
            "seed=0，上游 long-af 案例真实调用顺序：每轮 1 次 gauss(0,1) + "
            "choice(ngrams) 若干次（choice 内部为 _randbelow(len(ngrams))）。"
            "已用真实上游 monkeypatch 观测，且与纯 random.Random(0) 重放逐值相等。"
        ),
        "seed": 0,
        "case_id": obs["case_id"],
        "text_sha256": obs["text_sha256"],
        "ngram_count": obs["ngram_count"],
        "choice_counts_per_round": obs["choice_counts_per_round"],
        "gauss_per_round": [dbl(x) for x in sim["gauss_per_round"]],
        "alpha_per_round": [dbl(0.5 + x * 0.05) for x in sim["gauss_per_round"]],
        "choice_indices": sim["choice_indices"],
        "upstream_observed_gauss_matches_replay": True,
        "upstream_observed_choice_matches_replay": True,
    }
    (OUT_DIR / "mixed_sequence.json").write_text(
        json.dumps(mixed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    stress = {
        "generator": "tools/gen_rand_golden.py",
        "note": "gauss(0,1) 长序列压力测试：每 seed 512 个值，按 hex 逐位比较",
        "count_per_seed": STRESS_GAUSS,
        "series": {str(s): gauss_stress(s, STRESS_GAUSS) for s in STRESS_SEEDS},
    }
    (OUT_DIR / "gauss_stress.json").write_text(
        json.dumps(stress, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    mathf = {
        "generator": "tools/gen_rand_golden.py",
        "note": (
            "按 gauss 内部取值顺序采样 log/cos/sin 的输入输出（每 seed 256 个），"
            "用于判断 MoonBit 数学函数与 CPython 所用 libm 是否逐位一致"
        ),
        "count_per_seed": STRESS_MATH,
        "series": {str(s): math_stress(s, STRESS_MATH) for s in STRESS_SEEDS},
    }
    (OUT_DIR / "mathfunc.json").write_text(
        json.dumps(mathf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    meta = {
        "generator": "tools/gen_rand_golden.py",
        "python": sys.version.split()[0],
        "python_exe": sys.executable,
        "random_module": random.__file__,
        "math_tau_hex": bits(math.tau),
        "math_pi_hex": bits(math.pi),
        "random_random_impl": "Modules/_randommodule.c: (a*67108864.0+b)*(1.0/9007199254740992.0)",
        "gauss_impl": "Lib/random.py: x2pi=random()*tau; g2rad=sqrt(-2*log(1-random())); cos/sin",
    }
    (OUT_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    print("mixed counts:", obs["choice_counts_per_round"], "ngram_count:", obs["ngram_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
