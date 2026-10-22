# -*- coding: utf-8 -*-
"""低置信入口分组比对器（spec §8.2「低置信入口」行，PRD FR-21/22/23）。

判据
- 输入：``docs/port/golden/expected.json`` 与 ``docs/port/golden/cases.jsonl``
  中的同一批 268 个案例；本脚本按标签选出一个 seed 的 ``short`` / ``long``
  分组（每个标签 55 个，两个 seed 合计 110 个）。
- ``short``：调用诊断 CLI 的 ``confidence`` 模式，必须返回
  ``LowConfidence`` 且 ``char_count < 50``，``char_count`` 等于原文码点数。
- ``long``：必须返回 ``Detected`` 且 ``char_count >= 50``，且返回的主语言
  属于该案例在基准里登记过的候选集合（seed 0 与 seed 42 两条 ``detect_langs``
  的语言并集）。

  为什么用候选集合而不是单个 ``detect``：``detect_with_confidence`` 是
  **不设 seed** 的入口（spec §5.3 / PRD FR-22），其主语言天然带 RNG 抖动。
  上游同样如此——同一条 ``long-zh-tw`` 文本在未设 seed 时实测 30 次里
  26 次 ``zh-tw``、4 次 ``ko``（本 Task 的临时探针，实录见证据日志）。
  基准里的 ``detect`` 是在 seed 0 / 42 下采样得到的，把它当作不设 seed
  入口的唯一真值会得到假红。候选集合在 53/55 条长文本上是单元素
  （仍等价于严格相等），只有 ``long-zh-cn`` / ``long-zh-tw`` 两条是多元素，
  恰是上游本身会抖动的两条。
- 基线案例数由 ``--baseline`` 显式登记（268）；与基准实际计数不符即失败。

路径与可移植性
- 默认基准目录 = 仓库根下的 ``docs/port/golden``；覆盖顺序：
  ``--golden-dir`` > ``$LANGDETECT_GOLDEN_DIR`` > 默认目录。
- 诊断二进制解析复用 ``compare_golden`` 的规则：
  ``--binary`` > ``$LANGDETECT_GOLDEN_BIN`` > ``main.exe`` / ``golden.exe``。
- 脚本内不出现任何机器绝对路径。

退出码
- 0：全部分组判据成立。
- 1：基准内容或产品输出不满足判据。
- 2：参数非法、基准 / 案例 / 诊断二进制缺失或不可执行；``--target`` 非
  ``native``（诊断二进制只能在本机 native 运行，其他目标不冒充）。

用法
    .venv/Scripts/python.exe tools/compare_lowconf.py --short 55 --long 55 --baseline 268
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from compare_golden import (
    BASELINE_MD5,
    DEFAULT_GOLDEN_DIR,
    GOLDEN_DIR_ENV,
    TARGETS,
    CheckFailure,
    Diagnostic,
    SetupError,
    aggregate,
    md5_of,
    resolve_binary,
    resolve_golden_dir,
)

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2

BASELINE_NAME = "expected.json"
CASES_NAME = "cases.jsonl"

SEED_CHOICES = (0, 42)


def load_json_file(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise SetupError(f"cannot read {path}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckFailure(f"{path.name} is not valid UTF-8 JSON: {exc}") from exc


def load_cases_jsonl(path: Path) -> list[dict[str, Any]]:
    """逐行读取 cases.jsonl（只读）；空行跳过。"""
    if not path.is_file():
        raise SetupError(f"{CASES_NAME} not found: {path}")
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise CheckFailure(
                        f"{CASES_NAME}:{line_number} is not valid JSON: {exc}"
                    ) from exc
                if not isinstance(row, dict):
                    raise CheckFailure(
                        f"{CASES_NAME}:{line_number} must be a JSON object"
                    )
                rows.append(row)
    except OSError as exc:
        raise SetupError(f"cannot read {path}: {exc}") from exc
    return rows


def cross_check_cases(
    cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    baseline_count: int,
) -> None:
    """expected.json 与 cases.jsonl 必须描述同一批案例。"""
    if len(cases) != baseline_count:
        raise CheckFailure(
            f"expected.json cases {len(cases)} != --baseline {baseline_count}"
        )
    if len(rows) != baseline_count:
        raise CheckFailure(
            f"cases.jsonl rows {len(rows)} != --baseline {baseline_count}"
        )
    expected_by_id = {case["id"]: case for case in cases}
    if len(expected_by_id) != len(cases):
        raise CheckFailure("expected.json contains duplicate case ids")
    for row in rows:
        case = expected_by_id.get(row.get("id"))
        if case is None:
            raise CheckFailure(f"cases.jsonl id {row.get('id')!r} missing in expected.json")
        if row.get("seed") != case.get("seed"):
            raise CheckFailure(f"case {case['id']}: seed differs between the two files")
        if row.get("text") != case.get("text"):
            raise CheckFailure(f"case {case['id']}: text differs between the two files")
        if row.get("tags") != case.get("tags"):
            raise CheckFailure(f"case {case['id']}: tags differ between the two files")


def select_group(
    cases: list[dict[str, Any]],
    tag: str,
    seed: int,
    expected_count: int,
) -> list[dict[str, Any]]:
    selected = [
        case
        for case in cases
        if case["seed"] == seed and tag in case.get("tags", [])
    ]
    if len(selected) != expected_count:
        raise CheckFailure(
            f"tag {tag!r} seed {seed}: selected {len(selected)} cases, "
            f"expected --{tag} {expected_count}"
        )
    return selected


def build_candidates(cases: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Map every case id to the language codes the baseline recorded for it.

    The union of the seed-0 and seed-42 `detect_langs` lists, because the
    low-confidence entry point runs unseeded (spec §5.3) and its winning
    language therefore varies with the RNG draw. A case whose union holds a
    single code is compared strictly; only genuinely ambiguous cases (the
    upstream `zh-cn` / `zh-tw` versus `ko` pair) get a multi-element set.
    """
    candidates: dict[str, set[str]] = {}
    for case in cases:
        # The seed-42 twin of a case carries the "@seed42" id suffix; both
        # twins describe the same text, so they share one candidate set.
        base_id = case["id"].removesuffix("@seed42")
        langs = candidates.setdefault(base_id, set())
        for entry in case.get("detect_langs") or []:
            lang = entry.get("lang")
            if isinstance(lang, str):
                langs.add(lang)
    return candidates


def run(ctx: argparse.Namespace, golden_dir: Path, binary: Path) -> int:
    baseline_path = golden_dir / BASELINE_NAME
    cases_path = golden_dir / CASES_NAME
    if not baseline_path.is_file():
        raise SetupError(f"{BASELINE_NAME} not found in golden dir: {golden_dir}")

    digest = md5_of(baseline_path)
    if digest != BASELINE_MD5:
        raise CheckFailure(
            f"{BASELINE_NAME} md5 {digest} != registered baseline {BASELINE_MD5} "
            "(baseline is read-only)"
        )

    document = load_json_file(baseline_path)
    if not isinstance(document, dict) or not isinstance(document.get("cases"), list):
        raise CheckFailure("expected.json must contain a 'cases' array")
    cases = document["cases"]
    rows = load_cases_jsonl(cases_path)
    cross_check_cases(cases, rows, ctx.baseline)

    short_cases = select_group(cases, "short", ctx.seed, ctx.short)
    long_cases = select_group(cases, "long", ctx.seed, ctx.long)
    candidates = build_candidates(cases)

    diagnostic = Diagnostic(binary, ctx.timeout)
    failures: list[str] = []
    short_ok = 0
    long_ok = 0

    for case in short_cases:
        result = diagnostic.run({"mode": "confidence", "text": case["text"]})
        if "error" in result:
            failures.append(f"{case['id']}: unexpected error {result['error']}")
            continue
        char_count = result.get("char_count")
        if result.get("confidence") != "low":
            failures.append(
                f"{case['id']}: expected LowConfidence, observed "
                f"{result.get('confidence')!r}"
            )
        elif not isinstance(char_count, int) or char_count >= 50:
            failures.append(f"{case['id']}: char_count {char_count!r} is not < 50")
        elif char_count != len(case["text"]):
            failures.append(
                f"{case['id']}: char_count {char_count} != text codepoints "
                f"{len(case['text'])}"
            )
        else:
            short_ok += 1

    for case in long_cases:
        result = diagnostic.run({"mode": "confidence", "text": case["text"]})
        if "error" in result:
            failures.append(f"{case['id']}: unexpected error {result['error']}")
            continue
        char_count = result.get("char_count")
        langs = result.get("langs")
        if result.get("confidence") != "detected":
            failures.append(
                f"{case['id']}: expected Detected, observed "
                f"{result.get('confidence')!r}"
            )
            continue
        if not isinstance(char_count, int) or char_count < 50:
            failures.append(f"{case['id']}: char_count {char_count!r} is not >= 50")
            continue
        if char_count != len(case["text"]):
            failures.append(
                f"{case['id']}: char_count {char_count} != text codepoints "
                f"{len(case['text'])}"
            )
            continue
        if not isinstance(langs, list) or not langs:
            failures.append(f"{case['id']}: Detected without language entries")
            continue
        top = langs[0].get("lang") if isinstance(langs[0], dict) else None
        candidates_for_case = candidates.get(case["id"].removesuffix("@seed42"), set())
        if top not in candidates_for_case:
            failures.append(
                f"{case['id']}: top lang {top!r} not in the golden candidate set "
                f"{sorted(candidates_for_case)!r} (detect {case.get('detect')!r})"
            )
            continue
        if len(candidates_for_case) == 1 and top != case.get("detect"):
            failures.append(
                f"{case['id']}: top lang {top!r} != detect {case.get('detect')!r}"
            )
            continue
        long_ok += 1

    if failures:
        raise CheckFailure(aggregate(failures))
    print(
        f"ok lowconf seed={ctx.seed} "
        f"short={short_ok}/{len(short_cases)} (<50 LowConfidence), "
        f"long={long_ok}/{len(long_cases)} (>=50 Detected, top in golden candidates), "
        f"baseline={ctx.baseline}"
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compare_lowconf.py",
        allow_abbrev=False,
        description=(
            "Compare the low-confidence entry point against grouped golden cases "
            "(short < 50 codepoints -> LowConfidence; long >= 50 -> Detected)."
        ),
        epilog=(
            "Golden dir resolution (first match wins):\n"
            "  1. --golden-dir\n"
            f"  2. ${GOLDEN_DIR_ENV}\n"
            "  3. <repo-root>/docs/port/golden   (repo root = parent of this script's dir)\n"
            "\n"
            "Diagnostic binary resolution (first match wins):\n"
            "  1. --binary\n"
            "  2. $LANGDETECT_GOLDEN_BIN\n"
            "  3. _build/native/debug/build/src/core/cmd/golden/main.exe\n"
            "  4. _build/native/debug/build/src/core/cmd/golden/golden.exe\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--short",
        type=int,
        default=55,
        metavar="N",
        help="expected number of short cases for the selected seed (default: 55)",
    )
    parser.add_argument(
        "--long",
        type=int,
        default=55,
        metavar="N",
        help="expected number of long cases for the selected seed (default: 55)",
    )
    parser.add_argument(
        "--baseline",
        type=int,
        default=268,
        metavar="N",
        help="expected baseline case count (default: 268)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        choices=SEED_CHOICES,
        default=0,
        help="seed group to select (default: 0; counts are per seed)",
    )
    parser.add_argument(
        "--target",
        choices=TARGETS,
        default="native",
        help="target runtime (default: native)",
    )
    parser.add_argument(
        "--golden-dir",
        default=None,
        metavar="PATH",
        help=f"golden baseline directory (default: {DEFAULT_GOLDEN_DIR})",
    )
    parser.add_argument(
        "--binary",
        default=None,
        metavar="PATH",
        help="diagnostic CLI executable (default: main.exe, falling back to golden.exe)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        metavar="SECONDS",
        help="per-invocation timeout (default: 120)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    golden_dir, source = resolve_golden_dir(args.golden_dir)
    if not golden_dir.is_dir():
        print(
            f"error: golden dir does not exist or is not a directory: "
            f"{golden_dir} (source: {source})",
            file=sys.stderr,
        )
        return EXIT_USAGE
    if args.target != "native":
        print(
            f"error: lowconf: target {args.target!r} is not executable in this "
            "environment (only native is available)",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        binary = resolve_binary(args.binary)
        return run(args, golden_dir, binary)
    except SetupError as exc:
        print(f"error: lowconf: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except CheckFailure as exc:
        print(f"lowconf FAILED: {exc}", file=sys.stderr)
        return EXIT_CHECK_FAILED


if __name__ == "__main__":
    sys.exit(main())
