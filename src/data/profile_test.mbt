///| End-to-end checks for the embedded flat profiles and the derived
///| probability table. Parsing is deterministic, so each test re-parses the
///| same blob produced by `profiles_flat()`.

fn parsed_profiles() -> Array[@data.Profile] {
  @data.parse_profiles(@data.profiles_flat())
}

test "profiles_flat_parses_55_profiles_in_language_order" {
  let profiles = parsed_profiles()
  assert_eq(profiles.length(), 55)
  assert_eq(@data.languages.length(), 55)
  for index in 0..<profiles.length() {
    assert_eq(profiles[index].name, @data.languages[index])
    assert_eq(profiles[index].n_words.length(), 3)
    assert_true(profiles[index].n_words[0] >= 0)
    assert_true(profiles[index].n_words[1] >= 0)
    assert_true(profiles[index].n_words[2] >= 0)
  }
}

test "profile_totals_and_key_length_distribution" {
  let profiles = parsed_profiles()
  let mut total = 0
  let by_length : Array[Int] = [0, 0, 0, 0]
  let mut non_bmp_keys = 0
  for profile in profiles {
    let sums : Array[Int] = [0, 0, 0]
    for word, count in profile.freq {
      total = total + 1
      let length = word.char_length()
      if length >= 1 && length <= 3 {
        by_length[length] = by_length[length] + 1
        sums[length - 1] = sums[length - 1] + count
      }
      let mut has_non_bmp = false
      for ch in word {
        if ch.to_int() > 0xFFFF {
          has_non_bmp = true
        }
      }
      if has_non_bmp {
        non_bmp_keys = non_bmp_keys + 1
      }
    }
    assert_eq(profile.n_words[0], sums[0])
    assert_eq(profile.n_words[1], sums[1])
    assert_eq(profile.n_words[2], sums[2])
    assert_eq(profile.zero_n_words_index(), None)
  }
  assert_eq(total, 184129)
  assert_eq(by_length[1], 7791)
  assert_eq(by_length[2], 52387)
  assert_eq(by_length[3], 123951)
  assert_eq(non_bmp_keys, 0)
}

test "af_profile_matches_upstream_counts" {
  let profiles = parsed_profiles()
  let af = profiles[0]
  assert_eq(af.name, "af")
  assert_eq(af.freq.length(), 2143)
  assert_eq(af.freq.get("D"), Some(9246))
  assert_eq(af.n_words[0], 1541130)
  assert_eq(af.n_words[1], 1808182)
  assert_eq(af.n_words[2], 1328687)
}

test "build_prob_table_uses_freq_over_n_words" {
  let profiles = parsed_profiles()
  let table = @data.build_prob_table(profiles)
  assert_eq(profiles[1].name, "ar")
  assert_eq(profiles[8].name, "de")
  assert_eq(profiles[10].name, "en")
  let d = table.at("D")
  assert_eq(d.length(), 55)
  assert_eq(d[0], 9246.0 / profiles[0].n_words[0].to_double())
  // ar has no "D": a language missing the n-gram keeps 0.0.
  assert_eq(d[1], 0.0)
  let er = table.at("er")
  assert_eq(er.length(), 55)
  assert_eq(er[8], 2971302.0 / profiles[8].n_words[1].to_double())
  // af also has "er"; the same vector carries one slot per language.
  assert_eq(er[0], 33393.0 / profiles[0].n_words[1].to_double())
  let the = table.at("the")
  assert_eq(the.length(), 55)
  assert_eq(the[10], 3415279.0 / profiles[10].n_words[2].to_double())
}

test "build_prob_table_creates_zero_vector_for_over_three_gram" {
  let freq : Map[String, Int] = Map([])
  freq.set("abcd", 5)
  let profile = @data.Profile::new(
    name="synthetic",
    n_words=[1, 1, 1],
    freq=freq,
  )
  let table = @data.build_prob_table([profile])
  let vector = table.at("abcd")
  assert_eq(vector.length(), 1)
  assert_eq(vector[0], 0.0)
}

test "zero_n_words_precondition_is_observable_for_core_load_path" {
  let freq : Map[String, Int] = Map([])
  freq.set("a", 3)
  let profile = @data.Profile::new(
    name="synthetic-zero",
    n_words=[5, 0, 7],
    freq=freq,
  )
  // Task 5 does not divide with this profile: upstream raises code 1 on a
  // zero denominator, and that raise belongs to the core load path.
  assert_eq(profile.zero_n_words_index(), Some(1))
  assert_eq(profile.freq.get("a"), Some(3))
}
