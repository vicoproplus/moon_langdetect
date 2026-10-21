#!/usr/bin/env python3
"""Generate the embedded profile data for `src/data`.

Reads the 55 upstream JSON profiles (sorted by filename, which is also the
golden `meta.langlist` order) and emits one flat MoonBit string per language:
`key\\tcount\\n` repeated for every `freq` entry, preserving the upstream
insertion order. The generated module also exposes `languages` and a
`profiles_flat()` assembler so callers never have to read files at runtime.

Only the flat encoding is produced (convention A, mode = "flat"). The output
is deterministic (no timestamps, LF line endings, sorted languages) and is
written atomically (temp file in the destination directory + replace).
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "langdetect" / "langdetect" / "profiles"
DEFAULT_OUT = ROOT / "src" / "data" / "profiles.mbt"

EXPECTED_LANGS = 55
EXPECTED_ENTRIES = 184129
MODE = "flat"
HEADER = (
    "// 由 tools/gen_profile_data.py 生成，勿手改。"
    "编码: flat（key\\tcount\\n）"
)


def iter_profiles():
    """Yield `(name, freq_items)` in golden order (sorted profile filenames)."""
    names = sorted(
        entry.name
        for entry in PROFILES_DIR.iterdir()
        if entry.is_file() and not entry.name.startswith(".")
    )
    if len(names) != EXPECTED_LANGS:
        raise SystemExit(
            f"expected {EXPECTED_LANGS} profiles in {PROFILES_DIR}, "
            f"found {len(names)}"
        )
    for filename in names:
        path = PROFILES_DIR / filename
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        name = data["name"]
        if name != filename:
            raise SystemExit(
                f"profile name {name!r} does not match filename {filename!r}"
            )
        freq = data["freq"]
        if not isinstance(freq, dict):
            raise SystemExit(f"{filename}: freq is not an object")
        items = []
        for key, count in freq.items():
            if not key:
                raise SystemExit(f"{filename}: empty n-gram key")
            if "\t" in key or "\n" in key or "\r" in key:
                raise SystemExit(f"{filename}: key contains a delimiter: {key!r}")
            if len(key) > 3:
                raise SystemExit(f"{filename}: key longer than 3 codepoints: {key!r}")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise SystemExit(f"{filename}: invalid count for {key!r}: {count!r}")
            items.append((key, count))
        yield name, items


def escape_moonbit(text: str) -> str:
    """Escape a string for a MoonBit `"..."` literal.

    Backslashes are escaped first; tabs and newlines become their MoonBit
    escape sequences. Other characters are emitted as raw UTF-8.
    """
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\t", "\\t")
        .replace("\n", "\\n")
    )


def render() -> tuple[str, int]:
    """Render the full generated module and return `(text, entry_count)`."""
    names = []
    bodies = []
    counts = []
    entries = 0
    for name, items in iter_profiles():
        names.append(name)
        body = "".join(f"{key}\t{count}\n" for key, count in items)
        bodies.append(body)
        counts.append(len(items))
        entries += len(items)
    if entries != EXPECTED_ENTRIES:
        raise SystemExit(
            f"expected {EXPECTED_ENTRIES} profile entries, found {entries}"
        )

    lines = [
        HEADER,
        "",
        "///| Language codes in embedded profile order (sorted profile filenames,",
        "///| identical to the golden `meta.langlist` order).",
        "pub let languages : Array[String] = ["
        + ", ".join(f'"{name}"' for name in names)
        + "]",
        "",
    ]
    for name, body, count in zip(names, bodies, counts):
        ident = name.replace("-", "_")
        lines.append(
            f"///| Flat `key<TAB>count<NL>` body for `{name}` "
            f"({count} entries, upstream insertion order)."
        )
        lines.append(f'let {ident} : String = "{escape_moonbit(body)}"')
        lines.append("")
    lines.append(
        "///| Concatenate the embedded profile bodies into the multi-profile blob"
    )
    lines.append(
        "///| consumed by `parse_profiles`: one `#<lang>` header per profile,"
    )
    lines.append("///| followed by its flat `key<TAB>count<NL>` body.")
    lines.append("pub fn profiles_flat() -> String {")
    lines.append("  let buf = StringBuilder()")
    for name in names:
        ident = name.replace("-", "_")
        lines.append(f'  buf.write_string("#{name}\\n")')
        lines.append(f"  buf.write_string({ident})")
    lines.append("  buf.to_string()")
    lines.append("}")
    return "\n".join(lines) + "\n", entries


def write_atomic(path: Path, text: str) -> None:
    """Write `text` to `path` atomically with LF endings and UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"output path (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()

    text, entries = render()
    out = args.out
    write_atomic(out, text)
    size = out.stat().st_size
    print(f"mode={MODE}")
    print(f"profiles={EXPECTED_LANGS} entries={entries}")
    print(f"wrote {out} : {size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
