///| The single error type of the port (spec §5.8, `[EXT]` G-30).
///
///| Upstream `LangDetectException` carries only a code and the message
///| (`str(e)`); `input_len` and `input_prefix` are the product forensics
///| fields: the codepoint count of the failing input and its first 32
///| codepoints. The library never writes the record anywhere — the caller
///| serializes the four fields (spec §9.1, zero side effects).
///
///| Code domain 0..8 (`docs/port/upstream-behavior-contract.md` §9):
///| codes 0, 6 and 7 are reserved and have no raise site upstream (V-13),
///| so this port never raises them either.
pub(all) suberror LangDetectError {
  CantDetect(
    code~ : Int,
    message~ : String,
    input_len~ : Int,
    input_prefix~ : String
  )
}

///| Error code 0, `NoTextError`: reserved upstream error code with no raise
///| site in the package (V-13). Kept so the numeric domain stays 0..8.
pub const ERROR_NO_TEXT : Int = 0

///| Error code 1, `FormatError`: profile parse failure / structural
///| mismatch / `n_words` out of range or zero / duplicate language inside
///| the profile directory.
pub const ERROR_FORMAT : Int = 1

///| Error code 2, `FileLoadError`: opening a profile raised `IOError`.
pub const ERROR_FILE_LOAD : Int = 2

///| Error code 3, `DuplicateLangError`: `add_profile` was given a language
///| that is already loaded.
pub const ERROR_DUPLICATE_LANG : Int = 3

///| Error code 4, `NeedLoadProfileError`: detection before loading, empty
///| profile directory, or fewer than two profiles.
pub const ERROR_NEED_LOAD_PROFILE : Int = 4

///| Error code 5, `CantDetectError`: no feature could be extracted from the
///| cleaned text (message `No features in text.`, V-44).
pub const ERROR_CANT_DETECT : Int = 5

///| Error code 6, `CantOpenTrainData`: reserved upstream error code with no
///| raise site in the package (V-13).
pub const ERROR_CANT_OPEN_TRAIN_DATA : Int = 6

///| Error code 7, `TrainDataFormatError`: reserved upstream error code with
///| no raise site in the package (V-13).
pub const ERROR_TRAIN_DATA_FORMAT : Int = 7

///| Error code 8, `InitParamError`: a prior entry is negative, or the prior
///| sum is not positive.
pub const ERROR_INIT_PARAM : Int = 8
