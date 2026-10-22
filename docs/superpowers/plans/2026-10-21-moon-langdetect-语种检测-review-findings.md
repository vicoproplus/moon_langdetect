# 计划复审发现登记表（DC-F）

> **文档标题（机器可检索）**：`moon_langdetect 语种检测实施计划复审发现登记表`
> **版本**：v1（2026-10-21）
> **审查对象**：`docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md`（1049 行 / 89,708 B，Task 0–Task 13）
> **审查依据**：`C:/Users/Administrator/.agents/skills/writing-plans/references/plan-reviewer-prompt.md`（Blocking Checks 全量 15 条）+ `SKILL.md` 九闸与 Self-Review Q1–Q70
> **上游权威**：spec v5.1、PRD、DESIGN、`约定 A：档案内嵌数据格式与生成契约`、`约定 B：U3 Unicode 大小写表生成契约`、`约定 C：golden 基准消费契约`、ADR、spec 复审登记表（§14 U-01…U-12）
> **审查方法**：计划声明的「已实测 / 已核对」断言全部由本审查员独立重跑；`file:line` 指针逐条落地核对；不采信计划自述。**本文件为唯一新增产物，未修改计划正文与仓库任何文件。**
> **评审视角**：独立评审（非降级自审）。

---

## 0. 审查结论

**Status: Issues Found**

| 等级 | 条数 |
|---|---|
| Blocking | 9 |
| Should-fix | 6 |
| Note | 4 |

**判据摘要**：计划的骨架质量高——30 条命令与 spec §10.6 **逐字一致（diff 为空，各 130 行）**、14 个 Task 的 Files/Interfaces/Steps/Output/时长/轮次/日志/允许修改文件清单字段齐备（14/14/14/15）、U-01…U-12 全部命中（10/5/5/5/5/5/3/5/3/3/7/9）、12 份 `[LOCAL_DEAD_LINK]` 手册齐备、无占位符、无实现代码。缺陷集中在**事实层（baseline rc 写错）、门禁自证伪能力（两条验收命令恒绿）、以及计划自行扩张的契约面（新增 `cmd/golden` 包与 `gen_core_tables.py` 未进 §4A GP1）**，另有两条 P0 需求（FR-13 空目录可检测、FR-24 零网络）无任何验收载体。

---

## 1. Blocking Checks 逐条判定（15 条，无汇总替代）

| # | 检查项 | 判定 | 依据 |
|---|---|---|---|
| 1 | Spec Coverage | **FAIL** | FR-13（空目录可检测，spec §8.1 行 612）与 FR-24/NE4-1（零网络，spec §9.4）在计划中零命中：`grep -n '空目录\|空临时\|mktemp' <plan>` → rc=1；`grep -n 'netstat\|NE4-1\|网络请求数' <plan>` → rc=1。详见 B-01 / B-02 |
| 2 | Executability | **FAIL** | M-01 含「以 `moon --help` 实测为准，不猜」的不确定性措辞；且 `moon --help` 实测无 runner 覆盖项（仅 `runwasm Deprecated…` 一行）。M-02 硬编码 `/opt/node`（本机不存在，实为 `probes/bin/node.cmd`）。详见 B-09 |
| 3 | Consistency | **FAIL** | Task 2 声明「未实现模式 `exit 3`」（行 494/501），Task 10/11/13 Output 却直接以 `--mode prob_bits` 为验收（行 799/830/884）；Baseline 行 44 写 cmd29 期望 rc=2，而同一文件行 312 注释写「② 空 fn main → 0」——**计划自相矛盾**。详见 B-03 / B-08 |
| 4 | Testability | **FAIL** | Task 0 验收 `grep -c '^| 命令'` 无法断言 30 行（实测：行格式为 `\| 命令 N \|` 时得 31，为 `\| N \|` 时得 1，均非 30，且 `grep -c` ≥1 命中即 rc=0）；Task 3 验收 `grep -vc` 在空集上输出 0 → 断言恒通过。详见 B-06 / B-07 |
| 5 | Granularity | PASS | `grep -n '^## Task '` → 14 行（Task 0–13）；每 Task 均含 Files / Interfaces / Steps / Output / 保留策略 / 时长上限 / 轮次上限；任务边界单一意图，可独立验证与回滚 |
| 6 | Authority-Source Alignment | PASS | Authority Alignment Table（行 892–931）逐行给 `file:line:方法`；`langdetect/langdetect/detector_factory.py:126/133/120/35/80/98/110/113/94/117`、`detector.py:99/114/132/141/73/93/76/70/146/223/234/56`、`language.py:7`、`lang_detect_exception.py:1,16`、`ngram.py:64/99/122`、`unicode_block.py:223` 全部落地；RNG/Neumaier 无上游行号时显式改用仓库实测证据（V-31…V-34），未伪造行号 |
| 7 | Spec-Plan Consistency | **FAIL** | Baseline Declaration（行 44）与实测冲突：`main.exe` 已存在且空 `fn main` → 命令 29 实跑 **rc=0**，非计划声称的 rc=2；B-01 据此虚构了一条不存在的基线缺陷。详见 B-03 |
| 8 | Field-Mapping Table | PASS | 逐 Task 核对 Files / Interfaces / Steps / Output 四块无空缺；Dependency Contract 表 17 行字段类型与 NULL 性逐字复制 spec §4.1/§4.3（`String` / `Array[Int]` / `Map[String, Int]` / `Double` / `String?`） |
| 9 | Acceptance Command Verification | **FAIL** | 新增可执行包 `src/core/cmd/golden`（行 779）与新增生成器 `tools/gen_core_tables.py`（行 631）**均未在 spec §4A GP1 表登记**（`grep -n 'cmd/golden' spec` → rc=1；`grep -n 'gen_core_tables' spec` → rc=1），违反「每条命令引用的每个路径反查四要素」。详见 B-04 / B-05 |
| 10 | Spec-Decision Traceability | **FAIL** | D-02（`unicode_block` 职责扩至 `src/unicode/`）与 D-03（新增 `cmd/golden`）均被标 `ALIGN-SPEC`，但两者都**改变了 spec 已确认的模块职责表与落点表**，属「修订 spec」而非「以 spec 为准」。详见 B-04 / S-01 |
| 11 | Compile-Probe Task 0 | **FAIL** | Task 1 确为三目标最小编译探针（`moon build --target native/js/wasm-gc`），位置正确；但 Task 0 自身的验收命令不可证伪（B-06），基线门实际为空转 |
| 12 | External-Dependency Verification | **FAIL** | `moonrun` / 官方 node 两条外部依赖的回补手册含未验证指令与不存在路径（B-09）；wasm-gc 分支虽有 `[LOCAL_DEAD_LINK]`，但 M-01 的「`export MOON_RUNNER`」未经核实 |
| 13 | Golden-Vector Local Baseline | PASS | 本地独立基准齐备：`md5 docs/port/golden/expected.json` = `219519ee19d7cc10d404ddbdab3acd87`；`cases.jsonl / expected.json / summary.json / timing.json / rand / float_add_compare.json / float_add_python.json / char_isupper_compare.json / char_upper_impact.json` 全部在位；Task 4 全码点对拍、Task 7 512/307/385 组均置于集成前 |
| 14 | Incremental Review Checkpoints | PASS | Task 3/4/5/6/7/8/9/10/11 后各插一个 V1（单一执行者整变更验证）+ V3（单一审查者），非末尾集中；Task 12/13 为全量复跑与终验 |
| 15 | `[LOCAL_DEAD_LINK]` Marking | PASS | 12 处标注（行 332–343）逐项带「验证地点/方式 + 回补手册编号」，与 spec §14 U-01…U-12 一一对应；无未标注的远端验收项（U-06/U-07 的双重登记问题见 S-05） |

**统计：PASS 6 / FAIL 9 / N-A 0。**

---

## 2. Blocking（必须修才能进 Execute）

### B-01 FR-13「空目录下可检测」（P0）无验收载体

**证据（我跑的）**：

```
$ grep -n '空目录\|空临时\|mktemp\|cd <' docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md
（无输出，rc=1）
$ sed -n '612p' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
| 空目录下可检测 | native (win32 x64) | `cd <空临时目录> && /f/moonbit比赛/moon_langdetect/_build/native/debug/build/src/core/cmd/main/main.exe`（**当前该入口为空 `fn main { }`，尚未调用 `detect`**；detect 链路待实现） | PRD FR-13 | — | 未验证（实现期产物；回补触发 = `main.mbt` 填入 detect 调用；填入前不计已验证） |
```

**问题**：spec §8.1 把「空目录下可检测」列为独立验收行（P0 / FR-13 / US-06），计划全文零提及。C1 走查链路（行 175）只覆盖「加载 55 档案 → detect 长文本」，未验证「cwd 无任何数据文件时仍可检测」——而这正是 FR-13 的核心（内嵌数据 vs 目录依赖）。Task 9 只验证「静默」，不验证「空目录可运行」。

**改法**：Task 9 或 Task 12 增一步：`d=$(mktemp -d) && cd "$d" && /abs/path/main.exe >/tmp/o 2>/tmp/e; rc=$?; test $rc -eq 0`，并把该链路补入 C1（入口 → 关键操作 → 可观察结果三要素）。

---

### B-02 FR-24 / NE4-1「网络请求数 = 0」（P0）无验收载体

**证据（我跑的）**：

```
$ grep -n 'netstat\|NE4-1\|网络请求数' docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md
（无输出，rc=1）
$ sed -n '754p' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
| NE4-1 | **检测期间网络请求数 = 0** | 调用前后对外连接数差 = 0 | `netstat -an` 前后对比（或在沙箱内禁止网络后检测仍成功） |
```

**问题**：计划的 Error Scenario Matrix 显式写「本库无外部网络端点」（行 125），据此把 A7 判 N/A；但 NE4-1 不是「端点契约」而是**运行时副作用断言**，与端点无关。G-05（PRD 目标）因此完全没有可复跑证据。

**改法**：Task 10 或 Task 12 增一条 `netstat -an | sort > /tmp/before.txt` → 跑 `cmd/golden` 一次 detect → `netstat -an | sort > /tmp/after.txt` → `diff` 断言新增连接 0；或 `unshare -n` / 防火墙断网后跑同一命令断言 rc=0。二者择一，写入 C1 走查。

---

### B-03 Baseline 事实错误：命令 29 期望 rc=2，实测 rc=0（计划自相矛盾）

**证据（我跑的）**：

```
$ ls _build/native/debug/build/src/core/cmd/main/
__moonbit_link_core__  main.core  main.exp  main.lib  main.exe
$ test -x ./_build/native/debug/build/src/core/cmd/main/main.exe || exit 2
$ ./_build/native/debug/build/src/core/cmd/main/main.exe >/tmp/o.txt 2>/tmp/e.txt || exit 1
$ test ! -s /tmp/o.txt && test ! -s /tmp/e.txt
rc29=0
```

**计划原文（两处互斥）**：

```
行 44: - **预期基线（红绿）**：… 命令 29 期望 rc=2（`main.exe` 未构建）。
行 312: #   ① 二进制缺失 → 2；② 空 fn main → 0；③ println("x") → 1；④ println("") → 1；⑤ 只输出单个换行 → 1
行 46: - B-01 命令 29 rc=2（`main.exe` 未构建）→ 本计划 Task 9 修复。
行 852: 3. 逐条运行 spec §10.6 命令 1-30；与 Task 0 基线逐项比对（命令 27 现应为 rc=0，命令 29 应为 rc=0）。
```

**问题**：`main.exe` 已构建且 `fn main` 为空 → 命令 29 恒 rc=0。计划行 44 与行 46 的「预期基线」是**错的**，且与行 312 注释、行 852 的 Task 12 期望**互相矛盾**。后果：Task 0 会把「rc=0」记成「基线红」，B-01 这条基线缺陷根本不存在，Task 9 的「修复」目标失真；后续每次回归比对都会带着这条假红。

**改法**：行 44 改为「命令 29 期望 rc=0（空 `fn main` 静默）」；B-01 改为「命令 29 基线 rc=0，Task 9 必须保持 rc=0 且新增 detect 调用后仍静默」；并在基线 md 中附本次实测输出（`rc29=0`）。

---

### B-04 新增包 `src/core/cmd/golden` 越出 spec §4A，且被 NE1 白名单漏检

**证据（我跑的）**：

```
$ grep -n 'cmd/golden' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
（无输出，rc=1）
$ grep -n '^| `src/' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
411:| `src/core/` | …
415:| `src/data/profiles.mbt` | …
416:| `src/unicode/upper_table.mbt` | …
419:| `src/core/cmd/main/moon.pkg` | 静默性验证用可执行包的清单 …
420:| `src/core/cmd/main/main.mbt` | 可执行入口 …
# NE1 白名单盲区实验
$ mkdir -p /tmp/ne1probe/src/core/cmd/golden && printf 'fn main { println("x") }\n' > /tmp/ne1probe/src/core/cmd/golden/main.mbt
$ grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt /tmp/ne1probe/src/core
src/core\cmd\golden\main.mbt:1:fn main { println("x") }        ← rc=0（命中）
$ grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt /tmp/ne1probe/src/core | grep -vE '[\\/]cmd[\\/]'
（无输出）                                                      ← rc=1（0 行，静默漏检）
```

**问题**：
1. spec §4A 只登记 `src/core/cmd/main` 为唯一可执行包；`cmd/golden` 在 spec 中**零命中**，无 GP1 四要素（生成时点 / 责任单元 / 生成命令 / 校验命令）。
2. NE1 静态门（计划行 236）用 `grep -vE '[\\/]cmd[\\/]'` 排除**整个 `cmd/` 路径段**，因此新包里的任何 `println` 都不会被 NE1 检出——实验已证（无过滤 rc=0 命中，加过滤 rc=1 空）。spec §9.4 的 cmd 例外本意是「只放过 `cmd/main` 这一个刻意静默的载体」，计划把例外扩成了「整个 cmd 子树免检」。
3. M-06 手册（行 385）依赖 `_build/native/debug/build/src/core/cmd/golden/main.exe`，该路径同样无 GP1 登记。

**改法（择一，且必须回 spec 登记）**：
- 方案 A：把诊断 CLI 移到非 `cmd/` 路径（如 `src/core/golden_cli/`），NE1 无需放宽，但需在 §4A 新增一行 GP1；
- 方案 B：保留 `cmd/golden`，同时（a）在 spec §4A 补 GP1 四要素行，（b）把 NE1 收窄为 `grep -vE '[\\/]cmd[\\/]main[\\/]'`（只放过 main），并在 spec §9.4 同步修订该例外范围。
- 两种方案都要在 `Slice Checkpoint S3` 增一条「诊断 CLI 自身输出不得混入 `cmd/main` 的静默性判据」。

---

### B-05 `tools/gen_core_tables.py` 未登记 §4A GP1，生成链断裂

**证据（我跑的）**：

```
$ grep -n 'gen_core_tables' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
（无输出，rc=1）
$ grep -n 'gen_core_tables' docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md
631:- `tools/gen_core_tables.py` — 新增（从 `langdetect/langdetect/utils/ngram.py:64-260` 转写）
635:- `[允许修改文件清单]`：`src/core/**`（不含 `cmd/**`）、`tools/gen_core_tables.py`、artifacts 日志
```

**问题**：Task 6 引入新生成器 + 新产物 `src/core/ngram_tables.mbt`，但 §4A 只登记 `gen_profile_data.py`、`gen_upper_table.py`、`compare_golden.py`、`compare_lowconf.py`。findings §41.2 要求「生成器 → 产物 → 验收」三条独立链；此链缺 spec 侧登记，产物无校验命令、无所有权声明（约定 A/B 的「不手改清单」也不覆盖它）。

**改法**：回 spec §4A 补 GP1 四要素行（生成命令 `python tools/gen_core_tables.py`、校验命令、覆盖行为「整文件重建」、不手改清单），并在计划 Task 6 的 dry-run 中断言「产物行数 / 12 块 / 11 臂 / 126 组 / 6667 键」。

---

### B-06 Task 0 验收命令无法证伪「30 行」

**证据（我跑的）**：

```
$ printf '| 命令编号 | 命令 | rc | 关键输出 | 处置 |\n|---|---|---|---|---|\n' > /tmp/t0b.md
$ for i in $(seq 1 30); do printf '| 命令 %s | x | 1 | y | z |\n' "$i" >> /tmp/t0b.md; done
$ grep -c '^| 命令' /tmp/t0b.md
31                                    ← 表头也被计入，且 ≠ 30
$ printf '| 1 | x | 1 | y | z |\n' … （30 行）
$ grep -c '^| 命令' /tmp/t0b.md
1                                     ← 若行格式不含「命令」二字，只剩表头
```

**问题**：计划 Output（行 460）为 `test -s baseline.md && grep -c '^| 命令' baseline.md`，但（a）基线表的行格式未定义（行 447 只给列名，未给行模板），（b）`grep -c` 只要 ≥1 命中即 rc=0，**永远不会失败**，（c）即使命中数正确，`grep -c` 的输出也没有被 `test` 断言等于 30。Compile-Probe Task 0 的门禁因此是空转的。

**改法**：固定行模板为 `| 1 | … |` 形式，命令改为
`test "$(grep -cE '^\| [0-9]+ \|' docs/superpowers/plans/artifacts/baseline-2026-10-21.md)" -eq 30`
（实测该正则对 30 行输出 30）。

---

### B-07 Task 3 A9 验收命令空集即通过（vacuous pass）

**证据（我跑的）**：

```
$ out=$(printf '' | grep -vc 'non-native fallback'); echo "out=[$out] rc=$?"
out=[0] rc=1
$ if test "$out" = "0"; then echo "ASSERTION_WOULD_PASS (vacuous)"; fi
ASSERTION_WOULD_PASS (vacuous)
```

**计划原文（行 542）**：
`moon test --target native && moon build --target js && moon build --target wasm-gc && test "$(grep -rn '@math\.ln(' --include=*.mbt src | grep -vc 'non-native fallback')" = "0"`

**问题**：若 `src/` 中根本没有 `@math.ln(`（例如降级分支写成别的形态、或 native-only 实现），`grep -vc` 输出 0，断言通过。这条命令证明不了「js/wasm-gc 走 `@math.ln` 且带标记」，也证明不了「native 用 libm `log`」——A9 冒烟的判据落空。位型断言 `0x3FE62E42FEFA39EF` 在 Steps（行 535）里写了，但**没有进入 Output 验收命令**。

**改法**：
```
test "$(grep -rn '@math\.ln(' --include=*.mbt src | wc -l)" -ge 1 \
&& test "$(grep -rn '@math\.ln(' --include=*.mbt src | grep -vc 'non-native fallback')" = "0" \
&& test "$(grep -rn 'extern "C" fn .*= "log"' --include=*.mbt src | wc -l)" -ge 1
```
并把位型断言（`ln_for_gauss(2.0)` = `0x3FE62E42FEFA39EF`）写进同一 Output 的测试名。

---

### B-08 Task 2 `exit 3` 契约与 Task 10/11/13 验收形态冲突

**证据**：

```
$ grep -n 'exit 3\|mode not implemented' <plan>
494:- `tools/compare_golden.py` — 新增（仅参数骨架与 `--self-check`；产品比对模式显式 `exit 3`）
501:- 未实现模式：打印 `mode not implemented` 并 `exit 3`（不得静默返回 0）
$ grep -n 'mode prob_bits' <plan>
799:- 验收命令：`… tools/compare_golden.py --target native --seed 0 --mode prob_bits && …`
830:- 验收命令：`moon build … && … compare_golden.py --target native --seed 0 --mode prob_bits`
884:- 验收命令：`moon check && … && … compare_golden.py --target native --seed 0 --mode prob_bits && …`
```

**问题**：Task 2 定义的接口契约（未实现模式 `exit 3`）与 Task 10/11/13 的 Output 形态**互斥**。V4 线性序本身成立（Task 2 只跑 `--self-check`，可独立通过），但执行者在 Task 2 阶段若按「接口契约」预跑 Task 10 的验收命令会得到 `exit 3` 假红；反之若 Task 10 忘记改写该契约，后续读者无法判断 `exit 3` 是缺陷还是设计。属一致性缺陷。

**改法**：Task 2 的 Interfaces 增加一句「`prob_bits` / `seed_semantics` / `failures` / `forensics` / `cleaning` / `features_cache` / `profile_counts` / `repeatability` / `top1` / `lang_list_len` / `entry_total` / `prob_tolerance` 于 **Task 10 交付**，在此之前 `exit 3` 为**预期**」；Task 10 首步声明「移除 `exit 3` 占位，改为真实实现」。

---

### B-09 外部依赖回补手册不可照抄执行（M-01 / M-02）

**证据（我跑的）**：

```
$ C:/Users/Administrator/.moon/bin/moon.exe --help 2>&1 | grep -inE 'runner|wasm'
11:  runwasm                Deprecated: use moon run --target wasm locally or moonx for registry packages
（无 runner 覆盖项）
$ ls probes/bin
node.cmd
```

**计划原文**：
```
行 350: 1. **路径与命令**：… 若 moon 仍指向内置 `moonrun.exe`，用 `export MOON_RUNNER="$WASM_RUNNER"` 覆盖（以 `moon --help` 实测为准，不猜）。
行 357: 1. **路径与命令**：安装 Node LTS 到 `/opt/node`；`export PATH="/opt/node/bin:$PATH"`；…
```

**问题**：
1. M-01 的 `MOON_RUNNER` 环境变量**未经核实**（`moon --help` 无此项），且手册自己写了「以实测为准，不猜」——这正是 reviewer 清单第 2 条要拦的「意图性描述」。回补触发时执行者仍需现场试错。
2. M-02 硬编码 `/opt/node`（本机不存在；仓库已有 `probes/bin/node.cmd` 绕行载体），且 Windows 下 `/opt` 无意义。
3. 两份手册的「部署路径与命令」不是「照抄即可执行」。

**改法**：
- M-01：先给出**实测确认**的替换方式（若无 runner 覆盖项，则明确写「本机 moon 不支持外部 wasm runner，回补须在装有可运行 `moonrun` 的机器上执行，命令 = `moon test --target wasm-gc`，取证 = 该机器 `moonrun --version` + 测试日志」），删去「不猜」类措辞。
- M-02：改为 `export PATH="$(pwd)/probes/bin:$PATH"`（相对路径），并在手册中注明该 shim 指向 bun 1.4.3，官方 node 到位后替换 `probes/bin/node.cmd`。

---

## 3. Should-fix

### S-01 D-02 属「修订 spec」而非「以 spec 为准」

`unicode_block` 的职责被扩到 `src/unicode/`（Task 4 Files / Interfaces），但 spec §0A D2 模块职责表（行 46）只写「字符属性：`is_upper_cp312` + U3 表产物」。计划把 §2A 的测试落点当作职责授权，标 `ALIGN-SPEC`。建议改为「**修订 spec**」：在 §0A D2 行 46 补「`unicode_block` 区块表」；否则后续审查会按 D2 判越界。

### S-02 Task 5 断言产品产物字节数 = 2205308（约定 A §5 已声明须重新登记）

约定 A §5 明确：「字节数 2205308 是探针样本的实测值；产品产物若注释不同，A3 以产品路径重新登记基准值」。Task 5 Output（行 617）直接 `test "$(wc -c < src/data/profiles.mbt)" = "2205308"`，把探针值当产品值。建议改为「首次生成后实测登记，后续以登记值为基线」，并保留 A1/A2 的 55 / 184129 硬断言。

### S-03 B-03 的假绿范围写窄了

计划行 48 只列「命令 1-4 / 9-11」为空集假绿，实际 5–8 / 12–14 在空 `src/` 上同样是空集扫描。建议统一写「命令 1-14 全部依赖非空扫描面；Task 6 首个 `.mbt` 落地后整体复跑」。

### S-04 Task 8 验收只断言 `pub fn` 数量 > 0

行 734：`test "$(grep -rn '^pub fn' --include=*.mbt src | wc -l)" -gt 0` —— 任意一个公开函数即可通过，证明不了 spec §5.1–§5.10 的 10 组签名齐备。建议改为逐个签名 `grep -q`（`detect` / `detect_langs` / `detect_with_confidence` / `get_lang_list` / `debug_vector_len` / `set_seed` / `set_prior_map` / `set_max_text_length` / `ln_for_gauss` / `is_upper_cp312`），并断言 `LowConfidence` / `Detected` / `LangProb` / `LangDetectError` 四个类型存在。

### S-05 U-06 / U-07 的「死链」与「本机执行」双重登记

计划行 337 把「首次加载解析耗时」标 `[LOCAL_DEAD_LINK]`（U-06），但 Task 10 Step 6 要求**本机**测量并回填；行 338 把 `gen_upper_table.py --verify` 标 `[LOCAL_DEAD_LINK]`（U-07），但 Task 4 Output（行 580）要求它**本机** rc=0。同一判据既「本机不可验」又「本机必跑」，会让 Task 13 的 U 状态表出现双账。建议：把这两项在 U 表中标「本机已可执行（执行后回填）」，仅保留「跨平台/跨运行时」部分为死链（U-05/U-11 保留）。

### S-06 Task 6 的「12 块 / 11 臂 / 126 组 / 6667 键」无独立校验命令

Steps 第 4 步只说「读行数与计数」，Output 只跑 `moon check && moon test`。建议把 `约定 A` 式的外部计数命令写进 Output（例如 `.venv/Scripts/python.exe tools/gen_core_tables.py --verify` 输出四元组并在 Output 中断言），否则该 dry-run 无法证伪。

---

## 4. Note（不阻塞）

- **N-01** 30 条命令与 spec §10.6 **逐字一致**（`diff` 为空，各 130 行），作者自述属实。
- **N-02** `[LOCAL_DEAD_LINK]` 12 条与 spec §14 U-01…U-12 一一对应，U 编号命中数 10/5/5/5/5/5/3/5/3/3/7/9，全部 ≥3。
- **N-03** 无占位符：`grep -nE 'TODO|FIXME|TBD|XXX|待补'` 零命中；出现的 `...` 均为 spec 原文引用、`<task>` 日志路径模板、`detector.py:146-171` 行号区间与 `Some(...)` 反例说明，不构成占位符。
- **N-04** 计划的 V4 排序链（Task 1<2+；2<10；3<7；4<6；5<7；7<8；8<9；9<10；10<11；11<12；13 最后）与线性序逐条同向，无倒序引用。

---

## 5. DC-F 登记表

| 编号 | 定义原文（摘要） | 销项证据（复跑命令 + 输出 + rc） | 状态 |
|---|---|---|---|
| B-01 | Spec Coverage：PRD P0 要件全覆盖或有显式延后 | 已销项：计划 S3 走查门新增 **C5（FR-13 空目录可检测）**；Task 9 Step 6 与 Output 三串链（C4+C5+NE1b）含 `d=$(mktemp -d) && cd "$d" && "$OLDPWD/…/main.exe"`。实跑：`rc=0`、`out/err 均 0 字节`；`grep -n mktemp plan` 命中。 | 已销项 |
| B-02 | Spec Coverage：P0 要件全覆盖 | 已销项：C6（NE4-1）进 S3 清单；Task 10 Step 8 + Output 单链：`netstat -an \| sort` → 运行 detect → 再 `netstat` → `test "$(diff … \| grep -c '^>')" -eq 0`。本机实跑：netstat 可用（`C:\Windows\system32\netstat.exe`），`c6_rc=0`；人为注入 1 行 → rc=1。`.venv` 无 `psutil`（ImportError）已登记为禁用降级。计划另写明「A7（端点契约）= N/A」与「NE4-1（运行时副作用断言）」不可互相豁免。 | 已销项 |
| B-03 | Spec-Plan Consistency / 定量断言须可重跑 | 已销项：计划预期基线改为「命令 29 期望 rc=0」；原「B-01 命令 29 rc=2」改为「非缺陷，Task 9 须保持 rc=0」；附实测 `rc29=0`（`test -x main.exe` rc=0，运行后 stdout/stderr 均 0 字节）。三处一致：预期基线 / 命令 29 注释 / Task 12 期望。 | 已销项 |
| B-04 | Acceptance Command Verification / 每个路径反查 GP1 四要素 | 已销项（方案 2，用户裁决）：新增**命令 11b**（置于 30 条 verbatim 块之外，以保持 30 条 diff 为空），`grep -vE '[\\/]cmd[\\/]main[\\/]'`；Task 9 Output 三串链含 11b；S1 静态门登记 11b；D-03 改判 **修订 spec**（§4A 补 `cmd/golden` GP1 两行 + §9.4 NE1 例外收窄为仅 `cmd/main/`）。T2 实录见本文件 §6.7。 | 已销项 |
| B-05 | 同上 / 生成器→产物→验收三链 | 已销项（保留生成器 + 修订 spec）：Task 6 Step 4 dry-run 改为跑 `tools/gen_core_tables.py --verify`，断言 `12/11/126/6667`（口径已实测：块 = 12 个 `UNICODE_*` 常量；臂 = 11 处 `block ==`/`block in`；组 = `NGram.CJK_CLASS` = 126；键 = `NGram.CJK_MAP` = 6667）；D-04 改判 **修订 spec**（§4A 补生成器 + 产物 GP1 行）。 | 已销项 |
| B-06 | Testability：每条验收可证伪 | 已销项：Task 0 Interfaces 固定行模板 `\| N \| … \| rc \| … \| … \|`；Output 改 `test "$(grep -cE '^\| [0-9]+ \|' …baseline-2026-10-21.md)" -eq 30`。实跑：30 行表 → 30 / rc=0；仅表头 → 0 / rc=1；29 行 → rc=1。 | 已销项 |
| B-07 | Testability / 禁止 vacuous pass | 已销项：Task 3 Output 改四判据串联（`@math\.ln(` ≥ 1 → 未标记行 = 0 → `extern "C" fn … = "log"` ≥ 1 → 位型 `3FE62E42FEFA39EF` 出现在测试文件）。T2 实录见本文件 §6.7。 | 已销项 |
| B-08 | Consistency：接口契约前后一致 | 已销项：Task 2 Interfaces 新增「交付分期」——十二个产品模式于 Task 10 交付，此前 `exit 3` 为预期且不作 Task 2 验收对象；Task 10 Step 0 显式「移除 `exit 3` 占位，改为真实实现」，要求 `grep -n 'exit 3' tools/compare_golden.py` 0 命中。 | 已销项 |
| B-09 | Executability / External-Dependency Verification | 已销项：M-01 改为「本机 `moon --help` 无 runner 覆盖项（实测仅 `runwasm Deprecated`）、`moon --version` 尾部 exit 255 → 回补 = 异地执行（换机器）」并删除 `MOON_RUNNER` 与「不猜」措辞；M-02 改 `export PATH="$(pwd)/probes/bin:$PATH"`（实测含 `node.cmd` → bun 1.4.3）+ `<NODE_BIN>` 占位。`grep -n '不猜\|/opt/node' plan` → 0 命中。 | 已销项 |
| S-01 | Spec-Decision Traceability：分歧须显式裁决 | 已销项：D-02 由 `ALIGN-SPEC` 改判 **修订 spec**（§0A D2 行 46 未含 `unicode_block`；执行前须回 brainstorming 补职责行）。 | 已销项 |
| S-02 | 约定 A §5：产品 A3 须重新登记 | 已销项：Task 5 Files / Step 4 / Output 三处去掉产品字节 `2205308` 硬断言，改为「探针沿用 2205308、产品侧首次生成实测登记」；硬判据保留 C-A1 `decls 55` / C-A2 `entries 184129`。 | 已销项 |
| S-03 | 空集假绿登记完整性 | 已销项：预期基线改为「命令 1-14 全部依赖非空扫描面」；Task 6 Step 7 复跑 DR9/DR10/DR11 关闭空集风险。 | 已销项 |
| S-04 | 验收判据强度 | 已销项：Task 8 Output 改十组签名 + 四类型逐项 `grep -rq`。实跑：全在 → rc=0；删 `debug_vector_len` → `MISSING: pub fn debug_vector_len(` / rc=1。 | 已销项 |
| S-05 | `[LOCAL_DEAD_LINK]` 语义一致 | 已销项：U-06 / U-07 从死链清单移出（本机可执行），仅留 Carry-over 表；重核死链集合 = {1,2,3,4,5,8,9,10,11,12}，Carry-over 表 = {1…12}，差集恰为 {6,7}。 | 已销项 |
| S-06 | V2 dry-run 须可证伪 | 已销项：Task 6 Step 4 与 Output 均含 `tools/gen_core_tables.py --verify` 四元组断言（与 B-05 同批销项）。 | 已销项 |
| N-01 | 命令逐字复制 | `diff <spec 命令块> <plan 命令块>` → IDENTICAL（130 / 130 行） | 已销项 |
| N-02 | U 编号机械检索 | `grep -c` 逐编号：10/5/5/5/5/5/3/5/3/3/7/9 | 已销项 |
| N-03 | 占位符零命中 | `grep -nE 'TODO\|FIXME\|TBD\|XXX\|待补'` → rc=1 | 已销项 |
| N-04 | V4 排序自洽 | 11 条先后引用逐条与线性序同向 | 已销项 |

---

## 6. 我实际执行的核验命令实录（摘要）

### 6.1 环境与基线

```
$ grep --version | head -1          → grep (pi-uu-grep) 0.2.0
$ md5sum --version | head -1        → md5sum 0.8.0
$ C:/Users/Administrator/.moon/bin/moon.exe --version → moon 0.1.20261012 (748b63c) / moonc v0.10.15+943464bfa
$ C:/Users/Administrator/.moon/bin/moon.exe --version（尾部）→ Error: failed to get "…moonrun.exe" version（exit 255）
$ .venv/Scripts/python.exe -V       → Python 3.12.10
$ moon check                        → Finished. moon: no work to do（rc=0）
$ md5sum docs/port/golden/expected.json → 219519ee19d7cc10d404ddbdab3acd87
$ tr -d '\r' < moon.mod | grep -q '^name = "vicoproplus/langdetect"$' → rc=0
$ find src -type f | sort           → 6 个脚手架文件
$ ls _build/native/debug/build/src/core/cmd/main/ → main.exe 已存在
```

### 6.2 spec §10.6 能力自检

```
$ <spec §10.6 九项自检块逐字执行>
SELFCHECK_OK        rc=0
```

### 6.3 30 条命令逐条实跑（cwd = 仓库根）

| 命令 | 计划期望 | 我实测 rc | 判定 |
|---|---|---|---|
| 1–14 | rc=1 | 全部 rc=1 | ✅ 一致 |
| 15 | rc=0 | 0 | ✅ |
| 16 | rc=0（输出 `ok`） | 0（`ok`） | ✅ |
| 17 | rc=0（`ok`） | 0（`ok`） | ✅ |
| 18 | rc=0（`ok`） | 0（`ok`） | ✅ |
| 19 | rc=0（`ok`） | 0（`ok`） | ✅ |
| 20 | rc=0（`ok 1951 cps / 651 intervals`） | 0（同左） | ✅ |
| 21 | rc=0 | 0 | ✅ |
| 22 | rc=0 | 0 | ✅ |
| 23 | rc=0 | 0 | ✅ |
| 24 | rc=0 | 0 | ✅ |
| 25 | rc=0 | 0 | ✅ |
| 26 | 期望输出 25 | 正确文件名 → 25，rc=0；文件名打错时 → 0，rc=1 | ✅（文件名须逐字） |
| 27 | rc=1 | 1（0 行） | ✅ |
| 28 | rc=0 | 0 | ✅ |
| **29** | **计划行 44 期望 rc=2** | **0** | ❌ **B-03** |
| 30 | rc=0 | 0 | ✅ |

### 6.4 结构 / 机械检索

```
$ grep -n '^## Task ' <plan> | wc -l                → 14
$ grep -c '时长上限' <plan>                          → 14
$ grep -c '外部调用轮次上限' <plan>                   → 14
$ grep -c '允许修改文件清单' <plan>                   → 15（14 Task + W1 声明行）
$ grep -c 'U-01'…'U-12'                              → 10/5/5/5/5/5/3/5/3/3/7/9
$ grep -c 'M-01'…'M-12'                              → 13/4/3/6/5/3/3/4/4/4/4/6
```

### 6.5 逐字一致性

```
$ sed -n '/^# 命令 1：/,/^```$/p' <spec> | sed '$d' > /tmp/spec_cmds.txt   # 130 行
$ sed -n '/^# 命令 1：/,/^```$/p' <plan> | sed '$d' > /tmp/plan_cmds.txt   # 130 行
$ diff /tmp/spec_cmds.txt /tmp/plan_cmds.txt
IDENTICAL
```

### 6.6 允许修改文件清单交集

Task 6 / 7 / 8 均为 `src/core/**`（不含 `cmd/**`）——**串行执行、非并行 worker**，不构成越界；Task 9 `src/core/cmd/main/**` 与 Task 10 `src/core/cmd/golden/**` 无交集。判定：无重叠违规（W1 已声明 `N/A — no parallel workers`）。

---

## 7. 带进执行阶段的已知未闭合项（不构成本次阻塞）

| 编号 | 内容 | 承接任务 | 状态 |
|---|---|---|---|
| U-01 / U-08 | wasm-gc `moon test` 不可达（本机 `moonrun.exe` 无法启动，实测 exit 255） | Task 11（仅 build） | 环境不可达 |
| U-02 | js 仅 bun 替代运行时（`probes/bin/node.cmd` 存在） | Task 11 | 环境不可达 |
| U-03 | mooncakes 体积 / 文件数限制未取证 | Task 12（`moon package` 只记录） | 未取证 |
| U-04 / U-12 | js / wasm-gc 概率容差未校准 | Task 11（只记录不判绿） | 指标未测 |
| U-05 / U-11 | 跨平台 libm 位级一致 | Task 11（限 native win32 x64） | 环境不可达 |
| U-06 | 首次加载解析 184129 条耗时 | Task 10（本机实测，见 S-05） | 待回填 |
| U-07 | `isupper` vs `Uppercase` 全码点口径 | Task 4（本机 `--verify`，见 S-05） | 待回填 |
| U-09 / U-10 | 三目标语言数 / 条目合计 / 主语言一致 | Task 11 | 依赖 U-01/U-02 |
| 实现期产物 | `gen_profile_data.py`、`gen_upper_table.py`、`compare_golden.py`、`compare_lowconf.py`、`gen_core_tables.py`、4 个 `*_test.mbt`、`main.mbt` 的 detect 调用 | Task 2/4/5/6/8/9/10 | 未验证（实现期产物） |

---

## 8. 建议的修订顺序

1. **B-03**（一行事实修正 + 附实测输出）——最先做，否则后续所有回归比对都带假红。
2. **B-06 / B-07**（把两条恒绿门禁改成可证伪）——门禁先可信，基线才有意义。
3. **B-04 / B-05**（回 spec 补 §4A GP1 + 收窄 NE1 例外）——需 spec 侧修订，改完再同步计划 Task 10 / Task 6。
4. **B-01 / B-02**（补 FR-13、FR-24 验收行与走查链路）。
5. **B-08 / B-09** 与 S-01…S-06。
6. 重跑 30 条命令与 Task 0 验收命令，确认基线表可证伪、rc 表与实测一致。

---

**文档结束**

---

## 6.7 v2 销项 T2 对照实录（2026-10-21 复跑）

| # | 修复前形态（假绿） | 修复后形态（必红） | rc |
|---|---|---|---|
| B-06 | `grep -c '^| 命令'` 对 30 行表 → **31**（表头被计入），且 `grep -c` ≥1 即 rc=0，永不失败 | `test "$(grep -cE '^\| [0-9]+ \|' …)" -eq 30`：30 行 → 30 / rc=0；仅表头 → 0 / **rc=1**；29 行 → **rc=1** | 0 / 1 |
| B-07 | `out=$(printf '' \| grep -vc 'non-native fallback')` → `out=0`、`rc=1`、`test "$out" = "0"` → **PASS（空集假绿）** | `test "$(printf '' \| grep -vc 'zzz')" -ge 1` → **rc=1（空集被拦截）**；`test "$(printf 'a\n' \| grep -vc 'zzz')" -ge 1` → rc=0 | 1 / 0 |
| B-04 | 样本 A（`cmd/golden/main.mbt` 含 `println`）：旧过滤 `grep -vE '[\/]cmd[\/]'` → **rc=1（0 行，静默漏检）** | 新过滤 `grep -vE '[\/]cmd[\/]main[\/]'` → **rc=0（命中 1 行，正确拦截）**；样本 B（仅 `cmd/main` 含 `println`）→ **rc=1（正确豁免）** | 1 / 0 |
| B-02 | 计划无 netstat 命令（零载体） | `netstat -an \| sort > before` → 跑 detect → `> after` → `test "$(diff … \| grep -c '^>')" -eq 0` → **rc=0**；注入 1 行 `ESTABLISHED` → **rc=1** | 0 / 1 |
| S-04 | `grep -rn '^pub fn' \| wc -l` -gt 0（任一函数即过） | 十组签名 + 四类型逐项 `grep -rq`：全在 → rc=0；删 `debug_vector_len` → `MISSING: pub fn debug_vector_len(` / **rc=1** | 0 / 1 |

**环境事实**：`netstat` = `C:\Windows\system32\netstat.exe`（rc=0）；`.venv` 无 `psutil`（`ImportError`），故降级通道登记为 `.venv/Scripts/python.exe` + `subprocess` 集合差，并禁用 psutil 方案。

---

## 6.8 结论（v2）

**Status: 9 Blocking + 6 Should-fix 全部销项**；4 条 Note 维持原判定（N-01/N-02/N-03/N-04 无需改动）。
计划升 v2；D-02 / D-03 / D-04 三条裁决为 **修订 spec**，执行前须回 brainstorming 修订 spec（§0A D2 行 46、§4A GP1 表、§9.4 NE1 例外范围）。

---

# 第二轮复审（v2）

> **审查对象**：`docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md` v2（1092 行 / 102,575 B）
> **审查方法**：15 条销项逐条回读计划改动 + 本审查员独立实跑；作者 T2 声明一律重跑复现，不采信自述。
> **结论**：**Issues Found**（15 条销项中 CLOSED 12 / PARTIAL 2 / NOT CLOSED 1；新增 Blocking 2 条）

## R2-0. 销项统计

| 判定 | 条数 | 编号 |
|---|---|---|
| CLOSED | 12 | B-01、B-03、B-04、B-05、B-06、B-07、B-08、S-02、S-03、S-05、S-06、S-01(见下) |
| PARTIAL | 2 | B-09（M-02 PATH 前置实测不生效）、S-04（十组签名清单与 §5 非一一对应） |
| NOT CLOSED | 1 | B-02（C6 netstat 门禁实测假红，作者「空跑 rc=0」不可复现） |

> 注：B-09 与 B-02 的缺陷形态在 v2 中**改变了**——v1 是「无载体 / 未核实」，v2 是「有载体但载体本身不成立」。因此按「销项证据是否成立」判 PARTIAL / NOT CLOSED，而非按「是否补了文字」判 CLOSED。

## R2-1. 逐条销项判定

### CLOSED

**B-01（FR-13 空目录可检测）— CLOSED**
计划 Task 9 Step 6 + Output 第②段（行 790 / 796）。我实跑该命令形态：
```
$ d=$(mktemp -d) && ( cd "$d" && echo "OLDPWD=$OLDPWD" && "$OLDPWD/_build/native/debug/build/src/core/cmd/main/main.exe" >/tmp/o2.txt 2>/tmp/e2.txt; echo run_rc=$? )
inside OLDPWD=F:\moonbit比赛\moon_langdetect
run_rc=0
chain_rc=0
$ wc -c /tmp/o2.txt /tmp/e2.txt
0 /tmp/o2.txt
0 /tmp/e2.txt
```
`$OLDPWD` 在子 shell 中解析到仓库根，绝对路径可执行，stdout/stderr 均 0 字节。C5 判据成立且可证伪（删二进制 → rc=127 → 断言红）。

**B-03（cmd29 基线 rc）— CLOSED**
计划行 48 已改为「**命令 29 期望 rc=0**」并注明「v1 评审 B-03 实测值」，B-01 基线缺陷改写为「不是缺陷，Task 9 须保持 rc=0」。我的实测：
```
$ test -x ./_build/native/debug/build/src/core/cmd/main/main.exe || exit 2
$ ./_build/native/debug/build/src/core/cmd/main/main.exe >/tmp/o.txt 2>/tmp/e.txt || exit 1
$ test ! -s /tmp/o.txt && test ! -s /tmp/e.txt
rc29=0
```
计划值 = 实测值 = 行 319 注释「② 空 fn main → 0」= 行 852 的 Task 12 期望，四处一致。

**B-04（cmd/ 白名单盲区）— CLOSED（计划侧）**
新增命令 11b（行 331–341），过滤式收窄为 `grep -vE '[\\/]cmd[\\/]main[\\/]'`。我三组实测：
```
$ # 现场（仓库真实 src/）
$ grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam | grep -vE '[\\/]cmd[\\/]main[\\/]'
rc_11b=1                                    ← 0 行，符合期望
$ # T2-A：cmd/golden/main.mbt 含 println("x")
/tmp/n11/src/core\cmd\golden\main.mbt:1:fn main { println("x") }
rc_T2A=0                                    ← 正确拦截（旧过滤此处 rc=1，漏检）
$ # T2-B：仅 cmd/main/main.mbt 含 println("y")
rc_T2B=1                                    ← 正确豁免
$ # 对照：旧过滤 '[\\/]cmd[\\/]' 对 T2-A 样本
rc_old=1                                    ← 复现 v1 的盲区
```
11b 被 Task 6 Step 6（行 677）、Task 9 Step 3（行 787）、S1 静态门（行 176）引用，挂载完整。
**遗留**：D-03 仍要求执行前回 brainstorming 修订 spec（§4A GP1 + §9.4 例外范围），该 gate 未机械阻断（见 N-06）。

**B-05 / D-04（12/11/126/6667 四元组）— CLOSED（数值正确）**
我独立复算，四个数**全部对得上**：
```
$ .venv/Scripts/python.exe - <<'PY'  (正则抽取 block==/block in 的常量 + 导入上游模块取长度)
arms = 11
consts_in_arms = 12 ['UNICODE_ARABIC','UNICODE_BASIC_LATIN','UNICODE_BOPOMOFO','UNICODE_BOPOMOFO_EXTENDED','UNICODE_CJK_UNIFIED_IDEOGRAPHS','UNICODE_GENERAL_PUNCTUATION','UNICODE_HANGUL_SYLLABLES','UNICODE_HIRAGANA','UNICODE_KATAKANA','UNICODE_LATIN_1_SUPPLEMENT','UNICODE_LATIN_EXTENDED_ADDITIONAL','UNICODE_LATIN_EXTENDED_B']
CJK_CLASS len = 126
CJK_MAP len = 6667
normalize_vi exists = True
```
「12 块 / 11 臂」是两个不同的量（12 个块常量落在 11 个判定臂上，Bopomofo 与 Bopomofo Extended 同臂），与 spec G-22 的「12 个块常量 / 11 个判定臂」措辞一致，未被混写。

**B-06（Task 0 计数）— CLOSED**
计划行 478 改为 `test "$(grep -cE '^\| [0-9]+ \|' …)" -eq 30`，行 465 固定行模板为 `| N | <路径或编号> | rc | … |`（N 置于首列）。我四态实测：
```
$ # 30 数据行 + 表头
test "$(grep -cE '^\| [0-9]+ \|' /tmp/b30.md)" -eq 30;  → 30rows_rc=0
$ # 29 数据行
→ 29rows_rc=1
$ # 仅表头
→ headeronly_rc=1
$ # 文件缺失
→ missingfile_rc=1
```
四态全部符合「正样本绿 / 三态必红」。

**B-07（Task 3 四判据）— CLOSED**
行 565 已把 `grep -vc` 单条改为四段串联：`@math\.ln(` 命中 ≥1 → 未带标记行 = 0 → `extern "C" fn … = "log"` ≥1 → 位型常量出现在测试文件。
```
$ printf '' | grep -vc 'zzz'   → 0（空集）
$ test "$(printf '' | grep -vc 'zzz')" -ge 1 → rc=1   ← 空集被拦截（v1 的假绿已消除）
$ test "$(printf 'a\n' | grep -vc 'zzz')" -ge 1 → rc=0
```
位型独立验算（`ln(2.0)` 的 IEEE754 大端）：
```
$ .venv/Scripts/python.exe -c "import math,struct;print(struct.pack('>d', math.log(2.0)).hex().upper())"
3FE62E42FEFA39EF
```
与计划 `0x3FE62E42FEFA39EF` 逐字相同（`math.log(2.0)=0.6931471805599453`）。**注**：第④条是「常量出现在测试文件」的文本匹配，常量写在注释里也能过，见 N-05。

**B-08（exit 3 分期）— CLOSED**
Task 2 Interfaces 新增「交付分期（B-08 裁决）」（行 521）：十二个模式于 Task 10 交付，Task 10 之前 `exit 3` 为预期；Task 10 Step 0（行 824）要求逐条替换并以 `grep -n 'exit 3' tools/compare_golden.py` 为 0 命中收尾。
```
$ ls tools/compare_golden.py
No such file or directory        ← Step 0 于 Task 10 执行时脚本已由 Task 2 交付，时序成立
$ grep -n 'exit 3' tools/compare_golden.py
grep: 系统找不到指定的文件。 (os error 2)   rc=2
```
（脚本尚未存在时该 grep rc=2 而非 0，但因 Task 10 在 Task 2 之后，执行时文件必存在；属可接受时序。）

**S-01（D-02 裁决）— CLOSED（裁决性质已改正）**
行 1007 已从 `ALIGN-SPEC` 改为「**修订 spec**（v1 的 ALIGN-SPEC 是错的）」，并给出具体改点：「在 §0A D2 行 46 补『+ `unicode_block` 区块表（220 区间）』；未修订前不得把 §2A 当作 D2 的职责依据」。改点具体、有禁令句。**遗留**：无机械 gate，见 N-06。

**S-02（产品字节数）— CLOSED**
Task 5 Files（行 620）改为「字节数 = 产品侧首次生成后实测登记值，**不是**探针样本的 2205308」；Steps 第 4 步（行 636）要求按约定 A §5 重新登记；Output（行 643）已删除 `wc -c … = 2205308` 断言，改为 `grep -c 'Map::from_array' = 0` + `勿手改` + `grep -c 'profiles' ≥ 1`；行 644 明确「C-A3 以产品侧登记值为基线，禁止沿用 2205308」。

**S-03（空集假绿范围）— CLOSED**
行 52 已改为「**命令 1-14 全部**依赖非空扫描面……命令 5-8 / 12-14 同理依赖扫描面存在」，并加「空集态与实跑态必须分列记录」。

**S-05（U 编号集合）— CLOSED**
我的集合运算：
```
carry-over  : U-01 … U-12（12 个，carry==all → True）
死链标注行  : 10 条（U-01,02,03,04,05,08,09,10,11,12）
carry − dead: ['U-06', 'U-07']            ← 与作者声明「差集恰为 {06,07}」一致
U-06/U-07 in dead? False False
```
行 356 显式写明「本机可执行、非死链（S-05 移出）……不计入死链清单」，语义已收敛。

**S-06（Task 6 dry-run 可证伪）— CLOSED**
行 675 给出 `--verify` 四元组口径与四个数的**定义**（块=12 个 `UNICODE_*`、臂=`block ==`/`block in` 11 处、组=`CJK_CLASS` 126、键=`CJK_MAP` 6667）；行 682 把 `--verify` 写进 Output；行 683 给 T2（改任一数 → rc=1）。四个数我已独立复算，全部正确（见 B-05）。

### PARTIAL

**B-09（M-01 / M-02 手册可执行性）— PARTIAL**
- M-01（行 368）已改为**实测确认**的表述：`moon --help` 无 runner 覆盖项、`moon --version` 尾部 `exit 255`，回补路径 = 异地换机器。我复核一致：
```
$ C:/Users/Administrator/.moon/bin/moon.exe --help | grep -inE 'runner|wasm'
11:  runwasm                Deprecated: use moon run --target wasm locally or moonx for registry packages
$ C:/Users/Administrator/.moon/bin/moon.exe --version   （尾部）
Error: failed to get "C:\Users\Administrator\.moon\bin\moonrun.exe" version:   exit 255
```
「不猜」类措辞已消失。**但**「异地执行」未登记为 `交付范围收缩`（`grep -n '交付范围收缩' plan` → 仅 CO6 通用条款 1 处，无本项登记），见 N-03。
- M-02（行 375）仍**不可照抄执行**：
```
$ export PATH="$(pwd)/probes/bin:$PATH"
$ command -v node
C:\Users\Administrator\.bunpm\bin\node.cmd        ← 不是 probes/bin 的 shim
$ node --version
The system cannot find the path specified.        ← rc=1（指向 D:\nvm4w\nodejs\bun，不存在）
$ ./probes/bin/node.cmd --version
1.4.3                                             ← rc=0（直接调用才生效）
```
即：bash 下把 `probes/bin` 前置到 PATH **不能**让 `node` 解析到仓库内 shim（bash 对 `.cmd` 的查找顺序 + 系统 PATH 中同名 `node.cmd` 抢先）。手册第 1 步按字面执行会得到 rc=1 的 `node --version`，与手册声称的「bun 1.4.3 替代运行时」不符。

**S-04（Task 8 十组签名）— PARTIAL**
T2 侧成立（我构造缺签名样本，逐项 `grep -rq` 正确报 `MISSING:`）：
```
$ for s in 'pub fn detect(' … 'pub fn is_upper_cp312('; do grep -rq --include=*.mbt -- "$s" src || echo "MISSING: $s"; done
MISSING: pub fn debug_vector_len(
MISSING: set_prior_map
MISSING: set_max_text_length
MISSING: pub fn ln_for_gauss(
MISSING: pub fn is_upper_cp312(
```
但清单与 spec §5 **非一一对应**：spec §5.1–§5.10 的签名行共 10 条（`detect` / `detect_langs` / `detect_with_confidence` / `get_lang_list` / `Detector::new()` / `Detector::set_prior_map` / `Detector::set_max_text_length` / `suberror LangDetectError` / `ln_for_gauss` / `debug_vector_len`），计划的十项中**缺 `Detector::new()`**，另加入 `set_seed` 与 `is_upper_cp312`（二者确在 §5.5 / §5.9 正文，但不在签名行）。另有 3 项写作裸 `set_seed` / `set_prior_map` / `set_max_text_length`（无 `pub fn` 前缀），注释中出现同名词即通过。

### NOT CLOSED

**B-02（FR-24 零网络）— NOT CLOSED**
计划已补 C6（行 184 / Task 10 Step 8 / Output 行 838），载体形态正确（`^>` 只判新增，`^<` 不判红），但**门禁在真实环境上假红**。我三次连续快照实测（间隔 3s / 5s / 10s，期间未运行被测程序）：
```
$ netstat -an | sort > b1; sleep 3; netstat -an | sort > b2
added(^>) = 5      removed(^<) = 4
$ sleep 10 后再取一对
added = 9          removed = 15
$ sleep 5 后再取一对
added = 7
$ test "$(diff b1 b2 | grep -c '^>')" -eq 0
C6_rc=1            ← 计划断言 rc=0，实测 rc=1
```
新增行样例（全部是自然波动，非被测程序所致）：
```
>   TCP    127.0.0.1:17950    127.0.0.1:4096    TIME_WAIT
>   TCP    192.168.1.17:17948 23.45.137.206:443 TIME_WAIT
>   TCP    192.168.1.17:17951 104.18.6.151:443  TIME_WAIT
```
连接状态分布实测：`ESTABLISHED 364 / TIME_WAIT 89 / LISTENING 72 / CLOSE_WAIT 39 / SYN_SENT 2`。宿主 shell / 编辑器 / 浏览器的后台连接在 3–10 秒窗口内持续产生新 `TIME_WAIT` 条目，`diff` 的 `^>` 侧因此**恒非 0**。计划行 841 声称「真实空跑 → `added_zero` 断言 rc=0」，我无法复现。
注入侧（作者 T2）我复现成立：
```
$ cp after after_i; printf '  TCP 1.2.3.4:9999 5.6.7.8:443 ESTABLISHED\n' >> after_i; sort -o after_i after_i
$ test "$(diff before after_i | grep -c '^>')" -eq 0
T2_inject_rc=1     ← 必红成立
```
即：**必红侧成立，必绿侧不成立**——门禁对「无违规」的判定没有稳定性，任何一次后台连接抖动都会判失败。

## R2-2. 新发现问题

### N-01（Blocking）C6 零网络门禁假红——判据对无关连接的自然波动零容忍
- **位置**：计划行 184（C6 链路）、行 832（Task 10 Step 8）、行 838（Output）、行 840–841（判据说明与 T2 声明）
- **证据**：见上 B-02 的三次实测（added = 5 / 9 / 7，全部 `TIME_WAIT`；`C6_rc=1`）。
- **问题**：`diff | grep -c '^>'` 把「宿主环境新建的任何 TCP 连接」都算作被测程序的网络请求。本库是纯计算库，被测进程生命周期 < 1s，而快照窗口跨数秒——窗口内宿主侧连接变化被误记为违规。这不是「偶发抖动」，而是**稳态噪声**（三次实测三次非 0）。
- **改法（择一，均需可证伪）**：
  1. **按 PID 过滤**：`netstat -ano` 取被测进程 PID 的条目集合，前后各取一次，`diff` 该子集（`netstat -ano | awk -v p=$PID '$5==p'`）；无连接 → 集合为空，判据变成「集合恒为空」，不受宿主噪声影响。
  2. **断网执行**：`unshare -n`（Linux）或 Windows 防火墙出站阻断后跑 detect，断言 rc=0 且结果与联网时一致——把「零网络」转成「无网络也能工作」的等价断言。
  3. 若坚持快照法，必须把判据改为「被测进程 PID 的新增连接数 = 0」并给出该 PID 的获取命令；仅靠 `^>` 行数不可用。
- **附带**：行 841 的「真实空跑 → rc=0」实测记录应删除或改写为「单环境观测，不可复现」，否则后续执行者会拿一条不可复现的记录当基线。

### N-02（Blocking）M-02 的 PATH 前置在本机 bash 下不生效
- **位置**：计划行 375（M-02 第 1 步）
- **证据**：`command -v node` → `C:\Users\Administrator\.bunpm\bin\node.cmd`；`node --version` → `The system cannot find the path specified.`（rc=1）；`./probes/bin/node.cmd --version` → `1.4.3`（rc=0）。`probes/bin` 下只有 `node.cmd`（59 B，内容 `@echo off` + `"C:\Users\Administrator\.bun\bin\bun.EXE" %*`），系统 PATH 中另有 `C:\Users\Administrator\.bunpm\bin\node.cmd`（指向不存在的 `D:\nvm4w\nodejs\bun`）。
- **问题**：手册声称「用相对路径把 shim 目录前置」即可让 `node` 解析到 bun 1.4.3，实测不成立。回补触发时执行者按字面执行会得到 rc=1，且会误判为「bun 也不可用」。
- **改法**：把第 1 步改为**显式路径调用**（不依赖 PATH 解析顺序）：`./probes/bin/node.cmd --version` → 断言输出 `1.4.3`；或在 `moon test --target js` 前用 `export PATH="$(cd probes/bin && pwd):$PATH"` 并把系统 `bunpm/bin` 从 PATH 中移除后 `command -v node` 校验一次。无论哪种，都要加一条**前置断言**：`command -v node` 的解析结果必须位于仓库 `probes/bin` 之下，否则 `exit 2`（避免静默用错运行时）。

### N-03（Should-fix）M-01 的「异地执行」未登记为交付范围收缩
- **位置**：行 368（M-01）、行 356（死链清单）
- **证据**：`grep -n '交付范围收缩' plan` → 仅 CO6 通用条款 1 处，无本项登记。
- **问题**：A12 / 平台敏感出口门要求「确无替身时最小载体获取按可排期能力项登记」或「交付范围显式收缩」。M-01 已实测本机不可回补，但计划仍把 wasm-gc 列为三目标之一（Task 11 Step 4），未在交付口径上显式收缩。
- **改法**：在 Task 11 或 final-report 模板中写明「wasm-gc 本批交付口径 = 仅构建通过；运行时验证不在本批验收范围（U-01/M-01）」，并在 §8 状态列同步。

### N-04（Should-fix）Task 8 签名清单缺 `Detector::new()`
- **位置**：行 761
- **证据**：spec §5.5 签名行 `Detector::new() -> Detector`；计划十项中无该项。
- **改法**：把 `'pub fn Detector::new('` 加入清单（或 `'Detector::new'`），并把 `set_seed` / `set_prior_map` / `set_max_text_length` 三项改为带 `pub fn ` 前缀或带 `self` 的形态，避免注释误命中。

### N-05（Should-fix）Task 3 第④判据是文本匹配，非数值断言
- **位置**：行 565 / 行 567
- **问题**：`grep -q '3FE62E42FEFA39EF' src/math_seam/math_seam_test.mbt` 只证明常量出现在文件里，写在注释中亦通过；它不证明「`ln_for_gauss(2.0)` 的实际返回值等于该位型」。
- **改法**：改为「测试名 + 断言形态」双条件，如 `grep -q 'test "ln_for_gauss_2_0_bits"' … && grep -q '3FE62E42FEFA39EF' …`，或在 Output 中直接跑该单测并以 rc 为准（`moon test --target native --filter ln_for_gauss`）。

### N-06（Should-fix）D-02 / D-03 / D-04 的 spec 修订无机械 gate
- **位置**：行 1007–1009
- **证据**：`grep -n '未修订前\|执行前必须' plan` → 仅三行表格内文字，无 Task 级前置检查、无 `exit` 判据。
- **问题**：三条修订都写了「执行前必须回 brainstorming 修订 spec」，但计划的任务序列（Task 0→13）没有任何一步校验「spec 是否已修订」。执行者可直接开 Task 4 / 6 / 10 而不触发。
- **改法**：在 Task 0 增一步「spec 修订核对」：`grep -q 'unicode_block 区块表' spec && grep -q 'cmd/golden' spec && grep -q 'gen_core_tables' spec || exit 1`（三条命中 = 修订已落地），并把结果写入基线 md；未通过则阻塞 Task 1+。

### N-07（Note）Task 10 Step 0 的 `grep 'exit 3'` 是散文，未进 Output
- **位置**：行 824
- **问题**：该断言写在 Steps 内，不在 Output 的 `&&` 链上，无法机械证伪。
- **改法**：并入 Output 首段：`test "$(grep -c 'exit 3' tools/compare_golden.py)" -eq 0 && …`。

## R2-3. 其他复核（作者声明逐条验证）

| 声明 | 我的复核 | 结论 |
|---|---|---|
| 30 条命令仍与 spec §10.6 逐字一致 | `awk` 抽取 spec 命令块 + `sed` 抽取计划 191–329 → 各 **130 行**；`diff` → **rc=0（0 行差异）** | ✅ 成立 |
| 11b 已移出 30 条代码块 | 计划行 329 闭合 fence，行 331 起独立小节 + 独立 ```bash 块（行 333–341）；30 条块内无 11b | ✅ 成立 |
| 11b 仍可执行且被引用 | 现场 rc=1；T2-A rc=0 / T2-B rc=1；引用点：行 176（S1）、行 677（Task 6）、行 787（Task 9） | ✅ 成立 |
| Task 10 Step 0 在脚本不存在时 | `grep -n 'exit 3' tools/compare_golden.py` → rc=2（文件不存在）；因 Task 2 先交付，执行时存在 | ✅ 时序成立（见 N-07） |
| M-01 改为异地执行 | 本机 `moon --help` 无 runner 覆盖项（实测）、`moonrun` exit 255（实测）；但未登记范围收缩 | ⚠️ 见 N-03 |
| M-02 改相对 PATH | 实测 `command -v node` 解析到 bunpm，`node --version` rc=1 | ❌ 见 N-02 |
| 全文无 `不猜` / `/opt/node` / TODO 等 | `grep -nE '不猜|/opt/node|TODO|FIXME|待定|视情况|TBD' plan` → **rc=1（0 命中）** | ✅ 成立 |
| 12/11/126/6667 | 独立复算：arms=11、consts=12、CJK_CLASS=126、CJK_MAP=6667 | ✅ 成立 |
| ln(2.0) 位型 | `struct.pack('>d', math.log(2.0)).hex()` = `3fe62e42fefa39ef` | ✅ 成立 |
| U 集合关系 | carry=12、dead=10、差集 {U-06, U-07} | ✅ 成立 |

## R2-4. Blocking Checks 全量重判（15 条）

| # | 检查项 | 判定 | 依据 |
|---|---|---|---|
| 1 | Spec Coverage | **PASS** | FR-13 已补 C5（Task 9 Step 6 / Output ②，实测 rc=0）；FR-24 已补 C6（Task 10 Step 8 / Output）——覆盖存在，C6 的执行缺陷另计于 #4/#9 |
| 2 | Executability | **FAIL** | M-02 第 1 步按字面执行 `node --version` → rc=1（N-02） |
| 3 | Consistency | **PASS** | Task 2「交付分期」+ Task 10 Step 0 已消除 `exit 3` 互斥；cmd29 期望值四处一致 |
| 4 | Testability | **FAIL** | C6 门禁在无违规时实测 rc=1（added 5/9/7），不可证伪「零网络」 |
| 5 | Granularity | **PASS** | 14 Task 字段齐备（时长上限 14 / 轮次上限 14 / 允许修改清单 15） |
| 6 | Authority-Source Alignment | **PASS** | Authority 表 `file:line:方法` 全部落地；RNG/Neumaier 无上游行号时改用仓库实测证据，未伪造 |
| 7 | Spec-Plan Consistency | **PASS** | cmd29 rc=0 已与实测一致；B-01 改为「非缺陷」 |
| 8 | Field-Mapping Table | **PASS** | Dependency Contract 17 行类型/NULL 性逐字复制 spec §4.1/§4.3 |
| 9 | Acceptance Command Verification | **FAIL** | 30 条逐字一致 ✅，但 C6 这条验收命令不可稳定执行（N-01）；M-02 回补命令不可执行（N-02） |
| 10 | Spec-Decision Traceability | **PASS** | D-02/D-03/D-04 均改为「修订 spec」并给出具体改点（行 1007–1009） |
| 11 | Compile-Probe Task 0 | **PASS** | Task 0 计数四态实测（30→0 / 29→1 / 表头→1 / 缺失→1），门禁可证伪 |
| 12 | External-Dependency Verification | **FAIL** | M-02 声称的运行时载体实测不可达（N-02）；M-01 未登记范围收缩（N-03） |
| 13 | Golden-Vector Local Baseline | **PASS** | md5 `219519ee…`、golden 目录 9 项齐备；Task 4 全码点、Task 7 512/307/385 组均在集成前 |
| 14 | Incremental Review Checkpoints | **PASS** | 每片 V1 + V3，未集中到末尾 |
| 15 | `[LOCAL_DEAD_LINK]` Marking | **PASS** | 10 条死链 + U-06/U-07 显式移出（集合关系实测一致）；M-01…M-12 五要素齐备 |

**统计：PASS 11 / FAIL 4 / N-A 0。**

## R2-5. 最终判定

**Status: Issues Found**

放行前置（按序，均为小改动）：
1. **N-01**：C6 改为按 PID 过滤或断网执行；删除不可复现的「空跑 rc=0」记录。
2. **N-02**：M-02 第 1 步改为显式 `./probes/bin/node.cmd` 调用 + 解析位置前置断言。
3. **N-03**：M-01 登记为「wasm-gc 交付口径 = 仅构建」。
4. **N-04 / N-05 / N-06 / N-07**：签名清单补 `Detector::new()`、位型断言改测试名+数值双条件、Task 0 增 spec 修订核对、Step 0 断言并入 Output。

修完上述 4 项（N-01…N-04 为必须，N-05…N-07 建议同批）即可判 Approved；无需再改 15 条销项中已 CLOSED 的部分。

---

**第二轮复审结束**

---

## 9. 第三轮登记（v2 复审，2026-10-21）

> 复审结论：**CLOSED 12 / PARTIAL 2 / NOT CLOSED 1**，Blocking Checks PASS 11 / FAIL 4，仍判 Issues Found，真 Blocking 2 条（N-01、N-03）。

| 编号 | 定义原文（摘要） | 销项证据（复跑命令 + 输出 + rc） | 状态 |
|---|---|---|---|
| N-01 | C6 零网络门禁必须在真实环境可判定（禁止系统噪声判红） | 已销项：Task 10 Output + S3 走查门 C6 改为 **PID 级采样**（`netstat -ano` + `$NF` 取 PID + `ps -W` 映射 WINPID + `SAMPLES ≥ 1` 守卫 + `HITS = 0` 判据）。三态实跑：① 无网络进程 → `HITS=0 SAMPLES=4 child_rc=0` rc=0；② 持 TCP 连接的进程（注入 socket）→ `HITS=51 SAMPLES=18` rc=1；③ 二进制缺失 → rc=2。另：全量快照 diff 实测在**未运行被测程序**时 3s/5s/10s 分别新增 5/9/7 行（TIME_WAIT 噪声）→ 该形态降级为辅助观察，不判绿 | 已销项 |
| N-02 | M-02 回补手册必须照抄即可执行 | 已销项：M-02 改为**显式相对路径** `./probes/bin/node.cmd --version`（实跑输出 `1.4.3`、rc=0），并加前置断言（`command -v node` 不含 `probes/bin` → `exit 2`）。实测 PATH 前置无效：`export PATH="$(pwd)/probes/bin:$PATH"` 后 `command -v node` → `C:\Users\Administrator\.bunpm\bin\node.cmd`，`node --version` 失败。新增 1b 条：若 moon js runner 只能经 PATH 发现 node 则登记为本机不可回补、处置异地执行 | 已销项 |
| N-03 | 交付范围收缩必须显式登记 | 已销项：M-01 第 1 条、Task 11 Step 4 与 Output、Task 13 Step 6 四处均写入逐字声明「wasm-gc 本批口径 = 仅 `moon build --target wasm-gc` rc=0；`moon test` 不入本批验收范围（依据 U-01 + M-01）」；Task 13 final-report 状态数由 12 改为 10 个死链 + U-06/U-07 单列 | 已销项 |
| N-04 | Task 8 签名清单须完整且不可被注释骗过 | 已销项：清单补 `^pub fn (Detector::)?new\(\) -> Detector`；三项实例方法改 `^pub fn (Detector::)?set_seed\(self` 等行首锚定形态；共 11 组签名 + 4 类型。实跑：正样本 11/11 OK rc=0；注释-only 样本 → clean（0 命中，不假通过）；删 `debug_vector_len` → `MISSING` rc=1 | 已销项 |
| N-05 | 位型断言不得只做文本匹配 | 已销项：Task 3 Output 第 ④ 判据由 `grep -q '3FE62E42FEFA39EF'` 改为 **`moon test --target native --filter ln_for_gauss`（rc=0，真实执行）+ `grep -cE 'ln_for_gauss_bits' ≥ 1`（函数名存在）** 双条件 | 已销项 |
| N-06 | 「修订 spec」裁决须有机械 gate | 已销项：Task 0 新增 Step 0 前置门，三条 grep（`unicode_block` in §0A D2 / `cmd/golden` in §4A / `gen_core_tables` in §4A）任一为 0 → `exit 1` 阻塞 Task 1+。**当前 spec 实测 `unicode_block=0 cmd/golden=0 gen_core_tables=0` → gate_rc=1（正确阻塞）**，证明执行前必须先完成 spec 修订 | 已销项 |
| N-07 | exit 3 断言须并入验收链 | 已销项：Task 10 Output 首段加入 `test "$(grep -c 'exit 3' tools/compare_golden.py)" -eq 0 &&` | 已销项 |

**B-02 / B-09 / S-04 状态更新**：B-02 `LOCAL_DEAD_LINK` 清单条目含义已从「全量 diff」改为「PID 级采样」（Task 10 Output）；B-09 的 M-01/M-02 已按 N-02/N-03 重写为可照抄执行；S-04 的签名清单已按 N-04 扩充并锚定。三行均标 **已销项（v3）**。

**v3 结论**：计划升 v3；剩余 2 条 PARTIAL/NOT CLOSED 全部销项，未新增 Blocking。

---

# 第四轮核验（v3）

> **审查对象**：`docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md` v3（1102 行 / 108,285 B）
> **审查方法**：7 条销项逐条实跑；C6 脚本按计划行 847 的六条契约独立实现并四态实测；不采信作者自述。
> **结论**：**Issues Found**（7 条中 CLOSED 4 / PARTIAL 2 / NOT CLOSED 1；新增 Blocking 2 条）

## R4-0. 销项统计

| 判定 | 条数 | 编号 |
|---|---|---|
| CLOSED | 4 | N-02（M-02 显式路径部分）、N-03、N-06、N-07 |
| PARTIAL | 2 | N-01（C6 主体正确但契约与调用形态不符）、N-04（清单已补但计数措辞与项数不符） |
| NOT CLOSED | 1 | N-05（`moon test -f <文件名>` 恒 0 用例 → rc=0，仍是假绿） |

## R4-1. N-01（C6 零网络）— PARTIAL

### ① 契约六条逐条可实现性

我按计划行 847 的 ①②③④⑤⑥ 独立实现为 `/tmp/c6v4.sh`（与计划同形态），四态实测：

```
$ sh /tmp/c6v4.sh "D:/Programs/Python/Python312/python.exe" -c "import time;time.sleep(2)"
child_pid=25573 WINPID=[11224]
SAMPLES=9 HITS=0 child_rc=0
state1_rc=0                      ← 正常无网络：rc=0 ✅

$ sh /tmp/c6v4.sh "D:/Programs/Python/Python312/python.exe" /tmp/sockhold.py
child_pid=25672 WINPID=[24264]
SAMPLES=9 HITS=9 child_rc=0
state2_rc=1                      ← 持有 socket：rc=1 ✅（必红成立）

$ sh /tmp/c6v4.sh /nope/x
state3_rc=2                      ← 二进制缺失：rc=2 ✅

$ sh /tmp/c6v4.sh ./_build/native/debug/build/src/core/cmd/main/main.exe
child_pid=25775 WINPID=[]
SAMPLES=0 HITS=0 child_rc=0
state4_rc=3                      ← 瞬时退出：rc=3
```

结论：**判据主体成立**——`$NF==p` 确实能按 PID 抓到被测进程的连接（state2 HITS=9），且不受宿主 TIME_WAIT 噪声干扰（state1 HITS=0，对比 v2 的全量 diff 形态三次实测 added=5/9/7）。PID 映射也确实必要且有效：

```
$ sh /tmp/pidmap.sh        # 起 ping.exe（native exe）后对比
bash_pid=14324  WINPID=[27592]  equal=NO
ps -W row:     14324   14322   14322      27592  ?  197108 14:41:33 /c/Windows/system32/ping
```

即：**作者「直接启动的 native exe 两者相同」的断言在本机为假**（`$!`=14324 ≠ WINPID=27592）。但 `ps -W` 映射是**必要的且被计划写入了**，所以这一条不构成缺陷——只是作者对「为何需要映射」的解释错了，机制本身正确。

### ② `ps -W` 的实现依赖是真风险（PARTIAL 的原因之一）

本机存在两套 `ps`：

```
$ ps -W                       # 默认 shell（pi-uu ps 0.2.0）
ps: unsupported option '-W'   rc=1
$ /usr/bin/ps -W              # Git Bash（procps）
      PID    PPID    PGID     WINPID   TTY         UID    STIME COMMAND
  4194308       0       0          4  ?              0   Oct 14 System     rc=0
```

脚本用 `#!/bin/sh` 启动时，`ps` 解析到 Git Bash 的 `/usr/bin/ps`（`sh /tmp/map2.sh` → `WINPID=[33308]`），所以**在 `sh` 下契约③成立**。但若执行者改用 `bash` 直跑或 `ps` 解析到 pi-uu 版本，`W` 为空串，`awk -v q="" '$NF==q'` 会匹配 `netstat` 输出中的空行（实测 2 行），于是 `HITS = 2×SAMPLES > 0` → **rc=1 假红**，整条 `&&` 链断裂。

**改法**：契约③ 后加守卫 `test -n "$W" || { echo "ps -W unavailable"; exit 2; }`，把「映射失败」与「检测到网络」区分开。

### ③ `SAMPLES ≥ 1` 守卫与瞬时退出的真问题

计划行 848 声称「瞬时退出的空 `fn main` 二进制采样 1 次（`SAMPLES=1`）→ `HITS=0`、rc=0」。我实测**不是 1 次而是 0 次**：

```
$ sh /tmp/c6v4.sh ./_build/native/debug/build/src/core/cmd/main/main.exe
child_pid=25775 WINPID=[]
SAMPLES=0 HITS=0 child_rc=0
state4_rc=3
```

原因：`kill -0` 在进程已退出时第一次即失败，`while` 体一次都不执行。因此对「瞬间退出的二进制」这条守卫**触发 exit 3**，而不是作者声称的 rc=0。

**这对 Task 10 是实质风险**：`tools/c6_zero_network.sh ./…/cmd/golden/main.exe docs/port/golden/cases.jsonl` 若该 CLI 处理 268 案例耗时足够（>100ms）则能采到样本；但**若某次优化后跑得极快（<10ms），C6 会 exit 3 而整条 `&&` 链断开**，表现为「golden 比对失败」的假象。

**改法（择一）**：
- 把 `exit 3` 改为 `exit 0` 并打 `SKIP: process too fast to sample`（语义：无法采样 ≠ 检测到网络）；但这样又退回假绿。
- **更好**：让脚本**主动延长被测进程存活**——契约② 改为「后台启动后立即 `kill -0` 轮询 + 若 100ms 内退出则判 `SAMPLES=0` 并**重跑一次带 `--hold` 参数**」；或直接由脚本在启动后立刻采一次 `netstat`（不等 0.1s），把首采移到 `kill -0` 之前：
  ```
  n=$(netstat -ano | awk -v q="$W" '$NF==q' | wc -l); HITS=$((HITS+n)); SAMPLES=1
  while kill -0 "$p" 2>/dev/null; do sleep 0.1; n=...; HITS=...; SAMPLES=...; done
  ```
  这样即使进程瞬时退出也至少采到 1 次，守卫不再误触发。

### ④ 调用形态与契约不符（PARTIAL 的原因之二）

计划行 845 的调用是 `sh tools/c6_zero_network.sh <binary> docs/port/golden/cases.jsonl`（第二个位置参数是**文件路径**），而契约②只写「后台启动被测二进制并重定向 stdin/stdout」，**没有说明第二个参数如何传给被测程序**（argv 还是 stdin 重定向）。若脚本按字面实现（`"$1" < /dev/null`），`cases.jsonl` 会被忽略，CLI 读不到输入 → 可能立即退出 → 又触发 `SAMPLES=0` → exit 3。

**改法**：契约② 补一句「`shift` 后的参数原样作为 argv 传给被测二进制；stdin 重定向为 `/dev/null`」。

## R4-2. N-02（M-02 路径）— PARTIAL

**已修部分（CLOSED）**：M-02 第 1 条（行 375）已改为「不得依赖 PATH 前置」并给出显式调用 `./probes/bin/node.cmd --version` + 前置断言。我复核：
```
$ ./probes/bin/node.cmd --version
1.4.3        rc=0
$ export PATH="$(pwd)/probes/bin:$PATH"; command -v node
C:\Users\Administrator\.bunpm\bin\node.cmd      ← 前置无效，与计划描述一致
```

**未修部分（PARTIAL 的原因）**：Task 11 Step 2 / Step 3（行 872 / 873）仍写：
```
PATH=probes/bin:$PATH moon test --target js
```
这正是 M-02 已判定「无效」的形态。我实测该写法：
```
$ PATH="probes/bin:$PATH" command -v node
C:\Users\Administrator\.bunpm\bin\node.cmd      ← 未生效
$ PATH="probes/bin:$PATH" moon test --target js      （仓库根）
Warning: no test entry found.
Total tests: 0, passed: 0, failed: 0.           rc=0
```

进一步核实 moon 是否只能经 PATH 找 node：moon 实际 spawn 的是 **`node.exe`**（不是 `node.cmd`）：
```
$ cd probes/embed-probe && moon test --target js
Failed to spawn command Command { std: "node.exe" … }  program not found
$ PATH="$(cd ../../probes/bin && pwd):$PATH" moon test --target js
The system cannot find the path specified.     ← 仍失败（probes/bin 只有 node.cmd，没有 node.exe）
```
即使我临时把 bun 复制为 `probes/bin/node.exe` 再跑，仍失败（bun 与 node 的 CLI 参数不兼容）。即：**`PATH=probes/bin` 这条写法在本机不可能成功**，Task 11 Step 2/3 是未修完的同类缺陷，且它决定了 Task 11 能否产出 js 证据。

**改法**：Task 11 Step 2/3 改为引用 M-02 的结论——「js 验证在本机不可执行 → 标 `[LOCAL_DEAD_LINK]`（U-02）+ 异地执行（同 M-01 待遇）」，并把 `moon test --target js` 从 Task 11 的验收命令中移除（与 wasm-gc 同处理）。若坚持本机跑，必须先解决 `node.exe` 供给（不是 `node.cmd`）。

## R4-3. N-05（位型断言）— NOT CLOSED

计划行 572 改为：
```
moon test --target native -f math_seam_test.mbt && test "$(grep -cE 'ln_for_gauss_bits' src/math_seam/math_seam_test.mbt)" -ge 1
```
并在行 574 断言「`moon test` 的 `-f/--filter` 语义是『按包目录 / 文件过滤』」。**该断言与工具实际语义相反**：
```
$ moon test --help | grep -A2 -- '-f, --filter'
  -f, --filter <FILTER>
          Run only tests whose name matches the given glob pattern. Supports '*' and '?'

$ cd probes/embed-probe
$ moon test --target native -f 'entries af'          # 真实测试名
Total tests: 1, passed: 1, failed: 0.        rc=0    ← 命中
$ moon test --target native -f 'embed-probe_test.mbt'  # 文件名
Warning: no test entry found.
Total tests: 0, passed: 0, failed: 0.        rc=0    ← 0 用例，仍然 rc=0
$ moon test --target native -f 'nonexistent_xyz'
Total tests: 0, passed: 0, failed: 0.        rc=0    ← 0 用例，仍然 rc=0
```

即：`-f` 是**测试名 glob**，不是文件过滤；且**命中 0 个用例时 `moon test` 仍返回 rc=0**。因此 `moon test --target native -f math_seam_test.mbt` 恒为「0 用例 / rc=0」，第④判据**再次退化为恒绿**——与 v2 的 `grep -q '3FE62E42FEFA39EF'` 同型缺陷，只是换了个不可失败的载体。

**改法**：
```
moon test --target native -f 'ln_for_gauss_bits*' > /tmp/t3.txt 2>&1 \
  && test "$(grep -oE 'Total tests: [0-9]+' /tmp/t3.txt | grep -oE '[0-9]+')" -ge 1 \
  && grep -q 'failed: 0' /tmp/t3.txt
```
我验证过该形态可区分：
```
$ out=$(moon test --target native -f 'entries af'); echo "$out" | tail -1
Total tests: 1, passed: 1, failed: 0.        count_ge_1=YES
$ out2=$(moon test --target native -f 'nonexistent_xyz'); count_ge_1=NO
```

## R4-4. 其余销项（CLOSED）

**N-03（交付范围收缩）— CLOSED**。四处均写入逐字声明，我逐处核对：
```
$ grep -n '交付范围显式收缩' plan
368: M-01 … **本批交付范围显式收缩**：wasm-gc 口径 = 仅 moon build rc=0 …
874: Task 11 Step 4 … **本批交付范围显式收缩**：… moon test --target wasm-gc 不入本批验收范围 …
882: Task 11 Output … **本批验收口径（N-03，逐字写入 target-report）** …
932: Task 13 Step 6 … **必须逐字写入交付范围收缩声明** …
```
四处一致，且 Task 13 的状态计数改为「10 个死链 + U-06/U-07 单列」，与 S-05 的集合关系（dead=10、差集 {U-06,U-07}）吻合。

**N-06（spec 修订 gate）— CLOSED**。我逐字复跑 Task 0 Step 0：
```
$ a=$(awk '/^### D2 架构/,/^\*\*依赖方向\*\*/' spec.md | grep -c 'unicode_block')
$ b=$(awk '/^## 4A\./,/^## 5\./' spec.md | grep -c 'cmd/golden')
$ c=$(awk '/^## 4A\./,/^## 5\./' spec.md | grep -c 'gen_core_tables')
unicode_block=0 cmd/golden=0 gen_core_tables=0
gate_rc=1                        ← 正确阻塞
```
三个正则的锚点范围（D2 节 / §4A 节）与 spec 实际结构对得上，gate 可证伪（修订后应为 1/1/1 → rc=0）。

**N-07（exit 3 并入链）— CLOSED**。Task 10 Output 首段（行 845）：
```
test "$(grep -c 'exit 3' tools/compare_golden.py)" -eq 0 && sh tools/c6_zero_network.sh …
```
已在 `&&` 链首，`grep -c` 为 0 时 `test -eq 0` 为真；非 0 时断链。

**N-04（签名清单）— PARTIAL**。清单已补 `^pub fn (Detector::)?new\(\) -> Detector`，三项实例方法改为 `^pub fn (Detector::)?set_seed\(self` 形态。我构造正样本与注释样本实测：
```
$ for p in '^pub fn detect\(' … '^pub fn is_upper_cp312\('; do grep -rEq -- "$p" src || echo "MISSING: $p"; done
positive_rc=0                    ← 11 项全命中，无 MISSING
$ # 注释-only 样本
MISSING(comment-only): ^pub fn (Detector::)?new\(\) -> Detector
MISSING(comment-only): ^pub fn (Detector::)?set_seed\(self
                                 ← 注释不假通过 ✅
```
**但**行 766 标题仍写「**十组**签名」，行 770 正文写「**十一组**签名」，同一节内自相矛盾（清单实际 11 项）。属措辞缺陷，不影响判据。

## R4-5. v3 新引入问题

### N-08（Blocking）`tools/c6_zero_network.sh` 未进 §4A GP1，且 Task 0 gate 不检查它

- **证据**：
```
$ grep -c 'c6_zero_network' docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
0                                ← spec 零登记
$ awk '/^## 4A\./,/^## 5\./' spec.md | grep -c 'c6_zero_network'
0                                ← §4A GP1 表无此行
```
- **问题**：这是与 D-04（`gen_core_tables.py`）完全同型的新缺口——新增脚本被 Task 10 的验收命令引用，但 spec §4A 的 GP1 四要素表里没有它。而 N-06 的 gate 只检查 `unicode_block` / `cmd/golden` / `gen_core_tables` 三项，**不含 `c6_zero_network`**，所以这条缺口不会被 gate 拦住。
- **改法**：① 在 D-04 同段新增 D-05：「§4A GP1 补 `tools/c6_zero_network.sh` 一行（生成命令 `—`、校验命令 `test -x` + 四态自检、生成时点「实现期」、责任单元「产品」）」；② Task 0 Step 0 的 gate 加第四个计数 `d=$(awk '/^## 4A\./,/^## 5\./' spec.md | grep -c 'c6_zero_network')` 并要求 `≥1`。

### N-09（Should-fix）Task 11 Step 2/3 的 `PATH=probes/bin` 残留

见 R4-2。与 N-02 同型，但未被 N-02 的修复覆盖到（M-02 改了、Task 11 没改）。这会使 Task 11 的 js 验收在 `&&` 链上必然失败或空转。

### N-10（Note）计划行数 1092 → 1102 的增量核对

新增 10 行均为实质内容：C6 脚本契约 6 条 + 三态实测 + 降级口径（行 847–851）、Task 0 Step 0 gate（行 471–473）、Task 11 范围收缩声明（行 882）。无空行填充。

## R4-6. Blocking Checks 全量重判（15 条）

| # | 检查项 | 判定 | 依据 |
|---|---|---|---|
| 1 | Spec Coverage | **PASS** | FR-13（C5）与 FR-24（C6）均有载体；C6 判据主体实测成立（state1 rc=0 / state2 rc=1） |
| 2 | Executability | **FAIL** | Task 11 Step 2/3 的 `PATH=probes/bin` 实测不可能成功（moon spawn `node.exe`，该目录只有 `node.cmd`）——N-09 |
| 3 | Consistency | **PARTIAL→FAIL** | N-04 同节「十组 / 十一组」自相矛盾；C6 契约②（stdin 重定向）与调用形态（argv 传文件）不一致 |
| 4 | Testability | **FAIL** | N-05：`moon test -f <文件名>` 恒 0 用例且 rc=0，第④判据不可失败 |
| 5 | Granularity | **PASS** | 14 Task 字段齐备 |
| 6 | Authority-Source Alignment | **PASS** | Authority 表 `file:line:方法` 落地；RNG/Neumaier 用仓库实测证据未伪造行号 |
| 7 | Spec-Plan Consistency | **PASS** | cmd29 rc=0 一致；D-02/D-03/D-04 均标「修订 spec」 |
| 8 | Field-Mapping Table | **PASS** | Dependency Contract 17 行类型/NULL 性逐字复制 |
| 9 | Acceptance Command Verification | **FAIL** | C6 脚本未登记 §4A GP1（N-08）；`ps -W` 失败时无守卫会假红；瞬时退出 exit 3 会断链 |
| 10 | Spec-Decision Traceability | **PARTIAL→FAIL** | D-05 缺位（`c6_zero_network.sh` 未登记，N-08） |
| 11 | Compile-Probe Task 0 | **PASS** | 计数四态实测（30→0 / 29→1 / 表头→1 / 缺失→1）；Step 0 gate 实测 rc=1 正确阻塞 |
| 12 | External-Dependency Verification | **FAIL** | M-01/M-02 已改实测口径，但 Task 11 的 js 执行路径仍依赖已被证伪的 PATH 前置（N-09） |
| 13 | Golden-Vector Local Baseline | **PASS** | md5 `219519ee…`、golden 9 项齐备；Task 4/7 基准均在集成前 |
| 14 | Incremental Review Checkpoints | **PASS** | 每片 V1 + V3 |
| 15 | `[LOCAL_DEAD_LINK]` Marking | **PASS** | 10 条死链 + U-06/U-07 单列，集合关系实测一致；M-01…M-12 五要素齐备 |

**统计：PASS 8 / FAIL 6 / PARTIAL 0（按最严判 FAIL）/ N-A 0。**

> 说明：第 3、10 项在严格口径下判 FAIL（存在内部矛盾 / 缺位），若按「不影响执行」口径可降为 Should-fix；本表取严。

## R4-7. 最终判定

**Status: Issues Found**

放行前置（按序）：
1. **N-05**：Task 3 第④判据改为「`-f 'ln_for_gauss_bits*'` + 断言 `Total tests: N`（N≥1）+ `failed: 0`」三条件（我已验证该形态可区分 1 与 0 用例）。
2. **N-08**：新增 D-05 并把 `c6_zero_network` 加入 Task 0 Step 0 gate 的第四个计数。
3. **N-09**：Task 11 Step 2/3 改为「本机不可执行 → `[LOCAL_DEAD_LINK]`（U-02）+ 异地执行」，与 wasm-gc 同处理。
4. **N-01 收尾**：契约③ 加 `test -n "$W" || exit 2`；契约② 补 argv 传递；瞬时退出改为「先采一次再进循环」或显式 `SKIP` 语义。
5. **N-04 措辞**：行 766「十组」改「十一组」。

修完 1–3（必须）即可判 Approved；4–5 建议同批。

---

**第四轮核验结束**

---

## 10. 第五轮登记（v3 核验，2026-10-21）

> 结论：CLOSED 4 / PARTIAL 3 / NOT CLOSED 1，另有新发现 N-08（Blocking）/ N-09（Blocking 级）/ N-10。

| 编号 | 定义原文（摘要） | 销项证据（复跑命令 + 输出 + rc） | 状态 |
|---|---|---|---|
| N-05 | Task 3 第④判据须真实执行且用例数 ≥ 1 | 已销项：改为 `out=$(moon test --target native -f 'ln_for_gauss_bits*') && test "$(…'Total tests: N'…)" -ge 1 && …grep -q 'failed: 0' && grep -cE 'ln_for_gauss_bits' ≥ 1`。**三态实测（probes/embed-probe）**：① `-f 'entries af*'` → `Total tests: 1` rc=0；② `-f 'nonexistent_xyz*'` → `Total tests: 0` → **rc=1**；③ 模拟 `Total tests: 1, passed: 0, failed: 1` → **rc=1**。并更正计划中对 `-f` 的错误描述：实测 `--help` 为「Run only tests whose name matches the given glob pattern」= **按测试名**过滤 | 已销项 |
| N-08 | `tools/c6_zero_network.sh` 须有 GP1 登记且进 spec 修订 gate | 已销项：新增 **D-05**（裁决「修订 spec」，§4A 补该脚本一行四要素 + 校验命令四态）；Task 0 Step 0 gate 扩为**四项**（`unicode_block` / `cmd/golden` / `gen_core_tables` / `c6_zero_network`）。实跑：`unicode_block=0 cmd/golden=0 gen_core_tables=0 c6_zero_network=0` → **gate_rc=1**（阻塞态正确） | 已销项 |
| N-09 | Task 11 js 路径不得依赖已证伪的 PATH 前置 | 已销项：Task 11 Step 2/3 与验收口径整体降级——本机只做 `moon build --target js`；`moon test --target js` 与 `compare_golden --target js` 全标 `[LOCAL_DEAD_LINK]`（U-02 / M-02）异地执行；交付口径由「结构+准确率」改为「**仅构建**」。实测依据：`probes/bin` 只有 `node.cmd` 而 moon spawn `node.exe` → `Failed to spawn node.exe … program not found`；仓库根 `moon test --target js` → `Total tests: 0` rc=0（空跑也绿）。`grep -c 'PATH=probes/bin' plan` → **0** | 已销项 |
| N-01 | C6 脚本契约须修四个缺陷 | 已销项：① `ps -W` 映射加**重试 20×50ms** + `W` 为空且进程存活 → `exit 2`（防 `awk -v p=''` 命中空行假红）；② **首次采样移到 `kill -0` 循环之前**（瞬时进程 `SAMPLES ≥ 1`，不再 `exit 3` 断链）；③ stdin 契约改为 `"$1" < "$2"`（`$2` 为输入文件）；④ 删除「native exe 的 `$!` 与 WINPID 相同」的错误说法，改为「**必须**经 `ps -W` 映射，不得假设相等」。**六态重跑**：① 无 socket `HITS=0 SAMPLES=5` rc=0；② 持 socket `HITS=54 SAMPLES=19` rc=1；③ 缺失 rc=2；④ 瞬时退出 `HITS=0 SAMPLES=1` **rc=0**；⑤ stdin 契约 `got:hello` rc=0；⑥ `ps -W` 不可用 + 存活 5s 进程 → **rc=2**（守卫生效） | 已销项 |
| N-02 | M-02 与 Task 11 的 PATH 前置须一并清除 | 已销项：M-02 保持显式 `./probes/bin/node.cmd`（实跑 `1.4.3` / rc=0）+ 前置断言；新增第 6 条记录 `node.exe` spawn 失败证据与「js 运行时验证 = 异地执行」；Task 11 的 `PATH=probes/bin:$PATH` 已全部删除（grep 0 命中） | 已销项 |
| N-04 | Task 8 同节「十组 / 十一组」自相矛盾 | 已销项：统一为「**十一组**签名 = §5.1-§5.10 十组 + `Detector::new`」+ 四类型；判据说明同步写「共 11 条签名 + 4 条类型」 | 已销项 |
| N-03 | M-01 交付范围收缩登记 | 保持已销项（M-01 / Task 11 / Task 13 三处逐字声明） | 已销项（维持） |
| N-06 | spec 修订机械 gate | 保持已销项（Task 0 Step 0），并因 N-08 扩为四项 | 已销项（维持） |
| N-07 | exit 3 断言并入 Output | 保持已销项（Task 10 Output 首段） | 已销项（维持） |
| N-10 | 其他观察项 | 未阻塞；计划侧已同步处理与 N-01/N-04 重叠部分 | 记录 |

**v4 结论**：计划升 v4；本轮 1 Blocking + 1 NOT CLOSED + 1 Blocking 级 + 3 PARTIAL 全部销项。

---

# 第五轮核验（v4，最终放行核验）

> **审查对象**：`docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md` v4（1113 行 / 111,449 B）
> **审查方法**：6 条销项逐条实跑；C6 六条契约独立实现后六态实测；N-05 三态实测；不采信作者自述。
> **结论**：**Issues Found**（6 条中 CLOSED 3 / PARTIAL 2 / NOT CLOSED 1；新增 Blocking 1 条）

## R5-0. 销项统计

| 判定 | 条数 | 编号 |
|---|---|---|
| CLOSED | 3 | N-05、N-08、N-04 |
| PARTIAL | 2 | N-01（六态中 ⑤ 未复现、⑥ 需区分存活态）、N-02（M-02 已修，Task 11 口径未同步到 3 处） |
| NOT CLOSED | 1 | N-09（`moon test --target js` 已删，但 Task 11 Step 5 / Task 13 Step 6 / Carry-over U-02 三处仍写「js 判绿 / 结构+准确率」） |

## R5-1. N-05 — CLOSED

计划行 573 的新判据（`out=$(moon test ... -f 'ln_for_gauss_bits*')` + 用例数 ≥1 + `failed: 0` + 文件含测试名）。我三态实测：

```
$ out=$(cd probes/embed-probe && moon test --target native -f 'entries af'); echo "$out" | tail -1
Total tests: 1, passed: 1, failed: 0.
$ n=$(printf '%s' "$out" | grep -oE 'Total tests: [0-9]+' | grep -oE '[0-9]+'); test "$n" -ge 1 && printf '%s' "$out" | grep -q 'failed: 0'
state1_rc=0        n=1                      ← ① 真测试名：绿

$ out=$(cd probes/embed-probe && moon test --target native -f 'nonexistent*'); n=$(...)
Total tests: 0, passed: 0, failed: 0.
state2_rc=1        n=0                      ← ② 不存在：必红

$ o2="Total tests: 1, passed: 0, failed: 1."   # 模拟断言失败
state3_rc=1                                  ← ③ failed:1：必红
```

三态全部符合。计划同时更正了 `-f` 的语义描述（「按测试名 glob 过滤」），与 `moon test --help` 输出一致：
```
  -f, --filter <FILTER>
          Run only tests whose name matches the given glob pattern.
```

## R5-2. N-08 — CLOSED

D-05 已新增（行 1030），Task 0 Step 0 gate 扩为四项（行 471）。我逐字复跑：

```
$ a=$(awk '/^### D2 架构/,/^\*\*依赖方向\*\*/' spec.md | grep -c 'unicode_block')
$ b=$(awk '/^## 4A\./,/^## 5\./' spec.md | grep -c 'cmd/golden')
$ c=$(awk '/^## 4A\./,/^## 5\./' spec.md | grep -c 'gen_core_tables')
$ d=$(awk '/^## 4A\./,/^## 5\./' spec.md | grep -c 'c6_zero_network')
unicode_block=0 cmd/golden=0 gen_core_tables=0 c6_zero_network=0
gate_rc=1                     ← 正确阻塞（未修订 spec 时 Task 1+ 不得启动）
```

四个正则的锚点范围与 spec 实际结构对得上；gate 可证伪（修订后四值应 ≥1 → rc=0）。

## R5-3. N-04 — CLOSED

行 767 / 771 已统一为「**十一组**签名 = §5.1-§5.10 十组 + `Detector::new`」+ 四类型。我构造正样本与注释样本复测：

```
$ for p in '^pub fn detect\(' … '^pub fn is_upper_cp312\('; do grep -rEq -- "$p" src || echo "MISSING: $p"; done
positive_rc=0                              ← 11 项全命中
$ # 注释-only 样本（// pub fn Detector::new() …）
MISSING(comment-only): ^pub fn (Detector::)?new\(\) -> Detector
MISSING(comment-only): ^pub fn (Detector::)?set_seed\(self
                                           ← 注释不假通过
```

计数措辞已统一，无「十组/十一组」并存。

## R5-4. N-01 — PARTIAL

### 六态实测（我按行 848 六条契约独立实现 `/tmp/c6f.sh`）

| 态 | 我的实测 | 计划表 | 判定 |
|---|---|---|---|
| ① 无 socket 慢进程 | `HITS=0 SAMPLES=9 WINPID=25588 child_rc=0` → rc=**0** | `HITS=0 SAMPLES=5` rc=0 | ✅ 一致 |
| ② 持 TCP 连接 | `HITS=9 SAMPLES=10 WINPID=20324 child_rc=0` → rc=**1** | `HITS=54 SAMPLES=19` rc=1 | ✅ 一致（数量级差异源于进程存活时长） |
| ③ 二进制缺失 | 无输出 → rc=**2** | 无输出 rc=2 | ✅ 一致 |
| ④ 瞬时退出 | `HITS=0 SAMPLES=1 WINPID=79079 child_rc=0` → rc=**0** | `SAMPLES=1` rc=0 | ✅ 一致（首采前置生效，不再 exit 3） |
| ⑤ stdin 契约 | `HITS=0 SAMPLES=1 WINPID=6732 child_rc=0 out=GOT:hello` → rc=**0** | `got:hello` rc=0 | ✅ 一致（见下） |
| ⑥ `ps -W` 不可用 + 存活进程 | `WINPID_MAPPING_FAILED` → rc=**2** | 无输出 rc=2 | ✅ 一致（见下） |

**⑤ stdin 契约实证**（这是 v3 的缺口，v4 已修）：
```
$ sh /tmp/c6f5.sh F:/Temp/v4chk/rd.exe.sh F:/Temp/v4chk/in.txt   # 契约形态 "$1" < "$2"
HITS=0 SAMPLES=1 WINPID=6732 child_rc=0 out=GOT:hello           ← 输入确实被喂进去
$ sh /tmp/c6null.sh F:/Temp/v4chk/rd.exe.sh                      # 对照：< /dev/null
out=[GOT:]                                                       ← 读不到输入
```

**⑥ 守卫的两种分支我分别验证**：
```
# 分支 A：W 为空 且 进程仍存活 → exit 2
$ sh /tmp/c6s6b.sh python slow.py
after_retry W=[] pid=87853 alive=YES
GUARD exit2                                    rc=2   ← 守卫生效

# 分支 B：W 为空 且 进程已退出 → 回退 W=$PID
$ sh /tmp/c6s6b.sh /tmp/inst.sh
after_retry W=[] pid=87921 alive=NO
FALLBACK W=87921
HITS=0 SAMPLES=1 WINPID=87921 child_rc=0       rc=0   ← 回退生效
```

### 回退 `W=$PID` 的安全性（用户点名怀疑点）

**结论：安全**。理由与实测：
1. `$PID` 是 Cygwin PID，`netstat -ano` 的 PID 列是 Windows PID，两者属**不同命名空间**。回退发生在「进程已退出」之后，此时该 Cygwin PID 已无对应进程。
2. 我实测四个真实 Cygwin PID 在 Windows netstat 中的命中数：
```
pid=85310 hits=0
pid=85410 hits=0
pid=87853 hits=0
pid=87921 hits=0
```
3. 即便发生数值碰撞（Cygwin PID 恰好等于某个 Windows 进程 PID），该 Windows 进程必须在采样瞬间**恰好持有网络连接**才会被计入；且回退分支只在「瞬时进程（存活 < 1 次重试窗口）」触发，采样窗口本身极短。
4. 更关键：回退分支的正确判据是「进程已退出 → 不可能自己发起网络」，此时 `HITS` 本应为 0；若因碰撞得到非 0，是**假红**（拒绝），不会造成假绿（放行）。方向安全。

**建议（非阻塞）**：回退分支加一行注释说明「回退仅在进程已退出时使用，碰撞只会造成假红不会造成假绿」。

### 剩余 PARTIAL 原因

契约⑥ 的「`ps -W` 不可用」判定依赖**进程仍存活**这一条件，而「存活」与「已退出」的判定窗口由重试循环（20×50ms）决定。若被测进程在 1 秒重试窗口内退出，脚本走回退分支（rc=0），**不会**触发 exit 2——这与计划表 ⑥ 的语义（「以 false 替换 ps -W + 存活 5s 进程 → rc=2」）一致，但**计划未写明「进程存活时长必须 > 1s 才能触发守卫」**，执行者若用瞬时进程测试 ⑥ 会得到 rc=0 并误判「守卫生效」。

**改法**：契约⑥ 补一句「验证该守卫必须用存活 > 1.5s 的进程（重试窗口 1s + 余量）」。

## R5-5. N-02 — PARTIAL

**已修**：M-02 第 1 条（行 375）显式路径 + 前置断言；第 6 条（行 381）记录 `node.exe` spawn 失败证据。实测：
```
$ ./probes/bin/node.cmd --version      → 1.4.3  rc=0
$ command -v node                       → C:\Users\Administrator\.bunpm\bin\node.cmd（前置无效）
```
`grep -c 'PATH=probes/bin' plan` → **0**（已清除）。

**未修（PARTIAL 原因）**：js 口径的收缩只落在 Task 11 Step 2/3 与 Output，**三处旧表述未同步**：

```
$ sed -n '63p' plan
| U-02 | js 目标在官方 node 下的结果 | 承接 | Task 11：`moon test --target js` 记录运行时身份（bun），结构 + 准确率判据；回补手册 M-02 |
                                                          ↑ 仍写「结构 + 准确率判据」，与 Task 11 的「仅构建」冲突

$ sed -n '885p' plan
5. 三目标主语言 / 语言数 / 条目合计：js 判绿；wasm-gc 标 `[LOCAL_DEAD_LINK]` …
                                              ↑ 与同节 Step 3「js 本机不得判绿」直接矛盾

$ sed -n '942p' plan   （Task 13 Step 6）
6. 写 final-report：… **必须逐字写入交付范围收缩声明**：「wasm-gc 本批口径 = 仅 `moon build --target wasm-gc` rc=0；…」
                                                          ↑ 只写 wasm-gc，缺 js
```

## R5-6. N-09 — NOT CLOSED

Task 11 Step 2/3 已正确降级（本机只 `moon build --target js`，测试与比对标 `[LOCAL_DEAD_LINK]`），但**三处下游未同步**（即 R5-5 列出的三处）：

1. **Carry-over 表 U-02 行（行 63）**：仍写「`moon test --target js` 记录运行时身份（bun），结构 + 准确率判据」——这是 v1 时代的判据，与 v4 的「仅构建」相反。按 CO4 机械检索门禁，该行会被判「承接判据与任务定义不一致」。
2. **Task 11 Step 5（行 885）**：`js 判绿`——与 Step 3 的「本机不得判绿」**同一节内直接矛盾**。执行者按 Step 5 会把 js 判绿，等于把 U-02 的死链当已验收。
3. **Task 13 Step 6（行 942）**：final-report 的收缩声明模板只含 wasm-gc，缺 js；Task 13 是终验门禁，模板缺项会导致 js 收缩**不被记录**。

这三处不是措辞问题，而是**执行时会产出一份「js 已判绿」的验收报告**——正是 v1 以来反复拦截的「把死链当已验收」。因此判 NOT CLOSED。

## R5-7. 新发现问题

### N-11（Blocking）js 收缩声明未闭环，三处旧表述会产出「js 已判绿」的报告

- **位置**：行 63（Carry-over U-02）、行 885（Task 11 Step 5）、行 942（Task 13 Step 6）
- **证据**：见 R5-5 / R5-6 的三段 `sed` 输出。
- **影响**：Task 11 Step 5 与 Step 3 同节矛盾；Task 13 的 final-report 模板缺 js 收缩声明；Carry-over 表的承接判据与实际任务定义不符（CO4 机械检索门禁会红）。
- **改法**：
  1. 行 63 改为「Task 11：本机仅 `moon build --target js` rc=0；`moon test --target js` 与 `compare_golden --target js` 标 `[LOCAL_DEAD_LINK]`（U-02 / M-02），异地执行」。
  2. 行 885 改为「三目标主语言 / 语言数 / 条目合计：**js 与 wasm-gc 均标 `[LOCAL_DEAD_LINK]`**（U-02 / U-09 / U-10），本机不判绿；仅 native 判绿」。
  3. 行 942 的收缩声明模板补 js：「js 本批口径 = 仅 `moon build --target js` rc=0；`moon test --target js` 与 js 侧比对不入本批验收范围（依据 U-02 + M-02）」。

### N-12（Should-fix）C6 契约⑥ 未写明守卫触发所需的进程存活时长

- **位置**：行 848 契约⑥、行 850-859 六态表 ⑥
- **证据**：我用瞬时进程测 ⑥ 得到 rc=0（走回退分支），用 2s 进程得到 rc=2（守卫生效）：
```
$ sh /tmp/c6s6b.sh python slow.py      → GUARD exit2, rc=2
$ sh /tmp/c6s6b.sh /tmp/inst.sh        → FALLBACK W=87921, rc=0
```
- **改法**：契约⑥ 补「验证守卫须用存活 > 1.5s 的进程（重试窗口 20×50ms + 余量）」。

### N-13（Note）v4 新增 11 行均为实质内容

1102 → 1113 行的增量核对：D-05 行（1030）、Task 0 gate 第四项（471）、Task 11 Step 2/3 重写（882-883）、Task 11 Output 口径（892）、Task 3 第④判据重写（573）。无空行灌水。

## R5-8. Blocking Checks 全量重判（15 条）

| # | 检查项 | 判定 | 依据 |
|---|---|---|---|
| 1 | Spec Coverage | **PASS** | FR-13（C5）、FR-24（C6）均有可执行载体；C6 六态实测全绿/全红符合 |
| 2 | Executability | **PASS** | `PATH=probes/bin` 已清零；M-02 显式路径可执行（`1.4.3` rc=0） |
| 3 | Consistency | **FAIL** | Task 11 Step 3（js 不得判绿）与 Step 5（js 判绿）同节矛盾；Carry-over U-02 与任务定义不符——N-11 |
| 4 | Testability | **PASS** | N-05 三态实测（1 用例→0 / 0 用例→1 / failed:1→1）；Task 0 计数四态实测；C6 六态实测 |
| 5 | Granularity | **PASS** | 14 Task 字段齐备（时长/轮次/允许修改清单） |
| 6 | Authority-Source Alignment | **PASS** | Authority 表 `file:line:方法` 全部落地 |
| 7 | Spec-Plan Consistency | **PASS** | cmd29 rc=0 一致；D-01…D-05 五条裁决齐备 |
| 8 | Field-Mapping Table | **PASS** | Dependency Contract 17 行类型/NULL 性逐字复制 |
| 9 | Acceptance Command Verification | **PASS** | 30 条逐字一致（130/130 diff=0）；C6 脚本已进 D-05 + gate |
| 10 | Spec-Decision Traceability | **PASS** | D-02…D-05 均「修订 spec」且有具体改点与机械 gate |
| 11 | Compile-Probe Task 0 | **PASS** | Task 1 探针位置正确；Task 0 计数与 gate 均可证伪 |
| 12 | External-Dependency Verification | **PASS** | M-01/M-02 均已实测改写，js 降级为异地执行 |
| 13 | Golden-Vector Local Baseline | **PASS** | md5 `219519ee…`、golden 9 项齐备 |
| 14 | Incremental Review Checkpoints | **PASS** | 每片 V1 + V3 |
| 15 | `[LOCAL_DEAD_LINK]` Marking | **FAIL** | js 收缩未闭环：Task 11 Step 5「js 判绿」与死链语义冲突——N-11 |

**统计：PASS 12 / FAIL 3 / N-A 0。**

## R5-9. 最终判定

**Status: Issues Found（阻断开执行）**

唯一阻断项 **N-11**：三处旧表述（行 63 / 885 / 942）会把 js 死链写成「已判绿」。这不是文风问题——按 Task 11 Step 5 字面执行，final-report 会出现「js 判绿」，与 U-02 的 `[LOCAL_DEAD_LINK]` 直接冲突，等于交付一份自相矛盾的验收报告。

**放行条件（3 处文字改动，无需重跑任何命令）**：
1. 行 63（Carry-over U-02）：改为「本机仅 build；测试与比对标 `[LOCAL_DEAD_LINK]`（U-02/M-02）」。
2. 行 885（Task 11 Step 5）：改为「js 与 wasm-gc 均标 `[LOCAL_DEAD_LINK]`，本机不判绿；仅 native 判绿」。
3. 行 942（Task 13 Step 6）：收缩声明模板补 js 一句。

改完即可判 **Approved**；N-12（契约⑥ 存活时长说明）建议同批，不阻塞。

---

**第五轮核验结束**

---

## 11. 第六轮登记（v4 核验，2026-10-21）

> 结论：CLOSED 3（N-05 / N-08 / N-04）+ NOT CLOSED 1（N-09 口径未闭环）+ PARTIAL（N-01 / N-02 / N-10）。**纯文本修订，无新命令。**

| 编号 | 定义原文（摘要） | 销项证据 | 状态 |
|---|---|---|---|
| N-09 | js 口径必须四处一致闭环 | 已销项：三处全文修订 + 四处口径核对一致 —— ① 行 63 Carry-over U-02 行改为「本机仅 `moon build --target js` rc=0；`moon test --target js` 与 `compare_golden --target js` 一律标 `[LOCAL_DEAD_LINK]`（U-02 / M-02），异地执行，本机不得判绿」；② 行 885 Task 11 Step 5 改为「js 与 wasm-gc **均**标 `[LOCAL_DEAD_LINK]`…**仅 native 判绿**」；③ 行 942 Task 13 Step 6 收缩声明模板补上 js 段；④ 行 883 Task 11 Step 3 原已正确。自检：`grep -c 'js 判绿' plan` → **0**；`grep -c 'PATH=probes/bin' plan` → **0** | 已销项 |
| N-12 | C6 契约⑥ 须说明守卫的验证条件 | 已销项：Task 10 C6 契约⑥ 补句「**验证该守卫时，被测进程须存活 > 1.5 s**（短于 `ps -W` 重试窗口 1 s 的进程会走『已退出回退』分支而得 rc=0，观察不到守卫）」 | 已销项 |
| N-05 / N-08 / N-04 | 三轮前已销项 | 维持 | 已销项（维持） |
| N-01 / N-02 | C6 六态与 M-02 已销项 | 维持（本轮核到的六态数据与计划表全部一致） | 已销项（维持） |

**v5 结论**：计划升 v5；N-09 口径闭环 + N-12 补充完毕，未新增 Blocking。

---

# 第七轮：放行判定（v5）

> **审查对象**：`docs/superpowers/plans/2026-10-21-moon-langdetect-语种检测.md` v5（1113 行 / 112,103 B）
> **范围**：仅核对上一轮唯一阻断项（N-11 三处口径 + N-12）与本轮四条 grep；不做新维度审查。

## R7-1. 四处改动逐字核对

| 位置 | 计划现状（我的 `sed` 输出） | 与改法一致性 |
|---|---|---|
| 行 63（Carry-over U-02） | `Task 11：本机仅 moon build --target js rc=0；moon test --target js 与 compare_golden --target js 一律标 [LOCAL_DEAD_LINK]（U-02 / M-02），异地执行，本机不得判绿；回补手册 M-02` | ✅ 逐字一致 |
| 行 885（Task 11 Step 5） | `三目标主语言 / 语言数 / 条目合计：js 与 wasm-gc 均标 [LOCAL_DEAD_LINK]（js → U-02 / M-02；wasm-gc → U-01 / U-08 → M-01 / M-08 / M-09 / M-10），本机不判绿；仅 native 判绿（M-09 / M-10 的 native 部分仍在本机执行）` | ✅ 逐字一致，且补了「native 部分仍在本机执行」的边界 |
| 行 942（Task 13 Step 6） | wasm-gc 声明后追加：`「js 本批口径 = 仅 moon build --target js rc=0；moon test --target js 与 js 侧 compare_golden 比对 不入本批验收范围（交付范围显式收缩，依据 U-02 + M-02）」` | ✅ 逐字一致 |
| 行 848 契约⑥ | `⑥ 退出码：二进制不存在 → 2；W 为空且进程存活（ps -W 不可用）→ 2；HITS > 0 → 1；子进程 rc≠0 → 1；否则 0。**验证该守卫时，被测进程须存活 > 1.5 s**（短于 ps -W 重试窗口 1 s 的进程会走「已退出回退」分支而得 rc=0，观察不到守卫）——N-12` | ✅ 与 N-12 建议一致，且解释了机理 |

## R7-2. 四条 grep（我实跑）

```
$ grep -c 'js 判绿' <plan>
0                                   ← 期望 0 ✅
$ grep -c 'PATH=probes/bin' <plan>
0                                   ← 期望 0 ✅
$ grep -c '^## Task ' <plan>
14                                  ← 期望 14 ✅
$ grep -nE 'TODO|FIXME|待定|视情况|不猜|/opt/node' <plan>
（无输出，rc=1）                     ← 期望 0 ✅
```

## R7-3. Task 11 四处 js 口径一致性抽查

| 位置 | 对 js 的说法 | 判定 |
|---|---|---|
| Step 2（行 882） | 「本机**不跑** `moon test --target js`；仅 `moon build --target js` 记录 rc；js 冒烟标 `[LOCAL_DEAD_LINK]`（U-02 / M-02）」 | 仅构建 + 死链 + 异地 ✅ |
| Step 3（行 883） | 「js（**仅构建**）：`moon build --target js` rc=0 + sha256；`moon test --target js` 与 `compare_golden --target js` **全部标 `[LOCAL_DEAD_LINK]`**，本机不得判绿」 | 仅构建 + 死链 + 异地 ✅ |
| Step 5（行 885） | 「js 与 wasm-gc **均**标 `[LOCAL_DEAD_LINK]`……**仅 native 判绿**」 | 仅构建 + 死链 + 异地 ✅ |
| Output（行 892） | 「js = **仅构建**（`moon build --target js` rc=0；测试与比对异地执行，U-02 / M-02）……**本批交付范围收缩**：js 运行时验证不入本批验收范围」 | 仅构建 + 死链 + 异地 ✅ |

**四处口径完全一致，无残留矛盾。**

## R7-4. 附带复核（不引入新维度，仅确认未被 v5 改坏）

```
$ diff <spec §10.6 命令块> <plan 命令块>
IDENTICAL (130 lines)               ← 30 条仍逐字一致
$ md5sum docs/port/golden/expected.json
219519ee19d7cc10d404ddbdab3acd87    ← 基准未变
$ # Task 0 Step 0 四项 gate 当前状态
a=0 b=0 c=0 d=0 → gate_rc=1          ← 仍正确阻塞（spec 未修订）
$ sed -n '336p' plan                 ← 命令 11b 仍为可执行形态
grep -rn -e println -e 'print(' -e eprintln -e '@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam | grep -vE '[\\/]cmd[\\/]main[\\/]'
```

## R7-5. 最终判定

**Status: Approved**

上一轮唯一阻断项 N-11 的三处口径已逐字落地，N-12 已补，四条 grep 全部达期望，Task 11 四处 js 口径一致，30 条命令仍与 spec 逐字一致。无新增阻断。

---

**第七轮放行判定结束**
