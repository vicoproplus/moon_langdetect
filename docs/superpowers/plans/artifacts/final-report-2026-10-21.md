# 终局验收报告（Task 13 / V5 全量终局）

- 任务：Task 13 — 终验门禁（V5，全量终局）
- 仓库：`F:\moonbit比赛\moon_langdetect`；分支 `sdd/moon-langdetect-2026-10-21`（未切换；`main` 未触碰）
- 起始 HEAD：`c674a892ac92015b4dd0ac2c61d4c3acbad412bc`
- 验收日期：2026-10-23（+0800）；工具链与 Task 0 基线一致（`moon 0.1.20261012` / `moonc v0.10.15+943464bfa` / `Python 3.12.10`），未更换
- 证据日志：`docs/superpowers/plans/artifacts/task13-final-2026-10-21.log`（永久报告 / 日志 90 天）
- **保留策略**：本报告**永久**；证据日志**90 天**（至 2027-01-21）

## 总判定：DONE_WITH_CONCERNS

产品代码观测面**全绿且为当前树实测**（30 条 §10.6 静态门符合预期分割、三目标构建 rc=0、native 116/116、268/268 golden、低置信 short 55/55 & long 55/55、双 seed 位级一致、Output 验收链 rc=0）。js / wasm-gc 运行时按**已声明的交付范围收缩**全部登记 `[LOCAL_DEAD_LINK]`，**不判绿**。**B-2（`moon package` 内容越界）已在终审修复波中关闭**（`680f744`，见 §九）。**仍开放 3 项**（B-1 / B-3 / B-4），另有 1 个 **parked 用户决策**（`set_prior_map` 失败后状态，见 §九），均超出本任务授权面，需用户 / controller 决策。

---

## 一、通过项

| # | 项 | 目标环境 | 命令 | 观测输出 | rc |
|---|---|---|---|---|---|
| P-01 | §10.6 命令 1-14（红队静态门，必须零命中） | win32 x64 / GNU grep 3.0 | 见日志 §2.1 命令原文 1-14 | 全部 0 行 / 0 字节 | **1 ×14** |
| P-02 | §10.6 命令 15-26（基准与产物门） | win32 x64 | 见日志 §2.1 命令原文 15-26 | `ok`×4、`ok 1951 cps / 651 intervals`、`25` 等；md5 一致 | **0 ×12** |
| P-03 | §10.6 命令 27（`pub fn` 存在） | win32 x64 | `grep -rn '^pub fn' --include=*.mbt src` | **51 行 / 3994 B**（基线 rc=1 为空集态；本轮 rc=0 属计划预期推进 B-02 关闭） | **0** |
| P-04 | §10.6 命令 28-30（模块名 / 静默 CLI / 可执行包） | win32 x64 | 见日志 §2.1 | `main.exe` stdout 与 stderr **各 0 字节** | **0 ×3** |
| P-05 | `moon check` | native host | `moon check` | `Finished. moon: ran 2 tasks, now up to date (5 warnings, 0 errors)`；5 warning 均为 `src/data/profiles.mbt` 的长字符串 `[0033]`（既有基线现象） | **0** |
| P-06 | 三目标构建 | native / js / wasm-gc | `moon build --target native` / `js` / `wasm-gc` | 三条均 `Finished. moon: no work to do`；产物 sha256 `2cb6a0d6…c449c191`（exe 4 268 544 B）/ `f5acb7ee…0b843a6`（js 2 766 239 B）/ `11023f2f…cbd37bf0`（wasm 3 416 907 B） | **0 ×3** |
| P-07 | native 单测 | native (win32 x64) | `moon test --target native` | `Total tests: 116, passed: 116, failed: 0.` | **0** |
| P-08 | golden `--self-check` / `--dry-run` | native | `tools/compare_golden.py --self-check` / `--dry-run` | `ok 268=250+18 (prob_entries=274, seeds=0/42)`；`ok dry-run lines=268 expected=268 (250 probability + 18 error cases)`（stdout 实为 268 行） | **0 / 0** |
| P-09 | 位级一致 seed 0 | native (win32 x64) | `--target native --seed 0 --mode prob_bits` | `cases=125/125 entries=138 bitwise=identical` | **0** |
| P-10 | 位级一致 seed 42 | native (win32 x64) | `--target native --seed 42 --mode prob_bits` | `cases=125/125 entries=136 bitwise=identical` | **0** |
| P-11 | seed 语义 | native | `--mode seed_semantics` | `repeatability=14/14 groups x5 runs (70 runs), seed_diff=125/125, unseeded=7/7 texts (70 runs…)` | **0** |
| P-12 | 参数与失败路径 | native | `--mode failures` | `cases=18/18 code/message/input_len/input_prefix matched; failure_set=[]` | **0** |
| P-13 | 失败取证通道 | native | `--mode forensics` | `cases=18/18 four_fields=code/message/input_len/input_prefix` | **0** |
| P-14 | 清洗契约 | native | `--mode cleaning` | `cases=6/6 V-40..V-43` | **0** |
| P-15 | 大写词与缓存 | native | `--mode features_cache` | `checks=2/2 V-46 raw grams exact; V-47 probs1==probs2` | **0** |
| P-16 | 档案计数 / 首次加载计时 | native | `--mode profile_counts` | `lang_list_len=55 entry_total=184129 vector_len=55 u06_parse_ms=187 u06_load_ms=318` | **0** |
| P-17 | 同 seed 重复性 | native | `--mode repeatability` | `groups=14/14 runs=70 identical=yes` | **0** |
| P-18 | 主语言 | native | `--mode top1` | `cases=250/250 top_lang=detect` | **0** |
| P-19 | 可用语言数 | native | `--mode lang_list_len` | `len=55 order=expected.json/meta.langlist` | **0** |
| P-20 | 条目合计 | native | `--mode entry_total` | `total=184129` | **0** |
| P-21 | 容差档（native 不适用） | native | `--mode prob_tolerance` | `bitwise-only, tolerance not applicable (convention C C1/C5; native compares prob_bits)` | **0** |
| P-22 | 低置信入口 | native | `tools/compare_lowconf.py --short 55 --long 55 --baseline 268` | `short=55/55 (<50 LowConfidence), long=55/55 (>=50 Detected, top in golden candidates), baseline=268` | **0** |
| P-23 | **268 / 268** | native | `--self-check` + `--dry-run` + `failures` + `top1` | 268 = **250 概率案例 + 18 异常案例**；`--dry-run` 实输 268 行；`failure_set=[]` | **0** |
| P-24 | **short / long 拆分** | native | `compare_lowconf.py` | **short 55/55**、**long 55/55**、baseline 268（`51/55` 是上游短文本 top-1 基线 `summary.json → detect_accuracy_short_seed0`，**不是** long 输出，三者语义不同，未互相替换） | **0** |
| P-25 | 空目录可检测（PRD FR-13） | native | `cd <空目录> && main.exe`（目录条目 0） | `rc=0`，stdout **0 B** / stderr **0 B** | **0** |
| P-26 | golden 基准未被覆写 | native | §10.6 命令 15 | md5 `219519ee19d7cc10d404ddbdab3acd87`；结构 268/250/18 复验一致 | **0** |
| P-27 | brief Output 验收链（单条 `&&`） | native | 见日志 §7 | 7 段全通，`OUTPUT_CHAIN_RC=0`（05:10:34→05:11:44，70.53 s） | **0** |
| P-28 | 工作树排他（W1b） | — | `git status --porcelain --untracked-files=all` | 仅 7 项既存未跟踪输入（6 个 Task 0 时即存在且哈希未变的 `tools/*.py` + 1 个用户会话记录）；`_build/`、`.venv/` 由 `.git/info/exclude` 排除故不出行；**共享配置自 Task 12 起未变更**（tracked 树 diff 为空；`2215243..HEAD` 仅 3 个 artifacts 文档） | **0** |

### 1.1 30 条命令的 rc 范围（与基线、与 Task 12 三方比对）

| 区间 | 本轮 rc | Task 0 基线 rc | Task 12 rc | 比对结论 |
|---|---|---|---|---|
| 1-14 | 全 1 | 全 1 | 全 1 | 一致（0 命中；非空集假绿：`src/` 含 30+ 产品 `.mbt`，check / build / 116 测试实跑通过） |
| 15-26 | 全 0 | 全 0 | 全 0 | 一致 |
| 27 | **0** | **1** | 0 | **基线漂移 1 条**：B-02 空集态（0 个 `pub fn`）→ 实跑态 51 行；计划明写的预期推进，**非回归** |
| 28-30 | 全 0 | 全 0 | 全 0 | 一致 |

- **新失败：0 条。** **基线漂移：1 条（命令 27，已归因）。** 与 Task 12 差异：**0 条**。
- NE1 三形态（日志 §2.3）：spec 命令 11 → rc=1 / 0 行；计划 11b（仅豁免 `cmd/main`）→ rc=0 / 1 命中；spec 行 756 形态 → rc=1 / 0 行。与 Task 12 完全一致。

---

## 二、阻塞项（B-2 已于修复波关闭；B-1 / B-3 / B-4 仍未关闭）

### B-1 — U-06 spec 验收行未落档（`OPEN ACCEPTANCE ROW`）

- 状态：**已回填（报告侧）/ 未落档（spec 侧，阻塞）** —— `OPEN ACCEPTANCE ROW, OWNER: unassigned, 需用户 spec 编辑授权`
- 目标行：`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md:614`（§8.1「首次调用完成档案加载 / native (win32 x64)」）；本轮实测该行仍是 `观测输出 = —`、`状态 = 未验证（产品实现未落地）`。
- 已具备值（报告侧，`target-report-2026-10-21.md` §8）：首次解析 **209 ms** / 首次工厂加载 **347 ms** / 合计 **567 ms**（N=3 冷进程中位数），`entry_total=184129`；本轮交叉采样 `u06_parse_ms=187 u06_load_ms=318`。
- 阻塞原因：修改 spec 需用户在本次会话的显式编辑授权，本会话未持有；本任务对 spec 只读。
- **不得**在授权前把 U-06 记为「已验证」。

### B-2 — `moon package` 内容越界（RELEASE BLOCKER）— **已关闭（`680f744`）**

**原始测量（历史，保留不改写；测于 `.moonignore` 落地之前）**：`_build/publish/vicoproplus-langdetect-0.1.0.zip` —— **7 212 092 B**，**360 文件**，解压 **25 744 994 B**。越界内容：`2026-10-22-183213-empty-conversation.txt` 1 547 761 B（6.01 %，用户本地 agent 会话记录）、`docs/port/golden/` 1 728 082 B / 20 文件（R1 只读证据区）、`langdetect/` 2 325 270 B / 79 文件（9.03 %，上游 Python 参考实现）；非产品合计 **23 099 180 B = 89.72 %**，唯一产品 `src/` 仅 2 645 814 B（10.28 %，37 文件）。

**根因（已修）**：仓库根当时**无 `.moonignore`**（`ls -a | grep -i moonignore` → rc=1 无匹配），隐藏依赖 `.git/info/exclude`，而 **moonc 忽略 `.git/info/exclude`**。修复提交 `680f744` 在仓库根新增 `.moonignore`（**13 行**），覆盖 `/probes/`、`/langdetect/`、`/docs/`、`/analysis/`、`/.superpowers/`、`/_build/`、`/.venv/`、`*.txt`、`__pycache__/`、`*.pyc`（另含 3 行注释）。

**修复后复测**：

| 口径 | 字节 | 文件数 | 解压字节 | 违禁条目 |
|---|---:|---:|---:|---:|
| 修复前（无 `.moonignore`） | 7 212 092 | 360 | 25 744 994 | transcript / `docs/port/golden` / `langdetect` 均在内 |
| 修复后（干净树重打包，`git archive a29cb4e`） | **1 119 652** | **46** | **2 765 426** | **0** |
| 当前磁盘产物（本报告复测：`stat -c %s`） | **1 151 839** | **52** | **2 841 785** | **0** |

`unzip -Z1 _build/publish/*.zip | grep -cE '^(probes|langdetect|docs|analysis|\.superpowers)/|empty-conversation'` = **0**（rc=1，无匹配）。磁盘产物为 52 文件而非干净树的 46 文件，差值恰为 6 个生成器脚本（`tools/gen_float_golden.py`、`tools/gen_golden.py`、`tools/gen_rand_golden.py`、`tools/probe_facts.py`、`tools/profile_stats.py`、`tools/summarize_probes.py`）——它们在该 zip 构建（06:56）之后才由 `1395186` 纳入版本控制，属**应当随包发布的可复现性输入**，不是越界内容。

**A/B 证明**：同一棵树，带 `.moonignore` 打包 = **52 文件 / 2 841 785 B**；移除 `.moonignore` 后打包 = **362 文件 / 6 799 286 B**。差异全部为参考输入与用户私密记录。

`moon publish` **仍然从未执行**，无实际泄露；发布前只需复跑 `moon package` 并复核上表字节数。

### B-3 — 计划 v5.1 命令 11b rc 偏离（`PENDING CONTROLLER RULING`）

- 计划 11b（仅豁免 `cmd/main`，期望 rc=1）实测 **rc=0 / 1 命中**：`src/core/cmd/golden/main.mbt:330:  println(output.stringify())`。
- spec 行 756（2026-10-22 用户授权的 NE1 修订，同时豁免 `cmd/main` 与 `cmd/golden`）形态实测 **rc=1 / 0 命中**。
- spec 行 423 / 424（§4A GP1 两行）仍写「NE1 静态门**仅豁免 `cmd/main/`**」，与行 756 **内部矛盾**。
- 本轮按 spec 行 756 判绿，**未放行代码、未改 spec / plan**。计划文本与 spec 423/424 的一致性需用户裁决。

### B-4 — spec §2A 23 源用例到 116 目标测试的逐用例映射未登记（文档缺口）

- spec §8.3「源侧 23 用例的目标侧对应文件存在且通过」：本轮以「10 个 `*_test.mbt` 存在 + `moon test --target native` 116/116 通过」回填，但 23 → 116 的**逐用例映射表**在 spec 中未登记，本任务无授权补写。属文档缺口，不影响产品行为。

---

## 三、降级项

| 项 | 处置 | 依据 |
|---|---|---|
| js 运行时验证（`moon test --target js`、js 侧 `compare_golden` 比对） | 本机**不执行、不判绿**；整项 `[LOCAL_DEAD_LINK]` | `where.exe node.exe` rc=1（不存在）；`probes/bin/` 仅 `node.cmd`（bun 1.4.3）；空跑 0 测试不可作证据（U-02 / M-02） |
| wasm-gc 运行时验证（`moon test --target wasm-gc`、`profile_counts`） | 同上 | `moonrun --version` rc=127（命令不存在）；`moon --version` rc=127 同源（U-01 / M-01） |
| 三目标主语言 / 语言数 / 条目合计一致性 | 仅 **native 行实测判绿**；js / wasm-gc 行 `[LOCAL_DEAD_LINK]` | U-01 / U-02 → M-01 / M-02 / M-09 / M-10 |
| 容差档 `prob_tolerance` | **仅登记数值不判定**；native 声明「不适用」（约定 C C1/C5）；js / wasm-gc / native-other 数值待校准 | U-04 / U-12 / U-05 / U-11 |
| 跨平台（linux / macos）位级一致 | 仅登记，不判绿 | U-05 / U-11 / M-05 / M-11 |
| `moon publish`（mooncakes 体积 / 文件数上限） | **不执行**；仅本地 `moon package` 产物落档 | U-03 / M-03 |
| 非等价降级（`@math.ln` vs libm `log`） | 显式声明：js / wasm-gc 相对 native 为**非等价降级**（2000 点中 66 点差 1 ulp；gauss 512 点中 27 点不一致），不当作等价实现 | spec §8.4 Fail-2 |

### 3.1 本批交付范围收缩声明（逐字，不可改写）

「wasm-gc 本批口径 = 仅 `moon build --target wasm-gc` rc=0；`moon test --target wasm-gc` 不入本批验收范围（依据 U-01 + M-01）」

「js 本批口径 = 仅 `moon build --target js` rc=0；`moon test --target js` 与 js 侧 `compare_golden` 比对 **不入本批验收范围**（交付范围显式收缩，依据 U-02 + M-02）」

---

## 四、12 个 U 项逐条状态（无静默通过）

承接任务取自计划 `…语种检测.md:62-73`；手册取自计划 §363-450（M-01…M-12）。

| U | 项 | 承接任务 | 手册 | 状态 | 当前证据 |
|---|---|---|---|---|---|
| U-01 | wasm-gc `moon test` 结果 | Task 11 | M-01 | **`[LOCAL_DEAD_LINK]`**（能力未验证） | `moonrun --version` rc=127；本机仅 wasm-gc build rc=0 |
| U-02 | js 官方 node 结果 | Task 11 | M-02 | **`[LOCAL_DEAD_LINK]`**（能力未验证） | `where.exe node.exe` rc=1；仅 `node.cmd`→bun 1.4.3；js 侧仅 build rc=0 |
| U-03 | mooncakes 体积 / 文件数限制 | Task 12 | M-03 | **`[LOCAL_DEAD_LINK]`**（指标未测）；本地侧已落档 | 修复前 zip 7 212 092 B / 360 文件 / 解压 25 744 994 B → **修复后 1 119 652 B / 46 文件 / 2 765 426 B**（当前磁盘产物 1 151 839 B / 52 文件，见 B-2）；`moon publish` 未执行 |
| U-04 | js / wasm-gc 概率容差数值 | Task 11 | M-04 | **`[LOCAL_DEAD_LINK]`**（指标未测） | native `prob_tolerance` rc=0 但显式「不适用」；两目标容差数值待校准 |
| U-05 | 跨平台 libm 位级一致性 | Task 11 | M-05 | **`[LOCAL_DEAD_LINK]`**（能力未验证） | 位级档限 native(win32 x64)；linux / macos 无载体 |
| U-08 | wasm-gc 首次调用完成档案加载 | Task 11 | M-08 | **`[LOCAL_DEAD_LINK]`**（能力未验证） | 同 U-01；`--target wasm-gc --mode profile_counts` 不可达 |
| U-09 | 三目标语言数 / 条目合计一致性 | Task 11 | M-09 | **`[LOCAL_DEAD_LINK]`**（js / wasm-gc 侧） | native `len=55` / `total=184129` 已实测；js / wasm-gc 未执行 |
| U-10 | 三目标主语言一致性 | Task 11 | M-10 | **`[LOCAL_DEAD_LINK]`**（js / wasm-gc 侧） | native `top1 cases=250/250 top_lang=detect`；js / wasm-gc 未执行 |
| U-11 | 其他平台位级一致 | Task 11 | M-11 | **`[LOCAL_DEAD_LINK]`**（能力未验证） | 同 U-05；`--target native-other` 无载体 |
| U-12 | js / wasm-gc 容差档 | Task 11 | M-12 | **`[LOCAL_DEAD_LINK]`**（指标未测） | 同 U-04；两目标概率差分布未取得 |

- 以上 **10 项**即交付范围收缩所依据的 `[LOCAL_DEAD_LINK]` 全集（U-01…U-05、U-08…U-12），逐项**不判绿**。
- 承接任务、手册号、验证地点 / 方式见日志 §5。

### 4.1 本机可执行项（单列）

| U | 项 | 承接任务 | 手册 | 状态 | 证据（三要素齐备） |
|---|---|---|---|---|---|
| U-07 | `str.isupper` vs `Uppercase` 属性集合完全相等 | Task 4 | M-07 | **已回填** | 目标环境 win32 x64 / CPython 3.12.10；命令 `.venv/Scripts/python.exe tools/gen_upper_table.py --verify`；观测输出 `ok 1951 cps / 651 intervals / 0 diff` + `ok 220 blocks / 0 diff (full codepoint lookup)`；rc=**0** |
| U-06 | 首次加载解析 184129 条耗时 | Task 10 | M-06 | **已回填（报告侧）/ 未落档（spec 侧，阻塞） — OPEN ACCEPTANCE ROW, OWNER: unassigned, 需用户 spec 编辑授权** | 报告侧：`target-report-2026-10-21.md` §8（parse 209 ms / load 347 ms / total 567 ms，N=3 中位，`entry_total=184129`）+ 本轮 `u06_parse_ms=187 u06_load_ms=318`；spec 侧：`spec.md:614` 仍「未验证」→ 见阻塞项 **B-1** |

---

## 五、V5 终局条款（生效）

> 本 Task 通过后，**任何共享配置变更**（`moon.mod`、任一 `moon.pkg`、`tools/*.py`、`tools/*.sh`、`docs/port/golden/` 基准、产品源码 `src/**`、C 运行时 / 工具链版本）**必须复跑本 Task 全量**（30 条 §10.6 命令 + `moon check` / 三目标 build / native test 完整链 + `compare_golden` 全模式 + `compare_lowconf` + 12 个 U 状态核对），**禁止沿用旧绿**。

本轮**未变更任何共享配置**（判据：tracked 树 `git status` 无 `M`/`A`/`D`；`2215243..HEAD` 仅 3 个 artifacts 文档；`moon.mod` sha256 `7a8fe1d1…266e71458`；`expected.json` md5 `219519ee…ab3acd87`）。因此本轮绿全部产生于当前树，未复用 Task 12 的任何结果。

---

## 六、三要素回填小结（spec §8 共 22 行）

| 结论 | 行数 | 明细 |
|---|---:|---|
| 已回填（三要素齐备） | **15** | 8.1 native 档案加载（报告侧，spec 侧见 B-1）、8.1 空目录可检测、8.2 全部 8 行、8.3 三目标 build + 23 用例文件、8.4 位级三行 |
| 部分（缺 js / wasm-gc 观测） | **3** | 8.3 三目标主语言 / 语言数 / 条目合计 |
| 未完成（缺观测输出） | **4** | 8.1 js、8.1 wasm-gc 运行时、8.4 native-other 容差、8.4 js / wasm-gc 容差 |

缺三要素的行一律计「未完成」，**不以其他维度抵扣**（spec §8 Fail-3）。

---

## 七、配额与保留

| 项 | 上限 | 实际 |
|---|---|---|
| 时长 | 60 分钟 | **约 7.6 分钟**命令执行合计（30 命令 5.42 s + 完整链 7 s + 全模式 351.34 s + 低置信 19.87 s + Output 链 70.53 s + U-07 2.15 s + 收尾命令若干），含复核与撰写整轮远低于上限 |
| 外部调用轮次 | 10 | **0**（无 HTTP / 包管理器 / CI / 模型 API / `moon publish`） |
| 保留 | 报告永久、日志 90 天 | 已声明 |

---

## 八、限制与已知残余

1. js / wasm-gc 运行时与容差数值为**结构性不可达**（本机无 `node.exe`、无 `moonrun`），收缩声明已在 §3.1 逐字写入，**不得**读作等价实现。
2. `moon package` 的内容越界（B-2）**已关闭**（`680f744` 新增仓库根 `.moonignore`）：违禁条目 0，体积由 7 212 092 B / 360 文件降至 1 119 652 B / 46 文件（干净树口径）。`moon publish` 仍未执行，发布前需复跑 `moon package` 复核字节表。
3. U-06 的 spec 行未落档（B-1）；在授权前本项**不完整**。
4. 计划 11b 与 spec 423/424 的文本矛盾（B-3）未裁决；本轮按 spec 行 756 判绿。
5. 命令 27 的 rc 1→0 是计划明确的预期推进（B-02 关闭），已在日志中单列为「基线漂移」而非「新失败」。
6. `profile_counts` 的 `u06_*_ms` 是单次采样（本轮 187/318，Task 11 为 204/323），量级一致，不作为中位数口径使用。

RESULT: DONE_WITH_CONCERNS — 产品代码观测面全绿（30 命令 / 三目标构建 / 116 单测 / 268 golden / 双 seed 位级 / Output 链 rc=0）；js 与 wasm-gc 运行时按已声明交付范围收缩，10 项 `[LOCAL_DEAD_LINK]` 不判绿；**B-2 已在终审修复波中关闭**（`680f744`）。仍开放：B-1（U-06 spec 行）、B-3（11b 与 spec 423/424 矛盾）、B-4（spec §2A 映射文档缺口），外加 1 个 parked 用户决策（`set_prior_map` 失败后状态），均需用户 / controller 决策。

---

## 九、终审修复波（post-review fix wave，2026-10-23）

终审（whole-branch review，`192ce0e..58eb9cb`，26 commits / 60 files）判定 **Approved with fixes**：1 Critical + 5 Important + 9 minors。修复波 6 个提交，逐条对应：

| 级别 | 发现 | 处置 | 提交 | 验证 |
|---|---|---|---|---|
| **Critical** | 分支不自包含：`moon.mod` 未跟踪且被 `.git/info/exclude` 排除，`git archive HEAD \| tar -x && moon check` 报 "not in a Moon project" | 提交模块清单与全部参考输入；随后补齐被 tracked `docs/` 引用的 6 个生成器脚本 | `fa90bbb`（317 文件）+ `1395186`（6 生成器 / 1854 行） | 干净树 `git archive` → `moon check` rc=0、116/116、三目标 build rc=0、golden 双 seed 位级一致 |
| **Important** | `moon package` 打包含用户私密会话记录，非产品占 89.72 % | 新增仓库根 `.moonignore`（13 行）并重打包 | `680f744` | 违禁条目 **0**；7 212 092 B / 360 文件 → 1 119 652 B / 46 文件（见 B-2） |
| **Important** | 比对器存在永远为绿的通路：`prob_tolerance` 对任意目标恒 rc=0、`compare_lowconf --target` 被忽略、`Diagnostic.case` 缓存键忽略 mode、`-O` 下模块级 assert 失效 | 删除死参数与 always-green 分支；缓存键按 mode 分区；`-O` 守卫改为显式 `SystemExit` | `a0259aa` | `--target js --mode prob_tolerance` → **rc=2**；`compare_lowconf --target js` → **rc=2**；`python -O ... --mode prob_bits` → rc=0 且位级一致 |
| **Minor** | `char_of` 对越界码点静默回落为空格 | 改为 `abort` | `252f372` | 116/116 不变 |
| **Important** | `append` 在截断前物化整个数组 | 单趟截断，不再全量物化 | `a29cb4e` | 116/116、双 seed 位级一致；任一 gate 变化即回滚 |

**Parked，仍未关闭 —— `set_prior_map` 失败后状态**：上游 Python 在抛错前已安装全零向量，随后任一次检测会因 `sum = 0.0` 触发**未被捕获的 `ZeroDivisionError`**（落在文档化的 9 码契约之外）；本移植在失败后保持 `prior_map = None`，后续检测安静降级。两个测试（`detector_test.mbt`）锁定了当前行为。**两种修法都需先改 spec**（对齐上游 → 需把 `ZeroDivisionError` 纳入错误契约；保持现状 → 需在 spec §5.6 显式声明该差异），本会话**无 spec 编辑授权**，故作为**用户决策**挂起、不改代码。因此计划 `plan:1025` 的「✅ 一致」行**按此裁定即为不准确**（不是漏改，是被明确保留的不准确）。
