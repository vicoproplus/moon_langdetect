#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate `src/core/ngram_tables.mbt` from the repository upstream copy.

Upstream source: `langdetect/langdetect/utils/ngram.py:64-260` plus the block
codes of `langdetect/langdetect/utils/unicode_block.py`. The generated file
carries the data-only part of the port:

  * the 12 `UNICODE_*` block constants used by `NGram.normalize`
    (Bopomofo and Bopomofo Extended share one arm);
  * `latin1_excluded` = upstream `NGram.LATIN1_EXCLUDED`;
  * `cjk_pairs` : the 6667 `(codepoint, replacement)` pairs of
    `NGram.CJK_MAP`, sorted by codepoint for binary search (no `Map`,
    spec DR5);
  * `vi_triples` : the 120 `(base, mark, replacement)` triples derived from
    `TO_NORMALIZE_VI_CHARS` / `DMARK_CLASS` / `NORMALIZED_VI_CHARS`,
    sorted by `(base, mark)` for binary search.

Usage (from the repository root):

    .venv/Scripts/python.exe tools/gen_core_tables.py
    .venv/Scripts/python.exe tools/gen_core_tables.py --verify

`--verify` parses the generated file (it does not re-derive it) and checks:

  * 12 block constants in the file == the 12 names imported by upstream
    `ngram.py`, with the values of upstream `unicode_block.py`;
  * 11 normalize arms counted from the upstream `ngram.py` source
    (`block ==` / `block in` comparisons);
  * `CJK_CLASS` length 126 and `CJK_MAP` length 6667;
  * every generated CJK pair equals upstream `CJK_MAP`;
  * every generated VI triple equals the upstream derived mapping;
  * `latin1_excluded` equals upstream `NGram.LATIN1_EXCLUDED`.

It prints `ok 12 blocks / 11 arms / 126 groups / 6667 keys` and exits 0 on
success, 1 on any mismatch. `--input` exists only so a scratch copy can be
tampered with to prove the verification fails.

The output is deterministic: no timestamps, fixed sort order, LF line
endings, atomic replace (temp file in the target directory + `os.replace`).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = ROOT / "src" / "core" / "ngram_tables.mbt"
UPSTREAM_PACKAGE_ROOT = ROOT / "langdetect"
NGram_SOURCE = ROOT / "langdetect" / "langdetect" / "utils" / "ngram.py"

EXPECTED_BLOCKS = 12
EXPECTED_ARMS = 11
EXPECTED_CJK_GROUPS = 126
EXPECTED_CJK_KEYS = 6667
EXPECTED_VI_TRIPLES = 120

BLOCK_CONSTANT_RE = re.compile(r"pub const (UNICODE_[A-Z0-9_]+)\s*:\s*Int\s*=\s*(\d+)")
CJK_ARRAY_RE = re.compile(
    r"pub let cjk_pairs\s*:\s*Array\[\s*\(\s*Int\s*,\s*Int\s*\)\s*\]"
    r"\s*=\s*\[\n(.*?)\n\]",
    re.S,
)
CJK_TUPLE_RE = re.compile(r"\(\s*0x([0-9A-Fa-f]+)\s*,\s*0x([0-9A-Fa-f]+)\s*\)")
VI_ARRAY_RE = re.compile(
    r"pub let vi_triples\s*:\s*Array\[\s*\(\s*Int\s*,\s*Int\s*,\s*Int\s*\)\s*\]"
    r"\s*=\s*\[\n(.*?)\n\]",
    re.S,
)
VI_TUPLE_RE = re.compile(
    r"\(\s*0x([0-9A-Fa-f]+)\s*,\s*0x([0-9A-Fa-f]+)\s*,\s*0x([0-9A-Fa-f]+)\s*\)"
)
LATIN1_RE = re.compile(r'pub let latin1_excluded\s*:\s*String\s*=\s*"((?:\\u\{[0-9A-Fa-f]+\}|[^"\\])*)"')
UNICODE_ESCAPE_RE = re.compile(r"\\u\{([0-9A-Fa-f]+)\}")


def fail(message: str) -> NoReturn:
    print("error: " + message, file=sys.stderr)
    raise SystemExit(1)


def upstream_ngram() -> type:
    """Import `NGram` from the repository upstream copy (tool-side only)."""
    package_root = str(UPSTREAM_PACKAGE_ROOT)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    try:
        from langdetect.utils.ngram import NGram  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - environment error
        fail(f"cannot import upstream NGram: {exc}")
    return NGram


def upstream_unicode_block_module():
    package_root = str(UPSTREAM_PACKAGE_ROOT)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    try:
        from langdetect.utils import unicode_block  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - environment error
        fail(f"cannot import upstream unicode_block: {exc}")
    return unicode_block


def upstream_block_names() -> list[str]:
    """The 12 `UNICODE_*` names referenced by upstream `ngram.py`."""
    text = NGram_SOURCE.read_text(encoding="utf-8")
    names = sorted(set(re.findall(r"UNICODE_[A-Z0-9_]+", text)))
    if len(names) != EXPECTED_BLOCKS:
        fail(f"upstream ngram.py references {len(names)} block constants, expected {EXPECTED_BLOCKS}")
    return names


def upstream_arm_count() -> int:
    """Count the `block ==` / `block in` comparison arms in upstream source."""
    text = NGram_SOURCE.read_text(encoding="utf-8")
    equal_arms = text.count("block ==")
    membership_arms = len(re.findall(r"block in\b", text))
    return equal_arms + membership_arms


def expected_blocks() -> dict[str, int]:
    module = upstream_unicode_block_module()
    values: dict[str, int] = {}
    for name in upstream_block_names():
        value = getattr(module, name, None)
        if not isinstance(value, int):
            fail(f"upstream unicode_block.py has no integer constant {name}")
        values[name] = value
    return values


def expected_cjk_pairs(NGram: type) -> list[tuple[int, int]]:
    class_length = len(NGram.CJK_CLASS)
    map_length = len(NGram.CJK_MAP)
    if class_length != EXPECTED_CJK_GROUPS:
        fail(f"upstream CJK_CLASS has {class_length} groups, expected {EXPECTED_CJK_GROUPS}")
    if map_length != EXPECTED_CJK_KEYS:
        fail(f"upstream CJK_MAP has {map_length} keys, expected {EXPECTED_CJK_KEYS}")
    pairs = sorted((ord(ch), ord(replacement)) for ch, replacement in NGram.CJK_MAP.items())
    if len(pairs) != EXPECTED_CJK_KEYS:
        fail(f"derived {len(pairs)} CJK pairs, expected {EXPECTED_CJK_KEYS}")
    for ch in NGram.CJK_MAP:
        if len(ch) != 1:
            fail(f"upstream CJK_MAP key is not one codepoint: {ch!r}")
    return pairs


def expected_vi_triples(NGram: type) -> list[tuple[int, int, int]]:
    bases = NGram.TO_NORMALIZE_VI_CHARS
    marks = NGram.DMARK_CLASS
    rows = NGram.NORMALIZED_VI_CHARS
    if len(marks) != len(rows):
        fail(f"upstream has {len(marks)} marks but {len(rows)} replacement rows")
    triples: list[tuple[int, int, int]] = []
    for row_index, row in enumerate(rows):
        if len(row) != len(bases):
            fail(
                f"upstream NORMALIZED_VI_CHARS row {row_index} has {len(row)} chars, "
                f"expected {len(bases)}"
            )
        for base_index, base in enumerate(bases):
            triples.append((ord(base), ord(marks[row_index]), ord(row[base_index])))
    if len(triples) != EXPECTED_VI_TRIPLES:
        fail(f"derived {len(triples)} VI triples, expected {EXPECTED_VI_TRIPLES}")
    triples.sort()
    return triples


def moonbit_unicode_escapes(text: str) -> str:
    return "".join(f"\\u{{{ord(ch):04X}}}" for ch in text)


def render(
    blocks: dict[str, int],
    latin1_excluded: str,
    cjk_pairs: list[tuple[int, int]],
    vi_triples: list[tuple[int, int, int]],
) -> str:
    lines: list[str] = []
    lines.append(
        "// 由 tools/gen_core_tables.py 生成，勿手改。来源: langdetect 1.0.9 "
        "ngram.py:64-260 + unicode_block.py 常量。"
    )
    lines.append(
        f"// Counts: {len(blocks)} block constants / {EXPECTED_ARMS} normalize arms / "
        f"{EXPECTED_CJK_GROUPS} CJK groups -> {len(cjk_pairs)} CJK keys / "
        f"{len(vi_triples)} VI triples."
    )
    lines.append(
        "// Both pair arrays are sorted for binary search: cjk_pairs by codepoint, "
        "vi_triples by (base, mark)."
    )
    lines.append("")
    for name in sorted(blocks):
        lines.append(f"pub const {name} : Int = {blocks[name]}")
    lines.append("")
    lines.append(
        "///| Upstream `NGram.LATIN1_EXCLUDED` (NBSP, left guillemet, degree, right guillemet)."
    )
    lines.append(f'pub let latin1_excluded : String = "{moonbit_unicode_escapes(latin1_excluded)}"')
    lines.append("")
    lines.append(
        "///| `NGram.CJK_MAP` as sorted `(codepoint, replacement)` pairs "
        f"({len(cjk_pairs)} entries)."
    )
    lines.append("pub let cjk_pairs : Array[(Int, Int)] = [")
    for codepoint, replacement in cjk_pairs:
        lines.append(f"  (0x{codepoint:04X}, 0x{replacement:04X}),")
    lines.append("]")
    lines.append("")
    lines.append(
        "///| Vietnamese `(base, mark, replacement)` triples as sorted "
        f"`(base, mark, replacement)` tuples ({len(vi_triples)} entries)."
    )
    lines.append("pub let vi_triples : Array[(Int, Int, Int)] = [")
    for base, mark, replacement in vi_triples:
        lines.append(f"  (0x{base:04X}, 0x{mark:04X}, 0x{replacement:04X}),")
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


def decode_moonbit_escapes(body: str) -> str:
    """Decode a generated literal made only of `\\u{XXXX}` escapes and literals."""
    out: list[str] = []
    index = 0
    while index < len(body):
        match = UNICODE_ESCAPE_RE.match(body, index)
        if match is not None:
            out.append(chr(int(match.group(1), 16)))
            index = match.end()
        else:
            out.append(body[index])
            index += 1
    return "".join(out)


def parse_generated(
    path: Path,
) -> tuple[dict[str, int], str, list[tuple[int, int]], list[tuple[int, int, int]]]:
    if not path.is_file():
        fail(f"generated table not found: {path}")
    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text else ""
    if "勿手改" not in first_line:
        fail("generated header missing 勿手改 on line 1")
    for token in ("moonbitlang/x", "unicode-data", "Map::from_array"):
        if token in text:
            fail(f"generated table contains forbidden token {token!r}")

    blocks = {name: int(value) for name, value in BLOCK_CONSTANT_RE.findall(text)}
    if len(blocks) != EXPECTED_BLOCKS:
        fail(f"parsed {len(blocks)} block constants, expected {EXPECTED_BLOCKS}")

    latin1_match = LATIN1_RE.search(text)
    if latin1_match is None:
        fail("cannot locate pub let latin1_excluded : String")
    latin1_excluded = decode_moonbit_escapes(latin1_match.group(1))

    cjk_match = CJK_ARRAY_RE.search(text)
    if cjk_match is None:
        fail("cannot locate pub let cjk_pairs : Array[(Int, Int)]")
    cjk_pairs = [
        (int(codepoint, 16), int(replacement, 16))
        for codepoint, replacement in CJK_TUPLE_RE.findall(cjk_match.group(1))
    ]
    if len(cjk_pairs) != EXPECTED_CJK_KEYS:
        fail(f"parsed {len(cjk_pairs)} CJK pairs, expected {EXPECTED_CJK_KEYS}")

    vi_match = VI_ARRAY_RE.search(text)
    if vi_match is None:
        fail("cannot locate pub let vi_triples : Array[(Int, Int, Int)]")
    vi_triples = [
        (int(base, 16), int(mark, 16), int(replacement, 16))
        for base, mark, replacement in VI_TUPLE_RE.findall(vi_match.group(1))
    ]
    if len(vi_triples) != EXPECTED_VI_TRIPLES:
        fail(f"parsed {len(vi_triples)} VI triples, expected {EXPECTED_VI_TRIPLES}")
    return blocks, latin1_excluded, cjk_pairs, vi_triples


def check_sorted_ints(values: list[tuple[int, ...]], label: str) -> None:
    for previous, current in zip(values, values[1:]):
        if not previous < current:
            fail(f"{label} is not sorted strictly ascending at {previous!r} -> {current!r}")


def verify(path: Path) -> None:
    blocks, latin1_excluded, cjk_pairs, vi_triples = parse_generated(path)
    NGram = upstream_ngram()

    arms = upstream_arm_count()
    if arms != EXPECTED_ARMS:
        fail(f"upstream ngram.py has {arms} normalize arms, expected {EXPECTED_ARMS}")

    want_blocks = expected_blocks()
    if set(blocks) != set(want_blocks):
        missing = sorted(set(want_blocks) - set(blocks))
        extra = sorted(set(blocks) - set(want_blocks))
        fail(f"block constant names differ (missing {missing}, extra {extra})")
    for name in sorted(want_blocks):
        if blocks[name] != want_blocks[name]:
            fail(f"block {name} = {blocks[name]}, upstream is {want_blocks[name]}")

    want_latin1 = NGram.LATIN1_EXCLUDED
    if latin1_excluded != want_latin1:
        fail(f"latin1_excluded = {latin1_excluded!r}, upstream is {want_latin1!r}")

    check_sorted_ints(cjk_pairs, "cjk_pairs")
    want_cjk = expected_cjk_pairs(NGram)
    if cjk_pairs != want_cjk:
        for got, want in zip(cjk_pairs, want_cjk):
            if got != want:
                fail(f"CJK pair mismatch: generated {got!r}, upstream {want!r}")
        fail("CJK pair list length differs from upstream (unreachable)")

    check_sorted_ints(vi_triples, "vi_triples")
    want_vi = expected_vi_triples(NGram)
    if vi_triples != want_vi:
        for got, want in zip(vi_triples, want_vi):
            if got != want:
                fail(f"VI triple mismatch: generated {got!r}, upstream {want!r}")
        fail("VI triple list length differs from upstream (unreachable)")

    if len(NGram.CJK_CLASS) != EXPECTED_CJK_GROUPS or len(NGram.CJK_MAP) != EXPECTED_CJK_KEYS:
        fail("upstream CJK table sizes changed")

    print(
        f"ok {len(blocks)} blocks / {arms} arms / "
        f"{len(NGram.CJK_CLASS)} groups / {len(NGram.CJK_MAP)} keys"
    )
    print(
        f"ok {len(vi_triples)} vi triples / {len(latin1_excluded)} latin1 excluded / 0 diff"
    )


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
        help="generation target (default: src/core/ngram_tables.mbt)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="file to verify (default: --output)",
    )
    args = parser.parse_args(argv)

    if args.verify:
        verify(args.input if args.input is not None else args.output)
        return 0

    NGram = upstream_ngram()
    blocks = expected_blocks()
    cjk_pairs = expected_cjk_pairs(NGram)
    vi_triples = expected_vi_triples(NGram)
    text = render(blocks, NGram.LATIN1_EXCLUDED, cjk_pairs, vi_triples)
    atomic_write(args.output, text)
    print(
        f"wrote {args.output} : {len(blocks)} block constants / "
        f"{len(cjk_pairs)} CJK pairs / {len(vi_triples)} VI triples"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
