///| Public package-level API (spec §5.1, §5.2, §5.4, §5.10).
///

///| The embedded profile set is loaded lazily exactly once into a private

///| process-wide factory (upstream `detector_factory.py:118-137`). No

///| filesystem or network access is involved: `load_profile` parses the

///| embedded flat blob shipped in `src/data`. The singleton reference is

///| set before loading, so a load failure leaves an empty factory and later

///| detection calls raise code 4 instead of retrying.

///| The lazy process-wide factory. `None` means "not initialized yet";

///|
/// `Some(factory)` means initialized (possibly cleared to empty).
let global_factory : Ref[DetectorFactory?] = Ref(None)

///|
/// Return the global factory, loading the embedded profiles on first use.
fn ensure_global_factory() -> DetectorFactory raise LangDetectError {
  match global_factory.val {
    Some(factory) => factory
    None => {
      let factory = DetectorFactory::new()
      global_factory.val = Some(factory)
      factory.load_profile()
      factory
    }
  }
}

///| Non-raising view of the global factory, for the two diagnostic entry

///| points that have no error channel. The embedded load cannot fail; the

///|
/// catch only preserves the no-raise signatures.
fn try_global_factory() -> DetectorFactory? {
  Some(ensure_global_factory()) catch {
    _ => None
  }
}

///| Detect the language of `text` and return its code (spec §5.1,

///| FR-01/FR-12).
///

///| Raises code 5 (`No features in text.`) when the cleaned text yields no

///| vocabulary feature, and code 4 when no profiles are loaded. The error

///| forensics fields (`input_len`, `input_prefix`) are filled from the

///| **original** `text` argument, not from the URL/mail-cleaned detector

///|
/// text.
pub fn detect(text : String) -> String raise LangDetectError {
  try {
    let factory = ensure_global_factory()
    let detector = factory.create()
    detector.append(text)
    detector.detect()
  } catch {
    CantDetect(code~, message~, ..) =>
      raise CantDetect(
        code~,
        message~,
        input_len=text.char_length(),
        input_prefix=input_prefix(text, 32),
      )
  }
}

///| Return the detected languages with probabilities (spec §5.2, FR-02..

///| FR-04). Entries are strictly greater than 0.1, descending, with load

///| order on ties (V-49/V-50). Raises the same codes as `detect`, with

///|
/// forensics fields from the original `text` argument.
pub fn detect_langs(text : String) -> Array[LangProb] raise LangDetectError {
  try {
    let factory = ensure_global_factory()
    let detector = factory.create()
    detector.append(text)
    detector.get_probabilities()
  } catch {
    CantDetect(code~, message~, ..) =>
      raise CantDetect(
        code~,
        message~,
        input_len=text.char_length(),
        input_prefix=input_prefix(text, 32),
      )
  }
}

///| Language codes in embedded load order (spec §5.4, FR-13). Returns a

///|
/// shallow copy; mutating it does not affect the singleton.
pub fn get_lang_list() -> Array[String] {
  match try_global_factory() {
    Some(factory) => factory.get_lang_list()
    None => []
  }
}

///| Diagnostic `[EXT]` entry (spec §5.10, G-33): the length of one

///| probability vector row, i.e. the upstream `langsize`. Embedded loading

///| yields 55. This is the vector length, not the language count; with

///| embedded data the two happen to be equal because every profile is

///| valid (the upstream directory-entry quirk V-48 cannot be constructed

///|
/// without a filesystem and is intentionally not reproduced).
pub fn debug_vector_len() -> Int {
  match try_global_factory() {
    Some(factory) => factory.vector_len()
    None => 0
  }
}
