///| CPython `random.Random.gauss` (`Lib/random.py`) on top of the
/// MT19937 pipeline in `rng.mbt`.
///
/// The Box-Muller transform is copied call by call: `x2pi` consumes the
/// first `random()`, the logarithm consumes the second, `cos`/`sin` are
/// evaluated once each, and the cached `gauss_next` value is returned on
/// the next call before any new draw. Evaluation order is part of the
/// contract because every `random()` call advances the shared state.
///
/// `log` must go through `@math_seam.ln_for_gauss`: native targets bind
/// the host libm `log` (bitwise identical to CPython on the reference
/// platform, V-32), while js / wasm-gc use the pure-MoonBit fallback
/// (non-equivalent, 1 ulp class, V-35). `sqrt` is the `Double` method
/// (compiled to the hardware square root) and `cos` / `sin` come from
/// `@math`; the port never binds them itself.

///| `math.tau` as the exact IEEE-754 double `0x1.921fb54442d18p+2`
/// (upstream `random.py` imports `math.tau as TWOPI`).
pub const TWOPI : Double = 0x1.921FB54442D18p+2

///| CPython `random.Random.gauss(mu, sigma)`, including the one-value
/// `gauss_next` cache. Uses the platform logarithm seam.
pub fn Mt19937::gauss(self : Mt19937, mu : Double, sigma : Double) -> Double {
  self.gauss_with(mu, sigma, ln=@math_seam.ln_for_gauss)
}

///| Test-injection form of `gauss`: `ln` replaces the platform logarithm
/// seam without changing the Box-Muller call order, so tests can drive
/// the transform with a deterministic stub. Production code calls
/// `gauss`, which passes `@math_seam.ln_for_gauss`.
pub fn Mt19937::gauss_with(
  self : Mt19937,
  mu : Double,
  sigma : Double,
  ln~ : (Double) -> Double,
) -> Double {
  match self.gauss_next {
    Some(cached) => {
      self.gauss_next = None
      mu + cached * sigma
    }
    None => {
      let x2pi = self.random() * TWOPI
      let g2rad = (-2.0 * ln(1.0 - self.random())).sqrt()
      let z = @math.cos(x2pi) * g2rad
      self.gauss_next = Some(@math.sin(x2pi) * g2rad)
      mu + z * sigma
    }
  }
}
