///| Upstream parity for `langdetect/tests/utils/test_ngram.py` (all seven
///| test groups, adapted to the string-to-string `normalize` signature),
///| plus V-46 (`capitalword` yields exactly 10 features for "USA NASA FBI"),
///| the core constant set (V-07) and the error payload (spec §5.8).

///| Upstream `test_constants`: `NGram.N_GRAM == 3`.
test "n_gram_constant" {
  inspect(@core.N_GRAM, content="3")
}

///| Upstream `test_normalize_with_latin`: only A-Z / a-z survive in Basic
///| Latin; every other Basic Latin codepoint and the four Latin-1
///| exclusions become a space.
test "normalize_with_latin" {
  assert_eq(@core.NGram::normalize("\u{0000}"), " ")
  assert_eq(@core.NGram::normalize("\u{0009}"), " ")
  assert_eq(@core.NGram::normalize("\u{0020}"), " ")
  assert_eq(@core.NGram::normalize("\u{0030}"), " ")
  assert_eq(@core.NGram::normalize("\u{0040}"), " ")
  assert_eq(@core.NGram::normalize("\u{0041}"), "\u{0041}")
  assert_eq(@core.NGram::normalize("\u{005A}"), "\u{005A}")
  assert_eq(@core.NGram::normalize("\u{005B}"), " ")
  assert_eq(@core.NGram::normalize("\u{0060}"), " ")
  assert_eq(@core.NGram::normalize("\u{0061}"), "\u{0061}")
  assert_eq(@core.NGram::normalize("\u{007A}"), "\u{007A}")
  assert_eq(@core.NGram::normalize("\u{007B}"), " ")
  assert_eq(@core.NGram::normalize("\u{007F}"), " ")
  assert_eq(@core.NGram::normalize("\u{0080}"), "\u{0080}")
  assert_eq(@core.NGram::normalize("\u{00A0}"), " ")
  assert_eq(@core.NGram::normalize("\u{00A1}"), "\u{00A1}")
}

///| Upstream `test_normalize_with_cjk_kanji`: the canonical form of each
///| `CJK_CLASS` group is its first member; codepoints outside the map are
///| unchanged.
test "normalize_with_cjk_kanji" {
  assert_eq(@core.NGram::normalize("\u{4E00}"), "\u{4E00}")
  assert_eq(@core.NGram::normalize("\u{4E01}"), "\u{4E01}")
  assert_eq(@core.NGram::normalize("\u{4E02}"), "\u{4E02}")
  assert_eq(@core.NGram::normalize("\u{4E03}"), "\u{4E01}")
  assert_eq(@core.NGram::normalize("\u{4E04}"), "\u{4E04}")
  assert_eq(@core.NGram::normalize("\u{4E05}"), "\u{4E05}")
  assert_eq(@core.NGram::normalize("\u{4E06}"), "\u{4E06}")
  assert_eq(@core.NGram::normalize("\u{4E07}"), "\u{4E07}")
  assert_eq(@core.NGram::normalize("\u{4E08}"), "\u{4E08}")
  assert_eq(@core.NGram::normalize("\u{4E09}"), "\u{4E09}")
  assert_eq(@core.NGram::normalize("\u{4E10}"), "\u{4E10}")
  assert_eq(@core.NGram::normalize("\u{4E11}"), "\u{4E11}")
  assert_eq(@core.NGram::normalize("\u{4E12}"), "\u{4E12}")
  assert_eq(@core.NGram::normalize("\u{4E13}"), "\u{4E13}")
  assert_eq(@core.NGram::normalize("\u{4E14}"), "\u{4E14}")
  assert_eq(@core.NGram::normalize("\u{4E15}"), "\u{4E15}")
  assert_eq(@core.NGram::normalize("\u{4E1E}"), "\u{4E1E}")
  assert_eq(@core.NGram::normalize("\u{4E1F}"), "\u{4E1F}")
  assert_eq(@core.NGram::normalize("\u{4E20}"), "\u{4E20}")
  assert_eq(@core.NGram::normalize("\u{4E21}"), "\u{4E21}")
  assert_eq(@core.NGram::normalize("\u{4E22}"), "\u{4E22}")
  assert_eq(@core.NGram::normalize("\u{4E23}"), "\u{4E23}")
  assert_eq(@core.NGram::normalize("\u{4E24}"), "\u{4E13}")
  assert_eq(@core.NGram::normalize("\u{4E25}"), "\u{4E13}")
  assert_eq(@core.NGram::normalize("\u{4E30}"), "\u{4E30}")
}

///| Upstream `test_normalize_for_romanian`: comma-below s/t fold to the
///| cedilla forms; already-cedilla forms are unchanged.
test "normalize_for_romanian" {
  assert_eq(@core.NGram::normalize("\u{015F}"), "\u{015F}")
  assert_eq(@core.NGram::normalize("\u{0163}"), "\u{0163}")
  assert_eq(@core.NGram::normalize("\u{0219}"), "\u{015F}")
  assert_eq(@core.NGram::normalize("\u{021B}"), "\u{0163}")
}

///| Upstream `test_ngram`: the state machine across spaces, Arabic,
///| Latin Extended Additional, Hiragana, Katakana, Bopomofo, Hangul and
///| General Punctuation.
test "ngram" {
  let ngram = @core.NGram::new()
  assert_eq(ngram.get(0), None)
  assert_eq(ngram.get(1), None)
  assert_eq(ngram.get(2), None)
  assert_eq(ngram.get(3), None)
  assert_eq(ngram.get(4), None)
  ngram.add_char(' ')
  assert_eq(ngram.get(1), None)
  assert_eq(ngram.get(2), None)
  assert_eq(ngram.get(3), None)
  ngram.add_char('A')
  assert_eq(ngram.get(1), Some("A"))
  assert_eq(ngram.get(2), Some(" A"))
  assert_eq(ngram.get(3), None)
  ngram.add_char('\u{06CC}')
  assert_eq(ngram.get(1), Some("\u{064A}"))
  assert_eq(ngram.get(2), Some("A\u{064A}"))
  assert_eq(ngram.get(3), Some(" A\u{064A}"))
  ngram.add_char('\u{1EA0}')
  assert_eq(ngram.get(1), Some("\u{1EC3}"))
  assert_eq(ngram.get(2), Some("\u{064A}\u{1EC3}"))
  assert_eq(ngram.get(3), Some("A\u{064A}\u{1EC3}"))
  ngram.add_char('\u{3044}')
  assert_eq(ngram.get(1), Some("\u{3042}"))
  assert_eq(ngram.get(2), Some("\u{1EC3}\u{3042}"))
  assert_eq(ngram.get(3), Some("\u{064A}\u{1EC3}\u{3042}"))
  ngram.add_char('\u{30A4}')
  assert_eq(ngram.get(1), Some("\u{30A2}"))
  assert_eq(ngram.get(2), Some("\u{3042}\u{30A2}"))
  assert_eq(ngram.get(3), Some("\u{1EC3}\u{3042}\u{30A2}"))
  ngram.add_char('\u{3106}')
  assert_eq(ngram.get(1), Some("\u{3105}"))
  assert_eq(ngram.get(2), Some("\u{30A2}\u{3105}"))
  assert_eq(ngram.get(3), Some("\u{3042}\u{30A2}\u{3105}"))
  ngram.add_char('\u{AC01}')
  assert_eq(ngram.get(1), Some("\u{AC00}"))
  assert_eq(ngram.get(2), Some("\u{3105}\u{AC00}"))
  assert_eq(ngram.get(3), Some("\u{30A2}\u{3105}\u{AC00}"))
  ngram.add_char('\u{2010}')
  assert_eq(ngram.get(1), None)
  assert_eq(ngram.get(2), Some("\u{AC00} "))
  assert_eq(ngram.get(3), Some("\u{3105}\u{AC00} "))
  ngram.add_char('a')
  assert_eq(ngram.get(1), Some("a"))
  assert_eq(ngram.get(2), Some(" a"))
  assert_eq(ngram.get(3), None)
}

///| Upstream `test_ngram3`: a normalized space keeps the n=2/3 tails while
///| n=1 is suppressed.
test "ngram3" {
  let ngram = @core.NGram::new()
  ngram.add_char('A')
  assert_eq(ngram.get(1), Some("A"))
  assert_eq(ngram.get(2), Some(" A"))
  assert_eq(ngram.get(3), None)
  ngram.add_char('1')
  assert_eq(ngram.get(1), None)
  assert_eq(ngram.get(2), Some("A "))
  assert_eq(ngram.get(3), Some(" A "))
  ngram.add_char('B')
  assert_eq(ngram.get(1), Some("B"))
  assert_eq(ngram.get(2), Some(" B"))
  assert_eq(ngram.get(3), None)
}

///| Upstream `test_normalize_vietnamese`: 124 assertions (4 prelude plus
///| the full 120-entry base x mark table).
test "normalize_vietnamese" {
  assert_eq(@core.NGram::normalize_vi(""), "")
  assert_eq(@core.NGram::normalize_vi("\u{0041}\u{0042}\u{0043}"), "\u{0041}\u{0042}\u{0043}")
  assert_eq(@core.NGram::normalize_vi("\u{0030}\u{0031}\u{0032}"), "\u{0030}\u{0031}\u{0032}")
  assert_eq(@core.NGram::normalize_vi("\u{00C0}"), "\u{00C0}")
  assert_eq(@core.NGram::normalize_vi("\u{0041}\u{0300}"), "\u{00C0}")
  assert_eq(@core.NGram::normalize_vi("\u{0045}\u{0300}"), "\u{00C8}")
  assert_eq(@core.NGram::normalize_vi("\u{0049}\u{0300}"), "\u{00CC}")
  assert_eq(@core.NGram::normalize_vi("\u{004F}\u{0300}"), "\u{00D2}")
  assert_eq(@core.NGram::normalize_vi("\u{0055}\u{0300}"), "\u{00D9}")
  assert_eq(@core.NGram::normalize_vi("\u{0059}\u{0300}"), "\u{1EF2}")
  assert_eq(@core.NGram::normalize_vi("\u{0061}\u{0300}"), "\u{00E0}")
  assert_eq(@core.NGram::normalize_vi("\u{0065}\u{0300}"), "\u{00E8}")
  assert_eq(@core.NGram::normalize_vi("\u{0069}\u{0300}"), "\u{00EC}")
  assert_eq(@core.NGram::normalize_vi("\u{006F}\u{0300}"), "\u{00F2}")
  assert_eq(@core.NGram::normalize_vi("\u{0075}\u{0300}"), "\u{00F9}")
  assert_eq(@core.NGram::normalize_vi("\u{0079}\u{0300}"), "\u{1EF3}")
  assert_eq(@core.NGram::normalize_vi("\u{00C2}\u{0300}"), "\u{1EA6}")
  assert_eq(@core.NGram::normalize_vi("\u{00CA}\u{0300}"), "\u{1EC0}")
  assert_eq(@core.NGram::normalize_vi("\u{00D4}\u{0300}"), "\u{1ED2}")
  assert_eq(@core.NGram::normalize_vi("\u{00E2}\u{0300}"), "\u{1EA7}")
  assert_eq(@core.NGram::normalize_vi("\u{00EA}\u{0300}"), "\u{1EC1}")
  assert_eq(@core.NGram::normalize_vi("\u{00F4}\u{0300}"), "\u{1ED3}")
  assert_eq(@core.NGram::normalize_vi("\u{0102}\u{0300}"), "\u{1EB0}")
  assert_eq(@core.NGram::normalize_vi("\u{0103}\u{0300}"), "\u{1EB1}")
  assert_eq(@core.NGram::normalize_vi("\u{01A0}\u{0300}"), "\u{1EDC}")
  assert_eq(@core.NGram::normalize_vi("\u{01A1}\u{0300}"), "\u{1EDD}")
  assert_eq(@core.NGram::normalize_vi("\u{01AF}\u{0300}"), "\u{1EEA}")
  assert_eq(@core.NGram::normalize_vi("\u{01B0}\u{0300}"), "\u{1EEB}")
  assert_eq(@core.NGram::normalize_vi("\u{0041}\u{0301}"), "\u{00C1}")
  assert_eq(@core.NGram::normalize_vi("\u{0045}\u{0301}"), "\u{00C9}")
  assert_eq(@core.NGram::normalize_vi("\u{0049}\u{0301}"), "\u{00CD}")
  assert_eq(@core.NGram::normalize_vi("\u{004F}\u{0301}"), "\u{00D3}")
  assert_eq(@core.NGram::normalize_vi("\u{0055}\u{0301}"), "\u{00DA}")
  assert_eq(@core.NGram::normalize_vi("\u{0059}\u{0301}"), "\u{00DD}")
  assert_eq(@core.NGram::normalize_vi("\u{0061}\u{0301}"), "\u{00E1}")
  assert_eq(@core.NGram::normalize_vi("\u{0065}\u{0301}"), "\u{00E9}")
  assert_eq(@core.NGram::normalize_vi("\u{0069}\u{0301}"), "\u{00ED}")
  assert_eq(@core.NGram::normalize_vi("\u{006F}\u{0301}"), "\u{00F3}")
  assert_eq(@core.NGram::normalize_vi("\u{0075}\u{0301}"), "\u{00FA}")
  assert_eq(@core.NGram::normalize_vi("\u{0079}\u{0301}"), "\u{00FD}")
  assert_eq(@core.NGram::normalize_vi("\u{00C2}\u{0301}"), "\u{1EA4}")
  assert_eq(@core.NGram::normalize_vi("\u{00CA}\u{0301}"), "\u{1EBE}")
  assert_eq(@core.NGram::normalize_vi("\u{00D4}\u{0301}"), "\u{1ED0}")
  assert_eq(@core.NGram::normalize_vi("\u{00E2}\u{0301}"), "\u{1EA5}")
  assert_eq(@core.NGram::normalize_vi("\u{00EA}\u{0301}"), "\u{1EBF}")
  assert_eq(@core.NGram::normalize_vi("\u{00F4}\u{0301}"), "\u{1ED1}")
  assert_eq(@core.NGram::normalize_vi("\u{0102}\u{0301}"), "\u{1EAE}")
  assert_eq(@core.NGram::normalize_vi("\u{0103}\u{0301}"), "\u{1EAF}")
  assert_eq(@core.NGram::normalize_vi("\u{01A0}\u{0301}"), "\u{1EDA}")
  assert_eq(@core.NGram::normalize_vi("\u{01A1}\u{0301}"), "\u{1EDB}")
  assert_eq(@core.NGram::normalize_vi("\u{01AF}\u{0301}"), "\u{1EE8}")
  assert_eq(@core.NGram::normalize_vi("\u{01B0}\u{0301}"), "\u{1EE9}")
  assert_eq(@core.NGram::normalize_vi("\u{0041}\u{0303}"), "\u{00C3}")
  assert_eq(@core.NGram::normalize_vi("\u{0045}\u{0303}"), "\u{1EBC}")
  assert_eq(@core.NGram::normalize_vi("\u{0049}\u{0303}"), "\u{0128}")
  assert_eq(@core.NGram::normalize_vi("\u{004F}\u{0303}"), "\u{00D5}")
  assert_eq(@core.NGram::normalize_vi("\u{0055}\u{0303}"), "\u{0168}")
  assert_eq(@core.NGram::normalize_vi("\u{0059}\u{0303}"), "\u{1EF8}")
  assert_eq(@core.NGram::normalize_vi("\u{0061}\u{0303}"), "\u{00E3}")
  assert_eq(@core.NGram::normalize_vi("\u{0065}\u{0303}"), "\u{1EBD}")
  assert_eq(@core.NGram::normalize_vi("\u{0069}\u{0303}"), "\u{0129}")
  assert_eq(@core.NGram::normalize_vi("\u{006F}\u{0303}"), "\u{00F5}")
  assert_eq(@core.NGram::normalize_vi("\u{0075}\u{0303}"), "\u{0169}")
  assert_eq(@core.NGram::normalize_vi("\u{0079}\u{0303}"), "\u{1EF9}")
  assert_eq(@core.NGram::normalize_vi("\u{00C2}\u{0303}"), "\u{1EAA}")
  assert_eq(@core.NGram::normalize_vi("\u{00CA}\u{0303}"), "\u{1EC4}")
  assert_eq(@core.NGram::normalize_vi("\u{00D4}\u{0303}"), "\u{1ED6}")
  assert_eq(@core.NGram::normalize_vi("\u{00E2}\u{0303}"), "\u{1EAB}")
  assert_eq(@core.NGram::normalize_vi("\u{00EA}\u{0303}"), "\u{1EC5}")
  assert_eq(@core.NGram::normalize_vi("\u{00F4}\u{0303}"), "\u{1ED7}")
  assert_eq(@core.NGram::normalize_vi("\u{0102}\u{0303}"), "\u{1EB4}")
  assert_eq(@core.NGram::normalize_vi("\u{0103}\u{0303}"), "\u{1EB5}")
  assert_eq(@core.NGram::normalize_vi("\u{01A0}\u{0303}"), "\u{1EE0}")
  assert_eq(@core.NGram::normalize_vi("\u{01A1}\u{0303}"), "\u{1EE1}")
  assert_eq(@core.NGram::normalize_vi("\u{01AF}\u{0303}"), "\u{1EEE}")
  assert_eq(@core.NGram::normalize_vi("\u{01B0}\u{0303}"), "\u{1EEF}")
  assert_eq(@core.NGram::normalize_vi("\u{0041}\u{0309}"), "\u{1EA2}")
  assert_eq(@core.NGram::normalize_vi("\u{0045}\u{0309}"), "\u{1EBA}")
  assert_eq(@core.NGram::normalize_vi("\u{0049}\u{0309}"), "\u{1EC8}")
  assert_eq(@core.NGram::normalize_vi("\u{004F}\u{0309}"), "\u{1ECE}")
  assert_eq(@core.NGram::normalize_vi("\u{0055}\u{0309}"), "\u{1EE6}")
  assert_eq(@core.NGram::normalize_vi("\u{0059}\u{0309}"), "\u{1EF6}")
  assert_eq(@core.NGram::normalize_vi("\u{0061}\u{0309}"), "\u{1EA3}")
  assert_eq(@core.NGram::normalize_vi("\u{0065}\u{0309}"), "\u{1EBB}")
  assert_eq(@core.NGram::normalize_vi("\u{0069}\u{0309}"), "\u{1EC9}")
  assert_eq(@core.NGram::normalize_vi("\u{006F}\u{0309}"), "\u{1ECF}")
  assert_eq(@core.NGram::normalize_vi("\u{0075}\u{0309}"), "\u{1EE7}")
  assert_eq(@core.NGram::normalize_vi("\u{0079}\u{0309}"), "\u{1EF7}")
  assert_eq(@core.NGram::normalize_vi("\u{00C2}\u{0309}"), "\u{1EA8}")
  assert_eq(@core.NGram::normalize_vi("\u{00CA}\u{0309}"), "\u{1EC2}")
  assert_eq(@core.NGram::normalize_vi("\u{00D4}\u{0309}"), "\u{1ED4}")
  assert_eq(@core.NGram::normalize_vi("\u{00E2}\u{0309}"), "\u{1EA9}")
  assert_eq(@core.NGram::normalize_vi("\u{00EA}\u{0309}"), "\u{1EC3}")
  assert_eq(@core.NGram::normalize_vi("\u{00F4}\u{0309}"), "\u{1ED5}")
  assert_eq(@core.NGram::normalize_vi("\u{0102}\u{0309}"), "\u{1EB2}")
  assert_eq(@core.NGram::normalize_vi("\u{0103}\u{0309}"), "\u{1EB3}")
  assert_eq(@core.NGram::normalize_vi("\u{01A0}\u{0309}"), "\u{1EDE}")
  assert_eq(@core.NGram::normalize_vi("\u{01A1}\u{0309}"), "\u{1EDF}")
  assert_eq(@core.NGram::normalize_vi("\u{01AF}\u{0309}"), "\u{1EEC}")
  assert_eq(@core.NGram::normalize_vi("\u{01B0}\u{0309}"), "\u{1EED}")
  assert_eq(@core.NGram::normalize_vi("\u{0041}\u{0323}"), "\u{1EA0}")
  assert_eq(@core.NGram::normalize_vi("\u{0045}\u{0323}"), "\u{1EB8}")
  assert_eq(@core.NGram::normalize_vi("\u{0049}\u{0323}"), "\u{1ECA}")
  assert_eq(@core.NGram::normalize_vi("\u{004F}\u{0323}"), "\u{1ECC}")
  assert_eq(@core.NGram::normalize_vi("\u{0055}\u{0323}"), "\u{1EE4}")
  assert_eq(@core.NGram::normalize_vi("\u{0059}\u{0323}"), "\u{1EF4}")
  assert_eq(@core.NGram::normalize_vi("\u{0061}\u{0323}"), "\u{1EA1}")
  assert_eq(@core.NGram::normalize_vi("\u{0065}\u{0323}"), "\u{1EB9}")
  assert_eq(@core.NGram::normalize_vi("\u{0069}\u{0323}"), "\u{1ECB}")
  assert_eq(@core.NGram::normalize_vi("\u{006F}\u{0323}"), "\u{1ECD}")
  assert_eq(@core.NGram::normalize_vi("\u{0075}\u{0323}"), "\u{1EE5}")
  assert_eq(@core.NGram::normalize_vi("\u{0079}\u{0323}"), "\u{1EF5}")
  assert_eq(@core.NGram::normalize_vi("\u{00C2}\u{0323}"), "\u{1EAC}")
  assert_eq(@core.NGram::normalize_vi("\u{00CA}\u{0323}"), "\u{1EC6}")
  assert_eq(@core.NGram::normalize_vi("\u{00D4}\u{0323}"), "\u{1ED8}")
  assert_eq(@core.NGram::normalize_vi("\u{00E2}\u{0323}"), "\u{1EAD}")
  assert_eq(@core.NGram::normalize_vi("\u{00EA}\u{0323}"), "\u{1EC7}")
  assert_eq(@core.NGram::normalize_vi("\u{00F4}\u{0323}"), "\u{1ED9}")
  assert_eq(@core.NGram::normalize_vi("\u{0102}\u{0323}"), "\u{1EB6}")
  assert_eq(@core.NGram::normalize_vi("\u{0103}\u{0323}"), "\u{1EB7}")
  assert_eq(@core.NGram::normalize_vi("\u{01A0}\u{0323}"), "\u{1EE2}")
  assert_eq(@core.NGram::normalize_vi("\u{01A1}\u{0323}"), "\u{1EE3}")
  assert_eq(@core.NGram::normalize_vi("\u{01AF}\u{0323}"), "\u{1EF0}")
  assert_eq(@core.NGram::normalize_vi("\u{01B0}\u{0323}"), "\u{1EF1}")
}

///| V-46 (contract §10 quirk 7): a run of consecutive uppercase words
///| suppresses every feature; "USA NASA FBI" yields exactly these 10 raw
///| n-grams. The profile vocabulary filter is deliberately not applied
///| here (Task 7/8 owns it).
test "extract_ngrams_capitalword_v46" {
  assert_eq(
    @core.extract_ngrams("USA NASA FBI"),
    ["U", " U", "A ", "SA ", "N", " N", "A ", "SA ", "F", " F"],
  )
}

///| The same quirk on the smallest input from the contract: "AB" keeps
///| only the first uppercase letter's unigram and bigram.
test "extract_ngrams_capitalword_ab" {
  assert_eq(@core.extract_ngrams("AB"), ["A", " A"])
}

///| Raw extraction: every n-gram is returned in stream order, including
///| duplicates; no vocabulary is consulted.
test "extract_ngrams_raw_sequence" {
  assert_eq(@core.extract_ngrams("ab"), ["a", " a", "b", "ab", " ab"])
  assert_eq(@core.extract_ngrams(""), [])
  assert_eq(@core.extract_ngrams(" "), [])
}

///| Nine error code constants, 0..8 (spec §6).
test "error_code_constants" {
  inspect(@core.ERROR_NO_TEXT, content="0")
  inspect(@core.ERROR_FORMAT, content="1")
  inspect(@core.ERROR_FILE_LOAD, content="2")
  inspect(@core.ERROR_DUPLICATE_LANG, content="3")
  inspect(@core.ERROR_NEED_LOAD_PROFILE, content="4")
  inspect(@core.ERROR_CANT_DETECT, content="5")
  inspect(@core.ERROR_CANT_OPEN_TRAIN_DATA, content="6")
  inspect(@core.ERROR_TRAIN_DATA_FORMAT, content="7")
  inspect(@core.ERROR_INIT_PARAM, content="8")
}

///| The 10 upstream constants (spec §1.2 V-07) with exact values.
test "detector_constants" {
  assert_eq(@core.ALPHA_DEFAULT, 0.5)
  assert_eq(@core.ALPHA_WIDTH, 0.05)
  assert_eq(@core.ITERATION_LIMIT, 1000)
  assert_eq(@core.PROB_THRESHOLD, 0.1)
  assert_eq(@core.CONV_THRESHOLD, 0.99999)
  assert_eq(@core.BASE_FREQ, 10000)
  assert_eq(@core.UNKNOWN_LANG, "unknown")
  assert_eq(@core.seed, (None : Int64?))
  assert_eq(@core.n_trial, 7)
  assert_eq(@core.max_text_length, 10000)
}

///| The error payload is constructible and readable with the exact
///| four labels of spec §5.8; the raised code survives a catch.
fn raise_cant_detect(
  code : Int,
  message : String,
  input_len : Int,
  input_prefix : String,
) -> Unit raise @core.LangDetectError {
  raise CantDetect(
    code=code,
    message=message,
    input_len=input_len,
    input_prefix=input_prefix,
  )
}

///| Raise/catch helper: all four fields round-trip.
test "error_payload_fields" {
  let mut seen_code = -1
  let mut seen_message = ""
  let mut seen_len = -1
  let mut seen_prefix = ""
  try {
    raise_cant_detect(@core.ERROR_CANT_DETECT, "No features in text.", 3, "abc")
  } catch {
    CantDetect(code~, message~, input_len~, input_prefix~) => {
      seen_code = code
      seen_message = message
      seen_len = input_len
      seen_prefix = input_prefix
    }
  }
  assert_eq(seen_code, 5)
  assert_eq(seen_message, "No features in text.")
  assert_eq(seen_len, 3)
  assert_eq(seen_prefix, "abc")
}
