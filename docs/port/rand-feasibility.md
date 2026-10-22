# 随机数管线移植可行性实测（C1 判定）

范围：只验证「固定 seed 下，MoonBit 能否逐位复刻 CPython 3.12 的
`random.Random` 随机数管线」，即 langdetect `_detect_block()` 的
`seed → gauss → choice` 序列。不涉及 ngram 抽取、概率更新、语言模型。

结论先行：**C1 在 MoonBit(native) 上可行，前提是 `log` 必须用 libm，
不能用 `@math.ln`。** 见文末分界点。

---

## 0. 复现命令

```bash
# 1) 生成 Python golden（只读 langdetect/，用运行时 monkeypatch 观测真实调用顺序）
.venv/Scripts/python.exe tools/gen_rand_golden.py

# 2) 构建 MoonBit 探针 + 逐值按 IEEE-754 hex 比较，输出逐阶段统计
.venv/Scripts/python.exe probes/rand_probe_compare.py

# 3) alpha 扰动敏感性测量（1 ulp 是否实际影响 detect_langs）
.venv/Scripts/python.exe probes/rand_alpha_sensitivity.py
```

产物：

- `tools/gen_rand_golden.py` → `docs/port/golden/rand/*.json`
- `probes/rand-probe/` → MoonBit 实现（`moon.mod` 的 `preferred_target = "native"`）
- `probes/rand_probe_compare.py` → 比对脚本，写 `docs/port/golden/rand/compare_report.json`
- `probes/rand-probe/compare_stdout.txt` → 比对脚本原始 stdout

版本：Python 3.12.10（`D:\Programs\Python\Python312\Lib\random.py`），
moon 0.1.20261012，target = native（Windows x64，MSVC/UCRT）。

---

## 1. 上游实现依据（逐条对应）

| 环节 | 依据 | 实测核对方式 |
| --- | --- | --- |
| MT19937 状态/回火 | CPython v3.12.10 `Modules/_randommodule.c`：`genrand_uint32`、`init_genrand`、`init_by_array` | 前 64 个 32 位字逐值比对 |
| `random()` 53 位组合 | 同文件 `random_random`：`(a*67108864.0+b)*(1.0/9007199254740992.0)`，`a=u32>>5`, `b=u32>>6` | 前 64 个 double 位型比对 |
| `getrandbits(k)` | 同文件 `_random_Random_getrandbits_impl`：k≤32 走 `genrand>>(32-k)`；k>32 时低 32 位先取，最高字再右移 `32-(k%32)` | k=1,2,3,12,16,32,33 各 32 个 |
| `_randbelow(n)` | `Lib/random.py` `_randbelow_with_getrandbits`：`k=n.bit_length()`，循环 `getrandbits(k)` 直到 `<n` | n=1,2,3,5,7,55,1000 各 32 个 |
| `gauss(0,1)` | `Lib/random.py` `gauss`：`x2pi=random()*TWOPI`；`g2rad=sqrt(-2*log(1-random()))`；`z=cos(x2pi)*g2rad`；缓存 `sin(x2pi)*g2rad` | 前 64 个 + 4 个 seed × 512 个，另比 8 次调用的全部中间量 |
| `TWOPI` | `Lib/random.py`：`from math import tau as TWOPI`，即 `0x1.921fb54442d18p+2` | 探针硬编码该位型 |
| 调用顺序 | 上游 `_detect_block`：每轮先 `gauss`，再 `choice` 若干次 | 用真实上游 monkeypatch `_randbelow`/`gauss` 记录，见下 |

`choice(seq)` 的实现是 `seq[self._randbelow(len(seq))]`，
所以探针里用 `_randbelow(len(ngrams))` 直接建模，无需复刻 `choice`。

### 1.1 真实上游调用顺序（不是猜的）

`tools/gen_rand_golden.py::upstream_mixed_sequence` 在运行时 monkeypatch
`random.Random._randbelow` 与 `random.Random.gauss`，用真实 langdetect
处理 `docs/port/golden/cases.jsonl` 的 `long-af` 案例（seed=0）：

```
ngram_count = 667
每轮 choice 次数 = [51, 51, 51, 76, 36, 51, 41]   （合计 357）
每轮 gauss 值    = [0.9417154046806644, -1.3965781047011498, -0.7259935007426864,
                    -0.10002241628886355, -0.01787660291832088, -1.8790228879440645,
                    0.2472058343286591]
```

生成脚本内断言：用纯 `random.Random(0)` 按同一顺序重放，
`gauss` 7/7、`choice` 357/357 与真实上游逐值相等（否则脚本直接 AssertionError）。

---

## 2. 逐阶段结论（实测）

原始输出见 `probes/rand-probe/compare_stdout.txt`（`probes/rand_probe_compare.py` 的 stdout）。

| 阶段 | 一致数/总数 | 首个不一致 | 结论 |
| --- | --- | --- | --- |
| MT19937 原始 32 位字（seed=0） | 64/64 | 无 | 一致 |
| MT19937 原始 32 位字（seed=42） | 64/64 | 无 | 一致 |
| `random()` double（seed=0） | 64/64 | 无 | 一致 |
| `random()` double（seed=42） | 64/64 | 无 | 一致 |
| `getrandbits(1)` | 32/32 | 无 | 一致 |
| `getrandbits(2)` | 32/32 | 无 | 一致 |
| `getrandbits(3)` | 32/32 | 无 | 一致 |
| `getrandbits(12)` | 32/32 | 无 | 一致 |
| `getrandbits(16)` | 32/32 | 无 | 一致 |
| `getrandbits(32)` | 32/32 | 无 | 一致 |
| `getrandbits(33)` | 32/32 | 无 | 一致 |
| `_randbelow(1)` | 32/32 | 无 | 一致 |
| `_randbelow(2)` | 32/32 | 无 | 一致 |
| `_randbelow(3)` | 32/32 | 无 | 一致 |
| `_randbelow(5)` | 32/32 | 无 | 一致 |
| `_randbelow(7)` | 32/32 | 无 | 一致 |
| `_randbelow(55)` | 32/32 | 无 | 一致 |
| `_randbelow(1000)` | 32/32 | 无 | 一致 |
| `gauss(0,1)` 前 64 | 64/64 | 无 | 一致（用 libm `log`） |
| gauss 内部 x2pi / y / ln_arg / ln_result / g2rad / cos / sin / z / gauss_next（各 8 个） | 8/8 × 9 字段 | 无 | 一致 |
| 混合序列 gauss（7 轮） | 7/7 | 无 | 一致 |
| 混合序列 `alpha = 0.5 + g*0.05` | 7/7 | 无 | 一致 |
| 混合序列 choice 下标 | 357/357 | 无 | 一致 |
| `gauss(0,1)` 512 个，seed=0 / 1 / 42 / 12345 | 512/512 × 4 | 无 | 一致 |
| mathfunc `x2pi`/`ln_arg`/`log`/`cos`/`sin`，seed=0/1/42/12345 各 256 | 256/256 × 20 | 无 | 一致 |
| 广域扫描 `libm log` vs CPython（2000 点） | 2000/2000 | 无 | 一致 |
| 广域扫描 `cos`（2000 点） | 2000/2000 | 无 | 一致 |
| 广域扫描 `sin`（2000 点） | 2000/2000 | 无 | 一致 |
| 广域扫描 `sqrt`（2000 点） | 2000/2000 | 无 | 一致 |
| **对照组** `gauss` 改用 `@math.ln`（seed=0/1/42/12345，各 512） | 485/512、492/512、494/512、484/512 | seed=0 #82 | **不一致** |
| **对照组** `@math.ln` vs libm log（seed=0/1/42/12345，各 256） | 232/256、238/256、234/256、234/256 | seed=42 #1 | **不一致** |
| **对照组** 广域 `@math.ln` vs CPython（2000 点） | 1934/2000 | k=196 | **不一致** |

汇总：68 个比对阶段中 59 个全一致，合计比对 **21451 对值，21206 对逐位一致**；
9 个不一致的**全部**是 `@math.ln` 对照组，正式管线（libm `log`）无一处不一致。

### 2.1 MoonBit API 实测记录

符号名不是猜的，逐个用 `moon ide doc` 查实：

```bash
$ C:/Users/Administrator/.moon/bin/moon.exe ide doc @math
pub fn cos(Double) -> Double
pub fn exp(Double) -> Double
pub fn ln(Double) -> Double
pub fn sin(Double) -> Double
...

$ C:/Users/Administrator/.moon/bin/moon.exe ide doc @double
  pub fn Double::reinterpret_as_uint64(Double) -> UInt64
  pub fn Double::sqrt(Double) -> Double
```

`@math` 里没有 `sqrt`（它在 `Double::sqrt`，编译为 `%f64_sqrt`）。
native target 下 `@math.cos/sin` 的实现是 `extern "C" fn cos/sin`
（`~/.moon/lib/core/math/trig_double_sincos_native.mbt`），
`@math.ln` 是纯 MoonBit 多项式（`math/log_double_nonjs.mbt`）——这正是
下面分界点的来源。C 的 `log` 在 MoonBit 里没有现成绑定，
探针用 `pub extern "C" fn c_log(x : Double) -> Double = "log"` 自建。

---

## 3. 分界点：`@math.ln` vs libm `log`

### 3.1 差异是哪一步

`@math.ln`（MoonBit core，`math/log_double_nonjs.mbt`，Musl 风格多项式）
与 CPython 的 `math.log`（Windows 上走 UCRT/MSVC libm）在部分输入上差 1 ulp。
不是算法错，是两套实现都正确但末位舍入不同。

最小反例（广域扫描 k=196，输入 `x = 1.0 + 196*0.0001234567`）：

| 量 | 值 |
| --- | --- |
| 输入 x hex | `3ff0631cee7d6a9d` |
| 输入 x repr | `1.0241975132` |
| CPython `math.log(x)` hex | `3f987bb422dcde86` |
| libm `log(x)`（MoonBit `extern "C" log`）hex | `3f987bb422dcde86` |
| MoonBit `@math.ln(x)` hex | `3f987bb422dcde87`（+1 ulp） |

另一个反例（k=253，`x = 1.0312345451`）：

| 量 | hex |
| --- | --- |
| x | `3ff07fefcb5b5be7` |
| CPython `math.log` | `3f9f7ead513bbb05` |
| `@math.ln` | `3f9f7ead513bbb04`（-1 ulp） |

扫描统计：`@math.ln` 在 2000 个点上 66 个与 libm 差 1 ulp（1934/2000 一致）。

gauss 路径上的第一个分叉（seed=0，第 83 个 gauss，index 82）：

| 量 | 值 |
| --- | --- |
| `1-random()` | `0.6087039497653751`（`3fe37a80b4a606a9`） |
| CPython `log` | `bfdfc5660aec5b07` |
| MoonBit `@math.ln` | `bfdfc5660aec5b08` |
| 结果 z：Python | `bfeeda7e81a86b92` |
| 结果 z：MoonBit(`@math.ln`) | `bfeeda7e81a86b91` |

### 3.2 修复方式（已在探针中采用）

`probes/rand-probe/rand-probe.mbt` 直接绑定 C 标准库：

```moonbit
pub extern "C" fn c_log(x : Double) -> Double = "log"
```

`gauss` 用 `c_log` 替代 `@math.ln` 后，全部阶段一致（上表正式管线）。

`cos` / `sin` 在 native target 下 MoonBit 本身就是 `extern "C" fn cos/sin`
（见 `~/.moon/lib/core/math/trig_double_sincos_native.mbt`），
与 CPython 用同一 libm，实测 2000 点全一致；`sqrt` 走
`Double::sqrt`（`%f64_sqrt` 指令），2000 点全一致。

---

## 4. C1 判定

**可行。** 分界点如下：

| 阶段 | 能否逐位一致 | 条件 |
| --- | --- | --- |
| MT19937 原始字 | 能 | 纯整数运算，无外部依赖 |
| `random()` double | 能 | 整数 + 两次乘加，IEEE-754 精确 |
| `getrandbits` | 能 | 纯整数/移位 |
| `_randbelow` | 能 | 纯整数 |
| `gauss` | **能，但必须用 libm `log`** | `cos`/`sin`/`sqrt` 天然一致；`log` 不能用 `@math.ln`（约 3.3% 输入差 1 ulp） |
| 上游混合调用序列 | 能 | 调用顺序 + `gauss_next` 缓存语义都已复刻，357 次 choice + 7 次 gauss 全等 |

也就是说：**从 MT19937 到 `_randbelow` 完全无风险；唯一的分界点是
`gauss` 里的 `log`**。用 libm 绑定时整条链路逐位一致；用 `@math.ln` 时
在 gauss 阶段开始分叉，且因为 `gauss_next` 缓存，一次分叉会污染后续一次调用。

### 4.1 1 ulp 的实际影响（实测，非推断）

若坚持用 `@math.ln`，`gauss` 值会差 1 ulp，`alpha = 0.5 + g*0.05`
随之差约 1e-17。用真实上游测量这个量级的影响
（`probes/rand_alpha_sensitivity.py`，前 20 个案例）：

| 对每个 gauss 加 delta | detect_langs 概率 hex 变化的案例数 |
| --- | --- |
| 0 | 0/20 |
| 1e-15 | 0/20 |
| 1e-12 | 0/20 |
| 1e-9 | 16/20 |
| 1e-6 | 19/20 |
| 1e-3 | 20/20 |

1 ulp 对应的 alpha 偏移约 1e-17，低于 1e-12 的阈值，因此在本批 20 个案例上
**不改变**最终概率位型。但这是概率性的：样本更多、文本更长时
不能保证。要做到「严格逐位」，必须用 libm `log`。

---

## 5. 未测项

- **其他平台**：只测了 Windows x64 / MSVC(UCRT) / native target。Linux glibc、
  macOS libm 的 `log` 末位可能与 UCRT 不同；CPython 与 MoonBit 只要链接同一
  平台 libm 就仍应一致，但未实测。
- **wasm / wasm-gc / js target**：未测。js target 下 `@math.ln` 会变成
  `Math.log`，与 native 行为不同。
- **`gauss` 的 mu/sigma 非 (0,1)**：只测了 `gauss(0.0, 1.0)`，即上游唯一用法。
- **`random.seed()` 非整数 seed**：只测了 `0/1/42/12345` 四个整数 seed
  （上游 `Detector.seed` 默认 0）。字符串/大整数 seed 走 `PyObject_Hash`
  或 32 位块数组，未测。
- **`getrandbits(k>33)`**：探针实现了 k≤64，但只比对了 ≤33。
- **完整 detect_langs 端到端**：本探针只覆盖随机数管线，不含 ngram 抽取与
  概率更新；端到端一致性另有工作项。
- **`@math` 其他函数**（`exp`/`pow`/`tan` 等）：不在 gauss 路径上，未测。

---

## 6. 文件清单

| 路径 | 作用 |
| --- | --- |
| `tools/gen_rand_golden.py` | 生成 Python golden（含真实上游调用顺序观测） |
| `docs/port/golden/rand/mt19937.json` | 前 64 个 32 位原始字（seed=0/42） |
| `docs/port/golden/rand/random_double.json` | 前 64 个 `random()` double |
| `docs/port/golden/rand/getrandbits.json` | 7 个 k × 32 个值 |
| `docs/port/golden/rand/randbelow.json` | 7 个 n × 32 个值 |
| `docs/port/golden/rand/gauss.json` | 前 64 个 `gauss(0,1)` |
| `docs/port/golden/rand/gauss_parts.json` | 前 8 次 gauss 的全部中间量 |
| `docs/port/golden/rand/mixed_sequence.json` | 上游混合序列（7 gauss + 357 choice + alpha） |
| `docs/port/golden/rand/gauss_stress.json` | 4 个 seed × 512 个 gauss |
| `docs/port/golden/rand/mathfunc.json` | 4 个 seed × 256 组 log/cos/sin 采样 |
| `docs/port/golden/rand/alpha_sensitivity.json` | alpha 扰动敏感性 |
| `docs/port/golden/rand/meta.json` | 生成环境与实现依据 |
| `docs/port/golden/rand/compare_report.json` | 逐阶段比对结果（机器可读） |
| `probes/rand-probe/rand-probe.mbt` | MoonBit 实现（MT19937 / random / getrandbits / randbelow / gauss） |
| `probes/rand-probe/cmd/main/main.mbt` | 探针主程序，输出各阶段序列 |
| `probes/rand_probe_compare.py` | 构建 + 运行 + 逐位比对 |
| `probes/rand_alpha_sensitivity.py` | alpha 扰动敏感性测量 |
| `probes/rand-probe/rand-probe_test.mbt` | `moon test --target native` 自检（4/4 通过） |
| `probes/rand-probe/compare_stdout.txt` | 比对脚本原始输出 |

自检命令与结果：

```bash
cd probes/rand-probe && C:/Users/Administrator/.moon/bin/moon.exe test --target native
# Total tests: 4, passed: 4, failed: 0.
```
