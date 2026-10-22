///| Detector constants transcribed from upstream (spec §1.2 V-07).
///
///| Seven class constants live in `detector.py:44-51`; the three instance
///| defaults are `detector.py:65-66` and `detector_factory.py:29`. The
///| names match the upstream attribute names, so `seed`, `n_trial` and
///| `max_text_length` are immutable `let` values (MoonBit reserves
///| uppercase identifiers for `const`, which only accepts primitive types).

///| Upstream `Detector.ALPHA_DEFAULT` (`detector.py:44`).
pub const ALPHA_DEFAULT : Double = 0.5

///| Upstream `Detector.ALPHA_WIDTH` (`detector.py:45`).
pub const ALPHA_WIDTH : Double = 0.05

///| Upstream `Detector.ITERATION_LIMIT` (`detector.py:47`).
pub const ITERATION_LIMIT : Int = 1000

///| Upstream `Detector.PROB_THRESHOLD` (`detector.py:48`).
pub const PROB_THRESHOLD : Double = 0.1

///| Upstream `Detector.CONV_THRESHOLD` (`detector.py:49`).
pub const CONV_THRESHOLD : Double = 0.99999

///| Upstream `Detector.BASE_FREQ` (`detector.py:50`).
pub const BASE_FREQ : Int = 10000

///| Upstream `Detector.UNKNOWN_LANG` (`detector.py:51`).
pub const UNKNOWN_LANG : String = "unknown"

///| Upstream `DetectorFactory.seed` class attribute default
///| (`detector_factory.py:29`); `None` means a fresh unseeded generator.
pub let seed : Int64? = None

///| Upstream `Detector.n_trial` instance default (`detector.py:65`).
pub let n_trial : Int = 7

///| Upstream `Detector.max_text_length` instance default (`detector.py:66`).
pub let max_text_length : Int = 10000
