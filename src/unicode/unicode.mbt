///| Unicode character-property queries backed by the generated CPython
///| 3.12.10 / UCD 15.0.0 tables in `upper_table.mbt`. The tables are
///| generated data, so every target uses the same decisions.

///| CPython 3.12.10 `str.isupper()` decision for a Unicode scalar value.
///| Returns `false` outside the Unicode codespace and for surrogate
///| codepoints (the generated table skips `0xD800..0xDFFF`). Binary search
///| over the 651 maximal intervals keeps the full-codepoint scan cheap.
pub fn is_upper_cp312(cp : Int) -> Bool {
  if cp < 0 || cp > 0x10FFFF {
    return false
  }
  let mut lo = 0
  let mut hi = upper_intervals.length() - 1
  while lo <= hi {
    let mid = (lo + hi) / 2
    let (start, end) = upper_intervals[mid]
    if cp < start {
      hi = mid - 1
    } else if cp > end {
      lo = mid + 1
    } else {
      return true
    }
  }
  false
}

///| Upstream-compatible Unicode block code for a codepoint: the 1-based
///| code (1..220) of `langdetect.utils.unicode_block`, or `0` when the
///| codepoint lies in a gap of that table (upstream returns `None`).
///| Codepoints `<= 0x7F` are Basic Latin (code 1); values outside the
///| Unicode codespace also return the `0` sentinel.
pub fn unicode_block(ch : Int) -> Int {
  if ch < 0 || ch > 0x10FFFF {
    return 0
  }
  if ch <= 0x7F {
    return 1
  }
  let mut lo = 0
  let mut hi = unicode_block_ranges.length() - 1
  while lo <= hi {
    let mid = (lo + hi) / 2
    let (code, start, end) = unicode_block_ranges[mid]
    if ch < start {
      hi = mid - 1
    } else if ch > end {
      lo = mid + 1
    } else {
      return code
    }
  }
  0
}
