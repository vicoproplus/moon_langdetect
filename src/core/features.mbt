///| Feature extraction, ported from `Detector._extract_ngrams`
///| (`detector.py:189-203`).
///
///| `extract_ngrams` returns the **raw** n-gram sequence of `text`: it
///| applies the per-codepoint normalization through `NGram::add_char`, the
///| capital-word suppression, and the "skip a bare space" rule, but it does
///| **not** filter by the profile vocabulary. Upstream additionally keeps
///| only grams present in `word_lang_prob_map`; that vocabulary filter is
///| the job of the detection path (Task 7/8), which owns the loaded
///| profiles. Keeping the raw sequence here makes V-46 directly observable.
///
///| The loop mirrors the upstream optimized form: after adding a
///| character, every n in 1..3 is considered while the raw buffer still
///| has n codepoints; a space at n = 1 does not stop n = 2 / 3.
pub fn extract_ngrams(text : String) -> Array[String] {
  let result : Array[String] = []
  let ngram = NGram::new()
  for ch in text.iter() {
    ngram.add_char(ch)
    if ngram.is_capitalword() {
      continue
    }
    for n in 1..=N_GRAM {
      match ngram.raw_tail(n) {
        Some(gram) => {
          if gram != " " {
            result.push(gram)
          }
        }
        None => break
      }
    }
  }
  result
}
