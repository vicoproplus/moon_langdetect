# -*- coding: utf-8 -*-
"""Generate `src/unicode/upper_table.mbt` from the repository CPython 3.12.10.

The generated file carries two tables:

  * `upper_intervals` : maximal `(start, end)` intervals where
    `chr(cp).isupper()` is true in CPython 3.12.10 / UCD 15.0.0
    (1951 codepoints compressed into 651 intervals; surrogates skipped).
  * `unicode_block_ranges` : the 220 `(code, start, end)` ranges of the
    upstream `langdetect.utils.unicode_block` table, code 1..220.

Usage (from the repository root):

    .venv/Scripts/python.exe tools/gen_upper_table.py
    .venv/Scripts/python.exe tools/gen_upper_table.py --verify

`--verify` re-reads the generated file, expands both tables and compares
every codepoint against the live interpreter (`str.isupper`, block lookup).
`--output` / `--input` exist only so a scratch copy can be tampered with to
prove that verification really fails; the default path is the product file.

The output is deterministic: no timestamps, fixed ordering, LF line endings,
atomic replace (temp file in the target directory + `os.replace`).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Callable, NoReturn

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = ROOT / "src" / "unicode" / "upper_table.mbt"
UPSTREAM_PACKAGE_ROOT = ROOT / "langdetect"

EXPECTED_PYTHON = "3.12.10"
EXPECTED_UNIDATA = "15.0.0"
EXPECTED_CP_COUNT = 1951
EXPECTED_INTERVAL_COUNT = 651
EXPECTED_BLOCK_COUNT = 220
CP_LIMIT = 0x110000
SURROGATE_LO = 0xD800
SURROGATE_HI = 0xDFFF

UPPER_ARRAY_RE = re.compile(
    r"pub let upper_intervals\s*:\s*Array\[\s*\(\s*Int\s*,\s*Int\s*\)\s*\]"
    r"\s*=\s*\[\n(.*?)\n\]",
    re.S,
)
BLOCK_ARRAY_RE = re.compile(
    r"pub let unicode_block_ranges\s*:\s*Array\[\s*\(\s*Int\s*,\s*Int\s*,\s*Int\s*\)\s*\]"
    r"\s*=\s*\[\n(.*?)\n\]",
    re.S,
)
UPPER_TUPLE_RE = re.compile(r"\(\s*0x([0-9A-Fa-f]+)\s*,\s*0x([0-9A-Fa-f]+)\s*\)")
BLOCK_TUPLE_RE = re.compile(
    r"\(\s*(\d+)\s*,\s*0x([0-9A-Fa-f]+)\s*,\s*0x([0-9A-Fa-f]+)\s*\)"
)


def fail(message: str) -> NoReturn:
    print("error: " + message, file=sys.stderr)
    raise SystemExit(1)


def check_interpreter() -> None:
    if sys.implementation.name != "cpython":
        fail(f"CPython required, got implementation {sys.implementation.name!r}")
    version = sys.version.split()[0]
    if version != EXPECTED_PYTHON:
        fail(f"CPython {EXPECTED_PYTHON} required, got {version}")
    if unicodedata.unidata_version != EXPECTED_UNIDATA:
        fail(
            f"unicodedata {EXPECTED_UNIDATA} required, "
            f"got {unicodedata.unidata_version}"
        )


def upstream_block_rows() -> tuple[list[tuple[int, int, int]], Callable[[str], int | None]]:
    """Import the upstream 220-entry block table from this repository.

    The repository copy is pinned ahead of any installed distribution; this
    is a tool-side reference only - the product must not depend on it.
    """
    package_root = str(UPSTREAM_PACKAGE_ROOT)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    try:
        from langdetect.utils.unicode_block import (  # noqa: PLC0415
            _unicode_blocks,
            unicode_block,
        )
    except ImportError as exc:  # pragma: no cover - environment error
        fail(f"cannot import upstream unicode_block table: {exc}")
    rows = [(int(code), int(start), int(end)) for code, start, end in _unicode_blocks]
    if len(rows) != EXPECTED_BLOCK_COUNT:
        fail(f"upstream block table has {len(rows)} rows, expected {EXPECTED_BLOCK_COUNT}")
    expected_codes = list(range(1, EXPECTED_BLOCK_COUNT + 1))
    if [code for code, _, _ in rows] != expected_codes:
        fail("upstream block codes are not exactly 1..220")
    return rows, unicode_block


def uppercase_intervals() -> list[tuple[int, int]]:
    intervals: list[list[int]] = []
    for cp in range(CP_LIMIT):
        if SURROGATE_LO <= cp <= SURROGATE_HI:
            continue
        if not chr(cp).isupper():
            continue
        if intervals and cp == intervals[-1][1] + 1:
            intervals[-1][1] = cp
        else:
            intervals.append([cp, cp])
    if len(intervals) != EXPECTED_INTERVAL_COUNT:
        fail(f"derived {len(intervals)} intervals, expected {EXPECTED_INTERVAL_COUNT}")
    total = sum(end - start + 1 for start, end in intervals)
    if total != EXPECTED_CP_COUNT:
        fail(f"derived {total} uppercase codepoints, expected {EXPECTED_CP_COUNT}")
    return [(start, end) for start, end in intervals]


def render(
    intervals: list[tuple[int, int]], blocks: list[tuple[int, int, int]]
) -> str:
    lines: list[str] = []
    lines.append(
        "// 勿手改（generated）：tools/gen_upper_table.py 从 .venv CPython 生成；"
        f"python_version={EXPECTED_PYTHON}; unidata_version={EXPECTED_UNIDATA}"
    )
    lines.append(
        "// Truth source: chr(cp).isupper() over 0x000000..0x10FFFF; "
        "surrogates 0xD800..0xDFFF skipped."
    )
    lines.append(
        f"// Counts: {EXPECTED_CP_COUNT} uppercase codepoints in "
        f"{len(intervals)} maximal intervals; {len(blocks)} block ranges."
    )
    lines.append(
        "// Block sentinel: unicode_block returns 0 when a codepoint falls in a table gap."
    )
    lines.append("")
    lines.append(
        f"///| Maximal [start, end] intervals where CPython {EXPECTED_PYTHON} str.isupper() is true."
    )
    lines.append("pub let upper_intervals : Array[(Int, Int)] = [")
    for start, end in intervals:
        lines.append(f"  (0x{start:04X}, 0x{end:04X}),")
    lines.append("]")
    lines.append("")
    lines.append("///| (code, start, end) ranges of the upstream 220-entry unicode block table.")
    lines.append("pub let unicode_block_ranges : Array[(Int, Int, Int)] = [")
    for code, start, end in blocks:
        lines.append(f"  ({code}, 0x{start:04X}, 0x{end:04X}),")
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def parse_generated(path: Path) -> tuple[list[tuple[int, int]], list[tuple[int, int, int]]]:
    if not path.is_file():
        fail(f"generated table not found: {path}")
    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text else ""
    for marker in (
        "勿手改",
        f"python_version={EXPECTED_PYTHON}",
        f"unidata_version={EXPECTED_UNIDATA}",
    ):
        if marker not in first_line:
            fail(f"generated header missing {marker!r} on line 1")
    for token in ("moonbitlang/x", "unicode-data"):
        if token in text:
            fail(f"generated table references third-party Unicode package {token!r}")

    upper_match = UPPER_ARRAY_RE.search(text)
    if upper_match is None:
        fail("cannot locate pub let upper_intervals : Array[(Int, Int)]")
    block_match = BLOCK_ARRAY_RE.search(text)
    if block_match is None:
        fail("cannot locate pub let unicode_block_ranges : Array[(Int, Int, Int)]")

    intervals = [
        (int(start, 16), int(end, 16))
        for start, end in UPPER_TUPLE_RE.findall(upper_match.group(1))
    ]
    blocks = [
        (int(code), int(start, 16), int(end, 16))
        for code, start, end in BLOCK_TUPLE_RE.findall(block_match.group(1))
    ]
    if len(intervals) != EXPECTED_INTERVAL_COUNT:
        fail(f"parsed {len(intervals)} upper intervals, expected {EXPECTED_INTERVAL_COUNT}")
    if len(blocks) != EXPECTED_BLOCK_COUNT:
        fail(f"parsed {len(blocks)} block ranges, expected {EXPECTED_BLOCK_COUNT}")
    return intervals, blocks


def verify(path: Path) -> None:
    intervals, blocks = parse_generated(path)

    flags = bytearray(CP_LIMIT)
    expanded = 0
    previous_end = -2
    for start, end in intervals:
        if not (0 <= start <= end < CP_LIMIT):
            fail(f"invalid interval 0x{start:04X}..0x{end:04X}")
        if start <= previous_end + 1:
            fail("upper intervals are not maximal and disjoint")
        if start <= SURROGATE_HI and end >= SURROGATE_LO:
            fail(f"interval 0x{start:04X}..0x{end:04X} contains surrogates")
        for cp in range(start, end + 1):
            flags[cp] = 1
        expanded += end - start + 1
        previous_end = end

    true_count = 0
    diff = 0
    first_diffs: list[int] = []
    for cp in range(CP_LIMIT):
        if SURROGATE_LO <= cp <= SURROGATE_HI:
            continue
        want = chr(cp).isupper()
        if want:
            true_count += 1
        got = flags[cp] == 1
        if want != got:
            diff += 1
            if len(first_diffs) < 10:
                first_diffs.append(cp)

    if true_count != EXPECTED_CP_COUNT:
        fail(f"live isupper count is {true_count}, expected {EXPECTED_CP_COUNT}")
    if expanded != true_count:
        fail(f"table expands to {expanded} codepoints, live count is {true_count}")
    if diff != 0:
        shown = " ".join(f"0x{cp:04X}" for cp in first_diffs)
        fail(f"{diff} codepoint mismatches, first: {shown}")

    upstream_rows, upstream_lookup = upstream_block_rows()
    if blocks != upstream_rows:
        fail("generated block ranges differ from upstream _unicode_blocks")

    block_diff = 0
    first_block_diffs: list[int] = []
    for cp in range(CP_LIMIT):
        want = upstream_lookup(chr(cp))
        want = 0 if want is None else int(want)
        got = 0
        lo, hi = 0, len(blocks) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            code, start, end = blocks[mid]
            if cp < start:
                hi = mid - 1
            elif cp > end:
                lo = mid + 1
            else:
                got = code
                break
        if want != got:
            block_diff += 1
            if len(first_block_diffs) < 10:
                first_block_diffs.append(cp)

    if block_diff != 0:
        shown = " ".join(f"0x{cp:04X}" for cp in first_block_diffs)
        fail(f"{block_diff} block lookup mismatches, first: {shown}")

    print(f"ok {true_count} cps / {len(intervals)} intervals / {diff} diff")
    print(f"ok {len(blocks)} blocks / {block_diff} diff (full codepoint lookup)")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="verify a generated file instead of writing it",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_TARGET,
        help="generation target (default: src/unicode/upper_table.mbt)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="file to verify (default: --output)",
    )
    args = parser.parse_args(argv)

    check_interpreter()
    if args.verify:
        verify(args.input if args.input is not None else args.output)
        return 0

    intervals = uppercase_intervals()
    blocks, _ = upstream_block_rows()
    text = render(intervals, blocks)
    atomic_write(args.output, text)
    print(
        f"wrote {args.output} : {len(intervals)} upper intervals / "
        f"{len(blocks)} block ranges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
