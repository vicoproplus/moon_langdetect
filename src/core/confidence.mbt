///| One detected language and its probability (upstream `Language`,

///| `language.py:7-17`).
///

///| `lang` is `None` only for a manually constructed empty entry

///| (`Language(None, 0)` upstream); every entry returned by detection has a

///| language. `prob` is the normalized probability of that language.
///

///| Ordering follows upstream `__lt__`: only `prob` is compared, never

///| `lang`. Two entries with the same probability are therefore mutually

///| not-less, and the stable sort in `sort_probability` keeps their load

///|
/// order.
pub struct LangProb {
  lang : String?
  prob : Double
}

///|
/// Upstream `Language(lang, prob)` construction.
pub fn LangProb::new(lang : String?, prob : Double) -> LangProb {
  { lang, prob, }
}

///| Upstream `Language.__lt__` (`language.py:16-17`): compare probability

///|
/// only, ignoring the language code.
pub fn LangProb::less(self : LangProb, other : LangProb) -> Bool {
  self.prob < other.prob
}

///| Product extension `[EXT]` (spec §5.3, G-29): the result of the

///| low-confidence entry point.
///

///| `LowConfidence(char_count)` reports the original input length in

///| Unicode codepoints; the input was considered too short, or had no

///| extractable feature. `Detected` carries the winning language and the

///| non-empty filtered probability list (strictly greater than 0.1,

///|
/// descending, stable on ties).
pub(all) enum Confidence {
  LowConfidence(char_count~ : Int)
  Detected(lang~ : String, probs~ : Array[LangProb])
}

///| Low-confidence threshold on the input codepoint count: fewer than 50

///| codepoints is low confidence; 50 or more runs a full detection. The

///| value is a product decision (PRD FR-21..FR-23, spec §5.3), not an

///|
/// upstream constant.
pub const LOW_CONFIDENCE_THRESHOLD : Int = 50

///| Low-confidence entry point (spec §5.3, `[EXT]` G-29).
///

///| `char_count` semantics: the number of Unicode codepoints in the

///| **original** `text` argument (`String::char_length()`), measured before

///| URL / mail-address stripping and before the detector's

///| `max_text_length` truncation. An empty string therefore reports

///| `char_count = 0`.
///

///| Error semantics: this entry point never raises. Inputs shorter than 50

///| codepoints return `LowConfidence` without running the detector. Longer

///| inputs run a full detection on a fresh factory (a fresh detector

///| instance over a fresh, internally loaded embedded profile set, so no

///| global singleton state is read); upstream error code 5 ("no features",

///| for example all whitespace or a bare URL) is converted to

///| `LowConfidence(char_count)`. Any other unexpected load failure is also

///|
/// reported as low confidence because the signature has no error channel.
pub fn detect_with_confidence(text : String) -> Confidence {
  let char_count = text.char_length()
  if char_count < LOW_CONFIDENCE_THRESHOLD {
    return LowConfidence(char_count~)
  }
  let detected : Array[LangProb]? = try {
    let factory = DetectorFactory::new()
    factory.load_profile()
    let detector = factory.create()
    detector.append(text)
    Some(detector.get_probabilities())
  } catch {
    _ => None
  }
  match detected {
    None => LowConfidence(char_count~)
    Some(probs) =>
      if probs.is_empty() {
        LowConfidence(char_count~)
      } else {
        let lang = match probs[0].lang {
          Some(value) => value
          None => UNKNOWN_LANG
        }
        Detected(lang~, probs~)
      }
  }
}
