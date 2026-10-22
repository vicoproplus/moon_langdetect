///| Golden-comparison diagnostic CLI (Task 10 phase 10a).
///
/// Contract: one JSON line in, one JSON line out. The input is read from
/// `@env.args()[1]` because core has no stdin entry point; with no argument
/// the fixed default `langs` case below is used (phase 10b's C6 script runs
/// the binary while sampling the network, with stdin redirected and ignored).
/// Printing here is the sanctioned NE1 exception for this diagnostic tool:
/// `src/core`, every other library package and `src/core/cmd/main` stay
/// silent.
///
/// Modes (input fields `mode`, `text`, `text2?`, `seed`, `max_length?`):
/// - `langs`: local factory, seed applied before `create`, append, probs.
/// - `confidence`: `@core.detect_with_confidence(text)`.
/// - `meta`: lang list, entry total, vector length.
/// - `cleaning`: append (+ optional truncation), then `cleaning_text`.
/// - `features`: append + cleaning, then raw `@core.extract_ngrams`.
/// - `cache`: probabilities, then append `text2` and probabilities again.
///
/// Every failure is reported as a valid JSON line whose `error` object holds
/// the four forensics fields (`code`, `message`, `input_len`, `input_prefix`);
/// the two forensics fields are computed from the original `text` argument,
/// matching the public `detect` / `detect_langs` contract (spec §5.8).

///|
/// Default input (no argv): a valid `langs` case with fixed English text and
/// seed 0, so the binary performs one complete detection while phase 10b
/// samples its network usage.
const DEFAULT_INPUT : String = "{\"mode\":\"langs\",\"text\":\"The quick brown fox jumps over the lazy dog.\",\"seed\":0}"

///|
/// Build one JSON object from ordered key/value pairs.
fn json_object(pairs : Array[(String, Json)]) -> Json {
  let members : Map[String, Json] = Map([])
  for pair in pairs {
    let (key, value) = pair
    members.set(key, value)
  }
  Json::object(members)
}

///|
/// Read a string field; missing or non-string values become `""`.
fn string_field(obj : Map[String, Json], key : String) -> String {
  match obj.get(key) {
    Some(Json::String(text)) => text
    _ => ""
  }
}

///|
/// Read the optional `seed` field: number -> `Some`, null/missing -> `None`.
fn seed_field(obj : Map[String, Json]) -> Int64? {
  match obj.get("seed") {
    Some(Json::Number(number, ..)) => Some(number.to_int64())
    _ => None
  }
}

///|
/// Read the optional `max_length` field.
fn max_length_field(obj : Map[String, Json]) -> Int? {
  match obj.get("max_length") {
    Some(Json::Number(number, ..)) => Some(number.to_int())
    _ => None
  }
}

///|
/// First `limit` codepoints of `text` (spec §5.8 `input_prefix`).
fn prefix_of(text : String, limit : Int) -> String {
  let chars = text.to_array()
  let count = if chars.length() < limit {
    chars.length()
  } else {
    limit
  }
  let output = StringBuilder()
  let mut index = 0
  while index < count {
    output.write_char(chars[index])
    index += 1
  }
  output.to_string()
}

///|
/// IEEE754 double bit pattern as 16 lowercase hex digits (big-endian).
fn prob_bits(value : Double) -> String {
  let hex = value.reinterpret_as_uint64().to_string(radix=16)
  let mut padded = hex
  while padded.length() < 16 {
    padded = "0" + padded
  }
  padded
}

///|
/// One `{"lang":...,"prob_bits":...}` entry.
fn lang_entry(entry : @core.LangProb) -> Json {
  let lang = match entry.lang {
    Some(value) => value
    None => "unknown"
  }
  json_object([
    ("lang", Json::string(lang)),
    ("prob_bits", Json::string(prob_bits(entry.prob))),
  ])
}

///|
/// Serialize a probability list in result order.
fn probs_json(probs : Array[@core.LangProb]) -> Json {
  let entries : Array[Json] = []
  for entry in probs {
    entries.push(lang_entry(entry))
  }
  Json::array(entries)
}

///|
/// The four-field error object. `input_len` / `input_prefix` come from the
/// original input text, not from the detector's cleaned copy, so they match
/// the public API's forensics fields.
fn error_json(
  mode : String,
  code : Int,
  message : String,
  text : String,
) -> Json {
  json_object([
    ("mode", Json::string(mode)),
    (
      "error",
      json_object([
        ("code", Json::number(code.to_double())),
        ("message", Json::string(message)),
        ("input_len", Json::number(text.char_length().to_double())),
        ("input_prefix", Json::string(prefix_of(text, 32))),
      ]),
    ),
  ])
}

///|
/// Load a private factory and create one detector with the requested seed
/// (upstream `DetectorFactory.seed` is copied at `create` time).
fn make_detector(
  seed : Int64?,
  max_length : Int?,
) -> @core.Detector raise @core.LangDetectError {
  let factory = @core.DetectorFactory::new()
  factory.load_profile()
  factory.set_seed(seed)
  let detector = factory.create()
  match max_length {
    Some(limit) => detector.set_max_text_length(limit)
    None => ()
  }
  detector
}

///|
/// `langs` mode: one `detect_langs` equivalent with the requested seed.
fn langs_json(
  obj : Map[String, Json],
) -> Json raise @core.LangDetectError {
  let text = string_field(obj, "text")
  let detector = make_detector(seed_field(obj), max_length_field(obj))
  detector.append(text)
  let probs = detector.get_probabilities()
  json_object([
    ("mode", Json::string("langs")),
    ("langs", probs_json(probs)),
  ])
}

///|
/// `confidence` mode: the low-confidence entry point.
fn confidence_json(obj : Map[String, Json]) -> Json {
  let text = string_field(obj, "text")
  let result = @core.detect_with_confidence(text)
  match result {
    @core.LowConfidence(char_count~) =>
      json_object([
        ("mode", Json::string("confidence")),
        ("confidence", Json::string("low")),
        ("char_count", Json::number(char_count.to_double())),
      ])
    @core.Detected(lang~, probs~) =>
      json_object([
        ("mode", Json::string("confidence")),
        ("confidence", Json::string("detected")),
        ("char_count", Json::number(text.char_length().to_double())),
        ("lang", Json::string(lang)),
        ("langs", probs_json(probs)),
      ])
  }
}

///|
/// `meta` mode: language list, total `freq` entries, vector length, plus the
/// first-load timings used for U-06 (first load + parse of the 184129
/// embedded profile entries). The two millisecond figures are measured in
/// this cold process: `parse_ms` covers `@data.parse_profiles` alone and
/// `load_ms` covers the full `load_profile` (parse + probability table).
fn meta_json() -> Json raise @core.LangDetectError {
  let start_parse = @env.now()
  let profiles = @data.parse_profiles(@data.profiles_flat())
  let parse_ms = (@env.now() - start_parse).reinterpret_as_int64().to_int()
  let start_load = @env.now()
  let factory = @core.DetectorFactory::new()
  factory.load_profile()
  let load_ms = (@env.now() - start_load).reinterpret_as_int64().to_int()
  let lang_list = factory.get_lang_list()
  let mut entry_total = 0
  for profile in profiles {
    entry_total += profile.freq.length()
  }
  let langs : Array[Json] = []
  for lang in lang_list {
    langs.push(Json::string(lang))
  }
  json_object([
    ("mode", Json::string("meta")),
    ("lang_list", Json::array(langs)),
    ("lang_list_len", Json::number(lang_list.length().to_double())),
    ("entry_total", Json::number(entry_total.to_double())),
    ("vector_len", Json::number(@core.debug_vector_len().to_double())),
    ("parse_ms", Json::number(parse_ms.to_double())),
    ("load_ms", Json::number(load_ms.to_double())),
  ])
}

///|
/// `cleaning` mode: append (URL/mail/VI/truncation/space collapse), then the
/// non-Latin cleaning pass.
fn cleaning_json(
  obj : Map[String, Json],
) -> Json raise @core.LangDetectError {
  let detector = make_detector(seed_field(obj), max_length_field(obj))
  detector.append(string_field(obj, "text"))
  detector.cleaning_text()
  json_object([
    ("mode", Json::string("cleaning")),
    ("text", Json::string(detector.text)),
  ])
}

///|
/// `features` mode: the raw n-gram sequence (V-46).
fn features_json(
  obj : Map[String, Json],
) -> Json raise @core.LangDetectError {
  let detector = make_detector(seed_field(obj), max_length_field(obj))
  detector.append(string_field(obj, "text"))
  detector.cleaning_text()
  let grams = @core.extract_ngrams(detector.text)
  let entries : Array[Json] = []
  for gram in grams {
    entries.push(Json::string(gram))
  }
  json_object([
    ("mode", Json::string("features")),
    ("grams", Json::array(entries)),
  ])
}

///|
/// `cache` mode: probabilities before and after a second append (V-47).
fn cache_json(obj : Map[String, Json]) -> Json raise @core.LangDetectError {
  let detector = make_detector(seed_field(obj), max_length_field(obj))
  detector.append(string_field(obj, "text"))
  let probs1 = detector.get_probabilities()
  detector.append(string_field(obj, "text2"))
  let probs2 = detector.get_probabilities()
  json_object([
    ("mode", Json::string("cache")),
    ("probs1", probs_json(probs1)),
    ("probs2", probs_json(probs2)),
  ])
}

///|
/// Dispatch one parsed input object.
fn dispatch(obj : Map[String, Json]) -> Json {
  let mode = string_field(obj, "mode")
  let text = string_field(obj, "text")
  try {
    match mode {
      "langs" => langs_json(obj)
      "confidence" => confidence_json(obj)
      "meta" => meta_json()
      "cleaning" => cleaning_json(obj)
      "features" => features_json(obj)
      "cache" => cache_json(obj)
      _ =>
        error_json(
          mode,
          -1,
          "unknown mode: " + mode,
          text,
        )
    }
  } catch {
    @core.LangDetectError::CantDetect(code~, message~, ..) =>
      error_json(mode, code, message, text)
  }
}

///|
/// Entry point: parse argv[1] (or use the fixed default), print one JSON line.
fn main {
  let args = @env.args()
  let input = if args.length() >= 2 {
    args[1]
  } else {
    DEFAULT_INPUT
  }
  let parsed : Json? = try {
    Some(@json.parse(input))
  } catch {
    _ => None
  }
  let output = match parsed {
    None =>
      error_json("input", -1, "invalid JSON input", input)
    Some(Json::Object(obj)) => dispatch(obj)
    Some(_) => error_json("input", -1, "input must be a JSON object", input)
  }
  println(output.stringify())
}
