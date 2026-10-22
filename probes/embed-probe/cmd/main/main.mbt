///|
/// 探针入口：读取编译期内嵌档案并输出规模，确保数据包被真实链接。
fn main raise {
  let mut total = 0
  for lang in @data.languages {
    let n = @data.entry_count(lang)
    println("\{lang}: \{n}")
    total = total + n
  }
  println("total: \{total}")
}
