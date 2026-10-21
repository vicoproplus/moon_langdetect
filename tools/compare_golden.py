# -*- coding: utf-8 -*-
"""golden 基准比对脚本（Task 2 交付面：仅 ``--self-check``）。

契约来源
- `约定 C：golden 基准消费契约` §2（C1-C6）/ §3（C-C1…C-C6 门禁命令）/ §4（分档）。
- spec §8.2 / §8.4（维度二 / 维度四的比对入口）与 §10.6 命令 15-19。

交付分期（B-08 裁决）
- 本文件当前只实现 ``--self-check``：校验基准自身的完整性。
- ``prob_bits`` / ``seed_semantics`` / ``failures`` / ``forensics`` / ``cleaning`` /
  ``features_cache`` / ``profile_counts`` / ``repeatability`` / ``top1`` /
  ``lang_list_len`` / ``entry_total`` / ``prob_tolerance`` 十二个产品比对模式
  留待 Task 10 交付；在此之前它们打印 ``mode not implemented`` 并以退出码 3
  结束，**不得**静默返回 0。

``--self-check`` 的判据（逐条对应约定 C）
- C2：`cases` 计数三元组 = (268, 250, 18)，即 268 = 250（有 ``detect_langs``）+ 18（有 ``error``）。
- C3：`cases[*].seed` 集合 = {0, 42}。
- C1/C5：每条 ``detect_langs[*].prob_bits`` 匹配 ``^[0-9a-f]{16}$``（IEEE754 双精度大端 hex）。
- C4：异常案例 ``error.code`` 集合 = {5}。
- C6：``expected.json`` 的 md5 等于登记的基准摘要 ``BASELINE_MD5``（基准只读）。
- 结构：顶层 ``cases`` / ``meta`` / ``repeatability`` / ``seed_diff`` / ``unseeded_runs``
  齐备且容器类型分别为 list / dict / list / list / list。

md5 先于结构校验执行：摘要不符即判「基准被改，应回滚而非改期望值」（C6）；
结构校验把 C1-C6 的语义契约写成独立判据，登记新基准摘要后仍然生效。

路径与可移植性
- 默认基准目录 = 本脚本所在目录的上一级（仓库根）下的 ``docs/port/golden``；
  脚本内不出现任何机器绝对路径。
- 覆盖顺序：``--golden-dir`` > 环境变量 ``LANGDETECT_GOLDEN_DIR`` > 默认目录。
- 相对路径按当前工作目录解析。
- 当前只登记一个基准摘要（``docs/port/golden``，约定 C §3 记录）。``--golden-dir``
  指向内容相同的副本仍可通过；指向内容不同的基准则以退出码 1 拒绝——登记第二个
  基准摘要属于 Task 10 的扩展面。

只读承诺（C6）
- 脚本只以只读方式打开基准文件，不写入、不改名、不删除任何文件。

退出码
- 0：模式执行成功（``--self-check`` 输出 ``ok 268=250+18``）。
- 1：基准内容不满足契约（md5 / 结构 / 计数 / seed / prob_bits / 异常码）。
- 2：参数非法、基准目录不存在、``expected.json`` 缺失或不可读。
- 3：产品比对模式尚未实现（Task 10）。

用法
    .venv/Scripts/python.exe tools/compare_golden.py --self-check
    .venv/Scripts/python.exe tools/compare_golden.py --mode self-check
    LANGDETECT_GOLDEN_DIR=<dir> .venv/Scripts/python.exe tools/compare_golden.py --self-check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

# --------------------------------------------------------------------------- #
# 常量：路径（无机器绝对路径）
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOLDEN_DIR = ROOT / "docs" / "port" / "golden"
GOLDEN_DIR_ENV = "LANGDETECT_GOLDEN_DIR"

# --------------------------------------------------------------------------- #
# 常量：约定 C 判据
# --------------------------------------------------------------------------- #

BASELINE_NAME = "expected.json"
# 约定 C §3 实测记录 / spec §10.3 C-C6：docs/port/golden/expected.json
BASELINE_MD5 = "219519ee19d7cc10d404ddbdab3acd87"
# 约定 C C2：(案例总数, 有概率输出, 抛异常)
EXPECTED_CASE_COUNTS = (268, 250, 18)
# 约定 C C3
EXPECTED_SEEDS = (0, 42)
# 约定 C C4
EXPECTED_ERROR_CODES = frozenset({5})
# 约定 C C1 / C5（fullmatch，等价于门禁命令里的 re.fullmatch）
PROB_BITS_RE = re.compile(r"[0-9a-f]{16}")
# 顶层结构：(键名, 期望容器类型)
TOP_LEVEL_TYPES = (
    ("cases", list),
    ("meta", dict),
    ("repeatability", list),
    ("seed_diff", list),
    ("unseeded_runs", list),
)

# --------------------------------------------------------------------------- #
# 常量：CLI 与退出码
# --------------------------------------------------------------------------- #

TARGETS = ("native", "js", "wasm-gc", "native-other")
SEED_CHOICES = (0, 42)
MODE_SELF_CHECK = "self-check"
# 十二个产品比对模式：Task 10 交付；在此之前统一 exit 3。
PRODUCT_MODES = (
    "prob_bits",
    "seed_semantics",
    "failures",
    "forensics",
    "cleaning",
    "features_cache",
    "profile_counts",
    "repeatability",
    "top1",
    "lang_list_len",
    "entry_total",
    "prob_tolerance",
)
MODE_NAMES = (MODE_SELF_CHECK,) + PRODUCT_MODES

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2
EXIT_NOT_IMPLEMENTED = 3  # 产品模式占位 exit 3；Task 10 交付真实实现时删除

# --------------------------------------------------------------------------- #
# 异常：区分「环境/参数问题」(exit 2) 与「基准内容违约」(exit 1)
# --------------------------------------------------------------------------- #


class SetupError(Exception):
    """路径缺失、文件不可读等环境问题 → exit 2。"""


class CheckFailure(Exception):
    """基准内容不满足约定 C 的判据 → exit 1。"""


# --------------------------------------------------------------------------- #
# 运行上下文与模式派发（Task 10 在此扩展产品模式）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Context:
    """一次运行的不可变上下文。"""

    mode: str
    target: str
    seed: int | None
    golden_dir: Path

    @property
    def baseline_path(self) -> Path:
        return self.golden_dir / BASELINE_NAME


Handler = Callable[[Context], int]


# --------------------------------------------------------------------------- #
# 只读 IO 辅助
# --------------------------------------------------------------------------- #


def md5_of(path: Path) -> str:
    """按块读取计算 md5（只读）。"""
    digest = hashlib.md5()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SetupError(f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    """只读解析 JSON；编码错误/语法错误视为基准内容违约。"""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise SetupError(f"cannot read {path}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckFailure(f"{path.name} is not valid UTF-8 JSON: {exc}") from exc


# --------------------------------------------------------------------------- #
# 自检判据（逐条对应约定 C）
# --------------------------------------------------------------------------- #


def check_top_level(document: Any) -> dict[str, Any]:
    """五个顶层结构齐备且容器类型正确。"""
    if not isinstance(document, dict):
        raise CheckFailure(
            f"top level must be a JSON object, got {type(document).__name__}"
        )
    for key, expected_type in TOP_LEVEL_TYPES:
        if key not in document:
            raise CheckFailure(f"missing top-level key: {key}")
        value = document[key]
        if not isinstance(value, expected_type):
            raise CheckFailure(
                f"top-level {key!r} must be {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
    return document


def check_case_counts(cases: list[Any]) -> tuple[int, int]:
    """C2：268 = 250 + 18。返回 (有概率输出数, 抛异常数)。"""
    for case in cases:
        if not isinstance(case, dict):
            raise CheckFailure(
                f"cases entries must be JSON objects, got {type(case).__name__}"
            )
    total = len(cases)
    with_prob = 0
    with_error = 0
    for case in cases:
        if case.get("detect_langs"):
            with_prob += 1
        if "error" in case:
            with_error += 1
    observed = (total, with_prob, with_error)
    if observed != EXPECTED_CASE_COUNTS:
        raise CheckFailure(
            "case counts %d=%d+%d != %d=%d+%d (convention C C2)"
            % (total, with_prob, with_error, *EXPECTED_CASE_COUNTS)
        )
    return with_prob, with_error


def check_seeds(cases: list[Any]) -> None:
    """C3：seed 集合 = {0, 42}，且每个案例都带整型 seed。"""
    for case in cases:
        if "seed" not in case:
            raise CheckFailure(f"case {case.get('id')!r}: missing 'seed'")
        seed = case["seed"]
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise CheckFailure(
                f"case {case.get('id')!r}: seed must be int, got {type(seed).__name__}"
            )
    observed = sorted({case["seed"] for case in cases})
    if tuple(observed) != EXPECTED_SEEDS:
        raise CheckFailure(
            f"seed set {observed} != {list(EXPECTED_SEEDS)} (convention C C3)"
        )


def check_prob_bits(cases: list[Any]) -> int:
    """C1/C5：每条 prob_bits 为 16 位小写 hex。返回条目总数。"""
    entries = 0
    for case in cases:
        langs = case.get("detect_langs") or []
        if not isinstance(langs, list):
            raise CheckFailure(
                f"case {case.get('id')!r}: detect_langs must be a list, "
                f"got {type(langs).__name__}"
            )
        for index, entry in enumerate(langs):
            if not isinstance(entry, dict):
                raise CheckFailure(
                    f"case {case.get('id')!r} entry {index}: must be a JSON object"
                )
            bits = entry.get("prob_bits")
            if not isinstance(bits, str) or PROB_BITS_RE.fullmatch(bits) is None:
                raise CheckFailure(
                    f"case {case.get('id')!r} entry {index}: prob_bits {bits!r} "
                    "is not 16 lowercase hex (convention C C1/C5)"
                )
            entries += 1
    return entries


def check_error_codes(cases: list[Any]) -> None:
    """C4：异常案例的 error.code 集合 = {5}。"""
    codes: set[int] = set()
    for case in cases:
        if "error" not in case:
            continue
        error = case["error"]
        if not isinstance(error, dict) or "code" not in error:
            raise CheckFailure(
                f"case {case.get('id')!r}: 'error' must be an object with 'code'"
            )
        code = error["code"]
        if isinstance(code, bool) or not isinstance(code, int):
            raise CheckFailure(
                f"case {case.get('id')!r}: error.code must be int, "
                f"got {type(code).__name__}"
            )
        codes.add(code)
    if codes != EXPECTED_ERROR_CODES:
        raise CheckFailure(
            f"error codes {sorted(codes)} != {sorted(EXPECTED_ERROR_CODES)} "
            "(convention C C4)"
        )


# --------------------------------------------------------------------------- #
# 模式实现
# --------------------------------------------------------------------------- #


def run_self_check(ctx: Context) -> int:
    """--self-check：校验基准自身完整性（C1-C6 + 顶层结构）。"""
    path = ctx.baseline_path
    if not path.is_file():
        raise SetupError(f"{BASELINE_NAME} not found in golden dir: {ctx.golden_dir}")

    digest = md5_of(path)
    if digest != BASELINE_MD5:
        raise CheckFailure(
            f"{BASELINE_NAME} md5 {digest} != registered baseline {BASELINE_MD5} "
            "(convention C C6; baseline is read-only, mismatch means roll back, "
            "never edit expectations)"
        )

    document = check_top_level(load_json(path))
    cases = document["cases"]
    with_prob, with_error = check_case_counts(cases)
    check_seeds(cases)
    check_prob_bits(cases)
    check_error_codes(cases)

    print(f"ok {len(cases)}={with_prob}+{with_error}")
    return EXIT_OK


def run_not_implemented(ctx: Context) -> int:
    """十二个产品比对模式：Task 10 交付，当前显式 exit 3。"""
    # 占位分支：显式 exit 3（不得静默返回 0）。Task 10 Step 0 以
    # `grep -c 'exit 3' tools/compare_golden.py == 0` 作为本占位已移除的判据。
    print(
        f"mode not implemented: {ctx.mode} "
        "(Task 10; this task delivers --self-check only)",
        file=sys.stderr,
    )
    return EXIT_NOT_IMPLEMENTED


MODE_HANDLERS: dict[str, Handler] = {
    mode: (run_self_check if mode == MODE_SELF_CHECK else run_not_implemented)
    for mode in MODE_NAMES
}

# 派发完整性守卫：13 个 --mode 选项必须各有处理函数。
assert set(MODE_HANDLERS) == set(MODE_NAMES), "mode dispatch table is incomplete"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compare_golden.py",
        allow_abbrev=False,
        description=(
            "Self-check the langdetect golden baseline (docs/port/golden/expected.json). "
            "Task 2 delivers --self-check only; the twelve product comparison modes are "
            "deferred to Task 10 and exit 3 until then."
        ),
        epilog=(
            "Golden dir resolution (first match wins):\n"
            "  1. --golden-dir\n"
            "  2. $LANGDETECT_GOLDEN_DIR\n"
            "  3. <repo-root>/docs/port/golden   (repo root = parent of this script's dir)\n"
            "Relative paths are resolved against the current working directory.\n"
            "\n"
            "Exit codes:\n"
            "  0  mode succeeded (--self-check prints 'ok 268=250+18')\n"
            "  1  baseline violates the contract (md5 / structure / counts / seeds / "
            "prob_bits / error code)\n"
            "  2  invalid arguments, or golden dir / expected.json missing or unreadable\n"
            "  3  product comparison mode not implemented yet (Task 10)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        choices=TARGETS,
        default="native",
        help="target runtime for product modes (default: native; ignored by self-check)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        choices=SEED_CHOICES,
        default=None,
        help="RNG seed for product modes (default: none; ignored by self-check)",
    )
    parser.add_argument(
        "--mode",
        choices=MODE_NAMES,
        default=None,
        help="mode to run (default: self-check); the twelve product modes exit 3 "
        "until Task 10",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="alias for --mode self-check; conflicts with any other --mode",
    )
    parser.add_argument(
        "--golden-dir",
        default=None,
        metavar="PATH",
        help="golden baseline directory (default: <repo-root>/docs/port/golden, "
        "overridable via $LANGDETECT_GOLDEN_DIR)",
    )
    return parser


def resolve_mode(parser: argparse.ArgumentParser, args: argparse.Namespace) -> str:
    """--self-check 与 --mode 的合并规则（不允许静默忽略 --self-check）。"""
    if args.self_check:
        if args.mode not in (None, MODE_SELF_CHECK):
            parser.error(
                f"--self-check conflicts with --mode {args.mode!r}; "
                "run them separately"
            )
        return MODE_SELF_CHECK
    if args.mode is not None:
        return args.mode
    # 两者都未给出时的安全默认：只读自检，绝不臆造产品比对结论。
    return MODE_SELF_CHECK


def resolve_golden_dir(raw: str | None) -> tuple[Path, str]:
    """返回 (解析后的目录, 来源说明)。优先级：flag > env > 仓库默认。"""
    if raw is not None:
        source = "--golden-dir"
        candidate = Path(raw)
    else:
        env_value = os.environ.get(GOLDEN_DIR_ENV, "").strip()
        if env_value:
            source = f"${GOLDEN_DIR_ENV}"
            candidate = Path(env_value)
        else:
            source = "default"
            candidate = DEFAULT_GOLDEN_DIR
    return candidate.expanduser().resolve(), source


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    mode = resolve_mode(parser, args)
    golden_dir, source = resolve_golden_dir(args.golden_dir)

    if not golden_dir.is_dir():
        print(
            f"error: golden dir does not exist or is not a directory: "
            f"{golden_dir} (source: {source})",
            file=sys.stderr,
        )
        return EXIT_USAGE

    ctx = Context(
        mode=mode,
        target=args.target,
        seed=args.seed,
        golden_dir=golden_dir,
    )
    try:
        return MODE_HANDLERS[mode](ctx)
    except SetupError as exc:
        print(f"error: {mode}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except CheckFailure as exc:
        print(f"{mode} FAILED: {exc}", file=sys.stderr)
        return EXIT_CHECK_FAILED


if __name__ == "__main__":
    sys.exit(main())
