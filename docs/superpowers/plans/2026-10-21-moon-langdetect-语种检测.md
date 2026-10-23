# moon_langdetect 语种检测 Implementation Plan
> **文档标题（机器可检索）**：`moon_langdetect 语种检测实施计划`
> **版本**：v5.1（2026-10-21）—— v4 已销项 v3 核验的 1 Blocking（N-08）+ 1 NOT CLOSED（N-05）+ 1 Blocking 级（N-09）+ 3 PARTIAL（N-01 / N-02 / N-04）；**v5 已销项 v4 核验的 N-09（js 口径闭环）+ N-12（C6 守卫验证条件说明）**。共 5 条 Spec vs Plan Discrepancies（D-01 ALIGN-SPEC；D-02 / D-03 / D-04 / D-05 均为 **修订 spec**，由 Task 0 Step 0 的四项机械 gate 强制）；**v5.1 新增「执行期易错点（Executor Pitfalls）」章节（命令 11/11b 同跑、命令 1-14 空集假绿）**
> **计划权威边界**：`Spec authority = rules/contracts/architecture; Plan authority = execution flow/schedule/checkpoints`；上游裁决见 `docs/port/architecture-decisions.md`，行为口径见 `docs/port/upstream-behavior-contract.md`。


## Goal
在 MoonBit 中实现与上游 Python `langdetect` 行为等价的纯计算语种检测库：native（win32 x64）按 `prob_bits` 位级一致验收，js / wasm-gc 按 spec §8.4 分档验收（js 结构 + 准确率，wasm-gc 仅构建）；同时交付 `约定 A：档案内嵌数据格式与生成契约`、`约定 B：U3 Unicode 大小写表生成契约`、`约定 C：golden 基准消费契约` 所要求的生成器、产物与比对设施。

## Architecture
按 spec §0A D2：`src/core/` → {`src/math_seam/`, `src/unicode/`, `src/data/`} → 标准库，单向无环。`src/math_seam/` 是唯一平台分叉点（native = libm `log`；js / wasm-gc = `@math.ln`，带 `// non-native fallback` 标记）；`src/unicode/` 承载 U3 区间表、`is_upper_cp312` 与 `unicode_block`（spec §2A 落点）；`src/data/` 以编译期内嵌扁平字符串承载 55 个档案并在运行时解析为计数/概率表；`src/core/` 承载清洗、特征抽取、7 轮随机更新、Neumaier 归一化、公开 API 与 9 码错误类型。数据流：内嵌档案 → 解析 → 计数 → 概率表 → 特征 + 随机更新 → 归一化 → 阈值过滤 + 稳定排序 → 结果条目数组。

## Tech Stack
- MoonBit 工具链：`moon 0.1.20261012 (748b63c)` / `moonc v0.10.15+943464bfa` —— 溯源 spec §10.6 EC1 行 861。
- Python：`.venv/Scripts/python.exe` = Python 3.12.10 —— 溯源 spec §10.6 EC1 行 862；`unicodedata.unidata_version == 15.0.0` —— spec §10.6 命令 20。
- 零第三方 MoonBit 包依赖 —— spec §0A D3；ADR P 行；C 标准库 `log` 不算第三方包（spec §11 MS1-3）。
- 档案承载：编译期内嵌扁平字符串（`key\tcount\n`）—— `约定 A：档案内嵌数据格式与生成契约` v1；spec §4A 行 415。
- U3 区间表：CPython 3.12.10 生成 —— `约定 B：U3 Unicode 大小写表生成契约` v1；spec §4A 行 416。
- golden 消费：`prob_bits` IEEE754 大端 16 位 hex —— `约定 C：golden 基准消费契约` v1；`docs/port/golden/expected.json` md5 `219519ee19d7cc10d404ddbdab3acd87`（spec V-22，本计划实测复核一致）。
- 错误表达：`suberror` + 标签载荷 —— spec §5.8 / V-57。
- 根模块：`moon.mod` 的 `name = "vicoproplus/langdetect"`、`version = "0.1.0"` —— spec §4A 行 410；本仓库 `moon.mod:1-2` 实测一致。

## Global Constraints
- 不修改 PRD / DESIGN / SPEC / 三份约定 / `docs/port/` / `langdetect/`；`docs/port/golden/` 是只读证据区，产品代码与生成器不得写入。
- `src/core/` 禁止条件编译与运行期平台判断（spec §7 DR9 / DR10）；平台差异仅允许存在于 `src/math_seam/`。
- 禁止 `@math.sqrt`、禁止自行绑定 `cos`/`sin`、禁止 `is_ascii_uppercase`、禁止第三方 Unicode 包、禁止 `Map::from_array` 承载档案、禁止 `derive(Show)`、禁止 core `@fs`、禁止反向模块依赖（spec §7 DR1-DR11）。
- 库零网络、零存储写、零日志、零文件读取；`src/core/cmd/main` 静默（spec §9.1 L1-A1、§9.4 NE1 / NE4）。
- 任何多步命令链一律以失败即中止连接符（`&&`）串联，禁止 `;`、`|| true`、忽略错误（Slice-Checkpoint-Gate S4）。
- 整体判定：任一维度、任一行失败即整体验收失败，不得以其他维度通过抵扣，不得把某维度标「不适用」规避（spec §8 表头）。
- 数值权威形态：native 只比 `prob_bits`，不比 `prob` / `prob_repr`（`约定 C` C1 / C5）。

## Granularity & Consensus Declaration (MANDATORY)
- **Spec 层级**: `N/A — this plan is based on a single spec`（`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md` v5.1，单份 spec，未拆层级）。
- **Plan 颗粒度**: 本 plan 仅含具体执行 task（Files / Interfaces / Steps / Output / 时长与轮次上限），不含实现代码；函数体、伪代码一律不写入。
- **同级 plan 共识点**: `N/A — 单 spec，无同级 plan`。

## Environment Assumptions & Verification (MANDATORY)
- **E1 构建入口**: 假设 = 产品唯一规范构建入口是仓库根的 `moon`。核实：`moon.mod:1-2` 存在（`name` / `version`）；spec §4A 行 410 记录「根模块与嵌套探针模块共存已实测」（V-56：`moon check` exit 0）。探针工程 `probes/embed-probe` 是独立模块，不作为产品入口。结论：✅ 单入口成立；所有验收命令写 `moon`，不写机器绝对路径。
- **E2 工具链版本**: 核实：spec §10.6 EC1 行 861 记录 `moon 0.1.20261012` / `moonc v0.10.15+943464bfa`；EC1 行 862 记录 Python 3.12.10 且必须用 `.venv/Scripts/python.exe`。Task 0 必须实测 `moon --version`、`moonc --version`、`.venv/Scripts/python.exe -V` 并落日志。结论：✅ 以 Task 0 实测值为准，实测前不写成断言。
- **E3 运行环境**: native（win32 x64）= 位级档；js = bun 替代运行时（spec V-25）；wasm-gc = 仅 build（spec V-26）；其他平台 = 容差档（spec §8.4 + MS1-8）。结论：✅ 已登记，Task 11 按此分档。
- **E4 验收命令可移植性**: spec §10.6 的 30 条命令均使用相对路径与标准工具，无机器绑定绝对路径；构建命令统一 `moon`（PATH），并前置 `command -v moon || exit 2` 守卫。结论：✅ 可移植。
- **E5 编译探针 Task 0**: 产品模块在 js / wasm-gc 的首次构建未验证。按用户裁决：Task 0 = 只读全量基线（不改产品代码），Task 1 = 三目标最小编译探针，且 Task 1 必须先于任何功能编码。结论：✅ 探针先于功能编码；探针失败触发决策门（补环境 / 换方案 / ASK-USER），禁止进入 Task 2+。
- **E6 既存状态假设**: 假设 = `docs/port/golden/expected.json` 存在且 268 例、55 个档案、探针工程 56/56、`.venv` 可用。核实：本计划实测 `md5 = 219519ee19d7cc10d404ddbdab3acd87`、`(268, 250, 18)`、seed `{0, 42}`；spec V-14 / V-19 / V-24。无凭证 / 登录态 / 预置账号假设。结论：✅ Task 0 逐条实跑后生效；失败则登记 fallback 并触发决策门。
- **E7 验收观测通道**: 通道 = ① `moon test` stdout（探针日志 `probes/logs/target-native-02-test.log`，spec V-24）；② `tools/compare_golden.py` 的 stdout 与退出码；③ CLI stdout/stderr 字节计数（spec 命令 29）；④ 任务日志文件。Task 0 实测 ①④，Task 2 实测 ②，Task 9 实测 ③；任一不可用则改判据并显式裁决。结论：✅ 计划期先自检，禁止执行期现场试错。

## Baseline Declaration (MANDATORY)
- **Step 0 = Task 0**：在干净工作区全量运行 spec §10.6 的 30 条命令 + `moon check` + 根 `moon test --target native` + `probes/embed-probe` 的 `moon test --target native`，逐条记录命令 / 退出码 / 关键输出 / 代码版本标识（`moon --version` + `moon.mod` 内容 + `src`/`tools` 文件清单 sha256），写入 `docs/superpowers/plans/artifacts/baseline-2026-10-21.md`。基线记录未落档前禁止进入 Task 1 之后的功能编码。
- **预期基线（红绿）**：命令 1-14 期望 0 命中 / rc=1；命令 15-26、28、30 期望 rc=0；命令 27 期望 rc=1（产品 0 个 `pub fn`，spec §4A 行 427 如实状态）；**命令 29 期望 rc=0**（`_build/native/debug/build/src/core/cmd/main/main.exe` 已存在且为空 `fn main` → 静默）。命令 29 的 rc=0 为 v1 评审 B-03 实测值（`rc29=0`），与本文件命令 29 注释「② 空 fn main → 0」及 Task 12 期望值一致。
- **基线缺陷登记与处置**：
  - B-01 命令 29 基线 **rc=0**（空 `fn main` 静默）→ **不是缺陷**；Task 9 的职责是「填入 detect 调用后**仍保持** rc=0」，Task 9 Output 必须复跑命令 29 并断言 rc=0。
  - B-02 命令 27 rc=1（0 个产品公开符号）→ 本计划 Task 3-8 修复。
  - B-03 **命令 1-14 全部**依赖非空扫描面；在当前空 `src/` 上其「0 命中」是**空集假绿**（spec §7 注：DR9/DR10/DR11 的 T1 基线必须是非空包；命令 5-8 / 12-14 同理依赖扫描面存在）→ Task 6 首个 `.mbt` 落地后立即整体复跑 1-14，复跑结果写入 `task6-core-base-2026-10-21.log`；空集态与实跑态必须分列记录。
- **回归判定以基线为参照**：每次门禁复跑与基线逐项比对——基线绿项变红归因本轮改动；基线红项漂移逐项登记归因；新失败与基线失败分离统计（衔接 Fix-Loop-Discipline R10）。
- **基线时效**：共享配置（`moon.mod`、`src/*/moon.pkg`、常量表、生成器）变更或大规模合入后必须重跑刷新基线，禁止沿用过期基线。
- **降级口径**：若某命令本机不可执行（例如 `md5sum` 缺失），预先登记降级替代命令（`.venv/Scripts/python.exe` + `hashlib.md5` 读取同名文件）与记录方式，并在验收记录标注「降级执行 + 降级原因」；禁止静默跳过或死等。

## Carry-over Reconciliation Declaration (MANDATORY)
登记表 = `docs/superpowers/specs/202610202129-moon-langdetect-语种检测-review-findings.md` §14（U-01…U-12）。全表逐行对账如下，12 个编号全部出现且均映射本计划任务号 + 验收判据。

| 登记项标识 | 摘要 | 判定 | 归属任务号 + 验收判据 |
|---|---|---|---|
| U-01 | wasm-gc 目标的 `moon test` 结果 | 承接 | Task 11：只判 `moon build --target wasm-gc` rc=0，test 结果不作交付证据；回补手册 M-01 |
| U-02 | js 目标在官方 node 下的结果 | 承接 | Task 11：本机仅 `moon build --target js` rc=0；`moon test --target js` 与 `compare_golden --target js` 一律标 `[LOCAL_DEAD_LINK]`（U-02 / M-02），异地执行，本机不得判绿；回补手册 M-02 |
| U-03 | mooncakes 服务端体积 / 文件数限制 | 承接 | Task 12：`moon package` 产物字节数与文件数落档，不执行真实发布；回补手册 M-03 |
| U-04 | js / wasm-gc 的概率容差数值 | 承接 | Task 11：`--mode prob_tolerance` 只记录不判绿，容差栏保持待校准；回补手册 M-04 |
| U-05 | 跨平台 libm 位级一致性 | 承接 | Task 11：位级档限定 native(win32 x64)，其他平台只登记；回补手册 M-05 |
| U-06 | 首次加载解析 184129 条的耗时 | 承接 | Task 10：CLI 首次加载计时落档并回填 spec §8.1 该行；回补手册 M-06 |
| U-07 | `str.isupper` 与 `Uppercase` 属性集合是否完全相等 | 承接 | Task 4：`gen_upper_table.py --verify` 全码点对拍 0 不一致；回补手册 M-07 |
| U-08 | wasm-gc 首次调用完成档案加载 | 承接 | Task 11：同 U-01，仅 build；`profile_counts` 不可达时标阻塞；回补手册 M-08 |
| U-09 | 三目标可用语言数 / 条目合计一致性 | 承接 | Task 11：js 判 `lang_list_len` / `entry_total`，wasm-gc 只登记；回补手册 M-09 |
| U-10 | 三目标主语言一致性 | 承接 | Task 11：js 判 `--mode top1`，wasm-gc 只登记；回补手册 M-10 |
| U-11 | 其他平台位级一致 | 承接 | Task 11：仅登记为容差档，不判绿；回补手册 M-11 |
| U-12 | js / wasm-gc 容差档 | 承接 | Task 11：同 U-04；回补手册 M-12 |

- **机械检索门禁（CO4）**：计划定稿前逐条检索 `U-01`…`U-12`，本文件每个编号命中数 ≥ 1；任一为 0 即计划不完整。
- **转跟踪注册四要素（CO5）**：本计划产生的延期 / 转跟踪项均含「来源批次（本计划）+ 承接任务号（Task 11 / Task 12）+ 责任人（执行者）+ 到期 / 复验触发条件（运行器可用 / 官方 node 可用 / 首次真实发布 / 接缝可注入概率数组）」，缺任一不得注册。
- **批末超期升级（CO6）**：每个切片检查点与 Task 13 扫描本表；连续 ≥ 1 批无任务承接的 U 项升为阻塞并阻塞批关闭，处置三选一（本批补切任务 / 交付范围显式收缩 / ASK-USER），禁止静默续挂。

## Execution Design Declaration (MANDATORY)
- **W1 worker 允许修改文件清单**: `N/A — no parallel workers.`（本计划单执行者串行）；每个 Task 仍声明 `[允许修改文件清单]` 作为越界防线，越界修改属违规。
- **W1b 工作树排他声明**: 本计划单执行者串行，但**不假设事实独占**。核实：`git rev-parse --show-toplevel` rc=0（返回仓库根），HEAD = `192ce0e Initial commit`；`git status --porcelain` 存在未跟踪项（`.venv/`、`_build/`、`analysis/` 等），说明工作树并非由本计划独占管理。**协议**：每个切片开始前记录 `git rev-parse HEAD` + `git status --porcelain` + `src`/`tools`/`docs/superpowers/plans` 的 sha256 清单；检测到非本计划 overlay → 登记（来源 / 范围 / 时间）→ 隔离（不基于其构建或验证）→ 升级决策层裁决；禁止无协议混用。规划阶段不提交（SKILL.md 全局约定：规划阶段不要提交）。
- **W2 重派前残留核对**: `N/A — no re-dispatch in this plan.`；若中断后恢复，第一步执行 sha256 清单比对 + `_build` 时间戳核对，半落地状态按缺陷处置（补全或回退），禁止在半落地状态上继续追加。
- **V1 并行批后整变更集成验证**: `N/A — no parallel batches.`；等价执行方式 = 每个切片（Task 3、4、5、6、7、8、9、10、11）之后插入且仅插入一个「整变更集成验证」节点，由单一执行者运行 `moon check && moon build --target native && moon build --target js && moon build --target wasm-gc && moon test --target native` + 该片门禁，绿后才能进入下一片；禁止依赖自报。
- **V2 配置 / 生成产物改动 dry-run**: 每个生成器任务（Task 4 / 5 / 6 / 10）在生成命令之后紧跟 dry-run：读产物首尾、断言行数 / 声明数 / 字节数 / 区间数，确认无重复定义、形态正确；生成失败即中止，禁止在旧产物上继续构建。
- **L1 机械类任务执行上限**: Task 0 ≤ 40 条命令 / ≤ 3 轮；Task 4 全码点扫描 ≤ 1 次进程 / ≤ 5 分钟；Task 10 ≤ 300 案例 / 进程、≤ 3 轮；Task 12 ≤ 40 条命令 / ≤ 3 轮；超限立即终止并收紧任务描述，禁止空转轮询。
- **D1 构建 / 校验失败诊断路径**: 固定顺序 = ① 归因分析（哪条判据 / 哪一层贡献失败）→ ② 定位责任归属（哪个 Task / 文件 / 模块）→ ③ 处置（修复 / 拆分 / 搁置，并评估影响范围）；禁止先假设原因再行动。
- **V3 增量审查检查点**: 每个切片 V1 之后插入且仅插入一个「增量审查」检查点，由单一审查者审查该片产出（覆盖 / 可执行 / 一致性 / 测试），通过后才能进入下一片；禁止把审查集中在计划末尾。
- **V4 任务排序自洽性**: 任务线性序 Task 0 → Task 13；所有先后引用与线性序同向：Task 1 先于 Task 2+；Task 2 先于 Task 10；Task 3 先于 Task 7；Task 4 先于 Task 6；Task 5 先于 Task 7；Task 7 先于 Task 8；Task 8 先于 Task 9；Task 9 先于 Task 10；Task 10 先于 Task 11；Task 11 先于 Task 12；Task 13 位于最后。
- **V5 终验门禁终局性**: Task 13 位于所有可能改码的任务之后（含探针、修复轮、回补验证引发的改动）；Task 13 通过后任何共享配置（`moon.mod`、`src/*/moon.pkg`、常量表、生成器、`src/math_seam` 分支）变更必须强制复跑 Task 13 全部门禁，禁止沿用变更前结果。

## Surface Coverage Matrix Declaration (MANDATORY)
`N/A — this plan has no addressable surfaces to reconcile.` 理由：本库是纯计算库，无页面 / 路由 / 组件 / 渲染 / 交互入口（spec §9.2 已显式声明 N/A）；用户可见面仅为公开函数返回值，由 spec §8.2 / §8.4 的 golden 断言覆盖，不构成「表面 × 任务」矩阵。Q23 / Q27 / Q28 同此结论。

## Dependency Contract Declaration (MANDATORY)
消费者反查结果与逐字段生产方归属如下（字段类型与 NULL 性逐字复制 spec §4.1 / §4.3）：

| 字段 / 接口 | 读方（消费方） | 写方（生产方） | 生产方归属任务 | 断链处置 / 覆盖断言 |
|---|---|---|---|---|
| `name : String`（非空） | Task 6 / 7 / 8 | Task 5 解析器 | Task 5 | Task 5 单测 + `约定 A` C-A1 声明数 55 |
| `n_words : Array[Int]`（非空，长度恒 3） | Task 7 | Task 5 | Task 5 | 长度断言 + 除零走码 1 的测试 |
| `freq : Map[String, Int]`（非空容器，可为空表） | Task 7 | Task 5 | Task 5 | 键长仅 1/2/3 + `约定 A` C-A2 条目 184129 |
| `word_lang_prob[word][lang_index] : Double`（非空，缺省 0.0） | Task 7 | Task 5 | Task 5 | 概率表单测 + golden `prob_bits` |
| `unicode_block(ch : Int) -> Int`（220 区间） | Task 6 | Task 4 | Task 4 | `src/unicode/block_test.mbt`（spec §2A） |
| `is_upper_cp312(cp : Int) -> Bool` | Task 6 | Task 4 | Task 4 | 全码点对拍 0 不一致 + 1951 计数 |
| `ln_for_gauss(x : Double) -> Double` | Task 7 | Task 3 | Task 3 | A9 冒烟 + 512 点位级一致 |
| `Mt19937` / `random` / `getrandbits` / `randbelow` / `gauss` | Task 7 / 8 | Task 7 | Task 7 | V-31 / V-32 对照 |
| `langlist`（工厂 ↔ 实例别名共享） | Task 8 公开 API | Task 8 工厂 | Task 8 | V-52 / L1-A4 别名断言 |
| `word_lang_prob_map`（同上别名共享） | Task 7 / 8 | Task 8 工厂 | Task 8 | V-52 别名断言 |
| `langprob`（实例缓存，不随 `append` 失效） | Task 8 | Task 7 / 8 | Task 7 | V-47 同实例二次检测 |
| `prior_map`（归一化，NaN 例外） | Task 7 | Task 8 | Task 8 | 码 8 双消息 + V-51 |
| `seed`（构造时读一次） | Task 7 | Task 8 | Task 8 | V-58 seed 语义 |
| `debug_vector_len() -> Int` | Task 8 / 11 | Task 8 | Task 8 | V-48 / V-53 |
| 常量 10 项（V-07 断言域） | Task 7 / 8 | Task 6 | Task 6 | 常量断言测试逐值 |
| `LangProb.lang : String?`（**可空**，仅构造空对象时） | Task 8 / 10 | Task 8 | Task 8 | 排序/过滤测试 |
| `LangProb.prob : Double`（非空） | Task 8 / 10 | Task 8 | Task 8 | 严格大于 0.1 + 稳定排序 |

- 全部生产方与消费方均在本计划内，无跨批断链，无需登记跨批衔接点。
- 无测试手工注入共享状态字段的种子数据；阈值边界样本按 Fixture 节的 `synthetic` 登记，不用于证明生产链完整。

## Fixture Provenance Declaration (MANDATORY)
- **金样本来源**（真实 Python 抓取，`docs/port/golden/` 只读）：`golden:expected-json-219519ee`（md5 `219519ee19d7cc10d404ddbdab3acd87`，268 例）、`golden:profiles-v14`（55 档案 / 184129 条目 / 2204952 字节）、`golden:upper-1951-651`（spec V-36 / V-37）、`golden:rand-feasibility`（V-31 / V-32）、`golden:float-add-conclusion`（V-33 / V-34）、`golden:upstream-contract`（§8 / §9 / §10 quirk）。
- **逐 fixture 溯源标注**：`prob_bits` 一律 `golden:expected.json`；异常码与消息一律 `golden:upstream-behavior-contract.md §9`；清洗 / 大写词一律 `golden:probe_facts append_cleanup`；U3 计数一律 `golden:upper-1951-651`；RNG 序列一律 `golden:rand-feasibility`。
- **合成豁免登记**：① 阈值恰等于 0.1 的三组样本 = `synthetic:基准 250 例中最小条目 0.1428…，无 ≤ 0.1（V-49）`，由 Task 7 经接缝注入构造并在 `task7-prob-rng-2026-10-21.log` 登记；② js / wasm-gc 运行输出 = `synthetic:目标运行器 / 官方 node 不可达（U-01 / U-02）`，不得作为等价证据；③ 其他平台 libm 输出 = `synthetic:仅 win32 x64 可实测（U-05 / U-11）`。
- **替身强度（F5）**：`ln_for_gauss_with` 注入接缝仅用于构造阈值 / 异常样本，能力 ≤ 真实 libm 路径；生产路径 `ln_for_gauss` 必须单独实测（A9）。无其他 mock / stub；不存在替身比真实环境「更能干」的路径。
- **契约形态溯源（F6）**：`extern "C"` 的 `log` 绑定形态 = 1 个 `Double` 参数、返回 `Double`、无回调；溯源 `probes/rand-probe/rand-probe.mbt:176` + spec §5.9 + §8.4a 表行 657；`@math.ln` 溯源 spec §8.4a 表行 658。参数个数 / 顺序 / 返回值逐项登记，不按类型声明猜写。
- **种子数据栈隔离（F7）**：无演示栈；验证栈不使用任何自动注入的预置种子，golden 由脚本读取；依赖 golden 的验证步骤前置 md5 在位校验（spec 命令 15）。

## Error Scenario Matrix Declaration (MANDATORY)
- **网络 / 超时 / 端点未就绪 / 未交付 / 未路由**：`N/A — 本库无外部网络端点、无 HTTP 路由、无超时与重试`；故 EM2 的「端点未就绪」行不适用，错误矩阵改为「错误成因 × 入口」。
- **矩阵（每行附归属测试名）**：

| 错误成因 | 入口 | 期望形态断言 | 归属测试名 |
|---|---|---|---|
| 码 5 无特征（空串 / 纯空白 / 纯 emoji / 纯数字 / 纯标点 / 纯 URL） | `detect` / `detect_langs` / `Detector.detect` | 抛 `LangDetectError`，`code = 5`，消息 `No features in text.`，四字段齐备 | `error_code5_variants_test` |
| 码 5 同输入 | `detect_with_confidence` | **不抛**，返回 `LowConfidence(char_count = 0)` | `lowconf_empty_test` |
| 码 4 未加载档案 | `detect` / `detect_langs` | 消息 `Need to load profiles.` | `error_code4_test` |
| 码 8 负先验 | `set_prior_map` | 消息 `Prior probability must be non-negative.` | `prior_negative_test` |
| 码 8 先验总和 ≤ 0 | `set_prior_map` | 消息 `More one of prior probability must be non-zero.` | `prior_zero_sum_test` |
| 先验 NaN（显式例外） | `set_prior_map` → `detect` | 不抛码 8；概率过滤后为空；`detect` 返回 `"unknown"` | `prior_nan_unknown_test` |
| 码 1 档案格式 / `n_words` 越界 / 除零 / 目录内重复语言 | `load_profile` / `add_profile` | `Profile format error in "<path>"` 或 `Profile format error.` | `profile_format_error_test` |
| 码 2 打开档案失败 | `load_profile` | `Cannot open "<path>"`（保留实现，可达性未验证） | `profile_open_error_test`（标「可达性未验证」） |
| 码 3 重复语言 | `add_profile` | `Duplicate the same language profile.` | `duplicate_lang_test` |
| 低置信分支 | `detect_with_confidence` | `< 50` → `LowConfidence`；`>= 50` → `Detected` | `lowconf_boundary_test` |
| 空概率 → unknown | `detect` | NaN 先验下空概率后返回 `"unknown"` | `prior_nan_unknown_test` |

- **降级 / 阻塞复验安排（EM3）**：码 2 的可达性未验证登记为 `[LOCAL_DEAD_LINK]` 相邻项（不属 U 表，按「未验证（实现期产物）」口径处理），复验触发 = 构造不可打开路径的档案目录，目标批次 = Task 10 的 failures 模式。
- **缺口升级（EM4）**：无未确认就绪的外部端点；无静默假设端点可用的条目。

## Fix Loop Discipline Declaration (MANDATORY)
- **触发**：本计划含「实现 → 对照 → 修复」循环（Task 3-12 的 golden 对拍与门禁），故 R1-R11 全部适用。
- **R1 实证升级**：同一缺陷修复两轮未愈，第三轮起禁止推断式修复，必须运行时取证（真实运行日志 / 状态检查 / golden 逐案例差异），取证产物附入修复轮报告。
- **R2 缺陷类灭绝**：缺陷类 X 的完成定义 = 全仓按检索式排查同类模式（覆盖同型调用 / 同类消费方 / 同构路径）并逐个处置或显式豁免；检索式示例 = 同一错误码消息字面、同一 `.sqrt()` 误用、同一跨包无 `@` 调用、同一 `read_file` 外形。只修报告实例不得放行。
- **R3 修复性质**：每轮报告标注 `根因修复` / `症状修复`；症状修复必须登记根因假设与后续验证计划。
- **R4 取证先行**：报障处置第一步 = 取证落档（复现记录 / 环境日志 / 产物校验和对账），禁止先改代码。
- **R5 分层定位**：按「输入 / 清洗层 → 特征层 → 概率层 → 输出层」分开归因，逐层附可观察证据，禁止混层推断。
- **R6 单变量复验**：每轮修复改动数 = 1，改后复验该变量；多处疑似拆为顺序单变量轮次。
- **R7 调试环还原**：临时调试构件（日志开关 / 埋点 / 冗余输出）必须移除，经还原后的终版构建复验通过才算修复完成。
- **R8 连续复验关闭条件**：N = **3**；缺陷关闭 = 稳定复现 → 最小修复 → 连续 3 次真实目标环境（native win32 x64）复验全绿，逐次附证据（时间 + 环境 + 输出）；中途一次失败计数归零；间歇性缺陷按未愈处理并按 R1 升级取证。
- **R9 假设驱动定位**：可观测性不足时第一步跑最小基线区分「环境坏」与「内容坏」；假设清单（候选原因 / 验证方式 / 证实或证伪结果）落档，证伪即弃；二分前先验证工具链自身可用。
- **R10 靶向回归失败集合逐条比对**：每轮复验对修复前已记录的回归失败集合逐条比对（不变 / 漂移 / 新增 / 消失），逐项归因并附修复轮报告；空集合显式写 `N/A — no pre-existing regression failures.`。
- **R11 契约逃逸缺陷**：若根因是 `extern "C"` / `@math.ln` 契约形态错位且替身世界不可见，四步闭环 = 回填 spec（附权威源码 `file:line` 或实测样本）→ 修正实现 → 注释写真实目标环境实测证据（环境标识 + 日期 + 方式）→ 全仓同类排查；修复验证必须在真实目标环境执行，替身测试全绿不构成完成证据。
- **修复轮验收表**（每个修复轮必须填写）：`| 缺陷实例 | 本轮处置 | 实证证据 | 同类排查结果 | 修复性质 |`。

## Runtime Acceptance Declaration (MANDATORY)
- **A11 两档证据（适用）**：构建面 = 三目标产物存在 + sha256；运行面 = 运行 native CLI / 测试并记录可观察输出（golden 比对结果、`moon test` 汇总、命令 29 字节数）。仅构建面证据不得判「可运行」。
- **A9 未执行路径冒烟探针（必须）**：① Task 3 = 产品侧首次真实调用 `extern "C" log`（`ln_for_gauss(2.0)` 位型断言）；② Task 11 之前先跑 js 目标的 `@math.ln` 最小探针（bun 载体下 `ln_for_gauss(2.0)` 可调用），再进入完整 js 验收。
- **A12 载体核实**：wasm-gc / js 的验证载体已在 spec U-01 / U-02 登记；本计划给出 M-01 / M-02 回补手册，不以「载体不可用」为由跳过核实。
- **A1 / A2 / A6 / A13 显式 N/A**：`N/A — 本库无特权状态、无凭证与测试账号、无 UI 打开态、无体验检查点`；A13 无跨批「非判定项」连挂（每片走查均为判定项）。
- **A3 / A4**：每片末轻量走查 = 固定链路清单 C1-C4（见 Slice Checkpoint 节）；U 项资源到位时按 M-01…M-12 自动生成回补任务并落档。
- **A5 / A8**：`N/A — no deployment or environment-restore task`（本库为编译产物，无部署通道与恢复流程）。
- **A7 外部端点就绪登记**：`N/A — no external endpoints consumed`。
- **A10 真机门禁**：本库不属「外部原生能力依赖」批次；native libm 已在 Task 3 真机冒烟，`extern "C"` 在 js / wasm-gc 不可用由 spec §8.4a 显式声明并按容差 / 仅构建处置。

## Slice Checkpoint Gate Declaration (MANDATORY)
- **S0 门禁挂载到切片**: 三条门禁的执行点（命令 + 期望退出状态 + 日志路径）写入每个切片 Task 的 Output，不只写在 Task 13；里程碑 / 批末 / 终验挂载视为未挂载。
- **S1 静态门（适用）**: 检索式 = spec §10.6 命令 1-14（DR1-DR11 + NE1 / L1-A1 / NE4-2 / NE4-4）**加本计划增补的命令 11b**（命令 11b 的 rc=1 与命令 1-14 同判；Task 0 基线表需另记 11b 一行，见 Task 0 Step 3），期望 0 行 / rc=1；命令 15-19 为基准校验，期望 rc=0。命令 11b = `… | grep -vE '[\\/]cmd[\\/](main|golden)[\\/]'`（豁免 `cmd/main` 与 `cmd/golden` 两段，期望 rc=1 / 0 hits；`cmd/golden` 为诊断输出例外，2026-10-22 用户裁决 / spec §9.4 NE1 行 756；spec 命令 11 豁免整个 `cmd/` 子树，会漏检诊断包的 `println` —— B-04）。切片合并前置 = 对切片改动范围零命中；静态门零命中是编译门前置。新缺陷类灭绝后必须把模式追加进检索式。
- **S2 编译门（适用）**: `moon check && moon build --target native && moon build --target js && moon build --target wasm-gc` 零错误，是进入走查与合入的硬前置；共享代码切片（Task 3 / 4 / 5 / 6 / 7）合入前必须由其消费方（Task 7 / 8）通过一次成功构建。
- **S3 走查门（适用，库等价物）**: 固定核心链路清单（计划期冻结，触链即重走）：
  - **C1** 入口 = 加载 55 档案 → 关键操作 = `detect` 长文本 55 条 → 可观察结果 = 主语言与 `golden:expected.json` 一致（55/55）。
  - **C2** 入口 = 18 条异常输入 → 关键操作 = 调 `detect` / `detect_langs` → 可观察结果 = 码 5 与消息原文一致（18/18）。
  - **C3** 入口 = 55 短 + 55 长文本 → 关键操作 = `detect_with_confidence` → 可观察结果 = `< 50` 走低置信、`>= 50` 走 `Detected`，与 `compare_lowconf` 一致。
  - **C4** 入口 = `src/core/cmd/main` 无参数运行 → 关键操作 = 单次 `detect` → 可观察结果 = stdout / stderr 均 0 字节（spec 命令 29）。
  - **C5（FR-13 空目录可检测）** 入口 = 新建空临时目录并 `cd` 进入 → 关键操作 = 以绝对路径运行 `main.exe`（不依赖 cwd 下任何数据文件）→ 可观察结果 = 退出码 0（内嵌档案生效，spec §8.1 行 612）。
  - **C6（FR-24 / NE4-1 零网络）** 入口 = 后台启动被测二进制 → 关键操作 = 在其存活期间每 0.1s 采样 `netstat -ano` 中**属于该 WINPID** 的连接数 → 可观察结果 = `HITS = 0`（spec §9.4 行 754；判据必须是 PID 级，**禁用**全量快照 diff —— TIME_WAIT 噪声实测 3s/5s/10s 分别新增 5/9/7 行）。
- **S4 流水线纪律（适用）**: 全部多步命令链用 `&&`；生成 / 同步类脚本成功是后续构建的硬前置；禁止 `;`、`|| true`、忽略错误；生成失败时禁止在旧产物上构建。
- 清单与批次末走查（A3）同源维护，更新时两处同步。
- **C5 / C6 与 A7 的关系（B-02 澄清）**：A7「外部端点就绪登记」判 `N/A — no external endpoints consumed` 是**端点契约**层面的判定（本库不消费任何 HTTP / 服务端接口）；NE4-1 / FR-24 是**运行时副作用断言**（检测期间不得发起任何网络请求），与是否存在端点契约无关，**不因 A7 判 N/A 而免检**。二者必须分开登记：A7 = N/A（端点契约），C6 = 判定性走查项（副作用断言）。

## Interface Alignment (MANDATORY)
`N/A — this plan touches no endpoints`。本库无 HTTP 路由 / Service / DAO；spec §5.1-§5.10 的公开函数已按签名表登记，内部接缝（`ln_for_gauss` / `is_upper_cp312` / `unicode_block`）不是端点。

## Spec vs Code Discrepancies (MANDATORY)
`None`（本计划不涉及端点或代码路由，无 spec ↔ 代码路由差异）。spec ↔ plan 的取值差异见文末「Spec vs Plan Discrepancies」（3 条，均已裁决）。

## Acceptance & Verification Commands (MANDATORY)
以下 30 条为 spec §10.6 命令 1-30 **逐字复制**（含范围限定符与 `# rc=` 注释）；执行前须先通过 spec §10.6 的 9 项 grep 能力自检（`SELFCHECK_OK`）。

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

**命令 11b（本计划增补，非 spec §10.6；B-04 修补，2026-10-22 NE1 修订版）**——为保持上方 30 条与 spec §10.6 逐字一致，单独列出。本块文本已按 spec §9.4 NE1 行 756（2026-10-22 用户授权的 NE1 修订）改写：豁免范围由「仅 `cmd/main`」扩为「`cmd/main` + `cmd/golden`」，期望值由「rc=1 / 0 行」改为「rc=1 / 0 hits」；此变更是 2026-10-22 NE1 修订从 spec 带入本计划文本的结果（B-3 文本对齐，2026-10-23）。

```bash
# 命令 11b（**本计划增补，非 spec §10.6**，用于修补 B-04 的 cmd/ 白名单盲区；2026-10-22 NE1 修订版）—— 期望 0 hits / rc=1
# 与命令 11 的差异：豁免 `cmd/main/` 与 `cmd/golden/` 两个路径段，不豁免整个 `cmd/`；`cmd/golden` 是诊断输出例外（2026-10-22 用户裁决，spec §9.4 NE1 行 756），因此本条的绿只要求「库与 `cmd/main` 零命中」。
grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam | grep -vE '[\\/]cmd[\\/](main|golden)[\\/]'
# rc=1（0 hits）；2026-10-23 复测仍为 rc=1 / 0 行
# T2 对照（2026-10-21 实测，样本 = 临时目录 ne1v2/）：
#   样本 A：cmd/golden/main.mbt 含 println("x") → 命令 11（旧过滤 '[\/]cmd[\/]'）rc=1（0 行，**假绿/漏检**）；命令 11b（新过滤 '[\/]cmd[\/](main|golden)[\/]'）rc=0（命中 1 行，**正确拦截**）
#   样本 B：仅 cmd/main/main.mbt 含 println("y") → 命令 11b rc=1（0 hits，**正确豁免**）
```

补充构建 / 测试命令（非 §10.6，属本计划门禁，用 `&&` 串联）：

```bash
command -v moon && moon check && moon build --target native && moon build --target js && moon build --target wasm-gc && moon test --target native
```

`[LOCAL_DEAD_LINK]` 标注（本机不可验项，逐项附五要素手册）：

- `moon test --target wasm-gc` `[LOCAL_DEAD_LINK — 验证地点/方式: 具备可运行 wasm 运行时的机器（本机 `moonrun.exe` 无法启动，spec V-26 / U-01） | 回补手册: M-01]`
- `moon test --target js`（官方 node） `[LOCAL_DEAD_LINK — 验证地点/方式: 安装 Node LTS 的机器（本机仅 bun 替代，spec V-25 / U-02） | 回补手册: M-02]`
- `moon publish`（mooncakes 体积 / 文件数） `[LOCAL_DEAD_LINK — 验证地点/方式: mooncakes 真实发布（U-03） | 回补手册: M-03]`
- `compare_golden --target {js,wasm-gc} --mode prob_tolerance` `[LOCAL_DEAD_LINK — 验证地点/方式: js/wasm-gc 运行器可用后实测容差分布（U-04 / U-12） | 回补手册: M-04]`
- `compare_golden --target native --mode prob_bits`（其他平台） `[LOCAL_DEAD_LINK — 验证地点/方式: linux / macos 机器（U-05 / U-11） | 回补手册: M-05]`
- **本机可执行、非死链（S-05 移出）**：U-06 首次加载解析 184129 条耗时（Task 10 Step 6 本机实测，手册 M-06）与 U-07 `isupper` vs `Uppercase` 全码点核对（Task 4 `gen_upper_table.py --verify` 本机跑，手册 M-07）——两者**不属 `[LOCAL_DEAD_LINK]`**，执行后回填即可；保留在 Carry-over 承接表中，不计入死链清单。
- `compare_golden --target wasm-gc --mode profile_counts` `[LOCAL_DEAD_LINK — 验证地点/方式: 同 M-01（U-08） | 回补手册: M-08]`
- 三目标 `lang_list_len` / `entry_total` `[LOCAL_DEAD_LINK — 验证地点/方式: 三目标运行器可用（U-09） | 回补手册: M-09]`
- 三目标 `top1` `[LOCAL_DEAD_LINK — 验证地点/方式: 三目标运行器可用（U-10） | 回补手册: M-10]`
- 其他平台位级一致 `[LOCAL_DEAD_LINK — 验证地点/方式: 目标平台全量对照（U-11） | 回补手册: M-11]`
- js / wasm-gc 容差档 `[LOCAL_DEAD_LINK — 验证地点/方式: 两目标实测概率差分布（U-12） | 回补手册: M-12]`

## `[LOCAL_DEAD_LINK]` 五要素回补手册（M-01 … M-12）

> 每项五要素：① 部署 / 执行路径与命令；② 凭证与测试账号及供给方式；③ 运行时授权命令；④ 测试数据注入方式；⑤ 取证通道（日志来源与过滤标识）。触发回补时按手册逐步照抄执行，禁止现场即兴摸索。

### M-01（U-01 / U-08）wasm-gc `moon test`
1. **路径与命令（实测确认，B-09 / N-03）**：本机 `moon --help` **无** wasm runner 覆盖项（实测仅 `runwasm  Deprecated: use moon run --target wasm locally or moonx for registry packages`，无 `MOON_RUNNER` / `WASM_RUNNER` 变量）；`moon --version` 尾部实测 `Error: failed to get "…moonrun.exe" version (exit 255)`。因此**本机不可回补**，回补路径 = **异地执行（换机器）**：在一台 `moonrun` 可正常启动的机器上，于仓库根执行 `moon test --target wasm-gc`（不设任何 runner 环境变量），记录 rc 与测试计数。**本批交付范围显式收缩**：wasm-gc 口径 = 仅 `moon build --target wasm-gc` rc=0，`moon test` 不入本批验收范围（依据 U-01 + 本手册）。
2. **凭证与账号**：无。
3. **运行时授权**：目标机上 `moonrun --version` 必须 rc=0（本机该项 rc=255，即为不可回补的判据）；无需 sudo / 管理员。
4. **测试数据注入**：先跑 spec 命令 15-19 确认 golden 在位；再用 `compare_golden.py --target wasm-gc --mode profile_counts` 生成输入。
5. **取证通道**：日志 `docs/superpowers/plans/artifacts/u01-wasm-test-<date>.log`；先记录目标机 `moonrun --version` 输出与 `moon --version`，再记录 `moon test --target wasm-gc` 的 rc 与 `Total tests:` / `failed:` 行；不得把 build rc 当作 test 证据。

### M-02（U-02）官方 node
1. **路径与命令（实测确认，N-02）**：**不得依赖 PATH 前置** —— 本机实测 `export PATH="$(pwd)/probes/bin:$PATH"` 后 `command -v node` 仍解析到 `C:\Users\Administrator\.bunpm\bin\node.cmd`（Windows `.cmd` 解析顺序与 bash PATH 语义不一致），`node --version` 失败。正确做法 = **显式相对路径调用**：`./probes/bin/node.cmd --version`（实测输出 `1.4.3`、rc=0）。前置断言：`case "$(command -v node)" in *probes/bin*) : ;; *) echo "PATH prepend ineffective; use ./probes/bin/node.cmd explicitly"; exit 2;; esac`。官方 node 到位后用 `<NODE_BIN>` 替换 `probes/bin/node.cmd` 的指向；**禁止写死机器绑定的安装前缀**。
1b. **moon js runner 的 node 发现方式（实测）**：若 `moon test --target js` 只能通过 PATH 发现 node 且本机 PATH 前置不生效，则本手册**登记为本机不可回补**，处置 = **异地执行（换机器）**，与 M-01 同待遇；判定方式 = 在目标机执行 `moon test --target js` 并记录其实际调用的 node 路径（`moon --verbose` 输出），写进 u02 日志。
2. **凭证与账号**：无。
3. **运行时授权**：无需。
4. **测试数据注入**：spec 命令 15-19 先跑；再 `compare_golden.py --target js --mode top1`。
5. **取证通道**：日志 `u02-node-test-<date>.log`；过滤 `node --version` 首行、`Total tests:`、`failed:`；报告必须写 `runtime=<bun 1.4.3 或 node 版本>`，未替换 shim 时标「替代运行时」。
6. **本机不可回补的实测证据（N-09）**：`probes/bin` 内只有 `node.cmd`，而 moon spawn 的是 **`node.exe`** → `Failed to spawn node.exe … program not found`；在仓库根执行 `moon test --target js` 会输出 `Total tests: 0` 且 **rc=0**（空跑也绿），不可作为证据。故 js 运行时验证 = **异地执行（换机器）**；本批 js 口径收缩为「仅 `moon build --target js` rc=0」。若异地执行，需在目标机把官方 node 装为 `node.exe` 并确认 `moon test --target js` 的 `Total tests:` ≥ 1。

### M-03（U-03）mooncakes 限制
1. **路径与命令**：`moon package`；`ls -l _build` 与包产物；`moon publish --dry-run`（若不支持则直接 `moon publish`）。
2. **凭证与账号**：mooncakes 账号令牌，存 `~/.moon/credentials.json`（由本机 `moon login` 生成）；禁止写入仓库。
3. **运行时授权**：`moon login`（交互一次）；CI 场景用 `MOONCAKES_TOKEN` 环境变量注入（若工具不支持则以交互登录为准）。
4. **测试数据注入**：先发布最小包（仅 1 语言子集）试探体积 / 文件数上限；保留按语言子集裁剪方案。
5. **取证通道**：日志 `u03-publish-<date>.log`；过滤包名 / 版本 / 字节数 / 服务端错误原文；失败时保留完整响应。

### M-04（U-04 / U-12）js / wasm-gc 容差
1. **路径与命令**：`compare_golden.py --target js --mode prob_tolerance`；`compare_golden.py --target wasm-gc --mode prob_tolerance`。
2. **凭证与账号**：无。
3. **运行时授权**：无。
4. **测试数据注入**：268 golden + 55 长文本；前置 spec 命令 15（md5）与 16-19。
5. **取证通道**：日志 `u04-tolerance-<date>.log`；过滤每案例最大 ULP 差与分布；校准前只记录不判绿。

### M-05（U-05 / U-11）跨平台 libm 位级
1. **路径与命令**：在目标平台 CI 执行 `moon test --target native` 与 `compare_golden.py --target native --mode prob_bits`。
2. **凭证与账号**：CI runner 账号（由 CI 平台供给），不写入仓库。
3. **运行时授权**：CI secrets 只读注入。
4. **测试数据注入**：检出同一 commit；前置 spec 命令 15。
5. **取证通道**：日志 `u05-native-other-<date>.log`；过滤 `prob_bits` 不一致案例；记录 libm 版本（`ldd --version` / `otool -L`）。

### M-06（U-06）首次解析 184129 条耗时
1. **路径与命令**：`/usr/bin/time -v ./_build/native/debug/build/src/core/cmd/golden/main.exe < case.json`；Windows 用 `Measure-Command { ... }`。
2. **凭证与账号**：无。
3. **运行时授权**：无。
4. **测试数据注入**：55 档案内嵌产物；前置 spec 命令 22-25。
5. **取证通道**：日志 `u06-first-load-<date>.log`；过滤 `elapsed` / `parse_ms`；同机 3 次取中位数。

### M-07（U-07）`isupper` vs `Uppercase`
1. **路径与命令**：`.venv/Scripts/python.exe tools/gen_upper_table.py --verify`。
2. **凭证与账号**：无。
3. **运行时授权**：无。
4. **测试数据注入**：CPython 3.12.10 + `unicodedata` 15.0.0；前置 spec 命令 20。
5. **取证通道**：日志 `u07-isupper-<date>.log`；过滤 `0 diff`、`1951`、`651`。

### M-08（U-08）wasm-gc 首次加载
1. **路径与命令**：同 M-01，运行 `compare_golden.py --target wasm-gc --mode profile_counts`。
2. **凭证与账号**：无。
3. **运行时授权**：同 M-01。
4. **测试数据注入**：同 M-01。
5. **取证通道**：日志 `u08-wasm-firstload-<date>.log`；过滤 `profiles=55`、`entries=184129`。

### M-09（U-09）三目标语言数 / 条目合计
1. **路径与命令**：`compare_golden.py --target {native,js,wasm-gc} --mode lang_list_len`；同 `--mode entry_total`。
2. **凭证与账号**：无。
3. **运行时授权**：无。
4. **测试数据注入**：同 M-01。
5. **取证通道**：日志 `u09-targets-<date>.log`；过滤 `lang_list_len`、`entry_total`；wasm-gc 只记录不判绿。

### M-10（U-10）三目标主语言一致
1. **路径与命令**：`compare_golden.py --target {native,js,wasm-gc} --mode top1`。
2. **凭证与账号**：无。
3. **运行时授权**：无。
4. **测试数据注入**：250 有概率案例 + 55 长文本。
5. **取证通道**：日志 `u10-top1-<date>.log`；过滤 `mismatch=`；wasm-gc 不可达时标阻塞。

### M-11（U-11）其他平台位级
1. **路径与命令**：同 M-05，限定 `--target native-other`。
2. **凭证与账号**：CI 账号。
3. **运行时授权**：CI secrets。
4. **测试数据注入**：同 commit + md5。
5. **取证通道**：日志 `u11-native-other-<date>.log`；过滤 `prob_bits` 差异；未跑前保持 dead link。

### M-12（U-12）js / wasm-gc 容差档
1. **路径与命令**：同 M-04。
2. **凭证与账号**：无。
3. **运行时授权**：无。
4. **测试数据注入**：同 M-04。
5. **取证通道**：日志 `u12-tolerance-<date>.log`；过滤 `ulp_max`；校准前 `pending`。

---

# 执行期易错点（Executor Pitfalls，必读）

> 本节只记录**已实测证伪**的执行期陷阱，目的不是补充规范而是防止「看起来全绿」。遇到本节与正文其他描述冲突时，以本节为准（本节为 v5.1 增补）。

## P-1 命令 11 会漏检 `cmd/golden`，必须与命令 11b 同跑

**现象**
spec §10.6 命令 11（NE1 静态门，本文件「命令 11」块）以 `grep -vE '[\\/]cmd[\\/]'` 排除**整个 `cmd/` 子树**；而本计划 Task 10 新增诊断可执行包 `src/core/cmd/golden`（D-03），它也落在 `cmd/` 下 → 该包里的 `println` / `print(` / `eprintln` / `@stdio` 会被命令 11 **静默放过**，不产生任何命中。

**为什么容易踩**
命令 11 单独跑**永远是绿的**（0 行 / rc=1）。rc=1 正是期望值，于是「静态门通过」的结论看起来成立，实际上 `cmd/golden` 从未被检查。这不是偶发失败，而是白名单过宽导致的**结构性漏检**（review-findings B-04）。

**正确做法**
命令 11 与**命令 11b**（本文件「命令 11b」块，`... | grep -vE '[\\/]cmd[\\/](main|golden)[\\/]'`，豁免 `cmd/main/` 与 `cmd/golden/` 两段）**必须同时跑**，两条都 rc=1（0 hits）才算 NE1 静态门通过：
```bash
# 两条各自独立取 rc，禁止用 `;` 或 `|| true` 吞掉其中一条
grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam | grep -vE '[\\/]cmd[\\/]'
echo "cmd11_rc=$?"      # 期望 1
grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam | grep -vE '[\\/]cmd[\\/](main|golden)[\\/]'
echo "cmd11b_rc=$?"     # 期望 1 / 0 hits；若为 0，说明 cmd/main 与 cmd/golden 之外有输出调用
```
命令 11b 是**本计划增补**、不在 spec §10.6 的 30 条之内；Task 0 Step 3 基线表、Task 6 Step 6、Task 9 Step 3 / Output 三串链均已登记该条，执行时不得只跑命令 11。

**证据指针**
计划评审实测（2026-10-21，临时样本目录 `ne1v2/`）：向 `src/core/cmd/golden/main.mbt` 写入 `println("x")` 后，命令 11 → **rc=1（0 行，漏检）**；命令 11b → **rc=0（命中 1 行，正确拦截）**。另一样本仅 `cmd/main/main.mbt` 含 `println` → 命令 11b **rc=1（0 行，正确豁免）**。见 `docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测-review-findings.md` 的 **B-04**（§「B-04 新增包 `src/core/cmd/golden` 越出 spec §4A，且被 NE1 白名单漏检」）、**§6.7 T2 实录**、**R2-1 的 B-04 销项判定**与 **R2 段**。

## P-2 命令 1-14 在空 `src/` 上是「空集假绿」，必须在 Task 6 首个 `.mbt` 落地后整体复跑

**现象**
命令 1-14（DR1-DR11 + NE1 / L1-A1 / NE4-2 / NE4-4）都是「零命中即通过」的静态扫描。当前 `src/` 只有 4 个 0 字节 `moon.pkg` + `src/core/cmd/main` 的两个文件，**没有任何 `.mbt` 产品代码** → 扫描面为空 → 14 条全部 rc=1（0 行）。看起来是 14/14 全绿，但**一条都没有真正验证到**。

**为什么容易踩**
Task 0 基线跑完会得到「命令 1-14 全部 rc=1，符合预期」的漂亮结论，极易直接当成「静态门已过」并据此放行后续切片；实际上这些命令校验的是产品代码的形态，代码不存在时它们恒绿（空集上永远 rc=1）。同理 DR9 / DR10 / DR11 的 T1 基线**必须是非空包**（spec §7 注），而命令 5-8 / 12-14 同样依赖扫描面存在。

**正确做法**
1. Task 0 基线**分列记录两种状态**：「空集态（扫描面 0 个 `.mbt`）」与「实跑态（Task 6 首个 `.mbt` 落地后）」，两者不得混记为一行结论。
2. Task 6 步骤 7 已规定：首个 `.mbt` 落地后**立即整体复跑命令 1-14（含 11b）**，结果写入 `docs/superpowers/plans/artifacts/task6-core-base-2026-10-21.log`。
3. 空集态的「通过」**不得**计入任何切片合并前置（S1 静态门）；只有**实跑态 0 命中**才算静态门通过。命令 1-14 全绿但 `find src -name '*.mbt' | wc -l` 仍为 0 时，按「未验证」处理：
```bash
# 复跑前先确认扫描面非空，否则 1-14 的 rc=1 无意义
find src -name '*.mbt' | wc -l        # 期望 > 0（Task 6 之后）
# 然后逐条跑命令 1-14 + 命令 11b，单条取 rc，日志落 task6-core-base-2026-10-21.log
```

**证据指针**
spec §7 注（DR9 / DR10 / DR11 的 T1 基线必须是非空包）；本文件「Baseline Declaration」的 **B-03** 条（「命令 1-14 全部依赖非空扫描面……空集态与实跑态必须分列记录」）；计划评审实测（review-findings §6.3 逐条表）：空 `src/` 下命令 1-14 全部 **rc=1 且 0 行**，即全为假绿。

> 本节两条均为计划评审阶段实测证伪过的问题，不是理论风险；执行时若与本节的正确做法冲突，以本节为准。

# Task 序列

> 通用约定：日志路径 `docs/superpowers/plans/artifacts/<task>-2026-10-21.log`；保留策略 = 任务日志 90 天、基线 / 终验报告永久、失败日志保留至缺陷关闭。每个 Output 按三要素回填（目标环境标识 + 操作证据 + 观测输出）。

## Task 0 — 全量门禁基线（Baseline-Gate，只读）

### Files
- `docs/superpowers/plans/artifacts/baseline-2026-10-21.md` — 基线记录（新增）
- `docs/superpowers/plans/artifacts/task0-baseline-2026-10-21.log` — 原始输出（新增）
- `[允许修改文件清单]`：仅上述两个 artifacts 文件；`docs/port/**`、`src/**`、`tools/**`、`probes/**` 只读。

### Interfaces
- 无代码接口；产出 30 行命令 + 3 行门禁的基线表。**行模板固定为 `| N | <路径或编号> | rc | <关键输出> | <处置> |`**（N = 1…30 的数字，置于首列；不得写「命令 N」于首列——否则 `grep -c '^| 命令'` 会把表头也计入得 31，且 `grep -c` ≥1 即 rc=0，无法证伪）。

### Steps
0. **spec 修订前置门（N-06，机械 gate）**：D-02 / D-03 / D-04 / D-05 四条裁决为「修订 spec」，必须先于任何产品编码落地。执行四条 grep，**任一为 0 即 `exit 1` 并阻塞 Task 1+**：
   ```
   a=$(awk '/^### D2 架构/,/^\*\*依赖方向\*\*/' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -c 'unicode_block'); b=$(awk '/^## 4A\./,/^## 5\./' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -c 'cmd/golden'); c=$(awk '/^## 4A\./,/^## 5\./' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -c 'gen_core_tables'); d=$(awk '/^## 4A\./,/^## 5\./' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md | grep -c 'c6_zero_network'); echo "unicode_block=$a cmd/golden=$b gen_core_tables=$c c6_zero_network=$d"; test "$a" -ge 1 && test "$b" -ge 1 && test "$c" -ge 1 && test "$d" -ge 1
   ```
   **当前 spec 实测（2026-10-21）**：`unicode_block=0 cmd/golden=0 gen_core_tables=0 c6_zero_network=0` → `gate_rc=1`（**正确阻塞**）。这说明执行 Task 0 前必须先回 brainstorming 修订 spec 三处：§0A D2 行 46 补 `unicode_block`、§4A GP1 补 `cmd/golden`、`gen_core_tables`（及 `ngram_tables.mbt` 产物行）与 `c6_zero_network.sh`。**禁止在 gate 未绿时继续执行 Task 1 及之后的任务**。
1. `command -v moon || exit 2`；`moon --version`；`moonc --version`；`.venv/Scripts/python.exe -V`；逐行记录。
2. 计算代码版本标识：`moon.mod` 全文 + `find src tools -type f | sort` 的 sha256 清单，写入基线 md。
3. 逐条执行 spec §10.6 命令 1-30（单条执行，禁止 `;` 串联）；记录 rc 与 stdout/stderr 摘要；**另执行命令 11b**（豁免 `cmd/main` 与 `cmd/golden` 的 NE1 变体，期望 0 hits / rc=1），作为基线表的第 31 行（编号 11b，不占用 1…30 的编号）。
4. 执行 `moon check`；记录 rc。
5. 执行根 `moon test --target native`；记录 rc 与测试计数。
6. 执行 `probes/embed-probe` 下 `moon test --target native`；记录 56/56（spec V-24）。
7. 按预期基线写 B-01 / B-02 / B-03 与处置（Task 9 / Task 3-8 / Task 6 首次落地后复跑），写入基线 md。
8. W1b 检查：生成 `src`/`tools` sha256 清单；发现非本计划改动则登记来源 / 范围 / 时间。

### Output
- 验收命令：`test "$(grep -cE '^\| [0-9]+ \|' docs/superpowers/plans/artifacts/baseline-2026-10-21.md)" -eq 30`
- 期望退出码：0（T2 实测：30 行表 → 计数 30 / rc=0；表头-only 文件 → 计数 0 / rc=1，修复前 `grep -c '^| 命令'` 形态对 30 行表输出 31、对表头-only 输出 1，两者均无法证伪）。
- 附加验收（N-06 / N-08 前置门）：`unicode_block` / `cmd/golden` / `gen_core_tables` / `c6_zero_network` **四个**计数均 ≥ 1，否则 Task 0 判定为「阻塞（待 spec 修订）」而非通过；此时基线表仍可落档，但 Task 1+ 不得启动。
- 门禁自证伪（T2）：若 baseline md 只有 29 行 → 计数 29 → `test -eq 30` rc=1（必红）；若文件缺失 → `grep` 无匹配 → 计数 0 → rc=1（必红）。禁止用 `test -s` 或裸 `grep -c` 代替。
- 证据日志：`docs/superpowers/plans/artifacts/task0-baseline-2026-10-21.log`。
- 保留策略：基线 md 永久；日志 90 天。
- 时长上限：60 分钟；外部调用轮次上限：40。

## Task 1 — 三目标最小编译探针（E5，先于任何功能编码）

### Files
- `docs/superpowers/plans/artifacts/task1-probe-2026-10-21.log`（新增）
- `[允许修改文件清单]`：无源码修改，仅日志。

### Interfaces
- 仅调用规范入口 `moon`；不新增 `.mbt`。

### Steps
1. `command -v moon || exit 2`。
2. `moon build --target native`；记录 rc。
3. `moon build --target js`；记录 rc。
4. `moon build --target wasm-gc`；记录 rc。
5. 任一 rc ≠ 0 → 停止，按 D1 归因（工具链 / 包图 / 目标支持），触发决策门（补环境 / 换方案 / ASK-USER），禁止进入 Task 2。
6. 记录三目标产物路径与字节数（构建面证据）。
7. 复核 Task 0 的 sha256 清单（工作树排他）。

### Output
- 验收命令：`moon build --target native && moon build --target js && moon build --target wasm-gc`
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task1-probe-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：20 分钟；外部调用轮次上限：6。

## Task 2 — `tools/compare_golden.py` 骨架 + 自检模式

### Files
- `tools/compare_golden.py` — 新增（仅参数骨架与 `--self-check`；产品比对模式显式 `exit 3`，见 Interfaces 的交付分期声明）
- `docs/superpowers/plans/artifacts/task2-compare-selfcheck-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`tools/compare_golden.py`、artifacts 日志。

### Interfaces
- CLI：`--target {native,js,wasm-gc,native-other}`、`--seed {0,42}`、`--mode {self-check,prob_bits,seed_semantics,failures,forensics,cleaning,features_cache,profile_counts,repeatability,top1,lang_list_len,entry_total,prob_tolerance}`、`--golden-dir <path>`（默认 `docs/port/golden`）。
- `--self-check`：校验 `expected.json` 结构（`cases` / `meta` / `repeatability` / `seed_diff` / `unseeded_runs`）、`(268, 250, 18)`、seed `{0, 42}`、`prob_bits` 16 位小写 hex、异常码 `{5}`、md5。
- 未实现模式：打印 `mode not implemented` 并 `exit 3`（不得静默返回 0）。
- **交付分期（B-08 裁决）**：`prob_bits` / `seed_semantics` / `failures` / `forensics` / `cleaning` / `features_cache` / `profile_counts` / `repeatability` / `top1` / `lang_list_len` / `entry_total` / `prob_tolerance` 十二个模式**于 Task 10 交付**；在 Task 10 之前，这些模式返回 `exit 3` 是**预期行为**，不构成缺陷，也不得作为 Task 2 的验收对象。Task 2 的验收面仅限 `--self-check`。

### Steps
1. 读 `约定 C：golden 基准消费契约` §2 / §3 / §4 与 spec §8.2 / §8.4，登记字段与判据。
2. 实现参数解析与 `--self-check`；路径守卫（`--golden-dir` 不存在 → `exit 2`）；失败日志落盘。
3. 运行 `--self-check`；再逐条运行 spec §10.6 命令 15-19。
4. 脚本可移植契约：仅相对路径 / 脚本所在目录 / 临时目录；外部依赖支持环境变量覆盖；无机器绝对路径。
5. 记录自检输出、md5、Python 版本。
6. 记录「本 Task 交付面 = `--self-check`；十二个产品模式留待 Task 10」于日志首行，供 Task 10 首步比对。

### Output
- 验收命令：`.venv/Scripts/python.exe tools/compare_golden.py --self-check && test "$(md5sum docs/port/golden/expected.json | awk '{print $1}')" = "219519ee19d7cc10d404ddbdab3acd87"`
- 期望退出码：0；输出含 `ok 268=250+18`。
- 证据日志：`docs/superpowers/plans/artifacts/task2-compare-selfcheck-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：45 分钟；外部调用轮次上限：10。
- 说明：findings §34.1 B 要求 `compare_golden.py` 为「实现期第一顺位产物」；本计划把它置于 Task 0 / 1 门禁前置之后（Task 0 / 1 不改产品代码），先于全部产品实现，约束不削弱。

## Task 3 — `src/math_seam`（`ln_for_gauss` + 注入接缝 + A9 冒烟）

### Files
- `src/math_seam/math_seam.mbt` — 新增
- `src/math_seam/math_seam_test.mbt` — 新增
- `src/math_seam/moon.pkg` — 修改（当前 0 字节）
- `docs/superpowers/plans/artifacts/task3-math-seam-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`src/math_seam/**`、artifacts 日志。

### Interfaces
- `ln_for_gauss(x : Double) -> Double` —— spec §5.9；native 绑定 libm `log`，js / wasm-gc 走 `@math.ln`。
- `ln_for_gauss_with(f~ : (Double) -> Double, x~ : Double) -> Double` —— 测试注入接缝（spec §5.9「导出以支持测试注入」、MS1-10、EQ2 接缝注入依据）。
- 平台分支仅存在于本文件；降级分支注释必须含 `// non-native fallback`（spec §5.9 / DR2）。

### Steps
1. 回读权威源码：spec §5.9、§8.4a 表行 657-658、`docs/port/rand-feasibility.md` §2 / §3.1、`probes/rand-probe/rand-probe.mbt:176`（`extern "C"` 绑定形态）。
2. 实现 native `extern "C"` `log` 绑定与 `ln_for_gauss`；实现 js / wasm-gc 降级分支并写标记注释；实现注入接缝。
3. 新增测试：`ln_for_gauss(2.0)` 的 IEEE754 位型 = `0x3FE62E42FEFA39EF`（A9 产品侧首次真实调用）；512 点与 `docs/port/golden/rand` 对照；注入接缝只验证转发不验证数值。
4. `moon build --target native && moon build --target js && moon build --target wasm-gc`。
5. `moon test --target native`；运行 spec 命令 5、6、11。
6. 记录 512/512、位型、三目标 rc、标记命中情况。
- **原子标记**：单任务原子（绑定 + 降级分支 + 标记注释 + 导出必须同时落地）；中断恢复先核对全部编辑点（缺一即回退）。

### Output
- 验收命令（三条串联，任一失败即整体失败）：
  ```
  moon test --target native && moon build --target js && moon build --target wasm-gc && test "$(grep -rn '@math\.ln(' --include=*.mbt src | wc -l)" -ge 1 && test "$(grep -rn '@math\.ln(' --include=*.mbt src | grep -vc 'non-native fallback')" = "0" && test "$(grep -rn 'extern "C" fn .*= "log"' --include=*.mbt src | wc -l)" -ge 1 && out=$(moon test --target native -f 'ln_for_gauss_bits*') && test "$(printf '%s' "$out" | grep -oE 'Total tests: [0-9]+' | grep -oE '[0-9]+')" -ge 1 && printf '%s' "$out" | grep -q 'failed: 0' && test "$(grep -cE 'ln_for_gauss_bits' src/math_seam/math_seam_test.mbt)" -ge 1
  ```
- 四条判据的分工（缺一不可）：① `@math\.ln(` 命中 ≥ 1 —— 证明**非 native 降级分支真实存在**（旧的 `grep -vc` 单条在无 `@math.ln(` 时输出 0 即通过，属 vacuous pass）；② 未带 `non-native fallback` 标记的行数 = 0 —— 证明**每一处**降级调用都带标记；③ `extern "C" fn … = "log"` 绑定 ≥ 1 —— 证明 **native 走 libm**；④ **`moon test --target native -f 'ln_for_gauss_bits*'` 且用例数 ≥ 1 且 `failed: 0`**（`-f/--filter` 实测语义 = **按测试名 glob 过滤**，`-f <文件名>` 或 `-f <不存在>` 均输出 `Total tests: 0` 且 **rc 仍为 0**，故必须先断言用例数 ≥ 1 再断言 `failed: 0`，否则恒绿）+ 测试文件含名为 `ln_for_gauss_bits` 的测试函数（N-05：纯 `grep -q '3FE62E42FEFA39EF'` 会被**注释里的常量**骗过，故改为「执行 + 函数名」双条件）。
- 门禁自证伪（T2 实测，2026-10-21）：① 修复前形态 `out=$(printf '' | grep -vc 'non-native fallback')` → `out=0`、`rc=1`、`test "$out" = "0"` → **PASS（假绿）**；② 修复后形态 `test "$(printf '' | grep -vc 'zzz')" -ge 1` → **rc=1（必红，空集被拦截）**，`test "$(printf 'a\n' | grep -vc 'zzz')" -ge 1` → rc=0（有内容才通过）。
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task3-math-seam-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：60 分钟；外部调用轮次上限：12。

### 切片检查点（Task 3 后）
- 静态门：命令 1-14（对 `src/math_seam` 零命中）→ 编译门：三目标 build → 走查门：C1 的 `gauss` 前置链路（以 seam 单测等价，标注「CLI 未就绪」）。
- **V1**：单一执行者 `moon check && moon build --target native && moon build --target js && moon build --target wasm-gc && moon test --target native`，绿后进 Task 4。
- **V3**：单一审查者审查本片覆盖 / 可执行 / 一致性 / 测试，通过后进 Task 4。

## Task 4 — `src/unicode`（U3 表 + `is_upper_cp312` + `unicode_block`）

### Files
- `tools/gen_upper_table.py` — 新增（读 `.venv` 的 CPython 3.12.10）
- `src/unicode/upper_table.mbt` — 生成产物（新增；首行「勿手改」+ 版本表头）
- `src/unicode/unicode.mbt` — 新增（`is_upper_cp312`、`unicode_block`）
- `src/unicode/unicode_test.mbt`、`src/unicode/block_test.mbt` — 新增（spec §2A）
- `src/unicode/moon.pkg` — 修改
- `docs/superpowers/plans/artifacts/task4-unicode-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`src/unicode/**`、`tools/gen_upper_table.py`、artifacts 日志。

### Interfaces
- `is_upper_cp312(cp : Int) -> Bool` —— spec §5.9（651 区间 / 1951 码点）。
- `unicode_block(ch : Int) -> Int` —— spec G-25（220 区间；落点由 spec §2A 指定 `src/unicode/block_test.mbt`）。
- `tools/gen_upper_table.py --verify`：展开生成表并全码点对拍。

### Steps
1. 回读 `约定 B：U3 Unicode 大小写表生成契约` §3 / §5、spec §10.2 C-B1 / C-B2 / C-B5、§2A、`langdetect/langdetect/utils/unicode_block.py:223-465`。
2. **破坏性操作快照（首步）**：若 `src/unicode/upper_table.mbt` 已存在，`cp src/unicode/upper_table.mbt /tmp/upper_table.mbt.bak-20261021`，确认副本存在后才继续。
3. 实现生成器：从 `.venv` CPython 生成 651 区间 + `unidata_version` 表头 + 首行「勿手改」；同时生成 `unicode_block` 的 220 区间表。
4. 生成产物；dry-run：读首 5 行 / 末 5 行，断言区间数 651、表头版本字段存在、无第三方引用。
5. 全码点校验（Equivalence-Gate P3）：`--verify` 与 `chr(cp).isupper()`（跳过 0xD800-0xDFFF）逐点比对，0 不一致；输出 `ok 1951 cps / 651 intervals / 0 diff`。
6. MoonBit 测试：`is_upper_cp312` 计数 1951 + 区间边界抽样；`unicode_block` 按 spec §2A 用例。
7. 运行 spec 命令 20、21；三目标 build。
- **原子标记**：单任务原子（生成器 + 产物 + 查询函数 + 测试必须同时落地）；中断恢复核对产物与函数是否成对。

### Output
- 验收命令：`.venv/Scripts/python.exe tools/gen_upper_table.py --verify && moon build --target native && moon build --target js && moon build --target wasm-gc`
- 期望退出码：0；输出含 `0 diff`。
- 证据日志：`docs/superpowers/plans/artifacts/task4-unicode-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：90 分钟；外部调用轮次上限：15。

### 切片检查点（Task 4 后）
- 静态门命令 1-14；编译门三目标；走查门 C1 的 `capitalword` 前置（`unicode_test` 等价，标注）。
- **V1** + **V3**；通过后进 Task 5。

## Task 5 — `src/data`（flat 生成器 + 解析 + `freq → prob`）

### Files
- `tools/gen_profile_data.py` — 新增（只产 flat）
- `src/data/profiles.mbt` — 生成产物（55 声明、首行「勿手改」；字节数 = 产品侧首次生成后实测登记值，**不是**探针样本的 2205308）
- `src/data/profile.mbt` — 新增（解析、概率表）
- `src/data/profile_test.mbt` — 新增
- `src/data/moon.pkg` — 修改
- `docs/superpowers/plans/artifacts/task5-data-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`src/data/**`、`tools/gen_profile_data.py`、artifacts 日志。

### Interfaces
- `Profile`：`name : String`（非空）、`n_words : Array[Int]`（非空，长度恒 3）、`freq : Map[String, Int]`（非空容器，可为空表）—— spec §4.1 DT1-DT3。
- `parse_profiles(flat : String) -> Array[Profile]`
- `build_prob_table(profiles : Array[Profile]) -> Map[String, Array[Double]]` —— spec §4.2 公式 `freq_lang[word] / n_words_lang[len(word)-1]`；键长 > 3 不写入但仍建零向量（`detector_factory.py:87-92`）。

### Steps
1. 回读 `约定 A：档案内嵌数据格式与生成契约` §3 / §4、spec §4.1 / §4.2、`langdetect/langdetect/detector_factory.py:35-92`。
2. **破坏性操作快照（首步）**：若 `src/data/profiles.mbt` 已存在，`cp src/data/profiles.mbt /tmp/profiles.mbt.bak-20261021`，确认副本存在。
3. 实现生成器（只 flat）：55 档案 → `key\tcount\n`；首行标记；禁止 `Map::from_array`。
4. 生成产物；dry-run 读首尾；断言声明 55、条目 184129、`Map::from_array` 计数 0、首行含「勿手改」；**字节数按 `约定 A：档案内嵌数据格式与生成契约` §5 在产品路径重新登记**（2205308 是探针样本值），登记值写入 artifacts 作为后续基线。
5. 实现解析与概率表；单测：键长分布 7791 / 52387 / 123951（V-15）、非 BMP 0（V-16）、`n_words` 长度 3、除零路径走码 1。
6. 运行 `约定 A` 产品侧 C-A1…C-A6（`$F = src/data/profiles.mbt`）+ spec 命令 22-25（参照样本）+ 命令 21。
7. 三目标 build 与 `moon test --target native`。
- **原子标记**：单任务原子（生成器 + 产物 + 解析器必须同时落地）；中断恢复先核对 55 / 184129。

### Output
- 验收命令：`.venv/Scripts/python.exe tools/gen_profile_data.py && test "$(grep -c 'Map::from_array' src/data/profiles.mbt)" = "0" && head -1 src/data/profiles.mbt | grep -q '勿手改' && test "$(grep -c 'profiles' src/data/profiles.mbt)" -ge 1 && moon test --target native`
- 硬判据（与字节数无关）：`约定 A` C-A1 `decls 55`、C-A2 `entries 184129` 必须 rc=0；C-A3 字节数**以产品侧登记值为基线**，禁止沿用探针样本 2205308 作为产品断言（S-02）。
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task5-data-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：90 分钟；外部调用轮次上限：15。

### 切片检查点（Task 5 后）
- 静态门（DR5 产品侧此时生效）；编译门三目标；走查门 C1（加载 55 + 概统断言，模块测试等价）。
- **V1** + **V3**；通过后进 Task 6。

## Task 6 — `src/core` 基础（错误 / 常量 / NGram / 清洗 / 特征）

### Files
- `src/core/error.mbt`、`src/core/constants.mbt`、`src/core/ngram.mbt`、`src/core/cleaning.mbt`、`src/core/features.mbt`、`src/core/ngram_tables.mbt`（生成） — 新增
- `tools/gen_core_tables.py` — 新增（从 `langdetect/langdetect/utils/ngram.py:64-260` 转写）
- `src/core/ngram_test.mbt`、`src/core/cleaning_test.mbt` — 新增（spec §2A）
- `src/core/moon.pkg` — 修改
- `docs/superpowers/plans/artifacts/task6-core-base-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`src/core/**`（不含 `cmd/**`）、`tools/gen_core_tables.py`、artifacts 日志。

### Interfaces
- `suberror LangDetectError { CantDetect(code~ : Int, message~ : String, input_len~ : Int, input_prefix~ : String) }` —— spec §5.8；码域 0-8（§6），0 / 6 / 7 不实现抛出。
- 常量 10 项 —— spec §1.2 V-07：`ALPHA_DEFAULT = 0.5`、`ALPHA_WIDTH = 0.05`、`ITERATION_LIMIT = 1000`、`PROB_THRESHOLD = 0.1`、`CONV_THRESHOLD = 0.99999`、`BASE_FREQ = 10000`、`UNKNOWN_LANG = "unknown"`、`seed = None`、`n_trial = 7`、`max_text_length = 10000`。
- `NGram::normalize(text : String) -> String` —— 12 个块常量 / 11 个判定臂（Bopomofo 与 Bopomofo Extended 同臂）。
- `NGram::normalize_vi(text : String) -> String`
- `extract_ngrams(text : String) -> Array[String]` — capitalword 只产生 10 个特征（V-46）；表产物 `src/core/ngram_tables.mbt` 由 `tools/gen_core_tables.py` 生成（D-04 裁决见文末：**修订 spec 后** §4A 补 GP1 四要素；详见「Spec vs Plan Discrepancies」）。

### Steps
1. 回读 spec §5.8 / §6 / §1.2 / §9.3、`docs/port/upstream-behavior-contract.md` §3.2 与 §10 quirk 7、`detector.py:44-51,65-66,99-160`、`ngram.py:64-260`。
2. **破坏性操作快照（首步）**：若 `src/core/ngram_tables.mbt` 已存在，`cp` 到 `/tmp` 并确认。
3. 实现错误类型与 9 码常量；实现 10 项常量；实现生成器与表；实现 normalize / normalize_vi / cleaning / extract。
4. dry-run（S-06）：生成表后**必须跑 `tools/gen_core_tables.py --verify`**，断言输出四元组 `12 块 / 11 臂 / 126 组 / 6667 键`（实测口径：块 = 上游 `ngram.py` 出现的 12 个 `UNICODE_*` 常量；臂 = `block ==` / `block in` 比较 11 处；组 = `NGram.CJK_CLASS` 长度 126；键 = `NGram.CJK_MAP` 长度 6667）；不得以「读行数与计数」这类无法证伪的描述代替。
5. 测试：上游 7 个 ngram 用例（spec §2A）+ V-40…V-46；`cleaning_text` 幂等由 Task 8 覆盖。
6. 运行 spec 命令 1-14 与命令 11b；三目标 build；`moon test --target native`。
7. **关闭 B-03**：此时 `src/core` 非空，复跑 DR9 / DR10 / DR11 并把结果写入日志（命令 1-14 空集假绿风险解除）。
- **原子标记**：单任务原子（错误类型 + 所有引用该错误的签名 + 常量必须同时落地）；中断恢复核对「错误类型存在且全部 raise 点可编译」。

### Output
- 验收命令：`moon check && moon test --target native && test "$(grep -rnE '(^|[^[:alnum:]_])(is_wasm|target_name)[[:space:]]*[(]' --include=*.mbt src/core | wc -l)" = "0" && .venv/Scripts/python.exe tools/gen_core_tables.py --verify`
- 期望退出码：0；`--verify` 输出必须含 `12/11/126/6667`（T2：把任一数改错 → rc=1）。
- 证据日志：`docs/superpowers/plans/artifacts/task6-core-base-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：120 分钟；外部调用轮次上限：20。

### 切片检查点（Task 6 后）
- 静态门全量；编译门三目标；走查门 C2（异常码，模块测试等价）。
- **V1** + **V3**；通过后进 Task 7。

## Task 7 — `src/core` 概率与随机（MT19937 / gauss / `_detect_block` / Neumaier）

### Files
- `src/core/rng.mbt`、`src/core/gauss.mbt`、`src/core/detect_block.mbt`、`src/core/normalize_prob.mbt` — 新增
- `src/core/rng_test.mbt`、`src/core/detect_block_test.mbt` — 新增
- `src/core/moon.pkg` — 修改
- `docs/superpowers/plans/artifacts/task7-prob-rng-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`src/core/**`（不含 `cmd/**`）、artifacts 日志。

### Interfaces
- `Mt19937::new(seed : Int64?)`、`random(self) -> Double`、`getrandbits(self, k : Int) -> Int`、`randbelow(self, n : Int) -> Int`
- `gauss(self, mu : Double, sigma : Double) -> Double` —— `log` 必须走 `@math_seam.ln_for_gauss`。
- `detect_block(...)` —— 初始化 → 7 轮随机更新 → 收敛判断 `0.99999` → 平均 → 归一化（`detector.py:146-171`）。
- `normalize_prob(...)` —— `sum` 用 Neumaier（V-33）；`langprob[j] += prob[j] / n_trial` 用朴素加法（V-34，`detector.py:169`）。

### Steps
1. 回读 spec §1.8 V-31…V-35、§9.3、`detector.py:146-232`、`docs/port/rand-feasibility.md` §2、`docs/port/float-add-conclusion.md` 关键事实 3、`probes/rand-probe/rand-probe.mbt:176,186,203`。
2. 实现 MT19937（`seed = None` 不可复现；`Some(s)` 走确定性初始化）、`random` / `getrandbits` / `randbelow`、`gauss`、`detect_block`、Neumaier 求和。
3. 单测：512 点 gauss × 4 seed 与 `docs/port/golden/rand` 一致（V-32）；混合序列 7/7 gauss + 357/357 choice（V-31）；307 组 Neumaier 与 385 组朴素加（V-33 / V-34）。
4. 阈值边界三组样本（恰等于 / 略大于 / 略小于 0.1）经 `ln_for_gauss_with` 与接缝注入构造，报告标注 `synthetic:基准 250 例中最小条目 0.1428…，无 ≤ 0.1（V-49）`。
5. 流式测试：同 seed 重复 5 次一致；不设 seed 连续 10 次允许差异且零异常。
6. 运行 spec 命令 5-11；三目标 build；`moon test --target native`。
7. 生产方覆盖断言：Task 3 / 4 / 5 的接缝与数据契约已由本 Task 消费并通过（引用对应测试名）。

### Output
- 验收命令：`moon test --target native && moon build --target native && moon build --target js && moon build --target wasm-gc`
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task7-prob-rng-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：120 分钟；外部调用轮次上限：20。

### 切片检查点（Task 7 后）
- 静态门；编译门三目标；走查门 C1（概率向量、V-50 并列、V-51 NaN 路径）。
- **V1** + **V3**；通过后进 Task 8。

## Task 8 — 公开 API（`detect` / `detect_langs` / 低置信 / `Detector` / `debug_vector_len`）

### Files
- `src/core/api.mbt`、`src/core/detector.mbt`、`src/core/factory.mbt`、`src/core/confidence.mbt` — 新增
- `src/core/detector_test.mbt`、`src/core/language_test.mbt` — 新增（spec §2A）
- `src/core/moon.pkg` — 修改（导出）
- `docs/superpowers/plans/artifacts/task8-api-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`src/core/**`（不含 `cmd/**`）、artifacts 日志。

### Interfaces（逐字按 spec §5）
- `detect(text : String) -> String raise LangDetectError`
- `detect_langs(text : String) -> Array[LangProb] raise LangDetectError`
- `detect_with_confidence(text : String) -> Confidence`，`LowConfidence(char_count~ : Int)` / `Detected(lang~ : String, probs~ : Array[LangProb])`；阈值 `< 50` 低置信，`>= 50` 正常；空输入不抛码 5。
- `get_lang_list() -> Array[String]`
- `Detector::new() -> Detector`；`DetectorFactory::create(self : DetectorFactory, alpha? : Double) -> Detector`（不写 `Some(...)`）
- `Detector::set_seed(self : Detector, seed : Int64?) -> Unit`
- `Detector::set_prior_map(self : Detector, prior : Map[String, Double]) -> Unit raise LangDetectError`
- `Detector::set_max_text_length(self : Detector, n : Int) -> Unit`
- `debug_vector_len() -> Int`
- `DetectorFactory::load_profile` / `add_profile` / `clear` / `get_lang_list` / `set_seed`
- `LangProb`：`lang : String?`（可空，仅构造空对象时）、`prob : Double`（非空）。

### Steps
1. 回读 spec §5.1-§5.10、§9.3、`detector_factory.py:29-137`、`detector.py:44-144`、`language.py:7-17`。
2. 实现工厂惰性单例、`load_profile` 的目录列举序、`langsize` 与概率向量长度、别名共享（V-52）、实例缓存不失效（V-47）。
3. 实现公开入口、低置信入口、`debug_vector_len`；实现 `set_prior_map` 的码 8 与 NaN 例外（V-51）。
4. 测试：上游 `test_detector.py` 6 例 + `test_language.py` 2 例（spec §2A）；V-47 / V-48 / V-50 / V-51 / V-52 / V-53 / V-54；L1-A4 别名回填断言。
5. 运行 spec 命令 1-14；`moon test --target native`；三目标 build。
6. 生产方覆盖断言：`langlist` / `word_lang_prob_map` / `seed` / `prior_map` 均由本 Task 写入并有对应测试名。
- **原子标记**：单任务原子（`Detector` 字段 + 构造 + 工厂 + 全部导出必须同时落地）；中断恢复核对「§5 全部签名可编译且导出可见」。

### Output
- 验收命令（**十一组**签名 = §5.1-§5.10 十组 + `Detector::new`，加四类型逐项断言；任一缺失即红）：
  ```
  moon test --target native && for p in '^pub fn detect\(' '^pub fn detect_langs\(' '^pub fn detect_with_confidence\(' '^pub fn get_lang_list\(' '^pub fn debug_vector_len\(' '^pub fn (Detector::)?new\(\) -> Detector' '^pub fn (Detector::)?set_seed\(self' '^pub fn (Detector::)?set_prior_map\(self' '^pub fn (Detector::)?set_max_text_length\(self' '^pub fn ln_for_gauss\(' '^pub fn is_upper_cp312\('; do grep -rEq --include=*.mbt -- "$p" src || { echo "MISSING: $p"; exit 1; }; done && for t in 'LangDetectError' 'LangProb' 'LowConfidence' 'Detected'; do grep -rq --include=*.mbt -- "$t" src || { echo "MISSING TYPE: $t"; exit 1; }; done
  ```
- 判据说明（S-04 / N-04）：`pub fn` 计数 > 0 证明不了 spec §5.1-§5.10 的十一组签名齐备；本命令逐项 `grep -rEq`（共 11 条签名 + 4 条类型），**全部用行首锚定 `^pub fn`**（防止注释里出现同名文本造成假通过），任一缺失打印 `MISSING:` 并 `exit 1`。`Detector::new` 同时接受 `pub fn new()` 与 `pub fn Detector::new()` 两种书写（`(Detector::)?`）；`set_seed` / `set_prior_map` / `set_max_text_length` 三项以 `(self` 锚定实例方法形态。**T2 实测（2026-10-21）**：正样本（含上述四种方法 + 全部签名）→ 11/11 OK、rc=0；注释-only 样本（`// set_seed(self)`、`// Detector::new() -> Detector`）→ 两项均 clean（0 命中，不假通过）；删掉 `debug_vector_len` → `MISSING` / rc=1。
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task8-api-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：90 分钟；外部调用轮次上限：15。

### 切片检查点（Task 8 后）
- 静态门；编译门三目标；走查门 C1 / C2 / C3（模块测试等价）。
- **V1** + **V3**；通过后进 Task 9。

## Task 9 — `src/core/cmd/main`（静默 CLI，NE1）

### Files
- `src/core/cmd/main/main.mbt` — 修改（当前空 `fn main { }`）
- `src/core/cmd/main/moon.pkg` — 保持 / 修改（须含 `pkgtype(kind: "executable")`）
- `docs/superpowers/plans/artifacts/task9-cli-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`src/core/cmd/main/**`、artifacts 日志。

### Interfaces
- `main` 仅调用一次 `detect`（固定内置文本，返回值丢弃）；不打印、不读文件、不联网；stdout / stderr 均 0 字节。

### Steps
1. 回读 spec §4A 行 419-421、§9.4 NE1、§10.6 命令 29 / 30。
2. 实现 `main`（单次 detect）；不引入任何打印或 I/O。
3. `moon build --target native`；运行命令 30（pkgtype）与命令 29（静默，rc=0）；确认命令 11 **与命令 11b** 均 rc=1（11b 按 spec §9.4 NE1 行 756 的 2026-10-22 修订，豁免 `cmd/main` 与 `cmd/golden` 两段，对库与 `cmd/main` 要求 0 hits）。
4. 记录二进制路径、字节数、stdout / stderr 字节数（0 / 0）。
5. 三目标 build（js / wasm-gc 仅构建）。
6. **FR-13 空目录可检测（B-01）**：`d=$(mktemp -d) && cd "$d"` 后以**绝对路径**运行 `main.exe`，断言 rc=0 且 stdout/stderr 仍为 0 字节（证明内嵌档案不依赖 cwd 数据文件）。
- **原子标记**：单任务原子（`main.mbt` + `moon.pkg` 同时落地，否则命令 29 退化为 rc=2）。

### Output
- 验收命令（C4 + C5 + NE1b 三段串联）：
  ```
  moon build --target native && ./_build/native/debug/build/src/core/cmd/main/main.exe >/tmp/o.txt 2>/tmp/e.txt && test ! -s /tmp/o.txt && test ! -s /tmp/e.txt && d=$(mktemp -d) && ( cd "$d" && "$OLDPWD/_build/native/debug/build/src/core/cmd/main/main.exe" >/tmp/o2.txt 2>/tmp/e2.txt ) && test ! -s /tmp/o2.txt && test ! -s /tmp/e2.txt && test "$(grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam | grep -vE '[\\/]cmd[\\/](main|golden)[\\/]' | wc -l)" = "0"
  ```
- 三段判据：① 命令 29 静默（stdout/stderr 均 0 字节）；② **C5 / FR-13**：空 cwd 下以绝对路径运行仍 rc=0 且静默；③ **命令 11b**：`cmd/main` 与 `cmd/golden` 以外的任何路径不得出现 stdout/stderr 写调用（`cmd/golden` 为诊断输出例外，2026-10-22 用户裁决）。
- 门禁自证伪（T2 实测 2026-10-21）：空目录命令形态 `d=$(mktemp -d) && cd "$d" && "$ABS" >/tmp/o 2>/tmp/e; rc=$?` → `rc=0`、`assert_rc=0`、`out_bytes=0 err_bytes=0`；若 `main.exe` 缺失 → `rc=127` → 断言 rc=1（必红）。
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task9-cli-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：45 分钟；外部调用轮次上限：10。

### 切片检查点（Task 9 后）
- 静态门；编译门三目标；走查门 C4（命令 29）+ C1 抽查。
- **V1** + **V3**；通过后进 Task 10。

## Task 10 — `compare_golden.py` 产品模式 + `compare_lowconf.py` + 268 案例

### Files
- `tools/compare_golden.py` — 修改（接通产品输出）
- `tools/compare_lowconf.py` — 新增
- `tools/c6_zero_network.sh` — 新增（PID 级零网络断言脚本，见 Output 的行为契约；脚本骨架已在 spec §9.4 NE4-1 的复现中实测）
- `docs/superpowers/plans/artifacts/task10-golden-2026-10-21.log`（新增）
- `[允许修改文件清单]`：`tools/compare_golden.py`、`tools/compare_lowconf.py`、`tools/c6_zero_network.sh`、`src/core/cmd/golden/**`、artifacts 日志。

### Interfaces
- `compare_golden.py --target native --seed {0,42} --mode {prob_bits,seed_semantics,failures,forensics,cleaning,features_cache,profile_counts,repeatability,top1,lang_list_len,entry_total,prob_tolerance}`
- `compare_lowconf.py --short 55 --long 55 --baseline 268`
- 诊断 CLI：读一行 JSON 输入，输出一行 JSON（`langs` / `probs_bits` / `error` 四字段），仅供比对；`main` 仍静默。

### Steps
0. **移除 `exit 3` 占位（B-08 收尾）**：把 Task 2 交付的十二个模式的 `mode not implemented → exit 3` 分支逐条替换为真实实现；改完必须 `grep -n 'exit 3' tools/compare_golden.py` 为 0 命中（否则本 Task 后续验收全为假红）。Task 2 的「交付分期」声明自此失效，以本 Task 的实现为准。
1. 回读 `约定 C：golden 基准消费契约` §2-§4、spec §8.2 / §8.3 / §8.4、§4A。
2. 新增 `cmd/golden` 诊断入口（一次 `detect_langs`，序列化 `prob_bits` 与异常四字段）；构建 native。
3. 实现产品模式：逐案例喂入、解析输出、native 逐位比 `prob_bits`；异常案例比 `code` / `message` / `input_len` / `input_prefix`；实现 seed 语义、repeatability、profile_counts、top1、lang_list_len、entry_total。
4. 实现 `compare_lowconf.py`：55 短 + 55 长 + 268 基线，断言 `< 50` 分支与长文本主结果。
5. 运行 268 案例（250 概率 + 18 异常）；前置命令 16-18；记录失败集合（期望 0）。
6. 计时 U-06：首次加载 / 解析 184129 条耗时，写入 artifacts 并供 Task 11 回填。
7. dry-run：输出行数 = 268；`moon test --target native` 全绿。
8. **FR-24 / NE4-1 零网络运行时断言（C6，PID 级）**：用 `tools/c6_zero_network.sh` 在被测进程**存活期间**循环采样，只统计**属于被测 PID** 的连接（`netstat -ano` 的 PID 列）；全量快照 diff 因 TIME_WAIT 自然波动（实测未运行被测程序时 3s/5s/10s 分别新增 5/9/7 行）**不可作为判据**，仅作辅助观察。
- **原子标记**：单任务原子（脚本 + 诊断 CLI + pkg 同时落地）。

### Output
- 验收命令（单链；`C6` 段 = 零网络断言，后三段 = 268 案例比对）：
  ```
  test "$(grep -c 'exit 3' tools/compare_golden.py)" -eq 0 && sh tools/c6_zero_network.sh ./_build/native/debug/build/src/core/cmd/golden/main.exe docs/port/golden/cases.jsonl && .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode prob_bits && .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 42 --mode prob_bits && .venv/Scripts/python.exe tools/compare_lowconf.py --short 55 --long 55 --baseline 268
  ```
- `tools/c6_zero_network.sh` 必需行为（本 Task 交付，W1 清单已列）：① `test -x "$1" || exit 2`（二进制缺失 → rc=2）；② 后台启动被测二进制并重定向 stdin/stdout；③ **必须**用 `ps -W` 把 Cygwin PID 映射为 **WINPID**（**不得假设二者相等**：实测 `ping.exe` 的 `$!`=14324 而 WINPID=27592）；映射最多重试 20×50ms；若 `W` 为空且进程**仍存活** → `exit 2`（防 `awk -v p='' '$NF==p'` 命中空行造成假红）；若进程已退出且 `W` 为空 → 回退 `W=$PID`（瞬时进程）；④ **首次采样在 `kill -0` 循环之前**执行（保证瞬时进程 `SAMPLES ≥ 1`，不再出现 `exit 3` 断链）；随后每 0.1s 采样 `netstat -ano | awk -v p="$W" '$NF==p' | wc -l` 并累加 `HITS`；⑤ **输入文件契约**：`$2` 作为 stdin（`"$1" < "$2"`，默认 `/dev/null`），**不得**把 `$2` 当位置参数忽略；⑥ 退出码：二进制不存在 → 2；`W` 为空且进程存活（`ps -W` 不可用）→ 2；`HITS > 0` → 1；子进程 rc≠0 → 1；否则 0。**验证该守卫时，被测进程须存活 > 1.5 s**（短于 `ps -W` 重试窗口 1 s 的进程会走「已退出回退」分支而得 rc=0，观察不到守卫）——N-12。
- C6 判据说明（N-01）：`netstat -ano` 的 PID 列 = **最后一列**（本机 `netstat -ano | head -5` 实测五列：`Proto/Local/Foreign/State/PID`，故用 `$NF`，不写死列号）。全量 `netstat -an | sort` 前后 diff **保留为辅助观察**（写日志，不判绿），并注明「TIME_WAIT 噪声使其不可作为判据」。
- **五态实测（2026-10-21，本机，最终契约）**：
  | 态 | 触发 | 输出 | rc |
  |---|---|---|---|
  | ① 无 socket 慢进程 | `sh c6.sh python slow.py` | `HITS=0 SAMPLES=5 WINPID=14748 child_rc=0` | **0** |
  | ② 持有 TCP 连接 | `sh c6.sh python holder.py` | `HITS=54 SAMPLES=19 WINPID=28904` | **1（必红）** |
  | ③ 二进制缺失 | `sh c6.sh ./nope.exe` | 无输出 | **2** |
  | ④ 瞬时退出 | `sh c6.sh /tmp/inst.sh` | `HITS=0 SAMPLES=1 WINPID=66772 child_rc=0` | **0**（不再 exit 3） |
  | ⑤ stdin 契约 | `sh c6.sh /tmp/reader.sh /tmp/in.txt` | 被测进程读到 `got:hello`，`HITS=0 SAMPLES=1` | **0** |
  | ⑥ `ps -W` 不可用 | 以 `false` 替换 `ps -W` + 存活 5s 进程 | 无输出 | **2（守卫生效）** |
  > ⑥ 的守卫生效条件 = `W` 为空**且**进程仍存活 → `exit 2`；若进程已退出则回退 `W=$PID`（④ 的瞬时进程仍可得 rc=0）。
- 降级口径：若 `netstat` 不可用 → 用 `.venv/Scripts/python.exe` + `subprocess` 读 `netstat -ano` 的等价实现，标注「降级执行 + 原因」；`.venv` 无 `psutil`（实测 ImportError），禁用 psutil 方案。
- 期望退出码：0；报告 `268/268`。
- 证据日志：`docs/superpowers/plans/artifacts/task10-golden-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：90 分钟；外部调用轮次上限：15。

### 切片检查点（Task 10 后）
- 静态门；编译门三目标；走查门 C1 / C2 / C3 全量（268 语料）+ **C6 零网络（本 Task Step 8）**。
- **V1** + **V3**；通过后进 Task 11。

## Task 11 — 三目标验收（native 全量 / js 结构 + 准确率 / wasm-gc 仅 build）

### Files
- `docs/superpowers/plans/artifacts/task11-targets-2026-10-21.log`（新增）
- `docs/superpowers/plans/artifacts/target-report-2026-10-21.md`（新增）
- `[允许修改文件清单]`：仅 artifacts。

### Interfaces
- 复用 Task 10 的模式；js 运行时身份写入报告；wasm-gc 只接受 build。

### Steps
1. native：`moon build --target native && moon test --target native`；`compare_golden --target native` 全模式；记录 268/268 与 55/55、51/55。
2. **A9 前置（js，降级为异地）**：本机**不跑** `moon test --target js`。本机仅执行 `moon build --target js` 并记录 rc；`ln_for_gauss(2.0)` 的 js 侧冒烟登记 `[LOCAL_DEAD_LINK]`（U-02 / M-02），异地执行。理由（实测）：`probes/bin` 只有 `node.cmd`，而 moon spawn 的是 `node.exe` → `Failed to spawn node.exe … program not found`；且在仓库根执行 `moon test --target js` 会输出 `Total tests: 0` 且 rc=0（**空跑也绿**），不可作为证据。
3. js（**仅构建**）：`moon build --target js` rc=0 并记录产物 sha256；`moon test --target js` 与 `compare_golden --target js --mode top1 / lang_list_len / entry_total` **全部标 `[LOCAL_DEAD_LINK]`（U-02 / M-02），异地执行**，本机不得判绿。
4. wasm-gc：`moon build --target wasm-gc` rc=0；**不跑 test**（U-01 / U-08）。**本批交付范围显式收缩**：wasm-gc 验收口径 = 仅构建 rc=0，`moon test --target wasm-gc` 不入本批验收范围（依据 U-01 + M-01）；报告中必须逐字写出该收缩声明。
5. 三目标主语言 / 语言数 / 条目合计：js 与 wasm-gc **均**标 `[LOCAL_DEAD_LINK]`（js → U-02 / M-02；wasm-gc → U-01 / U-08 → M-01 / M-08 / M-09 / M-10），本机不判绿；**仅 native 判绿**（M-09 / M-10 的 native 部分仍在本机执行）。
6. 容差档：`--mode prob_tolerance` 不判数值，登记 U-04 / U-12 / M-04；其他平台登记 U-05 / U-11 / M-05 / M-11。
7. A11 两档：记录三目标产物 sha256（构建面）+ native 运行面证据（golden 输出 / 测试汇总）。
8. U-06 回填：把 Task 10 的首次加载耗时写入报告与 spec §8.1 对应行的验收记录。

### Output
- 验收命令：`moon build --target native && moon build --target js && moon build --target wasm-gc && moon test --target native && .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode prob_bits`
- **本批验收口径（N-03，逐字写入 target-report）**：wasm-gc = 仅 `moon build --target wasm-gc` rc=0；`moon test --target wasm-gc` **不入本批验收范围**（交付范围显式收缩，依据 U-01 + M-01）。js = **仅构建**（`moon build --target js` rc=0；测试与比对异地执行，U-02 / M-02）。native = 位级全量。**本批交付范围收缩**：js 运行时验证不入本批验收范围。
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task11-targets-2026-10-21.log`。
- 保留策略：90 天；target-report 永久。
- 时长上限：120 分钟；外部调用轮次上限：20。

### 切片检查点（Task 11 后）
- 静态门；编译门三目标；走查门 C1-C4。
- **V1** + **V3**；通过后进 Task 12。

## Task 12 — 方言红线 + §10.6 全量复跑 + `moon package`

### Files
- `docs/superpowers/plans/artifacts/task12-redline-2026-10-21.log`（新增）
- `[允许修改文件清单]`：仅 artifacts；若红线命中需改码，按 Fix Loop 插入修复轮后再复跑本 Task。

### Interfaces
- 30 条命令逐条；`moon package`；产物字节数 / 文件数（U-03 部分证据）。

### Steps
1. **破坏性操作快照（首步）**：若 `_build` 存在，`cp -r _build /tmp/_build.bak-20261021`，确认副本存在后 `rm -rf _build`（防旧产物假绿）。
2. `moon check`；三目标 build；`moon test --target native`。
3. 逐条运行 spec §10.6 命令 1-30；与 Task 0 基线逐项比对（命令 27 现应为 rc=0，命令 29 应为 rc=0）。
4. `moon package`；记录产物路径、字节数、文件数；不执行真实发布（U-03）。
5. 任一红线命中 → 按 D1 归因到 Task / 文件 → 按 Fix Loop 修复（取证、单变量、N=3）→ 从步骤 2 重跑。
6. 快照按保留策略清理（不进交付产物）。

### Output
- 验收命令：`moon check && moon build --target native && moon build --target js && moon build --target wasm-gc && moon test --target native && moon package`
- 期望退出码：0；命令 1-14 rc=1、15-26 rc=0、27 rc=0、28-30 rc=0。
- 证据日志：`docs/superpowers/plans/artifacts/task12-redline-2026-10-21.log`。
- 保留策略：90 天。
- 时长上限：90 分钟；外部调用轮次上限：15。

## Task 13 — 终验门禁（V5，全量终局）

### Files
- `docs/superpowers/plans/artifacts/task13-final-2026-10-21.log`（新增）
- `docs/superpowers/plans/artifacts/final-report-2026-10-21.md`（新增）
- `[允许修改文件清单]`：仅 artifacts；本 Task 不允许改产品代码，发现问题回到责任 Task 修复后重跑本 Task。

### Interfaces
- 汇总全部验收行：30 条命令 + 构建 + native 测试 + 268 golden + 低置信 + 三目标 + 12 个 U 状态。

### Steps
1. 复核工作树排他（W1b 清单）；若共享配置自 Task 12 后有变更，强制从头复跑。
2. 逐条执行 30 条命令；与 Task 0 基线比对（新失败 / 基线漂移分列）。
3. 执行完整链：`moon check && moon build --target native && moon build --target js && moon build --target wasm-gc && moon test --target native`；再跑 `compare_golden` 全模式与 `compare_lowconf`。
4. 核对 12 个 U 编号逐条有状态（承接任务、当前证据、手册编号）；无「静默通过」。
5. 三要素回填每条验收行（目标环境 + 命令 + 观测输出）；未回填不得判完成。
6. 写 final-report：通过项 / 阻塞项 / 降级项 / 10 个 `[LOCAL_DEAD_LINK]` 状态（U-01…U-05、U-08…U-12；U-06 / U-07 为本机可执行项，单列「已回填」）。**必须逐字写入交付范围收缩声明**：「wasm-gc 本批口径 = 仅 `moon build --target wasm-gc` rc=0；`moon test --target wasm-gc` 不入本批验收范围（依据 U-01 + M-01）」；「js 本批口径 = 仅 `moon build --target js` rc=0；`moon test --target js` 与 js 侧 `compare_golden` 比对 **不入本批验收范围**（交付范围显式收缩，依据 U-02 + M-02）」。
7. V5 条款：本 Task 通过后任何共享配置变更必须复跑本 Task，禁止沿用旧绿。

### Output
- 验收命令：`moon check && moon build --target native && moon build --target js && moon build --target wasm-gc && moon test --target native && .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode prob_bits && .venv/Scripts/python.exe tools/compare_lowconf.py --short 55 --long 55 --baseline 268`
- 期望退出码：0。
- 证据日志：`docs/superpowers/plans/artifacts/task13-final-2026-10-21.log`。
- 保留策略：final-report 永久；日志 90 天。
- 时长上限：60 分钟；外部调用轮次上限：10。

---

# Authority Alignment Table

> 说明：上游 Python 标准库 `random` 的源码不在本仓库，RNG / Neumaier 的「一致」以仓库内实测证据（V-31…V-34）为权威，不伪造行号。

| 决策点 | 权威位置（`file:line:方法`） | plan 结论 | 是否一致 |
|---|---|---|---|
| 包级 `detect` | `langdetect/langdetect/detector_factory.py:126:detect` | 惰性单例 → 新建实例 → append → detect | ✅ 一致 |
| 包级 `detect_langs` | `langdetect/langdetect/detector_factory.py:133:detect_langs` | 返回 `Array[LangProb]`，过滤 + 稳定排序 | ✅ 一致 |
| 惰性单例 | `langdetect/langdetect/detector_factory.py:120:init_factory` | 首次调用初始化，后续复用 | ✅ 一致 |
| `load_profile` | `langdetect/langdetect/detector_factory.py:35:DetectorFactory.load_profile` | 目录列举序；`langsize = len(list_files)`（同文件 40 行） | **功能等价（声明差异）** —— 重复加载：上游追加语义触发码 1 且留部分状态，本移植清空后整体重建、恒为 55；见 spec §5.9b D2 + 用户裁决 2026-10-23 |
| `add_profile` | `langdetect/langdetect/detector_factory.py:80:DetectorFactory.add_profile` | 码 3 重复；键长 > 3 不写概率仍建零向量 | **功能等价（声明差异）** —— 本移植去掉 `index` / `langsize`（推导）并预校验空 name / 任一 `n_words` 合计 0 / 负计数 → 码 1（**严于上游**，上游接受这三者，如 V-50 的 `[4,0,0]`）；不存在「除零」——上游只在出现该键长时才做除法；见 spec §4.1 DT4 / §5.9b D3 |
| `create` | `langdetect/langdetect/detector_factory.py:98:DetectorFactory.create` | `alpha? : Double`，裸值传参 | **功能等价（声明差异）** —— 空工厂上的错误时点：上游在 `create` 即抛码 4，本移植返回空 `Detector` 并把码 4 推迟到检测时；见 spec §5.5 D5 |
| `set_seed` | `langdetect/langdetect/detector_factory.py:110:DetectorFactory.set_seed` | 上游是**类属性**（同文件 29 行）→ 模块级单例可复现；本移植为实例方法，只影响该工厂后续新建实例 | **功能等价（声明差异）** —— 本移植无类属性（`constants.mbt` 的 `pub let seed` 为惰性占位），私有单例不可达，故模块级 `detect` / `detect_langs` 恒为未设 seed、不可复现；需要复现请自建工厂并 `set_seed`。见 spec §5.9b D4 |
| `get_lang_list` | `langdetect/langdetect/detector_factory.py:113:DetectorFactory.get_lang_list` | 返回浅拷贝、加载序 | ✅ 一致 |
| `clear` | `langdetect/langdetect/detector_factory.py:94:DetectorFactory.clear` | **重新绑定**两个容器（非就地清空）；已建实例保留旧容器并继续检测 | ✅ 一致（2026-10-23 对齐，`b7d4b0e`） |
| `PROFILES_DIRECTORY` | `langdetect/langdetect/detector_factory.py:117:PROFILES_DIRECTORY` | 内嵌档案替代目录读取 | ✅ 一致（承载方式按 ADR D 行） |
| `append` | `langdetect/langdetect/detector.py:99:Detector.append` | 追加不清缓存（V-47 / V-54） | ✅ 一致 |
| `cleaning_text` | `langdetect/langdetect/detector.py:114:Detector.cleaning_text` | 就地改写、幂等；URL / 邮箱清洗；LEA 恒不生效 | ✅ 一致 |
| `Detector.detect` | `langdetect/langdetect/detector.py:132:Detector.detect` | 首个 > 阈值；空则 `unknown`（NaN 例外） | ✅ 一致 |
| `get_probabilities` | `langdetect/langdetect/detector.py:141:Detector.get_probabilities` | 惰性触发 `_detect_block` | ✅ 一致 |
| `set_alpha` | `langdetect/langdetect/detector.py:73:Detector.set_alpha` | 无独立 setter；alpha 仅经 `create(alpha=…)` 传入（上游有公开 setter） | **功能等价（声明差异）—— 无独立 setter；alpha 仅经 create(alpha=…) 传入** |
| `set_max_text_length` | `langdetect/langdetect/detector.py:93:Detector.set_max_text_length` | 清洗后码点数截断（V-43） | ✅ 一致 |
| `set_prior_map` | `langdetect/langdetect/detector.py:76:Detector.set_prior_map` | 仅取可用语言；负 / 和 ≤ 0 走码 8；NaN 例外 | **功能等价（声明差异）** —— 失败后 `prior_map` 保持 `None`（上游留零向量，下次检测抛未捕获 `ZeroDivisionError`），见 spec §5.6「已声明差异」+ 用户裁决 2026-10-23 |
| `set_verbose` | `langdetect/langdetect/detector.py:70:Detector.set_verbose` | 不移植（ADR X 行） | ✅ 一致（显式不移植） |
| `Language` | `langdetect/langdetect/language.py:7:Language` | `lang` / `prob`；无 `__eq__`；`__repr__` 不移植 | **功能等价（声明差异）** —— 上游 `__repr__`（`language.py:11-14`）不移植，只影响调试打印；见 spec §4.3 D9 |
| 异常与 9 码 | `langdetect/langdetect/lang_detect_exception.py:1:LangDetectException` / `:16` | 9 码 + 消息原文；四字段为扩展 | ✅ 一致 |
| 常量 10 项 | `detector.py:44-51`、`detector_factory.py:29`、`detector.py:65-66` | V-07 值逐项照抄 | ✅ 一致 |
| `NGram.normalize` | `langdetect/langdetect/utils/ngram.py:64:NGram.normalize` | 12 块常量 / 11 判定臂 | ✅ 一致 |
| `NGram.normalize_vi` | `langdetect/langdetect/utils/ngram.py:99:NGram.normalize_vi` | 逐字表 | ✅ 一致 |
| `CJK_MAP` | `langdetect/langdetect/utils/ngram.py:122:CJK_MAP` | 126 组 / 6667 键 | ✅ 一致 |
| `unicode_block` | `langdetect/langdetect/utils/unicode_block.py:223:unicode_block` | 220 区间 | ✅ 一致 |
| `_detect_block` | `langdetect/langdetect/detector.py:146:Detector._detect_block` | 7 轮、收敛 0.99999、平均 | ✅ 一致 |
| `_normalize_prob` | `langdetect/langdetect/detector.py:223:Detector._normalize_prob` | Neumaier 求和（V-33） | ✅ 一致 |
| `_sort_probability` | `langdetect/langdetect/detector.py:234:Detector._sort_probability` | `p > 0.1` + 稳定降序 | ✅ 一致 |
| 别名共享 | `langdetect/langdetect/detector.py:56:Detector.__init__` | 工厂与实例共享容器（V-52） | ✅ 一致 |
| RNG（MT19937 / gauss） | 库外 CPython `random`；仓库证据 `docs/port/rand-feasibility.md` §2 + `probes/rand-probe/rand-probe.mbt:176` | 21206/21451；512/512 × 4 seed | ✅ 一致（实测等价） |
| Neumaier / 朴素加 | 仓库证据 `docs/port/float-add-conclusion.md` 关键事实 3（V-33 / V-34） | `sum` Neumaier；`langprob += prob/7` 朴素 | ✅ 一致（实测等价） |
| 低置信入口 | 上游无（`[EXT]` G-29；PRD FR-21/22/23） | 阈值 50；空输入不抛码 5 | ✅ 扩展（非对齐项） |
| `debug_vector_len` | 上游无（`[EXT]` G-33；V-53） | 返回 `langsize` | ✅ 扩展（非对齐项） |
| `is_upper_cp312` | 上游无独立 API（`[EXT]` G-31；`约定 B：U3 Unicode 大小写表生成契约`） | 651 区间 / 1951 码点 | ✅ 扩展（非对齐项） |

# Spec-Decision Traceability Table

| 决策点 | spec 位置 | plan 取值 | 仓库现状 | 是否一致 | 裁决 |
|---|---|---|---|---|---|
| 模块根 | spec §4A 行 406 | 仓库根 | `moon.mod:1` 存在 | ✅ | — |
| 模块布局 | spec §0A D2 表 | `src/{core,data,unicode,math_seam}` | 四个 `moon.pkg` 存在（0 字节） | ✅ | — |
| 档案产物 | spec §4A 行 415 | `src/data/profiles.mbt`（flat） | 未生成 | ✅ | — |
| U3 产物 | spec §4A 行 416 | `src/unicode/upper_table.mbt` | 未生成 | ✅ | — |
| 生成器 | spec §4A 行 417-418 | `tools/gen_profile_data.py`、`tools/gen_upper_table.py` | 不存在 | ✅ | — |
| 比对器 | spec §4A 行 422-423 | `tools/compare_golden.py`、`tools/compare_lowconf.py` | 不存在 | ✅ | — |
| CLI | spec §4A 行 419-421 | `src/core/cmd/main`（静默） | 空 `fn main { }` | ✅ | — |
| 数学接缝 | spec §5.9 / §8.4a | native `extern "C"` `log`；js / wasm-gc `@math.ln` + 标记 | 未实现 | ✅ | — |
| 异常形态 | spec §5.8 / V-57 | `suberror` + 四字段 | 未实现 | ✅ | — |
| `LangProb` | spec §4.3 / §5.2 | `LangProb{lang : String?, prob : Double}` | 未实现 | ✅ | — |
| 低置信枚举 | spec §5.3 / V-57 | `LowConfidence(char_count~)` / `Detected(lang~, probs~)` | 未实现 | ✅ | — |
| 常量 | spec §1.2 V-07 | 10 项逐值 | 未实现 | ✅ | — |
| 种子类型 | spec §5.5 / V-58 | `Int64?` + `Some(0L)` | 未实现 | ✅ | — |
| 错误码 | spec §6 | 0-8；0 / 6 / 7 不抛 | 未实现 | ✅ | — |
| 迭代 / 阈值 | spec §1.2 V-07 | 7 / 1000 / 0.1 / 0.99999 / 10000 | 未实现 | ✅ | — |
| RNG | spec §1.8 V-31 / V-32 | MT19937 + libm `log` | 未实现 | ✅ | — |
| 求和 | spec §1.8 V-33 / V-34 | Neumaier + 朴素 | 未实现 | ✅ | — |
| 零第三方 | spec §0A D3 / ADR P 行 | 仅标准库 + 本仓库包 | 现状符合 | ✅ | — |
| 测试文件 | spec §2A | 4 个 `*_test.mbt` + 模块内白盒 | 0 个 `.mbt` 测试 | ✅ | — |
| 档案编码 | spec §4A / V-14 | UTF-8 flat，`key\tcount\n` | 未生成 | ✅ | — |
| 位级档 | spec §8.4 / MS1-8 | 仅 native(win32 x64) | 本机即 win32 x64 | ✅ | — |
| 产物命名 | spec §4A 行 415-423 | 逐字照抄 | 未生成 | ✅ | — |

# Spec vs Plan Discrepancies

| # | 决策点 | spec 取值 | plan 取值 | 裁决 |
|---|---|---|---|---|
| D-01 | Python 调用方式 | §8.2 / §8.4 的操作证据写作裸 `python` | 统一 `.venv/Scripts/python.exe` | **ALIGN-SPEC**：以 §10.6 EC1 行 862（「必须用 `.venv/Scripts/python.exe`，系统 python 无依赖」）为权威；§8 的裸 `python` 属陈旧写法，不照搬也不静默偏离 |
| D-02 | `unicode_block` 的归属模块 | §2A 指定测试文件 `src/unicode/block_test.mbt`，但 §0A D2 行 46 的模块职责表只列 `is_upper_cp312` | 实现与测试均落 `src/unicode/` | **修订 spec**（v1 的 `ALIGN-SPEC` 是错的，S-01）：§2A 落点是测试文件位置，不是职责授权。**执行前必须回 brainstorming 修订 spec**：在 §0A D2 行 46 补「+ `unicode_block` 区块表（220 区间）」；未修订前不得把 §2A 当作 D2 的职责依据 |
| D-03 | golden 比对的可执行载体 | §4A 只登记 `src/core/cmd/main`（必须静默），但 §8.2 / §8.4 要求 `compare_golden` 读取产品输出 | 新增 `src/core/cmd/golden` 诊断可执行包（`cmd/` 路径，NE1 静态命令豁免 `cmd/main` 与 `cmd/golden` 两段，见命令 11b），不进公开 API | **修订 spec**（B-04，用户裁决保留 `cmd/golden` 方案）：**执行前必须回 brainstorming 修订 spec**：① §4A GP1 表补 `src/core/cmd/golden/{moon.pkg,main.mbt}` 两行四要素（生成时点「实现期」、责任单元「产品」、生成命令「—」、校验命令「命令 11b 零命中 + `compare_golden --mode prob_bits`」）；② §9.4 NE1 的 cmd 例外范围为「`cmd/main/` + `cmd/golden/`」，与命令 11b 一致。未修订前不得把该包当作已登记载体 |
| D-04 | ngram 表生成器 `tools/gen_core_tables.py` 与其产物 `src/core/ngram_tables.mbt` 的 GP1 登记 | §4A GP1 表**未登记**该生成器与产物（`grep -n 'gen_core_tables' spec` → rc=1），而 §4A 要求「每条命令引用的每个路径反查四要素」 | 保留生成器（126 组 / 6667 键手工抄写不可维护且易错），并在 Task 6 以 `--verify` 断言四元组 | **修订 spec**（B-05）：**执行前必须回 brainstorming 修订 spec**：在 §4A GP1 表补一行生成器登记（生成命令 `python tools/gen_core_tables.py`、校验命令 `--verify`（12/11/126/6667）、生成时点「构建前」、责任单元「产品」），并补产物行 `src/core/ngram_tables.mbt`（覆盖行为 = 整文件重建；首行含「勿手改」）。备选方案 = 取消生成器改为手写常量表（不推荐：6667 键手工转录不可验证） |
| D-05 | `tools/c6_zero_network.sh` 的 GP1 登记 | §4A GP1 表**未登记**该脚本（`grep -c 'c6_zero_network' spec` → 0），而它是 Task 10 的必交付脚本 | 新增并交付该脚本（PID 级零网络断言，Task 10 Output 调用） | **修订 spec**（N-08）：**执行前必须回 brainstorming 修订 spec**：在 §4A GP1 表补一行四要素（生成时点 = 实现期；责任单元 = 产品；生成命令 = —；校验命令 = `sh tools/c6_zero_network.sh <exe> <cases.jsonl>` 四态实测：无 socket → rc=0 / 持 socket → rc=1 / 缺失 → rc=2 / 瞬时退出 → rc=0） |

---

# Self-Review 结果（Q1-Q70）

| Q | 结论 | 证据 |
|---|---|---|
| Q1 | N/A | 本计划无端点（Interface Alignment 节显式 N/A） |
| Q2 | N/A | 无端点，无 spec 端点可回溯 |
| Q3 | N/A | 无端点，无既有实现可复用 |
| Q4 | Pass | Authority 表逐行比对语义（`detect` / `_sort_probability` / `cleaning_text` / `_detect_block`），非仅签名 |
| Q5 | Pass | 真值表覆盖：码 0-8、阈值三态、NaN、并列（V-50 / V-51）、seed 双套 |
| Q6 | Pass | Spec-Decision 表 22 行均有 spec 位置或仓库事实 |
| Q7 | Pass | D-01 / D-02 / D-03 显式裁决，无静默偏离 |
| Q8 | Pass | 全文无函数体 / 伪代码，仅签名、文件名、命令 |
| Q9 | N/A | 单 spec，无同级 plan |
| Q10 | Pass | E1-E7 均附 read/glob 证据或实测结果 |
| Q11 | Pass | 验收命令无机器绑定绝对路径，统一 `moon` 入口 |
| Q12 | Pass | Task 2 / 4 / 5 / 6 / 10 脚本含 env 覆盖 + 路径守卫 + 日志落盘 |
| Q13 | N/A | 无并行 worker（W1 显式 N/A），仍保留每 Task 允许修改清单 |
| Q14 | Pass | 每片后 V1 整变更集成验证（单一执行者） |
| Q15 | Pass | Task 4 / 5 / 6 / 10 生成后紧跟 dry-run |
| Q16 | Pass | Task 0 / 4 / 10 / 12 声明硬上限（命令条数 + 轮次） |
| Q17 | Pass | D1 三步固定顺序 |
| Q18 | Pass | Task 1 = 三目标编译探针，先于全部功能编码 |
| Q19 | Pass | `extern "C"` / `@math.ln` / bun 均有编码前核实任务（Task 1 / 3 / 11） |
| Q20 | Pass | Task 4 全码点 0 diff；Task 7 512 / 307 / 385 组；均置于集成前 |
| Q21 | Pass | 每片 V3 增量审查，非末尾集中 |
| Q22 | Pass | 12 个 U 项均标 `[LOCAL_DEAD_LINK]` 并注验证地点 |
| Q23 | N/A | 无用户可见表面 |
| Q24 | Pass | 全部 fixture 标 `golden:` 或 `synthetic:`，金样本任务在 Task 0 实测 |
| Q25 | Pass | 修复轮验收表 + R1-R11 全覆盖 |
| Q26 | N/A | 无特权状态 / 凭证 |
| Q27 | N/A | 无表面迁移 |
| Q28 | N/A | 无表面切片盘点 |
| Q29 | Pass | 依赖契约表 17 行，生产方全部映射任务 |
| Q30 | N/A | 无 mock 依赖端点；以真实运行时探针替代 |
| Q31 | Pass | R4-R7 写入 Fix Loop 声明与修复轮要求 |
| Q32 | Pass | A4 回补机制 + M-01…M-12；部署对账 N/A 已显式说明 |
| Q33 | Pass | 错误矩阵含码 5 / 4 / 8 / 1 / 2 / 3 + 低置信 + NaN，每行附测试名 |
| Q34 | N/A | 无 UI 打开态 |
| Q35 | N/A | 无外部端点 |
| Q36 | Pass | 注入接缝能力 ≤ 真实路径，生产路径单独测（A9） |
| Q37 | Pass | N = 3，逐次证据要求写入 R8 |
| Q38 | Pass | R9 最小基线 + 假设清单落档 |
| Q39 | Pass | 无部署任务（A5 / A8 N/A）；U 项出口门已声明 |
| Q40 | Pass | Task 4 / 5 / 6 / 12 首步为快照 |
| Q41 | Pass | V4 逐条先后引用与线性序同向 |
| Q42 | Pass | Task 13 最后 + 共享配置强制复跑条款 |
| Q43 | Pass | E6 逐条实测或 fallback |
| Q44 | Pass | E7 四通道计划期实测 |
| Q45 | Pass | Task 3（`extern "C" log`）+ Task 11（js `@math.ln`）A9 探针 |
| Q46 | Pass | R10 基线失败集合逐条比对 |
| Q47 | Pass | 实现方案均有 spec 章节或仓库事实来源 |
| Q48 | Pass | 30 条命令逐字复制并标注命令号 |
| Q49 | Pass | `extern "C"` 契约形态溯源 `probes/rand-probe/rand-probe.mbt:176` |
| Q50 | Pass | native 真机冒烟；替身仅作辅助证据 |
| Q51 | Pass | R11 四步闭环 |
| Q52 | Pass | Task 0 全量基线 + B-01 / B-02 / B-03 处置 |
| Q53 | Pass | 每门禁有执行与日志；降级口径已写 |
| Q54 | Pass | 测试文件均为新增，声明「diff 纯增量、0 删除行」 |
| Q55 | Pass | 12 份五要素手册 |
| Q56 | Pass | reviewer 失败 → 降级机器核验式自审 |
| Q57 | Pass | U-01…U-12 全表承接，承接行均有任务号 |
| Q58 | Pass | 转跟踪四要素齐备 |
| Q59 | Pass | 每片与终验扫描 U 表并升级 |
| Q60 | Pass | A11 构建面 + 运行面两档 |
| Q61 | Pass | A12 载体登记；A13 显式 N/A |
| Q62 | Pass | D-01 / D-02 / D-03 后果已传播到 Task 4 / 9 / 10 / 11 |
| Q63 | Pass | 每片 S0 / S1 / S2 / S3 挂载 |
| Q64 | Pass | 全部命令链用 `&&` |
| Q65 | Pass | Task 3 / 5 / 6 / 8 / 9 / 10 原子标记 + 中断核对 |
| Q66 | Pass | W1b 排他声明 + 外来 overlay 协议 |
| Q67 | Pass | 字段类型与 NULL 性逐字复制（`String` / `Array[Int]` / `Map[String, Int]` / `String?`） |
| Q68 | N/A | 无演示 / 验证双栈种子 |
| Q69 | Pass | js / wasm-gc 分层；E7 已预声明通道 |
| Q70 | Pass | 每 Output 三要素回填门禁 |

**计数：Pass 57 / N/A 13 / 未过 0（Q1-Q70 全覆盖）。**

---

**文档结束**
