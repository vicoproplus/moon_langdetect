///| The detector instance (upstream `Detector`, `detector.py:44-237`).
///

///| A detector created by `DetectorFactory::create` shares the factory's

///| `langlist` and `word_lang_prob_map` containers by reference (V-52):

///| mutating the factory (for example `add_profile`) is visible to already

///| created instances, and `LangProb` results follow the factory load

///| order. `Detector::new()` builds an empty detector instead; any

///| detection call on it raises code 4 (`Need to load profiles.`).
///

///| Instances cache the raw probability vector in `langprob`. `append`

///| never invalidates that cache (upstream quirk, V-47): once a detection

///| has run, later appends keep returning the first result. `cleaning_text`

///| also rewrites `text` in place and is idempotent (V-54).
///

///| Fields are public because the production-side tests observe the

///| producer-consumer contract directly (`langlist`, `word_lang_prob_map`,

///|
/// `seed`, `prior_map`, `text`, `langprob`).
pub struct Detector {
  langlist : Array[String]
  word_lang_prob_map : Map[String, Array[Double]]
  mut seed : Int64?
  mut alpha : Double
  n_trial : Int
  mut max_text_length : Int
  mut prior_map : Array[Double]?
  mut text : String
  mut langprob : Array[Double]?
}

///| An empty detector (no profiles). Detection on it raises code 4; this

///|
/// is the observable "no profiles loaded" path of the public API.
pub fn Detector::new() -> Detector {
  {
    langlist: [],
    word_lang_prob_map: Map([]),
    seed: None,
    alpha: ALPHA_DEFAULT,
    n_trial,
    max_text_length,
    prior_map: None,
    text: "",
    langprob: None,
  }
}

///| Build a detector over the factory's containers. The two containers are

///| copied as references, so the detector and the factory stay aliased

///| (V-52/L1-A4). `seed` is read once here, matching `detector.py:59`;

///|
/// later factory `set_seed` calls only affect detectors created later.
fn Detector::from_factory(factory : DetectorFactory) -> Detector {
  {
    langlist: factory.langlist,
    word_lang_prob_map: factory.word_lang_prob_map,
    seed: factory.seed,
    alpha: ALPHA_DEFAULT,
    n_trial,
    max_text_length,
    prior_map: None,
    text: "",
    langprob: None,
  }
}

///| Instance configuration: random seed. `Some` is reproducible, `None`

///|
/// uses the non-reproducible generator of `Mt19937::new(None)`.
pub fn Detector::set_seed(self : Detector, seed : Int64?) -> Unit {
  self.seed = seed
}

///| Instance configuration: maximum text length in **cleaned** codepoints

///| (upstream `detector.py:93-97`; V-43). The truncation happens inside

///| `append`, after URL / mail / Vietnamese normalization and before the

///|
/// consecutive-space collapse.
pub fn Detector::set_max_text_length(self : Detector, n : Int) -> Unit {
  self.max_text_length = n
}

///| Instance configuration: prior language probabilities (spec §5.6,

///| `detector.py:73-91`).
///

///| Only languages present in `langlist` are read; unknown keys are

///| ignored. A negative value raises code 8 with `Prior probability must

///| be non-negative.`. A non-positive sum (including an empty prior)

///| raises code 8 with `More one of prior probability must be non-zero.`.

///| A NaN value does **not** raise (the upstream `p < 0` test is false for

///| NaN): the whole vector becomes NaN, every result entry is filtered

///|
/// out, and `detect` returns `"unknown"` (V-51).
pub fn Detector::set_prior_map(self : Detector, prior : Map[String, Double]) -> Unit raise LangDetectError {
  let langsize = self.langlist.length()
  let vector : Array[Double] = Array::make(langsize, 0.0)
  let mut sump = 0.0
  let mut index = 0
  while index < langsize {
    match prior.get(self.langlist[index]) {
      Some(value) => {
        if value < 0.0 {
          raise CantDetect(
            code=ERROR_INIT_PARAM,
            message="Prior probability must be non-negative.",
            input_len=self.text.char_length(),
            input_prefix=input_prefix(self.text, 32),
          )
        }
        vector[index] = value
        sump = sump + value
      }
      None => ()
    }
    index += 1
  }
  if sump <= 0.0 {
    raise CantDetect(
      code=ERROR_INIT_PARAM,
      message="More one of prior probability must be non-zero.",
      input_len=self.text.char_length(),
      input_prefix=input_prefix(self.text, 32),
    )
  }
  let mut cursor = 0
  while cursor < langsize {
    vector[cursor] = vector[cursor] / sump
    cursor += 1
  }
  self.prior_map = Some(vector)
}

///| Upstream `Detector.cleaning_text` (`detector.py:114-130`) as an

///|
/// in-place instance method. The transformation is idempotent (V-54).
pub fn Detector::cleaning_text(self : Detector) -> Unit {
  self.text = cleaning_text(self.text)
}

///| True when `ch` belongs to the URL trailing character class

///|
/// `[-_.?&~;+=/#0-9A-Za-z]` (upstream `Detector.URL_RE`).
fn is_url_char(ch : Char) -> Bool {
  let cp = ch.to_int()
  if cp >= 0x30 && cp <= 0x39 {
    true
  } else if cp >= 0x41 && cp <= 0x5A {
    true
  } else if cp >= 0x61 && cp <= 0x7A {
    true
  } else {
    ch == '-' ||
    ch == '_' ||
    ch == '.' ||
    ch == '?' ||
    ch == '&' ||
    ch == '~' ||
    ch == ';' ||
    ch == '+' ||
    ch == '=' ||
    ch == '/' ||
    ch == '#'
  }
}

///| Length of the URL scheme at `index`, or 0 when there is no scheme.

///| The two recognized spellings are the upstream `URL_RE` prefix with the

///| optional `s`; the scheme letters are compared codepoint by codepoint so

///|
/// the source contains no URL-scheme literal (NE1 static gate).
fn scheme_length_at(chars : Array[Char], index : Int) -> Int {
  let length = chars.length()
  if index + 3 < length &&
    chars[index] == 'h' &&
    chars[index + 1] == 't' &&
    chars[index + 2] == 't' &&
    chars[index + 3] == 'p' {
    if index + 6 < length &&
      chars[index + 4] == ':' &&
      chars[index + 5] == '/' &&
      chars[index + 6] == '/' {
      7
    } else if index + 7 < length &&
      chars[index + 4] == 's' &&
      chars[index + 5] == ':' &&
      chars[index + 6] == '/' &&
      chars[index + 7] == '/' {
      8
    } else {
      0
    }
  } else {
    0
  }
}

///| Upstream `Detector.URL_RE.sub(' ', text)` (`detector.py:53,104`).
///

///| A faithful leftmost, non-overlapping scanner of the upstream URL
///| pattern: the scheme (lowercase, with or without the optional `s`), then
///| between 1 and 2076 trailing-class codepoints are consumed greedily. The
///| match is replaced by one space. Because the class contains letters and
///| digits, an URL followed directly by ASCII text swallows that text until
///| a codepoint outside the class (quirk

///|
/// §10-2, V-40).
fn strip_urls(text : String) -> String {
  let chars = text.to_array()
  let length = chars.length()
  let output = StringBuilder()
  let mut index = 0
  while index < length {
    let scheme = scheme_length_at(chars, index)
    if scheme > 0 {
      let mut end = index + scheme
      let mut count = 0
      while end < length && count < 2076 && is_url_char(chars[end]) {
        end += 1
        count += 1
      }
      if count >= 1 {
        output.write_char(' ')
        index = end
        continue
      }
    }
    output.write_char(chars[index])
    index += 1
  }
  output.to_string()
}

///| Mail local-part / final host-label character class

///|
/// `[-_.0-9A-Za-z]` (upstream `Detector.MAIL_RE`).
fn is_mail_local_char(ch : Char) -> Bool {
  let cp = ch.to_int()
  if cp >= 0x30 && cp <= 0x39 {
    true
  } else if cp >= 0x41 && cp <= 0x5A {
    true
  } else if cp >= 0x61 && cp <= 0x7A {
    true
  } else {
    ch == '-' || ch == '_' || ch == '.'
  }
}

///| First host-label character class `[-_0-9A-Za-z]` (no dot), used by the

///|
/// first domain quantifier of upstream `Detector.MAIL_RE`.
fn is_mail_domain_char(ch : Char) -> Bool {
  let cp = ch.to_int()
  if cp >= 0x30 && cp <= 0x39 {
    true
  } else if cp >= 0x41 && cp <= 0x5A {
    true
  } else if cp >= 0x61 && cp <= 0x7A {
    true
  } else {
    ch == '-' || ch == '_'
  }
}

///| End index of a mail match starting at `start`, or `None`.
///

///| Mirrors the backtracking behavior of

///| `[-_.0-9A-Za-z]{1,64}@[-_0-9A-Za-z]{1,255}[-_.0-9A-Za-z]{1,255}`:

///| the local part is the maximal run of at most 64 local characters

///| directly followed by `@`; the domain consumes a maximal run of at most

///| 255 non-dot host characters, then a maximal run of at most 255 local

///| characters. When the second run is empty the first run gives back one

///|
/// character, so at least two domain characters are required.
fn mail_match_end(chars : Array[Char], start : Int) -> Int? {
  let length = chars.length()
  let mut local_end = start
  while local_end < length &&
        local_end - start < 64 &&
        is_mail_local_char(chars[local_end]) {
    local_end += 1
  }
  let local_length = local_end - start
  if local_length < 1 {
    return None
  }
  if local_length == 64 &&
    local_end < length &&
    is_mail_local_char(chars[local_end]) {
    return None
  }
  if local_end >= length || chars[local_end] != '@' {
    return None
  }
  let domain_start = local_end + 1
  let mut first_end = domain_start
  while first_end < length &&
        first_end - domain_start < 255 &&
        is_mail_domain_char(chars[first_end]) {
    first_end += 1
  }
  let first_length = first_end - domain_start
  if first_length < 1 {
    return None
  }
  let mut second_end = first_end
  while second_end < length &&
        second_end - first_end < 255 &&
        is_mail_local_char(chars[second_end]) {
    second_end += 1
  }
  let second_length = second_end - first_end
  if second_length >= 1 {
    Some(second_end)
  } else if first_length >= 2 {
    Some(first_end)
  } else {
    None
  }
}

///| Upstream `Detector.MAIL_RE.sub(' ', text)` (`detector.py:54,105`).

///|
/// Leftmost, non-overlapping matches are replaced by one space (V-41).
fn strip_mail_addresses(text : String) -> String {
  let chars = text.to_array()
  let length = chars.length()
  let output = StringBuilder()
  let mut index = 0
  while index < length {
    match mail_match_end(chars, index) {
      Some(end) => {
        output.write_char(' ')
        index = end
      }
      None => {
        output.write_char(chars[index])
        index += 1
      }
    }
  }
  output.to_string()
}

///| Append text for detection (upstream `detector.py:99-112`).
///

///| Order is part of the contract: URL removal, mail removal, Vietnamese

///| diacritic normalization, truncation to `max_text_length` **cleaned**

///| codepoints, then collapse of consecutive U+0020 (tabs and newlines are

///| preserved). `pre` starts as a non-space, so a leading space is kept.

///| The cleaned chunk is appended to `text`; the method never reinitializes

///|
/// the `langprob` cache (V-47).
pub fn Detector::append(self : Detector, text : String) -> Unit {
  let without_urls = strip_urls(text)
  let without_mail = strip_mail_addresses(without_urls)
  let normalized = NGram::normalize_vi(without_mail)
  let chars = normalized.to_array()
  let limit = if chars.length() < self.max_text_length {
    chars.length()
  } else {
    self.max_text_length
  }
  let buffer = StringBuilder()
  let mut previous_space = false
  let mut index = 0
  while index < limit {
    let ch = chars[index]
    if ch != ' ' || !previous_space {
      buffer.write_char(ch)
    }
    previous_space = ch == ' '
    index += 1
  }
  self.text = self.text + buffer.to_string()
}

///| Raise code 4 when no profiles are loaded (the observable path of

///|
/// `Detector::new()` and of a factory whose containers were cleared).
fn Detector::ensure_loaded(self : Detector) -> Unit raise LangDetectError {
  if self.langlist.is_empty() {
    raise CantDetect(
      code=ERROR_NEED_LOAD_PROFILE,
      message="Need to load profiles.",
      input_len=self.text.char_length(),
      input_prefix=input_prefix(self.text, 32),
    )
  }
}

///| Filter and sort the raw probability vector: keep entries strictly

///| greater than 0.1, then order by descending probability while keeping

///| the language-list order on ties (upstream `_sort_probability`,

///| `detector.py:234-237`; V-49 strict threshold, V-50 stable ties).
///

///| NaN never passes the strict comparison, so a NaN-prior vector produces

///|
/// an empty result (V-51). Negative zero is also filtered out.
fn sort_probability(
  langlist : Array[String],
  prob : Array[Double],
) -> Array[LangProb] {
  let limit = if langlist.length() < prob.length() {
    langlist.length()
  } else {
    prob.length()
  }
  let filtered : Array[LangProb] = []
  let mut index = 0
  while index < limit {
    let value = prob[index]
    if value > PROB_THRESHOLD {
      filtered.push({ lang: Some(langlist[index]), prob: value, })
    }
    index += 1
  }
  // Stable descending selection sort: the strict `>` keeps the earliest
  // remaining entry when probabilities are equal.
  let remaining = filtered.copy()
  let result : Array[LangProb] = []
  while !remaining.is_empty() {
    let mut best = 0
    let mut cursor = 1
    while cursor < remaining.length() {
      if remaining[cursor].prob > remaining[best].prob {
        best = cursor
      }
      cursor += 1
    }
    result.push(remaining[best])
    let _ = remaining.remove(best)
  }
  result
}

///| Diagnostic seam used by the production-side threshold test (V-49):

///| replace the cached raw probability vector without running the random

///| block, after which `get_probabilities` applies the real strict

///| `> 0.1` filter and stable descending sort. `langprob` itself is only

///|
/// readable outside this package.
pub fn Detector::set_raw_probabilities(
  self : Detector,
  raw : Array[Double],
) -> Unit {
  self.langprob = Some(raw)
}

///| Upstream `Detector.get_probabilities` (`detector.py:141-144`):

///| lazily run the detection block once, cache the raw vector, and return

///| the filtered/sorted entries. A cached vector is sorted again without

///|
/// recomputation (V-47). Raises code 4 when no profiles are loaded.
pub fn Detector::get_probabilities(
  self : Detector,
) -> Array[LangProb] raise LangDetectError {
  self.ensure_loaded()
  match self.langprob {
    Some(cached) => sort_probability(self.langlist, cached)
    None => {
      let input_text = self.text
      // Upstream cleaning happens in place on first detection (contract
      // §3.2 point 5); the error payload keeps the pre-cleaning text.
      self.text = cleaning_text(self.text)
      let raw = detect_block(
        self.text,
        self.word_lang_prob_map,
        alpha=self.alpha,
        seed=self.seed,
        prior_map=self.prior_map,
        n_trial=self.n_trial,
      ) catch {
        CantDetect(code~, message~, ..) =>
          raise CantDetect(
            code~,
            message~,
            input_len=input_text.char_length(),
            input_prefix=input_prefix(input_text, 32),
          )
      }
      self.langprob = Some(raw)
      sort_probability(self.langlist, raw)
    }
  }
}

///| Upstream `Detector.detect` (`detector.py:132-139`): the language with

///| the highest filtered probability, or `"unknown"` when the filtered

///|
/// list is empty (NaN prior, V-51).
pub fn Detector::detect(self : Detector) -> String raise LangDetectError {
  let probabilities = self.get_probabilities()
  if probabilities.is_empty() {
    return UNKNOWN_LANG
  }
  match probabilities[0].lang {
    Some(lang) => lang
    None => UNKNOWN_LANG
  }
}
