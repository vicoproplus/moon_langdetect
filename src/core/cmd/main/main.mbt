///|
/// Silent executable entry (spec §4A line 422, §9.4 NE1).
///
/// Calls the package-level `detect` exactly once on a fixed built-in text and
/// discards the returned language code. Nothing is printed and no file,
/// network, or storage access is performed, so stdout and stderr both stay at
/// 0 bytes (spec §10.6 command 29). Profiles are loaded from the in-memory
/// blob embedded in `src/data`, so the run succeeds from an empty working
/// directory (PRD FR-13 / C5).
///
/// The fixed text is 44 code points, comfortably above the feature stage's
/// threshold. Any raised `LangDetectError` is swallowed so that an error
/// path can neither print nor abort: the silence contract holds on both the
/// success and the failure branch.
fn main {
  try {
    let _ = @core.detect("The quick brown fox jumps over the lazy dog.")
  } catch {
    _ => ()
  }
}
