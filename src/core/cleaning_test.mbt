///| Upstream parity for `Detector.cleaning_text` (`detector.py:114-130`,
///| contract §3.2): the inclusive `A`..`z` Latin count, the never-applying
///| Latin Extended Additional exemption (V-45) and idempotence (V-54).

///| Mostly non-Latin text loses every `A`..`z` codepoint; the space and the
///| Japanese text survive.
test "cleaning_removes_latin_when_mostly_non_latin" {
  assert_eq(
    @core.cleaning_text("日本語のテキストです。これはテストです。 hello"),
    "日本語のテキストです。これはテストです。 ",
  )
}

///| Enough Latin letters keep the text untouched.
test "cleaning_keeps_latin_when_not_outnumbered" {
  assert_eq(@core.cleaning_text("hello"), "hello")
  assert_eq(@core.cleaning_text(""), "")
}

///| Strict `<`: exactly twice as many non-Latin codepoints as Latin ones
///| does not trigger removal. Five Latin letters and ten `ạ` stay.
test "cleaning_threshold_is_strict" {
  let input = "aaaaa" + "\u{1EA1}".repeat(10)
  assert_eq(@core.cleaning_text(input), input)
}

///| The Latin count uses the codepoint interval U+0041..U+007A, which also
///| contains `[`, `\`, `]`, `^`, `_` and `` ` `` (U+005B..U+0060). Each of
///| the six characters below carries four "Latin" counts, so the input is
///| not stripped; if the interval were letter-only the single `a` would be
///| outnumbered 9:1 and removed.
test "cleaning_counts_ascii_between_A_and_z_as_latin" {
  let separators : Array[String] = ["[", "\\", "]", "^", "_", "`"]
  for separator in separators {
    let input = separator.repeat(4) + "a" + "\u{1EA1}".repeat(9)
    assert_eq(@core.cleaning_text(input), input)
  }
}

///| V-45: U+1EA1 lies in Latin Extended Additional, but upstream compares
///| the integer block code to a string, so the exemption is dead code and
///| the codepoint counts as non-Latin. Five Latin letters against twenty
///| `ạ` are stripped; an exemption would have kept the input unchanged.
test "cleaning_latin_extended_additional_is_never_exempt" {
  let input = "aaaaa " + "\u{1EA1}".repeat(20)
  assert_eq(@core.cleaning_text(input), " " + "\u{1EA1}".repeat(20))
}

///| V-54: `cleaning_text` is idempotent — a second pass changes nothing.
test "cleaning_text_is_idempotent" {
  let samples : Array[String] = [
    "日本語のテキストです。これはテストです。 hello",
    "aaaaa " + "\u{1EA1}".repeat(20),
    "hello",
    "",
    "12345",
    "a  b\u{0009}\u{0009}c",
  ]
  for sample in samples {
    let once = @core.cleaning_text(sample)
    assert_eq(@core.cleaning_text(once), once)
  }
}
