# moon_langdetect 语种检测库 — 技术规格（spec）

> **文档标题（机器可检索）**：`moon_langdetect 语种检测库技术规格`
> **版本**：v5.1（2026-10-21）
> **状态**：v5.1 已销项第七轮的全部 Fail（覆盖分母 / 非等价降级显式行 / 任一失败即整体失败 / 运行时原语矩阵 / EC1 环境事实）与全部 Note（N-25…N-29）；v5 及其以前见 findings
> **需求权威**：`docs/superpowers/prds/202610202129-moon-langdetect-语种检测-prd.md`（下称「PRD」）
> **设计权威**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-design.md`（下称「DESIGN」）
> **裁决权威**：`docs/port/architecture-decisions.md`（下称「ADR」）
> **复审登记表**：`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-review-findings.md`
>
> 本文是**契约级 how**：字段 schema、接口签名、错误码、可机检断言。不含实现代码、伪代码、实现顺序、排期、工时。
>
> **约定文档（逐字引用，禁止简称）**：本文遵守 `约定 A：档案内嵌数据格式与生成契约` v1、`约定 B：U3 Unicode 大小写表生成契约` v1、`约定 C：golden 基准消费契约` v1；正文只引用其完整标题与编号（如 A1、B3、C2），不复制正文。

---

## 0. spec 复杂度判定

**判定：必写 spec（不可跳过）。**

| 维度 | 事实 | 依据 |
|---|---|---|
| 契约面规模 | PRD 共 **26** 条 FR；错误码 **9** 个；目标运行时 **3** 个；公开接缝签名表 **10** 组（§5.1–§5.10 各一行签名，派生：`grep -c '^### 5\.[0-9]'`） | PRD §5.1；本文 §5 |
| 验收语义复杂度 | 数值验收是**位级**（`prob_bits` IEEE754 hex 逐位一致），且**按目标分档**；不是「返回非空」级断言 | `约定 C：golden 基准消费契约` §4；ADR A 行 |
| 跨环节约定 | 三份独立权威约定（A/B/C）必须被逐字引用并在 spec 内承接为验收命令 | DESIGN §八；ADR AD1-AD3 |
| 行为等价面 | 上游 quirk 被写成独立 FR 的有：URL 吞词（FR-15）、LEA 死代码（FR-17）、缓存不失效（FR-19）、`langsize`（FR-20）、capitalword（FR-18）、严格阈值（FR-03）、空特征异常码（FR-12） | PRD §5.1；`docs/port/upstream-behavior-contract.md` §10 |
| 失败路径 | 三类成因（码 5 / 4 / 8）可观察契约不同，且必须带 4 字段诊断载体 | PRD §5.2 失败可诊断性行 |

> 结论：契约面与验收语义都超出「一句话可交代」的量级，跳过 spec 会使位级验收、跨目标分档、三份约定全部失去承接点。

---

## 0A. 四维一致性（D1 背景 / D2 架构 / D3 范式 / D4 解决方案）

### D1 背景

见 PRD §一（问题陈述）与 §二（目标）。本文不复述；只记录一条对契约有约束力的事实：上游是可量化参照（档案规模与命中率见 §1），因此「行为等价」可按 V-XX 事实行做机器验收，而非主观判断。

### D2 架构：模块边界与依赖方向

**产品模块根**：`F:/moonbit比赛/moon_langdetect/`（`moon.mod` 的 `name = "vicoproplus/langdetect"`；根模块与嵌套探针模块共存已实测，见 V-56）。

| 模块（目录） | 职责 | 允许依赖 | 禁止 |
|---|---|---|---|
| `src/math_seam/` | 数学接缝：`ln_for_gauss`（native = libm `log`；js / wasm-gc = `@math.ln`） | 标准库 | 依赖其他产品模块 |
| `src/unicode/` | 字符属性：`is_upper_cp312` + U3 表产物 + `unicode_block` 区块表（220 区间） | 标准库 | 依赖其他产品模块 |
| `src/data/` | 档案：内嵌扁平字符串 + 解析为「语言 → n-gram → 计数」 | 标准库 | 依赖 `src/core/` |
| `src/core/` | 清洗与特征、概率更新、公开入口、结果类型、异常类型 | `src/math_seam/`、`src/unicode/`、`src/data/` | 反向被依赖 |

**依赖方向**：`src/core/` → {`src/math_seam/`, `src/unicode/`, `src/data/`} → 标准库。单向，无环。

**业务侧零平台分支**：`src/core/` 内不得出现平台条件编译或运行期平台判断；平台差异只允许存在于 `src/math_seam/` 内部（承接 DESIGN PS1 接缝登记表与 WB1 承载面表）。可机检形态见 DR9。

**数据流**：内嵌档案字符串 →（解析）→ 计数表 →（除以 `n_words`）→ 概率表 →（特征抽取 + 7 轮随机更新 + 归一化）→ 语言概率向量 →（阈值过滤 + 排序）→ 结果条目数组。

### D3 范式（技术路线与命名约定）

| 项 | 选定范式 | 依据 |
|---|---|---|
| 依赖 | 零第三方 MoonBit 包依赖；平台 C 库（libm）不算第三方包 | ADR P 行；DESIGN MS1-3 |
| 档案承载 | 编译期内嵌扁平字符串（`key\tcount\n`），运行时不读文件 | ADR D 行；`约定 A：档案内嵌数据格式与生成契约` |
| 大小写判定 | U3 内嵌区间表（CPython 3.12.10 生成），不用第三方 Unicode 包 | ADR U 行；`约定 B：U3 Unicode 大小写表生成契约` |
| 数值路径 | `gauss` 的 `log` 走接缝（native = libm）；`sum()` 复刻 Neumaier；`langprob += prob/7` 用朴素加法 | DESIGN D3；V-33 / V-34 |
| 错误表达 | `suberror` 单一错误类型，带 4 个标签载荷字段 | 本文 §5.8；V-57 |
| 命名 | 类型 `PascalCase`；函数与字段 `snake_case`；错误变体 `PascalCase` 带标签参数 `name~` | 与 MoonBit 惯例一致；V-57 的编译通过形态 |
| 测试组织 | 每个 `src/*/` 模块内 `*_test.mbt`（白盒）+ 顶层 `*_wbtest.mbt` | 与探针工程一致（`probes/embed-probe/*_test.mbt`） |

### D4 解决方案与范围

**方案承接**：DESIGN §六 的全部设计决策（D1–D12）原样承接，本文不重述其 which/why，只在需要契约化的地方落地为签名、错误码、验收行：

| DESIGN 决策 | 本文落点 |
|---|---|
| D1 兼容档分目标 | §8.4 位级维度 + EQ1 |
| D2 档案承载 | §0A D2 模块表 + 产品落点（§4A） |
| D3 随机与浮点 | §5.5 seed、§5.9 接缝、V-33/V-34 |
| D4 Unicode 大小写 | §5.9 `is_upper_cp312` + DR4 |
| D5 公开能力面四类 | §5.1–§5.7 |
| D6 低置信独立入口 | §5.3 |
| D7 失败路径分型 | §6 |
| D8 清洗 quirk 保真 | V-40…V-48 |
| D9 过滤与排序 | §4.4 + EQ3 |
| D10 目标运行面分级 | §8.1 / §8.3 + SF-09 的分级标注 |
| D11 失败诊断四字段 | §5.8 取证通道 + §8.2 验收行 |
| D12 不移植范围 | §2 的 G-17 / G-27 / G-28 |

**范围 in**：PRD §5.1 的 FR-01…FR-26；§5 的 9 组接口；§6 的 9 个码值；三份约定。
**范围 out**：PRD §三 的全部非目标；ADR X 节的全部不移植项；任何用户可见界面（本库无）。

---

## 1. Verified facts（先于任何结论）

格式：`| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |`。**编号唯一；后续正文只引用编号，数值只在本表出现。**

### 1.1 上游公开 API 面

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-01 | 包级公开名共 10 个（5 个语义导出 + 5 个子模块属性），且**无** `__all__` | `dir(langdetect)` 中不以 `_` 开头的名字 | `.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');import langdetect;print(sorted(n for n in dir(langdetect) if not n.startswith('_')));print(hasattr(langdetect,'__all__'))"` | 10 个名字 / `False` |
| V-02 | `__init__.py` 只从两处 re-export | 源码行 | `sed -n '1,2p' langdetect/langdetect/__init__.py` | 2 行 import |
| V-03 | 模块级单例入口 `detect` / `detect_langs` 走惰性初始化 | 源码行 | `docs/port/upstream-behavior-contract.md` §1.2 | 与契约一致 |
| V-04 | `PROFILES_DIRECTORY` = 包内 `profiles` 目录 | 源码行 | `langdetect/langdetect/detector_factory.py:117` | 已核读 |
| V-05 | `DetectorFactory` 公开方法 8 个 | 源码行 | `langdetect/langdetect/detector_factory.py:31-114` | 已核读 |
| V-06 | `Language` 只有 `__init__`/`__repr__`/`__lt__`，无 `__eq__`/`__gt__` | 源码行 | `langdetect/langdetect/language.py:7-17` | 已核读 |

### 1.2 上游常量与默认值

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-07 | 常量集合共 10 项（7 个类常量 + 3 个实例默认值） | **断言域** = 输出中的这 10 个键：`ALPHA_DEFAULT` / `ALPHA_WIDTH` / `ITERATION_LIMIT` / `PROB_THRESHOLD` / `CONV_THRESHOLD` / `BASE_FREQ` / `UNKNOWN_LANG` / `DetectorFactory_seed_class_attr` / `instance_n_trial` / `instance_max_text_length`。**测量域** = 命令输出的全部 19 个键（额外 9 个为 `MAIL_RE_pattern`、`URL_RE_pattern`、`factory_seed_instance`、`init_prob_repr`、`instance_alpha`、`instance_prior_map`、`instance_random_type`、`instance_seed`、`instance_verbose`，属观测项不属常量断言） | `.venv/Scripts/python.exe tools/probe_facts.py constants`；断言域对账：`.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,'tools');import probe_facts;d=probe_facts.constants_facts();k=['ALPHA_DEFAULT','ALPHA_WIDTH','ITERATION_LIMIT','PROB_THRESHOLD','CONV_THRESHOLD','BASE_FREQ','UNKNOWN_LANG','DetectorFactory_seed_class_attr','instance_n_trial','instance_max_text_length'];assert len(k)==10 and all(x in d for x in k);print('10 keys ok; total',len(d))"` | `10 keys ok; total 19`（exit 0） |
| V-08 | `seed` 默认 `None`，且是**类属性** | `DetectorFactory.seed` | 同 V-07 | `null` |
| V-09 | `n_trial=7`、`max_text_length=10000`、`prior_map=None`、`verbose=False`、`alpha=0.5` | 实例属性 | 同 V-07 | 与 `detector.py:64-68` 一致 |

V-07 明细（10 项）：

| 常量 | 值 | 上游指针 |
|---|---|---|
| `ALPHA_DEFAULT` | `0.5` | `detector.py:44` |
| `ALPHA_WIDTH` | `0.05` | `detector.py:45` |
| `ITERATION_LIMIT` | `1000` | `detector.py:47` |
| `PROB_THRESHOLD` | `0.1` | `detector.py:48` |
| `CONV_THRESHOLD` | `0.99999` | `detector.py:49` |
| `BASE_FREQ` | `10000` | `detector.py:50` |
| `UNKNOWN_LANG` | `'unknown'` | `detector.py:51` |
| `seed`（类属性默认） | `None` | `detector_factory.py:29` |
| `n_trial`（实例默认） | `7` | `detector.py:65` |
| `max_text_length`（实例默认） | `10000` | `detector.py:66` |

### 1.3 上游错误码表

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-10 | 错误码共 9 个，码值 0–8 | `_error_codes` 字典 | `sed -n '1,11p' langdetect/langdetect/lang_detect_exception.py` | 9 项 |
| V-11 | 异常携带 `code` 与消息；`get_code()` 返回 code；**无** `.message` 属性 | 构造异常后取属性 | `.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');from langdetect.lang_detect_exception import LangDetectException,ErrorCode;e=LangDetectException(ErrorCode.CantDetectError,'No features in text.');print('has message attr',hasattr(e,'message'));print('str',str(e),'code',e.code,'get_code',e.get_code())"` | `has message attr False` / `str No features in text. code 5 get_code 5` |
| V-12 | 三类失败的消息原文 | 实测构造 | `.venv/Scripts/python.exe tools/probe_facts.py empty_variants`；`docs/port/upstream-behavior-contract.md` §9 | 码 5 / 码 4 / 码 8 各原文 |
| V-13 | 码 0 / 6 / 7 在包内**无抛出点** | 全仓检索 | `grep -rn "NoTextError\|CantOpenTrainData\|TrainDataFormatError" langdetect/langdetect --include=*.py \| grep -v tests` | 仅 3 处定义 |

### 1.4 档案数据

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-14 | 档案文件 55 个、总字节 2204952、freq 条目 184129 | 55 个无扩展名 JSON | `.venv/Scripts/python.exe tools/profile_stats.py` | `files=55` / `total_bytes=2204952` / `total_entries=184129` |
| V-15 | 键长分布仅 1/2/3 码点，计数 7791 / 52387 / 123951 | 同上 `len_dist` | 同上 | `{1: 7791, 2: 52387, 3: 123951}` |
| V-16 | 非 BMP 条目 0 条 | 同上 `non_bmp_total` | 同上 | `0` |
| V-17 | 最大档案 `ko` 23031 条 / 307193 字节；最小条目 `gu` 1474 条；最小字节 `so` 16786 | 同上 | 同上 | 四项均一致 |
| V-18 | 档案 JSON 键集合恒为 `{freq, n_words, name}`，`n_words` 长度恒 3 | `probe_facts.py profile_fields` | `.venv/Scripts/python.exe tools/probe_facts.py profile_fields` | `key_sets=[[freq,n_words,name]]`、`n_words_lengths=[3]` |

### 1.5 golden 基准规模

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-19 | 案例 268 条 = 有概率输出 250 + 抛异常 18 | `expected.json.cases` | `.venv/Scripts/python.exe -c "import json;c=json.load(open('docs/port/golden/expected.json',encoding='utf-8'))['cases'];print(len(c),sum(1 for x in c if x.get('detect_langs')),sum(1 for x in c if 'error' in x))"` | `268 250 18` |
| V-20 | seed 仅取 0 与 42 两套 | 同上 `seed` 字段 | 同上 | `{0, 42}` |
| V-21 | 每条有概率输出的条目带 `prob_bits`（16 位小写十六进制） | 正则全匹配 | `约定 C：golden 基准消费契约` §3 C-C1 | 全部匹配 |
| V-22 | 基准文件 md5 | 整文件 | `md5sum docs/port/golden/expected.json` | `219519ee19d7cc10d404ddbdab3acd87` |
| V-23 | 长文本命中 55/55、短文本命中 51/55（seed=0） | `summary.json` | `.venv/Scripts/python.exe -c "import json;d=json.load(open('docs/port/golden/summary.json',encoding='utf-8'));print(d['detect_accuracy_long_seed0'],d['detect_accuracy_short_seed0'])"` | 55/55 与 51/55 |

### 1.6 工具链三目标

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-24 | native build 0 / test 0 / 56 条断言通过 | `moon test --target native` | `analysis/toolchain-probes.md` §C.1；`probes/logs/target-native-02-test.log` | 通过（56/56） |
| V-25 | js build 0 / test 0，但**依赖 bun 替代运行时**；默认 PATH 下失败 | 同上 | `analysis/toolchain-probes.md` §C.2；`probes/logs/target-js-02-test-noshim.log` | 通过（替代运行时）/ 默认 PATH 失败 |
| V-26 | wasm-gc build 0 / test **失败**；空工程同样失败，`moonrun.exe` 自身无法启动 | 同上 | `analysis/toolchain-probes.md` §C.2；`probes/logs/moonrun-help.log` | build 通过 / test `0xC0000139` |

### 1.7 内嵌 flat 实测

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-27 | 扁平编码产物：生成 2205308 B、冷编译 2.814–2.830 s、exe 3256320 B、`total: 184129` | 55 语言 flat | `analysis/toolchain-probes.md` §B.3；`probes/logs/s55-flat-04-run.log` | 全部达到 |
| V-28 | Map 字面量同规模栈溢出（`0xC00000FD`），exe 19826688 B | 55 语言 map | `analysis/toolchain-probes.md` §B.3；`probes/logs/s55-map-03-test.log` | 失败 |
| V-29 | flat/map 比值：字节 0.6309、编译秒 0.1874、exe 0.1642 | `analysis/probe-tables.md` 末表 | 同左 | 三项比值 |
| V-30 | 产物声明数 55、条目数 184129 | 正则计数 | `约定 A：档案内嵌数据格式与生成契约` §3 C-A1/C-A2 | `decls 55 entries 184129` |

### 1.8 RNG 与浮点

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-31 | RNG 全链路：68 阶段中 59 全一致、21451 对值 21206 一致，9 个不一致**全部**是 `@math.ln` 对照组 | `rand_probe_compare.py` | `docs/port/rand-feasibility.md` 汇总段 | 21206/21451 |
| V-32 | `gauss(0,1)` 用 libm `log` 时 512/512 × 4 seed 一致；混合序列 7/7 gauss + 357/357 choice | 同上 | `docs/port/rand-feasibility.md` §2 | 全部一致 |
| V-33 | `sum(prob)` 必须 Neumaier：307 组中仅 69 组与朴素循环一致，307/307 与 Neumaier 一致 | `float_probe_compare.py` | `docs/port/float-add-conclusion.md` | 69/307 与 307/307 |
| V-34 | `langprob[j] += prob[j]/7` 不是补偿求和：朴素 `+` 385/385 一致 | 同上 | `docs/port/float-add-conclusion.md` 关键事实 3 | 385/385 |
| V-35 | `@math.ln` 与 libm `log` 在 2000 点中 66 点差 1 ulp（1934/2000） | 广域扫描 | `docs/port/rand-feasibility.md` §3.1 | 1934/2000 |

### 1.9 U3 大小写表

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-36 | CPython 3.12.10 的 `isupper` 为真的码点 1951 个（跳过 2048 surrogate，可比 1112064） | 全码点扫描 | `约定 B：U3 Unicode 大小写表生成契约` §3 C-B1/C-B3 | `1951` |
| V-37 | 压缩为区间表后 651 个区间 | 同上 | `约定 B` §3 C-B4 | `651` |
| V-38 | `@ucd.is_uppercase` 与 CPython 有 75 点不一致（Python=0 / MoonBit=1，类别全 `Cn`），成因 Unicode 15.0.0 vs 18.0.0 | 全码点对拍 | `docs/port/c1-residual-risks.md` §1.2-§1.3 | 75 点 |
| V-39 | 该 75 点与本仓库语料交集为 0 | 集合交集 | `docs/port/c1-residual-risks.md` §1.6 | 交集 0 |

### 1.10 清洗与错误路径行为

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-40 | URL 清洗：`see http://a.com/x then TEXT-more` → `see then TEXT-more`；`hello https://example.com/abc` → `hello ` | `append` 后 `text` | `.venv/Scripts/python.exe tools/probe_facts.py append_cleanup` | 一致 |
| V-41 | 邮箱清洗：`mail me at john.doe@example.com please` → `mail me at please` | 同上 | 同上 | 一致 |
| V-42 | 连续 U+0020 折叠、`\t` 保留：`a  b\t\tc` → `a b\t\tc` | 同上 | 同上 | 一致 |
| V-43 | 长度上限截断在清洗之后：上限 5 + `abcdefghij` → `abcde`；上限 3 + `aaabbb` → `aaa` | 同上 | 同上 | 一致 |
| V-44 | 空串 / 纯空白 / 纯 emoji / 纯数字 / 纯标点 / 纯 URL 全部抛码 5 | 6 类输入 | `.venv/Scripts/python.exe tools/probe_facts.py empty_variants`；`docs/port/golden/summary.json` 的 `error_cases` | 全部码 5 |
| V-45 | `cleaning_text` 的 LEA 豁免永不生效（`unicode_block` 返回 int，与字符串比较恒 False） | 类型与比较 | `docs/port/upstream-behavior-contract.md` §3.2 | 恒不生效 |
| V-46 | capitalword：`USA NASA FBI` 只产生 10 个特征 | 特征序列 | `docs/port/upstream-behavior-contract.md` §10 quirk 7 | 10 项 |
| V-47 | `langprob` 缓存不随 `append` 失效 | 同实例二次检测 | `docs/port/upstream-behavior-contract.md` §10 quirk 4 | 返回旧结果 |
| V-48 | `langsize` = 档案目录条目数（含点文件/子目录）；2 档案可得向量长 4 | 临时目录构造 | `docs/port/upstream-behavior-contract.md` §10 quirk 5 | 长度 4 |

### 1.11 边界与语义分叉的实测样本（v2 新增）

| 编号 | 断言 | 可机检域定义 | 命令 | 结果 |
|---|---|---|---|---|
| V-49 | 250 条有概率输出的基准中**最小条目概率**为 0.1428316217995734（`short-ca` 的 `ro`），无任何条目 ≤ 0.1 | 全部条目 `prob` 排序取最小 | `.venv/Scripts/python.exe -c "import json;c=json.load(open('docs/port/golden/expected.json',encoding='utf-8'))['cases'];v=sorted((e['prob'],x['id'],e['lang']) for x in c for e in (x.get('detect_langs') or []));print(v[0]);print('le_0.1',sum(1 for z in v if z[0]<=0.1000001))"` | 最小条目为该值；`le_0.1 0` |
| V-50 | **等概率并列可构造**：2 档案（`freq={q:3,r:1}`、`n_words=[4,0,0]`）+ 文本 `q r` → 两条目概率同为 `0.4999999999999999`，顺序 = 档案加载序 | 临时目录 + 公开 API | `.venv/Scripts/python.exe -c "import sys,tempfile,json,os;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');from langdetect.detector_factory import DetectorFactory;d=tempfile.mkdtemp();[json.dump({'freq':{'q':3,'r':1},'n_words':[4,0,0],'name':n},open(os.path.join(d,n),'w')) for n in ('x1','x2')];g=DetectorFactory();g.load_profile(d);t=g.create();t.append('q r');print([(l.lang,repr(l.prob)) for l in t.get_probabilities()])"` | `[('x1','0.4999999999999999'),('x2','0.4999999999999999')]` |
| V-51 | **NaN 先验使 `detect` 返回 `'unknown'`**：`set_prior_map({'en': nan})` 后先验全为 NaN、总和为 NaN；对合法文本检测得到空概率列表，`detect` 返回 `'unknown'` | 公开 API | `.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');from langdetect.detector_factory import DetectorFactory,PROFILES_DIRECTORY as P;f=DetectorFactory();f.load_profile(P);d=f.create();d.set_prior_map({'en':float('nan')});print('prior',d.prior_map[:2]);d.append('the weather is nice today and the sun is shining brightly');p=d.get_probabilities();print('probs',len(p),'detect',d.detect())"` | `prior [nan, nan]` / `probs 0 detect unknown` |
| V-52 | **引用别名**：实例与工厂共享同一容器（`langlist`、`word_lang_prob_map` 是同一对象） | 身份比较 | `.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');from langdetect.detector_factory import DetectorFactory,PROFILES_DIRECTORY as P;f=DetectorFactory();f.load_profile(P);d=f.create();print(d.langlist is f.langlist, d.word_lang_prob_map is f.word_lang_prob_map)"` | `True True` |
| V-53 | **`langsize` 只体现在词向量行长**：2 档案 + 1 点文件 + 1 子目录 → 可用语言 2、词向量行长 4、实例概率向量长 2 | 临时目录 + 公开 API | `.venv/Scripts/python.exe -c "import sys,tempfile,json,os;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');from langdetect.detector_factory import DetectorFactory;d=tempfile.mkdtemp();open(os.path.join(d,'.h'),'w').write('x');os.mkdir(os.path.join(d,'sub'));[json.dump({'freq':{'a':1},'n_words':[1,0,0],'name':n},open(os.path.join(d,n),'w')) for n in ('aa','bb')];g=DetectorFactory();g.load_profile(d);x=g.create();x.append('a');x.get_probabilities();print('langlist',g.langlist,'word_row',len(g.word_lang_prob_map['a']),'langprob',len(x.langprob))"` | `langlist ['aa','bb'] word_row 4 langprob 2` |
| V-54 | `cleaning_text` **幂等**；`append` **累加**（不幂等） | 公开 API | `.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');from langdetect.detector_factory import DetectorFactory,PROFILES_DIRECTORY as P;f=DetectorFactory();f.load_profile(P);a=f.create();a.append('日本語のテキストです hello');a.cleaning_text();x=a.text;a.cleaning_text();print('idempotent',x==a.text);b=f.create();b.append('hello');b.append('hello');print('append',b.text)"` | `idempotent True` / `append hellohello` |
| V-55 | **旧签名在真实编译器下不成立**（4 处）：`struct` 作 raise 类型 → `[4118]`（并伴随 `[4127]`）；未命名参数带默认值 → `[3010]`；`enum` 用 `{}` 载荷 → `[3002]`；单行 struct 字段用 `,` 分隔 → `[3800]` | `moon check` 于临时工程 | `moon 0.1.20261012` / `moonc v0.10.15+943464bfa`；构造样本见 §5.8 注 | 全部报错，见 §5.8 证据列 |
| V-56 | **根模块与嵌套探针模块共存无冲突**：在仓库根建 `moon.mod`（`name = "vicoproplus/langdetect"`）后 `moon check` 退出码 0，且不把 `probes/*` 当作本模块包 | 根目录 `moon check` | `cd F:/moonbit比赛/moon_langdetect && C:/Users/Administrator/.moon/bin/moon.exe check`（2026-10-21） | `Finished. moon: no work to do`（exit 0） |
| V-57 | **修正后的签名在真实编译器下通过**：`suberror` + 标签载荷、`alpha? : Double`、`enum` 括号载荷、多行 struct 字段 | `moon check` 于临时工程 | 构造样本：`suberror LangDetectError { CantDetect(code~ : Int, message~ : String, input_len~ : Int, input_prefix~ : String) }` + `enum Confidence { LowConfidence(char_count~ : Int); Detected(lang~ : String, probs~ : Array[LangProb]) }` + `fn create(alpha? : Double)` | `Finished. moon: ran 1 task, now up to date`（0 errors） |
| V-58 | **§5.5–§5.7 的方法签名（含 `self`）在真实编译器下通过**：`Det::set_seed(self : Det, seed : Int64?)` / `Det::set_max_text_length(self : Det, n : Int)` / `Fac::create(self : Fac, alpha? : Double)` + 调用形态 `f.create()`、`f.create(alpha=0.5)`、`g.set_seed(Some(0L))`、`g.set_max_text_length(50)`。**反例**：缺 `self` 时同样调用报 `[4014]` + `[4080] … requires 1 arguments, but is given 2 arguments`；可选参数传 `Some(0.5)` 报 `[4080] requires 1 positional arguments, but is given 2 positional arguments`（必须传裸值） | `moon 0.1.20261012` / `moonc v0.10.15`；临时工程 `moon check`（多行 struct 字段；调用形态同写） | `Finished. moon: ran 2 tasks, now up to date`（0 errors）；反例错误码同栏记录 |

### 1.12 编号使用纪律

> 本文后续所有数值主张以 `V-XX` 引用；正文不重复书写表内已给出的具体数字。若某处必须出现数字（如错误码 5），其权威仍是 §6 的码表行。

---

## 2. Gap 表（源侧 vs 目标侧）

**枚举命令（可重跑，全部显式多模式，不依赖 shell 转义）**

```bash
# Python 侧公开面
.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,r'F:\moonbit比赛\moon_langdetect\langdetect');import langdetect;print(sorted(n for n in langdetect.__dict__ if not n.startswith('_')))"
# Python 侧方法面
grep -n "    def " langdetect/langdetect/detector_factory.py langdetect/langdetect/detector.py langdetect/langdetect/language.py
# MoonBit 侧产品公开面（v2：产品目录 = src/）
grep -rn '^pub fn\|^pub struct\|^pub enum\|^pub suberror' --include=*.mbt src
# MoonBit 侧全仓（排除探针与构建产物）
grep -rn '^pub fn\|^pub struct\|^pub enum\|^pub suberror' --include=*.mbt . | grep -v -e _build -e .mooncakes -e probes
```

实测（2026-10-21）：前两条见 §1；第三条对 `src/` 输出 **0 行**（产品实现未落地）；第四条同样 **0 行**（`grep -v -e _build -e .mooncakes -e probes` 为显式多模式，避免转义依赖）。

| # | Item | Source side (file:line) | Target side status | Label |
|---|---|---|---|---|
| G-01 | 包级入口 `detect(text) -> str` | `langdetect/langdetect/detector_factory.py:126-130` | missing | `[ALIGN]` |
| G-02 | 包级入口 `detect_langs(text) -> list[Language]` | `langdetect/langdetect/detector_factory.py:133-137` | missing | `[ALIGN]` |
| G-03 | 惰性单例 `init_factory()` + 模块级 `_factory` | `langdetect/langdetect/detector_factory.py:118-124` | missing | `[ALIGN]` |
| G-04 | `DetectorFactory.load_profile(dir)` | `langdetect/langdetect/detector_factory.py:35-64` | missing | `[ALIGN]` |
| G-05 | `DetectorFactory.add_profile(profile, index, langsize)` | `langdetect/langdetect/detector_factory.py:80-92` | missing | `[ALIGN]` |
| G-06 | `DetectorFactory.create(alpha=None)` | `langdetect/langdetect/detector_factory.py:98-103` | missing | `[ALIGN]` |
| G-07 | `DetectorFactory.set_seed(seed)` | `langdetect/langdetect/detector_factory.py:110-111` | missing | `[ALIGN]` |
| G-08 | `DetectorFactory.get_lang_list()` | `langdetect/langdetect/detector_factory.py:113-114` | missing | `[ALIGN]` |
| G-09 | `DetectorFactory.clear()` | `langdetect/langdetect/detector_factory.py:94-96` | missing | `[ALIGN]` |
| G-10 | `Detector.append(text)` | `langdetect/langdetect/detector.py:99-112` | missing | `[ALIGN]` |
| G-11 | `Detector.cleaning_text()` | `langdetect/langdetect/detector.py:114-130` | missing | `[ALIGN]` |
| G-12 | `Detector.detect()` | `langdetect/langdetect/detector.py:132-139` | missing | `[ALIGN]` |
| G-13 | `Detector.get_probabilities()` | `langdetect/langdetect/detector.py:141-144` | missing | `[ALIGN]` |
| G-14 | `Detector.set_alpha(alpha)` | `langdetect/langdetect/detector.py:73-74` | missing | `[ALIGN]` |
| G-15 | `Detector.set_max_text_length(n)` | `langdetect/langdetect/detector.py:93-97` | missing | `[ALIGN]` |
| G-16 | `Detector.set_prior_map(dict)` | `langdetect/langdetect/detector.py:76-91` | missing | `[ALIGN]` |
| G-17 | `Detector.set_verbose()` | `langdetect/langdetect/detector.py:70-71` | missing（ADR X 裁决不移植） | `[ALIGN]`（显式不移植） |
| G-18 | `Language{lang, prob}` + `__repr__` + `__lt__` | `langdetect/langdetect/language.py:7-17` | missing | `[ALIGN]` |
| G-19 | `LangDetectException{code, message}` + `get_code()` | `langdetect/langdetect/lang_detect_exception.py:16-22` | missing | `[ALIGN]` |
| G-20 | `ErrorCode` 9 个码值 | `langdetect/langdetect/lang_detect_exception.py:1-11` | missing | `[ALIGN]` |
| G-21 | 常量 10 项（V-07 断言域） | `detector.py:44-51`、`detector_factory.py:29`、`detector.py:65-66` | missing | `[ALIGN]` |
| G-22 | `NGram.normalize` 全表（**12 个块常量 / 11 个判定臂**——Bopomofo 与 Bopomofo Extended 同臂） | `langdetect/langdetect/utils/ngram.py:64-97` | missing | `[ALIGN]` |
| G-23 | `NGram.normalize_vi` | `langdetect/langdetect/utils/ngram.py:99-120` | missing | `[ALIGN]` |
| G-24 | `CJK_MAP`（126 组 / 6667 键） | `langdetect/langdetect/utils/ngram.py:122-260` | missing | `[ALIGN]` |
| G-25 | `unicode_block(ch)` + 220 条区间表 | `langdetect/langdetect/utils/unicode_block.py:223-465` | missing | `[ALIGN]` |
| G-26 | 档案数据 55 个（V-14） | `langdetect/langdetect/profiles/` | missing | `[ALIGN]` |
| G-27 | `LangProfile.add/omit_less_freq/update`（训练期） | `langdetect/langdetect/utils/lang_profile.py:28-70` | missing（ADR X 裁决不移植） | `[ALIGN]`（显式不移植） |
| G-28 | `load_json_profile(list[str])` | `langdetect/langdetect/detector_factory.py:66-78` | missing（ADR X 裁决不移植） | `[ALIGN]`（显式不移植） |
| G-29 | 低置信入口（短文本显式标记） | 上游无对应物 | missing | `[EXT]` — 非对齐项，产品决策驱动（PRD FR-21/22/23；DESIGN D6） |
| G-30 | 异常诊断四字段（`code` / `message` / `input_len` / `input_prefix`） | 上游仅有 `code` + 消息（`lang_detect_exception.py:16-22`；无 `.message` 属性，V-11） | missing | `[EXT]` — 非对齐项，产品决策驱动（PRD §5.2；DESIGN D11） |
| G-31 | `is_upper_cp312(cp)` 判定入口 | 上游用 CPython `str.isupper`（无独立 API） | missing | `[EXT]` — 非对齐项，产品决策驱动（ADR U 行；DESIGN D4） |
| G-32 | 固定 seed 位级比对设施 | 上游无（属测试设施） | missing | `[EXT]` — 非对齐项，产品决策驱动（验收设施形态由 `约定 C：golden 基准消费契约` 决定） |
| G-33 | `debug_vector_len()` 诊断入口（暴露 `langsize`，使 FR-20 可观察） | 上游无公开入口（V-53：`langsize` 只在词向量行长可见） | missing | `[EXT]` — 非对齐项，产品决策驱动（FR-20 可观察性；见 §5.10） |

**统计（由本表行数派生）**：`[ALIGN]` 28 行（G-01…G-28），`[EXT]` 5 行（G-29…G-33）。

### 2A. 源侧测试对齐

| 源侧测试文件 | 用例数 | 目标侧测试文件（计划） | 状态 |
|---|---|---|---|
| `langdetect/langdetect/tests/test_detector.py` | 6 | `src/core/detector_test.mbt` | 未落地（`[ALIGN]`，对应 G-01/G-02/G-04/G-05/G-08/G-12） |
| `langdetect/langdetect/tests/test_language.py` | 2 | `src/core/language_test.mbt` | 未落地（`[ALIGN]`，对应 G-18） |
| `langdetect/langdetect/tests/utils/test_lang_profile.py` | 7 | **无** | **gap 登记**：7 个用例全部覆盖训练期 `add`/`omit_less_freq`（对应 G-27，ADR X 裁决不移植），故不设目标侧对应；`LangProfile` 的字段解析行为改由 `约定 A：档案内嵌数据格式与生成契约` 的 A1/A2 与 `src/data/` 的解析测试覆盖 |
| `langdetect/langdetect/tests/utils/test_ngram.py` | 7 | `src/core/ngram_test.mbt` | 未落地（`[ALIGN]`，对应 G-22/G-23/G-24） |
| `langdetect/langdetect/tests/utils/test_unicode_block.py` | 1 | `src/unicode/block_test.mbt` | 未落地（`[ALIGN]`，对应 G-25） |

用例数由 `grep -c "def test_" <file>` 派生（2026-10-21 实测：6 / 2 / 7 / 7 / 1）。

---

## 3. PRD 回链表

| PRD 编号 | 类型 | spec 承接位置 | 验收行（§8） | 状态 |
|---|---|---|---|---|
| US-01 | 用户故事 | §5.1 | §8.2 主检测与概率形态 | 已承接 |
| US-02 | 用户故事 | §4.4 + §5.2 | §8.2 主检测与概率形态 | 已承接 |
| US-03 | 用户故事 | §5.5 + §9.3 | §8.2 seed 语义；§8.4 位级 | 已承接 |
| US-04 | 用户故事 | §5.3 | §8.2 低置信入口 | 已承接 |
| US-05 | 用户故事 | §5.8 + §6 | §8.2 参数与失败路径 + 取证通道 | 已承接 |
| US-06 | 用户故事 | §4.1 + §5.4 | §8.2 内嵌档案 | 已承接 |
| US-07 | 用户故事 | §5.6 + §5.7 | §8.2 参数与失败路径 | 已承接 |
| FR-01 | 功能需求 | §5.1 | §8.2 主检测与概率形态 | 已承接 |
| FR-02 | 功能需求 | §5.2 + §4.4 | §8.2 主检测与概率形态 | 已承接 |
| FR-03 | 功能需求 | §5.2 + §4.4 + EQ3 | §8.2 主检测与概率形态 | 已承接 |
| FR-04 | 功能需求 | §4.4 + EQ2/EQ3 | §8.2 主检测与概率形态 | 已承接 |
| FR-05 | 功能需求 | §5.5 | §8.2 seed 语义 | 已承接 |
| FR-06 | 功能需求 | §5.5 | §8.2 seed 语义 | 已承接 |
| FR-07 | 功能需求 | §5.6 | §8.2 参数与失败路径 | 已承接 |
| FR-08 | 功能需求 | §6 码 8 | §8.2 参数与失败路径 | 已承接 |
| FR-09 | 功能需求 | §6 码 8 | §8.2 参数与失败路径 | 已承接 |
| FR-10 | 功能需求 | §5.7 | §8.2 参数与失败路径 | 已承接 |
| FR-11 | 功能需求 | §6 码 4 | §8.2 参数与失败路径 | 已承接 |
| FR-12 | 功能需求 | §6 码 5 | §8.2 参数与失败路径 + 取证通道 | 已承接 |
| FR-13 | 功能需求 | §5.4 | §8.2 内嵌档案 | 已承接 |
| FR-14 | 功能需求 | §9.1 L1-A1 + NE4-2 | §8.2 内嵌档案 | 已承接 |
| FR-15 | 功能需求 | V-40 + §8.2 清洗契约 | §8.2 清洗契约 | 已承接 |
| FR-16 | 功能需求 | V-41 + §8.2 清洗契约 | §8.2 清洗契约 | 已承接 |
| FR-17 | 功能需求 | V-45 + §8.2 清洗契约 | §8.2 清洗契约 | 已承接 |
| FR-18 | 功能需求 | V-46 + §8.2 大写词与缓存 + DR4 | §8.2 大写词与缓存 | 已承接 |
| FR-19 | 功能需求 | V-47 + §9.3 | §8.2 大写词与缓存 | 已承接 |
| FR-20 | 功能需求 | V-53 + §5.10 | §8.2 大写词与缓存 | 已承接 |
| FR-21 | 功能需求 | §5.3 | §8.2 低置信入口 | 已承接 |
| FR-22 | 功能需求 | §5.3 | §8.2 低置信入口 | 已承接 |
| FR-23 | 功能需求 | §5.3 + §8.2（268 条口径） | §8.2 低置信入口 | 已承接 |
| FR-24 | 功能需求 | §9.4 NE4-1 | §8.2 内嵌档案 | 已承接 |
| FR-25 | 功能需求 | `约定 A` A2 + §4.1 | §8.2 内嵌档案 | 已承接 |
| FR-26 | 功能需求 | §4.2 | §8.2 内嵌档案 | 已承接 |

**覆盖核对（派生，不手写）**：

```bash
# 本表 FR 行数
grep -cE '^\| FR-[0-9]+ ' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
# 其中「验收行（§8）」列非空的行数（应为全部）
grep -E '^\| FR-[0-9]+ ' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -c '§8\.'
# PRD 侧优先级分布（分母来源）
awk -F'|' '/^\| FR-[0-9]+ \|/{gsub(/ /,"",$5); print $5}' docs/superpowers/prds/202610202129-moon-langdetect-语种检测-prd.md | sort | uniq -c
```

结论：本表覆盖 PRD 的**全部** FR 条目（含 P2），**无延期项、无 TBD**；不存在「只覆盖 P0/P1」的裁剪。

---

## 4. 数据模型（schema 级）

### 4.1 档案记录（内嵌数据）

| 字段 | 类型 | NULL 性 | 双锁（标量/容器） | 约束 | 权威源 |
|---|---|---|---|---|---|
| `name` | `String` | 非空 | `String` = UTF-8 码点序列；不可为空串 | 取值域 = 55 个语言代码集合（V-14）；唯一 | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §8.1 的 `name`；口径逐字：字段名 `name`，必填，值为语言代码字符串） |
| `n_words` | `Array[Int]` | 非空 | 长度固定 3；元素为 `Int`（非负） | 索引 0/1/2 对应 1/2/3-gram 总次数；`n_words[i] > 0`（除零会抛错，见 §6 码 1） | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §8.1 的 `n_words`；口径逐字：字段名 `n_words`，长度恒为 3，值为整数） |
| `freq` | `Map[String, Int]` | 非空（可为空表） | 键 `String` 长度仅 1/2/3；值 `Int` 非负 | 键长分布见 V-15；无非 BMP 键（V-16） | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §8.1 的 `freq`；口径逐字：字段名 `freq`，值为 n-gram 到出现次数的映射） |

**DT1（NULL 性锁）**：三字段均非空；`freq` 可为空表（`size == 0`）但不得为 `None`。
**DT2（标量类型锁）**：`name` 为字符串；`n_words` 元素与 `freq` 值为整数；不得用浮点承载计数。
**DT3（容器形态锁）**：`n_words` 必须是长度 3 的定长数组（非列表/映射）；`freq` 必须是字符串到整数的映射。

### 4.2 加载后的概率表

| 字段 | 类型 | NULL 性 | 约束 | 权威源 |
|---|---|---|---|---|
| `word_lang_prob[word][lang_index]` | `Double` | 非空（缺省 0.0） | 等于该 n-gram 在该语言的频率除以该语言同长度 n-gram 总次数；`len(word)` 仅 1/2/3 | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §1.3.2 公式；口径逐字：`prob(word, lang) = freq_lang[word] / n_words_lang[len(word) - 1]`） |

- 键集合大小 = 去重后 n-gram 数（V-14 的条目总数是各档案条目之和，去重后更小）。
- 未出现的语言在该词向量中保持 `0.0`。
- 键长 > 3 的条目**不**写入概率（`detector_factory.py:90` 的条件），但仍会建零向量（同文件 87-88）。

### 4.3 结果条目（结构体 `LangProb`）

| 字段 | 类型 | NULL 性 | 约束 | 权威源 |
|---|---|---|---|---|
| `LangProb.lang` | `String?` | **可空**（仅构造空对象时） | 非空时取值域 = 可用语言集合 | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §1.4 的 `lang`；口径逐字：字段名为 `lang`，类型为字符串或空值） |
| `LangProb.prob` | `Double` | 非空 | 出现在返回列表中时**严格大于** `PROB_THRESHOLD` | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §1.4 的 `prob` 与排序口径；口径逐字：字段名为 `prob`，类型为浮点数，条目按概率降序、仅保留严格大于 0.1 者） |

> 结构体名 `LangProb` 由本节定义；§5.2 / §5.3 引用同一名字（v2 修正：v1 只有字段表无类型名）。

### 4.4 排序与过滤契约（自然语言，非代码）

- **过滤**：先按「概率严格大于阈值」保留条目；等于阈值或小于阈值的条目一律丢弃。
- **排序**：保留的条目按概率从大到小排列；概率相等时，保持它们在可用语言列表中的先后次序（即档案加载序）。
- **比较语义（EQ3）**：比较与排序按 IEEE754 双精度**数值**比较；非数值（NaN）不参与过滤与排序——NaN 与任何值比较均为假，故 NaN 概率的条目不会被「严格大于阈值」保留，也不会进入排序结果。
- **零值语义（EQ3）**：负零与正零在数值比较上相等；负零不满足「严格大于正阈值」，故同样被过滤。
- **权威源**：本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §1.4 的 `_sort_probability` 口径；口径逐字：先用 `p > PROB_THRESHOLD` 过滤，再对结果做降序稳定排序）。

### 4.5 语言列表与向量长度（两个不同的量）

| 量 | 定义 | 约束 | 可观察性 | 权威源 |
|---|---|---|---|---|
| 可用语言列表 | 有效档案的 `name` 序列 | 长度 = 有效档案数；顺序 = 档案加载序 | `get_lang_list()`（§5.4） | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §1.3.1；口径逐字：`get_lang_list()` 返回 `list(self.langlist)` 的浅拷贝，顺序由目录列举顺序决定） |
| 概率向量长度 | 每语言概率向量的元素个数 | 由**档案目录条目数**决定，可**大于**可用语言数（V-48、V-53） | 仅经诊断入口 `debug_vector_len()`（§5.10，`[EXT]`） | 本表为摘要（权威＝`docs/port/upstream-behavior-contract.md` §1.3.1 的 `langsize = len(list_files)`；口径逐字：`langsize, index = len(list_files), 0`） |

> 两者不得互相替代：向量长度不得被用作「可用语言数」的判据（PRD §5.3 交互矩阵末行）。V-53 说明该值在公开面**不可直接观察**，故 §5.10 提供诊断入口（`[EXT]`，G-33）。

---

## 4A. 产品工程落点（GP1：每条命令引用的路径在此定义）

**裁决**：模块根 = 仓库根 `F:/moonbit比赛/moon_langdetect/`（**优先方案**，已实测与嵌套探针模块共存无冲突：V-56）。**未采用**的备选是子目录 `moon_langdetect/` 作为模块根——仅在根模块冲突时启用；当前无冲突，故不启用。

| 路径（逐字） | 角色 | 生成时点 | 责任单元 | 生成命令 | 校验命令 |
|---|---|---|---|---|---|
| `moon.mod` | 模块声明（`name = "vicoproplus/langdetect"`、`version = "0.1.0"`） | 一次性，手工 | 产品 | — | ① 字面校验：`grep -q '^name = "vicoproplus/langdetect"$' moon.mod`；② 语法/包图校验：`C:/Users/Administrator/.moon/bin/moon.exe check`（**只证明模块存在 + 包图可解，不校验 name 字面**；改 `name="x/y"` 后 rc 仍 0 已实测） |
| `src/core/` | 清洗与特征、概率更新、公开入口、结果与异常类型 | 实现期 | 产品 | — | `moon check` |
| `src/data/` | 档案解析与查询 | 实现期 | 产品 | — | `moon check` |
| `src/unicode/` | `is_upper_cp312` + 区块表 | 实现期 | 产品 | — | `moon check` |
| `src/math_seam/` | `ln_for_gauss`（唯一平台分叉点） | 实现期 | 产品 | — | `moon check` |
| `src/data/profiles.mbt` | **档案数据产物**（扁平字符串，55 声明） | 构建前 | 产品 | `python tools/gen_profile_data.py` | `约定 A：档案内嵌数据格式与生成契约` §3 全部命令 |
| `src/unicode/upper_table.mbt` | **U3 表产物**（651 区间 + 版本表头） | 构建前 | 产品 | `python tools/gen_upper_table.py` | `约定 B：U3 Unicode 大小写表生成契约` §3 全部命令 |
| `tools/gen_profile_data.py` | 档案生成器（只产 flat） | 实现期 | 产品 | — | `约定 A` C-A5（生成清单 mode） |
| `tools/gen_upper_table.py` | U3 表生成器（读 `.venv` 的 CPython） | 实现期 | 产品 | — | `约定 B` C-B1/B2 |
| `tools/gen_core_tables.py` | ngram 表生成器（从上游 `ngram.py` 转写） | 实现期 | 产品 | — | `python tools/gen_core_tables.py --verify`（12/11/126/6667） |
| `src/core/ngram_tables.mbt` | **ngram 表产物**（12 块 / 11 臂 / 126 组 / 6667 键；首行「勿手改」） | 构建前 | 产品 | `python tools/gen_core_tables.py` | `--verify` 四元组 + 首行「勿手改」；覆盖行为 = 整文件重建 |
| `src/core/cmd/main/moon.pkg` | 静默性验证用可执行包的清单（须含 `pkgtype(kind: "executable")`） | 实现期 | 产品 | —（随包一次写入） | `grep -q 'pkgtype(kind: "executable")' src/core/cmd/main/moon.pkg` |
| `src/core/cmd/main/main.mbt` | 可执行入口。**当前内容为空 `fn main { }`（脚手架占位，仅验证可执行包形态）；「调用一次 `detect` 且不打印」是实现期目标，尚未实现** | 实现期 | 产品 | — | `C:/Users/Administrator/.moon/bin/moon.exe build --target native` 后检查 `_build/native/debug/build/src/core/cmd/main/main.exe` 存在 |
| `src/core/cmd/golden/moon.pkg` | golden 比对诊断可执行包的清单（不属公开 API；NE1 静态门仅豁免 `cmd/main/`） | 实现期 | 产品 | — | 命令 11b 对库/cmd/main 零命中（cmd/golden 诊断输出例外，2026-10-22 用户裁决）+ `compare_golden --mode prob_bits` |
| `src/core/cmd/golden/main.mbt` | golden 比对诊断入口（读一行 JSON、写一行 JSON；`main` 仍静默） | 实现期 | 产品 | — | 命令 11b 对库/cmd/main 零命中（cmd/golden 诊断输出例外，2026-10-22 用户裁决）+ `compare_golden --mode prob_bits` |
| `_build/native/debug/build/src/core/cmd/main/main.exe` | 静默性验证用可执行产物 | 构建期 | 产品 | `C:/Users/Administrator/.moon/bin/moon.exe build --target native` | `./_build/native/debug/build/src/core/cmd/main/main.exe > /tmp/o.txt 2> /tmp/e.txt; wc -c /tmp/o.txt /tmp/e.txt` 两者均 0（NE1 运行时半句的载体） |
| `tools/compare_golden.py` | `约定 C` 的位级比对器（消费 `expected.json` 的 `prob_bits`） | **实现期（当前不存在，属实现期产物）** | 产品 | `—（实现期由产品实现者创建；本表登记其必须提供的调用形态）` | `约定 C：golden 基准消费契约` §3 全部命令 + §8.2 / §8.4 验收行。**状态：未验证（实现期产物；回补触发 = 脚本落地）** —— 按 §14 定义，`[LOCAL_DEAD_LINK]` 仅用于本机环境不可达项，不用于「实现期还没写的脚本」 |
| `tools/compare_lowconf.py` | 低置信入口分组比对器 | **实现期（当前不存在，属实现期产物）** | 产品 | `—（同上）` | §8.2 低置信入口行。**状态：未验证（实现期产物；回补触发 = 脚本落地）** |
| `tools/c6_zero_network.sh` | PID 级零网络运行时断言脚本（C6 / FR-24） | 实现期 | 产品 | — | `sh tools/c6_zero_network.sh <exe> <cases.jsonl>` 四态：无 socket → 0 / 持 socket → 1 / 缺失 → 2 / 瞬时退出 → 0 |

> **GP1 说明**：上表每个路径都能反查到「生成时点 / 责任单元 / 生成命令 / 校验命令」四要素；两个产物文件是**生成物**，其覆盖行为与不手改清单分别登记在 `约定 A` §4 与 `约定 B` §5。全文后续出现的 `src/` 均指本表定义的路径，无占位符。
>
> **脚手架状态（2026-10-21 实跑 `find src -type f`）**：`src/core/moon.pkg`、`src/data/moon.pkg`、`src/math_seam/moon.pkg`、`src/unicode/moon.pkg`、`src/core/cmd/main/moon.pkg`、`src/core/cmd/main/main.mbt` 共 **6** 个文件。四个基础 `moon.pkg` 为 **0 字节空包**，`src/core/cmd/main/main.mbt` 为空 `fn main { }`——全部属**脚手架**，**0 个产品 `.mbt` 符号**，不构成实现交付物。`moon check` 的 rc=0 只证明「模块存在 + 包图可解」，**不证明实现存在**。产品公开符号数（应为 0）的机检形态见 §10.6 命令 27。
> **脚手架状态（2026-10-21 实跑 `find src -type f`）**：`src/core/moon.pkg`、`src/data/moon.pkg`、`src/math_seam/moon.pkg`、`src/unicode/moon.pkg`、`src/core/cmd/main/moon.pkg`、`src/core/cmd/main/main.mbt`（+ `src/core/main.mbt` 若 build 需要）。四个空 `moon.pkg` **当前为 0 字节空包、0 个产品 `.mbt` 符号**，属**脚手架**，不构成实现交付物；`moon check` 的 rc=0 只证明「模块存在 + 包图可解」，**不证明实现存在**。`src/core/cmd/main/` 已按本表创建（含可执行包清单），产物路径已实测产出。


---

## 5. 公开接口契约（签名级）

> 命名与形态均已在真实编译器下验证（V-55 为错误形态、V-57 为通过形态）；证据等级 A。
> 「目标可用性」分级：`native ✅（V-24）` / `js ⚠（bun 替代，U-02）` / `wasm-gc ⚠（仅 build，U-01）`。

### 5.1 主语言检测

| 项 | 内容 |
|---|---|
| 签名 | `detect(text : String) -> String raise LangDetectError` |
| 入参 | `text`：任意 UTF-8 文本（可空串） |
| 出参 | 单一语言代码（取值域 = 可用语言集合） |
| 错误语义 | 无可提取特征 → 码 5；未加载档案 → 码 4 |
| 边界 | 在**合法参数**下返回不可能是 `'unknown'`（V-19 的 250 条基准从未触发）。**例外**：先验含 NaN 时上游返回 `'unknown'`（V-51）——本库照抄该行为，并在 §8.2 有对应验收行 |
| 目标可用性 | native ✅（V-24）/ js ⚠（bun 替代，U-02）/ wasm-gc ⚠（仅 build，U-01） |
| 回链 | FR-01、FR-12；US-01 |

### 5.2 概率分布

| 项 | 内容 |
|---|---|
| 签名 | `detect_langs(text : String) -> Array[LangProb] raise LangDetectError` |
| 入参 | 同 5.1 |
| 出参 | 按 §4.4 排序的 `LangProb` 数组；每条 `prob` 严格大于阈值 |
| 错误语义 | 同 5.1；**不**返回空数组作为「无结果」表达（空数组只在概率全被过滤时出现，属上游同义行为；V-51 是可构造实例） |
| 目标可用性 | native ✅（V-24）/ js ⚠（U-02）/ wasm-gc ⚠（U-01） |
| 回链 | FR-02、FR-03、FR-04；US-02 |

### 5.3 低置信入口

| 项 | 内容 |
|---|---|
| 签名 | `detect_with_confidence(text : String) -> Confidence` |
| 入参 | 任意 UTF-8 文本 |
| 出参 | `Confidence` 枚举，二选一：`LowConfidence(char_count~ : Int)` 或 `Detected(lang~ : String, probs~ : Array[LangProb])`（括号标签载荷形态已由 V-57 验证） |
| 阈值 | 字符数 `< 50` → 低置信；`>= 50` → 正常检测（阈值可配置，默认取 PRD 的 50） |
| 错误语义 | **不抛**码 5：空输入按 `char_count = 0` 归入低置信（与主 API 的显式差异，见 PRD §5.3 交互矩阵） |
| 目标可用性 | native ✅（V-24）/ js ⚠（U-02）/ wasm-gc ⚠（U-01） |
| 回链 | FR-21、FR-22、FR-23；US-04 |

> 与主 API 的关系：低置信入口**不改变** 5.1/5.2 的任何行为（FR-23）。

### 5.4 语言列表

| 项 | 内容 |
|---|---|
| 签名 | `get_lang_list() -> Array[String]` |
| 出参 | 可用语言代码数组，顺序 = 档案加载序（§4.5） |
| 错误语义 | 无 |
| 目标可用性 | native ✅（V-24）/ js ⚠（U-02）/ wasm-gc ⚠（U-01） |
| 回链 | FR-13；US-06 |

### 5.5 检测实例（构造 + seed）

| 项 | 内容 |
|---|---|
| 签名 | `Detector::new() -> Detector`（关联函数）；`DetectorFactory::create(self : DetectorFactory, alpha? : Double) -> Detector`（**实例方法，含 `self`**；`alpha` 为可选标签参数，**无默认值**） |
| 调用形态 | `let d = Detector::new()`；`let d = factory.create()` 或 `factory.create(alpha=0.5)`（**不写 `Some(...)`**：可选参数按裸值传，传 `Some(0.5)` 报 `[4080] requires 1 positional arguments, but is given 2`，见 V-58）。`alpha` 不传时取默认 0.5 |
| seed 默认 | 无值（不可复现，与上游一致，V-08） |
| seed 设置签名 | `Detector::set_seed(self : Detector, seed : Int64?) -> Unit`（**含 `self`**；缺 `self` 时 `d.set_seed(Some(0L))` 报 `[4014]` + `[4080]`，见 V-58） |
| 语义 | seed 在 `Detector` 构造时从工厂读取一次；设置后对**后续新建**的实例生效，对已建实例不追溯 |
| 目标可用性 | native ✅（V-24）/ js ⚠（U-02）/ wasm-gc ⚠（U-01） |
| 回链 | FR-05、FR-06；US-03 |

### 5.6 实例配置：先验

| 项 | 内容 |
|---|---|
| 签名 | `Detector::set_prior_map(self : Detector, prior : Map[String, Double]) -> Unit raise LangDetectError`（**含 `self`**） |
| 语义 | 只取可用语言中出现的键；负值 → 码 8（消息 `Prior probability must be non-negative.`）；总和 ≤ 0 → 码 8（消息 `More one of prior probability must be non-zero.`）；否则归一化为和 1。**NaN 值不触发码 8**（上游 `p < 0` 对 NaN 为假），归一化后全为 NaN，检测返回 `'unknown'`（V-51）——该行为按上游照抄并在 §8.2 验收 |
| 目标可用性 | native ✅（V-24）/ js ⚠（U-02）/ wasm-gc ⚠（U-01） |
| 回链 | FR-07、FR-08、FR-09；US-07 |

### 5.7 实例配置：长度上限

| 项 | 内容 |
|---|---|
| 签名 | `Detector::set_max_text_length(self : Detector, n : Int) -> Unit`（**含 `self`**） |
| 默认 | 10000（V-07） |
| 语义 | 计的是**清洗后**的码点数（V-43）；截断发生在空格折叠之前 |
| 目标可用性 | native ✅（V-24）/ js ⚠（U-02）/ wasm-gc ⚠（U-01） |
| 回链 | FR-10；US-07 |

### 5.8 异常类型与失败取证通道

| 项 | 内容 |
|---|---|
| 签名 | `suberror LangDetectError { CantDetect(code~ : Int, message~ : String, input_len~ : Int, input_prefix~ : String) }`（`suberror` + 标签载荷形态已由 V-57 验证；`struct` 作 raise 类型报 `[4118]`/`[4127]`，见 V-55） |
| 字段语义 | `code` ∈ 9 个码值（§6）；`message` 与上游 `str(e)` 逐字一致（上游**无** `.message` 属性，V-11）；`input_len` = 失败输入的码点数；`input_prefix` = 输入前 32 个码点 |
| **取证通道** | 四字段由调用方序列化为一行 JSON（`{"code":…,"message":…,"input_len":…,"input_prefix":…}`）写入调用方指定位置；记录可按 `code` 精确匹配检索。库**不**自行落盘（零副作用，见 §9.1） |
| 通道目标可用性 | native ✅ / js ✅ / wasm-gc ✅ —— 通道是「纯内存对象 + 调用方落盘」，与目标运行时无关 |
| 不可达码 | 0 / 6 / 7 保留码值，**不实现抛出**（§6） |
| 目标可用性 | native ✅（V-24）/ js ⚠（U-02）/ wasm-gc ⚠（U-01） |
| 回链 | FR-08/09/11/12；US-05；DESIGN D11；PRD §5.2 失败可诊断性行 |

> 后两个字段是 `[EXT]`（G-30）：上游异常只有 `code` + 消息。

### 5.9 接缝入口（内部契约，导出以支持测试注入）

| 项 | 内容 |
|---|---|
| 签名 | `ln_for_gauss(x : Double) -> Double`；`is_upper_cp312(cp : Int) -> Bool` |
| 语义 | `ln_for_gauss` 在 native 下绑定 libm `log`（1 参，返回自然对数），js / wasm-gc 下走 `@math.ln`；`is_upper_cp312` 查 U3 表（V-36/V-37） |
| 实现期新增字面 | 降级分支的代码注释必须带标记 `// non-native fallback`（当前仓库该字面 0 命中，属**实现期新增**；GP1 生成点 = `src/math_seam/` 实现时） |
| 目标可用性 | 两者全目标可用；**数值档位不同**：native = 逐位档（win32 x64），js / wasm-gc = 容差档（§8.4 + EQ1） |
| 回链 | DESIGN D3、D4；G1 接缝层；G2 XB1 |

### 5.10 诊断入口（`[EXT]`，G-33）

| 项 | 内容 |
|---|---|
| 签名 | `debug_vector_len() -> Int` |
| 语义 | 返回「每语言概率向量的元素个数」= 档案目录条目数（V-48、V-53）；**不是**可用语言数 |
| 用途 | 使 FR-20 在公开面可观察（V-53 证明上游公开面无此值） |
| 目标可用性 | native ✅ / js ✅ / wasm-gc ✅（纯整数读取） |
| 回链 | FR-20；`[EXT]` — 非对齐项，产品决策驱动 |

---

## 6. 错误码与消息表

| 码 | 名称 | 触发条件 | 消息原文 | 是否可达 | 目标可用性 |
|---|---|---|---|---|---|
| 0 | `NoTextError` | —（包内无抛出点，V-13） | —（无原文） | **否** | 保留占位，不实现抛出 |
| 1 | `FormatError` | 档案解析失败 / 结构不符 / `n_words` 越界或除零 / 档案目录内重复语言 | `Profile format error in "<path>"` 或 `Profile format error.` | 是（仅加载期） | 全目标 |
| 2 | `FileLoadError` | 打开档案抛 `IOError` | `Cannot open "<path>"` | 上游**未测**（ADR T9） | 保留实现，可达性未验证 |
| 3 | `DuplicateLangError` | `add_profile` 时语言已存在 | `Duplicate the same language profile.` | 是（仅直接调 `add_profile`） | 全目标 |
| 4 | `NeedLoadProfileError` | 未加载档案即检测 / 目录为空 / `load_json_profile` 少于 2 个 | `Need to load profiles.` / `Not found profile: <dir>` / `Need more than 2 profiles.` | 是 | 全目标 |
| 5 | `CantDetectError` | 清洗后无可提取特征 | `No features in text.` | 是（V-44） | 全目标 |
| 6 | `CantOpenTrainData` | —（包内无抛出点，V-13） | —（无原文） | **否** | 保留占位，不实现抛出 |
| 7 | `TrainDataFormatError` | —（包内无抛出点，V-13） | —（无原文） | **否** | 保留占位，不实现抛出 |
| 8 | `InitParamError` | 先验含负值 / 先验总和 ≤ 0 | `Prior probability must be non-negative.` / `More one of prior probability must be non-zero.` | 是 | 全目标 |

> 码 2 的实现保留但可达性未验证（ADR T9）。**NaN 先验不触发码 8**（V-51）：它走「先验全 NaN → 概率全 NaN → 过滤后为空 → `detect` 返回 `'unknown'`」路径，已写入 §5.6 与 §8.2。

---

## 7. 方言红线表（DR1-DR11，append-only）

**总则（BLK-13 / MS1-6 落回条款）**：

1. **检索面** = 产品源码目录 `src/`。`docs/`、`probes/`、`_build/`、`.mooncakes/` **不在扫描域**——文档与探针中提及被禁字面属说明性引用，不构成违规。
2. **产品注释书写纪律**：产品代码注释若需说明某禁令，必须用**描述形态**（如「禁用 math 模块的平方根」），**不得**复现被检索的字面形态，否则会命中自己的检索式。
3. 本表 **append-only**：新增行只追加，不改既有行；若某条因工具链升级失效，新增一行标注「替代 DRx」而不是改写原行。

| 编号 | 禁令 / 约束 | 权威出处 | 可机检形态 |
|---|---|---|---|
| DR1 | **禁止** `@math.sqrt`；平方根走 `Double::sqrt` | `probes/rand-probe/rand-probe.mbt:12`（注释「sqrt -> Double::sqrt（builtin，编译为 %f64_sqrt）」）+ 同文件 186 行 `.sqrt()` 用法 | `test -d src \|\| exit 2; grep -rn '@math\.sqrt' --include=*.mbt src` 必须 0 行 |
| DR2 | **禁止**用 `@math.ln` 的数值做位级断言；native 必须用 libm `log`；`@math.ln` 仅 js / wasm-gc 降级路径可用，且该处必须带标记 `// non-native fallback`（该字面为**实现期新增**，当前仓库 0 命中；GP1 生成点 = `src/math_seam/` 实现时） | `docs/port/rand-feasibility.md` §3.1（2000 点 66 点差）+ `probes/rand-probe/rand-probe.mbt:176`（`pub extern "C" fn c_log`）。**参照命中清单（探针，非产品）**：代码 3 处 —— `probes/rand-probe/rand-probe.mbt:203`、`probes/rand-probe/cmd/main/main.mbt:140`、`probes/rand-probe/cmd/main/main.mbt:150`；注释 4 处 —— `rand-probe.mbt:13,174,175`、`cmd/main/main.mbt` 文件头 | `test -d src \|\| exit 2; grep -rn '@math\.ln(' --include=*.mbt src` 的每行必须同时命中 `non-native fallback`（同文件同函数内） |
| DR3 | native 下 `@math.cos` / `@math.sin` 本身即 `extern "C"`（libm），**禁止**再自行绑定 `cos`/`sin` | `probes/rand-probe/rand-probe.mbt:14-15` + `docs/port/rand-feasibility.md` §3 | `test -d src \|\| exit 2; grep -rnE 'extern "C" fn c_(cos\|sin)' --include=*.mbt src` 必须 0 行 |
| DR4 | **禁止**用 `Char::is_ascii_uppercase` 或第三方 Unicode 包做大写判定；必须用 `is_upper_cp312` | `docs/port/c1-residual-risks.md` §1.1 + ADR U 行 | `test -d src \|\| exit 2; grep -rn 'is_ascii_uppercase' --include=*.mbt src` 必须 0 行；`grep -rn -e 'unicode-data' -e 'moonbitlang/x' --include=moon.pkg src` 必须 0 行 |
| DR5 | **禁止** `Map[String, Int]` 字面量承载 55 语言档案 | `analysis/toolchain-probes.md` §B.3；`probes/logs/s55-map-03-test.log`；`约定 A` A4 | `test -f src/data/profiles.mbt \|\| exit 2; grep -c 'Map::from_array' src/data/profiles.mbt` 必须 0（`约定 A` C-A4） |
| DR6 | **禁止**假设存在 core `@fs` 包；文件读取只在 `moonbitlang/async/fs`，且该包仅 native/wasm 可用 | `probes/fs-probe/cmd/main/moon.pkg:3` + `analysis/toolchain-probes.md` §C.3 | `grep -rn '"moonbitlang/core/fs"' --include=moon.pkg src` 必须 0 行；若出现 `async/fs` 则该包必须标 `targets` |
| DR7 | **禁止** `derive(Show)`；用 `derive(Debug)` 或手写 | 实测告警原文（`moonc v0.10.15`）：`derive(Show) is deprecated. Use derive(Debug) or manually implement the Show trait instead.` | `test -d src \|\| exit 2; grep -rn 'derive(Show)' --include=*.mbt src` 必须 0 行 |
| DR8 | 跨包调用必须用 `@alias.symbol()`；包 = 目录 | `probes/embed-probe/cmd/main/moon.pkg`（import 目录）+ `probes/embed-probe/cmd/main/main.mbt:5-6`（`@data.` 前缀） | `test -d src \|\| exit 2; grep -rnE '(^\|[^@[:alnum:]_])(data\|math\|fs)\.[a-z_]+\(' --include=*.mbt src` 必须 0 行（正则显式排除 `@` 前缀，v2 修正） |
| DR9 | **禁止**在 `src/core/` 出现**条件编译**（MoonBit 方言为 `#cfg(...)` / `#if(...)`）；平台差异只允许在 `src/math_seam/` 内 | DESIGN PS2（业务侧零内联平台条件分支）；MoonBit 实际条件编译形态由 N-01 实测确认（`#cfg(wasm)` / `#cfg(js)`） | 代码块见 §10.6 命令 1：只匹配行首（允许缩进）的 `#cfg(` / `#if(`，**不匹配**裸词 `target` / `platform`（否则合法标识符 `target_lang()` 与中文注释「目标」会假红） |
| DR10 | **禁止**在 `src/core/` 出现**运行期平台判断 API 的调用**（`is_wasm(...)` / `target_name(...)`） | 同上（N-01 要求把「运行期判断」与「条件编译」分成两行）；**v4 修正**：v3 的裸词形态对 `is_wasm_compatible()` / `get_target_name_of()` 假红（N-18），故改为**语法锚定调用形态** | 代码块见 §10.6 命令 2：`grep -rnE '(^|[^[:alnum:]_])(is_wasm\|target_name)[[:space:]]*\(' --include=*.mbt src/core` 必须 0 行（T1 基线：`pub fn is_wasm_compatible()` / `get_target_name_of(...)` 仍 rc=1；T2：`is_wasm()` 调用 → rc=0） |
| DR11 | **禁止反向模块依赖**：`src/data/`、`src/unicode/`、`src/math_seam/` 不得引用 `vicoproplus/langdetect/src/core`（D2 声明依赖单向） | DESIGN D2 模块边界表（依赖方向 `src/core/` → 三个基础包 → 标准库） | 代码块见 §10.6 命令 3：对三个基础包的 `moon.pkg` 检索 `src/core` 必须 0 行（N-09：编译器允许反向 import，故需独立门禁） |

> **表内 `\|` 仅为 Markdown 转义**；§7 的所有可执行命令同时以**代码块形态**给出（见 §10.6），执行时从代码块复制。表格单元格内的 `\|` 逐字复制会变成字面竖线（正则永不匹配 = 假绿）或让 `cut -d` 解析失败（永久红），见 review-findings N-02。

> DR9 承接 DESIGN G1 的 PS2 红线；**v3 修正**：检索式由裸词三元组改为 MoonBit 条件编译关键字（v2 的裸词形态对合法标识符假红、对真实 `#cfg` 漏检，见 review-findings N-01），并拆出 DR10（运行期平台 API）与 DR11（反向模块依赖，review-findings N-09）。DR9/DR10/DR11 的 T1 基线必须是**非空包**（先放合法 `.mbt` 再跑，空包 rc=1 属空集假绿）。

---

## 8. 验收表（分层，4 维度）

> **每行三要素**：目标环境标识 + 可重跑命令 + 观测输出（**未验证时填 `—`**；期望值来源单列）。
>
> **整体判定（Fail-3）**：本表**任一维度、任一行失败，整体验收即失败**；不允许用其他维度的通过抵扣，也不允许把某维度标「不适用」来规避。
> **门禁**：任一行「未验证」且无三要素时**不得**判该维度完成。本 spec 冻结时全部为「未验证」是如实状态（产品实现未落地）。

### 8.1 维度一：运行时链路

| 项目 | 目标环境 | 操作证据（命令 / 入口） | 期望值来源 | 观测输出 | 状态 |
|---|---|---|---|---|---|
| 首次调用完成档案加载 | native (win32 x64) | `C:/Users/Administrator/.moon/bin/moon.exe test --target native`（cwd = 仓库根） | `analysis/toolchain-probes.md` §C.1 | — | 未验证（产品实现未落地） |
| 首次调用完成档案加载 | js | `C:/Users/Administrator/.moon/bin/moon.exe test --target js`（PATH 前置 `probes/bin`） | `probes/logs/target-js-02-test.log` | — | 未验证（替代运行时，U-02） |
| 首次调用完成档案加载 | wasm-gc | `C:/Users/Administrator/.moon/bin/moon.exe build --target wasm-gc` | `probes/logs/target-wasm-gc-01-build.log` | — | `[LOCAL_DEAD_LINK]`（test 不可达，U-01） |
| 空目录下可检测 | native (win32 x64) | `cd <空临时目录> && /f/moonbit比赛/moon_langdetect/_build/native/debug/build/src/core/cmd/main/main.exe`（**当前该入口为空 `fn main { }`，尚未调用 `detect`**；detect 链路待实现） | PRD FR-13 | — | 未验证（实现期产物；回补触发 = `main.mbt` 填入 detect 调用；填入前不计已验证） |

### 8.2 维度二：功能对齐（按 FR 分组）

| 分组 | 覆盖 FR | 目标环境 | 操作证据（命令 / 入口） | 期望值来源 | 观测输出 | 状态 |
|---|---|---|---|---|---|---|
| 主检测与概率形态 | FR-01/02/03/04 | native (win32 x64) | `python tools/compare_golden.py --target native --seed 0 --mode prob_bits`（脚本**当前不存在**，GP1 见 §4A） | `docs/port/golden/expected.json` | — | 未验证（实现期产物；回补触发 = `tools/compare_golden.py` 落地；落地前本行不计已验证。**注：§10.6 命令 16–19 只校验基准文件自身，不校验产品行为，不构成等价入口**） |
| **seed 语义** | **FR-05/FR-06** | native (win32 x64) | `python tools/compare_golden.py --target native --mode seed_semantics`（脚本**当前不存在**，GP1 见 §4A）：① seed=0 同文本 ×5 差异数；② seed=42 与 0 的差异数且自身 ×5 可重复；③ 不设 seed ×10 的多结果计数与异常计数 | `docs/port/golden/expected.json` 的 `repeatability`（14 组）与 `unseeded_runs` | — | 未验证（实现期产物；回补触发 = 脚本落地；落地前不计已验证） |
| 参数与失败路径 | FR-07/08/09/10/11/12 | native (win32 x64) | `python tools/compare_golden.py --target native --mode failures`（脚本**当前不存在**，GP1 见 §4A） | `docs/port/upstream-behavior-contract.md` §9 | — | 未验证（实现期产物；同上） |
| **失败取证通道** | FR-08/09/11/12（PRD §5.2） | native (win32 x64) | `python tools/compare_golden.py --target native --mode forensics`（脚本**当前不存在**，GP1 见 §4A） | 本文 §5.8 | — | 未验证（实现期产物；回补触发 = 脚本落地） |
| 清洗契约 | FR-15/16/17 | native (win32 x64) | `python tools/compare_golden.py --target native --mode cleaning`（脚本**当前不存在**，GP1 见 §4A） | `tools/probe_facts.py append_cleanup` 同口径 | — | 未验证（实现期产物；回补触发 = 脚本落地） |
| 大写词与缓存 | FR-18/19/20 | native (win32 x64) | `python tools/compare_golden.py --target native --mode features_cache`（脚本**当前不存在**，GP1 见 §4A） | `docs/port/upstream-behavior-contract.md` §10 | — | 未验证（实现期产物；回补触发 = 脚本落地） |
| 低置信入口 | FR-21/22/23 | native (win32 x64) | `python tools/compare_lowconf.py --short 55 --long 55 --baseline 268`（脚本**当前不存在**，GP1 见 §4A） | PRD FR-21/22/23 | — | 未验证（实现期产物；回补触发 = `tools/compare_lowconf.py` 落地；落地前不计已验证） |
| 内嵌档案与零外部读取 | FR-13/14/24/25/26 | native (win32 x64) | §10.6 命令 21–25（约定 A/B/C 的产物侧，**已实跑**）+ `python tools/compare_golden.py --target native --mode profile_counts`（脚本**当前不存在**） | 约定 A/B/C + V-14 | — | 部分可跑：产物侧命令已跑（§10.6 rc 实录）；`profile_counts` 模式 未验证（实现期产物；同上） |

### 8.3 维度三：跨目标产物

| 项目 | 目标环境 | 操作证据（命令 / 入口） | 期望值来源 | 观测输出 | 状态 |
|---|---|---|---|---|---|
| 三目标 build 通过 | native / js / wasm-gc | `C:/Users/Administrator/.moon/bin/moon.exe build --target native`；`… --target js`；`… --target wasm-gc` | `analysis/toolchain-probes.md` §C.1 | — | 未验证 |
| 三目标主语言一致 | native / js / wasm-gc | `python tools/compare_golden.py --target {native,js,wasm-gc} --mode top1` | PRD FR-01 | — | 未验证（wasm-gc 运行时不可达 U-01 + js 替代运行时 U-02 + 比对脚本为实现期产物；回补触发 = 运行器/官方 node 可用且脚本落地） |
| 三目标可用语言数一致 | native / js / wasm-gc | `python tools/compare_golden.py --target {native,js,wasm-gc} --mode lang_list_len` | PRD FR-13 | — | 未验证（实现期产物；回补触发 = 脚本落地） |
| 三目标条目合计一致 | native / js / wasm-gc | `python tools/compare_golden.py --target {native,js,wasm-gc} --mode entry_total` | PRD FR-25 | — | 未验证（实现期产物；回补触发 = 脚本落地） |
| 源侧 23 用例的目标侧对应文件存在且通过 | native (win32 x64) | `C:/Users/Administrator/.moon/bin/moon.exe test --target native`（需 §2A 的 4 个 `*_test.mbt` 就位；当前 `find src -name "*_test.mbt"` → **0** 个） | §2A | — | 未验证（实现期产物；回补触发 = 产品测试文件建立后；建立前不计已验证） |

### 8.4 维度四：位级一致性（按平台分档）

| 项目 | 目标环境 | 操作证据（命令 / 入口） | 期望值来源 | 观测输出 | 状态 |
|---|---|---|---|---|---|
| `prob_bits` 逐位一致（seed 0） | **native (win32 x64)** | `python tools/compare_golden.py --target native --seed 0 --mode prob_bits` | `docs/port/golden/expected.json` | — | 未验证 |
| `prob_bits` 逐位一致（seed 42） | **native (win32 x64)** | `python tools/compare_golden.py --target native --seed 42 --mode prob_bits` | 同上 | — | 未验证 |
| 同 seed 重复 5 次一致 | **native (win32 x64)** | `python tools/compare_golden.py --target native --mode repeatability`（14 组） | `expected.json` 的 `repeatability` | — | 未验证 |
| 容差档（数值待校准） | **native（其他平台）** | `python tools/compare_golden.py --target native-other --mode prob_tolerance` | `约定 C` §4；U-05 | — | `[LOCAL_DEAD_LINK]`（能力未验证，U-05） |
| 容差档（数值待校准） | **js / wasm-gc** | `python tools/compare_golden.py --target {js,wasm-gc} --mode prob_tolerance` | `约定 C` §4；U-04 | — | `[LOCAL_DEAD_LINK]`（指标未测，U-04） |

> **非等价降级（Fail-2 显式声明）**：js / wasm-gc 走 `@math.ln`，相对 native 的 libm `log` 是**非等价降级**——实测 2000 点中 66 点差 1 ulp（1934/2000），`gauss` 512 点中 27 点不一致（485/512）。**不是等价实现**，故这两目标只能按容差档判定（§11 MS1-4 同一裁决）。

> **§8 门禁条款（补法，N-04）**：每行必须二选一——**(a)** 给出可复跑命令（含前提交付物路径，且该交付物已登记在 §4A 的 GP1 表）；**(b)** 标 `[LOCAL_DEAD_LINK]` + 分类（能力未验证 / 指标未测）+ 回补触发条件 + 处置（见 §14，U-01…U-12）。两者皆无 = 该行未回填，不得判该维度完成。环境不可达项见 §14（U-01…U-12）；**实现期产物未就绪类**另按 §14 的标签语义写「未验证（实现期产物）」，**不**计入 §14 的 U 表。

### 8.4a 运行时原语可用性矩阵（Fail-4）

> 证据等级：**A = 本机实测**（附命令/日志）／**B = 文档或上游源码**／**不可用**。**任一「不可用」格阻断依赖它的决策**（该格上的设计不成立）。

| 原语 | native | js | wasm-gc | 证据 |
|---|---|---|---|---|
| `extern "C"` 绑定 libm `log` | **A** | 不可用 | 不可用 | A：`probes/rand-probe/rand-probe.mbt:176` + 2000/2000 点一致（`docs/port/rand-feasibility.md` §2）；不可用：`extern "C"` 在 js/wasm-gc 无 C 运行时 |
| `@math.ln`（纯 MoonBit） | **A** | **A** | **A** | A：三目标均 build 通过（`analysis/toolchain-probes.md` §C.1）；数值与 libm 差 1 ulp（V-35） |
| `Double::sqrt` | **A** | **A** | **A** | A：`probes/rand-probe/rand-probe.mbt:186` 实际用法；`docs/port/rand-feasibility.md` §3（2000 点全一致） |
| `@math.cos` / `@math.sin` | **A**（libm） | **B**（`Math.cos/sin`，未逐位验证） | **B**（同上） | A：`probes/rand-probe/rand-probe.mbt:14-15` + §3（native 2000 点全一致）；B：js/wasm-gc 未逐位测 |
| 编译期大常量（2.2 MB 字符串） | **A** | **A** | **A（仅 build）** | A：`analysis/toolchain-probes.md` §B.3（s55-flat 56/56）+ §C.1（三目标 build 0）；wasm-gc 的 test 不可达（U-01） |

> 矩阵与 §10.6 命令 2 的 DR10、§11 MS1-3/MS1-4 一致：`extern "C"` 不可用的两格，正是「非等价降级」的来源。

### 8.5 EQ 分叉点（平台语义分叉断言）

**EQ1：分叉点清单（逐档登记目标运行时语义 + 受影响断言）**

| 分叉点 | 目标运行时语义 | 受影响断言 |
|---|---|---|
| `log` 位型档 | native = libm `log`（与 CPython 同平台 libm 逐位一致，V-32）；js / wasm-gc = `@math.ln`（1 ulp 级差异，V-35） | §8.4 前 3 行（native 逐位）/ 后 2 行（容差） |
| 浮点比较档 | 全目标均为 IEEE754 双精度比较（V-33/V-34 证明加法/除法同舍入；比较本身无舍入） | §8.2 主检测与概率形态（FR-03 的严格阈值）、§4.4 |
| 排序并列档 | 稳定排序；并列保持档案加载序（V-06、V-50） | §8.2 主检测与概率形态（FR-04）、§4.4 |

**EQ2：每档的构造输入（触及该档的样本）**

| 分叉点 | 构造输入 | 实测/状态 |
|---|---|---|
| `log` 位型档 | 固定 seed 的 55 条长文本（跨 native 与 js/wasm-gc 各跑一遍，比较 `prob_bits`） | 未验证（产品实现未落地）；参照量级见 V-35 |
| 浮点比较档（阈值边界） | 三组构造：**恰等于** 0.1 / **略大于** 0.1 / **略小于** 0.1。构造方式二选一：① `set_prior_map` 造出可控初始权重（如两语言等权 + 单特征文本，令归一化后最大概率落在边界）；② 接缝注入概率数组。**当前状态**：基准侧无恰等于阈值的样本（V-49：250 条中最小条目 0.1428…，无 ≤0.1），故本档**只能经接缝注入构造** → 登记 `[LOCAL_DEAD_LINK]`（分类：**能力未验证**；回补触发 = 接缝可注入概率数组之后；处置 = 实现期补三组样本并断言「恰等于 → 被过滤；略大 → 保留；略小 → 被过滤」） |
| 浮点比较档（NaN） | `set_prior_map({'en': NaN})` + 任意合法长文本 | **可构造**（V-51）：上游返回空列表 + `'unknown'` |
| 排序并列档 | 2 档案等权 + 文本 `q r` | **可构造**（V-50）：两条目概率相等，顺序 = 档案序 |

**EQ3：契约层的分叉语义声明**
- 比较与排序按 IEEE754 双精度**数值**比较（§4.4）。
- NaN 不参与过滤与排序：NaN 与任何值比较为假，故不被「严格大于阈值」保留（V-51 的上游行为与此一致）。
- 负零不满足「严格大于正阈值」，被过滤；负零与正零在数值比较上相等（故并列判定按数值相等处理）。

---

## 9. 行为等价断言（三层 + 负向轴）

### 9.1 层 1：数据流（每个入口的副作用全枚举）

| 入口 | 网络 | 存储写入 | 全局状态 | 事件 | 缓存 | 日志 | 别名回填 | 断言 |
|---|---|---|---|---|---|---|---|---|
| `detect` | 无 | 无 | 读单例工厂（首次初始化） | 无 | 写实例 `langprob` | 无 | 无 | L1-A1…A3 |
| `detect_langs` | 无 | 无 | 同上 | 无 | 同上 | 无 | 无 | 同上 |
| `detect_with_confidence` | 无 | 无 | 无（内部新建实例） | 无 | 无 | 无 | 无 | L1-A1 |
| `get_lang_list` | 无 | 无 | 只读 | 无 | 无 | 无 | 无 | L1-A1 |
| `debug_vector_len` | 无 | 无 | 只读 | 无 | 无 | 无 | 无 | L1-A1 |
| `Detector::set_seed` | 无 | 无 | 只写实例字段 | 无 | 无 | 无 | 无 | L1-A1 |
| `Detector::set_prior_map` | 无 | 无 | 只写实例字段 | 无 | 无 | 无 | 无 | L1-A1；失败码 8 |
| `Detector::set_max_text_length` | 无 | 无 | 只写实例字段 | 无 | 无 | 无 | 无 | L1-A1 |
| `Detector::append` | 无 | 无 | 改实例 `text`（**追加**，V-54） | 无 | **不**清 `langprob`（V-47） | 无 | 无 | L1-A1 + V-47 + V-54 |
| **`Detector::cleaning_text`** | 无 | 无 | **就地**改实例 `text`（幂等，V-54） | 无 | 无 | 无 | 无 | L1-A1 + V-54 |
| **`Detector::detect`** | 无 | 无 | 触发 `_detect_block` → 写 `langprob` | 无 | 同上 | 无 | 无 | L1-A1 + L1-A3 |
| **`Detector::get_probabilities`** | 无 | 无 | 惰性触发 `_detect_block`（首次） | 无 | 同上 | 无 | 无 | L1-A1 + L1-A3 |
| **`DetectorFactory::load_profile`** | 无 | 无 | 写工厂 `langlist` + `word_lang_prob_map` | 无 | 无 | 无 | **是**（已建实例通过别名可见） | L1-A1 + L1-A4 |
| `ln_for_gauss` / `is_upper_cp312` | 无 | 无 | 只读 | 无 | 无 | 无 | 无 | L1-A1 |

**断言（每条一行，可运行验证）**

| 编号 | 断言 | 验证命令 |
|---|---|---|
| L1-A1 | 每个入口的「网络 / 存储写入 / 事件 / 日志」四列均为「无」 | 静态：`grep -rnE 'http\|socket\|write_file\|log_write' src` 必须 0 行 |
| L1-A2 | 全局状态仅两处：单例工厂（首次初始化）与实例字段 | 静态：`grep -rn 'let mut\|global' src` 逐行核对归属 |
| L1-A3 | `append` 不清 `langprob`；`detect`/`get_probabilities` 首次调用触发检测 | 行为：同实例二次 `detect` 返回首次结果（V-47） |
| **L1-A4** | **引用别名回填**：`Detector` 与工厂共享 `langlist` 与 `word_lang_prob_map` 同一对象；`load_profile`/`clear` 后已建实例可见变化（V-52） | 行为：`load_profile` → `create` → 再 `add_profile` → 断言 `len(detector.langlist)` 与 `len(factory.langlist)` 同步增加（**不用 `get_lang_list()`：该方法是工厂的方法，`Detector` 无此方法**，N-05）；另断言 `detector.langlist is factory.langlist` 为 True |

> **表内 `\|` 仅为 Markdown 转义**；L1-A1…L1-A4 的可执行命令见 §10.6 命令 11–14，执行时从代码块复制（review-findings N-02）。

### 9.2 层 2：页面行为

**N/A — 无用户可见界面。** 本库是纯计算库，无页面、无组件、无渲染、无交互控件；不存在布局 / 截断 / 叠压 / 安全区类可观察项。故 DESIGN G1 的 RS1-RS4 与 P7 的渲染维度在此不适用（DESIGN §七 G1 已同样登记）。

### 9.3 层 3：生产者-消费者（共享状态逐键，一写多读逐行展开）

| 共享状态键 | 写方（生产者） | 写入位置 | 读方（消费者） | 消费位置 | 联动说明 |
|---|---|---|---|---|---|
| `langlist` | 工厂 `add_profile` | `langdetect/langdetect/detector_factory.py:84` | `detect_langs` 排序 | `detector.py:235` | 顺序即并列序（§4.4） |
| `langlist` | 同上 | 同上 | `get_lang_list` | `detector_factory.py:113` | 返回值顺序 |
| `langlist` | 同上 | 同上 | `_init_probability` | `detector.py:180` | 初始概率长度 |
| `langlist` | 同上 | 同上 | **已建 `Detector` 通过别名读取** | `detector.py:58`（构造时赋值） | **别名共享**（V-52）：工厂后续变更对已建实例可见 |
| `langlist` | 工厂 `clear` | `detector_factory.py:95` | 同上三处 + 已建实例 | 同上 | 清空后已建实例可见空列表 |
| `word_lang_prob_map` | 工厂 `add_profile` | `detector_factory.py:87-92` | 特征抽取（字典命中） | `detector.py:197` | 键集合决定哪些 n-gram 是特征 |
| `word_lang_prob_map` | 同上 | 同上 | 概率更新 | `detector.py:206` | 词向量取值 |
| `word_lang_prob_map` | 同上 | 同上 | **已建 `Detector` 通过别名读取** | `detector.py:57` | 别名共享（V-52） |
| `word_lang_prob_map` | 工厂 `clear` | `detector_factory.py:96` | 同上三处 + 已建实例 | 同上 | 清空后特征命中率归零 |
| `seed` | 工厂 `set_seed` / 类属性 | `detector_factory.py:29,110-111` | `Detector.__init__` 复制 | `detector.py:59` | 只在构造时读一次 |
| `langprob`（实例） | `_detect_block` | `detector.py:152,169` | `detect` | `detector.py:136` | 缓存复用（V-47） |
| `langprob`（实例） | 同上 | 同上 | `get_probabilities` | `detector.py:142-144` | 同上 |
| `text`（实例） | `append`（追加）/ `cleaning_text`（就地改写，幂等） | `detector.py:111,130` | `_extract_ngrams` | `detector.py:148` | `append` **追加**而非覆盖；`cleaning_text` 幂等（V-54） |
| `prior_map`（实例） | `set_prior_map` | `detector.py:78-91` | `_init_probability` | `detector.py:177-178` | 归一化后和恒为 1；NaN 例外见 V-51 |
| `Verbose`（实例） | `set_verbose` | `detector.py:71` | 多处打印 | `detector.py:165,170,207` | ADR X 裁决不移植 → 本库无此键 |

### 9.4 负向轴

| 编号 | 断言 | 可观察形态 | 验证命令 |
|---|---|---|---|
| **NE1** | 静默语境零展示：库自身不向 stdout/stderr 写任何字节（**与被测运行器输出无关**） | ① 静态：产品源码（**排除 `cmd/main/` 与 `cmd/golden/` 路径段**；`cmd/golden` 是诊断输出工具，按 NE1 例外处理，2026-10-22 用户裁决）中不存在 stdout/stderr 写调用；② 运行时：`src/core/cmd/main` 二进制 stdout 与 stderr 均为 0 字节 | 静态命令以命令 11b 为准（`grep … | grep -vE '[\\/]cmd[\\/](main|golden)[\\/]'`，rc=1 期望 0 行；库与 `cmd/main` 必须零命中，`cmd/golden` 为诊断输出例外；spec §10.6 命令 11 的宽豁免仅作参考）；运行时命令见 §10.6 命令 29（字节计数形态：二进制缺失 → rc=2；有输出 → rc=1；静默 → rc=0）。**实测**：`println` 放 `src/core/cmd/main/main.mbt` → 命令 11 rc=1（0 行）；放 `src/core/zz_n.mbt` → rc=0（命中 1 行）；空 `main` 的二进制 stdout/stderr 均 0 字节 |
| NEG-2 | 非约定形态错误的用户可见语义：签名不符（如 seed 传字符串）为**编译期**错误，不是运行期码 | 编译失败退出码 ≠ 0，无码值产生 | 构造错误调用 → `moon check` 非 0 |
| NEG-3 | 每条正向断言配失败分支 | 见 §8 各行的「未验证」态与 §6 码 5/4/8 的可构造性 | 逐行核对 |
| NE4-1 | **检测期间网络请求数 = 0** | 调用前后对外连接数差 = 0 | `netstat -an` 前后对比（或在沙箱内禁止网络后检测仍成功） |
| NE4-2 | **对非内置数据的文件读取数 = 0** | 产品源码无 `read_file` 调用 | `grep -rn 'read_file' src` 必须 0 行 |
| NE4-3 | **主 API 在合法参数下不返回 `'unknown'`** | `detect` 返回值 ∈ 可用语言集合 | 250 条有概率输出样本逐条断言（V-51 的 NaN 先验为**显式例外**，已登记） |
| NE4-4 | **零第三方运行时依赖** | `moon.pkg` 的 import 仅标准库 + 本仓库包 | `grep -rn -e 'moonbit-community' -e 'moonbitlang/x' --include=moon.pkg src` 必须 0 行 |

---

> **表内 `\|` 仅为 Markdown 转义**；NE1…NE4 的可执行命令见 §10.6 命令 11–15，执行时从代码块复制（review-findings N-02）。

## 10. 机检门禁命令清单（GT1-GT2 / GP1 / FL1）

**T1 = 语法可跑（已试跑）**；**T2 = 已知违规样本必红（实录退出码）**；**T3 = 证伪自检路径**。命令中 `src/` 的定义见 §4A。

### 10.1 约定 A 门禁（A1-A6）

| 命令 | T1 已试跑（2026-10-21，GNU grep） | T2 已知违规（实录） | T3 证伪路径 |
|---|---|---|---|
| C-A1/C-A2（声明数 55 / 条目 184129） | 对探针产物：`decls 55 entries 184129`，exit **0** | 删 1 个语言声明 → `decls 54 entries 181986`，exit **1**；删 1 个条目（保留声明数）→ `decls 55 entries 184128`，exit **1** | 若合法产物 exit 1 → 检查正则是否被注释行干扰 |
| C-A3（字节 2205308） | `test "$(wc -c < "$F" \| tr -d ' ')" = "2205308"`，exit **0** | 追加 1 个空格 → exit **1** | 若合法产物 exit 1 → 确认无 BOM/CRLF |
| C-A4（`Map::from_array` 计数 0） | `test "$(grep -c 'Map::from_array' "$F")" = "0"`，exit **0** | 注入一行 → 计数 1，exit **1** | 若误报 → 检查大小写与转义 |
| C-A5（生成清单 mode=flat） | `.venv/Scripts/python.exe -c "import json,sys;sys.exit(0 if json.load(open('probes/gen-manifest.json'))['mode']=='flat' else 1)"`，exit **0** | `mode` 改 `map` → exit **1** | 若合法清单 exit 1 → 检查 JSON 编码 |
| C-A6（首行含「勿手改」） | `head -1 "$F" \| grep -q '勿手改'`，exit **0** | 首行改 `// no marker` → exit **1** | 若合法产物 exit 1 → 检查首行是否被改写 |

> `$F` = `src/data/profiles.mbt`（产品）或 `probes/embed-probe/lib/data/data.mbt`（参照样本）。**产品产物尚未生成 → 产品侧 T1 未做**（阻塞 U-06 之外的 T16 类项）。

### 10.2 约定 B 门禁（B1-B6；B1/B3/B4 合并为一行）

| 命令 | T1 已试跑（2026-10-21，GNU grep） | T2 已知违规（实录） | T3 证伪路径 |
|---|---|---|---|
| C-B1/C-B3/C-B4（版本 + 1951 码点 + 651 区间） | `ok 1951 cps / 651 intervals`，exit **0** | 断言 `len(cps)==1950` → `AssertionError 1951`，exit **1** | 若合法环境 exit 1 → 检查 `.venv` 版本与 `unidata_version` |
| C-B2（表头版本字段） | **未做 T1**（产物 `src/unicode/upper_table.mbt` 未生成） | 表头缺失 `unidata_version` → 必然 exit 1 | 同上 |
| C-B5（全码点 0 不一致） | **未做 T1**（同上） | 注入 1 个错判码点 → diff 计数 1，exit 1 | 若合法表 exit 1 → 检查 surrogate 跳过范围 |
| C-B6（无第三方 Unicode 引用） | `test -d src \|\| exit 2; test "$(grep -rlE 'moonbitlang/x\|unicode-data' src \| wc -l)" = "0"` → exit **0**（路径存在、0 命中） | 在 `src/` 下写含 `"moonbit-community/unicode-data"` 的 `moon.pkg` → exit **1** | 若误报 → 检查检索面是否含 `.mooncakes`；**路径不存在时命令 exit 2**（不再是假绿） |

> v2 修正：C-B6 先断言路径存在（`test -d src || exit 2`），路径缺失时**不再**把 grep 的 exit 2 洗成 0。

### 10.3 约定 C 门禁（C1-C6；C1/C5 合并为一行）

| 命令 | T1 已试跑（2026-10-21，GNU grep） | T2 已知违规（实录） | T3 证伪路径 |
|---|---|---|---|
| C-C2（268 = 250 + 18） | `ok 268=250+18`，exit **0** | 断言改 `(268,249,18)` → `AssertionError`，exit **1** | 若合法基准 exit 1 → 检查读的文件 |
| C-C3（seed 集合 {0,42}） | `ok seeds 0/42`，exit **0** | 断言改 `[0]` → `AssertionError [0, 42]`，exit **1** | 同上 |
| C-C4（异常码全为 5） | `ok error code 5`，exit **0** | 断言改 `{4}` → `AssertionError {5}`，exit **1** | 同上 |
| C-C1/C5（`prob_bits` 16 位小写 hex） | `ok prob_bits hex16`，exit **0** | 用大写样本 `3FEB6DB6FE663AB1` 匹配 → `AssertionError`，exit **1** | 若合法基准 exit 1 → 检查正则字符类 |
| **C-C6（覆写检查：基准 md5 未变）** | `test "$(md5sum docs/port/golden/expected.json \| cut -d' ' -f1)" = "219519ee19d7cc10d404ddbdab3acd87"`，exit **0** | 复制基准到临时文件、追加 1 字节 → 用同一 `test` 命令比对 → exit **1**（v1 的 `md5sum` 单独执行恒 exit 0，无法表达该判据） | 若合法基准 exit 1 → 说明基准被改，必须回滚而非改期望值 |

### 10.4 方言红线 grep（DR1-DR11）

> **表内 `\|` 仅为 Markdown 转义；本节所有命令同时以代码块形态给出（见 §10.6），执行时从 §10.6 代码块复制。** 逐字复制表格单元格内的命令会因转义导致假绿（正则里的 `\|` 永不匹配）或永久红（`cut -d' ' ...` 被解析成 `md5sum -d`），见 review-findings N-02。

| 命令 | T1 已试跑（2026-10-21，`src/` 六文件已存在） | T2 已知违规（实录） | T3 证伪路径 |
|---|---|---|---|
| DR1 `@math.sqrt` | `grep -rn '@math\.sqrt' --include=*.mbt src` → 0 行，exit **1** | `src/math_seam/violation_tmp.mbt` 写 `@math.sqrt(x)` → 命中 1 行，exit **0** | 若合法代码被命中 → 确认是否仅注释提及（注释须改描述形态） |
| DR2 `@math.ln(` | 对 `src/` → 0 行；参照清单（探针，不在扫描域）代码 3 处 + 注释 4 处 | 注入 `@math.ln(x)` 且无 `non-native fallback` → 带标记命中行数 = **0** | 检查标记是否在同一函数内 |
| DR3 `extern "C" fn c_cos/c_sin` | `grep -rnE 'extern "C" fn c_(cos\|sin)' --include=*.mbt src` → 0 行，exit **1** | 注入 `pub extern "C" fn c_cos(...) = "cos"` → 命中 1 行，exit **0** | 同上 |
| DR4 `is_ascii_uppercase` | `grep -rn 'is_ascii_uppercase' --include=*.mbt src` → 0 行，exit **1**；`grep -rn -e unicode-data -e moonbitlang/x --include=moon.pkg src` → 0 行，exit **1** | 注入 `c.is_ascii_uppercase()` → 命中 1 行，exit **0** | 若合法代码被命中 → 确认是否用于 ASCII 快速路径（也违规） |
| DR5 `Map::from_array` | 同 C-A4（探针产物 0 命中，exit 0）；产品 `src/data/profiles.mbt` 未生成 → **未做 T1** | 同 C-A4 的 T2（注入 → exit 1） | 同 C-A4 |
| DR6 core `@fs` | `grep -rn '"moonbitlang/core/fs"' --include=moon.pkg src` → 0 行，exit **1**；参照：实际 import 为 `moonbitlang/async/fs` | 写 `"moonbitlang/core/fs"` 到 `src/core/moon.pkg.tmp` → 命中 1 行，exit **0** | 若误报 → 确认上游是否新增 core fs 包 |
| DR7 `derive(Show)` | `grep -rn 'derive(Show)' --include=*.mbt src` → 0 行，exit **1**；`moonc` 实测告警原文见 §7 DR7 | 注入 `derive(Show)` → 命中 1 行（`src/core/v7.mbt:1`），exit **0** | 若 moonc 升级后不再 deprecated → 追加新行替代（append-only） |
| **DR8 跨包别名** | 代码块见 §10.6 命令 4；对 `probes/embed-probe` → **0 行**（v1 的裸词边界形态命中 111 行合法 `@data.`，属假红；v5 起该形态已弃用）；对 `src/` → 0 行，exit **1** | 注入 `data.entry_count("af")`（无 `@`）→ 命中 1 行，exit **0** | 若合法 `@data.` 被命中 → 正则的前缀类写错 |
| **DR9 条件编译** | 代码块见 §10.6 命令 1。**非空包基线**：先放 `pub fn noop() -> Unit { () }` 到 `src/core`，跑出 rc=1（0 行）后删除。带合法标识符 `target_lang()` + 中文注释「目标」的样本 → rc=1（不假红，v2 的裸词形态同样本 rc=0 命中 2 行） | 写 `#cfg(wasm)` → 命中 1 行，exit **0**；写 `#cfg(js)` 同样 exit **0**（v2 形态对二者均 rc=1 漏检） | 若合法代码被命中 → 确认是否在注释中（注释须改描述形态） |
| DR10 运行期平台 API 调用 | 代码块见 §10.6 命令 2；非空包基线 rc=1。**假红对照（N-18）**：`pub fn is_wasm_compatible()` + `pub fn get_target_name_of(...)` → 新式 rc=**1**（0 行），v3 裸词形态同样本 rc=**0** 命中 2 行 | 写 `is_wasm()` 调用 → 命中 1 行，exit **0** | 若误报 → 确认是否真的以调用形态出现 |
| DR11 反向模块依赖 | 代码块见 §10.6 命令 3；对三个基础包 `moon.pkg` → 0 行，exit **1**（N-09：写入反向 import 后 `moon check` 仍 rc=0，编译器不拦） | 在 `src/data/moon.pkg` 写 `"vicoproplus/langdetect/src/core"` → 命中 1 行 | 若误报 → 确认检索式是否匹配合法依赖 |

> **T2 构造后已清理**：所有 `violation_tmp.mbt` / `v7.mbt` / `moon.pkg.tmp` / `zz_*.mbt` 均在同一次 shell 内删除；清理后 `moon check` 输出 `Finished. moon: no work to do`（exit 0）。
### 10.5 门禁命令的接入位置

| 门禁 | 接入位置 | 失败退出码 |
|---|---|---|
| 约定 A / B / C 全部命令 | 产品仓库 CI（构建前）+ 代码审查清单 | 非 0 即阻断 |
| 方言红线 DR1-DR11 | 代码审查清单 + pre-commit 钩子（**从 §10.6 代码块复制，不用表格单元格形态**） | 非 0 即阻断 |
| `expected.json` md5（C-C6） | 每次比对前后各跑一次 | 非 0 即说明基准被改 |

---

### 10.6 代码块命令清单（N-02：可复制执行形态）

> 本节把 §7 / §9 / §10 中所有曾以 Markdown 表格单元格形式出现的命令，逐条写成**代码块形态**；每条命令不含 `|`（用 `-e` 多模式或字符类替代），可逐字复制执行。`# rc=` 为 2026-10-21 实跑记录。
>
> **执行环境（N-02 / N-17）**：命令须在 POSIX shell 下执行，且 `grep` 支持 `-E` 交替、`--include`、`-e` 多模式与 `[[:space:]]`。**不写死任何 grep 发行版或安装路径**——改为下面这条**能力自检**（失败即 rc=2，不进入后续命令）：
>
> ```bash
> printf 'a\n' | grep -qE 'a|b' || exit 2
> printf ' a\n' | grep -qE '^[[:space:]]*a' || exit 2
> printf 'x\n' | grep -q -e x -e y || exit 2
> mkdir -p /tmp/selfchk/sub && printf 'z\n' > /tmp/selfchk/sub/f.mbt
> grep -qr 'z' /tmp/selfchk || exit 2
> grep -rn --include=*.mbt 'z' /tmp/selfchk | grep -q 'f.mbt' || exit 2
> printf 'q(is_wasm())\n' > /tmp/selfchk/p.txt
> grep -qE '(^|[^[:alnum:]_])(is_wasm)[[:space:]]*[(]' /tmp/selfchk/p.txt || exit 2
> printf 'name = "z"\r\n' | tr -d '\r' | grep -q '^name = "z"$' || exit 2
> rm -rf /tmp/selfchk
> echo "SELFCHECK_OK"
> # 实测输出 SELFCHECK_OK / rc=0（2026-10-21）；探针覆盖 -qE 交替、[[:space:]]、-e 多模式、-r、--include、(^|[^…]) 前缀类、CRLF 归一
> ```
>
> 下表 `# rc=` 均为**通过上述自检的环境**下实测值。
>
> **EC1 通道可用性（Fail-5）**：
>
> | 通道 | 版本（实测命令输出） | 可用性 | 验证命令 |
> |---|---|---|---|
> | `grep`（默认 shell） | harness 直接调用打印 `grep (pi-uu-grep) 0.2.0`；`bash -c` 内解析到 `/usr/bin/grep` = `grep (GNU grep) 3.11` | **可用**（三种 grep 均通过下方自检） | `grep --version \| head -1` |
> | `grep`（Git Bash 工具集） | `D:/Program Files/Git/usr/bin/grep.exe` = `grep (GNU grep) 3.0` | **可用，但有方言限制**：该版本把 ERE 里的 `\(` 判为 `Unmatched ( or \(` 并 exit 2 → **全部正则已改用 `[(]` 字符类** | 复制该 exe 到仓库内执行 `./grep.exe --version` |
> | `md5sum` | `md5sum 0.8.0`（默认 shell）/ `md5sum (GNU coreutils) 9.4`（WSL） | **可用** | `md5sum --version \| head -1` |
> | `awk` | `GNU Awk 5.4.1`（默认）/ `GNU Awk 5.2.1`（WSL） | **可用** | `awk --version \| head -1` |
> | `bash` | `GNU bash 5.2.21`（WSL）；Git Bash 为 `5.3.15 (x86_64-pc-cygwin)`（本 shell 无法直接 exec 该 bash.exe，仅取版本字符串） | **可用** | `bash --version \| head -1` |
> | `moon` / `moonc` | `moon 0.1.20261012 (748b63c)` / `moonc v0.10.15+943464bfa` | **可用** | `C:/Users/Administrator/.moon/bin/moon.exe --version` |
> | `python` | `.venv` 内 `Python 3.12.10` | **可用（必须用 `.venv/Scripts/python.exe`，系统 python 无依赖）** | `.venv/Scripts/python.exe -V` |

> **多环境实测（2026-10-21）**：
>
> | 环境 | grep | 结果 |
> |---|---|---|
> | 默认 shell（harness，`bash -c` 内） | GNU grep 3.11 | §10.6 每条命令的 rc 与其注释一致（逐条见该节代码块） |
> | Git Bash 工具集（`grep.exe`，GNU grep 3.0） | GNU grep 3.0 | 与默认 shell 逐条一致。**注意**：原 `\(` 形态在该版本 exit 2（`Unmatched ( or \(`），改用 `[(]` 后通过 |
> | WSL bash + `/usr/bin/grep` | GNU grep 3.11 | 各命令的命中行数与默认 shell 逐条一致（应 0 行的仍 0 行；`moon.mod` / `pkgtype` 校验均 MATCH；命令 29 输出 0/0 字节）。**退出码在该宿主包装下不可观测**（`false` 亦返回 0），故只比对 stdout |

```bash
# 命令 1：DR9 条件编译（src/core）—— 期望 0 行 / rc=1
grep -rnE '^[[:space:]]*#(cfg|if)[[:space:]]*[(]' --include=*.mbt src/core
# rc=1（非空包基线：先放 pub fn noop() -> Unit { () } 到 src/core 再跑）

# 命令 2：DR10 运行期平台 API（src/core）—— 期望 0 行 / rc=1
# 语法锚定「调用形态」；用 (^|[^[:alnum:]_]) 前缀类而非 \b（\b 是 GNU 扩展，残缺 grep 会当字面 b，见 N-20）
grep -rnE '(^|[^[:alnum:]_])(is_wasm|target_name)[[:space:]]*[(]' --include=*.mbt src/core
# rc=1（T1 基线：放 pub fn is_wasm_compatible() -> Bool { true } 与 get_target_name_of(...) → 仍 rc=1；
#        T2：写 is_wasm() 调用 → rc=0 命中 1 行）

# 命令 3：DR11 反向模块依赖 —— 期望 0 行 / rc=1
grep -rn -e 'vicoproplus/langdetect/src/core' --include=moon.pkg src/data src/unicode src/math_seam
# rc=1

# 命令 4：DR8 跨包调用未加 @ 前缀 —— 期望 0 行 / rc=1
grep -rnE '(^|[^@[:alnum:]_])(data|math|fs)\.[a-z_]+[(]' --include=*.mbt src
# rc=1

# 命令 5：DR1 @math.sqrt —— 期望 0 行 / rc=1
grep -rn '@math\.sqrt' --include=*.mbt src
# rc=1

# 命令 6：DR3 自行绑定 cos/sin —— 期望 0 行 / rc=1
grep -rnE 'extern "C" fn c_(cos|sin)' --include=*.mbt src
# rc=1

# 命令 7：DR4 is_ascii_uppercase —— 期望 0 行 / rc=1
grep -rn 'is_ascii_uppercase' --include=*.mbt src
# rc=1

# 命令 8：DR4 第三方 Unicode 包 —— 期望 0 行 / rc=1
grep -rn -e unicode-data -e 'moonbitlang/x' --include=moon.pkg src
# rc=1

# 命令 9：DR6 core @fs 包 —— 期望 0 行 / rc=1
# 注：`--include=moon.pkg` 只匹配文件名为 moon.pkg 的文件；T2 须写进真实的 moon.pkg（写 .tmp 不会命中）
grep -rn '"moonbitlang/core/fs"' --include=moon.pkg src
# rc=1（T2：把 `"moonbitlang/core/fs",` 写进 src/core/moon.pkg → rc=0 命中 1 行，随后还原）

# 命令 10：DR7 derive(Show) —— 期望 0 行 / rc=1
grep -rn 'derive(Show)' --include=*.mbt src
# rc=1

# 命令 11：NE1 静态（排除 cmd）—— 期望 0 行 / rc=1
grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam | grep -vE '[\\/]cmd[\\/]'
# rc=1

# 命令 12：L1-A1 网络/写文件副作用 —— 期望 0 行 / rc=1
grep -rn -e http -e socket -e write_file -e log_write --include=*.mbt src
# rc=1

# 命令 13：NE4-2 对内置数据的文件读取 —— 期望 0 行 / rc=1
grep -rn 'read_file' src
# rc=1

# 命令 14：NE4-4 第三方运行时依赖 —— 期望 0 行 / rc=1
grep -rn -e moonbit-community -e 'moonbitlang/x' --include=moon.pkg src
# rc=1

# 命令 15：C-C6 基准覆写检查 —— 期望 rc=0
test "$(md5sum docs/port/golden/expected.json | awk '{print $1}')" = "219519ee19d7cc10d404ddbdab3acd87"
# rc=0

# 命令 16：C-C2 基准规模（268=250+18）—— 期望 rc=0
.venv/Scripts/python.exe -c "import json;c=json.load(open('docs/port/golden/expected.json',encoding='utf-8'))['cases'];assert (len(c),sum(1 for x in c if x.get('detect_langs')),sum(1 for x in c if 'error' in x))==(268,250,18);print('ok')"
# rc=0

# 命令 17：C-C3 seed 双套 —— 期望 rc=0
.venv/Scripts/python.exe -c "import json;c=json.load(open('docs/port/golden/expected.json',encoding='utf-8'))['cases'];assert sorted({x['seed'] for x in c})==[0,42];print('ok')"
# rc=0

# 命令 18：C-C4 异常码 —— 期望 rc=0
.venv/Scripts/python.exe -c "import json;c=json.load(open('docs/port/golden/expected.json',encoding='utf-8'))['cases'];assert {x['error']['code'] for x in c if 'error' in x}=={5};print('ok')"
# rc=0

# 命令 19：C-C1/C5 prob_bits 形态 —— 期望 rc=0
.venv/Scripts/python.exe -c "import json,re;c=json.load(open('docs/port/golden/expected.json',encoding='utf-8'))['cases'];bad=[e for x in c for e in (x.get('detect_langs') or []) if not re.fullmatch(r'[0-9a-f]{16}',e['prob_bits'])];assert not bad;print('ok')"
# rc=0

# 命令 20：C-B1/B3/B4 U3 版本+码点+区间 —— 期望 rc=0
# 显式 for 循环（不用列表推导副作用 / 不碰 list.__setitem__，见 review-findings N-13）
.venv/Scripts/python.exe -c "exec('import sys,unicodedata\nassert sys.version.split()[0]==\'3.12.10\'\nassert unicodedata.unidata_version==\'15.0.0\'\ncps=[cp for cp in range(0x110000) if not (0xD800<=cp<=0xDFFF) and chr(cp).isupper()]\nassert len(cps)==1951\niv=[]\nfor cp in cps:\n    if iv and cp==iv[-1][1]+1:\n        iv[-1][1]=cp\n    else:\n        iv.append([cp,cp])\nassert len(iv)==651\nprint(\'ok 1951 cps / 651 intervals\')')"
# rc=0（实测输出：ok 1951 cps / 651 intervals）

# 命令 21：C-B6 无第三方 Unicode（含路径守卫）—— 期望 rc=0
test -d src || exit 2
test "$(grep -rl -e 'moonbitlang/x' -e unicode-data src | wc -l)" = "0"
# rc=0（路径缺失 → rc=2）

# 命令 22：C-A5 生成清单 mode —— 期望 rc=0
.venv/Scripts/python.exe -c "import json,sys;sys.exit(0 if json.load(open('probes/gen-manifest.json',encoding='utf-8'))['mode']=='flat' else 1)"
# rc=0

# 命令 23：C-A6 生成标记 —— 期望 rc=0
head -1 probes/embed-probe/lib/data/data.mbt | grep -q '勿手改'
# rc=0

# 命令 24：C-A3 产物字节数（参照样本）—— 期望 rc=0
test "$(wc -c < probes/embed-probe/lib/data/data.mbt | awk '{print $1}')" = "2205308"
# rc=0

# 命令 25：C-A4 禁止 Map 字面量（参照样本）—— 期望 rc=0
test "$(grep -c 'Map::from_array' probes/embed-probe/lib/data/data.mbt)" = "0"
# rc=0

# 命令 26：门禁表行数派生（不派生通过数）—— 期望 25
awk '/^### 10\.[1-4]/,/^### 10\.5/' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -cE '^\| \*{0,2}(C-|DR)'
# rc=0

# 命令 27：产品公开符号数（应为 0，产品未实现）
grep -rn '^pub fn' --include=*.mbt src
# rc=1（0 行 = 产品无实现）

# 命令 28：moon.mod name 字面（N-03 / N-11）—— 期望 rc=0
# moon.mod 为 CRLF 行尾，必须先 tr -d '\r'，否则 $ 锚点匹配不到 \r 前的字符
tr -d '\r' < moon.mod | grep -q '^name = "vicoproplus/langdetect"$'
# rc=0（T2：把 name 改成 "x/y" → rc=1）

# 命令 29：NE1 运行时（cmd/main 静默性）—— 期望 rc=0
# 五态守卫（字节计数；不用 $(...) 因为命令替换会吃掉尾部换行，见 N-19）：
#   ① 二进制缺失 → 2；② 空 fn main → 0；③ println("x") → 1；④ println("") → 1；⑤ 只输出单个换行 → 1
# （v3 形态 `wc -c` 无断言，二进制缺失时也输出 0，属永久绿，见 review-findings N-10）
test -x ./_build/native/debug/build/src/core/cmd/main/main.exe || exit 2
./_build/native/debug/build/src/core/cmd/main/main.exe >/tmp/o.txt 2>/tmp/e.txt || exit 1
test ! -s /tmp/o.txt && test ! -s /tmp/e.txt
# rc=0（五态实测见 §10.6 的 T2 表）

# 命令 30：cmd/main 可执行包形态（N-03）—— 期望 rc=0
grep -q 'pkgtype(kind: "executable")' src/core/cmd/main/moon.pkg
# rc=0
```

**T2 违规样本实录（逐条构造后已清理，2026-10-21）**

| 命令 | 违规样本 | rc |
|---|---|---|
| 命令 1（DR9） | `src/core/zz_t.mbt` 写 `#cfg(wasm)` | **0**（命中 1 行） |
| 命令 1（DR9） | `src/core/zz_t2.mbt` 写 `#cfg(js)` | **0**（命中 1 行） |
| 命令 2（DR10） | `src/core/zz_t3.mbt` 写 `is_wasm()` | **0**（命中 1 行） |
| 命令 4（DR8） | `src/core/zz_n.mbt` 写 `data.entry_count("af")`（无 `@`） | **0**（命中 1 行） |
| 命令 5（DR1） | `src/math_seam/violation_tmp.mbt` 写 `@math.sqrt(x)` | **0**（命中 1 行） |
| 命令 3（DR11） | `src/data/moon.pkg` 写 `"vicoproplus/langdetect/src/core"` | **0**（命中 1 行） |
| 命令 6（DR3） | `src/math_seam/vt.mbt` 写 `extern "C" fn c_cos(...) = "cos"` | **0**（命中 1 行） |
| 命令 7（DR4） | `src/core/zz_t.mbt` 写 `c.is_ascii_uppercase()` | **0**（命中 1 行） |
| 命令 9（DR6） | `src/core/moon.pkg` 写 `"moonbitlang/core/fs",` | **0**（命中 1 行；写 `.tmp` 不会命中——`--include=moon.pkg` 只匹配该文件名） |
| 命令 10（DR7） | `src/core/v7.mbt` 写 `derive(Show)` | **0**（命中 1 行） |
| 命令 11（NE1） | `src/core/zz_n.mbt` 写 `println("x")` | **0**（命中 1 行） |
| 命令 29（NE1 运行时）① 二进制缺失 | `mv` 走 `main.exe` | **2** |
| 命令 29 ② 空 `fn main { }` | 现有脚手架 | **0** |
| 命令 29 ③ `fn main { println("x") }` | 打印 1 行 | **1** |
| 命令 29 ④ `fn main { println("") }` | **本机实测输出 0 字节 → 判 0**（`wc -c`=0、`od -c` 空）；reviewer 环境实测 **2 字节（`\r\n`）→ 判 1**。该态结果**依赖 `println` 的换行实现**，故不作为唯一覆盖——确定性覆盖由 ⑥ 的 1 字节样本承担 |
| 命令 29 ⑤ `fn main { print("") }` | 语法不支持（`print` 未绑定，`[4021]`），改用 ④ 的 `println("")` 形态 | 不适用 |
| 命令 29 ⑥ 只输出单个 LF（1 字节） | 1 字节样本文件 `one.bin`（`b"\n"`）模拟程序输出 | **1**（v5 字节计数形态）。**对照**：同一 1 字节输出下 v4 的 `out=$(...)` 形态判 **PASS（假绿）**——命令替换吃掉了尾部换行，`test -z` 看到空串。实测记录：`out=$(cat one.bin); test -z "$out"` → PASS（假绿）；`cat one.bin > o.bin; test ! -s o.bin` → FAIL（正确拦截） |
| 命令 15（C-C6） | 复制基准追加 1 字节后同命令比对 | **1** |
| 命令 21（C-B6） | `src/unicode/moon.pkg.tmp` 写 `"moonbit-community/unicode-data"` | **1** |
| 命令 28（moon.mod name） | `name = "x/y"` | **1**（`grep -q` 不匹配） |

**N-01 的假红对照（v2 旧式 vs v3 新式）**

| 样本 | v2 旧式 `grep -rnE 'target|#if|platform'` | v3 命令 1 |
|---|---|---|
| `pub fn target_lang() -> String { "en" }` + 注释「目标」 | rc=**0**（命中 1 行，假红） | rc=**1**（0 行，正确） |
| `#cfg(wasm)` | rc=**1**（0 行，漏检） | rc=**0**（命中 1 行，正确） |

> **NE1 的 cmd 例外（BLK-10 修正）**：命令 11 用 `grep -vE '[\\/]cmd[\\/]'` 排掉 `cmd/` 路径段（同时兼容 `\` 与 `/`）。实测：`println` 放进 `src/core/cmd/main/main.mbt` → 命令 11 **rc=1（0 行）**；放进 `src/core/zz_n.mbt` → **rc=0（命中 1 行）**。

## 11. 契约可实现性互查（MS1-MS2）

枚举 7 类约束性条款：① 导出面；② 错误码封闭域；③ 承载约束；④ 机检档位；⑤ 声明面；⑥ 字面闭集；⑦ 目录所有权。

| # | 冲突对 | 是否撞 | 裁决（已落回条款） |
|---|---|---|---|
| MS1-1 | ① × ⑦ | 否 | 导出面是符号级，目录所有权是落点级；落点见 §4A。 |
| MS1-2 | ② × `[EXT]` 四字段异常 | 否 | 四字段扩展**异常对象形状**，不改 9 个码值与消息原文；码域仍封闭（§6）。 |
| MS1-3 | ③（零第三方依赖）× native 需 libm `log` | 否 | `log` 是 C 标准库符号（ISO/IEC 9899 `<math.h>`），由平台数学库解析，非第三方 MoonBit 包。依据 DESIGN G2 XB1（证据等级 A）。 |
| MS1-4 | ③ × js / wasm-gc 需 `log` | 否（降级路径） | 该两目标走 `@math.ln`（标准库），已按 G3 FE2 声明为**非等价降级**；影响量化见 V-35。落点：§8.4 容差档 + EQ1。 |
| MS1-5 | ④（native 位级）× ⑤（js/wasm-gc 容差） | 否 | 按目标分栏（§8.4）。 |
| MS1-6 | ⑥（DR 表 grep）× 文档/注释提及被禁字面 | 可能撞 | **裁决已落回 §7 总则**：检索面 = `src/`；`docs/`、`probes/`、`_build/`、`.mooncakes/` 不在扫描域；产品注释须用描述形态。 |
| MS1-7 | ⑦ × 生成物 | 否 | 生成物落 `src/data/`、`src/unicode/`，覆盖行为与不手改清单见 `约定 A` §4、`约定 B` §5。 |
| MS1-8 | ④（位级）× 跨平台 libm | 可能撞 | **裁决已落回 §8.4**：位级档限定 `native (win32 x64)`；`native (其他平台)` 与 `js / wasm-gc` 均按容差档。 |
| MS1-9 | ② × 低置信入口不抛码 5 | 否 | 低置信入口是独立入口（§5.3），其契约明确「不抛码 5」；主 API 仍抛。 |
| MS1-10 | ① × 接缝入口导出 | 否 | 接缝导出为可测性（TD1-TD3），README 不列为公开 API。 |
| MS1-11 | ② × NaN 先验（V-51） | 否 | NaN 不触发码 8（`p < 0` 对 NaN 为假），走「空概率 → `'unknown'`」路径；已写入 §5.6 与 NE4-3 的例外声明。 |

**结论**：11 对候选中 0 对真冲突；2 对「可能撞」均已落回条款（MS1-6 → §7 总则；MS1-8 → §8.4 平台列）。

---

## 12. 文档契约纪律（DC-A…DC-G）

| 项 | 自查结果 |
|---|---|
| **DC-A 稳定标识引用** | 跨文档引用一律用编号（`V-XX`、`FR-XX`、`US-XX`、`A1`/`B3`/`C2`、`DR1-DR11`、`MS1-1`）或文档**完整标题**；**禁止**裸行号作契约锚。**如实登记（v3 补全，SF-11 余项）**：`file:line` 出现在 §1 事实表（事实源）、§2 Gap 表 Source side 列（事实源）、§2A 测试对齐表（源文件路径）、§4.1/§4.2/§4.3 权威源列（上游口径定位）、§4.4 权威源（上游口径定位）、§7 DR 表权威出处列（方言事实源）、§9.3 层 3 写读位置列（副作用事实源）、**§10.4 的 T2 实录列（构造样本路径 `violation_tmp.mbt:N`、`v7.mbt:N` 与参照 import 行）**、**§10.6 的 T2 表（同上）**、**§13 的 R1 理由（`probes/gen_mbt.py:80`、`rand-probe.mbt:203`）**——以上**全部是事实源指针**（可重跑复查），**不是契约锚**；契约锚只用编号。 |
| **DC-B 状态唯一陈述** | 本文唯一文档状态区 = 文档头「状态：生效」。§8 的「未验证」是**验收行状态**（逐行），不是文档状态。 |
| **DC-C 完成断言载体** | 所有「已试跑」断言同行带命令 + 日期（2026-10-21）+ 输出（§10 各表）。§8 中未跑的行明确标「未验证」并填 `—`。 |
| **DC-D 数字机检派生** | 正文计数全部指向 `V-XX` 或由表格行数派生；**已删除 §15 的手写合计**（v1 的 T1/T2 合计与分组相加不符，见 BLK-02）。现 §15 只给「逐行状态指针」与一条行数派生命令。 |
| **DC-E 双形态契约** | 已裁决：档案编码唯一权威 = `约定 A：档案内嵌数据格式与生成契约` v1；`probes/gen_mbt.py` 为参考实现（DESIGN G7）。 |
| **DC-F 复审发现登记表** | 登记表 = `docs/superpowers/specs/202610202129-moon-langdetect-语种检测-review-findings.md` §4；v2 已逐条填「销项证据」与状态。 |
| **DC-G 仓规先读** | ① `validate_prd.py` 的 `FILENAME_RE` 只约束 PRD（对 design/spec 路径实测 exit 1 属预期）；② 仓库根非 git（`git rev-parse --show-toplevel` exit 128），无 `.gitignore` 约束；③ `probes/*/.gitignore` 只忽略 `_build/ target/ .mooncakes/ .moonagent/`；④ 既有脚本写入面仅 `docs/port/golden/`；⑤ **v2 新增**：根模块与嵌套探针模块共存已实测（V-56），故模块根可设在仓库根。 |

---

## 13. 红线段（R1-R4）

**判断：N/A —— 本任务是新建 MoonBit 库（产品侧 `src/` 当前 0 个公开符号），不修改任何既有 MoonBit 代码。**

| 编号 | 检查项 | 结论 | 理由 |
|---|---|---|---|
| R1 | 既有违规 | **N/A** | 产品侧无代码（§2 枚举命令对 `src/` 输出 0 行）；`probes/` 下为取证探针，不属产品契约面，且其中确实存在 `Map::from_array`（`probes/gen_mbt.py:80`）与 `@math.ln`（`probes/rand-probe/rand-probe.mbt:203` 等 3 处代码）——这是**探针合法用法**（对照实验需要），不受产品红线约束（§7 总则已把 `probes/` 排除出检索面）。 |
| R2 | 兼容性破坏 | **N/A** | 无既有调用方（新包）。 |
| R3 | 数据迁移 | **N/A** | 无既有数据；55 个档案是只读输入。 |
| R4 | 依赖替换 | **N/A** | 无既有依赖；上游 Python 包仅作只读参照。 |

> 若未来把 `probes/` 代码提升为产品代码，R1 **立即生效**：那时代码里的 `Map::from_array` 与 `@math.ln` 调用必须按 DR5/DR2 处理。

---

## 14. 未决与 `[LOCAL_DEAD_LINK]`

> **标签语义（v5 明确，N-21）**：本 spec 中 `[LOCAL_DEAD_LINK]` **仅用于「本机环境不可达」的项**（如运行器坏、无官方运行时、跨平台未验证）。**实现期产物尚未就绪**（如尚未创建的比对脚本、尚未落地的测试文件）一律写「**未验证（实现期产物；回补触发 = …）**」，**不得**打 `[LOCAL_DEAD_LINK]`——二者混淆会让「还没写」伪装成「环境不允许」。

**`[LOCAL_DEAD_LINK]` 行数**：见下方派生命令（不手写）。U-08…U-12 为 §8 各环境不可达行的宿主项；「实现期产物未就绪」类**不**在本表（见本节开头的标签语义）。

| 编号 | 未决项 | 标签 | 分类 | 回补触发条件 | 处置 |
|---|---|---|---|---|---|
| U-01 | wasm-gc 目标的 `moon test` 结果 | `[LOCAL_DEAD_LINK]` | 能力未验证 | `moonrun.exe` 可正常启动的环境重跑同一套断言 | 只接受 `moon build --target wasm-gc` 退出码；README 声明「wasm-gc 实验性，仅保证构建」；§8 该行保持「未验证」 |
| U-02 | js 目标在官方 node 下的结果 | `[LOCAL_DEAD_LINK]` | 能力未验证 | 官方 node 可用后跑 `moon test --target js` | 当前结论来自 bun 替代运行时；验收记录标注运行时身份 |
| U-03 | mooncakes 服务端体积 / 文件数限制 | `[LOCAL_DEAD_LINK]` | 能力未验证 | 首次真实发布或小包试探 | 发布前用小包试探；保留按语言子集裁剪方案 |
| U-04 | js / wasm-gc 的概率容差数值 | `[LOCAL_DEAD_LINK]` | 指标未测 | 在两目标上实测概率差分布后登记 | `约定 C` §4 容差栏保持「待校准」；校准前只判 §8.1/§8.3 的结构项与准确率项 |
| U-05 | 跨平台 libm 位级一致性 | `[LOCAL_DEAD_LINK]` | 能力未验证 | 在目标平台跑全量对照 | 位级档限定 `native (win32 x64)`；其他平台按容差档（§8.4） |
| U-06 | 首次加载解析 184129 条的耗时 | `[LOCAL_DEAD_LINK]` | 指标未测 | 产品实现后实测 | §8.1 该行保持「未验证」 |
| U-07 | `str.isupper` 与 `Uppercase` 属性集合是否完全相等 | `[LOCAL_DEAD_LINK]` | 能力未验证 | 生成 U3 表时用 `str.isupper` 全码点实测口径核对 | `约定 B` 复开条件③ |
| U-08 | wasm-gc 首次调用完成档案加载 | `[LOCAL_DEAD_LINK]` | 能力未验证 | 同 U-01 | §8.1 wasm-gc 行：只接受 build |
| U-09 | 三目标可用语言数 / 条目合计一致性 | `[LOCAL_DEAD_LINK]` | 环境未验证 | 运行器与官方运行时可用 + 比对脚本落地 | §8.3 两行；wasm-gc 行按 U-01 处置 |
| U-10 | 三目标主语言一致性 | `[LOCAL_DEAD_LINK]` | 环境未验证 | 同 U-09 | §8.3 对应行 |
| U-11 | 其他平台位级一致 | `[LOCAL_DEAD_LINK]` | 能力未验证 | 同 U-05 | §8.4 native（其他平台）行 |
| U-12 | js / wasm-gc 容差档 | `[LOCAL_DEAD_LINK]` | 指标未测 | 同 U-04 | §8.4 js / wasm-gc 行 |

```bash
# 派生：本表带 [LOCAL_DEAD_LINK] 的 U 行数
grep -cE '^\| U-[0-9]+ .*\[LOCAL_DEAD_LINK\]' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
# 实测 12 / rc=0（派生值，不手算）
```

---

## 15. 门禁状态指针（不设手写合计）

v1 曾在此给 T1/T2 手写合计，与分组相加不符（review-findings BLK-02）。v2 删除合计；v3 修正口径错位（把「表行数」写成「命令行数」）；**v5 收尾**：本节**不再出现任何手写数字**，只保留两条派生命令的实测输出——「表行数」与「命令条数」是两个不同的量，合并行（如 B1/B3/B4 合为一行）使二者天然不等，因此分别派生、分别标注：

| 派生对象 | 派生命令（代码块形态） | 2026-10-21 实测 |
|---|---|---|
| 门禁**表行数**（§10.1–§10.4 的数据行，含合并行） | 见下方命令 A | **25**（派生命令实测输出） |
| 门禁**命令条数**（§10.6 代码块中的可执行命令） | 见下方命令 B（`grep -cE '^# 命令 [0-9]+：'`） | **30**（派生命令实测输出；不写手算数） |

```bash
# 命令 A：门禁表数据行数（只数行，不数通过数）
awk '/^### 10\.[1-4]/,/^### 10\.5/' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -cE '^\| \*{0,2}(C-|DR)'
# 实测 25 / rc=0（派生值，不手算）

# 命令 B：§10.6 代码块内的可执行命令条数
grep -cE '^# 命令 [0-9]+：' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
# 实测 30 / rc=0（派生值，不手算）

# 命令 C：§10.6 T2 表的数据行数
awk '/^\*\*T2 违规样本实录/,/^\*\*N-01 的假红对照/' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -cE '^\| 命令 '
# 实测 21 / rc=0（派生值，不手算）
```

**逐行状态指针**（不写合计；每条状态必须读对应表）：

- 逐行 T1/T2/T3 状态见 §10.1 / §10.2 / §10.3 / §10.4 四张表 + §10.6 代码块清单（每行/每条都有独立记录）。
- **未做 T1 的行**：§10.2 的 C-B2、C-B5（产物 `src/unicode/upper_table.mbt` 未生成）；§10.1 的产品侧 C-A1…C-A6 与 DR5 的产品侧（产物 `src/data/profiles.mbt` 未生成）。
- **未做 T2 的行**：§10.1 的产品侧 C-A1…C-A6、§10.2 的 C-B2/C-B5、DR5 的产品侧（均依赖未生成的产物）。
- **已做 T2 的行（v4 实录）**：§10.1 的探针产物侧 C-A1…C-A6；§10.2 的 C-B1/B3/B4 与 C-B6；§10.3 的 C-C1/C2/C3/C4/C6；§10.4 与 §10.6 的 DR1…DR11。构造物均已清理，`moon check` 复跑 exit 0。
- **§10.6 的命令**：T1 与 T2 的逐条状态见 §10.6 代码块内的 `# rc=` 注释与紧随其后的 T2 表；条数用派生命令（见下方命令 B）与 T2 表行数（见下方命令 C）读出，**不手写**。

> 上述派生只回答「登记了多少」，**不**回答「通过多少」——通过状态必须逐行读表（DC-D：禁止手写合计）。

---

**文档结束**
