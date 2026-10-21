///| Platform seam for the natural logarithm consumed by the Box-Muller
///| `gauss` transform. Native targets must call the host libm `log` so the
///| result is bitwise identical to CPython's own libm call; js / wasm-gc fall
///| back to the pure-MoonBit implementation, which is a non-equivalent
///| approximation (1 ulp differences are possible, see
///| `docs/port/rand-feasibility.md` §3.1).

///| Binding to the C standard library `log` (libm on the host platform).
#cfg(any(target="native", target="llvm"))
extern "C" fn c_log(x : Double) -> Double = "log"

///| Natural logarithm for `gauss`. On native targets this is libm `log`,
///| which matches CPython bit-for-bit on the reference platform.
#cfg(any(target="native", target="llvm"))
pub fn ln_for_gauss(x : Double) -> Double {
  c_log(x)
}

///| Natural logarithm for `gauss` on non-native targets. The pure-MoonBit
///| implementation can differ from libm by 1 ulp, so this branch is a
///| non-equivalent fallback used only where the C runtime is unavailable.
#cfg(not(any(target="native", target="llvm")))
pub fn ln_for_gauss(x : Double) -> Double {
  @math.ln(x) // non-native fallback
}

///| Test-injection seam: forwards `f(x)` unchanged. Tests substitute a stub
///| through `f` to observe how `gauss` consumes the logarithm without
///| depending on platform-specific numerical behavior.
pub fn ln_for_gauss_with(f~ : (Double) -> Double, x~ : Double) -> Double {
  f(x)
}
