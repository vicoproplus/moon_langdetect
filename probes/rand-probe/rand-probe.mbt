// Copyright 2026 moon_langdetect port probe
//
// 仅用于移植可行性取证：在 MoonBit(native) 中逐位复刻 CPython 3.12 的
// random.Random 随机数管线。不实现任何业务检测逻辑。
//
// 上游依据（CPython v3.12.10）：
//   Modules/_randommodule.c: genrand_uint32 / random_random / init_genrand /
//     init_by_array / _random_Random_getrandbits_impl / random_seed
//   Lib/random.py: gauss()、_randbelow_with_getrandbits()
//
// 数学函数映射：
//   sqrt -> Double::sqrt（builtin，编译为 %f64_sqrt）
//   ln   -> @math.ln（native 下为 libm log）
//   cos  -> @math.cos（native 下为 extern "C" cos，即 libm cos）
//   sin  -> @math.sin（native 下为 extern "C" sin，即 libm sin）
// CPython 3.12 的 math.cos/log 在 Windows 上同样调用 UCRT 的 libm，
// 是否末位一致由实测决定。

///| MT19937 参数，与 CPython `Modules/_randommodule.c` 一致。
const N : Int = 624
const M : Int = 397
const MATRIX_A : UInt = 0x9908B0DFU
const UPPER_MASK : UInt = 0x80000000U
const LOWER_MASK : UInt = 0x7FFFFFFFU

///| CPython `random.py` 的 `TWOPI = math.tau`。
pub const TWOPI : Double = 0x1.921FB54442D18p+2

///| `random()` 组合常数。
const POW2_26 : Double = 67108864.0
const POW2_53_INV : Double = 1.0 / 9007199254740992.0

///| CPython 3.12 `random.Random` 的移植版。
pub struct Random {
  state : Array[UInt]
  mut index : Int
  mut gauss_next : Double?
}

///| 空实例（等价 C 层 RandomObject 刚分配，尚未 seed）。
pub fn Random::new() -> Random {
  { state: Array::make(N, 0U), index: N, gauss_next: None }
}

///| CPython `init_genrand`。
pub fn Random::init_genrand(self : Random, s : UInt) -> Unit {
  self.state[0] = s
  for mti in 1..<N {
    let prev = self.state[mti - 1]
    self.state[mti] = 1812433253U * (prev ^ (prev >> 30)) + mti.reinterpret_as_uint()
  }
  self.index = N
}

///| CPython `init_by_array`。
pub fn Random::init_by_array(self : Random, key : Array[UInt]) -> Unit {
  self.init_genrand(19650218U)
  let key_length = key.length()
  let mut i = 1
  let mut j = 0
  let mut k = if N > key_length { N } else { key_length }
  while k > 0 {
    let m1 = self.state[i - 1]
    self.state[i] = (self.state[i] ^ ((m1 ^ (m1 >> 30)) * 1664525U)) +
      key[j] + j.reinterpret_as_uint()
    i += 1
    j += 1
    if i >= N {
      self.state[0] = self.state[N - 1]
      i = 1
    }
    if j >= key_length {
      j = 0
    }
    k -= 1
  }
  let mut k2 = N - 1
  while k2 > 0 {
    let m1 = self.state[i - 1]
    self.state[i] = (self.state[i] ^ ((m1 ^ (m1 >> 30)) * 1566083941U)) -
      i.reinterpret_as_uint()
    i += 1
    if i >= N {
      self.state[0] = self.state[N - 1]
      i = 1
    }
    k2 -= 1
  }
  self.state[0] = 0x80000000U
}

///| 等价于 `random.Random(seed)`，0 <= seed <= 0xFFFFFFFF。
pub fn Random::from_seed(seed : UInt) -> Random {
  let r = Random::new()
  r.init_by_array([seed])
  r
}

///| CPython `genrand_uint32`。
pub fn Random::genrand_uint32(self : Random) -> UInt {
  let mut y : UInt = 0U
  if self.index >= N {
    let mut kk = 0
    while kk < N - M {
      y = (self.state[kk] & UPPER_MASK) | (self.state[kk + 1] & LOWER_MASK)
      self.state[kk] = self.state[kk + M] ^ (y >> 1) ^
        (if (y & 1U) == 1U { MATRIX_A } else { 0U })
      kk += 1
    }
    while kk < N - 1 {
      y = (self.state[kk] & UPPER_MASK) | (self.state[kk + 1] & LOWER_MASK)
      self.state[kk] = self.state[kk + (M - N)] ^ (y >> 1) ^
        (if (y & 1U) == 1U { MATRIX_A } else { 0U })
      kk += 1
    }
    y = (self.state[N - 1] & UPPER_MASK) | (self.state[0] & LOWER_MASK)
    self.state[N - 1] = self.state[M - 1] ^ (y >> 1) ^
      (if (y & 1U) == 1U { MATRIX_A } else { 0U })
    self.index = 0
  }
  y = self.state[self.index]
  self.index += 1
  y = y ^ (y >> 11)
  y = y ^ ((y << 7) & 0x9D2C5680U)
  y = y ^ ((y << 15) & 0xEFC60000U)
  y = y ^ (y >> 18)
  y
}

///| CPython `random_random`：53 位组合。
pub fn Random::random(self : Random) -> Double {
  let a = self.genrand_uint32() >> 5
  let b = self.genrand_uint32() >> 6
  (a.to_double() * POW2_26 + b.to_double()) * POW2_53_INV
}

///| CPython `_random.Random.getrandbits(k)`（k <= 64）。
pub fn Random::getrandbits(self : Random, k : Int) -> UInt64 {
  if k == 0 {
    return 0UL
  }
  if k <= 32 {
    return (self.genrand_uint32() >> (32 - k)).to_uint64()
  }
  let low = self.genrand_uint32()
  let high = self.genrand_uint32()
  let rem = k - 32
  let hi = if rem < 32 { high >> (32 - rem) } else { high }
  (hi.to_uint64() << 32) | low.to_uint64()
}

///| CPython `int.bit_length()`（UInt64 版）。
pub fn bit_length_u64(x : UInt64) -> Int {
  let mut v = x
  let mut n = 0
  while v != 0UL {
    v = v >> 1
    n += 1
  }
  n
}

///| CPython `_randbelow_with_getrandbits(n)`。
pub fn Random::randbelow(self : Random, n : UInt64) -> UInt64 {
  let k = bit_length_u64(n)
  let mut r = self.getrandbits(k)
  while r >= n {
    r = self.getrandbits(k)
  }
  r
}

///| 直接绑定 C 标准库 `log`（native 下即 UCRT/MSVC libm）。
/// CPython 3.12 的 `math.log` 也走同一 libm；而 MoonBit 的 `@math.ln` 是纯
/// MoonBit 多项式实现，实测在部分输入上与 libm 差 1 ulp（见 docs/port/rand-feasibility.md）。
pub extern "C" fn c_log(x : Double) -> Double = "log"

///| CPython `random.Random.gauss(mu, sigma)`，含 `gauss_next` 缓存。
pub fn Random::gauss(self : Random, mu : Double, sigma : Double) -> Double {
  let z = self.gauss_next
  self.gauss_next = None
  match z {
    Some(zv) => mu + zv * sigma
    None => {
      let x2pi = self.random() * TWOPI
      let g2rad = (-2.0 * c_log(1.0 - self.random())).sqrt()
      let zc = @math.cos(x2pi) * g2rad
      self.gauss_next = Some(@math.sin(x2pi) * g2rad)
      mu + zc * sigma
    }
  }
}

///| 对照实现：与 `gauss` 完全相同，但 `log` 用 MoonBit 的 `@math.ln`
/// （纯 MoonBit 多项式）而非 libm `log`。仅用于量化分界点，不用于移植。
pub fn Random::gauss_moonmath(self : Random, mu : Double, sigma : Double) -> Double {
  let z = self.gauss_next
  self.gauss_next = None
  match z {
    Some(zv) => mu + zv * sigma
    None => {
      let x2pi = self.random() * TWOPI
      let g2rad = (-2.0 * @math.ln(1.0 - self.random())).sqrt()
      let zc = @math.cos(x2pi) * g2rad
      self.gauss_next = Some(@math.sin(x2pi) * g2rad)
      mu + zc * sigma
    }
  }
}
