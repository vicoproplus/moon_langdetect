# -*- coding: utf-8 -*-
"""取证辅助：按需重跑 langdetect 上游，输出可核验事实。

只读 langdetect/，不修改任何上游文件。
用法:
    python tools/lib_lineprobe.py <topic> [args...]

topic 与输出字段见各 probe_* 函数 docstring。所有数字均为运行时实测。
"""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "langdetect" / "langdetect" / "profiles"

# 让上游包可导入（.venv 已 pip install -e，但仓库根目录下的 `langdetect/`
# 目录名会把包遮蔽成 namespace package；任何探测都必须从仓库根之外运行，
# 或先 sys.path.insert 之后让真实包优先。这里显式使用已安装的包位置。）
SITE = ROOT / ".venv" / "Lib" / "site-packages"
if SITE.is_dir():
    if SITE.as_posix() in [p.replace("\\", "/") for p in sys.path]:
        pass
    else:
        sys.path.insert(0, str(SITE))


def upstream():
    import langdetect

    assert langdetect.__file__ and langdetect.__file__.endswith("__init__.py"), (
        "imported namespace package instead of real package: %r" % (langdetect.__file__,)
    )
    return langdetect


def prob_formula_check():
    """核对 detector_factory.add_profile 的 freq->prob 公式与 lang_profile 的字段。

    输出: p = freq / n_words[len-1]，与 word_lang_prob_map 实际值逐一比对。
    """
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    factory = DetectorFactory()
    factory.load_profile(str(PROFILE_DIR))
    langsize = len(factory.langlist)
    mismatches = 0
    max_abs_err = 0.0
    entries = 0
    zero_len_grams = 0
    for filename in sorted(os.listdir(PROFILE_DIR)):
        if filename.startswith("."):
            continue
        p = Path(PROFILE_DIR) / filename
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        index = factory.langlist.index(data["name"])
        freq = data["freq"]
        n_words = data["n_words"]
        assert set(data.keys()) == {"freq", "n_words", "name"}, sorted(data.keys())
        for word, count in freq.items():
            entries += 1
            denom = n_words[len(word) - 1]
            if denom == 0:
                zero_len_grams += 1
                expected = 0.0
            else:
                expected = 1.0 * count / denom
            actual = factory.word_lang_prob_map.get(word)
            if actual is None or actual[index] == 0.0:
                mismatches += 1
                if mismatches <= 5:
                    print("MISS", repr(word), count, denom, expected, actual is None)
            else:
                err = abs(actual[index] - expected)
                max_abs_err = max(max_abs_err, err)
    return {
        "langsize": langsize,
        "entries_checked": entries,
        "mismatches": mismatches,
        "max_abs_err": max_abs_err,
        "zero_len_grams": zero_len_grams,
    }


def profile_field_facts():
    """统计 55 个档案 JSON 的字段结构：键集合、n_words 长度、freq 键长分布、条目合计。"""
    files = sorted(p for p in PROFILE_DIR.iterdir() if p.is_file())
    key_sets = set()
    n_words_lens = set()
    gram_len_hist = {}
    entries = 0
    nwords_nonint = 0
    neg_freq = 0
    for p in files:
        data = json.loads(p.read_text(encoding="utf-8"))
        key_sets.add(tuple(sorted(data.keys())))
        nwords_nonint += sum(1 for v in data["n_words"] if not isinstance(v, int))
        n_words_lens.add(len(data["n_words"]))
        for w in data["freq"]:
            gram_len_hist[len(w)] = gram_len_hist.get(len(w), 0) + 1
            entries += 1
        neg_freq += sum(1 for v in data["freq"].values() if v < 0)
    return {
        "file_count": len(files),
        "key_sets": sorted(map(list, key_sets)),
        "n_words_lengths": sorted(n_words_lens),
        "non_int_n_words_values": nwords_nonint,
        "negative_freq_values": neg_freq,
        "gram_length_hist": dict(sorted(gram_len_hist.items())),
        "total_freq_entries": entries,
    }


def unicode_block_facts():
    """unicode_block.py 区间表结构与边界语义：条目数、连续性、端点闭合性实测。"""
    from langdetect.utils import unicode_block as ub

    blocks = ub._unicode_blocks
    n = len(blocks)
    gaps = []
    overlaps = []
    for i in range(n - 1):
        end = blocks[i][2]
        nxt_start = blocks[i + 1][1]
        if nxt_start > end + 1:
            gaps.append([end + 1, nxt_start - 1])
        elif nxt_start <= end:
            overlaps.append([blocks[i][0], blocks[i + 1][0]])
    probe = {
        "num_blocks": n,
        "NUM_BLOCKS_constant": ub.NUM_BLOCKS,
        "gaps": gaps,
        "overlaps": overlaps,
        "boundary_closed": (
            ub.unicode_block(chr(blocks[0][1])) == blocks[0][0],
            ub.unicode_block(chr(blocks[0][2])) == blocks[0][0],
            ub.unicode_block(chr(blocks[0][2] + 1)) == blocks[1][0],
        ),
        "cp_above_last_end": ub.unicode_block(chr(0x10FFFF)),
        "cp_last_block_start": ub.unicode_block(chr(0x100000)),
        "special_0x7f": ub.unicode_block(chr(0x7F)),
        "special_0x80": ub.unicode_block(chr(0x80)),
    }
    return probe


def ngram_normalize_table():
    """NGram.normalize 对各类样本字符的实测结果（file:line 表的机器核验）。"""
    from langdetect.utils.ngram import NGram

    cases = [
        "a", "z", "A", "Z", "0", "9", " ", "-", "_", "@", "#",
        "\u00a0", "\u00ab", "\u00b0", "\u00bb", "\u00e9", "\u00ff", "\u0080",
        "\u0219", "\u021b", "\u015f", "\u0163", "\u0250", "\u0300",
        "\u3000", "\u2013", "\u060c", "\u06cc", "\u064a", "\u0627",
        "\u1ea0", "\u1ea1", "\u1eff", "\u3042", "\u304b", "\u30a2",
        "\u3105", "\u31a0", "\u4e00", "\u9f62", "\uac00", "\ud7a3",
        "\U00020000", "f",
    ]
    out = {}
    for ch in cases:
        out["U+%04X" % ord(ch)] = NGram.normalize(ch)
    return {
        "LATIN1_EXCLUDED": [hex(ord(c)) for c in NGram.LATIN1_EXCLUDED],
        "N_GRAM": NGram.N_GRAM,
        "CJK_MAP_size": len(NGram.CJK_MAP),
        "CJK_CLASS_groups": len(NGram.CJK_CLASS),
        "CJK_MAP_distinct_representatives": len(set(NGram.CJK_MAP.values())),
        "CJK_MAP_self_mappings": sum(1 for k, v in NGram.CJK_MAP.items() if k == v),
        "normalize": out,
    }


def append_cleanup_demo():
    """Detector.append() 的清洗顺序与截断：URL/邮箱、越南语规范化、连续空格折叠、截断时机。"""
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    factory = DetectorFactory()
    factory.load_profile(str(PROFILE_DIR))

    cases = {
        "url_spaces": "hello https://example.com/a?b=1 world",
        "url_no_trailing_space": "hello https://example.com/abc",
        "mail": "mail me at john.doe@example.com please",
        "url_greedy_tail": "see http://a.com/x then TEXT-more",
        "double_space": "a  b\t\tc",
        "vi_normalize": "Ti\u1ebfng Vi\u1ec7t",
        "long_url_2077": "x" + "a" * 2077 + " y",
    }
    out = {}
    for name, text in cases.items():
        d = factory.create()
        d.append(text)
        out[name] = {"input_len": len(text), "text_after_append": d.text}
    # 截断时机：max_text_length 在 append 中按 min(len(text), max_text_length) 截
    d = factory.create()
    d.set_max_text_length(5)
    d.append("abcdefghij")
    out["truncate_max5"] = d.text
    d2 = factory.create()
    d2.set_max_text_length(3)
    d2.append("aaabbb")
    out["truncate_max3_head_only"] = d2.text
    return out


def unknown_and_empty():
    """['000','quirk','frozen'] 占位由 gen_golden 提供；这里只测 API 层空返回。"""
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    factory = DetectorFactory()
    factory.load_profile(str(PROFILE_DIR))
    results = {}
    for name in ["", " ", "\t\n ", "\u00e9"]:
        d = factory.create()
        d.append(name)
        try:
            results[name] = detect_one(factory, name)
        except Exception as exc:  # noqa: BLE001
            results[name] = {
                "exception": type(exc).__name__,
                "message": str(exc),
            }
    return results


def detect_one(factory, text):
    d = factory.create()
    d.append(text)
    return d.detect()


def language_sort_facts():
    """Language 排序语义：等概率时的稳定性、__lt__ 缺失其他比较。"""
    from langdetect.language import Language

    a = Language("a", 0.5)
    b = Language("b", 0.5)
    c = Language("c", 0.9)
    lst = [c, b, a]
    lst.sort(reverse=True)
    return {
        "lt_eq": a.__lt__(b),
        "has_gt": hasattr(a, "__gt__"),
        "has_eq": hasattr(a, "__eq__"),
        "repr_none": repr(Language(None, 0)),
        "repr_one": repr(Language("en", 1.0)),
        "sorted_ties_keep_input_order": [x.lang for x in lst],
    }


def urandom_uncertainty():
    """未设 seed 的实际不确定性证据：同一文本重复 detect，统计不同结果。"""
    from langdetect import detect

    texts = ["Otec matka syn.", "Ein, zwei, drei, vier", "hi", "a b c"]
    out = {}
    for t in texts:
        got = [detect(t) for _ in range(10)]
        out[t] = {"runs": got, "distinct": len(set(got))}
    return out


def constants_facts():
    """常量与默认值的运行时实测。"""
    from langdetect.detector import Detector

    c = {
        "ALPHA_DEFAULT": Detector.ALPHA_DEFAULT,
        "ALPHA_WIDTH": Detector.ALPHA_WIDTH,
        "ITERATION_LIMIT": Detector.ITERATION_LIMIT,
        "PROB_THRESHOLD": Detector.PROB_THRESHOLD,
        "CONV_THRESHOLD": Detector.CONV_THRESHOLD,
        "BASE_FREQ": Detector.BASE_FREQ,
        "UNKNOWN_LANG": Detector.UNKNOWN_LANG,
        "URL_RE_pattern": Detector.URL_RE.pattern,
        "MAIL_RE_pattern": Detector.MAIL_RE.pattern,
    }
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    f = DetectorFactory()
    f.load_profile(str(PROFILE_DIR))
    d = f.create()
    c["instance_n_trial"] = d.n_trial
    c["instance_max_text_length"] = d.max_text_length
    c["instance_alpha"] = d.alpha
    c["instance_prior_map"] = d.prior_map
    c["instance_verbose"] = d.verbose
    c["instance_seed"] = d.seed
    c["instance_random_type"] = type(d.random).__name__
    c["DetectorFactory_seed_class_attr"] = DetectorFactory.seed
    c["factory_seed_instance"] = f.seed
    c["init_prob_repr"] = d._init_probability()[:3]
    return c


PROBES = {
    "prob_formula": prob_formula_check,
    "profile_fields": profile_field_facts,
    "unicode_blocks": unicode_block_facts,
    "ngram_normalize": ngram_normalize_table,
    "append_cleanup": append_cleanup_demo,
    "empty_variants": unknown_and_empty,
    "language_sort": language_sort_facts,
    "urandom_uncertainty": urandom_uncertainty,
    "constants": constants_facts,
}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: lib_lineprobe.py <topic>")
        print("topics:", ", ".join(sorted(PROBES)))
        return 2
    topic = sys.argv[1]
    fn = PROBES[topic]
    print(json.dumps(fn(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
