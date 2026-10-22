///|
/// 探针：native 下用 @fs.read_file 读取档案文件，验证文件读取能力可用。
async fn main raise {
  let data : &@io.Data = @fs.read_file("../../langdetect/langdetect/profiles/en")
  let text : String = data.text()
  println("chars=\{text.length()}")
  println("has_freq=\{text.contains("freq")}")
}
