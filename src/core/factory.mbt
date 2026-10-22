///| The detector factory (upstream `DetectorFactory`,

///| `detector_factory.py:15-114`).
///

///| The factory owns the two containers shared with every detector it

///| creates: `langlist` (language codes in load order) and

///| `word_lang_prob_map` (n-gram to per-language probability vectors).

///| They are never rebound: `load_profile`, `add_profile` and `clear`

///| mutate them in place, so an already created `Detector` observes the

///| change (V-52 / L1-A4, spec §9.3).
///

///| `seed` is copied into each detector at `create` time; calling

///| `set_seed` later affects only detectors created afterwards

///|
/// (spec §5.5, `detector_factory.py:29,110-111`).
pub struct DetectorFactory {
  langlist : Array[String]
  word_lang_prob_map : Map[String, Array[Double]]
  mut seed : Int64?
}

///| An empty factory: no languages, no vocabulary, unseeded. This is the

///| construction used by the production-side tests; the package-level

///|
/// `detect` / `detect_langs` use a lazy private singleton instead.
pub fn DetectorFactory::new() -> DetectorFactory {
  { langlist: [], word_lang_prob_map: Map([]), seed: None, }
}

///| Upstream `_create_detector` + `create` (`detector_factory.py:98-108`),

///| minus the code-4 raise: this port returns an empty detector whose

///| detection calls raise code 4. `alpha` is an optional labelled

///| parameter passed as a bare value (`factory.create(alpha=0.5)`), and

///|
/// `0.0` is applied just like any other value.
pub fn DetectorFactory::create(
  self : DetectorFactory,
  alpha? : Double,
) -> Detector {
  let detector = Detector::from_factory(self)
  match alpha {
    Some(value) => detector.alpha = value
    None => ()
  }
  detector
}

///| Reject a profile that would divide by zero or index outside

///| `n_words`: upstream `n_words` must hold the three 1/2/3-gram totals and

///| every total must be positive (`detector_factory.py:89-92`; a zero

///| denominator is a `ZeroDivisionError` wrapped as code 1). The check

///|
/// runs before any container mutation and before any division.
fn validate_profile(profile : @data.Profile) -> Unit raise LangDetectError {
  if profile.n_words.length() != 3 {
    raise CantDetect(
      code=ERROR_FORMAT,
      message="Profile format error.",
      input_len=0,
      input_prefix="",
    )
  }
  match profile.zero_n_words_index() {
    Some(_) =>
      raise CantDetect(
        code=ERROR_FORMAT,
        message="Profile format error.",
        input_len=0,
        input_prefix="",
      )
    None => ()
  }
}

///| Load the 55 embedded profiles (spec §4.5, FR-13/FR-14).
///

///| The profile flat blob is parsed with the data package, every profile's

///| `n_words` precondition is checked (code 1), and the probability table

///| is built with `build_prob_table`, so every word vector has one slot per

///| embedded language (55). `langlist` keeps the embedded order

///| (`@data.languages`). The containers are updated **in place** so existing

///| detector instances keep the aliases and observe the new content

///|
/// (V-52 / L1-A4). No filesystem or network access is involved.
pub fn DetectorFactory::load_profile(
  self : DetectorFactory,
) -> Unit raise LangDetectError {
  let profiles = @data.parse_profiles(@data.profiles_flat())
  if profiles.is_empty() {
    raise CantDetect(
      code=ERROR_NEED_LOAD_PROFILE,
      message="Not found profile: embedded",
      input_len=0,
      input_prefix="",
    )
  }
  for profile in profiles {
    validate_profile(profile)
  }
  let table = @data.build_prob_table(profiles)
  self.langlist.clear()
  for profile in profiles {
    self.langlist.push(profile.name)
  }
  self.word_lang_prob_map.clear()
  for word, vector in table {
    self.word_lang_prob_map.set(word, vector)
  }
}

///| Add one profile by its frequency data (upstream

///| `detector_factory.py:80-92` with the product precondition from spec

///| §4.1).
///

///| A duplicate language raises code 3 (`Duplicate the same language

///| profile.`) before any mutation. A malformed `n_words` (not length 3,

///| or any zero total) raises code 1 (`Profile format error.`) before any

///| mutation or division. Otherwise every existing word vector grows by one

///| zero slot, the language is appended at `langlist.length()`, and words

///| of length 1..3 store `count / n_words[len - 1]`; longer keys keep the

///|
/// zero row (they are inserted but never written), as upstream does.
pub fn DetectorFactory::add_profile(
  self : DetectorFactory,
  profile : @data.Profile,
) -> Unit raise LangDetectError {
  if self.langlist.contains(profile.name) {
    raise CantDetect(
      code=ERROR_DUPLICATE_LANG,
      message="Duplicate the same language profile.",
      input_len=0,
      input_prefix="",
    )
  }
  validate_profile(profile)
  let index = self.langlist.length()
  for _word, vector in self.word_lang_prob_map {
    vector.push(0.0)
  }
  self.langlist.push(profile.name)
  for word, count in profile.freq {
    let vector = match self.word_lang_prob_map.get(word) {
      Some(existing) => existing
      None => {
        let created : Array[Double] = Array::make(index + 1, 0.0)
        self.word_lang_prob_map.set(word, created)
        created
      }
    }
    let length = word.char_length()
    if length >= 1 && length <= 3 {
      vector[index] = count.to_double() /
        profile.n_words[length - 1].to_double()
    }
  }
}

///| Reset both shared containers in place (upstream

///| `detector_factory.py:94-96`). `seed` is retained, as upstream does.

///| Existing detectors observe the empty containers (spec §9.3) and then

///|
/// raise code 4 on detection.
pub fn DetectorFactory::clear(self : DetectorFactory) -> Unit {
  self.langlist.clear()
  self.word_lang_prob_map.clear()
}

///| Language codes in load order, as a shallow copy: mutating the returned

///| array does not affect the factory (upstream

///|
/// `detector_factory.py:113-114`).
pub fn DetectorFactory::get_lang_list(self : DetectorFactory) -> Array[String] {
  self.langlist.copy()
}

///| Set the seed copied into detectors created afterwards

///| (`detector_factory.py:110-111`). Already created detectors keep the

///|
/// seed they read at construction.
pub fn DetectorFactory::set_seed(self : DetectorFactory, seed : Int64?) -> Unit {
  self.seed = seed
}

///| Length of one probability vector row (the upstream `langsize`).

///| Embedded loading yields 55. If no word is present the language count is

///|
/// returned, so an empty/cleared factory reports 0.
fn DetectorFactory::vector_len(self : DetectorFactory) -> Int {
  let mut length = self.langlist.length()
  let mut found = false
  for _word, vector in self.word_lang_prob_map {
    if !found {
      length = vector.length()
      found = true
    }
  }
  length
}
