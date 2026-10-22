///| Upstream `Detector.cleaning_text` (`detector.py:114-130`) as a pure
///| function: drop the Latin letters when the text is mostly non-Latin.
///
///| Counting rules (contract §3.2):
///
///| * `latin_count` counts codepoints in the inclusive range `A`..`z`
///|   (U+0041..U+007A). That range is a codepoint interval, not "Latin
///|   letters": `[`, `\`, `]`, `^`, `_` and `` ` `` (U+005B..U+0060) also
///|   count as Latin.
///| * `non_latin_count` counts codepoints `>=` U+0300. Upstream additionally
///|   compares `unicode_block(ch)` to the string `'Latin Extended Additional'`;
///|   `unicode_block` returns an Int, so that comparison is always true and
///|   the exemption never applies (V-45, contract §10 quirk 1). This port
///|   therefore counts every codepoint `>=` U+0300, including U+1E00..U+1EFF.
///| * When `latin_count * 2 < non_latin_count` (strict), every codepoint in
///|   `A`..`z` is removed and all other codepoints are kept. The operation
///|   is idempotent (V-54).
pub fn cleaning_text(text : String) -> String {
  let mut latin_count = 0
  let mut non_latin_count = 0
  for ch in text.iter() {
    let codepoint = ch.to_int()
    if codepoint >= 0x41 && codepoint <= 0x7A {
      latin_count = latin_count + 1
    } else if codepoint >= 0x0300 {
      // Upstream also requires unicode_block(ch) != 'Latin Extended
      // Additional'. The block query returns an Int, so the comparison is
      // always true and the Latin Extended Additional exemption never
      // applies (V-45). Counting is unconditional.
      non_latin_count = non_latin_count + 1
    }
  }
  if latin_count * 2 < non_latin_count {
    let stripped = StringBuilder()
    for ch in text.iter() {
      let codepoint = ch.to_int()
      if codepoint < 0x41 || codepoint > 0x7A {
        stripped.write_char(ch)
      }
    }
    stripped.to_string()
  } else {
    text
  }
}
