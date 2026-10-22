///| Normalization and summation for the probability vector, ported from
/// `Detector._normalize_prob` (`detector.py:219-231`).
///
/// CPython 3.12 changed the builtin `sum()` float path to Neumaier
/// compensated summation (gh-100425). `sum(prob)` therefore is not a
/// left-to-right loop: in 307 recorded groups only 69 match the naive
/// sum, while all 307 match Neumaier (V-33,
/// `docs/port/float-add-conclusion.md`). The port must reproduce the
/// compensation term exactly, including its branch order, otherwise
/// `sump` differs by 1 ulp and the quotient propagates the difference.
///
/// The auxiliary `langprob[j] += prob[j] / n_trial` accumulation in
/// `detect_block` is a plain `+` on the other hand (V-34: 385/385 naive
/// states match); only this `sum()` is compensated.

///| CPython 3.12 `sum()` for a `Double` array, i.e. Neumaier summation:
/// accumulate `hi`, and keep the lost low-order part in `c` using the
/// branch that picks the larger magnitude operand. The final result is
/// `hi + c`. NaN propagates through both accumulators.
pub fn neumaier_sum(values : Array[Double]) -> Double {
  let mut hi = 0.0
  let mut c = 0.0
  for value in values {
    let total = hi + value
    if hi.abs() >= value.abs() {
      c = c + ((hi - total) + value)
    } else {
      c = c + ((value - total) + hi)
    }
    hi = total
  }
  hi + c
}

///| Upstream `_normalize_prob`: divide every entry by the compensated
/// `sum(prob)` in place and return the maximum quotient.
///
/// The comparison is strict (`maxp < p`), so a NaN entry is never
/// selected and `maxp` stays at 0.0 when the vector contains NaN; the
/// loop still visits every entry, exactly like upstream. Callers must
/// not reject NaN here — the NaN-prior path relies on it (V-51).
pub fn normalize_prob(prob : Array[Double]) -> Double {
  let sump = neumaier_sum(prob)
  let mut maxp = 0.0
  let mut index = 0
  while index < prob.length() {
    let p = prob[index] / sump
    if maxp < p {
      maxp = p
    }
    prob[index] = p
    index += 1
  }
  maxp
}
