// 由 probes/gen_mbt.py 生成，勿手改。

test "entries af" {
  assert_eq(@data.entry_count("af"), 2143)
  let m = match @data.profile("af") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2143)
  assert_eq(m.get("D"), Some(9246))
}

test "entries ar" {
  assert_eq(@data.entry_count("ar"), 2626)
  let m = match @data.profile("ar") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2626)
  assert_eq(m.get("و"), Some(674395))
}

test "entries bg" {
  assert_eq(@data.entry_count("bg"), 2597)
  let m = match @data.profile("bg") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2597)
  assert_eq(m.get("D"), Some(2636))
}

test "entries bn" {
  assert_eq(@data.entry_count("bn"), 2846)
  let m = match @data.profile("bn") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2846)
  assert_eq(m.get("D"), Some(455))
}

test "entries ca" {
  assert_eq(@data.entry_count("ca"), 6331)
  let m = match @data.profile("ca") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 6331)
  assert_eq(m.get("A"), Some(167967))
}

test "entries cs" {
  assert_eq(@data.entry_count("cs"), 2957)
  let m = match @data.profile("cs") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2957)
  assert_eq(m.get("D"), Some(14883))
}

test "entries cy" {
  assert_eq(@data.entry_count("cy"), 4795)
  let m = match @data.profile("cy") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 4795)
  assert_eq(m.get("D"), Some(338489))
}

test "entries da" {
  assert_eq(@data.entry_count("da"), 2320)
  let m = match @data.profile("da") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2320)
  assert_eq(m.get("D"), Some(31963))
}

test "entries de" {
  assert_eq(@data.entry_count("de"), 2316)
  let m = match @data.profile("de") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2316)
  assert_eq(m.get("D"), Some(565432))
}

test "entries el" {
  assert_eq(@data.entry_count("el"), 2747)
  let m = match @data.profile("el") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2747)
  assert_eq(m.get("D"), Some(1964))
}

test "entries en" {
  assert_eq(@data.entry_count("en"), 2301)
  let m = match @data.profile("en") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2301)
  assert_eq(m.get("D"), Some(662077))
}

test "entries es" {
  assert_eq(@data.entry_count("es"), 2137)
  let m = match @data.profile("es") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2137)
  assert_eq(m.get("D"), Some(116547))
}

test "entries et" {
  assert_eq(@data.entry_count("et"), 7046)
  let m = match @data.profile("et") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 7046)
  assert_eq(m.get("D"), Some(3604))
}

test "entries fa" {
  assert_eq(@data.entry_count("fa"), 2185)
  let m = match @data.profile("fa") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2185)
  assert_eq(m.get("٬"), Some(970))
}

test "entries fi" {
  assert_eq(@data.entry_count("fi"), 2287)
  let m = match @data.profile("fi") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2287)
  assert_eq(m.get("D"), Some(15745))
}

test "entries fr" {
  assert_eq(@data.entry_count("fr"), 2232)
  let m = match @data.profile("fr") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2232)
  assert_eq(m.get("D"), Some(116102))
}

test "entries gu" {
  assert_eq(@data.entry_count("gu"), 1474)
  let m = match @data.profile("gu") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 1474)
  assert_eq(m.get("ૈદિ"), Some(382))
}

test "entries he" {
  assert_eq(@data.entry_count("he"), 2785)
  let m = match @data.profile("he") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2785)
  assert_eq(m.get("D"), Some(3214))
}

test "entries hi" {
  assert_eq(@data.entry_count("hi"), 2400)
  let m = match @data.profile("hi") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2400)
  assert_eq(m.get("ौद्"), Some(366))
}

test "entries hr" {
  assert_eq(@data.entry_count("hr"), 2431)
  let m = match @data.profile("hr") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2431)
  assert_eq(m.get("D"), Some(8690))
}

test "entries hu" {
  assert_eq(@data.entry_count("hu"), 2808)
  let m = match @data.profile("hu") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2808)
  assert_eq(m.get("D"), Some(13198))
}

test "entries id" {
  assert_eq(@data.entry_count("id"), 1960)
  let m = match @data.profile("id") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 1960)
  assert_eq(m.get("D"), Some(29898))
}

test "entries it" {
  assert_eq(@data.entry_count("it"), 1955)
  let m = match @data.profile("it") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 1955)
  assert_eq(m.get("D"), Some(94947))
}

test "entries ja" {
  assert_eq(@data.entry_count("ja"), 1831)
  let m = match @data.profile("ja") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 1831)
  assert_eq(m.get("é"), Some(1545))
}

test "entries kn" {
  assert_eq(@data.entry_count("kn"), 2860)
  let m = match @data.profile("kn") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2860)
  assert_eq(m.get("ುರಾ"), Some(118))
}

test "entries ko" {
  assert_eq(@data.entry_count("ko"), 23031)
  let m = match @data.profile("ko") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 23031)
  assert_eq(m.get("정리이"), Some(69))
}

test "entries lt" {
  assert_eq(@data.entry_count("lt"), 6593)
  let m = match @data.profile("lt") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 6593)
  assert_eq(m.get("ūdu"), Some(237))
}

test "entries lv" {
  assert_eq(@data.entry_count("lv"), 7563)
  let m = match @data.profile("lv") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 7563)
  assert_eq(m.get("ūci"), Some(182))
}

test "entries mk" {
  assert_eq(@data.entry_count("mk"), 2412)
  let m = match @data.profile("mk") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2412)
  assert_eq(m.get("D"), Some(603))
}

test "entries ml" {
  assert_eq(@data.entry_count("ml"), 2786)
  let m = match @data.profile("ml") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2786)
  assert_eq(m.get("D"), Some(213))
}

test "entries mr" {
  assert_eq(@data.entry_count("mr"), 2578)
  let m = match @data.profile("mr") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2578)
  assert_eq(m.get("णां"), Some(79))
}

test "entries ne" {
  assert_eq(@data.entry_count("ne"), 2382)
  let m = match @data.profile("ne") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2382)
  assert_eq(m.get("ेश्"), Some(122))
}

test "entries nl" {
  assert_eq(@data.entry_count("nl"), 2163)
  let m = match @data.profile("nl") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2163)
  assert_eq(m.get("D"), Some(295391))
}

test "entries no" {
  assert_eq(@data.entry_count("no"), 2287)
  let m = match @data.profile("no") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2287)
  assert_eq(m.get("D"), Some(67298))
}

test "entries pa" {
  assert_eq(@data.entry_count("pa"), 2318)
  let m = match @data.profile("pa") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2318)
  assert_eq(m.get("ਾਜ਼"), Some(17))
}

test "entries pl" {
  assert_eq(@data.entry_count("pl"), 2629)
  let m = match @data.profile("pl") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2629)
  assert_eq(m.get("D"), Some(76546))
}

test "entries pt" {
  assert_eq(@data.entry_count("pt"), 2162)
  let m = match @data.profile("pt") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2162)
  assert_eq(m.get("D"), Some(84998))
}

test "entries ro" {
  assert_eq(@data.entry_count("ro"), 6071)
  let m = match @data.profile("ro") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 6071)
  assert_eq(m.get("D"), Some(14206))
}

test "entries ru" {
  assert_eq(@data.entry_count("ru"), 2770)
  let m = match @data.profile("ru") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2770)
  assert_eq(m.get("D"), Some(12949))
}

test "entries sk" {
  assert_eq(@data.entry_count("sk"), 2868)
  let m = match @data.profile("sk") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2868)
  assert_eq(m.get("D"), Some(6323))
}

test "entries sl" {
  assert_eq(@data.entry_count("sl"), 6415)
  let m = match @data.profile("sl") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 6415)
  assert_eq(m.get("D"), Some(7697))
}

test "entries so" {
  assert_eq(@data.entry_count("so"), 1874)
  let m = match @data.profile("so") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 1874)
  assert_eq(m.get("YO "), Some(13))
}

test "entries sq" {
  assert_eq(@data.entry_count("sq"), 2304)
  let m = match @data.profile("sq") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2304)
  assert_eq(m.get("D"), Some(2951))
}

test "entries sv" {
  assert_eq(@data.entry_count("sv"), 2404)
  let m = match @data.profile("sv") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2404)
  assert_eq(m.get("D"), Some(81614))
}

test "entries sw" {
  assert_eq(@data.entry_count("sw"), 1770)
  let m = match @data.profile("sw") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 1770)
  assert_eq(m.get("jer"), Some(348))
}

test "entries ta" {
  assert_eq(@data.entry_count("ta"), 2249)
  let m = match @data.profile("ta") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2249)
  assert_eq(m.get("D"), Some(612))
}

test "entries te" {
  assert_eq(@data.entry_count("te"), 2797)
  let m = match @data.profile("te") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2797)
  assert_eq(m.get("ొరి"), Some(395))
}

test "entries th" {
  assert_eq(@data.entry_count("th"), 3426)
  let m = match @data.profile("th") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 3426)
  assert_eq(m.get("D"), Some(2767))
}

test "entries tl" {
  assert_eq(@data.entry_count("tl"), 1873)
  let m = match @data.profile("tl") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 1873)
  assert_eq(m.get("D"), Some(3787))
}

test "entries tr" {
  assert_eq(@data.entry_count("tr"), 2584)
  let m = match @data.profile("tr") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2584)
  assert_eq(m.get("D"), Some(20468))
}

test "entries uk" {
  assert_eq(@data.entry_count("uk"), 2531)
  let m = match @data.profile("uk") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2531)
  assert_eq(m.get("D"), Some(2686))
}

test "entries ur" {
  assert_eq(@data.entry_count("ur"), 2310)
  let m = match @data.profile("ur") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2310)
  assert_eq(m.get("ٹ"), Some(7565))
}

test "entries vi" {
  assert_eq(@data.entry_count("vi"), 6354)
  let m = match @data.profile("vi") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 6354)
  assert_eq(m.get("D"), Some(18934))
}

test "entries zh-cn" {
  assert_eq(@data.entry_count("zh-cn"), 2151)
  let m = match @data.profile("zh-cn") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2151)
  assert_eq(m.get("·"), Some(11798))
}

test "entries zh-tw" {
  assert_eq(@data.entry_count("zh-tw"), 2104)
  let m = match @data.profile("zh-tw") {
    Some(m) => m
    None => abort("missing profile")
  }
  assert_eq(m.length(), 2104)
  assert_eq(m.get("·"), Some(11773))
}

test "language count" {
  assert_eq(@data.languages.length(), 55)
}
