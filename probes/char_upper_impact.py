# -*- coding: utf-8 -*-
"""量化 75 个 isupper 不一致码点对上游 detect_langs 的真实影响。

原理：真实上游 langdetect 只读，自己改不了 isupper；因此用 monkeypatch
`NGram.add_char` 里的 `ch.isupper()` 判定来模拟「MoonBit Unicode 18 口径」，
对比两种口径跑出的 detect_langs 概率位型。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe probes/char_upper_impact.py

产出:
    docs/port/golden/char_upper_impact.json
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG_PARENT = ROOT / "langdetect"
OUT = ROOT / "docs" / "port" / "golden" / "char_upper_impact.json"


def bits(x: float) -> str:
    return struct.pack(">d", x).hex()


def main() -> int:
    if str(PKG_PARENT) not in sys.path:
        sys.path.insert(0, str(PKG_PARENT))
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY
    from langdetect.utils.ngram import NGram

    report = json.loads(
        (ROOT / "docs" / "port" / "golden" / "char_isupper_compare.json").read_text(encoding="utf-8")
    )
    extra = [int(x["cp"], 16) for x in report["point_mismatches_all"]]
    extra_set = set(extra)

    factory = DetectorFactory()
    factory.load_profile(str(PROFILES_DIRECTORY))
    word_map = factory.word_lang_prob_map

    orig_normalize = NGram.normalize
    orig_get = NGram.get

    def make_detector(seed: int, moonbit_semantics: bool):
        f = DetectorFactory()
        f.langlist = list(factory.langlist)
        f.word_lang_prob_map = word_map
        f.seed = seed
        d = f.create()
        if moonbit_semantics:
            # 复刻上游 add_char，但 isupper 判定改成「Python isupper 或属于 Unicode18 新增大写集」
            def add_char(self, ch):
                ch = self.normalize(ch)
                last = self.grams[-1]
                if last == " ":
                    self.grams = " "
                    self.capitalword = False
                    if ch == " ":
                        return
                elif len(self.grams) >= self.N_GRAM:
                    self.grams = self.grams[1:]
                self.grams += ch

                def up(c):
                    return c.isupper() or ord(c) in extra_set

                if up(ch):
                    if up(last):
                        self.capitalword = True
                else:
                    self.capitalword = False

            NGram.add_char = add_char
        else:
            NGram.add_char = orig_ngram_add_char
        return d

    # 保留原始 add_char
    orig_ngram_add_char = NGram.add_char

    tje = chr(0x1C89)  # Unicode 16 新增 Lu；Python 3.12 的 unicodedata 15.0 视为 Cn
    garay = chr(0x10D50)
    texts = {
        "plain_af": "Die woordeboek is 'n versameling van woorde wat in 'n taal gebruik word.",
        "with_tje": f"Die {tje}{tje}{tje} woordeboek is 'n versameling van woede wat gebruik word.",
        "only_tje": f"{tje}{tje}",
        "with_garay": f"Garay {garay}{garay} text sample",
        "rep_A_tje": "A" + tje + "A " * 40,
        "rep_THE_tje": ("THE " + tje + "QUICK BROWN FOX ") * 10,
        "rep_plain_repeat": ("Hello world this is a test " * 5) + (" " + tje + " ") * 10,
    }

    def run(text, moonbit_semantics):
        d = make_detector(0, moonbit_semantics)
        d.append(text)
        try:
            d._detect_block()
        except Exception as e:  # noqa: BLE001
            return {"error": type(e).__name__}
        finally:
            NGram.add_char = orig_ngram_add_char
            NGram.normalize = orig_normalize
            NGram.get = orig_get
        return [{"lang": p.lang, "prob": bits(p.prob)} for p in d.get_probabilities()]

    results = {}
    for name, text in texts.items():
        py = run(text, False)
        mb = run(text, True)
        results[name] = {
            "text": text,
            "python_semantics": py,
            "moonbit_semantics": mb,
            "identical": py == mb,
        }

    changed = [k for k, v in results.items() if not v["identical"]]
    payload = {
        "generator": "probes/char_upper_impact.py",
        "note": (
            "用 monkeypatch NGram.add_char 的 isupper 判定模拟 Unicode18 口径，"
            "对同文本跑真实上游 _detect_block，比较 detect_langs 概率位型。"
            "75 个不一致码点全部来自 point_mismatches_all。"
        ),
        "extra_uppercase_count": len(extra),
        "cases_identical": sum(1 for v in results.values() if v["identical"]),
        "cases_total": len(results),
        "cases_changed": changed,
        "results": results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for name, v in results.items():
        print(f"{name:12s} identical={v['identical']}")
        if not v["identical"]:
            print(f"   python : {v['python_semantics']}")
            print(f"   moonbit: {v['moonbit_semantics']}")
    print(f"changed: {len(changed)}/{len(results)}")
    print("->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
