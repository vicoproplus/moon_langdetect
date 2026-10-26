# moon_langdetect

Offline language detection for **55 languages**, ported from the Python
[`langdetect`](https://github.com/Mimino666/langdetect) package.

No network, no model server, no runtime data files: the language profiles are
embedded in the module, so a single call works from an empty working directory.

## Install

```bash
moon add vicoproplus/langdetect
```

## Usage

```moonbit
///| Package manifest: import { "vicoproplus/langdetect/src/core" }
fn main {
  let lang = @core.detect("The quick brown fox jumps over the lazy dog.")
  println(lang) // en
}
```

### Probability distribution

```moonbit
let probs = @core.detect_langs("Das ist ein deutscher Satz.")
for p in probs {
  let code = match p.lang {
    Some(code) => code
    None => "unknown"
  }
  println("\{code}: \{p.prob}") // de: 0.9999...
}
```

`LangProb.lang` is `String?` because the upstream `Language` type allows an
empty entry; every entry returned by detection carries a language.

Entries are ordered by descending probability, contain only languages whose
probability is strictly greater than `0.1`, and keep the profile load order on
ties.

### Low-confidence entry point

```moonbit
match @core.detect_with_confidence("Hello") {
  LowConfidence(char_count~) => println("too short: \{char_count}")
  Detected(lang~, ..) => println("detected: \{lang}")
}
```

Inputs shorter than 50 codepoints return `LowConfidence` instead of guessing.
This entry point never raises: an input with no extractable feature (empty,
whitespace only, emoji only, digits only, punctuation only, URL only) is also
reported as low confidence.

Note that this entry point builds a **fresh** factory on every call, so each
call re-parses the embedded profiles (~460 ms measured on Windows x64 native).
Use `detect` / `detect_langs` for per-call hot paths.

### Reproducible results

`detect` and `detect_langs` use an unseeded RNG, matching upstream: the same
text may yield different top languages across calls. To make a run
reproducible, build your own factory and set a seed:

```moonbit
let factory = @core.DetectorFactory::new()
factory.load_profile()
factory.set_seed(Some(0L))
let detector = factory.create()
detector.append("Otec matka syn.")
println(detector.detect())
```

### Supported languages

```
af ar bg bn ca cs cy da de el en es et fa fi fr gu he hi hr hu id it ja kn ko
lt lv mk ml mr ne nl no pa pl pt ro ru sk sl so sq sv sw ta te th tl tr uk ur
vi zh-cn zh-tw
```

Simplified and Traditional Chinese are separate codes (`zh-cn` / `zh-tw`).

## Errors

Detection raises `LangDetectError` with four forensics fields (`code`,
`message`, `input_len`, `input_prefix`):

| code | meaning | message |
|---:|---|---|
| 1 | profile format error | `Profile format error.` |
| 3 | duplicate language profile | `Duplicate the same language profile.` |
| 4 | profiles not loaded | `Need to load profiles.` |
| 5 | no features in text | `No features in text.` |
| 8 | invalid prior probability | `Prior probability must be non-negative.` / `More one of prior probability must be non-zero.` |

Codes 0, 2, 6 and 7 are reserved by the upstream error enum; this port never
raises them.

## Size and startup cost

- Embedded profile data: ~2.2 MB of MoonBit source, ~1.15 MB in the published
  package (53 files).
- First call parses 184,129 profile entries; measured cold start on
  Windows x64 native is ~567 ms (209 ms parse + 347 ms load, median of 3 cold
  processes).
- Subsequent single detections are sub-millisecond.

If cold-start cost matters for your workload, warm the singleton once at
startup by calling `detect` on a known string.

## Target support

| target | status |
|---|---|
| `native` | verified: bit-identical probabilities against the Python baseline |
| `js` | build verified; runtime verification pending |
| `wasm-gc` | build verified; runtime verification pending (treated as experimental) |

`js` and `wasm-gc` route the natural logarithm through `@math.ln` instead of the
platform libm, so their probabilities are **not** bit-identical to `native`
(measured: 66 of 2000 sample points differ by 1 ulp).

## Development

```bash
moon check
moon build --target native
moon build --target js
moon build --target wasm-gc
moon test --target native
```

Cross-checking against the Python baseline requires the reference checkout and
its goldens, which are not part of the published package:

```bash
python tools/compare_golden.py --target native --seed 0 --mode prob_bits
python tools/compare_lowconf.py --short 55 --long 55 --baseline 268
```

## License

MIT. See [LICENSE](LICENSE).

### Upstream attribution

This project is a MoonBit port of the Python package `langdetect` (1.0.9),
which is itself a port of Nakatani Shuyo's Java library `language-detection`
(version from 2014-03-03).

- Upstream Python port: <https://github.com/Mimino666/langdetect>
- Original Java library: <https://github.com/shuyo/language-detection>

The embedded language profile data is derived from the upstream package's
`langdetect/profiles/` directory. The notices shipped with that distribution
are reproduced verbatim in [NOTICE](NOTICE).

Reference scope: this port reproduces the upstream detection algorithm
(character 1–3-gram profiles, Naive Bayes with random sampling), the text
cleaning rules, and the error-code contract. It does **not** port the training
pipeline (`LangProfile`, `load_json_profile`) or mixed-language detection.
