# -*- coding: utf-8 -*-
"""golden 基准比对器（约定 C 全部产品模式，Task 10 phase 10a）。

契约来源
- `约定 C：golden 基准消费契约` §2（C1-C6）/ §3（C-C1…C-C6 门禁命令）/ §4（分档）。
- spec §8.2 / §8.3 / §8.4（维度二 / 三 / 四的比对入口）与 §4A 的产品落点。

模式
- ``--self-check``：校验基准自身完整性（C1-C6 + 顶层结构），输出
  ``ok 268=250+18``。
- ``--dry-run``：逐案例打印 ``<id>\\t<seed>\\t<tags>`` 一行，并断言行数 =
  268（计划 Task 10 Step 7 的「dry-run：输出行数 = 268」）。只读基准，
  不调用诊断二进制，任何目标平台均可运行。
- 十二个产品比对模式：``prob_bits`` / ``seed_semantics`` / ``failures`` /
  ``forensics`` / ``cleaning`` / ``features_cache`` / ``profile_counts`` /
  ``repeatability`` / ``top1`` / ``lang_list_len`` / ``entry_total`` /
  ``prob_tolerance``。native 目标通过诊断 CLI ``src/core/cmd/golden`` 逐案例
  求值；``prob_tolerance`` 只登记 native 的「位级唯一口径」结论，js / wasm-gc /
  native-other 因容差值未登记而以 exit 2 拒绝（与 ``require_native`` 同语义）。

诊断 CLI 协议
- 每次调用读一个 JSON 参数（``mode`` / ``text`` / ``text2?`` / ``seed`` /
  ``max_length?``），stdout 输出一行 JSON。
- 默认二进制路径（相对仓库根）：
  ``_build/native/debug/build/src/core/cmd/golden/main.exe``；本工具链按
  包目录名命名可执行产物，因此同一目录下的 ``golden.exe`` 作为回退候选。
  覆盖顺序：``--binary`` > 环境变量 ``LANGDETECT_GOLDEN_BIN`` > 默认候选。
- 判据（约定 C）：native 只比 ``prob_bits``（16 位小写 hex），不比
  ``prob`` / ``prob_repr``；异常案例比 ``code`` / ``message`` /
  ``input_len`` / ``input_prefix``，其中后两者由案例原文推导
  （``input_len`` = 码点数，``input_prefix`` = 前 32 码点，spec §5.8）。

路径与可移植性
- 默认基准目录 = 本脚本所在目录的上一级（仓库根）下的 ``docs/port/golden``；
  脚本内不出现任何机器绝对路径。
- 覆盖顺序：``--golden-dir`` > 环境变量 ``LANGDETECT_GOLDEN_DIR`` > 默认目录。
- 相对路径按当前工作目录解析。

只读承诺（C6）
- 脚本只以只读方式打开基准文件，不写入、不改名、不删除任何文件。

退出码
- 0：模式执行成功且所有判据成立（``prob_tolerance`` 的 native 记录模式也返回 0）。
- 1：基准内容或产品输出不满足契约（md5 / 结构 / 计数 / seed / prob_bits /
  异常四字段 / 其他模式判据）。
- 2：参数非法、基准目录 / 基准文件 / 诊断二进制缺失或不可执行。

用法
    .venv/Scripts/python.exe tools/compare_golden.py --self-check
    .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode prob_bits
    .venv/Scripts/python.exe tools/compare_golden.py --target native --mode seed_semantics
    .venv/Scripts/python.exe tools/compare_golden.py --target native --mode failures
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
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

# 诊断可执行产物：moon 按包目录名命名，golden 包的产物是 golden.exe；
# 任务约定路径写的是 main.exe，故两者都列为默认候选（存在者优先）。
DEFAULT_BINARY_CANDIDATES = (
    ROOT / "_build" / "native" / "debug" / "build" / "src" / "core" / "cmd" / "golden" / "main.exe",
    ROOT / "_build" / "native" / "debug" / "build" / "src" / "core" / "cmd" / "golden" / "golden.exe",
)
BINARY_ENV = "LANGDETECT_GOLDEN_BIN"
DEFAULT_TIMEOUT_SECONDS = 120.0

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

# 产品规模判据（spec §4.5 / FR-13 / FR-25 / 约定 A）
EXPECTED_LANG_LIST_LEN = 55
EXPECTED_ENTRY_TOTAL = 184129
EXPECTED_VECTOR_LEN = 55

# --------------------------------------------------------------------------- #
# 常量：CLI 与退出码
# --------------------------------------------------------------------------- #

TARGETS = ("native", "js", "wasm-gc", "native-other")
SEED_CHOICES = (0, 42)
MODE_SELF_CHECK = "self-check"
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
MODE_DRY_RUN = "dry-run"
MODE_NAMES = (MODE_SELF_CHECK, MODE_DRY_RUN) + PRODUCT_MODES

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2

# --------------------------------------------------------------------------- #
# 异常：区分「环境/参数问题」(exit 2) 与「基准/产品内容违约」(exit 1)
# --------------------------------------------------------------------------- #


class SetupError(Exception):
    """路径缺失、文件不可读、二进制缺失等环境问题 → exit 2。"""


class CheckFailure(Exception):
    """基准内容或产品输出不满足约定 C 的判据 → exit 1。"""


# --------------------------------------------------------------------------- #
# 运行上下文与模式派发
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Context:
    """一次运行的不可变上下文。"""

    mode: str
    target: str
    seed: int | None
    golden_dir: Path
    binary: Path
    timeout: float

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
# 基准加载（只读，C6）
# --------------------------------------------------------------------------- #


def load_baseline(ctx: Context, verify_md5: bool = True) -> dict[str, Any]:
    """读取并结构校验基准；产品模式同样先验 md5，保证只读口径一致。"""
    path = ctx.baseline_path
    if not path.is_file():
        raise SetupError(f"{BASELINE_NAME} not found in golden dir: {ctx.golden_dir}")
    if verify_md5:
        digest = md5_of(path)
        if digest != BASELINE_MD5:
            raise CheckFailure(
                f"{BASELINE_NAME} md5 {digest} != registered baseline {BASELINE_MD5} "
                "(convention C C6; baseline is read-only, mismatch means roll back, "
                "never edit expectations)"
            )
    document = check_top_level(load_json(path))
    cases = document["cases"]
    check_case_counts(cases)
    check_seeds(cases)
    check_prob_bits(cases)
    check_error_codes(cases)
    return document


# --------------------------------------------------------------------------- #
# 诊断 CLI 调用
# --------------------------------------------------------------------------- #


def resolve_binary(raw: str | None) -> Path:
    """返回诊断二进制路径：flag > env > 默认候选（main.exe 优先）。"""
    if raw is not None:
        candidate = Path(raw)
        source = "--binary"
        if not candidate.is_file():
            raise SetupError(f"diagnostic binary not found (source: {source}): {candidate}")
        return candidate.expanduser().resolve()

    env_value = os.environ.get(BINARY_ENV, "").strip()
    if env_value:
        candidate = Path(env_value)
        if not candidate.is_file():
            raise SetupError(
                f"diagnostic binary not found (source: ${BINARY_ENV}): {candidate}"
            )
        return candidate.expanduser().resolve()

    existing = [path for path in DEFAULT_BINARY_CANDIDATES if path.is_file()]
    if not existing:
        tried = ", ".join(str(path) for path in DEFAULT_BINARY_CANDIDATES)
        raise SetupError(
            "diagnostic binary not built; run `moon build --target native` first "
            f"(tried: {tried})"
        )
    return existing[0].resolve()


def require_native(ctx: Context, mode: str) -> None:
    """产品模式只在本机 native 运行；其余目标在 Task 11 回补。"""
    if ctx.target != "native":
        raise SetupError(
            f"{mode}: target {ctx.target!r} is not executable in this environment "
            "(only native is available; js / wasm-gc / native-other are Task 11)"
        )


class Diagnostic:
    """逐案例调用诊断 CLI，并按 (case id, seed, mode) 缓存结果。"""

    def __init__(self, binary: Path, timeout: float) -> None:
        self.binary = binary
        self.timeout = timeout
        self._cache: dict[tuple[str, int | None, str], dict[str, Any]] = {}

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        line = json.dumps(payload, ensure_ascii=False)
        try:
            proc = subprocess.run(
                [str(self.binary), line],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
        except OSError as exc:
            raise SetupError(f"cannot execute diagnostic binary: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise CheckFailure(
                f"diagnostic binary timed out after {self.timeout}s "
                f"for mode {payload.get('mode')!r}"
            ) from exc
        if proc.returncode != 0:
            raise CheckFailure(
                f"diagnostic binary exited {proc.returncode} "
                f"(mode {payload.get('mode')!r}); stderr={proc.stderr.strip()[:400]!r}"
            )
        lines = [row for row in proc.stdout.splitlines() if row.strip()]
        if len(lines) != 1:
            raise CheckFailure(
                f"diagnostic binary must print exactly one JSON line, "
                f"got {len(lines)}: {proc.stdout.strip()[:400]!r}"
            )
        try:
            result = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            raise CheckFailure(
                f"diagnostic output is not JSON: {lines[0][:400]!r}"
            ) from exc
        if not isinstance(result, dict):
            raise CheckFailure("diagnostic output must be a JSON object")
        if result.get("mode") != payload.get("mode"):
            raise CheckFailure(
                f"diagnostic output mode {result.get('mode')!r} != "
                f"requested {payload.get('mode')!r}"
            )
        return result

    def case(self, case: dict[str, Any], mode: str = "langs") -> dict[str, Any]:
        key = (case["id"], case["seed"], mode)
        if key not in self._cache:
            self._cache[key] = self.run(
                {
                    "mode": mode,
                    "text": case["text"],
                    "seed": case["seed"],
                }
            )
        return self._cache[key]


# --------------------------------------------------------------------------- #
# 结果比较辅助
# --------------------------------------------------------------------------- #


def lang_pairs(entries: Any, label: str) -> list[tuple[str, str]]:
    """把 detect_langs / langs 列表规约为 (lang, prob_bits) 序列。"""
    if not isinstance(entries, list):
        raise CheckFailure(f"{label}: expected a JSON array, got {type(entries).__name__}")
    pairs: list[tuple[str, str]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise CheckFailure(f"{label} entry {index}: must be a JSON object")
        lang = entry.get("lang")
        bits = entry.get("prob_bits")
        if not isinstance(lang, str):
            raise CheckFailure(f"{label} entry {index}: lang must be a string")
        if not isinstance(bits, str) or PROB_BITS_RE.fullmatch(bits) is None:
            raise CheckFailure(
                f"{label} entry {index}: prob_bits {bits!r} is not 16 lowercase hex"
            )
        pairs.append((lang, bits))
    return pairs


def observed_lang_pairs(result: dict[str, Any], label: str) -> list[tuple[str, str]]:
    return lang_pairs(result.get("langs"), label)


def expected_lang_pairs(case: dict[str, Any]) -> list[tuple[str, str]]:
    return lang_pairs(case.get("detect_langs"), f"expected {case['id']}")


def top_lang(result: dict[str, Any], label: str) -> str:
    pairs = observed_lang_pairs(result, label)
    if not pairs:
        raise CheckFailure(f"{label}: result has no languages")
    return pairs[0][0]


def aggregate(failures: list[str], limit: int = 12) -> str:
    head = failures[:limit]
    suffix = ""
    if len(failures) > limit:
        suffix = f" (+{len(failures) - limit} more)"
    return "; ".join(head) + suffix


def diff_text(text: str) -> str:
    """Repr 便于在日志中看到空白/控制字符。"""
    return repr(text)


# --------------------------------------------------------------------------- #
# 模式实现：基准自检
# --------------------------------------------------------------------------- #


def run_self_check(ctx: Context) -> int:
    """--self-check：校验基准自身完整性（C1-C6 + 顶层结构）。"""
    document = load_baseline(ctx)
    cases = document["cases"]
    with_prob, with_error = check_case_counts(cases)
    total_entries = check_prob_bits(cases)
    print(
        f"ok {len(cases)}={with_prob}+{with_error} "
        f"(prob_entries={total_entries}, seeds=0/42)"
    )
    return EXIT_OK


# 计划 Task 10 Step 7 的 dry-run：输出行数必须等于基准案例总数（268）。
DRY_RUN_EXPECTED_LINES = EXPECTED_CASE_COUNTS[0]


def run_dry_run(ctx: Context) -> int:
    """--dry-run：逐案例打印一行，并断言行数 = 268（计划 Step 7）。

    行格式：`<id>\\t<seed>\\t<tags>`（tags 以逗号连接，空则 `-`）。
    只读基准，不调用诊断二进制，因此目标平台无关。
    """
    document = load_baseline(ctx)
    cases = document["cases"]
    lines = 0
    for case in cases:
        tags = case.get("tags") or []
        tag_text = ",".join(str(tag) for tag in tags) if tags else "-"
        print(f"{case['id']}\t{case['seed']}\t{tag_text}")
        lines += 1
    if lines != DRY_RUN_EXPECTED_LINES:
        raise CheckFailure(
            f"dry-run: printed {lines} lines, expected {DRY_RUN_EXPECTED_LINES} "
            "(one per baseline case)"
        )
    print(
        f"ok dry-run lines={lines} expected={DRY_RUN_EXPECTED_LINES} "
        f"(250 probability + 18 error cases)",
        file=sys.stderr,
    )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式实现：prob_bits（C1/C5，native 位级）
# --------------------------------------------------------------------------- #


def run_prob_bits(ctx: Context) -> int:
    require_native(ctx, "prob_bits")
    if ctx.seed is None:
        raise SetupError("mode prob_bits requires --seed {0,42}")
    document = load_baseline(ctx)
    cases = [
        case
        for case in document["cases"]
        if case.get("detect_langs") and case["seed"] == ctx.seed
    ]
    if not cases:
        raise CheckFailure(f"no probability cases for seed {ctx.seed}")
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)
    failures: list[str] = []
    entry_count = 0
    for case in cases:
        try:
            result = diagnostic.case(case)
            observed = observed_lang_pairs(result, case["id"])
            expected = expected_lang_pairs(case)
            if observed != expected:
                failures.append(
                    f"{case['id']}: expected {expected!r}, observed {observed!r}"
                )
            entry_count += len(expected)
        except CheckFailure as exc:
            failures.append(f"{case['id']}: {exc}")
    if failures:
        raise CheckFailure(aggregate(failures))
    print(
        f"ok prob_bits target=native seed={ctx.seed} "
        f"cases={len(cases)}/{len(cases)} entries={entry_count} bitwise=identical"
    )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式实现：failures / forensics（C4 + spec §5.8 四字段）
# --------------------------------------------------------------------------- #


def check_error_cases(
    ctx: Context,
    detail: bool,
) -> tuple[int, list[str]]:
    document = load_baseline(ctx)
    error_cases = [case for case in document["cases"] if "error" in case]
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)
    failures: list[str] = []
    matched = 0
    for case in error_cases:
        text = case["text"]
        expected = case["error"]
        expected_len = len(text)
        expected_prefix = text[:32]
        try:
            result = diagnostic.case(case)
            if "langs" in result:
                failures.append(f"{case['id']}: expected error, observed langs")
                continue
            error = result.get("error")
            if not isinstance(error, dict):
                failures.append(f"{case['id']}: missing 'error' object")
                continue
            problems: list[str] = []
            if error.get("code") != expected.get("code"):
                problems.append(
                    f"code {error.get('code')!r} != {expected.get('code')!r}"
                )
            if error.get("message") != expected.get("message"):
                problems.append(
                    f"message {error.get('message')!r} != {expected.get('message')!r}"
                )
            if error.get("input_len") != expected_len:
                problems.append(
                    f"input_len {error.get('input_len')!r} != {expected_len}"
                )
            if error.get("input_prefix") != expected_prefix:
                problems.append(
                    f"input_prefix {error.get('input_prefix')!r} != "
                    f"{expected_prefix!r}"
                )
            if detail:
                print(
                    f"forensics {case['id']}: code={error.get('code')} "
                    f"message={error.get('message')!r} "
                    f"input_len={error.get('input_len')} "
                    f"input_prefix={diff_text(str(error.get('input_prefix')))} "
                    f"expected_len={expected_len} "
                    f"expected_prefix={diff_text(expected_prefix)}"
                )
            if problems:
                failures.append(f"{case['id']}: " + ", ".join(problems))
            else:
                matched += 1
        except CheckFailure as exc:
            failures.append(f"{case['id']}: {exc}")
    if detail:
        print(
            f"forensics: expected.json carries code/message/type only; "
            f"input_len/input_prefix derived from case text (spec §5.8)"
        )
    return matched, failures


def run_failures(ctx: Context) -> int:
    require_native(ctx, "failures")
    matched, failures = check_error_cases(ctx, detail=False)
    if failures:
        raise CheckFailure(aggregate(failures))
    print(
        f"ok failures target=native cases={matched}/{matched} "
        "code/message/input_len/input_prefix matched; failure_set=[]"
    )
    return EXIT_OK


def run_forensics(ctx: Context) -> int:
    require_native(ctx, "forensics")
    matched, failures = check_error_cases(ctx, detail=True)
    if failures:
        raise CheckFailure(aggregate(failures))
    print(
        f"ok forensics target=native cases={matched}/{matched} "
        "four_fields=code/message/input_len/input_prefix"
    )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式实现：seed 语义（repeatability / seed_diff / unseeded_runs）
# --------------------------------------------------------------------------- #


def check_repeatability(
    document: dict[str, Any],
    diagnostic: Diagnostic,
) -> tuple[int, int, list[str]]:
    cases_by_id = {case["id"]: case for case in document["cases"] if case["seed"] == 0}
    groups = document["repeatability"]
    failures: list[str] = []
    checked_runs = 0
    groups_ok = 0
    for group in groups:
        case = cases_by_id.get(group["id"])
        if case is None:
            failures.append(f"{group['id']}/seed{group['seed']}: no seed-0 case")
            continue
        expected = lang_pairs(
            group["sample"].get("detect_langs"),
            f"expected repeatability {group['id']}/seed{group['seed']}",
        )
        observed_runs: list[list[tuple[str, str]]] = []
        for _ in range(group["runs"]):
            result = diagnostic.run(
                {"mode": "langs", "text": case["text"], "seed": group["seed"]}
            )
            observed_runs.append(
                observed_lang_pairs(result, f"{group['id']}/seed{group['seed']}")
            )
            checked_runs += 1
        if any(pairs != expected for pairs in observed_runs):
            failures.append(
                f"{group['id']}/seed{group['seed']}: runs differ from expected sample"
            )
        elif len({tuple(pairs) for pairs in observed_runs}) != 1:
            failures.append(
                f"{group['id']}/seed{group['seed']}: same-seed runs are not identical"
            )
        else:
            groups_ok += 1
    return groups_ok, checked_runs, failures


def run_repeatability(ctx: Context) -> int:
    require_native(ctx, "repeatability")
    document = load_baseline(ctx)
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)
    groups_ok, checked_runs, failures = check_repeatability(document, diagnostic)
    groups = len(document["repeatability"])
    if failures:
        raise CheckFailure(aggregate(failures))
    print(
        f"ok repeatability target=native groups={groups_ok}/{groups} "
        f"runs={checked_runs} identical=yes"
    )
    return EXIT_OK


def check_seed_diff(
    document: dict[str, Any],
    diagnostic: Diagnostic,
) -> tuple[int, list[str]]:
    cases_by_id = {case["id"]: case for case in document["cases"] if case["seed"] == 0}
    entries = document["seed_diff"]
    failures: list[str] = []
    checked = 0
    for entry in entries:
        case = cases_by_id.get(entry["id"])
        if case is None:
            failures.append(f"{entry['id']}: no seed-0 case")
            continue
        result0 = diagnostic.run(
            {"mode": "langs", "text": case["text"], "seed": 0}
        )
        result42 = diagnostic.run(
            {"mode": "langs", "text": case["text"], "seed": 42}
        )
        observed0 = observed_lang_pairs(result0, f"{entry['id']}/seed0")
        observed42 = observed_lang_pairs(result42, f"{entry['id']}/seed42")
        expected0 = lang_pairs(entry.get("seed0_langs"), f"{entry['id']}/seed0 expected")
        expected42 = lang_pairs(entry.get("seed42_langs"), f"{entry['id']}/seed42 expected")
        problems: list[str] = []
        if observed0 != expected0:
            problems.append("seed0 differs from expected")
        if observed42 != expected42:
            problems.append("seed42 differs from expected")
        if observed0 == observed42:
            problems.append("seed0 and seed42 are identical (expected a difference)")
        observed_same_detect = (
            bool(observed0) and bool(observed42) and observed0[0][0] == observed42[0][0]
        )
        if observed_same_detect != bool(entry.get("same_detect")):
            problems.append(
                f"same_detect {observed_same_detect} != {entry.get('same_detect')}"
            )
        if problems:
            failures.append(f"{entry['id']}: " + ", ".join(problems))
        else:
            checked += 1
    return checked, failures


# unseeded 批大小与最大批数（I3）：单批 10 次在变异文本上会误红，故允许补跑。
UNSEEDED_BATCH_RUNS = 10
UNSEEDED_MAX_BATCHES = 3


def unseeded_allowed_tops(
    document: dict[str, Any], entry: dict[str, Any]
) -> set[str]:
    """该文本允许出现的 top language 集合。

    判据来源（从严）：基准 `distinct_langs` ∪ 同文本 seed-0 / seed-42 的
    `detect`（基准里若登记了该文本的定种结果）。任何集合外的 top 都判红——
    上游 `detect()` 在 unseeded 路径上仍取 `max(prob)`，随机只应改变两个
    候选的相对次序，不应换成第三种语言。
    """
    allowed = {str(lang) for lang in (entry.get("distinct_langs") or [])}
    text = entry.get("text")
    for case in document["cases"]:
        if case.get("text") == text and case.get("detect"):
            allowed.add(str(case["detect"]))
    return allowed


def check_unseeded(
    document: dict[str, Any],
    diagnostic: Diagnostic,
) -> tuple[int, int, list[str]]:
    """比对 unseeded 路径：top 语言严格 + RNG 变异（I3）。

    判据
    1. 严格（每次运行）：观测 top 必须属于 `unseeded_allowed_tops(...)`。
       这能抓住「实现换成了第三种语言」或「top 选择逻辑坏了」。
    2. 变异（基准 `distinct_count > 1` 时）：至少出现两个不同的签名
       `((lang, prob_bits), ...)`。实现若把 unseeded 退化成定种（
       `distinct_results=1`），单批 10 次会漏判；故单批退化为单例时最多补
       跑至 3 批（30 次），**只有全部批次都单调**才判红。

    残余误红概率（本机实测上游 split 为 fi 6 / pl 4，即单次 0.6/0.4）：
    - 以实测 split 计：P(单批单调) = 0.6^10 + 0.4^10 ≈ 6.2e-3，
      P(连续 3 批单调) ≈ 2.4e-7；
    - 以最保守的「每次运行 0.85 概率落在同一侧」模型计（reviewer 口径）：
      P(全部 30 次单调) ≈ 0.85^30 ≈ 7.6e-3。
    两种口径都不影响正常实现（正常实现单批几乎必然出现两个签名）。
    """
    failures: list[str] = []
    total_runs = 0
    texts_ok = 0
    for entry in document["unseeded_runs"]:
        text = entry["text"]
        label = f"unseeded text_len={len(text)}"
        allowed = unseeded_allowed_tops(document, entry)
        baseline_distinct = int(entry.get("distinct_count") or 0)
        want_variation = baseline_distinct > 1
        signatures: set[tuple[tuple[str, str], ...]] = set()
        tops: set[str] = set()
        text_failed = False
        batches = 0
        while batches < UNSEEDED_MAX_BATCHES:
            batches += 1
            for _ in range(UNSEEDED_BATCH_RUNS):
                result = diagnostic.run({"mode": "langs", "text": text, "seed": None})
                total_runs += 1
                if "error" in result:
                    failures.append(
                        f"{label}: unexpected error "
                        f"{result['error'].get('code')}: {result['error'].get('message')}"
                    )
                    text_failed = True
                    break
                pairs = observed_lang_pairs(result, "unseeded")
                if not pairs:
                    failures.append(f"{label}: empty language list")
                    text_failed = True
                    break
                top = pairs[0][0]
                tops.add(top)
                if top not in allowed:
                    failures.append(
                        f"{label}: top {top!r} not in baseline distinct_langs "
                        f"{sorted(allowed)}"
                    )
                    text_failed = True
                    break
                signatures.add(tuple(pairs))
            if text_failed or not want_variation or len(signatures) >= 2:
                break
        if text_failed:
            continue
        if want_variation and len(signatures) < 2:
            failures.append(
                f"{label}: no RNG variation across {batches * UNSEEDED_BATCH_RUNS} "
                f"runs (distinct_results=1, baseline distinct_count={baseline_distinct})"
            )
            continue
        texts_ok += 1
        print(
            f"unseeded text_len={len(text)} runs={batches * UNSEEDED_BATCH_RUNS} "
            f"batches={batches} distinct_results={len(signatures)} "
            f"distinct_top_langs={sorted(tops)} "
            f"allowed_top_langs={sorted(allowed)}"
        )
    return texts_ok, total_runs, failures


def run_seed_semantics(ctx: Context) -> int:
    require_native(ctx, "seed_semantics")
    document = load_baseline(ctx)
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)

    groups_ok, checked_runs, failures = check_repeatability(document, diagnostic)
    groups = len(document["repeatability"])
    if groups_ok != groups:
        raise CheckFailure("repeatability: " + aggregate(failures))

    diff_ok, diff_failures = check_seed_diff(document, diagnostic)
    failures.extend(diff_failures)
    diff_total = len(document["seed_diff"])

    texts_ok, unseeded_runs, unseeded_failures = check_unseeded(document, diagnostic)
    failures.extend(unseeded_failures)
    unseeded_total = len(document["unseeded_runs"])

    if failures:
        raise CheckFailure(aggregate(failures))
    print(
        f"ok seed_semantics target=native "
        f"repeatability={groups_ok}/{groups} groups x5 runs ({checked_runs} runs), "
        f"seed_diff={diff_ok}/{diff_total} (0 vs 42 differ as recorded), "
        f"unseeded={texts_ok}/{unseeded_total} texts "
        f"({unseeded_runs} runs; top in baseline distinct_langs, RNG variation "
        f"required where baseline distinct_count > 1)"
    )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式实现：top1 / lang_list_len / entry_total / profile_counts
# --------------------------------------------------------------------------- #


def run_top1(ctx: Context) -> int:
    require_native(ctx, "top1")
    document = load_baseline(ctx)
    cases = [case for case in document["cases"] if case.get("detect_langs")]
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)
    failures: list[str] = []
    matched = 0
    for case in cases:
        try:
            result = diagnostic.case(case)
            observed = top_lang(result, case["id"])
            expected = case["detect"]
            if observed != expected:
                failures.append(f"{case['id']}: top {observed!r} != detect {expected!r}")
            else:
                matched += 1
        except CheckFailure as exc:
            failures.append(f"{case['id']}: {exc}")
    if failures:
        raise CheckFailure(aggregate(failures))
    print(f"ok top1 target=native cases={matched}/{len(cases)} top_lang=detect")
    return EXIT_OK


def run_meta(ctx: Context, mode: str) -> dict[str, Any]:
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)
    result = diagnostic.run({"mode": "meta"})
    if "error" in result:
        raise CheckFailure(f"meta: {result['error']}")
    return result


def run_lang_list_len(ctx: Context) -> int:
    require_native(ctx, "lang_list_len")
    document = load_baseline(ctx)
    result = run_meta(ctx, "lang_list_len")
    lang_list = result.get("lang_list")
    expected_list = document["meta"].get("langlist")
    problems: list[str] = []
    if result.get("lang_list_len") != EXPECTED_LANG_LIST_LEN:
        problems.append(
            f"lang_list_len {result.get('lang_list_len')!r} != {EXPECTED_LANG_LIST_LEN}"
        )
    if not isinstance(lang_list, list) or len(lang_list) != EXPECTED_LANG_LIST_LEN:
        problems.append(f"lang_list length {len(lang_list) if isinstance(lang_list, list) else None}")
    if lang_list != expected_list:
        problems.append("lang_list differs from expected.json meta.langlist")
    if problems:
        raise CheckFailure("; ".join(problems))
    print(
        f"ok lang_list_len target=native len={EXPECTED_LANG_LIST_LEN} "
        f"order=expected.json/meta.langlist"
    )
    return EXIT_OK


def run_entry_total(ctx: Context) -> int:
    require_native(ctx, "entry_total")
    load_baseline(ctx)
    result = run_meta(ctx, "entry_total")
    observed = result.get("entry_total")
    if observed != EXPECTED_ENTRY_TOTAL:
        raise CheckFailure(f"entry_total {observed!r} != {EXPECTED_ENTRY_TOTAL}")
    print(f"ok entry_total target=native total={EXPECTED_ENTRY_TOTAL}")
    return EXIT_OK


def run_profile_counts(ctx: Context) -> int:
    require_native(ctx, "profile_counts")
    load_baseline(ctx)
    result = run_meta(ctx, "profile_counts")
    problems: list[str] = []
    if result.get("lang_list_len") != EXPECTED_LANG_LIST_LEN:
        problems.append(f"lang_list_len {result.get('lang_list_len')!r}")
    if result.get("entry_total") != EXPECTED_ENTRY_TOTAL:
        problems.append(f"entry_total {result.get('entry_total')!r}")
    if result.get("vector_len") != EXPECTED_VECTOR_LEN:
        problems.append(f"vector_len {result.get('vector_len')!r}")
    if problems:
        raise CheckFailure(
            "profile_counts: "
            + ", ".join(problems)
            + f" (expected {EXPECTED_LANG_LIST_LEN}/{EXPECTED_ENTRY_TOTAL}/{EXPECTED_VECTOR_LEN})"
        )
    print(
        f"ok profile_counts target=native lang_list_len={EXPECTED_LANG_LIST_LEN} "
        f"entry_total={EXPECTED_ENTRY_TOTAL} vector_len={EXPECTED_VECTOR_LEN} "
        f"u06_parse_ms={result.get('parse_ms')} u06_load_ms={result.get('load_ms')}"
    )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式实现：cleaning（V-40…V-43）
# --------------------------------------------------------------------------- #

# (标签, 输入, 期望 append+cleaning_text 之后的文本)
CLEANING_CASES = (
    (
        "V-40-url-followed-by-text",
        {"text": "see http://a.com/x then TEXT-more"},
        "see then TEXT-more",
    ),
    (
        "V-40-url-trailing-space",
        {"text": "hello https://example.com/abc"},
        "hello ",
    ),
    (
        "V-41-mail-address",
        {"text": "mail me at john.doe@example.com please"},
        "mail me at please",
    ),
    (
        "V-42-consecutive-spaces",
        {"text": "a  b\t\tc"},
        "a b\t\tc",
    ),
    (
        "V-43-max-length-5",
        {"text": "abcdefghij", "max_length": 5},
        "abcde",
    ),
    (
        "V-43-max-length-3",
        {"text": "aaabbb", "max_length": 3},
        "aaa",
    ),
)


def run_cleaning(ctx: Context) -> int:
    require_native(ctx, "cleaning")
    load_baseline(ctx)
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)
    failures: list[str] = []
    matched = 0
    for label, fields, expected in CLEANING_CASES:
        payload = {"mode": "cleaning", "seed": 0}
        payload.update(fields)
        result = diagnostic.run(payload)
        if "error" in result:
            failures.append(f"{label}: {result['error']}")
            continue
        observed = result.get("text")
        if observed != expected:
            failures.append(
                f"{label}: observed {diff_text(str(observed))} != "
                f"expected {diff_text(expected)}"
            )
        else:
            matched += 1
    if failures:
        raise CheckFailure(aggregate(failures))
    print(f"ok cleaning target=native cases={matched}/{len(CLEANING_CASES)} V-40..V-43")
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式实现：features_cache（V-46 / V-47）
# --------------------------------------------------------------------------- #

FEATURES_TEXT = "USA NASA FBI"
FEATURES_EXPECTED = (
    "U",
    " U",
    "A ",
    "SA ",
    "N",
    " N",
    "A ",
    "SA ",
    "F",
    " F",
)


def run_features_cache(ctx: Context) -> int:
    require_native(ctx, "features_cache")
    document = load_baseline(ctx)
    diagnostic = Diagnostic(ctx.binary, ctx.timeout)
    failures: list[str] = []
    matched = 0

    result = diagnostic.run({"mode": "features", "text": FEATURES_TEXT, "seed": 0})
    observed_grams = result.get("grams")
    if result.get("mode") != "features" or "error" in result:
        failures.append(f"V-46: {result.get('error')}")
    elif observed_grams != list(FEATURES_EXPECTED):
        failures.append(
            f"V-46: grams {observed_grams!r} != {list(FEATURES_EXPECTED)!r}"
        )
    else:
        matched += 1

    case = next(
        (
            item
            for item in document["cases"]
            if item["id"] == "short-en" and item["seed"] == 0
        ),
        None,
    )
    if case is None:
        failures.append("V-47: baseline is missing short-en/seed0")
    else:
        cache = diagnostic.run(
            {
                "mode": "cache",
                "text": case["text"],
                "text2": "Ein, zwei, drei, vier",
                "seed": 0,
            }
        )
        if "error" in cache:
            failures.append(f"V-47: {cache['error']}")
        else:
            probs1 = lang_pairs(cache.get("probs1"), "cache probs1")
            probs2 = lang_pairs(cache.get("probs2"), "cache probs2")
            expected = expected_lang_pairs(case)
            if probs1 != probs2:
                failures.append("V-47: probs1 != probs2 after second append")
            elif probs1 != expected:
                failures.append("V-47: probs1 != short-en/seed0 expected")
            else:
                matched += 1

    if failures:
        raise CheckFailure(aggregate(failures))
    print(
        f"ok features_cache target=native checks={matched}/2 "
        "V-46 raw grams exact; V-47 probs1==probs2"
    )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式实现：prob_tolerance（C5 分档记录）
# --------------------------------------------------------------------------- #


def run_prob_tolerance(ctx: Context) -> int:
    if ctx.target != "native":
        raise SetupError(
            f"prob_tolerance: target {ctx.target!r} is not executable in this "
            "environment (only native is available; js / wasm-gc / native-other "
            "have no registered tolerance values)"
        )
    print(
        "ok prob_tolerance target=native: bitwise-only, tolerance not applicable "
        "(convention C C1/C5; native compares prob_bits)"
    )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# 模式派发
# --------------------------------------------------------------------------- #

MODE_HANDLERS: dict[str, Handler] = {
    MODE_SELF_CHECK: run_self_check,
    MODE_DRY_RUN: run_dry_run,
    "prob_bits": run_prob_bits,
    "seed_semantics": run_seed_semantics,
    "failures": run_failures,
    "forensics": run_forensics,
    "cleaning": run_cleaning,
    "features_cache": run_features_cache,
    "profile_counts": run_profile_counts,
    "repeatability": run_repeatability,
    "top1": run_top1,
    "lang_list_len": run_lang_list_len,
    "entry_total": run_entry_total,
    "prob_tolerance": run_prob_tolerance,
}

# 派发完整性守卫：每个 --mode 选项必须各有处理函数。写成显式分支而非
# ``assert``，否则 ``python -O`` 会把守卫优化成空操作。
if set(MODE_HANDLERS) != set(MODE_NAMES):
    print(
        "error: mode dispatch table is incomplete: "
        f"missing={sorted(set(MODE_NAMES) - set(MODE_HANDLERS))} "
        f"unknown={sorted(set(MODE_HANDLERS) - set(MODE_NAMES))}",
        file=sys.stderr,
    )
    raise SystemExit(EXIT_USAGE)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compare_golden.py",
        allow_abbrev=False,
        description=(
            "Compare the MoonBit port against the langdetect golden baseline "
            "(docs/port/golden/expected.json). Native product modes drive the "
            "src/core/cmd/golden diagnostic CLI and judge prob_bits bitwise."
        ),
        epilog=(
            "Golden dir resolution (first match wins):\n"
            "  1. --golden-dir\n"
            "  2. $LANGDETECT_GOLDEN_DIR\n"
            "  3. <repo-root>/docs/port/golden   (repo root = parent of this script's dir)\n"
            "\n"
            "Diagnostic binary resolution (first match wins):\n"
            "  1. --binary\n"
            "  2. $LANGDETECT_GOLDEN_BIN\n"
            "  3. _build/native/debug/build/src/core/cmd/golden/main.exe\n"
            "  4. _build/native/debug/build/src/core/cmd/golden/golden.exe\n"
            "Relative paths are resolved against the current working directory.\n"
            "\n"
            "Exit codes:\n"
            "  0  mode succeeded and all judgements hold\n"
            "  1  baseline or product output violates the contract\n"
            "  2  invalid arguments, or golden dir / baseline / diagnostic binary missing\n"
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
        help="RNG seed for prob_bits (0 or 42); other modes use the baseline seeds",
    )
    parser.add_argument(
        "--mode",
        choices=MODE_NAMES,
        default=None,
        help="mode to run (default: self-check)",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="alias for --mode self-check; conflicts with any other --mode",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="alias for --mode dry-run; prints one line per case and asserts 268",
    )
    parser.add_argument(
        "--golden-dir",
        default=None,
        metavar="PATH",
        help="golden baseline directory (default: <repo-root>/docs/port/golden, "
        "overridable via $LANGDETECT_GOLDEN_DIR)",
    )
    parser.add_argument(
        "--binary",
        default=None,
        metavar="PATH",
        help="diagnostic CLI executable (default: "
        "_build/native/debug/build/src/core/cmd/golden/main.exe, "
        "falling back to golden.exe; overridable via $LANGDETECT_GOLDEN_BIN)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"per-invocation timeout (default: {DEFAULT_TIMEOUT_SECONDS:g})",
    )
    return parser


def resolve_mode(parser: argparse.ArgumentParser, args: argparse.Namespace) -> str:
    """--self-check / --dry-run 与 --mode 的合并规则（不允许静默忽略别名）。"""
    if args.self_check and args.dry_run:
        parser.error("--self-check and --dry-run conflict; run them separately")
    alias_mode = None
    alias_flag = ""
    if args.self_check:
        alias_mode, alias_flag = MODE_SELF_CHECK, "--self-check"
    elif args.dry_run:
        alias_mode, alias_flag = MODE_DRY_RUN, "--dry-run"
    if alias_mode is not None:
        if args.mode not in (None, alias_mode):
            parser.error(
                f"{alias_flag} conflicts with --mode {args.mode!r}; "
                "run them separately"
            )
        return alias_mode
    if args.mode is not None:
        return args.mode
    # 两者都未给出时的安全默认：只读自检。
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

    try:
        # 自检与 dry-run 只读基准，不依赖诊断二进制；其余模式先解析二进制。
        if mode in (MODE_SELF_CHECK, MODE_DRY_RUN):
            binary = DEFAULT_BINARY_CANDIDATES[0]
        else:
            binary = resolve_binary(args.binary)
        ctx = Context(
            mode=mode,
            target=args.target,
            seed=args.seed,
            golden_dir=golden_dir,
            binary=binary,
            timeout=args.timeout,
        )
        return MODE_HANDLERS[mode](ctx)
    except SetupError as exc:
        print(f"error: {mode}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except CheckFailure as exc:
        print(f"{mode} FAILED: {exc}", file=sys.stderr)
        return EXIT_CHECK_FAILED


if __name__ == "__main__":
    sys.exit(main())
