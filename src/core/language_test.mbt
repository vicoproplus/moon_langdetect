///| Upstream `test_language.py` (2 cases), adapted to `LangProb`.
///

///| The upstream `__repr__`/`str` requirement (`''` for `None`,

///| `'en:1.0'` otherwise) is intentionally not ported: MoonBit `Double`

///| formatting is not Python's shortest-round-trip `str`, and the product

///| API returns structured fields instead of formatted text.

///|
/// Upstream `test_language`: fields and the empty object.
test "language_fields_none_and_prob" {
  let empty = @core.LangProb::new(None, 0.0)
  assert_true(empty.lang is None)
  assert_eq(empty.prob, 0.0)
  let english = @core.LangProb::new(Some("en"), 1.0)
  assert_eq(english.lang, Some("en"))
  assert_eq(english.prob, 1.0)
}

///| Upstream `test_cmp`: ordering uses probability only, and equal

///|
/// probabilities are mutually not-less.
test "language_compare_by_prob_only" {
  let low = @core.LangProb::new(Some("a"), 0.1)
  let high = @core.LangProb::new(Some("b"), 0.5)
  assert_true(@core.LangProb::less(low, high))
  assert_true(!@core.LangProb::less(high, low))
  // The language code does not participate: a different code with a
  // larger probability is still greater.
  let other_code = @core.LangProb::new(Some("z"), 0.5)
  let small_code = @core.LangProb::new(Some("a"), 0.1)
  assert_true(@core.LangProb::less(small_code, other_code))
  assert_true(!@core.LangProb::less(high, other_code))
  assert_true(!@core.LangProb::less(other_code, high))
  assert_true(!@core.LangProb::less(high, high))
}
