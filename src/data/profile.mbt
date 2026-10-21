///| One language profile parsed from the embedded flat data.
///
///| `n_words[i]` is the total number of `(i + 1)`-codepoint n-grams in
///| `freq`; `freq` maps an n-gram to its upstream occurrence count. Fields
///| are read-only outside this package, so downstream code constructs a
///| profile with `Profile::new`.
pub struct Profile {
  name : String
  n_words : Array[Int]
  freq : Map[String, Int]
}

///| Construct a profile from its parts. `n_words` is expected to have
///| length 3 (1/2/3-gram totals). Positive denominators are a precondition
///| of `build_prob_table`; the upstream zero-division error (code 1) is
///| raised by the core load path, which owns the error type.
pub fn Profile::new(
  name~ : String,
  n_words~ : Array[Int],
  freq~ : Map[String, Int],
) -> Profile {
  { name: name, n_words: n_words, freq: freq }
}

///| Index of the first zero 1/2/3-gram total, or `None` when every total
///| is positive. The core load path uses this precondition check to raise
///| upstream error code 1 before any probability division; `src/data`
///| cannot import `LangDetectError` (that would reverse the module
///| dependency).
pub fn Profile::zero_n_words_index(self : Profile) -> Int? {
  let mut index = 0
  while index < self.n_words.length() {
    if self.n_words[index] == 0 {
      return Some(index)
    }
    index = index + 1
  }
  None
}

///| Parse the multi-profile flat blob: a line starting with `#` opens a
///| new profile (`#<name>`), every other non-empty line is `key<TAB>count`.
///| Blank lines are skipped. `n_words` is derived while parsing by summing
///| counts per codepoint length (1/2/3), matching the upstream JSON totals.
pub fn parse_profiles(flat : String) -> Array[Profile] {
  let profiles : Array[Profile] = []
  let mut name = ""
  let mut n_words : Array[Int] = [0, 0, 0]
  let mut freq : Map[String, Int] = Map([])
  let mut open_profile = false
  for line in flat.split("\n") {
    if line.is_empty() {
      continue
    }
    if line.get_char(0) == Some('#') {
      if open_profile {
        profiles.push(Profile::new(name=name, n_words=n_words, freq=freq))
      }
      name = match line.get_view(start=1) {
        Some(view) => view.to_owned()
        None => ""
      }
      n_words = [0, 0, 0]
      freq = Map([])
      open_profile = true
      continue
    }
    let (key_view, count_view) = match line.split_once("\t") {
      Some(pair) => pair
      None => abort("profile data: missing tab separator")
    }
    let key = key_view.to_owned()
    let count = try @string.parse_int(count_view) catch {
      _ => abort("profile data: invalid count")
    } noraise {
      value => value
    }
    freq.set(key, count)
    let length = key.char_length()
    if length >= 1 && length <= 3 {
      n_words[length - 1] = n_words[length - 1] + count
    }
  }
  if open_profile {
    profiles.push(Profile::new(name=name, n_words=n_words, freq=freq))
  }
  profiles
}

///| Build the upstream `word_lang_prob` table. The vector for each n-gram
///| has one slot per profile (language), in profile order; slot `index` is
///| `freq[word] / n_words[length - 1]`. A word absent from a language
///| keeps `0.0` there. Keys longer than 3 codepoints are inserted with an
///| all-zero vector but are never written (`detector_factory.py:87-92`).
///
///| Precondition: `n_words[length - 1] > 0` for every key length present
///| in the profile. Upstream raises error code 1 on a zero denominator;
///| that check belongs to the core load path (see
///| `Profile::zero_n_words_index`), not to this package.
pub fn build_prob_table(
  profiles : Array[Profile],
) -> Map[String, Array[Double]] {
  let langsize = profiles.length()
  let table : Map[String, Array[Double]] = Map([])
  let mut index = 0
  while index < langsize {
    let profile = profiles[index]
    for word, count in profile.freq {
      let vector = match table.get(word) {
        Some(existing) => existing
        None => {
          let created = Array::make(langsize, 0.0)
          table.set(word, created)
          created
        }
      }
      let length = word.char_length()
      if length >= 1 && length <= 3 {
        vector[index] = count.to_double() / profile.n_words[length - 1].to_double()
      }
    }
    index = index + 1
  }
  table
}
