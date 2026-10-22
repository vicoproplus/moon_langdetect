///| The random block of `Detector._detect_block` (`detector.py:146-171`):
/// initialize a probability vector, run `n_trial` rounds of randomly
/// sampled n-grams, detect convergence at `0.99999`, and average the
/// rounds into `langprob`.
///
/// Signature (documented contract for Task 8):
///
/// ```
/// detect_block(
///   text, word_lang_prob_map,
///   alpha~, seed~, prior_map~, n_trial~
/// ) -> Array[Double] raise LangDetectError
/// ```
///
/// * `text` is the detector text after `append` (URL / mail / Vietnamese
///   normalization). `detect_block` applies `cleaning_text` itself, as
///   upstream `_detect_block` does; the operation is idempotent (V-54).
/// * `word_lang_prob_map` is the profile vocabulary (Task 5) and the
///   authoritative source of both the feature filter and the per-word
///   probability vectors. Its vector length is the language count.
/// * `alpha~` is the detector alpha (default `ALPHA_DEFAULT = 0.5` at
///   the Task 8 call site), `seed~` the factory seed (`None` unseeded),
///   `prior_map~` the normalized prior vector or `None` for uniform
///   `1 / langsize`, and `n_trial~` the round count (`7` upstream).
///
/// Raw-to-filtered integration (R19): `extract_ngrams` (Task 6) returns
/// the **raw** n-gram sequence — every normalized 1/2/3-gram of the
/// cleaned text, including duplicates and grams absent from the
/// profiles. Upstream filters inside `_extract_ngrams` with
/// `w in self.word_lang_prob_map`; this function performs the same
/// membership filter explicitly, preserving order and duplicates, so an
/// empty result is exactly upstream's "no features" case and raises
/// code 5 with the message `No features in text.` (`V-44`). Task 8
/// passes the cleaned detector text and the shared vocabulary map; the
/// returned vector is the raw `langprob` cache (before the `> 0.1`
/// filter of `_sort_probability`, which Task 8 owns).
pub fn detect_block(
  text : String,
  word_lang_prob_map : Map[String, Array[Double]],
  alpha~ : Double,
  seed~ : Int64?,
  prior_map~ : Array[Double]?,
  n_trial~ : Int,
) -> Array[Double] raise LangDetectError {
  let cleaned = cleaning_text(text)
  let raw = extract_ngrams(cleaned)
  let ngrams : Array[String] = []
  for word in raw {
    if word_lang_prob_map.contains(word) {
      ngrams.push(word)
    }
  }
  if ngrams.is_empty() {
    raise CantDetect(
      code=ERROR_CANT_DETECT,
      message="No features in text.",
      input_len=text.char_length(),
      input_prefix=input_prefix(text, 32),
    )
  }
  let langsize = match word_lang_prob_map.get(ngrams[0]) {
    Some(vector) => vector.length()
    None => 0
  }
  let langprob = Array::make(langsize, 0.0)
  let rng = Mt19937::new(seed)
  for _round in 0..<n_trial {
    let prob = match prior_map {
      Some(prior) => prior.copy()
      None => Array::make(langsize, 1.0 / langsize.to_double())
    }
    let alpha_t = alpha + rng.gauss(0.0, 1.0) * ALPHA_WIDTH
    let weight = alpha_t / BASE_FREQ.to_double()
    let mut i = 0
    while true {
      let word = ngrams[rng.randbelow(ngrams.length())]
      match word_lang_prob_map.get(word) {
        Some(vector) => {
          let mut j = 0
          while j < langsize {
            prob[j] = prob[j] * (weight + vector[j])
            j += 1
          }
        }
        None => ()
      }
      if i % 5 == 0 {
        let maxp = normalize_prob(prob)
        if maxp > CONV_THRESHOLD || i >= ITERATION_LIMIT {
          break
        }
      }
      i += 1
    }
    let mut j = 0
    while j < langsize {
      // Upstream `langprob[j] += prob[j] / n_trial` is a plain addition;
      // it is not compensated (V-34, 385/385 naive states match).
      langprob[j] = langprob[j] + prob[j] / n_trial.to_double()
      j += 1
    }
  }
  langprob
}

///| First `limit` codepoints of the failing input, used as the
/// `input_prefix` forensics field of `CantDetect`.
fn input_prefix(text : String, limit : Int) -> String {
  let builder = StringBuilder()
  let mut count = 0
  for ch in text.iter() {
    if count >= limit {
      break
    }
    builder.write_char(ch)
    count += 1
  }
  builder.to_string()
}
