# moon_langdetect 语种检测库 — 设计文档（which / why）

> **文档标题（机器可检索）**：`moon_langdetect 语种检测库设计文档`
> **版本**：v1（2026-10-20）
> **状态**：生效
> **需求权威**：`docs/superpowers/prds/202610202129-moon-langdetect-语种检测-prd.md`（下称「PRD」，引用章节号而非复述）
> **裁决权威**：`docs/port/architecture-decisions.md`（下称「ADR」，引用节名 C/N/S/D/B/A/P/U/X 与 R/T 编号）
>
> 本文只回答 **which（选哪条路）+ why（为何这条赢）**。字段级 schema、API 签名、错误码表、实现顺序属 spec。

---

## 一、用户当前理解（认知校准结果）

开工前的默认认知与实测/裁决的差异，逐条校准。凡「校准后」一栏与「原认知」不同的，本文后续所有决策以此为准。

| # | 原认知 | 校准后（有证据） | 影响的设计决策 |
|---|---|---|---|
| K1 | 「移植 = 让结果大致对」 | native 目标下概率可与上游**逐位一致**：RNG 全链路 21206/21451 对一致，剩余 9 个不一致**全部**是 `@math.ln` 对照组（`docs/port/rand-feasibility.md` 汇总行）；改用 libm `log` 后 `gauss` 512/512 × 4 seed 一致（同文件 §2 表）。 | D1 兼容档按目标分档 |
| K2 | 「`sum()` 就是顺序累加」 | CPython 3.12 的 `sum(prob)` 是 **Neumaier 补偿求和**：307 组里只有 69 组与朴素循环相同（`docs/port/float-add-conclusion.md`「Python 内建 sum() 的真实语义」表）。误用朴素累加会让 `sump` 在 A-uniform 145/200、B-extreme 50/50 组上差 1 ulp。 | D3 随机与浮点管线 |
| K3 | 「档案可以运行时读文件，更灵活」 | 运行时读文件 API 仅 native/wasm 可用，wasm-gc/js 构建直接报 `Value read_file not found in package fs`（`analysis/toolchain-probes.md` §C.3）。 | D2 档案承载 |
| K4 | 「Map 字面量最自然」 | 55 语言 Map 字面量：编译 15.019–15.357 s、exe 19,826,688 B、`moon test` **栈溢出 `0xC00000FD`**（`analysis/toolchain-probes.md` §B.3）；扁平字符串同规模：2.814–2.830 s、3,256,320 B、56/56 通过。 | D2 档案承载 |
| K5 | 「`isupper` 用现成 Unicode 包即可」 | `@ucd.is_uppercase` 与 CPython 3.12 全码点比有 **75 点**不一致（Unicode 15 vs 18），且该差异**可被任意输入触发**（`rep_THE_tje` 首选从 `vi` 变 `en`，`docs/port/c1-residual-risks.md` §1.7）。 | D4 Unicode 大小写 |
| K6 | 「上游那些怪行为是 bug，移植时顺手修掉」 | URL 吞词、`cleaning_text` 死代码豁免、空输入抛 `CantDetectError(5)` 都是**契约**；268 条基准里 18 条就是异常案例（`docs/port/golden/summary.json`）。修掉即全面失配。 | D8 清洗契约 |
| K7 | 「产品默认应该固定 seed 才好用」 | 上游默认 `seed=None`，实测同一文本 10 次中 `Otec matka syn.` 出现 `fi`/`pl` 两种结果（`docs/port/golden/expected.json` 的 `unseeded_runs`）；固定 seed 会改变可观察默认行为。 | D3 随机与浮点管线 |
| K8 | 「wasm-gc/js 跟 native 一样能验证」 | wasm-gc 在本机**不可验证**：空工程 `tiny-probe` 同样 `0xC0000139`，`moonrun.exe` 连 `--help` 都失败（`analysis/toolchain-probes.md` §C.2）；js 仅以 bun 替代验证（同节）。 | D10 目标运行面分级 |
| K9 | 「PRD 的 268 条都能逐位比」 | 268 = **250 有概率输出 + 18 抛异常**（`docs/port/golden/summary.json`）；异常案例没有 `prob_bits`。 | 约定 C + D1 |

---

## 二、目标

见 PRD §二（G-01 至 G-05）。本文不重述目标值，只在决策追溯表中回链「该决策服务哪条 G」。

---

## 三、关键约束

### 3.1 技术约束

| 编号 | 约束 | 证据 |
|---|---|---|
| T1 | 概率逐位一致要求 `gauss` 里的 `log` 必须落到平台 libm，不能用纯 MoonBit 多项式 `@math.ln` | `docs/port/rand-feasibility.md` §3（2000 点中 66 点差 1 ulp，最小反例 x=1.0241975132：`3f987bb422dcde86` vs `…e87`） |
| T2 | `_normalize_prob` 的分母必须复刻 Neumaier 补偿求和，不能朴素累加 | `docs/port/float-add-conclusion.md`（307 组仅 69 组与朴素一致） |
| T3 | `langprob[j] += prob[j] / n_trial` **不是**补偿求和，朴素 `+` 即逐位一致 | `docs/port/float-add-conclusion.md`「关键事实清单」第 3 条（385/385） |
| T4 | 内嵌档案必须用扁平字符串编码；Map 字面量在 55 语言下栈溢出 | `analysis/toolchain-probes.md` §B.3；`probes/logs/s55-map-03-test.log` |
| T5 | 大小写判定必须以 CPython 3.12.10 的 `isupper` 真值为准（1951 个 True 码点） | `docs/port/c1-residual-risks.md` §1.2 |
| T6 | wasm-gc 在本机不可验证（运行器坏），js 仅 bun 替代 | `analysis/toolchain-probes.md` §C.2；`probes/logs/moonrun-help.log` |
| T7 | 文件读取 API 仅 native/wasm，wasm-gc/js 不可用 | `analysis/toolchain-probes.md` §C.3；`probes/logs/fsprobe-build-wasm-gc.log` |

### 3.2 成本约束

| 编号 | 约束 | 证据 |
|---|---|---|
| C1 | 55 语言内嵌后冷编译约 2.8 s、exe 约 3.26 MB，成本会传导给使用方 | `analysis/toolchain-probes.md` §B.3（s55-flat 行） |
| C2 | 发布包体积 949,937 B / 12 文件，服务端限制未取证 | `analysis/toolchain-probes.md` §C.4；`probes/logs/package.log` |
| C3 | 首次加载需解析 184129 条，解析耗时未测（ADR T6） | ADR 待回填表 T6 |

### 3.3 合规约束

| 编号 | 约束 | 证据 |
|---|---|---|
| L1 | 零第三方运行时依赖；不引入 `moonbitlang/x`、`moonbit-community/unicode-data` | ADR P 行 |
| L2 | 上游 MIT，本项目 MIT，README 注明出处 | `申报书-moon_langdetect-语种检测.md` §五 |
| L3 | 检测全程本地、零网络请求、不读用户数据文件 | PRD §5.2 安全性行；ADR B 行 |

---

## 四、非目标

见 PRD §三（6 条，含混合语言检测、档案重训练管线、方言/地区变体、上游训练期 API 移植、云端形态）。本文不重述；D12 只补充「ADR X 节逐项裁决」与 PRD §三的对应关系。

---

## 五、验收场景（回链 PRD US-XX）

| 场景编号 | 场景 | 回链 | 关键可观察结果 |
|---|---|---|---|
| S1 | 长文本主语言判定 | US-01 / FR-01 / G-01 | 55 条中/长文本首选语言与预期一致（上游基线 55/55，`docs/port/golden/summary.json`） |
| S2 | 概率分布形态 | US-02 / FR-02,03,04 / G-02 | 降序、仅保留 > 0.1、并列按档案顺序 |
| S3 | 固定 seed 位级一致 | US-03 / FR-05 / G-02 | native 下 250 条有概率输出样本 `prob_bits` 逐位一致 |
| S4 | 短文本低置信 | US-04 / FR-21,22,23 / G-04 | 55 条短文本走低置信分支，主 API 不受影响 |
| S5 | 失败路径分型 | US-05 / FR-08,09,11,12 / G-03 | 错误码 5 / 4 / 8 各自可观察，消息文本与上游一致 |
| S6 | 离线自包含 | US-06 / FR-13,14,24,25 / G-05 | 空目录可检测、外部数据文件读取 0 次、网络请求 0 次 |
| S7 | 参数控制 | US-07 / FR-07,10 | 长度上限截断、先验归一化 |

---

## 六、设计决策追溯表

> 说明：`P0/P1` 的每条 FR 至少被一行覆盖；`P2` 项同样登记，未覆盖者显式标注「由 spec 直接承接」。每一行的「代价」列写被弃项牺牲了什么。

| 编号 | 设计决策 | which / why 论证要点 | 回链 PRD 条目 | 代价（被弃项牺牲了什么） | 复开条件 |
|---|---|---|---|---|---|
| **D1** | **兼容档按目标分档**：native = C1（`prob_bits` 逐位）；js / wasm-gc = C2（容差，数值待校准） | 逐位可行性已被实测证明：RNG 全链路 21206/21451 对一致，9 个不一致**全部**来自 `@math.ln` 对照组（`docs/port/rand-feasibility.md` 汇总行）；换 libm `log` 后 `gauss` 512/512 × 4 seed 一致。因此 native 取逐位是**可达**而非理想化。js/wasm-gc 下 `extern "C"` 不适用、`@math.ln` 变 `Math.log`（同文件 §5 未测项），位级不可达。**被否决**：①「全目标统一 C2」——放弃已证明可达的最强对照证据，等于主动降低 native 验收强度；②「全目标 C1」——js/wasm-gc 无可达路径，会写出永远红的目标；③「C3 产品优先」——会改动空输入异常语义与 URL 清洗，268 条基准中 18 条异常案例 + 多条 URL 案例直接失配。 | FR-01, FR-02, FR-03, FR-05, FR-15, FR-18, FR-21, FR-22；G-01, G-02；US-01, US-03 | 放弃「一套口径覆盖三目标」的简洁性：README 与验收记录必须按目标分别声明，用户需理解 native 与 js 的数值差异来源。 | ADR C 行复开条件：若 `c1-residual-risks` 后续报出不可控因素（`isupper`/累加顺序）→ native 降级 C2；若 js 实测证明可位级 → 升级。 |
| **D2** | **档案承载 = 编译期内嵌 + 扁平字符串编码**；运行时不读外部数据文件 | 三选一实测对照：map 字面量 55 语言 `0xC00000FD` 栈溢出（`probes/logs/s55-map-03-test.log`）；flat 同规模 56/56 通过、`total: 184129`（`probes/logs/s55-flat-04-run.log`）；flat/map 比值 0.6309 字节 / 0.1874 编译秒 / 0.1642 exe（`analysis/probe-tables.md` 末表）。跨目标：内嵌在 native/wasm-gc/js 三目标均 build 成功（`analysis/toolchain-probes.md` §C.1），而运行时读文件仅 native/wasm（同 §C.3）。**被否决**：①「map 字面量」——栈溢出实测失败；②「native 运行时读文件为默认」——砍掉两个目标且引入 async 依赖；③「宿主注入」——把 2.2 MB 负担外移给每个使用方，与离线嵌入定位冲突。 | FR-13, FR-14, FR-25, FR-26；G-05；US-06 | 放弃「档案可热替换」的灵活性：更新档案必须重新编译；消费方承担约 2.8 s 冷编译与 3.26 MB exe 增量（`analysis/toolchain-probes.md` §B.3）；首次解析 184129 条的耗时未测（ADR T6）。 | ① 若首次解析耗时不可接受 → 评估二分/惰性解析或二进制编码；② 若 mooncakes 服务端有体积限制（ADR R3，未取证）→ 评估分包或按语言子集裁剪；③ 若 MoonBit 提供跨目标文件读取 → 重新评估运行时加载。 |
| **D3** | **随机与浮点管线按目标分两段**：`log` 走接缝（native=libm、js/wasm-gc=`@math.ln`）；`sum()` 一律复刻 Neumaier；`langprob += prob/7` 用朴素 `+` | `gauss` 公式见 `docs/port/rand-feasibility.md` §1 表（`x2pi=random()*TWOPI`；`g2rad=sqrt(-2*log(1-random()))`；缓存 `gauss_next`）。求和语义：`sum(prob)` 在 CPython 3.12 是 Neumaier（307 组仅 69 组与朴素同，`docs/port/float-add-conclusion.md` 表），而 `langprob[j] += prob[j]/7` 实测朴素 `+` 与 MoonBit 逐位一致 385/385（同文件「关键事实清单」3）。seed 默认 `None`（上游 `detector_factory.py:29`），实测未设 seed 会出现两种结果（`docs/port/golden/expected.json` 的 `unseeded_runs`）。**被否决**：①「全用 `@math.ln`」——2000 点中 66 点差 1 ulp，`gauss` 512 点中 seed=0 有 485/512 一致（27 点不一致，`docs/port/rand-feasibility.md` §2 对照组行），且因 `gauss_next` 缓存一次分叉会污染下一次调用；②「`sum()` 用朴素累加」——`sump` 在 A-uniform 145/200、B-extreme 50/50 组差 1 ulp 并向下游 2027/2750 个归一化值传播（`docs/port/float-add-conclusion.md`）；③「产品默认固定 seed」——改变上游默认可观察行为，且让 `unseeded_runs` 证据失去意义。 | FR-05, FR-06；G-02；US-03 | 放弃「单一路径覆盖所有目标」：接缝层必须持有两个 `log` 实现；native 侧多一条 `extern "C"` 绑定（跨平台 libm 一致性未测，ADR R11）。 | ① 若换平台后 libm 与 CPython 不同位（ADR R11）→ 该平台按容差档声明；② 若上游改用非整数 seed 或 `gauss(μ,σ)≠(0,1)`（ADR T8 未测）→ 重评。 |
| **D4** | **大小写判定 = U3 内嵌表**（CPython 3.12.10 `unicodedata` 生成，1951 码点 → 651 区间），禁止用 `@char.is_ascii_uppercase` / `moonbitlang/x/unicode` / `moonbit-community/unicode-data` | 全码点实测：`@ucd.is_uppercase` 有 75 点不一致（Python=0 / MoonBit=1，类别全 `Cn`），成因 Unicode 15.0.0 vs 18.0.0（`docs/port/c1-residual-risks.md` §1.2-§1.3）；该差异**可被任意输入触发**（`rep_THE_tje` 首选 `vi`→`en`，§1.7），但在本仓库 55 档案 3160 码点、268 golden 849 码点、上游源码 869 码点上交集为 0（§1.6）——即现有基准**暴露不了**它，只能靠构造性对齐。四路径对比：A 75 差 / B 651 差 / C 195 差 / D 0 差（§1.5 表）。**被否决**：①U1 直接依赖 `@ucd`——任意输入可分叉且引入第三方依赖；②U2 `@ucd` + 75 点补丁——0 差但仍依赖第三方，且补丁方向是「18.0 回退到 15.0」，语义脆弱；③路径 B `to_upper==c && to_lower!=c`——651 点不一致（反例 U+03D2）；④路径 C `category==Lu`——195 点不一致（反例 U+2160 罗马数字）。 | FR-18；US-03 | 放弃「跟随 Unicode 新版本」：表锁死在 15.0.0，上游升级需重生成；需一条生成脚本与一张表（651 区间，压缩后约 9.8 KB 文本，实测）。 | 上游改用其他 Python/Unicode 版本运行 → 重生成表并同步表头版本（约定 B / ADR R13）；若实测 `str.isupper`（`cased && uppercase`）与 `Uppercase` 属性集合不等 → 改用 `str.isupper` 全码点实测口径。 |
| **D5** | **公开能力面 = 四类**（无状态入口 / 可配置实例 / 语言列表 / 低置信入口），有状态实例为一等能力 | PRD §5.1 的 FR-07/10/19/20 都需要「可配置实例」作宿主（设置 seed、长度上限、先验、重复送入文本），否则这四条无载体、不可验收。上游对应物存在且语义已固化：`set_alpha`/`set_max_text_length`/`set_prior_map`（`docs/port/upstream-behavior-contract.md` §1.3、§3.1）。**被否决**：①「只暴露两个无状态函数」——FR-07/10/19/20 失去宿主；②「把配置做成全局单例」——多实例并发会互相污染 seed 与先验，且与上游「每次检测新建实例」的语义冲突。 | FR-07, FR-10, FR-19, FR-20；US-07；FR-05 | 放弃「最小 API 面」：调用方需理解实例生命周期；实例内的 `langprob` 缓存语义（FR-19）会被误当 bug。 | 若下游要求纯函数式接口 → 在无状态入口上加显式参数，实例能力仍保留。 |
| **D6** | **低置信 = 新增独立入口**，主 API 语义不变 | 上游对空/纯符号抛 `CantDetectError(5)`（`docs/port/upstream-behavior-contract.md` §9），短文本照常检测（实测长 55/55、短 51/55，`docs/port/golden/summary.json`）。申报书要求「<50 字符返回低置信提示」（`申报书-moon_langdetect-语种检测.md:34`）是**新增能力**。**被否决**：①「改主 API：空输入返回 `unknown`」——直接违背 18 条异常基准；②「改主 API：短文本返回特殊标记」——违背 4 条已知短文本基线；③「不做低置信」——违背申报书交付项。 | FR-21, FR-22, FR-23；G-04；US-04 | 放弃「单一入口的简洁」：两套语义并存，文档必须显式区分；调用方要选对入口。 | 若评审要求主 API 也带置信度 → 用附加字段扩展返回类型，不改抛异常行为。 |
| **D7** | **失败路径按成因分型**：无特征 → 码 5；未加载档案 → 码 4；参数非法 → 码 8；各自消息文本逐字对齐 | 三类成因在上游是**不同**的可观察契约（`docs/port/upstream-behavior-contract.md` §9 错误码表）：`No features in text.`（`detector.py:150`）、`Need to load profiles.`（`detector_factory.py:107`）、`Prior probability must be non-negative.` / `More one of prior probability must be non-zero.`（`detector.py:85,89`）。实测 18 条异常案例全部为码 5（`docs/port/golden/summary.json`）。**被否决**：①「统一成一个错误类型 + 统一文案」——三种成因的恢复动作不同（改输入 / 先加载 / 改参数），合并即丢失可操作性；②「返回 `unknown` 不抛」——与 18 条基准冲突。 | FR-08, FR-09, FR-11, FR-12；G-03；US-05 | 放弃「单一错误码」的简单：调用方需按码分支；异常类型需携带 4 个诊断字段（D11）。 | 若某成因在实际使用中不可达（如码 4 仅测试期出现）→ 保留码值但降级文档强调级别。 |
| **D8** | **清洗顺序与 quirk 逐条保真**：URL → 邮箱 → VI 规范化 → 截断 → 空格折叠；`cleaning_text` 的 LEA 豁免**照抄死代码**；`langsize=len(listdir)` 照抄 | 顺序是契约（`docs/port/upstream-behavior-contract.md` §3.1）；URL 字符类含 `.`/`-`/`;` 会继续吞 ASCII（实测 `http://a.com/x-then` → `' '`，`go http://a.com/x,TEXT` → `go ,TEXT`）；`unicode_block` 返回 int 而代码比字符串，豁免恒不生效（§10 quirk 1）；`langsize` 含点文件与子目录（实测 2 档案得向量长 4）。**被否决**：①「修正 URL 正则」——`GOLDEN` 中多条 URL 案例失配；②「修掉死代码豁免让越南语正确」——改变 `cleaning_text` 的剥离判据，长文本概率全变；③「`langsize` 改用有效档案数」——与上游向量长度语义分叉（FR-20）。 | FR-15, FR-16, FR-17；FR-20；US-03 | 放弃「让实现看起来正确」：代码里会保留一处明显像 bug 的比较；维护者需读契约才知道不能改。 | 若上游发布修正版 → 跟随上游版本重新取基准，本决策随之失效。 |
| **D9** | **输出过滤与排序照抄**：严格 `p > 0.1`；降序；并列保持档案加载顺序 | 过滤是严格大于（`detector.py:235`），0.1 本身被丢弃；`list.sort(reverse=True)` 稳定，并列保持 `langlist` 顺序（`docs/port/upstream-behavior-contract.md` §1.4，实测 `[c,b,a]` 保持输入序）。**被否决**：①「用 `>=` 更直观」——边界样本多出一条；②「并列时按语言代码排序」——与档案顺序不一致，跨机器可复现性反而变差（档案顺序是唯一权威序）。 | FR-02, FR-03, FR-04；US-02 | 放弃「确定性排序」：并列顺序依赖档案目录顺序（本机实测等于字典序，跨机器未验证，ADR T10）。 | 若跨机器 `os.listdir` 顺序被证实不同且影响基准 → 在约定 C 中登记平台基线。 |
| **D10** | **目标运行面分级**：native 完整支持；js 支持（验证受限）；wasm-gc 实验性（仅保证 build） | native build/test 均 0、56/56（`analysis/toolchain-probes.md` §C.1）；js 56/56 但依赖 bun 替代（同 §C.2，`probes/logs/target-js-02-test-noshim.log` 为失败对照）；wasm-gc 失败与本机运行器相关（空工程同样 `0xC0000139`，`moonrun.exe` 自身坏，同 §C.2）。零网络（FR-24）由「全内嵌数据 + 无外部服务调用」在本承载面上天然成立，非靠运行时禁用。**被否决**：①「仅 native」——放弃两个已 build 成功的目标；②「native+wasm-gc 不含 js」——把唯一不可验证的目标当主承诺，风险倒挂。 | FR-24；承载 PRD §5.2 兼容性行；影响 FR-01/02/12/13 在三目标的可达性 | 放弃「三目标同等承诺」：wasm-gc 只能声明 build 通过，用户需自担验证风险。 | 换 `moonrun.exe` 可用环境 → wasm-gc 升级；官方 node 验证 js → 去掉「验证受限」。 |
| **D11** | **失败诊断载体 = 异常对象四字段**（`code` / `message` / `input_len` / `input_prefix`），可序列化落记录 | PRD §5.2 失败可诊断性要求「可持久化、可检索」；上游异常已带 `code` 与消息（`lang_detect_exception.py:16-22`），但**没有**输入摘要。补两个字段即可在不改错误码语义的前提下让调用方落一条可检索记录。**被否决**：①「只靠错误消息」——消息是固定文案，无法定位是哪次输入；②「库内写日志文件」——违反「不写外部状态」（PRD §5.2 安全性）与零副作用。 | FR-08, FR-09, FR-11, FR-12；PRD §5.2 失败可诊断性行 | 放弃「异常保持最小」：异常对象体积略增（前 32 字符）；调用方需自行序列化。 | 若某目标运行时无法承载 4 字段 → 降级为 3 字段并在约定中登记。 |
| **D12** | **不移植范围照 ADR X 执行**：训练期三方法 / `load_json_profile` / verbose 不移植；`set_prior_map`（P2 级）/ `set_max_text_length` / `clear` 移植；三个死错误码保留码值不实现 | ADR X 逐项裁决已有依据（训练期方法无运行时调用点、`load_json_profile` 仅服务上游测试、verbose 需 stdout 格式化）。PRD §三 已把这批列入非目标。**被否决**：①「全量移植以最大化兼容」——扩大验收面却不增加用户价值；②「连码值也删」——错误码表断裂，与上游码 0/6/7 对照时无法解释。 | 非目标 §三；FR-07, FR-10（保留的配置能力） | 放弃「100% API 面兼容」：使用上游训练期 API 的调用方无法直接迁移（本库定位不接受该人群）。 | 若出现真实使用方要求训练期能力 → 作为独立 PRD 立项，不在本库内加。 |

### 6.1 FR 覆盖核对（P0/P1 逐条）

| FR | 覆盖决策 | 备注 |
|---|---|---|
| FR-01 | D1, D2 | 主语言返回值与取值域 |
| FR-02 | D1, D9 | 降序 |
| FR-03 | D9 | 严格 `> 0.1` |
| FR-05 | D1, D3, D5 | seed 生效 |
| FR-06 | D3 | 默认 `None` 的不可复现 |
| FR-07 | D5, D12 | 先验归一化（`set_prior_map` 移植） |
| FR-08 | D7 | 负先验 → 码 8 |
| FR-09 | D7 | 零和先验 → 码 8 |
| FR-10 | D5, D12 | 长度上限（`set_max_text_length` 移植） |
| FR-11 | D7 | 未加载 → 码 4 |
| FR-12 | D7, D8 | 无特征 → 码 5 |
| FR-13 | D2 | 内嵌 55 语言 |
| FR-14 | D2 | 零外部数据读取 |
| FR-15 | D8 | URL 吞词 |
| FR-16 | D8 | 邮箱剥离 |
| FR-17 | D8 | 拉丁剥离 |
| FR-18 | D4, D8 | capitalword 跳过 |
| FR-21 | D6 | 低置信入口 |
| FR-22 | D6 | 长文本走正常路径 |
| FR-23 | D6 | 主 API 不受影响 |
| FR-24 | D2, D10 | 零网络 |
| FR-25 | D2 | 档案字段消费与条目合计 |
| FR-26 | D2 | freq→prob 公式 |
| FR-04（P2） | D9 | — |
| FR-19（P2） | D5 | 缓存语义 |
| FR-20（P2） | D8, D5 | `langsize` 语义 |

> 无「由 spec 直接承接、无需方案决策」的 P0/P1 项——每条都有 which/why 分叉需要裁决。

---

## 七、门禁逐项结果

### G1 平台接缝一致性（PS1-PS3 / TB1-TB3 / RS1-RS4）

**PS1 接缝登记表**

| 能力 | 分叉轴 | 接缝层位置（持有分叉的模块） | 业务侧是否可见分支 |
|---|---|---|---|
| `log(x)` 用于 `gauss` | native（libm `extern "C"`）vs js / wasm-gc（`@math.ln`） | 单一「数学内核」接缝模块；对外只暴露 `ln_for_gauss(x)` | 否——业务侧只调 `ln_for_gauss` |
| `is_upper(cp)` | 无平台分叉（U3 内嵌表，全目标同一份数据） | 单一「字符属性」模块，对外 `is_upper_cp312(cp)` | 否——且**不是**平台分叉，登记于此仅为说明它与 `log` 同属「外部事实驱动的判定源」 |
| 档案数据访问 | 无平台分叉（编译期内嵌，全目标同一份） | 单一「档案」模块，对外按语言取表 | 否 |

**PS2 收编结论**：两处真实平台差异（`log`）全部收进数学内核接缝；业务侧（检测主流程、清洗、特征抽取、概率更新）**零**平台条件分支。`is_upper` 与档案数据**不是**平台分叉（同数据全目标共享），不建接缝、直接作为普通模块调用——若把它们也包成「按目标切换」的接缝，会制造不存在的分叉点。

**PS3 一致性对照**：仓库既有模式中，唯一同类先例是 `@math.cos` / `@math.sin`——native 下 MoonBit 本身就是 `extern "C"`（`docs/port/rand-feasibility.md` §3），即**平台差异由标准库内部吸收**。本设计对 `log` 的处理与之一致：差异吸收在接缝模块内部，业务侧不见分支。不一致点已登记：`cos`/`sin` 由标准库吸收、`log` 由本库接缝吸收——原因是标准库的 `@math.ln` 是纯 MoonBit 多项式（`math/log_double_nonjs.mbt`），无法满足 native 逐位要求。

**TB1 逐分支可测性**

| 分支 | 测试环境可达性 | 依据 |
|---|---|---|
| native + libm `log` | **可达**：native 目标 build/test 均通过（`analysis/toolchain-probes.md` §C.1，56/56） | `probes/logs/target-native-02-test.log` |
| js + `@math.ln` | **部分可达**：本机 node 损坏，须以 `probes/bin/node.cmd` → bun 1.4.3 替代（`analysis/toolchain-probes.md` §C.2）；未用官方 node 验证 | `probes/logs/node-plain-version.log`、`target-js-02-test-noshim.log` |
| wasm-gc + `@math.ln` | **不可达**：`moonrun.exe` 自身无法启动，空工程同样 `0xC0000139` | `probes/logs/moonrun-help.log`、`tinyprobe-test-wasm-gc.log` |

**TB2 不可达分支处置**：wasm-gc 分支**降级为交付环境验证**并显式登记——验收记录标注「本机不可验证，仅保证 build 退出码 0」，不声称测试通过。js 分支以 bun 替代运行时验证并在记录中标注运行时身份。**禁止**把 wasm-gc 分支写成「应该没问题」。

**TB3 守卫重构决策**：**不重构**。理由：`log` 的分支是**编译目标**级差异（由目标决定可用符号），不是可在运行期注入的配置——把它重构成运行时可切换，会引入一个生产中永不切换的开关，且无法在 wasm-gc 上真正执行。替代方案：把 `ln_for_gauss` 做成接缝模块的**公开可替换入口**（测试可注入替身），使 native 侧的数学逻辑可被独立验证；wasm-gc 仍按 TB2 降级登记。

**RS1-RS4 渲染接缝**：**N/A — 本库无用户可见界面**（纯库，无页面/组件/样式），故无引擎默认值差异、无贴边元素、无渲染断言载体问题。

### G2 外部契约真值源（XB1-XB3 / SD1-SD2 / TD1-TD3 / CF1-CF2）

**XB1 逐 API 登记**

| API | 真实签名（实参个数 / 顺序 / 含义） | 权威源 | 证据等级 |
|---|---|---|---|
| C 标准库 `log` | `double log(double x)`——**1 个实参**，顺序：待求自然对数的正实数；返回该值的自然对数 | ① **C 标准**：ISO/IEC 9899 `<math.h>` 声明 `double log(double)`（标准库函数名 `log`，1 参）；② 上游调用点：CPython `Lib/random.py` 的 `gauss` 调 `math.log`（`docs/port/rand-feasibility.md` §1 表第 45 行引述公式）；③ **真机探针**：MoonBit 侧 `pub extern "C" fn c_log(x : Double) -> Double = "log"`（`probes/rand-probe/rand-probe.mbt`），实测 2000/2000 点与 CPython `math.log` 逐位一致（`docs/port/rand-feasibility.md` §2 表「广域扫描 libm log vs CPython（2000 点） 2000/2000」） | **A**（真机探针 + 官方标准双重支撑） |

> 关于「这是 C 标准库符号名 `log`」的权威依据：ISO/IEC 9899（C 语言标准）在 `<math.h>` 中定义 `double log(double x)`，符号名即 `log`，由链接器在平台数学库（Windows 为 UCRT，Linux 为 glibc 的 libm）中解析。证据等级标注为 **A** 是因为「符号名 + 1 参形态 + 逐位一致」三者都有实测（`probes/rand-probe/rand-probe.mbt` 的绑定 + 2000 点比对），而不仅是文档引用。

**XB2 逐字签名**：`extern "C" fn c_log(x : Double) -> Double = "log"`——1 个位置参数 `x : Double`；无回调、无错误分支（C 的 `log` 对非正值返回 `-inf`/`NaN`，**不抛异常**）。调用方必须保证 `1 - random() > 0`——上游公式 `sqrt(-2*log(1-random()))` 中 `random()` 取值 `[0,1)`，故 `1-random() ∈ (0,1]`，恒为正，无需额外守卫（`docs/port/rand-feasibility.md` §1 表）。

**XB3 禁止记忆建模**：本条签名同时有标准、上游调用点、真机探针三重证据；不存在「按 web 习惯推断」的成分。**若 spec 需改动该绑定（如换符号名），必须先补一条真机探针，否则不得写入契约。**

**SD1 真值源决策**：**搬运探针已验证实现**（不是重新登记）。理由：`probes/rand-probe/rand-probe.mbt` 的 `c_log` 绑定与 2000 点比对已完成，属「旧权威代码 + 真机探针」双证；重新登记会引入手抄错误风险（ADR 的风险模式）。影响面：仅 `gauss` 路径的 `log` 一处；`cos`/`sin`/`sqrt` 由标准库承载，无需搬运。

**SD2 权威来源注释断言**：产品代码中该绑定行必须附注释指向 `probes/rand-probe/rand-probe.mbt` 与 `docs/port/rand-feasibility.md` §2（2000/2000）。

**TD1 替身签名来源**：`ln_for_gauss` 的测试替身签名**只**来自 XB1 行（1 个 `Double` 入参、1 个 `Double` 返回），**不**从被测实现照抄。

**TD2 契约守卫**：构造签名不符的调用（0 参 / 2 参）→ 断言编译期即失败或替身走失败分支；用例必须红。这是防止「三参退两参」类回退的回归保护。

**TD3 类型独立溯源**：`Double` 是语言内建类型，无自建类型定义 → 无可溯源的自建类型；替身输入输出直接用 `Double`，溯源至 XB1 行。

**CF1 调用形态断言**：对 `c_log` 的每个调用点断言「1 个实参、类型 `Double`、返回值参与 `-2.0 *` 乘法」；绑定签名回退（改 2 参）时用例直接红。

**CF2 回退红断言**：由 TD2 的守卫承接。

### G3 降级等价（FE1-FE3）

**FE1 逐条登记**

| 降级路径 | 触发条件 | 降级后可观察行为 | 与主路径是否等价 |
|---|---|---|---|
| `ln_for_gauss` → `@math.ln` | 目标为 js / wasm-gc（`extern "C"` 不可用）；或 native 下 C 运行时缺失（理论情形） | 检测仍完成，返回语言列表与概率；概率末位可能与 native 不同 | **非等价**（见 FE2） |
| 档案 → 无降级 | — | 内嵌数据全目标可用，无降级路径 | N/A |
| 大小写表 → 无降级 | — | U3 表全目标同一份，无降级路径 | N/A |

**FE2 显式声明「非等价降级」**

- 实测差异：`@math.ln` 在 2000 点扫描中 **66 点差 1 ulp（1934/2000 一致）**（`docs/port/rand-feasibility.md` §3.1 末段）；`gauss` 512 点中 seed=0 有 **485/512** 一致（27 点不一致，§2 对照组行）。
- **为何可接受**：① 差异量级为 1 ulp（约 1e-16 相对误差），`alpha = 0.5 + g*0.05` 随之偏移约 1e-17；实测把该量级扰动注入上游后，**0/20 案例**改变最终概率位型（1e-9 才 16/20，`docs/port/rand-feasibility.md` §4.1 表）。② js/wasm-gc 本就声明为容差档（D1），不承诺位级。
- **用户可见差异**：概率数值末位可能不同 → 在这些目标上，`detect_langs` 的概率可能与 native 相差极小量；**首位语言**在 20 例实测中未变。必须在 README 按目标声明，禁止写成「等价」。
- **禁止写法**：不得写成「可接受等价降级」——它是**非等价**降级，只是影响被量化后可接受。

**FE3 硬依赖缺失时的可观察行为**

| 硬依赖 | 缺失时行为（设计定义，不留 TBD） |
|---|---|
| libm `log` 符号（native） | 若链接期找不到 `log` → 构建失败（不是运行期降级）；若运行期 C 运行库缺失 → 进程无法启动，由宿主环境报错。**不定义静默回退到 `@math.ln`**——静默回退会让 native 悄悄失去位级承诺，比失败更糟。 |
| 内嵌档案 | 无缺失可能（编译期常量）。 |
| U3 表 | 无缺失可能（编译期常量）。 |

> 若某目标完全没有可用 `log`（既无 `extern "C"` 也无 `@math.ln`）：不存在此情形——`@math.ln` 是纯 MoonBit 实现，全目标可用。该问题在设计上已闭合。

### G4 权威派生约定文档（AD1-AD3）

**AD1 独立权威文档**：三份约定各自独立成文（不在本文正文散写约定内容），标题机器可检索、均含版本号 `v1`、均含「适用范围 / 约定正文 / 门禁命令 / 生成物所有权」四段；本文只引用标题与路径。

| 约定 | 路径 | 版本 | 硬承诺条数 | 门禁命令 |
|---|---|---|---|---|
| A：档案内嵌数据格式与生成契约 | `docs/superpowers/designs/202610202129-moon-langdetect-语种检测-convention-a-profile-embed.md` | v1 | 6（A1-A6） | 见该文 §3 |
| B：U3 Unicode 大小写表生成契约 | `docs/superpowers/designs/202610202129-moon-langdetect-语种检测-convention-b-uppercase-table.md` | v1 | 6（B1-B6） | 见该文 §3 |
| C：golden 基准消费契约 | `docs/superpowers/designs/202610202129-moon-langdetect-语种检测-convention-c-golden.md` | v1 | 6（C1-C6） | 见该文 §3 |

**AD2 实测核验**（本文写作时已重跑，非事后补跑）：

| 约定 | 命令 | 输出 | 退出码 |
|---|---|---|---|
| A | 声明数/条目数统计（约定 A §3 C-A1/C-A2） | `decls 55 entries 184129` | 0 |
| A | `wc -c` 与 2205308 比对（C-A3） | 相等 | 0 |
| A | `grep -c 'Map::from_array'`（C-A4） | 0 | 0 |
| A | 生成清单 `mode`（C-A5） | `flat` | 0 |
| B | 版本/计数/区间数断言（C-B1/C-B3/C-B4） | `ok 1951 cps / 651 intervals` | 0 |
| C | 268=250+18（C-C2） | `ok 268=250+18` | 0 |
| C | `prob_bits` 形态（C-C1/C5） | `ok prob_bits hex16` | 0 |

**AD3 指针链**：本文 §八 逐字引用三份文档的**完整标题**；spec 必须逐字引用同一标题；计划与代码审查携带同一指针。下游只引用、不复制正文。

### G5 跨契约交叉影响（ND1-ND3 / WB1-WB3）

**ND1 既有谓词全集（机检枚举，非印象）**

| 谓词编号 | 谓词 | 枚举命令 | 结果 |
|---|---|---|---|
| P1 | 仓库级 CI / 门禁脚本 | `find . -maxdepth 3 -name "*.yml" -o -name "*.yaml" -o -name "Makefile" -o -name "*.sh" \| grep -v ".venv\|_build\|.mooncakes"` | 仅 `./langdetect/.travis.yml`（上游只读仓，不受本设计影响） |
| P2 | git 忽略规则 | `git rev-parse --show-toplevel` | `fatal: not a git repository`，退出码 128 → 工作区根**不受任何 .gitignore 约束** |
| P3 | PRD 校验器是否扫描目录 | `grep -n "glob\|iterdir\|walk\|scandir" validate_prd.py` | 无命中 → 只校验 stdin 指定的单文件 |
| P4 | 既有脚本对 `docs/` 的写入面 | `grep -ln "docs/" tools/*.py probes/*.py` | 6 个脚本，全部只写 `docs/port/golden/`（`tools/gen_golden.py`、`tools/gen_float_golden.py`、`tools/gen_rand_golden.py`、`probes/char_upper_impact.py`、`probes/float_probe_compare.py`、`probes/rand_probe_compare.py`） |
| P5 | 文档命名约束 | `validate_prd.py` 的 `FILENAME_RE = ^\d{12}-.+-prd\.md$` + 落点必须 `docs/superpowers/prds` | 只约束 PRD |
| P6 | 探针工程忽略规则 | `cat probes/embed-probe/.gitignore` | `_build/ target/ .mooncakes/ .moonagent/` |
| P7 | 既有代码是否引用 `superpowers` | `grep -rn "superpowers" --include=*.py tools probes` | 0 命中 |

**ND1 逐实体干跑**

| 新实体 | × P1 | × P2 | × P3 | × P4 | × P5 | × P7 |
|---|---|---|---|---|---|---|
| E1 设计文档 `…-design.md` | 不命中 | 不适用（非 git） | 不命中（不被扫描） | 不命中 | **命中**（若误用 PRD 校验器会红） | 不命中 |
| E2 约定 A `…-convention-a-….md` | 不命中 | 不适用 | 不命中 | 不命中 | 不命中（不以 `-prd.md` 结尾） | 不命中 |
| E3 约定 B | 同上 | 不适用 | 不命中 | 不命中 | 不命中 | 不命中 |
| E4 约定 C | 同上 | 不适用 | 不命中 | 不命中 | 不命中 | 不命中 |
| E5（spec 期）产品生成器脚本 | 不命中 | 不适用 | 不命中 | **可能命中**（若误写 `docs/port/golden/`） | 不命中 | 不命中 |

**ND2 命中项裁决**

| 命中 | 裁决 | 理由 |
|---|---|---|
| E1 × P5 | **改形态（不豁免）**：设计文档**不走** `validate_prd.py`；该脚本只对 PRD 生效。干跑已确认：对 design 路径运行会 8 项失败（`filename_location` 等），这是**预期行为**，不是缺陷。 | 设计文档与 PRD 是不同文档类型，不应共享同一校验器；豁免会让 PRD 校验器语义模糊。 |
| E5 × P4 | **改形态（预防性裁决）**：产品生成器**不得**写 `docs/port/golden/`（该目录是只读证据区）；产品产物落产品源码目录。 | 与 PRD §5.2 安全性的「不写外部状态」一致；也避免与既有 6 个脚本的写入面冲突。 |

**ND3 干跑命令登记**：上表每条命令可重跑；E1×P5 的干跑记录为「对 design 路径运行 `validate_prd.py` → exit 1，8 项失败，其中 `filename_location` 明确指出落点/文件名不符」——该结果作为**反向验收**（证明设计文档不被 PRD 校验器管辖）。

**WB1 承载面表**

| 承载对象 | 承载面（选定） | 被否决候选 + 理由 | 验收可达性反查 |
|---|---|---|---|
| 55 语言档案数据 | **编译期内嵌常量**（扁平字符串） | ①运行时文件：wasm-gc/js 无 `read_file`（`analysis/toolchain-probes.md` §C.3），且引入 async 依赖；②宿主注入：把 2.2 MB 负担外移，违背离线嵌入定位；③Map 字面量：55 语言栈溢出（同 §B.3） | 可达：三目标 build 均 0（同 §C.1）；`total: 184129` 可复现（`probes/logs/s55-flat-04-run.log`） |
| `log` 实现 | **数学内核接缝模块**（native=libm / js·wasm-gc=`@math.ln`） | ①全局用 `@math.ln`：2000 点 66 点差，native 失去位级；②全局用 `extern "C"`：js/wasm-gc 不可用 | native 可达（56/56）；js 部分可达（bun）；wasm-gc 不可达（已按 TB2 登记） |
| 大小写判定 | **字符属性模块 + U3 内嵌表** | ①第三方 Unicode 包：75 点差 + 违反零依赖；②运行时读 Unicode 数据文件：同档案的跨目标问题 | 全目标可达（纯数据） |
| 失败诊断信息 | **异常对象四字段** | ①库内写日志：违反「不写外部状态」；②仅消息文案：无法定位输入 | 全目标可达（纯内存对象） |
| 低置信入口 | **独立公开入口** | ①改主 API：违背 18 条异常基准；②不提供：违背申报书 | 可达（纯逻辑） |

**WB2 下游允许触碰的文件清单（从承载表推导）**

| 承载面 | 下游（spec/plan）允许新增或修改的落点 |
|---|---|
| 档案内嵌常量 | 产品档案数据产物文件（路径由 spec 定）+ 其生成器；**不得**改 `docs/port/golden/` |
| 数学内核接缝 | 接缝模块文件（`log` 两实现 + `ln_for_gauss` 入口）+ 其测试替身 |
| 字符属性模块 | 属性模块文件 + U3 表产物 + 生成脚本 |
| 检测主流程 | 清洗/特征/概率更新模块文件（零平台分支） |
| 公开能力面 | 入口模块 + 结果类型定义 |

> 反向禁止：不得由「仓库现有目录布局」倒推承载落点（例如不能因为 `probes/` 下已有 `embed-probe` 就把产品代码放进 `probes/`）。

**WB3 承载 × 既有约束交叉核对**

| 承载决策 | 零第三方依赖（ADR P） | 目录所有权 | 生成物目录（GO） | 结论 |
|---|---|---|---|---|
| 内嵌档案 | 不引入依赖 ✅ | 产品数据落产品目录，不进 `docs/port/` ✅ | 数据文件是生成物，须登记不手改清单 ✅（约定 A §4） | 无冲突 |
| `log` 接缝 | 不引入依赖（C 标准库符号，非第三方包）✅ | 落产品源码目录 ✅ | 非生成物 ✅ | 无冲突 |
| U3 表 | 不引入依赖 ✅（这是选 U3 的核心原因） | 落产品源码目录 ✅ | 生成物，须登记（约定 B §5）✅ | 无冲突 |
| 异常四字段 | 不引入依赖 ✅ | 落产品源码目录 ✅ | 非生成物 ✅ | 无冲突 |

### G6 验收可达性反查（逐决策两栏）

| 决策 | 栏 1：技术方案可达性（是否破坏 PRD 验收条目的可观察性） | 栏 2：交付结构可达性 |
|---|---|---|
| D1 | 可达——native 逐位有实测支撑（21206/21451）；js/wasm-gc 容差需先校准，否则该两目标只判结构项 | N/A — 单份 PRD，无兄弟单元 |
| D2 | 可达——`total: 184129` 与 56/56 均有日志 | N/A — 同上 |
| D3 | 可达——`gauss` 512/512、`sum` 307/307 Neumaier 均有实测 | N/A — 同上 |
| D4 | 可达——1951 码点与 0 不一致目标可机检（约定 B） | N/A — 同上 |
| D5 | 可达——实例能力使 FR-07/10/19/20 有宿主 | N/A — 同上 |
| D6 | 可达——低置信入口独立，主 API 基准不变 | N/A — 同上 |
| D7 | 可达——三码各自可构造（实测 18 条码 5） | N/A — 同上 |
| D8 | 可达——清洗后文本可直接读取断言（`append_cleanup` 探针） | N/A — 同上 |
| D9 | 可达——排序/阈值可直接读返回列表 | N/A — 同上 |
| D10 | **部分可达**——wasm-gc 不可验证，已在 TB2 登记降级 | N/A — 同上 |
| D11 | 可达——四字段可序列化并回读 | N/A — 同上 |
| D12 | 可达——不移植项在 PRD §三 已有排除理由 | N/A — 同上 |

**时序可达性**：N/A — no cross-unit artifact references（单份交付，无跨单元产物引用）。

### G7 双形态契约（DC-E）

**候选**：扁平字符串编码规则在 `probes/gen_mbt.py`（探针实现）与产品生成器（未来实现）两处表述。

**裁决**：**唯一权威形态 = 约定 A（`约定 A：档案内嵌数据格式与生成契约` v1）**。

- `probes/gen_mbt.py` 降级为**参考实现**（示范如何产出符合约定的编码），不是权威。
- 产品生成器是**派生实现**，必须满足约定 A 的 A1-A6。
- 同步方式（机检对账命令）：对探针产物与产品产物分别跑约定 A §3 的 C-A1/C-A2/C-A4，两者必须都输出 `decls 55 entries 184129` 且 `Map::from_array` 计数为 0。
- 实测：探针产物已跑通（`decls 55 entries 184129`，退出码 0）；产品产物在 spec 期落地后补跑同一命令。

**为何不构成「两种可并存形态」**：编码规则只有一份定义（约定 A），探针与产品是同一规则的两次实例化，不是两套规则。若未来产品生成器改用不同编码（如二进制），则**必须**先改约定 A 并重跑对账，否则视为双形态违规。

---

## 八、权威约定文档指针链

| 约定 | 完整标题（逐字引用） | 版本 | 本文引用位置 |
|---|---|---|---|
| A | `约定 A：档案内嵌数据格式与生成契约` | v1 | D2、G4、G7、WB1/WB3 |
| B | `约定 B：U3 Unicode 大小写表生成契约` | v1 | D4、G4、WB1/WB3 |
| C | `约定 C：golden 基准消费契约` | v1 | D1、D9、G4、K9 |

**AD3 指针链要求**：spec 必须逐字引用上述三个标题（禁止简称「A 约定」「B 表」）；plan 携带同一指针；代码审查按约定 A/B/C 的 §3 门禁命令核验。下游只引用不复制正文。

---

## 九、未知项

| 编号 | 未知项 | 为何现在不能定 | 处置（回填触发） |
|---|---|---|---|
| U1 | js / wasm-gc 的概率容差取值 | 该两目标的概率差分布未实测（`docs/port/rand-feasibility.md` §5） | js 目标实测差值分布后回填约定 C §4 与 ADR A 行 |
| U2 | wasm-gc 真实测试结果 | 本机运行器坏（空工程同样失败） | 换环境重跑 56 条断言 |
| U3 | 首次加载解析 184129 条的耗时 | 未测（ADR T6） | 实现后实测，与 PRD NFR 性能目标比对 |
| U4 | 消费方编译耗时增量 | 未测 | 使用方工程实测 |
| U5 | mooncakes 服务端体积/文件数限制 | 未取证（`--help` 无条款，未成功发布） | 首次发布或小包试探 |
| U6 | 跨平台 libm 与 CPython 是否仍同一位型 | 仅 Windows x64 实测（`docs/port/rand-feasibility.md` §5） | 目标平台重跑全量对照 |
| U7 | 档案目录顺序在跨机器上是否稳定 | 本机恰为字典序（ADR T10） | 换文件系统复跑基准 |
| U8 | `str.isupper` 与 `Uppercase` 属性集合是否完全相等 | 本次未逐一验证（约定 B 复开条件③） | 生成表时用 `str.isupper` 全码点实测口径核对 |

---

## 十、被否决方案汇总

| # | 被否决方案 | 否决依据 | 牺牲了什么 |
|---|---|---|---|
| 1 | 全目标统一 C2（容差） | RNG 已证明可逐位（21206/21451） | 放弃 native 的最强对照强度 |
| 2 | 全目标统一 C1（位级） | js/wasm-gc 下 `extern "C"` 不可用、`@math.ln`→`Math.log` | 会写出永远红的目标 |
| 3 | C3 产品优先（顺手修 quirk） | 18 条异常 + 多条 URL 案例直接失配 | 放弃「代码看起来正确」 |
| 4 | Map 字面量内嵌 | 55 语言栈溢出 `0xC00000FD` | 放弃 map 的查表直观性 |
| 5 | native 运行时读文件为默认 | wasm-gc/js 无 `read_file` | 放弃档案热替换 |
| 6 | 宿主注入档案 | 把 2.2 MB 负担外移，违背离线嵌入 | 放弃「零内置数据」的轻包 |
| 7 | 全局用 `@math.ln` | 2000 点 66 点差、gauss 485/512 | 放弃单一路径的简洁 |
| 8 | `sum()` 用朴素累加 | 307 组仅 69 组一致，2027/2750 归一化值受影响 | 放弃朴素循环的直觉性 |
| 9 | 产品默认固定 seed | 改变上游默认行为、`unseeded_runs` 证据失效 | 放弃开箱即得的确定性 |
| 10 | U1 直接用 `@ucd.is_uppercase` | 75 点差且任意输入可分叉 + 违反零依赖 | 放弃「跟随最新 Unicode」 |
| 11 | U2 `@ucd` + 75 点补丁 | 仍依赖第三方；补丁方向反了 | 放弃「0 差但依赖」的折中 |
| 12 | 路径 B `to_upper==c && to_lower!=c` | 651 点不一致 | — |
| 13 | 路径 C `category==Lu` | 195 点不一致 | — |
| 14 | 只暴露两个无状态函数 | FR-07/10/19/20 失去宿主 | 放弃最小 API 面 |
| 15 | 配置做成全局单例 | 多实例互相污染 seed/先验 | 放弃「全局一处配置」 |
| 16 | 改主 API 让空输入返回 `unknown` | 违背 18 条异常基准 | 放弃「不抛异常」的友好性 |
| 17 | 统一错误类型 + 统一文案 | 三种成因恢复动作不同 | 放弃单码简单性 |
| 18 | 修正 URL 正则 | URL 案例失配 | 放弃「正则正确」的外观 |
| 19 | 修掉 LEA 死代码豁免 | 剥离判据变化，概率全变 | 放弃「代码无死逻辑」 |
| 20 | `langsize` 改用有效档案数 | 与上游向量长度语义分叉 | 放弃「两个量合一」 |
| 21 | 输出过滤用 `>=` | 边界样本多一条 | 放弃「边界包含」直觉 |
| 22 | 并列时按语言代码排序 | 与档案顺序不一致 | 放弃跨机器确定性 |
| 23 | 仅 native 单目标 | 放弃两个已 build 成功的目标 | — |
| 24 | native+wasm-gc 不含 js | 把唯一不可验证目标当主承诺 | — |
| 25 | 库内写日志文件做诊断 | 违反「不写外部状态」 | 放弃「库自带诊断」 |
| 26 | 全量移植上游 API 面 | 扩大验收面不增价值 | 放弃 100% API 兼容 |
| 27 | 连死错误码也删 | 错误码表断裂 | 放弃「零冗余枚举」 |
| 28 | 把 `is_upper` 也包成平台接缝 | 它无平台分叉，包接缝会制造假分叉点 | 放弃「形式统一」 |
| 29 | 把 `log` 分支重构成运行期开关（TB3） | 生产中永不切换，且 wasm-gc 上无法真执行 | 放弃「测试可全分支覆盖」的假象 |
| 30 | 设计文档走 PRD 校验器 | 文档类型不同，8 项失败是预期 | 放弃「一个校验器管所有文档」 |

---

**文档结束**
