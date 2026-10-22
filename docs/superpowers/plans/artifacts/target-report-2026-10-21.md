# 三目标验收报告（Task 11）

- 日期：2026-10-23（计划文件日期口径 2026-10-21）
- 仓库：`F:/moonbit比赛/moon_langdetect`；分支：`sdd/moon-langdetect-2026-10-21`
- 基线 HEAD：`5c2a7f264966decf2c93a0a6eab4294e8c3320da`
- 工具链：`moon 0.1.20261012 (748b63c 2026-10-12)`；`Python 3.12.10`；win32 10.0.19045 x64；Git Bash
- 证据日志：`docs/superpowers/plans/artifacts/task11-targets-2026-10-21.log`
- **保留策略：本报告永久保留；证据日志保留 90 天。**
- 本报告只记录**实测**结果；未实测者一律标 `[LOCAL_DEAD_LINK]`，不判绿、不补写。

## 0. 本批验收口径（交付范围显式收缩）

「wasm-gc 本批口径 = 仅 `moon build --target wasm-gc` rc=0；`moon test --target wasm-gc` 不入本批验收范围（依据 U-01 + M-01）」

「js 本批口径 = 仅 `moon build --target js` rc=0；`moon test --target js` 与 js 侧 `compare_golden` 比对 **不入本批验收范围**（交付范围显式收缩，依据 U-02 + M-02）」

补充口径：

- **native = 位级全量**（`prob_bits` seeds 0/42 位级一致 + 268 案例 + 116 单测）。
- **本批交付范围收缩**：js 运行时验证不入本批验收范围。

## 1. 总判定

| 维度 | 结果 | 判定 |
|---|---|---|
| native 构建 + 测试 | `moon build --target native` rc=0；`moon test --target native` → `Total tests: 116, passed: 116, failed: 0.` | **绿** |
| native 全模式比对 | 12 产品模式 + `--self-check` + `--dry-run` 全部 rc=0；268/268 案例覆盖 | **绿** |
| native 低置信 | short 55/55、long 55/55、baseline 268 | **绿** |
| native 位级 | `prob_bits` seed 0（125/125, 138 entries）、seed 42（125/125, 136 entries）均 `bitwise=identical` | **绿** |
| js 构建 | `moon build --target js` rc=0；`golden.js` sha256 已记录 | **绿（仅构建）** |
| js 运行时 | test / 三个 compare 模式 / `ln_for_gauss(2.0)` 冒烟 | `[LOCAL_DEAD_LINK]`（U-02 / M-02），**不判绿** |
| wasm-gc 构建 | `moon build --target wasm-gc` rc=0；`golden.wasm` sha256 已记录 | **绿（仅构建）** |
| wasm-gc 运行时 | `moon test` / `profile_counts` / 三目标一致性行 | `[LOCAL_DEAD_LINK]`（U-01 / U-08 → M-01 / M-08 / M-09 / M-10），**不判绿** |
| 容差档 | `--mode prob_tolerance` 仅登记，无数值判定 | 登记（U-04 / U-12 / M-04；U-05 / U-11 / M-05 / M-11） |
| 验收链 | brief Output 命令整条执行 | **rc=0** |

## 2. 命令与输出

完整逐条记录见证据日志 §1–§9。摘要：

```text
$ moon build --target native && moon test --target native
Finished. moon: no work to do
Total tests: 116, passed: 116, failed: 0.
rc=0

$ .venv/Scripts/python.exe tools/compare_golden.py --self-check
ok 268=250+18 (prob_entries=274, seeds=0/42)
rc=0

$ .venv/Scripts/python.exe tools/compare_golden.py --dry-run
ok dry-run lines=268 expected=268 (250 probability + 18 error cases)
rc=0

$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode prob_bits
ok prob_bits target=native seed=0 cases=125/125 entries=138 bitwise=identical
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 42 --mode prob_bits
ok prob_bits target=native seed=42 cases=125/125 entries=136 bitwise=identical

$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode seed_semantics
ok seed_semantics target=native repeatability=14/14 groups x5 runs (70 runs), seed_diff=125/125 (0 vs 42 differ as recorded), unseeded=7/7 texts (70 runs; top in baseline distinct_langs, RNG variation required where baseline distinct_count > 1)
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode failures
ok failures target=native cases=18/18 code/message/input_len/input_prefix matched; failure_set=[]
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode forensics
ok forensics target=native cases=18/18 four_fields=code/message/input_len/input_prefix
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode cleaning
ok cleaning target=native cases=6/6 V-40..V-43
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode features_cache
ok features_cache target=native checks=2/2 V-46 raw grams exact; V-47 probs1==probs2
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode profile_counts
ok profile_counts target=native lang_list_len=55 entry_total=184129 vector_len=55 u06_parse_ms=204 u06_load_ms=323
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode repeatability
ok repeatability target=native groups=14/14 runs=70 identical=yes
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode top1
ok top1 target=native cases=250/250 top_lang=detect
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode lang_list_len
ok lang_list_len target=native len=55 order=expected.json/meta.langlist
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode entry_total
ok entry_total target=native total=184129
$ .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode prob_tolerance
ok prob_tolerance target=native: bitwise-only, tolerance not applicable (convention C C1/C5; native compares prob_bits)

$ .venv/Scripts/python.exe tools/compare_lowconf.py --short 55 --long 55 --baseline 268
ok lowconf seed=0 short=55/55 (<50 LowConfidence), long=55/55 (>=50 Detected, top in golden candidates), baseline=268
rc=0
```

### 2.1 268 / 55 / 51 的口径（含差异声明）

| 记录值 | 来源 | 实际含义 |
|---|---|---|
| **268/268** | `--self-check`（`ok 268=250+18`）+ 全模式覆盖 | 基准案例总数 = 250 概率 + 18 异常；`failure_set=[]` |
| **55/55（short）** | `compare_lowconf.py --short 55` | 55 条 **< 50 码点**文本全部 `LowConfidence`，`char_count` 校验通过 |
| **55/55（long，实测）** | `compare_lowconf.py --long 55` | 55 条 **≥ 50 码点**文本全部 `Detected`，top ∈ 该案例 golden 候选集合 |
| **51/55（基准）** | `docs/port/golden/summary.json` → `detect_accuracy_short_seed0` | 上游 Python **短文本** top-1 基线：`hit=51, miss=4, n=55`；miss = `short-bg` / `short-no` / `short-zh-cn` / `short-zh-tw` |

**差异声明（显式记录，未静默替换）**：brief Step 1 与 rubric R9 把 `51/55` 表述为 `compare_lowconf.py --short 55 --long 55` 的 **long** 分组结果；runner 实测输出为 `long=55/55`。

- `compare_lowconf.py:266-277` 的 long 判据是「`>=50` 且 `Detected` 且 top ∈ golden 候选集合」，**不是** top-1 严格准确率，因此结构上不可能输出 51/55。
- `51/55` 的真实来源是 `docs/port/golden/summary.json` 的 `detect_accuracy_short_seed0`（上游短文本 top-1 基线，seed=0），与 `docs/port/architecture-decisions.md:83,93`、spec V-23 一致。

结论：三个数各自成立但**语义不同**。本报告按实测记录 `long=55/55`，并把 `51/55` 归位为「上游短文本准确率基线」；**brief/rubric 的 51/55 归属有误，属文档口径缺陷，不是产品失败**。

## 3. 三目标主语言 / 语言数 / 条目合计（仅 native 判绿）

| 目标 | 主语言（`--mode top1`） | 语言数（`--mode lang_list_len`） | 条目合计（`--mode entry_total`） | 判定 |
|---|---|---|---|---|
| **native (win32 x64)** | `detect`（250/250） | **55** | **184129** | **绿**（M-09 / M-10 的 native 部分本机实跑通过） |
| **js** | `[LOCAL_DEAD_LINK]` | `[LOCAL_DEAD_LINK]` | `[LOCAL_DEAD_LINK]` | **不判绿** — U-02 / M-02，异地执行 |
| **wasm-gc** | `[LOCAL_DEAD_LINK]` | `[LOCAL_DEAD_LINK]` | `[LOCAL_DEAD_LINK]` | **不判绿** — U-01 / U-08 → M-01 / M-08 / M-09 / M-10 |

native 证据行：

```text
ok top1 target=native cases=250/250 top_lang=detect
ok lang_list_len target=native len=55 order=expected.json/meta.langlist
ok entry_total target=native total=184129
```

## 4. js 目标：仅构建 + 死链登记

### 4.1 构建

```text
$ moon build --target js
Finished. moon: no work to do
js_build_rc=0
```

产物：`_build/js/debug/build/src/core/cmd/golden/golden.js`（2 766 239 B）。

### 4.2 本机**未**运行 `moon test --target js`（理由逐字）

> `probes/bin` 只有 `node.cmd`，而 moon spawn 的是 `node.exe` → `Failed to spawn node.exe … program not found`；且在仓库根执行 `moon test --target js` 会输出 `Total tests: 0` 且 rc=0（**空跑也绿**），不可作为证据。

本机旁证（同根因）：`moon run --target js src/core/cmd/main` → `The system cannot find the path specified.`，**rc=1**，无任何测试计数输出。

### 4.3 `[LOCAL_DEAD_LINK]` 登记（本机**不判绿**）

| 项 | 标签 | 依据 | 回补手册 |
|---|---|---|---|
| `moon test --target js` | `[LOCAL_DEAD_LINK]` | U-02 / M-02 | M-02 |
| `compare_golden.py --target js --mode top1` | `[LOCAL_DEAD_LINK]` | U-02 / M-02（U-10 → M-10） | M-10 |
| `compare_golden.py --target js --mode lang_list_len` | `[LOCAL_DEAD_LINK]` | U-02 / M-02（U-09 → M-09） | M-09 |
| `compare_golden.py --target js --mode entry_total` | `[LOCAL_DEAD_LINK]` | U-02 / M-02（U-09 → M-09） | M-09 |
| `ln_for_gauss(2.0)` js 侧冒烟（A9） | `[LOCAL_DEAD_LINK]` | U-02 / M-02 | M-02 |

### 4.4 js 运行时身份（本机实际可观测，未虚构版本）

| 观测项 | 观测命令 | 观测结果 |
|---|---|---|
| `probes/bin` 内容 | `ls probes/bin/` | 仅 `node.cmd`（59 B），**无 `node.exe`** |
| `probes/bin/node.cmd` 指向 | `cat probes/bin/node.cmd` | `"C:\Users\Administrator\.bun\bin\bun.EXE" %*` |
| 替代运行时版本 | `"/c/Users/Administrator/.bun/bin/bun.exe" --version` | **bun 1.4.3**（bun，非 Node） |
| `node.exe` 是否存在 | `where.exe node.exe` | `INFO: Could not find files for the given pattern(s).` → **rc=1，不存在** |
| `node` 解析结果 | `where.exe node` | `C:\Users\Administrator\.bunpm\bin\node.cmd`（仍是 `.cmd`） |
| 该 `.cmd` 指向 | `cat "C:/Users/Administrator/.bunpm/bin/node.cmd"` | `"D:\nvm4w\nodejs\bun" %*` |
| 该目标是否存在 | `ls /d/nvm4w/nodejs` | `No such file or directory` → **指向失效路径** |
| 官方 Node 安装 | `ls "C:/Program Files/nodejs"` | `No such file or directory` → **未安装** |
| `moonrun` | `moonrun --version` | **rc=127**（命令不存在） |
| moon runner 覆盖项 | `moon --help \| grep -i run` | 仅 `run`、`runwasm Deprecated…`，**无 runner 覆盖变量** |

**结论**：本机 js 运行时 = **bun 1.4.3（经两层 `.cmd` shim）**；官方 Node **未安装**、`node.exe` **不存在**、`moonrun` **不存在**。moon 无法 spawn `node.exe` → js 运行时链路在本机为**死链**。

## 5. wasm-gc 目标：仅构建 + 死链登记

```text
$ moon build --target wasm-gc
Finished. moon: no work to do
wasm_build_rc=0
```

产物：`_build/wasm-gc/debug/build/src/core/cmd/golden/golden.wasm`（3 416 907 B）。

**未执行** `moon test --target wasm-gc`（U-01 / U-08；本机 `moonrun` rc=127）。`profile_counts` 与三目标一致性行的 wasm-gc 侧同样登记为 `[LOCAL_DEAD_LINK]`（M-01 / M-08 / M-09 / M-10）。

## 6. 容差档 `--mode prob_tolerance`（仅登记，无数值判定）

```text
ok prob_tolerance target=native: bitwise-only, tolerance not applicable (convention C C1/C5; native compares prob_bits)
rc=0
```

| 平台 | 状态 | 登记项 |
|---|---|---|
| native | 位级唯一口径，容差**不适用**（约定 C C1 / C5） | — |
| js / wasm-gc | 容差数值**待校准**，不判绿 | **U-04 / U-12 / M-04** |
| native-other（linux / macos） | 不判绿 | **U-05 / U-11 / M-05 / M-11** |

## 7. A11 两档证据

### 7.1 构建面：三目标产物 sha256

| 目标 | 产物 | 字节数 | sha256 | build rc |
|---|---|---|---|---|
| native | `_build/native/debug/build/src/core/cmd/golden/golden.exe` | 4 268 544 | `5d75dc59d47d7dee8153f1058258425884d408c97982f3eb66e11ad22fbe56e2` | 0 |
| js | `_build/js/debug/build/src/core/cmd/golden/golden.js` | 2 766 239 | `f5acb7eea3b306c617db512a4f0ec315a4e365a9b1f6f6dae7b2424ea0b843a6` | 0 |
| wasm-gc | `_build/wasm-gc/debug/build/src/core/cmd/golden/golden.wasm` | 3 416 907 | `11023f2f1c084e39765ce57df9395be6aa3d3a5d0f736c0fc9a48cf5cbd37bf0` | 0 |

（静默 CLI `cmd/main` 产物 sha256 对照：`main.exe` = `3aaed8a3…566d1b73`、`main.js` = `d07c83c1…315ac9b`、`main.wasm` = `cec742f1…07a9ff`；详见证据日志 §7.1。）

### 7.2 运行面：native 运行证据

- golden 输出行：15 条 `ok …`（见 §2），覆盖 268 案例。
- 测试汇总：`Total tests: 116, passed: 116, failed: 0.`
- 低置信：`ok lowconf seed=0 short=55/55 …, long=55/55 …, baseline=268`

## 8. U-06 回填：首次加载 / 解析 184129 条耗时（Task 10 实测值）

> **本节是 destined-for-spec 的回填值，口径对位 spec §8.1「首次调用完成档案加载」行的验收记录。**
> **spec §8.1 本身未在本 Task 修改** —— 按全局约束 R1，`docs/superpowers/specs/` 只读；spec 编辑**顺延至拥有该授权的任务**（Task 12 / Task 13 或独立授权项）。本报告仅保存待落档的权威数值，不构成 spec 变更。

来源：Task 10 对 `golden.exe '{"mode":"meta"}'` 的 3 次**冷进程**采样（N=3，取中位数），每次运行为独立 OS 进程。

| 运行 | `parse_ms` | `load_ms` | `total_ms` | `entry_total` |
|---|---|---|---|---|
| 1 | 229 | 347 | 576 | 184129 |
| 2 | 209 | 358 | 567 | 184129 |
| 3 | 207 | 317 | 524 | 184129 |
| **中位数** | **209** | **347** | **567** | **184129** |

**回填结论（拟写入 spec §8.1 的验收记录列）**：原生目标首次解析 **184129** 条档案条目耗时中位 **209 ms**；首次工厂加载（解析 + 概率表构建）中位 **347 ms**；两者合计中位 **567 ms**；`entry_total=184129`。

交叉核对：本轮 `--mode profile_counts` 给出 `u06_parse_ms=204 u06_load_ms=323`，与上表同量级（单次采样，不替代中位数口径）。

## 9. 验收链（brief Output 命令，整条执行一次）

```text
$ moon build --target native && moon build --target js && moon build --target wasm-gc \
    && moon test --target native \
    && .venv/Scripts/python.exe tools/compare_golden.py --target native --seed 0 --mode prob_bits
Finished. moon: no work to do
Finished. moon: no work to do
Finished. moon: no work to do
Total tests: 116, passed: 116, failed: 0.
ok prob_bits target=native seed=0 cases=125/125 entries=138 bitwise=identical
rc=0        # start=2026-10-23T03:55:22+0800, end=2026-10-23T03:56:08+0800
```

与 brief「期望退出码：0」一致。全链以 `&&` 串联（R5），无 `;`、无 `|| true`、无错误吞没。

## 10. 保留策略与配额

| 项 | 值 |
|---|---|
| 本报告 `target-report-2026-10-21.md` | **永久** |
| 证据日志 `task11-targets-2026-10-21.log` | **90 天**（至 2027-01-21） |
| 时长上限 120 分钟 | 实际约 25 分钟墙钟（未超） |
| 外部调用轮次上限 20 次 | 实际 **0 次**（零网络、零外部服务） |

## 11. 已知限制

- js / wasm-gc 的运行面在本机**不可达**，本批只判构建；三目标一致性（主语言 / 语言数 / 条目合计）**只有 native 行有实测**，其余两行为 `[LOCAL_DEAD_LINK]`。
- 容差档（js / wasm-gc / native-other）数值**未校准**，本批只登记不判定；校准依据必须来自 js 目标实测，不得凭空写数。
- U-06 为 N=3 冷进程采样的中位数；如需更稳定口径应增大 N（Task 10 已记录该限制）。
- `51/55` 归属偏差见 §2.1：brief/rubric 将其置于 `compare_lowconf` 的 long 分组，实测 runner 输出 `long=55/55`；`51/55` 实为上游短文本准确率基线。
