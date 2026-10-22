# C1 剩余风险实测（isupper 语义 + 浮点累加）

范围：只补 `docs/port/rand-feasibility.md` 之后剩下的两个风险点，
不重做随机数管线（已完成，21206/21451 逐位一致）。

- 任务 1：上游 `NGram.add_char` 的 `ch.isupper()` 在 MoonBit 侧能否对齐
- 任务 2：上游 `sum(prob)` / `langprob[j] += prob[j]/7` 的浮点累加顺序

---

## 0. 复现命令

```bash
# 任务 1
.venv/Scripts/python.exe probes/char_probe_compare.py     # 全码点对拍
.venv/Scripts/python.exe probes/char_upper_impact.py      # 不一致码点对 detect_langs 的实际影响

# 任务 2
.venv/Scripts/python.exe tools/gen_float_golden.py
.venv/Scripts/python.exe probes/float_probe_compare.py

# 工程自检
cd probes/rand-probe && C:/Users/Administrator/.moon/bin/moon.exe build --target native
cd probes/rand-probe && C:/Users/Administrator/.moon/bin/moon.exe test --target native
cd probes/char-probe && C:/Users/Administrator/.moon/bin/moon.exe build --target native
```

产物：

| 路径 | 作用 |
| --- | --- |
| `probes/char-probe/` | MoonBit 字符语义探针（依赖 `moonbit-community/unicode-data@0.6.0`） |
| `probes/char_probe_compare.py` | 全码点对拍，写 `docs/port/golden/char_isupper_compare.json` |
| `probes/char-probe/compare_stdout.txt` | 对拍脚本原始 stdout |
| `probes/char_upper_impact.py` | 不一致码点对 detect_langs 的影响，写 `docs/port/golden/char_upper_impact.json` |
| `probes/char-probe/impact_stdout.txt` | 影响测量原始 stdout |
| `probes/rand-probe/cmd/float/main.mbt` | 浮点累加探针（复用 `probes/rand-probe` 工程） |
| `tools/gen_float_golden.py` | CPython 侧 golden，写 `docs/port/golden/float_add_python.json` |
| `probes/float_probe_compare.py` | 逐位比对，写 `docs/port/golden/float_add_compare.json` |
| `docs/port/float-add-conclusion.md` | 浮点累加详细结论 |

---

## 1. 任务 1：`isupper` 语义对齐

### 1.1 MoonBit 侧 API 查实（不是猜的）

```bash
$ C:/Users/Administrator/.moon/bin/moon.exe ide doc @char
type Char
  pub fn Char::is_ascii_uppercase(Char) -> Bool
  pub fn Char::to_ascii_uppercase(Char) -> Char
  ...（无 Unicode 语义的大小写 API）

$ C:/Users/Administrator/.moon/bin/moon.exe ide doc @unicode
package "moonbitlang/x/unicode" // moonbitlang/x@0.5.5
  pub fn to_lowercase(Char) -> Char
  ...（只有 lowercase，无 isupper / cased）

$ C:/Users/Administrator/.moon/bin/moon.exe ide doc 'is_uppercase'
package "moonbit-community/unicode-data" // moonbit-community/unicode-data@0.6.0
pub fn is_uppercase(Char) -> Bool
```

结论：**MoonBit core 没有 Unicode `isupper`**（`Char` 只有 ASCII 版），
`moonbitlang/x/unicode` 也没有。可用的是第三方 `moonbit-community/unicode-data`
（`moon add moonbit-community/unicode-data@0.6.0` 成功，README 声明 **Unicode 18.0.0** 数据）。

它的 `is_uppercase` 直接对应 UCD 的 `Uppercase` 派生属性
（`uppercase.mbt` 注释 `Generated from DerivedCoreProperties.txt`），
语义上就是 Python `str.isupper()` 对单字符的判定基础
（`cased && uppercase`）。

### 1.2 全码点对拍结果

| 指标 | 数值 |
| --- | --- |
| 总码点 | 1114112 |
| surrogate 区（MoonBit `Int::to_char` 返回 `None`，跳过） | 2048 |
| 可比码点 | 1112064 |
| Python `chr(cp).isupper()==True` | 1951 |
| MoonBit `@ucd.is_uppercase==True` | 2026 |
| 32 位组比对 | **34807 / 34816 组一致** |
| 逐点不一致 | **75 个码点**（全部 Python=0、MoonBit=1） |
| 不一致码点的 Python 类别 | `{'Cn': 75}`（全是 Unicode 15.0 未分配） |
| profile 实际用到的 3160 个码点 | **0 个不一致** |
| 三类抽样字符（17 个） | **0 个不一致** |

跳过说明：`moonbit_unconstructible_codepoints = 2048`，恰好等于 surrogate 区
（U+D800..U+DFFF）；`SKIP 55296` / `SKIP 57343` 是两端点探针输出。
Python `chr()` 允许 surrogate，MoonBit `Char` 不允许，故这 2048 个点从分母中扣除。

### 1.3 75 个不一致码点（全部列出）

完整清单（75 个码点，已压缩为 27 段区间）：

```
[0x1C89],
[0xA7CB,0xA7CC], [0xA7CE], [0xA7D2], [0xA7D4], [0xA7DA], [0xA7DC,0xA7DD], [0xA7E2],
[0xAB6C,0xAB6D],
[0x10D50,0x10D65]  (22 个),
[0x16EA0,0x16EB8]  (25 个),
[0x1DF40], [0x1DF48], [0x1DF4A], [0x1DF4D], [0x1DF51], [0x1DF68], [0x1DF6A],
[0x1DF6C], [0x1DF6E], [0x1DF72], [0x1DF74], [0x1DF76], [0x1DF78], [0x1DF7A],
[0x1DF7C], [0x1DF7E]
```

（区间正好对应 `probes/char-probe/cmd/main/main.mbt` 的 `post15_upper()`。）

成因：**Unicode 版本差**。Python 3.12.10 的 `unicodedata.unidata_version` 是
**15.0.0**；`unicode-data@0.6.0` 是 **18.0.0**。这 75 个码点在 15.0 里是 `Cn`
（未分配），在 16/17/18 里新增为 `Lu`。已核实 U+1C89 是 Unicode 16.0 新增的
CYRILLIC CAPITAL LETTER TJE。

### 1.4 三类字符专项

| 类别 | 抽样码点 | MoonBit 类别 | MoonBit is_uppercase | Python isupper | 一致 |
| --- | --- | --- | --- | --- | --- |
| Lu | U+00C4 Ä | Lu | 1 | 1 | 是 |
| Lu | U+0130 İ | Lu | 1 | 1 | 是 |
| Lu | U+03A9 Ω | Lu | 1 | 1 | 是 |
| Lu | U+0416 Ж | Lu | 1 | 1 | 是 |
| Lt | U+01C5 ǅ | Lt | 0 | 0 | 是 |
| Lt | U+01C8 ǈ | Lt | 0 | 0 | 是 |
| 无 cased | U+4E00 一 | Lo | 0 | 0 | 是 |
| 无 cased | U+3042 あ | Lo | 0 | 0 | 是 |
| 无 cased | U+AC00 가 | Lo | 0 | 0 | 是 |
| 无 cased | U+0628 ب | Lo | 0 | 0 | 是 |
| 无 cased | U+0967 १ | Nd | 0 | 0 | 是 |
| 无 cased | U+1F600 😀 | So | 0 | 0 | 是 |
| 无 cased | U+0301 组合符 | Mn | 0 | 0 | 是 |
| 无 cased | U+2000 空格 | Zs | 0 | 0 | 是 |
| Nl | U+2160 Ⅰ | Nl | 1 | 1 | 是 |
| So | U+24B6 Ⓐ | So | 1 | 1 | 是 |
| No | U+00B2 ² | No | 0 | 0 | 是 |

注意 Lt：Python 的 `str.isupper()` 对标题大小写字符返回 **False**
（`ǅ`.isupper() == False），MoonBit 的 `is_uppercase`（UCD `Uppercase` 属性）
同样返回 False —— 两者在这里口径一致，不需要特殊处理。
Nl（罗马数字）与 So（带圈字母）两边都判 True，也一致。

### 1.5 替代路径（MoonBit 无直接等价 API 时的可行性）

三条候选路径的实测一致率（全码点，surrogate 已扣除）：

| 路径 | 实现 | 不一致码点数 | 一致率 |
| --- | --- | --- | --- |
| A（推荐） | `@ucd.is_uppercase` | 75 | 1111989/1112064（99.9933%） |
| B | `to_simple_uppercase(c)==c && to_simple_lowercase(c)!=c` | 651 | 1111413/1112064 |
| C | `general_category(c) == Lu` | 195 | 1111869/1112064 |
| D（A + 补丁表） | `is_uppercase && !post15_upper(cp)` | **0** | **1112064/1112064** |

路径 B 的典型反例：U+03D2 `ϒ` 是 Lu 但简单大写映射恒等（Python 判 True，B 判 False）；
U+1F88 `ᾈ` 是 Lt（Python 判 False，B 判 True）。
路径 C 的反例：U+2160 罗马数字是 Nl 但 Python 判 True；U+1C89 在 Unicode18 是 Lu
但 Python 判 False。

**路径 D 已实测 0 不一致**：`probes/char-probe/cmd/main/main.mbt` 里的
`post15_upper()` 就是上面 75 个码点的区间表，判定式
`@ucd.is_uppercase(c) && !post15_upper(c.to_int())`。

### 1.6 不一致码点是否影响 profile 实际字符集

| 检查 | 结果 |
| --- | --- |
| 55 个 profile 文件的 87598 个 ngram 键，涉及 3160 个不同码点 | 与 75 个不一致码点的交集 = **0** |
| `docs/port/golden/cases.jsonl` 全部用例文本（849 个不同码点） | 交集 = **0** |
| 上游 `langdetect/**/*.py` 源码字符（869 个不同码点） | 交集 = **0** |
| profile 中 `isupper` 的码点 | 127 个，全部 ≤ U+0490，**0 个**落在不一致集 |

即：**在本仓库的 profile 与全部 golden 用例上，75 个不一致码点完全不出现**，
因此不影响任何已测用例的 `detect_langs`。

### 1.7 但它是真实可触发的语义差（必须写明）

`probes/char_upper_impact.py` 用 monkeypatch 复刻 `NGram.add_char`，把
「MoonBit Unicode18 口径」注入真实上游，对同一文本跑 `_detect_block`：

| 用例 | 文本 | Python 口径 | MoonBit 口径 | 一致 |
| --- | --- | --- | --- | --- |
| plain_af | 纯拉丁文本 | `af 3feffff8e634a260` | 同 | 是 |
| with_tje | 文本内嵌 3 个 U+1C89 | `af 3feffff6a40e9976` | 同 | 是 |
| only_tje | 只有 U+1C89 | 抛 `LangDetectException` | 同 | 是 |
| with_garay | 内嵌 2 个 U+10D50 | `ca/en/tl` | 同 | 是 |
| **rep_A_tje** | `AᲉA A A ...` | `hu 3feffffccff6acab` | `hu 3feffffc2f48e5fe` | **否** |
| **rep_THE_tje** | `THE ᲉQUICK BROWN FOX` ×10 | `vi 3feffff5ed0d6ac5` | `en 3feffff6ee299850` | **否**（语言都变了） |
| rep_plain_repeat | 纯拉丁重复 + 空格包裹的 U+1C89 | 一致 | 一致 | 是 |

机制：U+1C89 被 MoonBit 判为大写后，`AᲉA` 连续两个「大写」把 `capitalword`
置真，导致整段 ngram 被跳过；Python 口径下它不算大写，ngram 照常进入概率更新。
`rep_THE_tje` 甚至把首选语言从 `vi` 改成 `en`。

**所以：只要输入文本含 Unicode 16+ 新增的大写字符，且它们与拉丁大写相邻，
两种口径的 detect_langs 就会分叉。** 这不是理论风险，是实测可复现的。

### 1.8 结论与建议

- 直接 `@ucd.is_uppercase`：99.9933% 一致，**在 profile 与现有用例上 100% 不影响结果**。
- 要求严格逐位复现 CPython 3.12：用 **路径 D**（`is_uppercase` + 75 码点补丁表），
  实测 0 不一致，代价是一张 27 段的区间表。
- 替代路径 B/C 都不可取（651 / 195 个不一致）。

---

## 2. 任务 2：浮点累加顺序可达性

详细数据见 `docs/port/float-add-conclusion.md`，这里只列关键结论。

| 场景 | 组数 | 比较对象 | 对数 | 一致 | 首个不一致 |
| --- | --- | --- | --- | --- | --- |
| A-uniform（55 个正数） | 200 | 输入位型 | 11000 | 11000 | 无 |
| A-uniform | 200 | 朴素左到右累加 | 200 | 200 | 无 |
| B-extreme（1e300/1e-300/次正规/相消） | 50 | 输入位型 | 2750 | 2750 | 无 |
| B-extreme | 50 | 朴素左到右累加 | 50 | 50 | 无 |
| C-negative（负 alpha 产生负概率） | 50 | 输入位型 | 2750 | 2750 | 无 |
| C-negative | 50 | 朴素左到右累加 | 50 | 50 | 无 |
| C-negative | 50 | `p/sump`（两种分母） | 5500 | 5500 | 无 |
| E-stochastic（完整链路） | 7 | 归一化结果 | 385 | 385 | 无 |
| D-langprob7（`langprob[j] += h[j]/7`，7×55） | 7 | 每轮后状态 | 385 | 385 | 无 |

合计 **24154 个逐位比较值，0 个不一致**。

关键发现（不在 MoonBit 侧，在 Python 侧）：

| 比较 | 对数 | 一致 | 首个不一致 |
| --- | --- | --- | --- |
| `sum(xs)` vs 显式 `acc += x` | 307 | **69** | A-uniform 组 1：`4039bd256889ff8d` vs `4039bd256889ff8c` |
| `sum(xs)` vs Neumaier 复刻 | 307 | **307** | 无 |

CPython 3.12 的内建 `sum()` 对 float 走 **Neumaier 补偿求和**（gh-100425）。
`_normalize_prob` 的 `sump = sum(prob)` 因此**不是**朴素累加：
A-uniform 145/200、B-extreme 50/50、C-negative 40/50、E-stochastic 3/7 组
与朴素循环不同，连带 `prob[i] = p / sump` 在 C-negative 有 2027/2750 个值改变。

而 `_detect_block` 的 `self.langprob[j] += prob[j] / self.n_trial` 是就地 `+=`，
无补偿：实测 Python 朴素循环与 MoonBit 朴素 `+` 385/385 逐位一致，照抄即可。

**结论：MoonBit(native) 的顺序 `Double` 累加与 CPython 3.12 bit-exact 一致**
（含次正规数、1e300、1e300+(-1e300) 相消、负值）。
唯一要求是**算法要对**：`_normalize_prob` 必须实现 Neumaier 循环，
`langprob +=` 必须用朴素顺序加法。

---

## 3. C1 端到端剩余不可控因素

逐条判定（C1 = 固定 seed 下 detect_langs 概率逐位一致）：

| 环节 | 状态 | 依据 |
| --- | --- | --- |
| MT19937 / `random()` / `getrandbits` / `_randbelow` | 可控，已逐位一致 | `docs/port/rand-feasibility.md`（21206/21451，正式管线 0 差异） |
| `gauss` | 可控，条件明确：`log` 必须用 libm | 同上，`@math.ln` 有 1 ulp 差（66/2000） |
| 浮点累加 | 可控，已逐位一致 | 本文件 §2，24154/24154 |
| `sum(prob)` 语义 | 可控，但**必须实现 Neumaier** | §2，朴素循环只有 69/307 一致 |
| `isupper` | **唯一剩下的不可控点** | §1，Unicode 18 vs 15 差 75 个码点 |

**明确回答：C1 端到端还剩一条不可控因素 —— `isupper` 的 Unicode 版本差。**

- 在**本仓库 profile + 现有 golden 用例**范围内：不可控因素**不出现**
  （交集为 0），C1 可判定为成立。
- 在**任意用户输入**范围内：只要文本含 Unicode 16/17/18 新增的大写字符
  （如 U+1C89、U+10D50..、U+16EA0..、U+1DF40..），且与拉丁大写相邻，
  两种口径会产生不同的 ngram 序列，`detect_langs` 概率（甚至首选语言）会分叉。
  已实测 2/7 用例分叉（`rep_A_tje` 概率不同，`rep_THE_tje` 语言不同）。
- 消除方式已实测可行：**路径 D**（`is_uppercase && !post15_upper(cp)`）
  在全码点上 0 不一致，代价是一张 75 码点 / 27 段区间表。

另外两项不是「不可控」，但属于实现纪律：
1. `gauss` 的 `log` 必须绑定 libm（`extern "C" log`），不能用 `@math.ln`；
2. `_normalize_prob` 的 `sum` 必须复刻 Neumaier，不能用朴素循环。

---

## 4. 未测项

- **Unicode 版本对齐的其他字符属性**：本次只测 `isupper`。上游 `NGram.normalize`
  还依赖 `unicode_block()`（按码点区间分块）与 `LATIN1_EXCLUDED` 等常量，
  这些是硬编码码点区间，与 Unicode 版本无关，但**未逐个对拍**。
- **`isupper` 在多字符字符串上的语义**：上游只用单字符 `ch.isupper()`，
  未测 `str.isupper()` 的字符串级语义（也不需要）。
- **`@ucd.is_uppercase` 之外的大小写 API**（`to_uppercase` 返回 String 的全映射）
  未做全码点对拍。
- **浮点累加的非 double 场景**：只测 55 元素 × 固定长度；未测 55 之外的
  langlist 长度（上游固定 55）。
- **`sum()` 的 Neumaier 实现细节**在 MoonBit 侧已由 `cmd/float` 探针复刻并
  307/307 一致，但**未接入真实检测实现**（本任务不实现业务逻辑）。
- **其他平台/目标**：只测 Windows x64 native；wasm/js target 未测。

---

## 5. 本轮交付文件

| 路径 | 说明 |
| --- | --- |
| `probes/char-probe/` | 新 MoonBit 工程（`preferred_target = "native"`），依赖 `moonbit-community/unicode-data@0.6.0` |
| `probes/char-probe/cmd/main/main.mbt` | 全码点 isupper 位集 + 三条替代路径 + 抽样点 + `post15_upper` 补丁表 |
| `probes/char_probe_compare.py` | 全码点对拍 |
| `probes/char_upper_impact.py` | 75 码点对 detect_langs 的实际影响 |
| `probes/char-probe/compare_stdout.txt` | 对拍原始输出 |
| `probes/char-probe/impact_stdout.txt` | 影响测量原始输出 |
| `docs/port/golden/char_isupper_compare.json` | 全码点对拍结果（含 75 码点完整清单） |
| `docs/port/golden/char_upper_impact.json` | 影响测量结果 |
| `probes/rand-probe/cmd/float/main.mbt` | 浮点累加探针 |
| `tools/gen_float_golden.py` | 浮点 golden 生成器 |
| `docs/port/golden/float_add_python.json` | 浮点 golden |
| `probes/float_probe_compare.py` | 浮点逐位比对 |
| `docs/port/golden/float_add_compare.json` | 浮点比对结果 |
| `docs/port/float-add-conclusion.md` | 浮点详细结论 |
