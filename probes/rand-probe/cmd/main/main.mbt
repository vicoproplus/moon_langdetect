// 随机数管线探针：把 MoonBit 侧各阶段输出打到 stdout，供
// probes/rand_probe_compare.py 与 Python golden 逐位比较。
//
// 输出格式（每行一条，空格分隔）：
//   MT <seed> <index> <hex8>            MT19937 原始 32 位字
//   RND <seed> <index> <hex16>          random() 的 double 位型
//   GB <k> <index> <hex16> <dec>        getrandbits(k)
//   RB <n> <index> <dec>                _randbelow(n)
//   GAUSS <index> <hex16>               gauss(0,1)
//   GPART <index> <field> <hex16>       gauss 内部中间量
//   MIXG <round> <hex16>                混合序列每轮 gauss
//   MIXC <index> <dec>                  混合序列每次 choice 下标
//   MIXMETA <ngram_count>               混合序列元信息

fn pad16(u : UInt64) -> String {
  let s = u.to_string(radix=16)
  let mut out = ""
  for _ in 0..<(16 - s.length()) {
    out = out + "0"
  }
  out + s
}

fn hex(d : Double) -> String {
  pad16(d.reinterpret_as_uint64())
}

fn main {
  // 1) MT19937 原始 32 位字：seed=0 与 seed=42，前 64 个。
  for seed in [0U, 42U] {
    let r = @rp.Random::from_seed(seed)
    for i in 0..<64 {
      let w = r.getrandbits(32)
      println("MT \{seed} \{i} \{pad16(w)}")
    }
  }

  // 2) random() 前 64 个 double。
  for seed in [0U, 42U] {
    let r = @rp.Random::from_seed(seed)
    for i in 0..<64 {
      println("RND \{seed} \{i} \{hex(r.random())}")
    }
  }

  // 3) getrandbits(k)：每个 k 用全新的 Random(0)，前 32 个。
  for k in [1, 2, 3, 12, 16, 32, 33] {
    let r = @rp.Random::from_seed(0U)
    for i in 0..<32 {
      let v = r.getrandbits(k)
      println("GB \{k} \{i} \{pad16(v)} \{v.to_string()}")
    }
  }

  // 4) _randbelow(n)：每个 n 用全新的 Random(0)，前 32 个。
  for n in [1UL, 2UL, 3UL, 5UL, 7UL, 55UL, 1000UL] {
    let r = @rp.Random::from_seed(0U)
    for i in 0..<32 {
      let v = r.randbelow(n)
      println("RB \{n.to_string()} \{i} \{v.to_string()}")
    }
  }

  // 5) gauss(0,1) 前 64 个。
  {
    let r = @rp.Random::from_seed(0U)
    for i in 0..<64 {
      println("GAUSS \{i} \{hex(r.gauss(0.0, 1.0))}")
    }
  }

  // 6) gauss 内部中间量，前 8 次，用于把差异定位到具体数学函数。
  {
    let r = @rp.Random::from_seed(0U)
    for i in 0..<8 {
      let x2pi = r.random() * @rp.TWOPI
      let y = r.random()
      let ln_arg = 1.0 - y
      let ln_res = @rp.c_log(ln_arg)
      let g2rad = (-2.0 * ln_res).sqrt()
      let c = @math.cos(x2pi)
      let s = @math.sin(x2pi)
      let z = c * g2rad
      println("GPART \{i} x2pi \{hex(x2pi)}")
      println("GPART \{i} y \{hex(y)}")
      println("GPART \{i} ln_arg \{hex(ln_arg)}")
      println("GPART \{i} ln_result \{hex(ln_res)}")
      println("GPART \{i} g2rad \{hex(g2rad)}")
      println("GPART \{i} cos_x2pi \{hex(c)}")
      println("GPART \{i} sin_x2pi \{hex(s)}")
      println("GPART \{i} z \{hex(z)}")
      println("GPART \{i} gauss_next \{hex(s * g2rad)}")
    }
  }

  // 7) 模拟上游混合调用序列（seed=0，long-af，ngram_count=667）：
  //    每轮 1 次 gauss(0,1) + 该轮次数的 _randbelow(667)。
  let counts : Array[Int] = [51, 51, 51, 76, 36, 51, 41]
  let ngram_count = 667UL
  println("MIXMETA \{ngram_count.to_string()}")
  {
    let r = @rp.Random::from_seed(0U)
    let mut idx = 0
    for round in 0..<7 {
      let g = r.gauss(0.0, 1.0)
      let alpha = 0.5 + g * 0.05
      println("MIXG \{round} \{hex(g)}")
      println("MIXA \{round} \{hex(alpha)}")
      for _ in 0..<counts[round] {
        println("MIXC \{idx} \{r.randbelow(ngram_count).to_string()}")
        idx += 1
      }
    }
  }

  // 8) 压力序列：多 seed 的 gauss 长序列 + 数学函数采样。
  // 对照：gauss 改用 @math.ln（纯 MoonBit log）时的结果，用于量化分界点。
  for seed in [0U, 1U, 42U, 12345U] {
    let r = @rp.Random::from_seed(seed)
    for i in 0..<512 {
      println("GAUSSM \{seed} \{i} \{hex(r.gauss_moonmath(0.0, 1.0))}")
    }
  }
  for seed in [0U, 1U, 42U, 12345U] {
    let r = @rp.Random::from_seed(seed)
    for i in 0..<512 {
      println("GAUSSS \{seed} \{i} \{hex(r.gauss(0.0, 1.0))}")
    }
  }
  for seed in [0U, 1U, 42U, 12345U] {
    let r = @rp.Random::from_seed(seed)
    for i in 0..<256 {
      let x2pi = r.random() * @rp.TWOPI
      let ln_arg = 1.0 - r.random()
      println("MF \{seed} \{i} x2pi \{hex(x2pi)}")
      println("MF \{seed} \{i} ln_arg \{hex(ln_arg)}")
      println("MF \{seed} \{i} log \{hex(@rp.c_log(ln_arg))}")
      println("MF \{seed} \{i} cos \{hex(@math.cos(x2pi))}")
      println("MF \{seed} \{i} sin \{hex(@math.sin(x2pi))}")
      println("MF \{seed} \{i} moonmath_ln \{hex(@math.ln(ln_arg))}")
    }
  }

  // 9) 更广的函数扫描：对数/三角函数/开方/指数，用确定性的输入网格，
  //    覆盖 gauss 实际会遇到的取值范围，统计 libm 与 @math 的分歧率。
  {
    let mut k = 0
    while k < 2000 {
      let x = 1.0 + k.to_double() * 0.0001234567
      println("SW log \{k} \{hex(x)} \{hex(@rp.c_log(x))} \{hex(@math.ln(x))}")
      let a = -20.0 + k.to_double() * 0.0197
      println("SW cos \{k} \{hex(a)} \{hex(@math.cos(a))}")
      println("SW sin \{k} \{hex(a)} \{hex(@math.sin(a))}")
      let s = k.to_double() * 0.0009765625
      println("SW sqrt \{k} \{hex(s)} \{hex(s.sqrt())}")
      k += 1
    }
  }
}
