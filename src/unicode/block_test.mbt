///| Upstream parity for `unicode_block`: the 12 assertions of
///| `langdetect/tests/utils/test_unicode_block.py` plus three samples that
///| fall in gaps of the 220-entry table (upstream returns None -> here 0).

///| Upstream test cases: Basic Latin special case, Latin-1 Supplement,
///| Arrows, Mathematical Operators, Miscellaneous Technical and the two
///| supplementary private use areas.
test "unicode_block_upstream_cases" {
  inspect(@unicode.unicode_block(0x0065), content="1")
  inspect(@unicode.unicode_block(0x007F), content="1")
  inspect(@unicode.unicode_block(0x0080), content="2")
  inspect(@unicode.unicode_block(0x21FF), content="74")
  inspect(@unicode.unicode_block(0x2200), content="75")
  inspect(@unicode.unicode_block(0x2201), content="75")
  inspect(@unicode.unicode_block(0x22FF), content="75")
  inspect(@unicode.unicode_block(0x2300), content="76")
  inspect(@unicode.unicode_block(0xF0000), content="219")
  inspect(@unicode.unicode_block(0xFFFFF), content="219")
  inspect(@unicode.unicode_block(0x100000), content="220")
  inspect(@unicode.unicode_block(0x10FFFF), content="220")
}

///| Gap samples and out-of-range inputs map to the documented 0 sentinel.
test "unicode_block_gap_sentinel" {
  inspect(@unicode.unicode_block(0x0860), content="0")
  inspect(@unicode.unicode_block(0x2FE0), content="0")
  inspect(@unicode.unicode_block(0xE0080), content="0")
  inspect(@unicode.unicode_block(-1), content="0")
  inspect(@unicode.unicode_block(0x110000), content="0")
}
