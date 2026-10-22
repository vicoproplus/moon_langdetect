// 浮点累加探针：验证 MoonBit(native) 的 Double 累加是否与 CPython 3.12 逐位一致，
// 覆盖上游 langdetect 的两条累加路径：
//
//   1) detector.py:223-232 `_normalize_prob`:  sump = sum(prob)，随后
//      prob[i] = p / sump。
//      ⚠ 实测（tools/gen_float_golden.py 的 sum_semantics）：CPython 3.12 的
//      内建 sum() 已改用 Neumaier 补偿求和（gh-100425），与朴素左到右顺序累加
//      在 307 组里有 238 组不一致。因此本探针对每条路径都输出两份：
//        R    = 朴素左到右顺序累加（acc 初值 0.0）
//        RNEU = Neumaier 补偿累加（复刻 CPython 3.12 builtin_sum_impl 的浮点分支）
//   2) detector.py:168-169 轮间累加:  self.langprob[j] += prob[j] / self.n_trial
//      （n_trial = 7，j 升序，就地 `+`，无补偿）→ 场景 D，只输出朴素序列。
//
// 输入不是从文件读取，而是由 @rp.Random(MT19937, 与 CPython random.Random 逐位
// 一致，已由 probes/rand_probe_compare.py 验证) 按下面固定配方现场生成；Python 侧
// 用同一配方 + random.Random(0) 重放，因此两侧的输入位型也必须完全相同（比较脚本
// 会逐值校验输入 hex）。
//
// 配方（N = 55 = len(LANGUAGE_PROFILES)，uniform = 1.0/55.0）：
//   A-uniform   200 组：xs[i] = uniform + u*(1.0 - uniform), u = random()；
//               Fisher-Yates(r._randbelow) 打乱后累加（上游 detect() 打乱 langlist）。
//   B-extreme    50 组：i 偶数位 1e300，i 奇数位 1e-300*(1.0+u)；覆盖
//               xs[0]=5e-324、xs[1]=1e300、xs[11]=-1e300、xs[53]=1e-300、
//               xs[54]=1e300（次正规/巨量/相消）。
//   C-negative   50 组：xs[i] = p*(1e300 - 1e300*u)，p = uniform + u*(1.0-uniform)；
//               负值模拟负 alpha 产生的负概率。
//   D-langprob7  7 轮：langprob 初值 uniform；每轮 h[j] = uniform + 1e-3*random()，
//               然后 langprob[j] = langprob[j] + h[j]/7.0（j 升序），记录每轮后状态。
//   E-stochastic 7 组：probs[j] = (base + noise) * (0.5 + random())，
//               base = alpha*w + (1-alpha)*uniform，alpha = 0.6 + 0.25*(random()-0.5)，
//               w = 0.3 + 0.7*random()，noise = 0.05*(random()-0.5)；
//               累加得 sump，再输出 probs[j]/sump（_normalize_prob 全链路）。
//
// 输出（空格分隔，hex 为 struct.pack('>d', x).hex() 语义的大端 16 位十六进制）：
//   HEAD float-add-probe v1 hex16-be
//   SCEN <name> <groups>
//   IN  <name> <flat_index>        <hex>   累加所用的输入（打乱后的真实顺序）
//   R   <name> <group_index>       <hex>   朴素左到右顺序累加结果
//   RNEU <name> <group_index>      <hex>   Neumaier 补偿累加结果
//   MIXPROB    <name> <flat_index> <hex>   xs[i]/sump_naive（C/E）
//   MIXPROBSUM <name> <flat_index> <hex>   xs[i]/sump_neumaier（C/E）
//   LP  D-langprob7 <flat_index>   <hex>   每轮结束后的 langprob 状态（朴素 `+=`）
//
// 累加一律为标量左到右顺序，不使用任何并行/归约。

///|
fn pad16(u : UInt64) -> String {
  let s = u.to_string(radix=16)
  let mut out = ""
  for _ in 0..<(16 - s.length()) {
    out = out + "0"
  }
  out + s
}

///|
/// IEEE-754 大端位型 hex（等价 Python struct.pack('>d', x).hex()）。
fn hex(d : Double) -> String {
  pad16(d.reinterpret_as_uint64())
}

///|
/// 上游 detect() 的 langlist 洗牌：random.shuffle，Fisher-Yates 递减。
fn shuffle(r : @rp.Random, xs : Array[Double]) -> Unit {
  let mut i = xs.length() - 1
  while i > 0 {
    let j = r.randbelow((i + 1).to_uint64()).to_int()
    let tmp = xs[i]
    xs[i] = xs[j]
    xs[j] = tmp
    i -= 1
  }
}

///|
/// 朴素左到右顺序累加（acc 初值 0.0）。等价于下游手工循环，**不等价**于
/// CPython 3.12 的内建 sum()（后者是 Neumaier 补偿）。
fn seq_sum(xs : Array[Double]) -> Double {
  let mut acc = 0.0
  for i in 0..<xs.length() {
    acc = acc + xs[i]
  }
  acc
}

///|
/// 复刻 CPython 3.12 `builtin_sum_impl` 的浮点快路径（Neumaier 补偿求和）。
/// C 源码语义：total = hi + x; if (fabs(hi) >= fabs(x)) c += (hi - total) + x;
/// else c += (x - total) + hi; hi = total; 收尾 return hi + c。
fn neumaier_sum(xs : Array[Double]) -> Double {
  let mut hi = 0.0
  let mut c = 0.0
  for i in 0..<xs.length() {
    let x = xs[i]
    let total = hi + x
    if hi.abs() >= x.abs() {
      c = c + (hi - total + x)
    } else {
      c = c + (x - total + hi)
    }
    hi = total
  }
  hi + c
}

///|
fn main {
  let n : Int32 = 55
  let uniform : Double = 1.0 / 55.0
  println("HEAD float-add-probe v1 hex16-be")

  // 场景 A/B/C/E 共用的输出：输入、朴素累加、Neumaier 累加（+ C/E 的归一化）。
  let emit_group = fn(
    name : String,
    g : Int32,
    xs : Array[Double],
    with_norm : Bool,
  ) {
    for i in 0..<n {
      println("IN \{name} \{g * n + i} \{hex(xs[i])}")
    }
    let sump_naive = seq_sum(xs)
    let sump_neu = neumaier_sum(xs)
    println("R \{name} \{g} \{hex(sump_naive)}")
    println("RNEU \{name} \{g} \{hex(sump_neu)}")
    if with_norm {
      for i in 0..<n {
        println("MIXPROB \{name} \{g * n + i} \{hex(xs[i] / sump_naive)}")
      }
      for i in 0..<n {
        println("MIXPROBSUM \{name} \{g * n + i} \{hex(xs[i] / sump_neu)}")
      }
    }
  }

  // A-uniform：200 组，打乱后的 55 个 [uniform, 1] 正数。
  {
    println("SCEN A-uniform 200")
    let r = @rp.Random::from_seed(0U)
    for g in 0..<200 {
      let xs : Array[Double] = Array::make(n, 0.0)
      for i in 0..<n {
        let u = r.random()
        xs[i] = uniform + u * (1.0 - uniform)
      }
      shuffle(r, xs)
      emit_group("A-uniform", g, xs, false)
    }
  }

  // B-extreme：50 组，1e300 与 1e-300/次正规数混合，含 1e300 + (-1e300) 相消。
  {
    println("SCEN B-extreme 50")
    let r = @rp.Random::from_seed(0U)
    for g in 0..<50 {
      let xs : Array[Double] = Array::make(n, 0.0)
      for i in 0..<n {
        let u = r.random()
        xs[i] = if i % 2 == 0 { 1.0e300 } else { 1.0e-300 * (1.0 + u) }
      }
      xs[0] = 5.0e-324
      xs[1] = 1.0e300
      xs[11] = -1.0e300
      xs[53] = 1.0e-300
      xs[54] = 1.0e300
      emit_group("B-extreme", g, xs, false)
    }
  }

  // C-negative：50 组，正负巨量混合，并跑 _normalize_prob 的 prob[j]/sump。
  {
    println("SCEN C-negative 50")
    let r = @rp.Random::from_seed(0U)
    for g in 0..<50 {
      let xs : Array[Double] = Array::make(n, 0.0)
      for i in 0..<n {
        let u = r.random()
        let p = uniform + u * (1.0 - uniform)
        xs[i] = p * (1.0e300 - 1.0e300 * u)
      }
      emit_group("C-negative", g, xs, true)
    }
  }

  // D-langprob7：上游 7 轮 `langprob[j] += prob[j] / n_trial` 的逐位复刻（朴素 +=）。
  {
    println("SCEN D-langprob7 7")
    let r = @rp.Random::from_seed(0U)
    let langprob : Array[Double] = Array::make(n, uniform)
    for t in 0..<7 {
      let h : Array[Double] = Array::make(n, 0.0)
      for j in 0..<n {
        h[j] = uniform + 1.0e-3 * r.random()
      }
      for j in 0..<n {
        langprob[j] = langprob[j] + h[j] / 7.0
      }
      for j in 0..<n {
        println("LP D-langprob7 \{t * n + j} \{hex(langprob[j])}")
      }
    }
  }

  // E-stochastic：7 组，模拟一次完整 _detect_block + _normalize_prob。
  println("SCEN E-stochastic 7")
  let r = @rp.Random::from_seed(0U)
  for t in 0..<7 {
    let alpha = 0.6 + 0.25 * (r.random() - 0.5)
    let probs : Array[Double] = Array::make(n, 0.0)
    for j in 0..<n {
      let w = 0.3 + r.random() * 0.7
      let base = alpha * w + (1.0 - alpha) * uniform
      let noise = 0.05 * (r.random() - 0.5)
      probs[j] = (base + noise) * (0.5 + r.random())
    }
    emit_group("E-stochastic", t, probs, true)
  }
}
