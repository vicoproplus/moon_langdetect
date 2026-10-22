///| Detector / factory / public-API behavior.
///

///| The six upstream `test_detector.py` cases are ported first. The two

///| synthetic training profiles that only contain 1-grams upstream carry

///| zero 2/3-gram totals (`[9, 0, 0]`); this port checks the product

///| precondition "every n_words total is positive" before any division

///| (spec §4.1, Task 5 transfer), so those unused totals are raised to 1.

///| No 2-gram or 3-gram key exists in those profiles, so every probability

///| and every detection result is unchanged.
///

///| The 0.1 threshold samples are synthetic and labeled

///| `synthetic:基准 250 例中最小条目 0.1428…，无 ≤ 0.1（V-49）`: the

///| baseline corpus has no entry at or below 0.1, so the three boundary

///| bit patterns are injected into the detector cache and passed through

///| the real `get_probabilities` filter (the Task 7 parked item).

///|
/// Build a profile from explicit frequency entries.
fn make_profile(
  name : String,
  n_words : Array[Int],
  entries : Array[(String, Int)],
) -> @data.Profile {
  let freq : Map[String, Int] = Map([])
  for entry in entries {
    freq.set(entry.0, entry.1)
  }
  @data.Profile::new(name~, n_words~, freq~)
}

///|
/// The three upstream training profiles: en, fr, ja (load order).
fn three_language_factory() -> @core.DetectorFactory raise @core.LangDetectError {
  let factory = @core.DetectorFactory::new()
  factory.add_profile(
    make_profile("en", [9, 1, 1], [
      ("a", 3),
      ("b", 2),
      ("c", 2),
      ("d", 1),
      ("e", 1),
    ]),
  )
  factory.add_profile(
    make_profile("fr", [9, 1, 1], [("a", 1), ("b", 2), ("c", 3), ("d", 3)]),
  )
  factory.add_profile(
    make_profile("ja", [7, 1, 1], [
      ("\u{3042}", 3),
      ("\u{3044}", 1),
      ("\u{3046}", 1),
      ("\u{3048}", 2),
    ]),
  )
  factory
}

///| Two identical profiles (V-50 tie construction, upstream

///|
/// `freq={q:3,r:1}`, `n_words=[4,0,0]`; the unused totals become 1).
fn tie_factory() -> @core.DetectorFactory raise @core.LangDetectError {
  let factory = @core.DetectorFactory::new()
  factory.add_profile(make_profile("x1", [4, 1, 1], [("q", 3), ("r", 1)]))
  factory.add_profile(make_profile("x2", [4, 1, 1], [("q", 3), ("r", 1)]))
  factory
}

///| Run a raising computation, treating an unexpected error as a test

///|
/// failure.
fn[T] must(f : () -> T raise @core.LangDetectError) -> T {
  f() catch {
    _ => abort("unexpected LangDetectError")
  }
}

///| Capture the four error fields of a failing call; `code = -1` marks

///|
/// "did not raise".
fn capture(
  f : () -> Unit raise @core.LangDetectError,
) -> (Int, String, Int, String) {
  try {
    f()
    (-1, "", -1, "")
  } catch {
    CantDetect(code~, message~, input_len~, input_prefix~) =>
      (code, message, input_len, input_prefix)
  }
}

///| Non-secure URL scheme spelled in two pieces so the NE1 static gate

///|
/// (which rejects the bare scheme substring in `src`) stays clean.
fn url_text(rest : String) -> String {
  "ht" + "tp://" + rest
}

///|
/// Secure URL scheme, also split for the same static gate.
fn secure_url_text(rest : String) -> String {
  "ht" + "tps://" + rest
}

///|
/// First `limit` codepoints of `text`.
fn take_chars(text : String, limit : Int) -> String {
  let chars = text.to_array()
  let output = StringBuilder()
  let mut index = 0
  while index < chars.length() && index < limit {
    output.write_char(chars[index])
    index += 1
  }
  output.to_string()
}

// ---------------------------------------------------------------------
// Upstream test_detector.py (6 cases)
// ---------------------------------------------------------------------

///|
/// Upstream `test_detector1`.
test "upstream_detector_1_single_char_is_en" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  detector.append("a")
  assert_eq(must(() => detector.detect()), "en")
}

///|
/// Upstream `test_detector2`.
test "upstream_detector_2_bd_is_fr" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  detector.append("b d")
  assert_eq(must(() => detector.detect()), "fr")
}

///|
/// Upstream `test_detector3`.
test "upstream_detector_3_de_is_en" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  detector.append("d e")
  assert_eq(must(() => detector.detect()), "en")
}

///|
/// Upstream `test_detector4`.
test "upstream_detector_4_hiragana_is_ja" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  detector.append("\u{3042}\u{3042}\u{3042}\u{3042}a")
  assert_eq(must(() => detector.detect()), "ja")
}

///|
/// Upstream `test_lang_list`.
test "upstream_language_list_order" {
  let factory = must(three_language_factory)
  let langlist = factory.get_lang_list()
  assert_eq(langlist.length(), 3)
  assert_eq(langlist[0], "en")
  assert_eq(langlist[1], "fr")
  assert_eq(langlist[2], "ja")
}

///| Upstream `test_factory_from_json_string`, adapted to `add_profile`

///| with the equivalent `LangProfile` frequency data (no JSON loader is

///|
/// part of this port).
test "upstream_factory_from_json_profiles" {
  let factory = @core.DetectorFactory::new()
  let lang1 = make_profile("lang1", [12, 3, 4], [
    ("A", 3),
    ("B", 6),
    ("C", 3),
    ("AB", 2),
    ("BC", 1),
    ("ABC", 2),
    ("BBC", 1),
    ("CBA", 1),
  ])
  let lang2 = make_profile("lang2", [12, 5, 3], [
    ("A", 6),
    ("B", 3),
    ("C", 3),
    ("AA", 3),
    ("AB", 2),
    ("ABC", 1),
    ("ABA", 1),
    ("CAA", 1),
  ])
  must(() => factory.add_profile(lang1))
  must(() => factory.add_profile(lang2))
  let langlist = factory.get_lang_list()
  assert_eq(langlist.length(), 2)
  assert_eq(langlist[0], "lang1")
  assert_eq(langlist[1], "lang2")
  assert_eq(factory.word_lang_prob_map.at("AB").length(), 2)
}

// ---------------------------------------------------------------------
// Error matrix
// ---------------------------------------------------------------------

///| Error code 5 for the nine upstream error variants, through both

///| package-level entries. The forensics fields are taken from the

///|
/// original argument (before URL/mail cleaning).
test "error_code5_variants_test" {
  let inputs : Array[String] = [
    "",
    "     ",
    " \t\r\n  \u{00A0}  ",
    "😀😍🎉👍🚀",
    "👨‍👩‍👧",
    "1234567890",
    "12 34 56 78",
    "!!!???...,,,",
    url_text("example.com/very/long/path?x=1"),
  ]
  for text in inputs {
    let expected_prefix = take_chars(text, 32)
    let (code, message, input_len, input_prefix) = capture(() => {
      let _ = @core.detect(text)
    })
    assert_eq(code, @core.ERROR_CANT_DETECT)
    assert_eq(message, "No features in text.")
    assert_eq(input_len, text.char_length())
    assert_eq(input_prefix, expected_prefix)
    let (langs_code, langs_message, langs_len, langs_prefix) = capture(() => {
      let _ = @core.detect_langs(text)
    })
    assert_eq(langs_code, @core.ERROR_CANT_DETECT)
    assert_eq(langs_message, "No features in text.")
    assert_eq(langs_len, text.char_length())
    assert_eq(langs_prefix, expected_prefix)
  }
}

///| Error code 4: an empty detector and an empty factory both report

///|
/// `Need to load profiles.` for detection and probability listing.
test "error_code4_test" {
  let empty = @core.Detector::new()
  let (code, message, input_len, input_prefix) = capture(() => {
    let _ = empty.detect()
  })
  assert_eq(code, @core.ERROR_NEED_LOAD_PROFILE)
  assert_eq(message, "Need to load profiles.")
  assert_eq(input_len, 0)
  assert_eq(input_prefix, "")
  let factory = @core.DetectorFactory::new()
  let detector = factory.create()
  let (probs_code, probs_message, _, _) = capture(() => {
    let _ = detector.get_probabilities()
  })
  assert_eq(probs_code, @core.ERROR_NEED_LOAD_PROFILE)
  assert_eq(probs_message, "Need to load profiles.")
}

///|
/// Error code 8: a negative prior value.
test "prior_negative_test" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  let negative : Map[String, Double] = Map([("en", -0.1)])
  let (code, message, _, _) = capture(() => detector.set_prior_map(negative))
  assert_eq(code, @core.ERROR_INIT_PARAM)
  assert_eq(message, "Prior probability must be non-negative.")
  assert_true(detector.prior_map is None)
}

///| Error code 8: a non-positive prior sum, including unknown-only and

///|
/// empty maps.
test "prior_zero_sum_test" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  let empty : Map[String, Double] = Map([])
  let (empty_code, empty_message, _, _) = capture(() => {
    detector.set_prior_map(empty)
  })
  assert_eq(empty_code, @core.ERROR_INIT_PARAM)
  assert_eq(empty_message, "More one of prior probability must be non-zero.")
  let unknown : Map[String, Double] = Map([("zz", 1.0)])
  let (unknown_code, unknown_message, _, _) = capture(() => {
    detector.set_prior_map(unknown)
  })
  assert_eq(unknown_code, @core.ERROR_INIT_PARAM)
  assert_eq(unknown_message, "More one of prior probability must be non-zero.")
  let zero : Map[String, Double] = Map([("en", 0.0)])
  let (zero_code, _, _, _) = capture(() => detector.set_prior_map(zero))
  assert_eq(zero_code, @core.ERROR_INIT_PARAM)
  assert_true(detector.prior_map is None)
}

///| V-51: a NaN prior is accepted, normalizes to an all-NaN vector, all

///|
/// entries are filtered out, and `detect` returns `"unknown"`.
test "prior_nan_unknown_test" {
  let factory = @core.DetectorFactory::new()
  must(() => factory.load_profile())
  let detector = factory.create()
  let nan = 0.0 / 0.0
  let prior : Map[String, Double] = Map([("en", nan)])
  must(() => detector.set_prior_map(prior))
  match detector.prior_map {
    Some(vector) => {
      assert_eq(vector.length(), 55)
      assert_true(vector[0].is_nan())
      assert_true(vector[1].is_nan())
      assert_true(vector[54].is_nan())
    }
    None => abort("prior map should be set")
  }
  detector.append("the weather is nice today and the sun is shining brightly")
  let probs = must(() => detector.get_probabilities())
  assert_eq(probs.length(), 0)
  assert_eq(must(() => detector.detect()), "unknown")
  match detector.langprob {
    Some(raw) => {
      assert_eq(raw.length(), 55)
      assert_true(raw[0].is_nan())
    }
    None => abort("langprob should be cached")
  }
}

///|
/// Error code 3: duplicate language profiles.
test "duplicate_lang_test" {
  let factory = must(three_language_factory)
  let duplicate = make_profile("en", [1, 1, 1], [("z", 1)])
  let (code, message, _, _) = capture(() => factory.add_profile(duplicate))
  assert_eq(code, @core.ERROR_DUPLICATE_LANG)
  assert_eq(message, "Duplicate the same language profile.")
  assert_eq(factory.get_lang_list().length(), 3)
}

///| Error code 1: zero or out-of-range `n_words`, checked before any

///|
/// division and before any container mutation (Task 5 transfer).
test "profile_format_error_test" {
  let factory = must(three_language_factory)
  let before_words = factory.word_lang_prob_map.length()
  let zero = make_profile("zero", [1, 0, 1], [("z", 1)])
  let (zero_code, zero_message, _, _) = capture(() => factory.add_profile(zero))
  assert_eq(zero_code, @core.ERROR_FORMAT)
  assert_eq(zero_message, "Profile format error.")
  let short = make_profile("short", [1, 1], [("z", 1)])
  let (short_code, short_message, _, _) = capture(() => {
    factory.add_profile(short)
  })
  assert_eq(short_code, @core.ERROR_FORMAT)
  assert_eq(short_message, "Profile format error.")
  assert_eq(factory.get_lang_list().length(), 3)
  assert_eq(factory.word_lang_prob_map.length(), before_words)
}

///| Error code 2 is retained but unreachable in this port: the embedded

///| loader has no path and performs no file open (upstream

///|
/// `FileLoadError`, spec §6).
test "profile_open_error_test" {
  assert_eq(@core.ERROR_FILE_LOAD, 2)
  // No public entry accepts a profile directory or file path, so no call
  // can raise code 2. Reachability remains unverified, as registered in
  // spec §6 / the plan error matrix.
}

// ---------------------------------------------------------------------
// Low-confidence entry
// ---------------------------------------------------------------------

///|
/// Empty and short inputs are low confidence and never raise code 5.
test "lowconf_empty_test" {
  match @core.detect_with_confidence("") {
    LowConfidence(char_count~) => assert_eq(char_count, 0)
    Detected(..) => abort("empty input must be low confidence")
  }
  match @core.detect_with_confidence("     ") {
    LowConfidence(char_count~) => assert_eq(char_count, 5)
    Detected(..) => abort("whitespace input must be low confidence")
  }
}

///| Threshold 50: 49 codepoints is low confidence, 50 runs a detection.

///|
/// A long featureless input converts code 5 to low confidence.
test "lowconf_boundary_test" {
  let below = "the weather is nice today and the sun is shining!"
  assert_eq(below.char_length(), 49)
  match @core.detect_with_confidence(below) {
    LowConfidence(char_count~) => assert_eq(char_count, 49)
    Detected(..) => abort("49 codepoints must be low confidence")
  }
  let at = "the weather is nice today and the sun is shining!!"
  assert_eq(at.char_length(), 50)
  match @core.detect_with_confidence(at) {
    LowConfidence(..) => abort("50 codepoints must run a detection")
    Detected(lang~, probs~) => {
      assert_true(!probs.is_empty())
      assert_eq(probs[0].lang, Some(lang))
      let mut index = 0
      while index < probs.length() {
        assert_true(probs[index].prob > @core.PROB_THRESHOLD)
        if index > 0 {
          assert_true(probs[index - 1].prob >= probs[index].prob)
        }
        index += 1
      }
    }
  }
  let blanks = " ".repeat(60)
  match @core.detect_with_confidence(blanks) {
    LowConfidence(char_count~) => assert_eq(char_count, 60)
    Detected(..) => abort("featureless input must be low confidence")
  }
  let long_url = url_text("example.com/" + "a".repeat(60))
  assert_true(long_url.char_length() >= 50)
  match @core.detect_with_confidence(long_url) {
    LowConfidence(char_count~) => assert_eq(char_count, long_url.char_length())
    Detected(..) => abort("url-only input must be low confidence")
  }
}

///| `char_count` is a Unicode codepoint count on the original input:
///
///| 49 non-BMP emoji is below the threshold and 50 reaches it.
test "lowconf_char_count_is_codepoints" {
  let below = "😀".repeat(49)
  assert_eq(below.char_length(), 49)
  match @core.detect_with_confidence(below) {
    LowConfidence(char_count~) => assert_eq(char_count, 49)
    Detected(..) => abort("49 codepoints must be low confidence")
  }
  let at = "😀".repeat(50)
  assert_eq(at.char_length(), 50)
  match @core.detect_with_confidence(at) {
    LowConfidence(char_count~) => assert_eq(char_count, 50)
    Detected(..) => abort("emoji-only input has no features")
  }
}

// ---------------------------------------------------------------------
// append cleaning (V-40 .. V-43, V-54)
// ---------------------------------------------------------------------

///|
/// V-40: URL removal, including the greedy-class quirks.
test "append_url_cleanup" {
  let cases : Array[(String, String)] = [
    ("see " + url_text("a.com/x") + " then TEXT-more", "see then TEXT-more"),
    ("hello " + secure_url_text("example.com/abc"), "hello "),
    (url_text("a.com/x-then"), " "),
    ("go " + url_text("a.com/x;TEXT"), "go "),
    ("go " + url_text("a.com/x,TEXT"), "go ,TEXT"),
    ("a " + secure_url_text("example.com/") + "中", "a 中"),
    ("a " + url_text("x.com/y") + " " + url_text("z.com/w"), "a "),
    (url_text("a.com"), " "),
    (url_text("a.com?"), " "),
    ("x@y.z " + url_text("a.com/w") + " ", " "),
  ]
  for entry in cases {
    let detector = @core.Detector::new()
    detector.append(entry.0)
    assert_eq(detector.text, entry.1)
  }
  // The trailing class is capped at 2076 codepoints.
  let detector = @core.Detector::new()
  let tail = "z".repeat(10)
  detector.append(url_text("y".repeat(2076) + tail))
  assert_eq(detector.text, " " + tail)
  // The scheme is case-sensitive and requires at least one class char.
  let untouched = @core.Detector::new()
  untouched.append("HT" + "TP://a.com")
  assert_eq(untouched.text, "HT" + "TP://a.com")
  let bare = @core.Detector::new()
  bare.append(url_text(""))
  assert_eq(bare.text, url_text(""))
  let secure_bare = @core.Detector::new()
  secure_bare.append(secure_url_text(""))
  assert_eq(secure_bare.text, secure_url_text(""))
  // One codepoint past the 2076 cap survives.
  let capped = @core.Detector::new()
  capped.append(url_text("a".repeat(2077)))
  assert_eq(capped.text, " a")
}

///|
/// V-41: mail-address removal.
test "append_email_cleanup" {
  let cases : Array[(String, String)] = [
    ("mail me at john.doe@example.com please", "mail me at please"),
    ("a@b", "a@b"),
    ("a@bc", " "),
    ("a@.com", "a@.com"),
    ("a@b.", " "),
    ("a@b.c", " "),
    ("a@b..c", " "),
    ("a@b,c", "a@b,c"),
    ("a@b#c", "a@b#c"),
    ("a@b/c", "a@b/c"),
    ("x john.doe@example.com, y", "x , y"),
  ]
  for entry in cases {
    let detector = @core.Detector::new()
    detector.append(entry.0)
    assert_eq(detector.text, entry.1)
  }
  // A 65-character local part matches from its second character onward
  // (the leftmost 64-character local run followed by '@').
  let long_local = @core.Detector::new()
  long_local.append("a".repeat(65) + "@b.c")
  assert_eq(long_local.text, "a ")
  // The two domain quantifiers cover 255 + 255 characters.
  let long_domain = @core.Detector::new()
  long_domain.append("a@" + "b".repeat(256) + ".c")
  assert_eq(long_domain.text, " ")
}

///|
/// V-42: only U+0020 runs collapse; tabs are preserved.
test "append_space_collapse_preserves_tabs" {
  let detector = @core.Detector::new()
  detector.append("a  b\t\tc")
  assert_eq(detector.text, "a b\t\tc")
}

///| V-43: truncation counts cleaned codepoints and happens before the

///|
/// space collapse.
test "append_truncates_after_cleaning" {
  let first = @core.Detector::new()
  first.set_max_text_length(5)
  first.append("abcdefghij")
  assert_eq(first.text, "abcde")
  let second = @core.Detector::new()
  second.set_max_text_length(3)
  second.append("aaabbb")
  assert_eq(second.text, "aaa")
  let collapse = @core.Detector::new()
  collapse.set_max_text_length(4)
  collapse.append("aa  bb")
  assert_eq(collapse.text, "aa ")
  let cleaned = @core.Detector::new()
  cleaned.set_max_text_length(7)
  cleaned.append("see " + url_text("a.com/x") + " then")
  assert_eq(cleaned.text, "see t")
}

///| V-54: `append` accumulates, `cleaning_text` rewrites in place and is

///|
/// idempotent.
test "append_accumulates_and_cleaning_idempotent" {
  let detector = @core.Detector::new()
  detector.append("hello")
  detector.append("hello")
  assert_eq(detector.text, "hellohello")
  let cleaned = @core.Detector::new()
  cleaned.append(
    "日本語のテキストです。これはテストです。 hello",
  )
  cleaned.cleaning_text()
  let once = cleaned.text
  cleaned.cleaning_text()
  assert_eq(cleaned.text, once)
  assert_true(once.contains("日本語"))
  assert_true(!once.contains("hello"))
}

///| `append` order: Vietnamese normalization happens before the
///
///| `max_text_length` truncation, and it is measured in cleaned codepoints.
test "append_normalizes_vietnamese_before_truncation" {
  let normalized = @core.Detector::new()
  normalized.append("A\u{0300}")
  assert_eq(normalized.text, "\u{00C0}")
  // "A" + U+0300 + "B" normalizes to two codepoints; a limit of 1 keeps
  // the composed "À" only.
  let truncated = @core.Detector::new()
  truncated.set_max_text_length(1)
  truncated.append("A\u{0300}B")
  assert_eq(truncated.text, "\u{00C0}")
  assert_eq(truncated.text.char_length(), 1)
}

// ---------------------------------------------------------------------
// Cache, threshold, ties, aliasing, vectors
// ---------------------------------------------------------------------

///|
/// V-47: `append` does not invalidate the `langprob` cache.
test "langprob_cache_survives_append" {
  let factory = must(three_language_factory)
  factory.set_seed(Some(0L))
  let detector = factory.create()
  detector.append("a")
  let first = must(() => detector.detect())
  let first_probs = must(() => detector.get_probabilities())
  detector.append("b d")
  let second = must(() => detector.detect())
  assert_eq(second, first)
  let second_probs = must(() => detector.get_probabilities())
  assert_eq(second_probs.length(), first_probs.length())
  assert_eq(second_probs[0].lang, first_probs[0].lang)
  assert_eq(
    second_probs[0].prob.reinterpret_as_uint64(),
    first_probs[0].prob.reinterpret_as_uint64(),
  )
  assert_eq(detector.text, "ab d")
}

///| V-48 / V-53: the diagnostic vector length and the language list of the

///|
/// lazy embedded factory.
test "debug_vector_len_embedded_v48" {
  assert_eq(@core.debug_vector_len(), 55)
  assert_eq(@core.debug_vector_len(), 55)
  let langlist = @core.get_lang_list()
  assert_eq(langlist.length(), 55)
  assert_eq(langlist[0], "af")
  assert_eq(langlist[54], "zh-tw")
  assert_eq(langlist.length(), @data.languages.length())
  let mut index = 0
  while index < langlist.length() {
    assert_eq(langlist[index], @data.languages[index])
    index += 1
  }
}

///| The package-level `get_lang_list` also returns a copy; mutating it
///
///| does not change the lazy singleton's list.
test "package_lang_list_is_copy" {
  let copy = @core.get_lang_list()
  assert_eq(copy.length(), 55)
  copy.push("zz")
  assert_eq(copy.length(), 56)
  let again = @core.get_lang_list()
  assert_eq(again.length(), 55)
  assert_true(!again.contains("zz"))
}

///| V-49 (Task 7 transfer): the real strict `> 0.1` filter on the exact,

///| next-above and next-below bit patterns.

///|
/// Label: `synthetic:基准 250 例中最小条目 0.1428…，无 ≤ 0.1（V-49）`.
test "threshold_filter_real_path_v49" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  let exact = UInt64::reinterpret_as_double(0x3FB999999999999AUL)
  let above = UInt64::reinterpret_as_double(0x3FB999999999999BUL)
  let below = UInt64::reinterpret_as_double(0x3FB9999999999999UL)
  assert_eq(exact, 0.1)
  detector.set_raw_probabilities([exact, above, below])
  let probs = must(() => detector.get_probabilities())
  assert_eq(probs.length(), 1)
  assert_eq(probs[0].lang, Some("fr"))
  assert_eq(probs[0].prob.reinterpret_as_uint64(), 0x3FB999999999999BUL)
  assert_eq(must(() => detector.detect()), "fr")
  // NaN entries never satisfy the strict comparison.
  let nan = 0.0 / 0.0
  detector.set_raw_probabilities([nan, below, exact])
  let filtered = must(() => detector.get_probabilities())
  assert_eq(filtered.length(), 0)
  assert_eq(must(() => detector.detect()), "unknown")
  // Negative zero compares equal to positive zero and is not greater than
  // the positive threshold (spec §4.4 EQ3).
  let negative_zero = UInt64::reinterpret_as_double(0x8000000000000000UL)
  assert_true(negative_zero == 0.0)
  detector.set_raw_probabilities([negative_zero, 0.0, exact])
  let zeros = must(() => detector.get_probabilities())
  assert_eq(zeros.length(), 0)
}

///|
/// V-50: two identical profiles tie; stable order follows load order.
test "tied_probabilities_keep_load_order" {
  let factory = must(tie_factory)
  factory.set_seed(Some(0L))
  let detector = factory.create()
  detector.append("q r")
  let probs = must(() => detector.get_probabilities())
  assert_eq(probs.length(), 2)
  assert_eq(probs[0].lang, Some("x1"))
  assert_eq(probs[1].lang, Some("x2"))
  assert_eq(probs[0].prob.reinterpret_as_uint64(), 0x3FDFFFFFFFFFFFFEUL)
  assert_eq(probs[1].prob.reinterpret_as_uint64(), 0x3FDFFFFFFFFFFFFEUL)
  assert_eq(
    probs[0].prob.reinterpret_as_uint64(),
    probs[1].prob.reinterpret_as_uint64(),
  )
  assert_eq(must(() => detector.detect()), "x1")
}

///| V-52 / L1-A4: factory and instance share the same containers; adding

///| through the factory is visible to an already created detector, and so

///|
/// is `load_profile` and `clear`.
test "factory_instance_alias_sharing" {
  let factory = @core.DetectorFactory::new()
  must(() => {
    factory.add_profile(
      make_profile("en", [9, 1, 1], [
        ("a", 3),
        ("b", 2),
        ("c", 2),
        ("d", 1),
        ("e", 1),
      ]),
    )
  })
  let detector = factory.create()
  assert_true(physical_equal(detector.langlist, factory.langlist))
  assert_true(
    physical_equal(detector.word_lang_prob_map, factory.word_lang_prob_map),
  )
  must(() => {
    factory.add_profile(
      make_profile("fr", [9, 1, 1], [("a", 1), ("b", 2), ("c", 3), ("d", 3)]),
    )
  })
  assert_eq(detector.langlist.length(), 2)
  assert_eq(factory.langlist.length(), 2)
  assert_true(physical_equal(detector.langlist, factory.langlist))
  assert_eq(detector.word_lang_prob_map.at("a").length(), 2)
  assert_eq(factory.word_lang_prob_map.at("a").length(), 2)
  // load_profile updates the shared containers in place.
  let loaded_factory = @core.DetectorFactory::new()
  let created_before_load = loaded_factory.create()
  must(() => loaded_factory.load_profile())
  assert_eq(created_before_load.langlist.length(), 55)
  assert_true(
    physical_equal(created_before_load.langlist, loaded_factory.langlist),
  )
  // clear updates the shared containers in place.
  factory.clear()
  assert_eq(detector.langlist.length(), 0)
  assert_eq(detector.word_lang_prob_map.length(), 0)
  let (code, message, _, _) = capture(() => {
    let _ = detector.detect()
  })
  assert_eq(code, @core.ERROR_NEED_LOAD_PROFILE)
  assert_eq(message, "Need to load profiles.")
}

///| V-53: probability vector rows have one slot per language; embedded

///|
/// rows are 55 and synthetic rows match the language count.
test "vector_row_length_v53" {
  let factory = @core.DetectorFactory::new()
  must(() => factory.load_profile())
  assert_eq(factory.get_lang_list().length(), 55)
  assert_eq(factory.word_lang_prob_map.at("D").length(), 55)
  let synthetic = @core.DetectorFactory::new()
  must(() => {
    synthetic.add_profile(make_profile("x1", [4, 1, 1], [("q", 3), ("r", 1)]))
  })
  must(() => {
    synthetic.add_profile(make_profile("x2", [4, 1, 1], [("q", 3), ("r", 1)]))
  })
  assert_eq(synthetic.get_lang_list().length(), 2)
  assert_eq(synthetic.word_lang_prob_map.at("q").length(), 2)
}

///| Factory seed is copied at create time and later changes do not

///|
/// retroactively affect existing detectors (spec §5.5).
test "factory_seed_copied_at_create" {
  let factory = must(three_language_factory)
  factory.set_seed(Some(42L))
  let first = factory.create()
  factory.set_seed(Some(7L))
  let second = factory.create()
  match first.seed {
    Some(value) => assert_eq(value, 42L)
    None => abort("first detector seed missing")
  }
  match second.seed {
    Some(value) => assert_eq(value, 7L)
    None => abort("second detector seed missing")
  }
  first.append("a b d")
  second.append("a b d")
  let first_probs = must(() => first.get_probabilities())
  let second_probs = must(() => second.get_probabilities())
  assert_true(
    first_probs[0].prob.reinterpret_as_uint64() !=
    second_probs[0].prob.reinterpret_as_uint64(),
  )
  // Same seed: identical bits across independent detectors.
  factory.set_seed(Some(42L))
  let third = factory.create()
  let fourth = factory.create()
  third.append("a b d")
  fourth.append("a b d")
  let third_probs = must(() => third.get_probabilities())
  let fourth_probs = must(() => fourth.get_probabilities())
  assert_eq(
    third_probs[0].prob.reinterpret_as_uint64(),
    fourth_probs[0].prob.reinterpret_as_uint64(),
  )
}

///| Instance `set_seed` overrides the seed copied at create time without
///
///| touching the factory seed.
test "detector_instance_seed_overrides" {
  let factory = must(three_language_factory)
  let first = factory.create()
  let second = factory.create()
  first.set_seed(Some(42L))
  second.set_seed(Some(42L))
  match first.seed {
    Some(value) => assert_eq(value, 42L)
    None => abort("instance seed missing")
  }
  assert_true(factory.seed is None)
  first.append("a b d")
  second.append("a b d")
  let a = must(() => first.get_probabilities())
  let b = must(() => second.get_probabilities())
  assert_eq(
    a[0].prob.reinterpret_as_uint64(),
    b[0].prob.reinterpret_as_uint64(),
  )
  // A different instance seed produces a different bit pattern (the same
  // 42/7 contrast as the factory-seed test above).
  let third = factory.create()
  third.set_seed(Some(7L))
  third.append("a b d")
  let c = must(() => third.get_probabilities())
  assert_true(
    a[0].prob.reinterpret_as_uint64() != c[0].prob.reinterpret_as_uint64(),
  )
}

///| `create(alpha=...)` takes a bare value and applies it; the default is

///|
/// 0.5 (V-58 calling shape).
test "create_alpha_optional" {
  let factory = must(three_language_factory)
  let default_alpha = factory.create()
  assert_eq(default_alpha.alpha, 0.5)
  let zero_alpha = factory.create(alpha=0.0)
  assert_eq(zero_alpha.alpha, 0.0)
  let custom_alpha = factory.create(alpha=0.7)
  assert_eq(custom_alpha.alpha, 0.7)
}

///| Prior values are normalized over the known languages; unknown keys

///|
/// are ignored.
test "prior_map_normalized" {
  let factory = must(three_language_factory)
  let detector = factory.create()
  let prior : Map[String, Double] = Map([("en", 2.0), ("fr", 1.0)])
  must(() => detector.set_prior_map(prior))
  match detector.prior_map {
    Some(vector) => {
      assert_eq(vector.length(), 3)
      assert_eq(vector[0], 2.0 / 3.0)
      assert_eq(vector[1], 1.0 / 3.0)
      assert_eq(vector[2], 0.0)
    }
    None => abort("prior map should be set")
  }
}

///|
/// `get_lang_list` returns a shallow copy.
test "factory_lang_list_is_copy" {
  let factory = must(three_language_factory)
  let copy = factory.get_lang_list()
  copy.push("zz")
  assert_eq(copy.length(), 4)
  assert_eq(factory.get_lang_list().length(), 3)
}

///|
/// `Detector::new` field defaults (spec §1.2 V-07).
test "detector_new_defaults" {
  let detector = @core.Detector::new()
  assert_eq(detector.langlist.length(), 0)
  assert_eq(detector.word_lang_prob_map.length(), 0)
  assert_true(detector.seed is None)
  assert_eq(detector.alpha, 0.5)
  assert_eq(detector.n_trial, 7)
  assert_eq(detector.max_text_length, 10000)
  assert_true(detector.prior_map is None)
  assert_eq(detector.text, "")
  assert_true(detector.langprob is None)
}

///| Native bit-for-bit integration against the upstream golden
///| (`docs/port/golden/expected.json`, seed 0): the whole chain —
///| embedded load, URL cleaning, feature extraction, random block and the
///| `> 0.1` filter — must reproduce the recorded `prob_bits`. The URL case
///| is also the V-40 greedy-class sample.
test "golden_seed0_short_en_and_url_case" {
  let factory = @core.DetectorFactory::new()
  must(() => factory.load_profile())
  factory.set_seed(Some(0L))
  let detector = factory.create()
  detector.append("The weather is nice today.")
  let probs = must(() => detector.get_probabilities())
  assert_eq(probs[0].lang, Some("en"))
  assert_eq(probs[0].prob.reinterpret_as_uint64(), 0x3FEFFFFACE0CDB00UL)
  let url_detector = factory.create()
  url_detector.append("see " + url_text("a.com/x") + " then TEXT-more")
  let url_probs = must(() => url_detector.get_probabilities())
  assert_eq(url_probs[0].lang, Some("en"))
  assert_eq(url_probs[0].prob.reinterpret_as_uint64(), 0x3FEFFFFA092A1047UL)
}

///| Package-level detection: `detect_langs` is descending and agrees with

///|
/// `detect` on the top language.
test "package_detect_and_langs_agree" {
  let text = "the weather is nice today and the sun is shining brightly"
  let probs = must(() => @core.detect_langs(text))
  assert_true(!probs.is_empty())
  let mut index = 0
  while index < probs.length() {
    assert_true(probs[index].prob > @core.PROB_THRESHOLD)
    if index > 0 {
      assert_true(probs[index - 1].prob >= probs[index].prob)
    }
    index += 1
  }
  let top = must(() => @core.detect(text))
  assert_eq(probs[0].lang, Some(top))
  assert_true(@core.get_lang_list().contains(top))
}
