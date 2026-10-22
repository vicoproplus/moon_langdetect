// 自检：MoonBit 探针必须与 Python golden 中的固定锚点一致。
// golden 来源：`tools/gen_rand_golden.py`（CPython 3.12.10）。
test "mt19937 seed=0 first words" {
  let r = Random::from_seed(0U)
  inspect(r.getrandbits(32), content="3626764237")
  inspect(r.getrandbits(32), content="1654615998")
}

test "random() seed=0 first values" {
  let r = Random::from_seed(0U)
  let a = r.random()
  let b = r.random()
  inspect(a.reinterpret_as_uint64(), content="4605781095417019838")
  inspect(b.reinterpret_as_uint64(), content="4605002265878567962")
}

test "gauss seed=0 first value" {
  let r = Random::from_seed(0U)
  let g = r.gauss(0.0, 1.0)
  // Python: random.Random(0).gauss(0,1) => 0.9417154046806644
  inspect(g.reinterpret_as_uint64(), content="4606657437836494208")
}

test "randbelow(667) seed=0 first values" {
  let r = Random::from_seed(0U)
  inspect(r.randbelow(667UL), content="394")
  inspect(r.randbelow(667UL), content="430")
}
