// Char 语义探针：Python `str.isupper()` 与 MoonBit 侧 `@ucd.is_uppercase` 逐点对拍。
//
// 上游依据（只读，未改）：
//   langdetect/langdetect/utils/ngram.py:44-48  `ch.isupper()` -> `capitalword`
//   langdetect/langdetect/detector.py:190-191   `if ngram.capitalword: continue`
//
// 输出格式（stdout，一行一条）：
//   SKIP <cp>                       该码点无法构造 Char（surrogate 区）
//   ISUB <start> <hex8>             32 个码点的 isupper 位集，bit i = cp start+i
//   SAMPLE <cp> <cat> <0|1>         三类抽样字符的类别与 isupper
fn main {
  // ① 全码点 isupper 位集（每 32 个码点打包成 8 位十六进制）。
  let mut start = 0
  let mut none_count = 0
  while start <= 0x10FFFF {
    let mut bits = 0U
    let mut alt = 0U
    let mut lub = 0U
    let mut v15 = 0U
    let mut i = 0
    while i < 32 && start + i <= 0x10FFFF {
      match (start + i).to_char() {
        None => none_count += 1
        Some(ch) => {
          if @ucd.is_uppercase(ch) {
            bits = bits | (1U << i)
          }
          // 替代路径：to_simple_uppercase 恒等 且 to_simple_lowercase 改变
          if @ucd.to_simple_uppercase(ch) == ch &&
            @ucd.to_simple_lowercase(ch) != ch {
            alt = alt | (1U << i)
          }
          // 替代路径 3：is_uppercase 且不属于 Unicode 15.0 之后新增的大写集
          if @ucd.is_uppercase(ch) && !post15_upper(start + i) {
            v15 = v15 | (1U << i)
          }
          // 替代路径 2：general_category == Lu
          if @ucd.general_category(ch) == @ucd.GeneralCategory::Lu {
            lub = lub | (1U << i)
          }
        }
      }
      i += 1
    }
    println("ISUB \{start} \{bits.to_string(radix=16)}")
    println("ALTB \{start} \{alt.to_string(radix=16)}")
    println("LUB \{start} \{lub.to_string(radix=16)}")
    println("V15 \{start} \{v15.to_string(radix=16)}")
    start += 32
  }

  println("NONECOUNT \{none_count}")

  // ② surrogate 区探测：确认这两个端点无法构造 Char。
  for cp in [0xD800, 0xDFFF] {
    match cp.to_char() {
      None => println("SKIP \{cp}")
      Some(_) => println("SKIP \{cp} false")
    }
  }

  // ②b 逐码点类别（仅对指定清单，用于把不一致码点归类）
  for cp in detail_cps() {
    match cp.to_char() {
      None => println("CAT \{cp} <invalid> 0")
      Some(ch) => {
        let cat = @ucd.general_category(ch).to_string()
        let up = if @ucd.is_uppercase(ch) { 1 } else { 0 }
        println("CAT \{cp} \{cat} \{up}")
      }
    }
  }

  // ③ 三类抽样字符（Lu / Lt / 无 cased 属性的非 ASCII）。
  for cp in sample_cps() {
    match cp.to_char() {
      None => println("SAMPLE \{cp} <invalid> 0")
      Some(ch) => {
        let cat = @ucd.general_category(ch).to_string()
        let up = if @ucd.is_uppercase(ch) { 1 } else { 0 }
        println("SAMPLE \{cp} \{cat} \{up}")
      }
    }
  }
}

///|
/// 实测得到的「Unicode 18 有、Unicode 15.0 无」的大写码点（共 75 个，
/// 见 docs/port/golden/char_isupper_compare.json 的 point_mismatches_all）。
/// 这是把 MoonBit 侧 is_uppercase 对齐到 CPython 3.12 (Unicode 15.0) 的补丁表。
fn post15_upper(cp : Int) -> Bool {
  (cp >= 0x1C89 && cp <= 0x1C89) ||
  (cp >= 0xA7CB && cp <= 0xA7CC) ||
  (cp >= 0xA7CE && cp <= 0xA7CE) ||
  (cp >= 0xA7D2 && cp <= 0xA7D2) ||
  (cp >= 0xA7D4 && cp <= 0xA7D4) ||
  (cp >= 0xA7DA && cp <= 0xA7DA) ||
  (cp >= 0xA7DC && cp <= 0xA7DD) ||
  (cp >= 0xA7E2 && cp <= 0xA7E2) ||
  (cp >= 0xAB6C && cp <= 0xAB6D) ||
  (cp >= 0x10D50 && cp <= 0x10D65) ||
  (cp >= 0x16EA0 && cp <= 0x16EB8) ||
  (cp >= 0x1DF40 && cp <= 0x1DF40) ||
  (cp >= 0x1DF48 && cp <= 0x1DF48) ||
  (cp >= 0x1DF4A && cp <= 0x1DF4A) ||
  (cp >= 0x1DF4D && cp <= 0x1DF4D) ||
  (cp >= 0x1DF51 && cp <= 0x1DF51) ||
  (cp >= 0x1DF68 && cp <= 0x1DF68) ||
  (cp >= 0x1DF6A && cp <= 0x1DF6A) ||
  (cp >= 0x1DF6C && cp <= 0x1DF6C) ||
  (cp >= 0x1DF6E && cp <= 0x1DF6E) ||
  (cp >= 0x1DF72 && cp <= 0x1DF72) ||
  (cp >= 0x1DF74 && cp <= 0x1DF74) ||
  (cp >= 0x1DF76 && cp <= 0x1DF76) ||
  (cp >= 0x1DF78 && cp <= 0x1DF78) ||
  (cp >= 0x1DF7A && cp <= 0x1DF7A) ||
  (cp >= 0x1DF7C && cp <= 0x1DF7C) ||
  (cp >= 0x1DF7E && cp <= 0x1DF7E)
}

///|
/// 需要逐点查类别的码点（对拍脚本回填的不一致清单 + 抽样点）。
fn detail_cps() -> Array[Int] {
  [
    0x1C89, 0xA7CB, 0xA7CC, 0xAB6C, 0x10D50, 0x16EA0, 0x16EAF,
    0x1DF40, 0x1DF7E, 0x3D2, 0x1F88, 0x1C5,
  ]
}

///|
/// 三类抽样码点：Lu、Lt、以及无 cased 属性的非 ASCII（CJK/假名/谚文/阿拉伯/
/// 天城文数字/emoji/组合符/空格）。
fn sample_cps() -> Array[Int] {
  [
    // Lu
    0xC4, // Ä
    0x130, // İ
    0x3A9, // Ω
    0x416, // Ж
    // Lt（标题大小写）
    0x1C5, // ǅ
    0x1C8, // ǈ
    // 无 cased 属性
    0x4E00, // 一
    0x3042, // あ
    0xAC00, // 가
    0x628, // ب
    0x967, // १
    0x1F600, // 😀
    0x301, // 组合符 U+0301
    0x2000, // 空格 U+2000
    // 补充：Nl 罗马数字、So 带圈字母（Python 里 isupper 为 True）
    0x2160, // Ⅰ
    0x24B6, // Ⓐ
    0xB2, // ²（No，isupper False）
  ]
}
