///| U3 table conformance: the full-codepoint count must equal CPython
///| 3.12.10 `str.isupper()` (1951 codepoints, surrogates skipped).

///| Full-codepoint count over 0x000000..0x10FFFF (surrogates excluded).
test "is_upper_cp312_full_count" {
  let mut count = 0
  for cp = 0; cp < 0x110000; cp = cp + 1 {
    if cp >= 0xD800 && cp <= 0xDFFF {
      continue
    }
    if @unicode.is_upper_cp312(cp) {
      count = count + 1
    }
  }
  inspect(count, content="1951")
}

///| Interval shape and boundary sampling: 651 maximal intervals cover 1951
///| codepoints; each sampled interval is true at both ends and false just
///| outside, which proves the endpoints are included and the gaps excluded.
test "is_upper_cp312_interval_boundaries" {
  let intervals = @unicode.upper_intervals
  inspect(intervals.length(), content="651")
  let mut covered = 0
  for (start, end) in intervals {
    covered = covered + (end - start + 1)
  }
  inspect(covered, content="1951")
  let samples : Array[Int] = [0, 1, 17, 100, 325, 650]
  for index in samples {
    let (start, end) = intervals[index]
    inspect(@unicode.is_upper_cp312(start), content="true")
    inspect(@unicode.is_upper_cp312(end), content="true")
    inspect(@unicode.is_upper_cp312(start - 1), content="false")
    inspect(@unicode.is_upper_cp312(end + 1), content="false")
  }
}

///| Known cased letters across scripts: uppercase members are true and
///| their lowercase partners are false (A, Latin-1, Greek, Cyrillic,
///| capital sharp s, Deseret).
test "is_upper_cp312_known_letters" {
  inspect(@unicode.is_upper_cp312(0x0041), content="true")
  inspect(@unicode.is_upper_cp312(0x0061), content="false")
  inspect(@unicode.is_upper_cp312(0x00C0), content="true")
  inspect(@unicode.is_upper_cp312(0x00E0), content="false")
  inspect(@unicode.is_upper_cp312(0x0391), content="true")
  inspect(@unicode.is_upper_cp312(0x03B1), content="false")
  inspect(@unicode.is_upper_cp312(0x0410), content="true")
  inspect(@unicode.is_upper_cp312(0x0430), content="false")
  inspect(@unicode.is_upper_cp312(0x1E9E), content="true")
  inspect(@unicode.is_upper_cp312(0x00DF), content="false")
  inspect(@unicode.is_upper_cp312(0x10400), content="true")
  inspect(@unicode.is_upper_cp312(0x10428), content="false")
  inspect(@unicode.is_upper_cp312(-1), content="false")
  inspect(@unicode.is_upper_cp312(0x110000), content="false")
  inspect(@unicode.is_upper_cp312(0xD800), content="false")
}
