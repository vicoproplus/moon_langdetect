# -*- coding: utf-8 -*-
"""生成浮点累加的 CPython 3.12 golden（唯一事实来源：真实运行）。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe tools/gen_float_golden.py

产出:
    docs/port/golden/float_add_python.json

输入配方与 probes/rand-probe/cmd/float/main.mbt 完全一致：所有随机数来自
random.Random(0)（MT19937，已被 rand_probe_compare 验证与 MoonBit @rp.Random
逐位一致），调用顺序逐个对应。N = 55，uniform = 1.0 / 55.0。

  A-uniform   200 组：xs[i] = uniform + u*(1.0 - uniform)；Fisher-Yates
              （random.shuffle 语义）打乱。
  B-extreme    50 组：偶数位 1e300，奇数位 1e-300*(1.0+u)；再覆盖
              xs[0]=5e-324, xs[1]=1e300, xs[11]=-1e300, xs[53]=1e-300,
              xs[54]=1e300。
  C-negative   50 组：xs[i] = p*(1e300 - 1e300*u)，p = uniform + u*(1.0-uniform)。
  D-langprob7  7 轮：langprob 初值 uniform；每轮 h[j]=uniform+1e-3*random()，
              langprob[j] = langprob[j] + h[j]/7.0，记录每轮后状态。
  E-stochastic 7 组：alpha = 0.6+0.25*(random()-0.5)；
              w=0.3+0.7*random()；base=alpha*w+(1-alpha)*uniform；
              noise=0.05*(random()-0.5)；probs[j]=(base+noise)*(0.5+random())。

每条累加路径记录两种求和：
  sum_naive   = 显式左到右 `acc = acc + x`（acc 初值 0.0）
  sum_builtin = Python 内建 sum(xs) —— CPython 3.12 起是 Neumaier 补偿求和
                （gh-100425, Modules/builtinmodule.c builtin_sum_impl），
                本脚本另用 Python 复刻的 neumaier_sum 逐位对照，确认两者相等。

所有浮点结果用 struct.pack('>d', x).hex()（大端 16 位十六进制）记录。
"""
from __future__ import annotations

import json
import platform
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "port" / "golden" / "float_add_python.json"

N = 55
UNIFORM = 1.0 / 55.0
SEED = 0


def hexd(x: float) -> str:
    return struct.pack(">d", x).hex()


def shuffle(r: random.Random, xs: list[float]) -> None:
    """CPython 3.12 random.shuffle 的 Fisher-Yates 语义。"""
    for i in reversed(range(1, len(xs))):
        j = r._randbelow(i + 1)
        xs[i], xs[j] = xs[j], xs[i]


def seq_sum(xs: list[float]) -> float:
    """显式左到右顺序累加。"""
    acc = 0.0
    for x in xs:
        acc = acc + x
    return acc


def neumaier_sum(xs: list[float]) -> float:
    """复刻 CPython 3.12 builtin_sum_impl 的浮点快路径（Neumaier 补偿）。"""
    hi = 0.0
    c = 0.0
    for x in xs:
        total = hi + x
        if abs(hi) >= abs(x):
            c += (hi - total) + x
        else:
            c += (x - total) + hi
        hi = total
    return hi + c


def gen_a() -> dict:
    r = random.Random(SEED)
    groups = []
    for _ in range(200):
        xs = [UNIFORM + r.random() * (1.0 - UNIFORM) for _ in range(N)]
        shuffle(r, xs)
        groups.append({"inputs": xs})
    return {"groups": groups}


def gen_b() -> dict:
    r = random.Random(SEED)
    groups = []
    for _ in range(50):
        xs = []
        for i in range(N):
            u = r.random()
            xs.append(1e300 if i % 2 == 0 else 1e-300 * (1.0 + u))
        xs[0] = 5e-324
        xs[1] = 1e300
        xs[11] = -1e300
        xs[53] = 1e-300
        xs[54] = 1e300
        groups.append({"inputs": xs})
    return {"groups": groups}


def gen_c() -> dict:
    r = random.Random(SEED)
    groups = []
    for _ in range(50):
        xs = []
        for _ in range(N):
            u = r.random()
            p = UNIFORM + u * (1.0 - UNIFORM)
            xs.append(p * (1e300 - 1e300 * u))
        groups.append({"inputs": xs})
    return {"groups": groups}


def gen_d() -> dict:
    r = random.Random(SEED)
    langprob = [UNIFORM] * N
    rounds = []
    for _ in range(7):
        h = [UNIFORM + 1e-3 * r.random() for _ in range(N)]
        for j in range(N):
            langprob[j] = langprob[j] + h[j] / 7.0
        rounds.append(list(langprob))
    return {"rounds": rounds}


def gen_e() -> dict:
    r = random.Random(SEED)
    groups = []
    for _ in range(7):
        alpha = 0.6 + 0.25 * (r.random() - 0.5)
        probs = []
        for _ in range(N):
            w = 0.3 + r.random() * 0.7
            base = alpha * w + (1.0 - alpha) * UNIFORM
            noise = 0.05 * (r.random() - 0.5)
            probs.append((base + noise) * (0.5 + r.random()))
        groups.append({"inputs": probs})
    return {"groups": groups}


def build_all() -> dict:
    """返回全部场景的输入（浮点原值），供本脚本与比较脚本复用。"""
    return {
        "A-uniform": gen_a(),
        "B-extreme": gen_b(),
        "C-negative": gen_c(),
        "D-langprob7": gen_d(),
        "E-stochastic": gen_e(),
    }


def sum_semantics(all_scenarios: dict) -> dict:
    """校验 Python 内建 sum(xs) 与两种参考实现的关系。"""
    pairs = 0
    vs_naive_same = 0
    vs_neumaier_same = 0
    first_vs_naive = None
    first_vs_neumaier = None
    for name, sc in all_scenarios.items():
        if "groups" not in sc:
            continue
        for gi, g in enumerate(sc["groups"]):
            xs = g["inputs"]
            b = hexd(sum(xs))
            a = hexd(seq_sum(xs))
            c = hexd(neumaier_sum(xs))
            pairs += 1
            if a == b:
                vs_naive_same += 1
            elif first_vs_naive is None:
                first_vs_naive = {"scenario": name, "group": gi, "builtin": b, "naive": a}
            if c == b:
                vs_neumaier_same += 1
            elif first_vs_neumaier is None:
                first_vs_neumaier = {
                    "scenario": name,
                    "group": gi,
                    "builtin": b,
                    "neumaier": c,
                }
    return {
        "pairs": pairs,
        "builtin_vs_naive_identical": vs_naive_same,
        "builtin_vs_naive_first_mismatch": first_vs_naive,
        "builtin_vs_neumaier_identical": vs_neumaier_same,
        "builtin_vs_neumaier_first_mismatch": first_vs_neumaier,
    }


def to_json(all_scenarios: dict, semantics: dict) -> dict:
    out: dict = {
        "meta": {
            "python": sys.version,
            "platform": platform.platform(),
            "seed": SEED,
            "n": N,
            "uniform_hex": hexd(UNIFORM),
            "recipe": "见 tools/gen_float_golden.py 模块 docstring",
            "hex_format": "struct.pack('>d', x).hex() (big-endian)",
        },
        "sum_semantics": semantics,
        "scenarios": {},
    }
    for name, sc in all_scenarios.items():
        if name == "D-langprob7":
            out["scenarios"][name] = {
                "groups": len(sc["rounds"]),
                "rounds": [[hexd(x) for x in rnd] for rnd in sc["rounds"]],
            }
            continue
        entry = {
            "groups": len(sc["groups"]),
            "inputs": [[hexd(x) for x in g["inputs"]] for g in sc["groups"]],
            "sums_naive": [hexd(seq_sum(g["inputs"])) for g in sc["groups"]],
            "sums_builtin": [hexd(sum(g["inputs"])) for g in sc["groups"]],
            "sums_neumaier": [hexd(neumaier_sum(g["inputs"])) for g in sc["groups"]],
        }
        if name in ("C-negative", "E-stochastic"):
            entry["normalized_builtin"] = [
                [hexd(x / sum(g["inputs"])) for x in g["inputs"]] for g in sc["groups"]
            ]
            entry["normalized_naive"] = [
                [hexd(x / seq_sum(g["inputs"])) for x in g["inputs"]]
                for g in sc["groups"]
            ]
        out["scenarios"][name] = entry
    return out


def main() -> int:
    all_scenarios = build_all()
    semantics = sum_semantics(all_scenarios)
    data = to_json(all_scenarios, semantics)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"python {sys.version.split()[0]}  ->  {OUT.relative_to(ROOT)}")
    for name, sc in data["scenarios"].items():
        if "rounds" in sc:
            print(f"  {name:12s} groups={sc['groups']:4d} states={sc['groups'] * N}")
        else:
            print(
                f"  {name:12s} groups={sc['groups']:4d} sums={sc['groups']}"
                f"{' +normalized' if 'normalized_builtin' in sc else ''}"
            )
    print(
        f"  sum() vs naive loop : pairs={semantics['pairs']} "
        f"identical={semantics['builtin_vs_naive_identical']} "
        f"first_mismatch={semantics['builtin_vs_naive_first_mismatch']}"
    )
    print(
        f"  sum() vs neumaier   : pairs={semantics['pairs']} "
        f"identical={semantics['builtin_vs_neumaier_identical']} "
        f"first_mismatch={semantics['builtin_vs_neumaier_first_mismatch']}"
    )
    for name in ("A-uniform", "B-extreme", "C-negative", "E-stochastic"):
        sc = data["scenarios"][name]
        print(
            f"  sample {name}[0]: naive={sc['sums_naive'][0]} "
            f"builtin={sc['sums_builtin'][0]} neumaier={sc['sums_neumaier'][0]}"
        )
    print(f"  sample D-langprob7 last[0] = {data['scenarios']['D-langprob7']['rounds'][-1][0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
