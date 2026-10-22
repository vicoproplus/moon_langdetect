# -*- coding: utf-8 -*-
"""字符语义对拍：Python `str.isupper()` 全码点 vs MoonBit `@ucd.is_uppercase`。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe probes/char_probe_compare.py

流程:
    1. `moon build --target native`（cwd = probes/char-probe）；
    2. 运行 exe，解析 ISUB 位集行 + SAMPLE + SKIP；
    3. Python 侧对 0..0x10FFFF 全部码点算 `chr(cp).isupper()`（surrogate 区也算，
       MoonBit 侧单独统计跳过数后从总数中扣除）；
    4. 逐点按 hex 位比对（这里用「码点 + 布尔」；不涉及浮点）；
    5. 额外输出：profile 实际用到的 3160 个码点比对、三类抽样字符比对、
       以及 `@ucd.is_uppercase` 与 `is_lowercase/is_alphabetic/to_upper` 组合路径的差异。

只读 langdetect/，不修改其任何文件。

对拍维度（4 条 MoonBit 路径）：
  A. @ucd.is_uppercase                         —— 原生（Unicode 18.0 数据）
  B. to_simple_uppercase 恒等 且 to_simple_lowercase 改变
  C. general_category == Lu
  D. is_uppercase 且不属于 Unicode 15.0 之后新增大写集（补丁表，见 cmd/main/main.mbt）
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "docs" / "port" / "golden"
PROBE = ROOT / "probes" / "char-probe"
MOON = Path.home() / ".moon" / "bin" / "moon.exe"
EXE = PROBE / "_build" / "native" / "debug" / "build" / "cmd" / "main" / "main.exe"

MAX_CP = 0x10FFFF
SURROGATES = range(0xD800, 0xE000)


def build_and_run() -> dict:
    build = subprocess.run(
        [str(MOON), "build", "--target", "native"],
        cwd=PROBE, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if build.returncode != 0:
        raise SystemExit("moon build 失败:\n" + build.stdout + build.stderr)
    run = subprocess.run(
        [str(EXE)], cwd=PROBE, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if run.returncode != 0:
        raise SystemExit("char 探针执行失败:\n" + run.stdout + run.stderr)

    bits: dict[int, int] = {}
    alt: dict[int, int] = {}
    lub: dict[int, int] = {}
    v15: dict[int, int] = {}
    skips: list[int] = []
    samples: list[list[str]] = []
    none_count = None
    for line in run.stdout.splitlines():
        t = line.split(" ")
        if t[0] == "ISUB":
            bits[int(t[1])] = int(t[2], 16)
        elif t[0] == "ALTB":
            alt[int(t[1])] = int(t[2], 16)
        elif t[0] == "LUB":
            lub[int(t[1])] = int(t[2], 16)
        elif t[0] == "V15":
            v15[int(t[1])] = int(t[2], 16)
        elif t[0] == "NONECOUNT":
            none_count = int(t[1])
        elif t[0] == "SKIP":
            skips.append(int(t[1]))
        elif t[0] == "SAMPLE":
            samples.append(t[1:])
    # 跳过清单 = MoonBit 报 SKIP 的码点；另外 int 版 surrogate 区必然全部无法构造，
    # 这里直接对 surrogate 区做整体推断并由 python_counts 统一处理。
    return {"bits": bits, "alt": alt, "lub": lub, "v15": v15, "skips": skips, "samples": samples,
            "none_count": none_count,
            "stdout_lines": len(run.stdout.splitlines())}


def python_counts() -> tuple[int, int]:
    total = 0
    upper = 0
    for cp in range(MAX_CP + 1):
        total += 1
        if chr(cp).isupper():
            upper += 1
    return total, upper


def _mismatch_categories(mismatches) -> dict:
    import unicodedata

    out: dict[str, int] = {}
    for cp, _c, _p, _m in mismatches:
        cat = unicodedata.category(chr(cp))
        out[cat] = out.get(cat, 0) + 1
    return out


def profile_code_points() -> list[int]:
    sys.path.insert(0, str(ROOT / "langdetect"))
    from langdetect.detector_factory import PROFILES_DIRECTORY

    cps: set[int] = set()
    for fn in sorted(Path(PROFILES_DIRECTORY).iterdir()):
        data = json.loads(fn.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "freq" in data:
            for key in data["freq"]:
                for ch in key:
                    cps.add(ord(ch))
    return sorted(cps)


def main() -> int:
    mb = build_and_run()
    GOLDEN.mkdir(parents=True, exist_ok=True)

    total, py_upper = python_counts()
    surrogate_count = len(SURROGATES)

    # MoonBit 侧：surrogate 区全部未在 bits 中计入；先统计 MoonBit 认为 upper 的个数
    mb_upper = sum(bin(v).count("1") for v in mb["bits"].values())

    # 逐 32 位组比对
    mismatches: list[tuple[int, int, bool, bool]] = []
    matched = 0
    groups = 0
    for start in range(0, MAX_CP + 1, 32):
        py_mask = 0
        for i in range(32):
            cp = start + i
            if cp > MAX_CP or cp in SURROGATES:
                continue
            if chr(cp).isupper():
                py_mask |= 1 << i
        groups += 1
        got = mb["bits"].get(start, 0)
        if py_mask == got:
            matched += 1
            continue
        # 定位到具体码点
        for i in range(32):
            cp = start + i
            if cp > MAX_CP or cp in SURROGATES:
                continue
            py_bit = bool(py_mask >> i & 1)
            mb_bit = bool(got >> i & 1)
            if py_bit != mb_bit:
                mismatches.append((cp, cp, py_bit, mb_bit))

    # 替代路径（to_simple_uppercase 恒等 且 to_simple_lowercase 改变）
    alt_mismatch = []
    for start in range(0, MAX_CP + 1, 32):
        py_mask = 0
        for i in range(32):
            cp = start + i
            if cp > MAX_CP or cp in SURROGATES:
                continue
            if chr(cp).isupper():
                py_mask |= 1 << i
        got = mb["alt"].get(start, 0)
        if py_mask != got:
            for i in range(32):
                cp = start + i
                if cp > MAX_CP or cp in SURROGATES:
                    continue
                if bool(py_mask >> i & 1) != bool(got >> i & 1):
                    alt_mismatch.append(
                        {"cp": hex(cp), "python_isupper": int(py_mask >> i & 1),
                         "alt_path": int(got >> i & 1)}
                    )

    # 替代路径 2：general_category == Lu
    lub_mismatch = []
    for start in range(0, MAX_CP + 1, 32):
        py_mask = 0
        for i in range(32):
            cp = start + i
            if cp > MAX_CP or cp in SURROGATES:
                continue
            if chr(cp).isupper():
                py_mask |= 1 << i
        got = mb["lub"].get(start, 0)
        if py_mask != got:
            for i in range(32):
                cp = start + i
                if cp > MAX_CP or cp in SURROGATES:
                    continue
                if bool(py_mask >> i & 1) != bool(got >> i & 1):
                    lub_mismatch.append(
                        {"cp": hex(cp), "python_isupper": int(py_mask >> i & 1),
                         "lu_only": int(got >> i & 1)}
                    )

    # 替代路径 3：is_uppercase 且排除 Unicode 15 之后新增的大写集（补丁表）
    v15_mismatch = []
    for start in range(0, MAX_CP + 1, 32):
        py_mask = 0
        for i in range(32):
            cp = start + i
            if cp > MAX_CP or cp in SURROGATES:
                continue
            if chr(cp).isupper():
                py_mask |= 1 << i
        got = mb["v15"].get(start, 0)
        if py_mask != got:
            for i in range(32):
                cp = start + i
                if cp > MAX_CP or cp in SURROGATES:
                    continue
                if bool(py_mask >> i & 1) != bool(got >> i & 1):
                    v15_mismatch.append(
                        {"cp": hex(cp), "python_isupper": int(py_mask >> i & 1),
                         "v15_masked": int(got >> i & 1)}
                    )

    # profile 用到的码点
    prof_cps = profile_code_points()
    prof_mb = []
    for cp in prof_cps:
        start = cp & ~31
        prof_mb.append(bool(mb["bits"].get(start, 0) >> (cp & 31) & 1))
    prof_py = [chr(cp).isupper() for cp in prof_cps]
    prof_bad = [
        {"cp": hex(cp), "cat": None, "python": p, "moonbit": m}
        for cp, p, m in zip(prof_cps, prof_py, prof_mb) if p != m
    ]

    # 三类抽样字符的 Python 侧真值
    sample_rows = []
    for row in mb["samples"]:
        cp = int(row[0])
        sample_rows.append(
            {
                "cp": hex(cp),
                "moonbit_category": row[1],
                "moonbit_is_uppercase": int(row[2]),
                "python_isupper": int(chr(cp).isupper()),
            }
        )
    sample_bad = [r for r in sample_rows if r["moonbit_is_uppercase"] != r["python_isupper"]]

    report = {
        "generator": "probes/char_probe_compare.py",
        "moonbit_stdout_lines": mb["stdout_lines"],
        "moonbit_skips": [hex(x) for x in mb["skips"]],
        "moonbit_unconstructible_codepoints": mb["none_count"],
        "python": sys.version.split()[0],
        "total_codepoints": total,
        "surrogate_codepoints": surrogate_count,
        "comparable_codepoints": total - surrogate_count,
        "python_isupper_count": py_upper,
        "moonbit_is_uppercase_count": mb_upper,
        "groups_compared": groups,
        "groups_matched": matched,
        "point_mismatch_list_len": len(mismatches),
        "point_mismatches_all": [
            {"cp": hex(cp), "python_isupper": int(p), "moonbit_is_uppercase": int(m)}
            for cp, _c, p, m in mismatches
        ],
        "point_mismatches_first_50": [
            {
                "cp": hex(cp),
                "python_isupper": int(p),
                "moonbit_is_uppercase": int(m),
            }
            for cp, _cp2, p, m in mismatches[:50]
        ],
        "alt_path_mismatch_count": len(alt_mismatch),
        "lu_only_path_mismatch_count": len(lub_mismatch),
        "v15_masked_path_mismatch_count": len(v15_mismatch),
        "v15_masked_path_mismatches_first_50": v15_mismatch[:50],
        "lu_only_path_mismatches_first_50": lub_mismatch[:50],
        "alt_path_mismatches_first_50": alt_mismatch[:50],
        "mismatch_categories_python": _mismatch_categories(mismatches),
        "profile_distinct_codepoints": len(prof_cps),
        "profile_mismatches": prof_bad,
        "profile_mismatch_count": len(prof_bad),
        "sample_rows": sample_rows,
        "sample_mismatch_count": len(sample_bad),
    }
    (GOLDEN / "char_isupper_compare.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print(f"总码点                 : {total}")
    print(f"surrogate 区（跳过）    : {surrogate_count}")
    print(f"可比码点               : {total - surrogate_count}")
    print(f"Python isupper=True    : {py_upper}")
    print(f"MoonBit is_uppercase=T : {mb_upper}")
    print(f"32 位组比对            : {matched}/{groups} 组一致")
    print(f"逐点不一致             : {len(mismatches)} 个码点")
    for cp, _c, p, m in mismatches[:50]:
        print(f"   cp={hex(cp)} python={int(p)} moonbit={int(m)}")
    print(f"替代路径(to_upper==c && to_lower!=c) 不一致: {len(alt_mismatch)}")
    for r in alt_mismatch[:10]:
        print(f"   {r}")
    if alt_mismatch:
        print("   替代路径前 10 个的 Python 视角：")
        for r in alt_mismatch[:10]:
            cp = int(r["cp"], 16)
            print(
                f"     {r['cp']} cat={__import__('unicodedata').category(chr(cp))} "
                f"upper={chr(cp).upper()!r} lower={chr(cp).lower()!r}"
            )
    print(f"不一致码点的 Python 类别分布: {report['mismatch_categories_python']}")
    print(f"替代路径2(仅 general_category==Lu) 不一致: {len(lub_mismatch)}")
    for r in lub_mismatch[:10]:
        print(f"   {r}")
    print(f"替代路径3(is_uppercase + Unicode15 补丁表) 不一致: {len(v15_mismatch)}")
    for r in v15_mismatch[:10]:
        print(f"   {r}")
    print(f"profile 用到码点       : {len(prof_cps)}，不一致 {len(prof_bad)}")
    for r in prof_bad[:50]:
        print(f"   {r}")
    print(f"三类抽样字符           : 不一致 {len(sample_bad)}/{len(sample_rows)}")
    for r in sample_rows:
        print(
            f"   cp={r['cp']} cat={r['moonbit_category']} "
            f"mb={r['moonbit_is_uppercase']} py={r['python_isupper']}"
        )
    print("report ->", GOLDEN / "char_isupper_compare.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
