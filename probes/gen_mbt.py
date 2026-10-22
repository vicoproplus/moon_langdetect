#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 langdetect 档案转成 MoonBit 常量数据（探针用，不含业务逻辑）。

两种编码:
  map  : Map[String, Int]，每语言一个字面量 Map，直接可查
  flat : 每语言一个扁平字符串 "key\\tcount\\n..."，运行时 split 解析

用法:
  python probes/gen_mbt.py --mode map  --langs so
  python probes/gen_mbt.py --mode map  --langs so,sw,tl,af,en
  python probes/gen_mbt.py --mode map  --langs all
  python probes/gen_mbt.py --mode flat --langs all
  python probes/gen_mbt.py --mode map  --langs all --out-dir probes/embed-probe/lib/data

输出(覆盖):
  <out-dir>/data.mbt        数据与访问 API
  probes/embed-probe/embed-probe_test.mbt  逐语言断言
  probes/gen-manifest.json  本次生成的期望条目数与字节数
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "langdetect" / "langdetect" / "profiles"
DEFAULT_OUT = ROOT / "probes" / "embed-probe" / "lib" / "data"
TEST_FILE = ROOT / "probes" / "embed-probe" / "embed-probe_test.mbt"
MANIFEST = ROOT / "probes" / "gen-manifest.json"

SCALE_5 = ["so", "sw", "tl", "af", "en"]


def ident(lang: str) -> str:
    """zh-cn -> zh_cn；其余原样。"""
    return lang.replace("-", "_")


def load(lang: str) -> dict[str, int]:
    path = PROFILE_DIR / lang
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj["freq"]


def mbt_str(s: str) -> str:
    """生成 MoonBit 字符串字面量。档案键已确认不含 " \\ 与控制字符，这里仍做转义兜底。"""
    out = ['"']
    for ch in s:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif code < 0x20:
            out.append(f"\\u{{{code:x}}}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def gen_map(langs: list[str], data: dict[str, dict[str, int]]) -> list[str]:
    lines = [
        "// 由 probes/gen_mbt.py 生成，勿手改。编码: map",
        "",
        f"pub let languages : Array[String] = [{', '.join(mbt_str(l) for l in langs)}]",
        "",
    ]
    for lang in langs:
        freq = data[lang]
        lines.append(f"let {ident(lang)} : Map[String, Int] = Map::from_array([")
        for key, count in freq.items():
            lines.append(f"  ({mbt_str(key)}, {count}),")
        lines.append("])")
        lines.append("")
    lines.append("fn raw(lang : String) -> Map[String, Int]? {")
    lines.append("  match lang {")
    for lang in langs:
        lines.append(f'    {mbt_str(lang)} => Some({ident(lang)})')
    lines.append("    _ => None")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("pub fn profile(lang : String) -> Map[String, Int]? raise {")
    lines.append("  raw(lang)")
    lines.append("}")
    lines.append("")
    lines.append("pub fn entry_count(lang : String) -> Int raise {")
    lines.append("  match raw(lang) {")
    lines.append("    Some(m) => m.length()")
    lines.append("    None => -1")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    return lines


def gen_flat(langs: list[str], data: dict[str, dict[str, int]]) -> list[str]:
    lines = [
        "// 由 probes/gen_mbt.py 生成，勿手改。编码: flat（key\\tcount\\n）",
        "",
        f"pub let languages : Array[String] = [{', '.join(mbt_str(l) for l in langs)}]",
        "",
    ]
    for lang in langs:
        freq = data[lang]
        payload = "".join(f"{k}\t{v}\n" for k, v in freq.items())
        lines.append(f"let {ident(lang)} : String = {mbt_str(payload)}")
        lines.append("")
    lines.append("fn raw_text(lang : String) -> String? {")
    lines.append("  match lang {")
    for lang in langs:
        lines.append(f'    {mbt_str(lang)} => Some({ident(lang)})')
    lines.append("    _ => None")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("pub fn profile(lang : String) -> Map[String, Int]? raise {")
    lines.append("  let text = match raw_text(lang) {")
    lines.append("    Some(t) => t")
    lines.append("    None => return None")
    lines.append("  }")
    lines.append("  let out : Map[String, Int] = Map([])")
    lines.append("  for line in text.split(\"\\n\") {")
    lines.append("    if line.length() > 0 {")
    lines.append("      let parts = line.split(\"\\t\").collect()")
    lines.append("      out[parts[0].to_owned()] = @string.parse_int(parts[1])")
    lines.append("    }")
    lines.append("  }")
    lines.append("  Some(out)")
    lines.append("}")
    lines.append("")
    lines.append("pub fn entry_count(lang : String) -> Int raise {")
    lines.append("  match profile(lang) {")
    lines.append("    Some(m) => m.length()")
    lines.append("    None => -1")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    return lines


def gen_test(langs: list[str], data: dict[str, dict[str, int]]) -> str:
    lines = ["// 由 probes/gen_mbt.py 生成，勿手改。", ""]
    for lang in langs:
        freq = data[lang]
        sample_key, sample_count = next(iter(freq.items()))
        lines.append(f'test "entries {lang}" {{')
        lines.append(f'  assert_eq(@data.entry_count({mbt_str(lang)}), {len(freq)})')
        lines.append("  let m = match @data.profile(" + mbt_str(lang) + ") {")
        lines.append("    Some(m) => m")
        lines.append('    None => abort("missing profile")')
        lines.append("  }")
        lines.append(f"  assert_eq(m.length(), {len(freq)})")
        lines.append(f"  assert_eq(m.get({mbt_str(sample_key)}), Some({sample_count}))")
        lines.append("}")
        lines.append("")
    lines.append('test "language count" {')
    lines.append(f"  assert_eq(@data.languages.length(), {len(langs)})")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["map", "flat"], required=True)
    ap.add_argument("--langs", default="all")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    available = sorted(p.name for p in PROFILE_DIR.iterdir() if p.is_file())
    if args.langs == "all":
        langs = available
    elif args.langs == "5":
        langs = SCALE_5
    elif args.langs == "1":
        langs = ["so"]
    else:
        langs = args.langs.split(",")
        missing = [l for l in langs if l not in available]
        if missing:
            raise SystemExit(f"未知语言: {missing}")

    data = {lang: load(lang) for lang in langs}
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    lines = gen_map(langs, data) if args.mode == "map" else gen_flat(langs, data)
    src = "\n".join(lines)
    data_file = out_dir / "data.mbt"
    data_file.write_text(src, encoding="utf-8")
    TEST_FILE.write_text(gen_test(langs, data), encoding="utf-8")
    elapsed = time.time() - started

    total_entries = sum(len(v) for v in data.values())
    manifest = {
        "mode": args.mode,
        "langs": langs,
        "languages": len(langs),
        "entries": total_entries,
        "data_mbt_bytes": data_file.stat().st_size,
        "test_mbt_bytes": TEST_FILE.stat().st_size,
        "gen_seconds": round(elapsed, 3),
        "per_language": {l: len(data[l]) for l in langs},
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "per_language"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
