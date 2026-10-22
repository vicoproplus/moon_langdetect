///| MT19937 and the `random.Random` scalar pipeline, ported from CPython
/// 3.12.10 (`Modules/_randommodule.c` and `Lib/random.py`).
///
/// The state transition, tempering and seeding are literal ports of
/// `init_genrand` / `init_by_array` / `genrand_uint32`; `random`,
/// `getrandbits` and `randbelow` follow `random_random`,
/// `_random_Random_getrandbits_impl` and
/// `_randbelow_with_getrandbits`. The probe in `probes/rand-probe`
/// verified the whole pipeline bit-for-bit against CPython 3.12.10 on
/// native (`docs/port/rand-feasibility.md` §2).
///
/// Seeding semantics: `Some(s)` is deterministic and follows CPython
/// `random.Random(int)` — the absolute value of the signed 64-bit seed is
/// split into little-endian 32-bit words and fed to `init_by_array`.
/// `None` is non-reproducible: it mixes `@env.now()` with a monotonically
/// increasing process counter (no file or network access), so repeated
/// constructions differ even when the clock is coarse.

///| MT19937 word count (`Modules/_randommodule.c`).
const MT_N : Int = 624

///| MT19937 middle word (`Modules/_randommodule.c`).
const MT_M : Int = 397

///| Tempering matrix A.
const MT_MATRIX_A : UInt = 0x9908B0DFU

///| Most significant bit mask.
const MT_UPPER_MASK : UInt = 0x80000000U

///| Least significant 31 bits mask.
const MT_LOWER_MASK : UInt = 0x7FFFFFFFU

///| `random()` combines two 32-bit draws: `a` keeps the top 27 bits and
/// `b` the top 26 bits, giving a 53-bit fraction.
const POW2_26 : Double = 67108864.0

///| Exact reciprocal of `2^53`, the denominator of the 53-bit fraction.
const POW2_53_INV : Double = 1.0 / 9007199254740992.0

///| A CPython `random.Random` generator: 624-word state, cursor, and the
/// one-value `gauss` cache (`gauss_next`).
pub struct Mt19937 {
  state : Array[UInt]
  mut index : Int
  mut gauss_next : Double?
}

///| Process-wide counter mixed into every unseeded construction. A `Ref`
/// keeps the counter mutable without a platform-specific clock: two
/// `Mt19937::new(None)` calls always receive different seed material.
let unseeded_counter : Ref[UInt64] = Ref(0UL)

///| Seed material for `Mt19937::new(None)`: current time xor a
/// monotonically increasing counter (multiplied by a 64-bit odd
/// constant, so both low and high counter bits affect the result).
fn next_unseeded_seed() -> Int64 {
  let counter = unseeded_counter.val
  unseeded_counter.val = counter + 1UL
  let now = @env.now()
  (now ^ (counter * 0x9E3779B97F4A7C15UL) ^ (counter << 17)).reinterpret_as_int64()
}

///| CPython `random_seed` word split: absolute value, little-endian
/// 32-bit words, at least one word (seed 0 becomes `[0]`).
fn seed_key(seed : Int64) -> Array[UInt] {
  let bits = seed.reinterpret_as_uint64()
  let mut rest = if seed < 0 { 0UL - bits } else { bits }
  let key : Array[UInt] = []
  while rest != 0UL {
    key.push((rest & 0xFFFFFFFFUL).to_uint())
    rest = rest >> 32
  }
  if key.is_empty() {
    key.push(0U)
  }
  key
}

///| Build a generator. `Some(s)` mirrors `random.Random(s)` for any
/// signed 64-bit `s` (the golden seeds are 0 / 1 / 42 / 12345);
/// `None` mirrors `random.Random()` with OS entropy replaced by the
/// time xor counter mix above, so it is never reproducible.
pub fn Mt19937::new(seed : Int64?) -> Mt19937 {
  let rng : Mt19937 = { state: Array::make(MT_N, 0U), index: MT_N, gauss_next: None }
  let key = match seed {
    Some(value) => seed_key(value)
    None => seed_key(next_unseeded_seed())
  }
  rng.init_by_array(key)
  rng
}

///| CPython `init_genrand`.
fn Mt19937::init_genrand(self : Mt19937, seed : UInt) -> Unit {
  self.state[0] = seed
  for index in 1..<MT_N {
    let previous = self.state[index - 1]
    self.state[index] = 1812433253U *
      (previous ^ (previous >> 30)) +
      index.reinterpret_as_uint()
  }
  self.index = MT_N
}

///| CPython `init_by_array`.
fn Mt19937::init_by_array(self : Mt19937, key : Array[UInt]) -> Unit {
  self.init_genrand(19650218U)
  let key_length = key.length()
  let mut i = 1
  let mut j = 0
  let mut k = if MT_N > key_length { MT_N } else { key_length }
  while k > 0 {
    let previous = self.state[i - 1]
    self.state[i] = (self.state[i] ^ ((previous ^ (previous >> 30)) * 1664525U)) +
      key[j] +
      j.reinterpret_as_uint()
    i += 1
    j += 1
    if i >= MT_N {
      self.state[0] = self.state[MT_N - 1]
      i = 1
    }
    if j >= key_length {
      j = 0
    }
    k -= 1
  }
  let mut k2 = MT_N - 1
  while k2 > 0 {
    let previous = self.state[i - 1]
    self.state[i] = (self.state[i] ^ ((previous ^ (previous >> 30)) * 1566083941U)) -
      i.reinterpret_as_uint()
    i += 1
    if i >= MT_N {
      self.state[0] = self.state[MT_N - 1]
      i = 1
    }
    k2 -= 1
  }
  self.state[0] = 0x80000000U
}

///| CPython `genrand_uint32`: regenerate the block when the cursor runs
/// out, then temper one word.
fn Mt19937::genrand_uint32(self : Mt19937) -> UInt {
  let mut y : UInt = 0U
  if self.index >= MT_N {
    let mut kk = 0
    while kk < MT_N - MT_M {
      y = (self.state[kk] & MT_UPPER_MASK) | (self.state[kk + 1] & MT_LOWER_MASK)
      self.state[kk] = self.state[kk + MT_M] ^
        (y >> 1) ^
        (if (y & 1U) == 1U { MT_MATRIX_A } else { 0U })
      kk += 1
    }
    while kk < MT_N - 1 {
      y = (self.state[kk] & MT_UPPER_MASK) | (self.state[kk + 1] & MT_LOWER_MASK)
      self.state[kk] = self.state[kk + (MT_M - MT_N)] ^
        (y >> 1) ^
        (if (y & 1U) == 1U { MT_MATRIX_A } else { 0U })
      kk += 1
    }
    y = (self.state[MT_N - 1] & MT_UPPER_MASK) | (self.state[0] & MT_LOWER_MASK)
    self.state[MT_N - 1] = self.state[MT_M - 1] ^
      (y >> 1) ^
      (if (y & 1U) == 1U { MT_MATRIX_A } else { 0U })
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

///| CPython `random_random`: two tempered words folded into a 53-bit
/// fraction, `(a * 2^26 + b) * 2^-53`.
pub fn Mt19937::random(self : Mt19937) -> Double {
  let a = self.genrand_uint32() >> 5
  let b = self.genrand_uint32() >> 6
  (a.to_double() * POW2_26 + b.to_double()) * POW2_53_INV
}

///| CPython `bit_length` for an unsigned 64-bit value.
pub fn bit_length_u64(value : UInt64) -> Int {
  let mut rest = value
  let mut length = 0
  while rest != 0UL {
    rest = rest >> 1
    length += 1
  }
  length
}

///| CPython `_random.Random.getrandbits(k)` for `0 <= k <= 64`, kept in
/// `UInt64` so every bit is representable. `randbelow` and the golden
/// cases for k = 32 / 33 use this form; the public `Int` form below is
/// capped at 32 bits because MoonBit `Int` is 32-bit signed.
pub fn Mt19937::getrandbits_u64(self : Mt19937, k : Int) -> UInt64 {
  if k <= 0 {
    return 0UL
  }
  if k <= 32 {
    return (self.genrand_uint32() >> (32 - k)).to_uint64()
  }
  let low = self.genrand_uint32()
  let high = self.genrand_uint32()
  let remaining = k - 32
  let high_word = if remaining < 32 { high >> (32 - remaining) } else { high }
  (high_word.to_uint64() << 32) | low.to_uint64()
}

///| CPython `_random.Random.getrandbits(k)` in the plan's `Int` shape.
///
/// MoonBit `Int` is 32-bit signed, so this form accepts `0 <= k <= 32`:
/// `k = 32` returns the raw 32-bit pattern reinterpreted as `Int`
/// (negative when the top bit is set). Values wider than 32 bits use
/// `getrandbits_u64`; k outside `0..=32` is a precondition violation.
pub fn Mt19937::getrandbits(self : Mt19937, k : Int) -> Int {
  if k < 0 {
    abort("Mt19937::getrandbits: k must be non-negative")
  }
  if k > 32 {
    abort("Mt19937::getrandbits: the Int form supports k <= 32; use getrandbits_u64")
  }
  if k == 0 {
    return 0
  }
  (self.genrand_uint32() >> (32 - k)).reinterpret_as_int()
}

///| CPython `_randbelow_with_getrandbits(n)` for `n >= 1`: draw
/// `bit_length(n)` bits until the value is below `n`. `n = 1` still
/// consumes draws (upstream loops until the single bit is 0), so this
/// function must not shortcut it. Non-positive `n` has no upstream
/// meaning (it would loop forever); it returns 0.
pub fn Mt19937::randbelow(self : Mt19937, n : Int) -> Int {
  if n <= 0 {
    return 0
  }
  let k = bit_length_u64(n.to_uint64())
  let bound = n.to_uint64()
  let mut value = self.getrandbits_u64(k)
  while value >= bound {
    value = self.getrandbits_u64(k)
  }
  value.to_int()
}
