# moon_langdetect 架构决策记录（ADR）

- 版本：v1（2026-10-20）
- 输入证据：`docs/port/upstream-behavior-contract.md`、`docs/port/golden/`、`analysis/toolchain-probes.md`、`analysis/probe-tables.md`、`probes/logs/`
- 约束：本文件只做裁决与理由，不写 PRD、不写业务代码；所有数字引用自上述证据，未重测。

**引用简写**

| 简写 | 实体 |
|---|---|
| `CONTRACT §n` | `docs/port/upstream-behavior-contract.md` 第 n 节 |
| `GOLDEN` | `docs/port/golden/expected.json` / `summary.json` |
| `TC §X` | `analysis/toolchain-probes.md` 第 X 节 |
| `PT` | `analysis/probe-tables.md` |

---

## 0. 裁决总表

| # | 主题 | 裁决 | 状态 |
|---|---|---|---|
| C | 兼容档 | **C1（位级复刻）为主目标**：native 目标逐位；js/wasm-gc 目标 C2 容差（目标差异，非缺陷） | 已定 |
| N | 目标运行面 | **native（主）+ js（次）+ wasm-gc（experimental）** | 已定 |
| S | 种子策略 | **对照测试固定 seed=0/42；产品默认 `None`（随上游）** | 已定 |
| D | 档案承载 | **编译期内嵌 + flat 紧凑编码**为默认；运行时读文件为可选 feature | 已定 |
| B | 短文本/无特征 | **新增独立 API**，主 API 保持上游语义 | 已定 |
| A | 验收度量 | **native：`prob_bits` 逐位一致为硬门槛**；js/wasm-gc：容差（待校准） | 已定（js 容差待校准） |
| P | 依赖口径 | **默认零第三方依赖**；`moonbitlang/async` 仅可选 native feature；Unicode 大小写用 U3 内嵌表 | 已定 |
| U | Unicode 大小写语义 | **U3**：内嵌 CPython 3.12 生成的 Uppercase 区间表（1951 码点） | 已定 |
| X | 不移植范围 | 训练期管线/`load_json_profile`/verbose **不移植**；`set_prior_map`/`set_max_text_length` **移植** | 已定 |

---

## C. 兼容档：C1 / C2 / C3

| 项 | 内容 |
|---|---|
| **决策** | **C1（位级复刻）为主目标，按目标分档**：<br>① **native 目标 = C1**：固定 seed（0/42）下 `detect_langs` 的概率按 `prob_bits` **逐位一致**；实现依赖一条 `extern "C" fn log` 绑定 libm（替代 `@math.ln`）。<br>② **js / wasm-gc 目标 = C2**：概率按容差比对（js 下 `@math.ln` 变 `Math.log`，`extern "C"` 不适用）。这是**目标能力差异**，不是实现缺陷，须在 README/CI 中按目标声明。<br>③ 两档共同保留上游全部可观察语义（含 quirk）。 |
| **理由** | ① **RNG 链路已实测可逐位**：MT19937 原始字、`random()` double、`getrandbits`、`_randbelow` 全部逐位一致（`rand-feasibility.md §4` 表，纯整数/移位/乘加，无外部依赖）。② **分界点只有一个：`gauss` 里的 `log`**——`gauss(0,1)` 用 libm `log` 时 **512/512 × 4 seed 一致**；混合调用序列 **7/7 gauss + 357/357 choice** 与真实上游逐值相等（`rand-feasibility.md:67,99-100`）。③ `@math.ln` 是纯 MoonBit 多项式，2000 点扫描中 **66 点差 1 ulp（1934/2000）**，最小反例 x=1.0241975132：CPython/libm `3f987bb422dcde86` vs `@math.ln` `3f987bb422dcde87`（`rand-feasibility.md:152-165`）。④ 汇总：**68 阶段中 59 全一致，21451 对值 21206 对一致，9 个不一致全部是 `@math.ln` 对照组**（`rand-feasibility.md:110`）。⑤ `cos`/`sin` 在 native 下 MoonBit 本就是 `extern "C"`，2000 点全一致；`sqrt` 走 `Double::sqrt` 亦全一致（`rand-feasibility.md §3`）。⑥ 1 ulp 影响实测：alpha 偏移约 1e-17 时 **0/20 案例改变概率位型**，1e-9 才 16/20（`rand-feasibility.md §4.1`）——属概率性、不保证，故严格逐位必须用 libm `log`。 |
| **被否决替代** | **C2 作为全目标**：否决——RNG 已证明可逐位（21206/21451 对一致，剩余 9 个不一致全在可控的 `@math.ln` 对照），放弃位级等于放弃最强的对照证据，且会让 native 与 js 的验收口径被无谓拉低到同一弱标准。**C1 覆盖全部目标**：否决——js/wasm-gc 下 `extern "C"` 不适用、`@math.ln`→`Math.log`（`rand-feasibility.md §5`），无法声称位级。**C3 产品优先**：否决——会改变 `detect()` 对空输入的行为、可能「修正」URL 吞词与死代码豁免，导致 `GOLDEN` 268 条中至少 18 条异常案例与多条 URL 案例失配（`CONTRACT §10` quirk 2、3）。 |
| **代价 / 复开条件** | 代价：① native 侧需维护一条 `extern "C"` 绑定（libm `log`），**跨平台 libm 一致性未测**（只测 Windows x64 / UCRT / native，`rand-feasibility.md §5`）。② js/wasm-gc **不能声称位级**，需按目标分别声明验收口径。③ C1 只在**固定 seed** 下有意义（见 S 行）。**复开条件**：若 `docs/port/c1-residual-risks.md`（`isupper` Unicode 语义 / 浮点累加顺序）报出**不可控**因素 → 降级为 C2，并在本行写明触发的那一条与证据指针。 |

---

## N. 目标运行面：native / +wasm-gc / +js

| 项 | 内容 |
|---|---|
| **决策** | 发布支持三目标，但**分级承诺**：**native = 完整支持（已实测 56/56）**；**js = 支持（验证环境受限，见下）**；**wasm-gc = experimental（仅保证 build，测试本机不可验证）**。 |
| **理由** | ① native：build 0 / test 0 / 56/56（`TC §C.1`；`probes/logs/target-native-02-test.log`）。② js：build 0 / test 0 / 56/56，但**依赖 `probes/bin/node.cmd` → bun 1.4.3 绕行**；本机 `node.cmd` 指向不存在的 `D:\nvm4w\nodejs\bun`，`node --version` 报 `The system cannot find the path specified.`（`TC §C.2`；`probes/logs/node-plain-version.log`、`target-js-02-test-noshim.log`）→ **未用官方 node 验证**。③ wasm-gc：build 0 / test `0xC0000139`，且**空工程 `probes/tiny-probe` 同样失败**、`moonrun.exe` 连 `--help` 都返回 `0xC0000139`（`TC §C.2`；`probes/logs/tinyprobe-test-wasm-gc.log`、`moonrun-help.log`）→ 失败与本机运行器相关，**与数据规模无关**。④ 文件读取 API 仅 native/wasm：`moonbitlang/async/fs.read_file` 在 wasm-gc/js 构建报 `Value read_file not found in package fs`（`TC §C.3`；`probes/logs/fsprobe-build-wasm-gc.log`）——这直接影响 D 行必须选内嵌。 |
| **被否决替代** | **仅 native**：否决——放弃 js/wasm-gc 的既有 build 证据（两者 build 均为 0），与「多端可用」目标不符。**native+wasm-gc（不含 js）**：否决——wasm-gc 是三者中唯一不可验证的，把不可验证目标当主承诺、把可验证的 js 排除，风险倒挂。 |
| **代价 / 复开条件** | 代价：wasm-gc 只能声明「build 通过」，测试缺口需在 CI 说明。**复开条件**：① 换一台 `moonrun.exe` 可正常启动的机器重跑 `moon test --target wasm-gc` → 若 56/56 则升级为完整支持；② 用官方 node 重跑 js 测试 → 若 56/56 则 js 去掉「验证受限」标注。 |

---

## S. 种子策略

| 项 | 内容 |
|---|---|
| **决策** | **两处口径分开**：<br>① **对照测试**：显式固定 `seed=0` 与 `seed=42` 两套，逐案例比对；不使用 `None`。<br>② **产品默认**：`seed=None`（与上游一致，不可复现），但必须提供显式设置入口（等价 `DetectorFactory.seed`）。 |
| **理由** | ① 上游默认 `DetectorFactory.seed = None`（`detector_factory.py:29`），`random.Random.seed(None)` 取系统熵（`CONTRACT §4.1`）。实测未设 seed 时同一文本 10 次中 `"Otec matka syn."` 出现 `fi`/`pl` 两种结果（`GOLDEN.unseeded_runs`）。② 固定 seed 下 14 组（7 文本 × 2 seed）重复 5 次**逐字节一致**（`GOLDEN.repeatability[*].all_identical`）；seed 0 vs 42 有 125/134 组概率不同、其中 122 组首位语言不变（`GOLDEN.seed_diff`）。③ 若产品默认固定 seed，会与上游默认行为分叉，且掩盖「短文本不可复现」这一上游事实。 |
| **被否决替代** | **产品默认固定 seed=0**：否决——改变上游默认可观察行为，且让用户误以为结果确定；同时使 `GOLDEN` 的 `unseeded_runs` 证据失去意义。**对照测试只用单 seed**：否决——无法覆盖 seed 敏感性（125 组差异是本项目已知的最大数值方差来源）。 |
| **代价 / 复开条件** | 代价：产品默认行为不可复现，需在 README 显式提示；且 **native 下的 C1 位级复刻只在固定 seed（0/42）时有判定意义**——`seed=None` 时连上游自身都不可复现，无位级可言。**复开条件**：若下游要求「同输入同输出」的确定性契约 → 改为默认固定 seed，并同步修订 C 行的兼容档说明。 |

---

## D. 档案承载方式

| 项 | 内容 |
|---|---|
| **决策** | **编译期内嵌 + flat 紧凑编码**（`key\tcount\n` 扁平字符串，运行时 `split` + `parse_int`）为**默认且唯一默认路径**；native 运行时读文件作为**可选 feature**（需 `moonbitlang/async`）。 |
| **理由（量化）** | ① **map 编码在 55 语言下不可用**：`moon test` 失败 `0xC00000FD`（栈溢出），exe 运行退出码 `3221225725`（`TC §B.3`；`probes/logs/s55-map-03-test.log`、`s55-map-04-run.log`）。② flat 在 55 语言下全绿：`data.mbt` **2,205,308 B**、冷编译 **2.814–2.830 s**、exe **3,256,320 B**、`moon test` **56/56**、运行输出 `total: 184129`（`TC §B.3`；`probes/logs/s55-flat-03-test.log`、`s55-flat-04-run.log`）。③ flat/map 比值：生成字节 **0.6309**、编译秒 **0.1874**、exe 字节 **0.1642**、`_build` 字节 0.1545（`PT` 末表；`TC §B.4`）。④ 发布包实测 zip **949,937 B / 12 文件**，最大成员 `lib/data/data.mbt` 2,205,308 B（`TC §C.4`；`probes/logs/package.log`）。⑤ 跨目标：内嵌数据在 native/wasm-gc/js 三目标均 build 成功（`TC §C.1`）；而运行时读文件仅 native/wasm（`TC §C.3`）。⑥ 档案规模：55 文件 / 184,129 条目 / 2,204,952 B，键长仅 1~3、非 BMP 0 条（`TC §A.1`）。 |
| **被否决替代** | **map 字面量内嵌**：否决——55 语言栈溢出实测失败（同上）。**native 运行时读文件为默认**：否决——wasm-gc/js 无 `read_file`（`TC §C.3`），会直接砍掉两个目标；且引入 async 依赖。**宿主注入（调用方传数据）**：否决——把 2.2 MB 数据负担外移给每个使用方，违背「离线、可嵌入」定位，且无实测支撑其可行性。 |
| **代价 / 复开条件** | 代价：启动时需解析 184,129 条（split/parse）——**解析耗时未测**（见待回填表）；消费方冷编译约 2.8 s 的链接成本（本机实测，他机未验证）。**复开条件**：① 若实测解析耗时不可接受（阈值待定）→ 评估二分/惰性解析或二进制编码；② 若 `mooncakes` 服务端存在体积限制（未取证）→ 评估分包或压缩。 |

---

## B. 短文本与无特征输入

| 项 | 内容 |
|---|---|
| **决策** | **新增独立 API**（如「带置信度的检测」）承载申报书的「<50 字符返回低置信提示」；**主 API `detect`/`detect_langs` 保持上游语义不变**：空/纯符号输入抛 `CantDetectError(5)`，短文本照常检测并返回概率分布。 |
| **理由** | ① 上游对空/纯空白/纯 emoji/纯数字/纯标点/纯 URL **全部抛 `CantDetectError(5)`「No features in text.」**（`CONTRACT §9`、`detector.py:149-150`；`GOLDEN.summary.error_cases` 18 条 = 9 类 × 2 seed）。② `unknown` 只在概率列表为空时由 `detect()` 返回（`detector.py:137-139`），实测 268 条 + 3000 随机短串**未触发**（`CONTRACT §4.3`、`§12`）。③ 上游对短文本照常检测，实测长文本 55/55、短文本 51/55（`GOLDEN.detect_accuracy_short_seed0`，miss：`short-bg`/`short-no`/`short-zh-cn`/`short-zh-tw`）。④ 申报书要求低置信提示（`申报书` 第 34 行）——这是**新增能力**，不是上游语义，混入主 API 会破坏对照。 |
| **被否决替代** | **改主 API 语义**（空输入返回 `unknown`、短文本返回特殊标记）：否决——直接违背 `GOLDEN` 的 18 条异常案例与 4 条短文本基线，C2 档失去意义。**完全不实现低置信提示**：否决——违背申报书交付项。 |
| **代价 / 复开条件** | 代价：两套 API 语义并存，需在 README 明确区分。**复开条件**：若评审要求主 API 也带置信度 → 用附加字段/包装类型扩展，不改抛异常行为。 |

---

## A. 验收度量

| 项 | 内容 |
|---|---|
| **决策** | **分档硬门槛（无一处是「建议」）**：<br>① **所有目标 + 所有档**的硬门槛：`detect` 的 top-1 语言一致；`detect_langs` 的**语言序列与顺序**一致；异常案例的**异常类型 + code + 消息**一致。<br>② **native = C1，硬门槛为 `prob_bits`（IEEE754 大端 hex）逐位一致**，不再是容差。<br>③ **js / wasm-gc = C2，概率按容差比对**；容差数值标为**待校准**，校准依据必须来自 js 目标的实测（不得凭空写数）。<br>④ 准确率基线不变：长文本 **55/55**、短文本 **51/55**（seed=0）；seed=42 作为第二套同口径基线。<br>⑤ **native 的 C1 门槛仅在固定 seed（0/42）下有判定意义**（见 S 行）。 |
| **理由** | ① `GOLDEN` 的 `prob_bits` 已按 IEEE754 大端 hex 记录（`expected.json.meta.note`），正是为逐位比对预留。② 上游浮点运算顺序固定（`CONTRACT §4.4`），RNG 侧已实测 21206/21451 对逐位一致、剩余 9 个不一致全在 `@math.ln` 对照（`rand-feasibility.md:110`）——即「用 libm `log` 即可逐位」已被证明，故 native 可取逐位作硬门槛。③ js/wasm-gc 的 `@math.ln`→`Math.log` 且 `extern "C"` 不适用（`rand-feasibility.md §5`），位级不可达，只能取容差。④ 短文本 51/55 是实测基线而非目标值（`GOLDEN.detect_accuracy_short_seed0.n = 55`），低于它说明实现偏离。⑤ 异常消息原文已固化在 `CONTRACT §9`。 |
| **被否决替代** | **只比 top-1**：否决——丢失 `detect_langs` 的排序与阈值（`p > 0.1` 严格过滤，`detector.py:235`）契约。**短文本设 55/55 目标**：否决——与上游实测矛盾（4 条已知 miss）。**native 沿用容差**：否决——RNG 已证明可逐位，改用容差会掩盖真实偏差。**顺手写死一个容差值（如 1e-6）**：否决——缺乏 js 侧实测支撑，须等校准。 |
| **代价 / 复开条件** | 代价：① 逐位门槛对浮点累加顺序敏感（见 T14），实现期必须在同一顺序上累加。② js 容差未定之前，js 目标只能跑「结构 + 准确率」门槛。**复开条件**：① js 侧实测概率差分布 → 据此设定容差（同时回填 T12）；② 若 `c1-residual-risks.md` 报出 `isupper` / 累加顺序不可控 → 按 C 行复开条件降级 native 至 C2。 |

---

## P. 依赖与版本口径

| 项 | 内容 |
|---|---|
| **决策** | **默认零第三方运行时依赖**（仅 MoonBit 标准库）；`moonbitlang/async`（实测 `0.21.3`）**仅在可选 native 文件加载 feature 中引入**，并按目标裁剪；不引入 `moonbitlang/x`、`moonbit-community/unicode-data` **等任何第三方依赖**。Unicode 大小写属性以 **U3 的内嵌表**为准（见 U 行），不依赖任何第三方 Unicode 包。 |
| **理由** | ① 默认路径是编译期内嵌 flat 字符串（D 行），运行期不需要文件 IO，因此不需要 `async`。② `moonbitlang/async/fs.read_file` 能读真实档案（`chars=28151, has_freq=true`，`TC §C.3`；`probes/logs/fsprobe-run.log`），但 `src/fs/moon.pkg` 用 `targets:` 限定为 `["native","wasm"]` → wasm-gc/js 构建失败（`TC §C.3`）。③ `moon ide doc @fs` 未命中 core `@fs`，命中 `moonbitlang/async/fs`（`probes/logs/idedoc-at-fs.log`）；`open_file` 无结果（`idedoc-open_file.log`）——API 面需以 `read_file`/`open` 为准。 |
| **被否决替代** | **把 `async` 作为必需依赖**：否决——会直接砍掉 wasm-gc/js 的默认构建。**引入第三方 JSON 解析（运行时读档案）**：否决——多一层依赖与解析成本，且同样受目标限制。 |
| **代价 / 复开条件** | 代价：可选 feature 需额外的 target gate 与文档说明；U3 表需一个生成脚本（见 U 行）。**复开条件**：若 MoonBit 提供跨目标文件读取 → 重新评估运行时加载路径。

---

## U. Unicode 大小写语义（`isupper`）

| 项 | 内容 |
|---|---|
| **决策** | **U3**：用 CPython 3.12.10 的 `unicodedata` 直接生成 **Uppercase 属性**的区间表（**1951 个 True 码点**，生成后压缩为区间表），实现 `is_upper_cp312(ch)` 作为 `NGram.add_char` 的 `ch.isupper()` 判定源（`ngram.py:44`）。**禁止**直接使用 `@char.is_ascii_uppercase`、`moonbitlang/x/unicode`、`moonbit-community/unicode-data` 作为判定源。 |
| **理由** | ① **ground truth 就是 CPython 3.12 本身**：上游 `isupper()` 的语义由运行它的 CPython 决定，直接取同一版本的属性表即构造性对齐。② **零第三方依赖**，与 D 行「模型即数据 / 默认零依赖」一致（P 行）。③ **不会被上游 Unicode 版本升级悄悄改变**：表随本仓库版本化，不随依赖漂移。④ 实测证据（`docs/port/c1-residual-risks.md §1.2`）：全码点 **1112064** 点中 `@ucd.is_uppercase` 有 **75 点不一致**（Python `chr(cp).isupper()` 为 True 的共 **1951** 点，MoonBit 判 True 共 2026 点；75 点**全部**是 Python=0 / MoonBit=1，且 Python 类别全为 `Cn`），成因是 **Unicode 15.0.0（Python 3.12.10）vs 18.0.0（`unicode-data@0.6.0`）**（`c1-residual-risks.md:80-111`）。⑤ 该差异**在任意用户输入上可触发**：`rep_THE_tje`（`THE ᲉQUICK BROWN FOX` ×10）首选语言从 `vi` 变为 `en`，`rep_A_tje` 概率位型不同（`c1-residual-risks.md:186,191`）——机制是 U+1C89 被 MoonBit 判大写后与相邻拉丁大写凑成 `capitalword`，整段 ngram 被跳过（`ngram.py:44-48`、`CONTRACT §5.1`）。⑥ 但在本仓库语料上交集为 **0**：55 档案的 **3160** 码点、268 golden 的 **849** 码点、上游源码的 **869** 码点均不含这 75 点（`c1-residual-risks.md:166-168`）——即现有 golden 无法暴露该分叉，必须靠构造性对齐。 |
| **被否决替代** | **U1 = `@ucd.is_uppercase`（直接依赖 `moonbit-community/unicode-data`）**：否决——99.9933% 一致（1111989/1112064）但**任意输入可分叉**（`rep_THE_tje` 实测语言翻转），且引入第三方依赖、版本随依赖漂移。**U2 = `@ucd` + 75 码点补丁表**：否决——实测 0 不一致（1112064/1112064，`c1-residual-risks.md:151`），但仍依赖第三方包，且补丁方向是「把 18.0 回退到 15.0」，语义脆弱、依赖版本升级即失效。**路径 B = `to_upper(c)==c && to_lower(c)!=c`**：否决——**651 点不一致**（1111413/1112064），典型反例 U+03D2 `ϒ`（Lu 但简单大写映射恒等）。**路径 C = `general_category == Lu`**：否决——**195 点不一致**（1111869/1112064），反例 U+2160 罗马数字（Nl 但 Python 判 True）。 |
| **代价 / 复开条件** | 代价：① 需一个**生成脚本**（从 `.venv` 的 CPython 3.12 读 `unicodedata`，全码点扫 `chr(cp).isupper()`，压缩为区间表）；② 一张内嵌表（1951 码点，**压缩后区间数待测**，见 T16）；③ Python 版本升级（如 3.13 换 Unicode 15.1）时表须重新生成。**复开条件**：① 上游 langdetect 改到不同 Unicode 版本的 Python 运行 → 重生成表；② 实测发现 CPython 侧 `str.isupper` 语义（`cased && uppercase`，非单纯 `Uppercase` 派生属性）与该表不符 → 改用 **`str.isupper` 全码点实测结果**生成（口径以实测为准，不以属性定义为准）；③ 若 CPython 3.12 的 `isupper` 与 `Uppercase` 属性集合存在差异（本次未逐一验证二者完全相等）→ 同上改用实测口径。 |

---

## X. 不移植范围（逐项）

| 上游项 | 指针 | 裁决 | 理由 |
|---|---|---|---|
| `LangProfile.add` / `omit_less_freq` / `update`（训练期） | `lang_profile.py:28-70`；`CONTRACT §8.2/§8.3` | **不移植** | 包内**无运行时调用点**（`grep` 仅定义处 + 测试）；模型即数据，无训练需求；申报书明确「不做训练管线」。 |
| `set_prior_map` | `detector.py:76-91`；`CONTRACT §9` | **移植（P2）** | 契约明确（含 2 条 `InitParamError`，实测消息原文已固化）；实现成本低；影响 `_init_probability`（`detector.py:173-180`）。 |
| `set_max_text_length` | `detector.py:93-97`；`CONTRACT §3.1` 第 4 点 | **移植** | 截断时机在 URL/邮箱/VI 清洗之后、空格折叠之前（`detector.py:104-112`），是 `append` 契约的一部分；默认 10000。 |
| `load_json_profile` | `detector_factory.py:66-78` | **不移植** | 仅服务于上游测试的注入路径；异常语义是把一切重包成 `FormatError(1)`，对产品无价值。 |
| verbose 输出（`set_verbose` / `six.print_`） | `detector.py:70-71,165-166,170-171,207-208` | **不移植** | 需 stdout 与 `%s`/`%.5f` 格式化（`detector.py:215-221`）；不影响检测结果；产品用日志/回调替代。 |
| `DetectorFactory.clear` | `detector_factory.py:94-96` | **移植** | 12 行、无副作用，是测试辅助的必要能力。 |
| `NoTextError(0)` / `CantOpenTrainData(6)` / `TrainDataFormatError(7)` | `lang_detect_exception.py:2,8,9` | **不移植（枚举保留占位）** | 包内无抛出点（`grep` 仅定义处），不可触发（`CONTRACT §9`、`§12`）；保留码值以免错误码表断裂。 |

---

## 风险登记表

| # | 风险 | 触发条件 | 影响 | 缓解 |
|---|---|---|---|---|
| R1 | **wasm-gc 目标在本机不可验证** | 需要确认 wasm-gc 测试结果时 | 无法证明 56/56；只能声明「build 通过」 | 明确标 experimental；换 `moonrun.exe` 可用环境重跑（`TC §C.2`；`moonrun-help.log` 均 `0xC0000139`）；对照空工程 `tiny-probe` 排除数据因素 |
| R2 | **js 仅有 bun 替代验证** | 用户使用官方 node 运行时 | 行为可能不同（未测） | 记录绕行细节（`probes/bin/node.cmd` → bun 1.4.3，`TC §C.2`）；CI 中用官方 node 补测后解除 |
| R3 | **mooncakes 服务端限制未取证** | 首次真实 `moon publish` | 可能因体积/文件数被拒（zip 949,937 B / 12 文件） | `--help` 无限制条款（`TC §C.4`）；首次发布前先 `--dry-run` 或小包试发布；预留拆包方案 |
| R4 | **55 语言内嵌后消费方编译耗时** | 下游项目依赖本库 | 冷编译 2.814–2.830 s、exe 3,256,320 B 传导至下游（`TC §B.3`） | 提供 feature 裁剪（按语言子集）；文档标注体积；跟踪下游实测 |
| R5 | **上游 quirk 不复刻导致对照失败** | 实现时「顺手修正」URL 吞词/死代码豁免/异常语义 | `GOLDEN` 268 条大面积失配 | quirk 清单（`CONTRACT §10`）进验收清单；CI 跑 golden 全量而非抽样 |
| R6 | **`rand-probe` 已回填：C1 可行** | 决定 C1/C2 时 | ~~兼容档悬空~~ → 已裁决为 C1（native 逐位）；分界点 = `gauss` 的 `log`，用 libm `extern "C" log` 即 512/512 × 4 seed 一致（`rand-feasibility.md §4`） | 已回填，无需缓解；后续按 R11/R12 跟踪残余风险 |
| R7 | **本机 node 安装损坏** | 在新机器复现 js 测试 | 直接报 `The system cannot find the path specified.` | 文档化绕行（`TC §C.2`）；CI 固化运行时检查 |
| R8 | **误用 map 编码导致栈溢出** | 后续开发者改回 `Map[String,Int]` 字面量 | `0xC00000FD`，产物启动即崩（`TC §B.3`；`s55-map-03-test.log`） | 生成器只产出 flat；在 `gen_mbt.py` 与 CI 中禁止 map 模式用于 55 语言 |
| R9 | **运行时文件加载若成为默认** | 有人把 `read_file` 路径设为默认 | wasm-gc/js 构建报 `Value read_file not found in package fs` | 依赖口径（P 行）写死；feature 需 target gate |
| R10 | **js/wasm-gc 概率容差未校准** | C2 档验收比对 | 过松则放过偏差，过紧则误报失败 | 容差留空（**待校准**），校准依据必须来自 js 目标实测（`rand-feasibility.md §5` 未测 js）；不得凭空写数（A 行复开条件） |
| R11 | **`extern "C" log` 跨平台 libm 末位差异未测** | 换 Linux/macOS 构建与运行 | native 的 C1 逐位一致性可能失效（Python 与该平台 libm 是否仍同位未实测；`rand-feasibility.md §5` 只测 Windows x64/UCRT/native） | CI 在每个目标平台跑 `GOLDEN` 全量（不只本机）；README 逐位声明限定在已验证平台；必要时在 CI 加 `log` 位型对拍 |
| R12 | **`isupper` 语义不可对齐** → **已裁决并关闭** | ~~实现 `NGram.add_char` 的 capitalword 判定时~~ 已由 U3 消除 | 构造上 100% 对齐（表由 CPython 3.12.10 `unicodedata` 生成，1951 码点）；原先的 75 点版本差不再进入实现 | **已关闭**。残余风险转移为「表生成源版本漂移」→ 见 R13 |
| R13 | **内嵌 Uppercase 表的生成源版本漂移** | 上游改用其他 Python/Unicode 版本运行，或本项目重生成表时版本不同 | 表与上游 ground truth 错位 → C1 位级门槛失效（`c1-residual-risks.md §1.3` 已证 75 点差即可让 `rep_THE_tje` 语言翻转） | 生成脚本把 `sys.version` + `unicodedata.unidata_version` 写入表头；CI 断言表头版本 = **3.12.10 / 15.0.0**；上游版本变更时重生成（U 行复开条件①） |

---

## 待回填 / 未测项表

| # | 项 | 状态 | 回补触发条件 |
|---|---|---|---|
| T1 | **`rand-probe`：MoonBit 能否复刻 CPython MT19937 / `gauss` / `choice` 管线** | **已回填：可行（C1）**；分界点 = `gauss` 的 `log`，改用 libm `extern "C" log` 后 512/512 × 4 seed 一致、混合序列 7/7 gauss + 357/357 choice 一致（`rand-feasibility.md §4`） | 已完成 → C 行已改为 C1；残余见 T13/T14/T15 |
| T2 | wasm-gc 在可用 `moonrun` 环境下的真实测试结果 | 未测（运行器坏） | 换机器后 `moon test --target wasm-gc` 成功 → 回填 N 行 |
| T3 | js 在官方 node 下的测试结果 | 未测（本机 node 损坏） | 官方 node 可用 → `moon test --target js` → 回填 N 行 |
| T4 | mooncakes 服务端体积/文件数限制 | 未取证 | `moon publish` 成功或得到明确拒绝 → 回填 R3 |
| T5 | `s55-map` 失败的 `0xC00000FD` 具体栈帧 | 未测 | 需要解释栈溢出根因时做栈回溯 |
| T6 | flat 内嵌数据的**启动解析耗时**（184,129 条 split/parse） | 未测 | 首次性能基准 → 回填 D 行代价 |
| T7 | 空概率列表 → `unknown` 分支 | 未测（268 golden + 3000 随机短串未触发） | 构造出触发输入 → 回填 B/A 行 |
| T8 | 负 alpha（`gauss` 极端值） | 未测（`rand-feasibility.md §5` 未覆盖；只测了 `gauss(0,1)` 与整数 seed） | 若需覆盖非整数 seed / `gauss` 非 (0,1) → 回填 C 行 |
| T9 | `FileLoadError(2)` 触发路径 | 未测（Windows 难以复现） | 跨平台实测 → 回填错误码表 |
| T10 | 跨机器 `os.listdir` 顺序对并列排序的影响 | 未验证 | 换文件系统/机器复跑 `GOLDEN` → 回填 A 行 |
| T11 | seed=42 长文本/短文本准确率 | 未统计（数据已在 `GOLDEN`） | 需要第二套基线时按 `tags` 过滤统计 → 回填 A 行 |
| T12 | **js/wasm-gc 的 C2 概率容差取值** | **待校准**（原「暂定 1e-6」已撤销；`rand-feasibility.md §5` 未测 js target） | js 目标实测概率差分布 → 据此设容差，回填 A 行③ |
| T13 | **`isupper` Unicode 语义一致性**（`ngram.py:44-48` capitalword 判定） | **已回填 → U3 裁决**（`docs/port/c1-residual-risks.md §1`；`@ucd` 75 点差已有实测复现） | 已完成，见本文 U 节；R12 关闭、R13 承接残余风险 |
| T14 | **浮点累加顺序一致性**（`_detect_block` 的 `langprob[j] += prob[j]/n_trial` 与 `_update_lang_prob` 的连乘累加，`detector.py:161-169`） | 进行中（同 `c1-residual-risks.md`） | 结论落地 → 若不可控，native 位级门槛降回容差 |
| T15 | **端到端 `detect_langs` 位级一致性**（随机数管线之外的 ngram 抽取 + 概率更新全链路） | 未测，属实现期验证（`rand-feasibility.md §5` 明示只覆盖随机数管线） | MoonBit 实现完成后跑 `GOLDEN` 268 条全量 → 回填 A 行②是否达标 |
| T16 | **U3 内嵌表的区间数与生成体积**（1951 个 True 码点压缩后剩多少区间、生成 `data.mbt` 字节） | 未测，属实现期 | 生成脚本产出后实测 → 回填 U 行代价②与 D 行体积口径 |
| T17 | **`is_upper_cp312` 与 CPython 全码点对拍**（1112064 可比点，须 0 不一致） | 未测，实现期**必须做** | MoonBit 实现后跑全码点对拍（跳过 2048 surrogate，与 `c1-residual-risks.md §1.2` 同口径）→ 结果写入 A 行②的验收记录 |

---

## 附：证据指针索引

| 结论 | 指针 |
|---|---|
| 档案规模 55/184,129/2,204,952 B、键长 1~3、非 BMP 0 | `TC §A.1`；`tools/profile_stats.py` |
| `ko` 最大 23,031 条 / 307,193 B，`gu` 最小 1,474 条 | `TC §A.1` |
| map 55 语言栈溢出 | `probes/logs/s55-map-03-test.log`、`s55-map-04-run.log`；`TC §B.3` |
| flat 55 语言全绿 56/56、`total: 184129` | `probes/logs/s55-flat-03-test.log`、`s55-flat-04-run.log`；`TC §B.3` |
| flat/map 比值 0.6309 / 0.1874 / 0.1642 | `PT` 末表；`TC §B.4` |
| 三目标 build/test | `probes/logs/target-{native,wasm-gc,js}-0{1-build,2-test}.log`；`TC §C.1` |
| wasm-gc 与数据无关（空工程同样失败、`moonrun.exe` 自身坏） | `probes/logs/tinyprobe-test-wasm-gc.log`、`moonrun-help.log`；`TC §C.2` |
| js 需 bun 绕行、官方 node 未验证 | `probes/logs/node-plain-version.log`、`node-shim-version.log`、`target-js-02-test-noshim.log`；`TC §C.2` |
| `read_file` 仅 native/wasm | `probes/logs/fsprobe-build-wasm-gc.log`、`fsprobe-run.log`；`TC §C.3` |
| zip 949,937 B / 12 文件、无体积条款 | `probes/logs/package.log`、`publish-help.log`、`mooncake-help.log`；`TC §C.4` |
| 上游常量与默认值 | `CONTRACT §2`；`detector.py:44-68`、`detector_factory.py:29` |
| 空/纯符号抛 `CantDetectError(5)` | `CONTRACT §9`；`detector.py:149-150`；`GOLDEN.summary.error_cases` |
| 长 55/55、短 51/55 | `GOLDEN.summary.detect_accuracy_*` |
| 同 seed 可复现、seed 间 125 组差异 | `GOLDEN.repeatability`、`GOLDEN.seed_diff` |
| 未设 seed 的不确定性 | `GOLDEN.unseeded_runs` |
| RNG 逐位可行（MT19937 / `random()` / `getrandbits` / `_randbelow`） | `docs/port/rand-feasibility.md §4` 表 |
| `gauss` 需 libm `log`：512/512 × 4 seed；混合序列 7/7 gauss + 357/357 choice | `docs/port/rand-feasibility.md:67,99-100,204` |
| `@math.ln` 对照 1934/2000，最小反例 x=1.0241975132（`3f987bb422dcde86` vs `…e87`） | `docs/port/rand-feasibility.md:108,152-165` |
| 汇总：68 阶段中 59 全一致、21451 对值 21206 对一致、9 个不一致全是 `@math.ln` 对照 | `docs/port/rand-feasibility.md:110` |
| 1 ulp alpha 扰动实测影响（0/20；1e-9 时 16/20） | `docs/port/rand-feasibility.md §4.1` |
| `isupper` 语义实测：1112064 可比点 / Python True 1951 / MoonBit True 2026 / 不一致 75（全 Python=0、MoonBit=1） | `docs/port/c1-residual-risks.md:80-86` |
| 75 点为 Unicode 15.0.0（Python 3.12.10）vs 18.0.0（`unicode-data@0.6.0`）版本差，已压为 27 段区间 | `docs/port/c1-residual-risks.md:93-111` |
| 本仓库语料交集为 0：profile 3160 码点 / golden 849 / 上游源码 869 | `docs/port/c1-residual-risks.md:166-168` |
| 任意输入可触发分叉：`rep_THE_tje` 首选从 `vi` 变 `en`；`rep_A_tje` 概率位型不同 | `docs/port/c1-residual-risks.md:186-191` |
| 四条路径对比：A 75 差 / B 651 差 / C 195 差 / D 0 差（但 D 依赖第三方包） | `docs/port/c1-residual-risks.md:148-159` |
| quirk 清单 | `CONTRACT §10` |