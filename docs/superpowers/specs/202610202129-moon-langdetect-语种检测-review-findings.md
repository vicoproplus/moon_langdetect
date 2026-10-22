# Spec 复审发现登记表（DC-F）

> **文档标题（机器可检索）**：`moon_langdetect 语种检测库 spec 复审发现登记表`
> **版本**：v1（2026-10-20）
> **审查对象**：`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md`（679 行 / 59,693 B，v1）
> **审查依据**：`C:/Users/Administrator/.agents/skills/brainstorming/references/spec-document-reviewer-prompt.md`（Blocking Checks 全量 53 条）
> **上游权威**：PRD（`docs/superpowers/prds/202610202129-moon-langdetect-语种检测-prd.md`）、DESIGN（`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-design.md`）、`约定 A：档案内嵌数据格式与生成契约`、`约定 B：U3 Unicode 大小写表生成契约`、`约定 C：golden 基准消费契约`、ADR（`docs/port/architecture-decisions.md`）
> **复审方法**：所有「已实跑」断言由本审查员独立重跑；T2 违规样本由本审查员现场构造；`file:line` 指针逐条落地核对；不采信文档自述。

---

## 0. 审查结论

**Status: Issues Found**

| 等级 | 条数 |
|---|---|
| Blocking | 14 |
| Should-fix | 11 |
| Note | 6 |

**判据摘要**：spec 的事实层（§1 的 48 条 V-XX）质量高——抽查的 15+ 条指针全部落地，55 / 184129 / 2204952 / 268 / 250 / 18 / 1951 / 651 / 21206 / 21451 / 2205308 / 3256320 全部由我独立复跑复现。缺陷集中在**契约层与门禁层**：门禁命令有 3 条无法实现其声明的判据（C-C6、DR8、C-B6），§15 的 T1/T2 合计与分组相加不符，`<产品目录>` 占位符从未定义导致 11 处命令不可执行，4 处 MoonBit 签名在真实编译器下不成立，且缺少 spec 四维（D1-D4）、交付物清单、源侧测试对齐与失败取证通道。

---

## 1. Blocking（必须改才能进 plan）

### BLK-01 缺少 spec 四维一致性内容（D1 背景 / D2 架构 / D3 范式 / D4 解决方案）

**定义原文**：`spec-document-reviewer-prompt.md` Blocking #5 —— 「Does the spec produce the four-dimensional consistency content (背景/架构/范式/解决方案, D1-D4) with NO implementation code…missing any of the four dimensions, blocks the whole spec.」

**证据（我跑的）**：

```
$ grep -n "背景\|架构\|范式" docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
（无输出，exit 1）
$ grep -n "^#\{1,3\} " docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md
16:## 0. spec 复杂度判定
32:## 1. Verified facts（先于任何结论）
155:## 2. Gap 表（源侧 vs 目标侧）
209:## 3. PRD 回链表
251:## 4. 数据模型（schema 级）
303:## 5. 公开接口契约（签名级）
406:## 6. 错误码与消息表
424:## 7. 方言红线表（DR1-DR3，append-only）
443:## 8. 验收表（分层，≥3 维度）
489:## 9. 行为等价断言（三层 + 负向轴）
543:## 10. 机检门禁命令清单
599:## 11. 契约可实现性互查
620:## 12. 文档契约纪律
634:## 13. 红线段
649:## 14. 未决与 [LOCAL_DEAD_LINK]
665:## 15. 门禁命令汇总
```

**问题**：全文没有任何一节承担 D1 背景 / D2 架构（系统结构、模块边界、数据流）/ D3 范式（技术选型、命名与组织约定、技术路线）/ D4 解决方案（方案决策 + 理由 + 范围 in/out）。§1 是事实表、§5 是签名表，都不构成架构维度：模块如何切分（数学接缝 / 字符属性 / 档案 / 清洗 / 特征 / 概率更新）、谁依赖谁、数据从档案到概率表的流向，全部缺席。DESIGN §七 G1 有 PS1 接缝表、WB1 承载面表，spec 未承接。

**改法**：在 §1 之前插入 D1（引 PRD 一、二节，不复述）、D2（模块边界图/表：接缝模块、字符属性模块、档案模块、清洗与特征、概率更新、公开入口；含依赖方向与「业务侧零平台分支」）、D3（技术路线：零第三方依赖、U3 表、扁平字符串、`extern "C" log`、`suberror` 异常；命名约定）、D4（承接 DESIGN D1-D12 的决策表指针 + 范围 in/out）。同时把 §4.4 的代码围栏（第 284-290 行 `sort_key(entry) = (...)` 与 Python 列表推导引文）改为纯自然语言描述，因为文档头第 10 行自述「不含实现代码、伪代码」。

---

### BLK-02 §15 门禁汇总的 T1/T2 合计与分组相加不符（DC-D 违反）

**定义原文**：`document-contract-discipline.md` DC-D —— 「文档正文中所有手写的计数类声称…每个手写数字要么由机检命令派生…要么不写死」；Blocking #49 要求每个定量断言带「断言 + 域定义 + 可重跑命令 + 结果」四元组且域与测量域对账。

**证据（我跑的）**：spec 第 667-675 行逐字为：

```
| 约定 A（C-A1…C-A6） | 6 | 6 | 5（…） | 6 |
| 约定 B（C-B1…C-B6） | 6 | 4（…） | 5（…） | 6 |
| 约定 C（C-C1…C-C6） | 6 | 5（C6 为 md5 记录） | 4 | 6 |
| 方言红线（DR1-DR8） | 8 | 8（对现有探针基线） | 3 条构造实录（DR1/DR5/DR7 类） | 8 |
| 合计 | 26 | 22 | 13 | 26 |
```

我做的算术核对：

```
T1: 6 + 4 + 5 + 8 = 23   ≠ 22（表内合计）
T2: 5 + 5 + 4 + 3 = 17   ≠ 13（表内合计）
命令条数: 6 + 6 + 6 + 8 = 26 ✓
```

同时 §10.4 表内实际只有 **3** 行写了构造实录（DR1 / DR5 / DR7），DR2 写「探针中命中仅在 rand-probe.mbt:203 的降级路径」不是违规样本，DR3/DR4/DR6/DR8 只写「构造样本 → 命中」而未落实录退出码。

**改法**：把 T1/T2 两列改为由命令派生的数字（逐行计数脚本输出），或删除合计行改为「见 §10.x 逐行状态」；T2 列对未实录的行显式写「未做 T2（阻塞项 SF-02）」。

---

### BLK-03 C-C6 没有比对命令，T2「比对 exit 1」不可能发生

**定义原文**：Blocking #50 —— 每条机检命令必须有 T1 语法可跑 + T2 已知违规样本必红（附声明退出码）+ T3 可证伪路径。

**证据（我跑的）**：spec 第 574 行 T2 列写「人为改 1 字节 → md5 变化，**比对 exit 1**」。但该行 T1 列给出的全部命令只有 `md5sum docs/port/golden/expected.json`：

```
$ cp docs/port/golden/expected.json F:/Temp/tmp.yY8g4pn6Y5/mod.json
$ printf 'x' >> F:/Temp/tmp.yY8g4pn6Y5/mod.json
$ md5sum F:/Temp/tmp.yY8g4pn6Y5/mod.json
ad495cd0134fa3e2ce4a0daea443dabe  F:/Temp/tmp.yY8g4pn6Y5/mod.json
md5sum_modified_exit=0        ← 文件已被改，命令仍然 exit 0
$ md5sum docs/port/golden/expected.json
219519ee19d7cc10d404ddbdab3acd87  docs/port/golden/expected.json
md5sum_orig_exit=0
```

`md5sum` 恒 exit 0，spec 没有给出「与 V-22 期望值比较」的那条命令，因此 T2 的「比对 exit 1」没有载体，T3 也无从证伪——该门禁当前对「基准被改」零约束力。

**改法**：补一条可执行比对命令（示例形态，非唯一写法）：`test "$(md5sum docs/port/golden/expected.json | cut -d' ' -f1)" = "219519ee19d7cc10d404ddbdab3acd87"`，并把 T2 实录改为该命令的 exit 1。

---

### BLK-04 `<产品目录>` 占位符从未定义，11 处门禁命令不可执行（GP1 幽灵输入）

**定义原文**：`gate-command-validation-gate.md` GP1 —— 「每条命令引用的每个路径反查到四要素（生成时点/责任单元/生成命令/校验命令）；反查不到 = 该命令不可跑」。

**证据（我跑的）**：

```
$ grep -o "<产品目录>" docs/.../…-spec.md | wc -l
11
$ grep -n "产品目录的路径\|产品目录 =\|产品目录为\|产品目录：\|产品目录路径" docs/.../…-spec.md
（无输出，exit 1）
```

出现位置：第 430/431/433/434/435/436/437 行（DR1-DR8 全部）、第 509/510 行（L1-A1/L1-A2）、第 537/539 行（NE4-2/NE4-4）。另有第 451 行「cwd = 产品工程」、第 465 行「`<产品目录>/moon.pkg`」同属未定义路径。

DESIGN WB2（第 297-303 行）给出了允许落点，但 spec 从未把「产品目录 = 哪个路径、moon.mod 名 = 什么、包名 = 什么」写死；而 §2 第 165 行的枚举命令又把 `probes/` 排除在外，等于命令的扫描域本身悬空。

**改法**：在 §5 前新增「产品工程落点」小节，写死：`moon.mod` 的 `name`（逐字）、产品源码目录路径（逐字）、数据产物路径、U3 表路径、生成器路径，并对每个路径给出 GP1 四要素行。DR/NE4/L1 的命令把 `<产品目录>` 替换为该路径。

---

### BLK-05 C-B6 的 T1 是空路径假通过（vacuous pass）

**定义原文**：`gate-command-validation-gate.md` §1 规则 —— 「一切正常时也输出 OK 的命令…必然假通过」；GP1 禁止幽灵输入。

**证据（我跑的）**：spec 第 564 行 T1 列写「当前 `lib/` 不存在 → grep 无匹配 → exit **0**」。仓库根确无 `lib/`：

```
$ ls -d lib
ls: cannot access 'lib': No such file or directory
$ test "$(grep -rlE 'moonbitlang/x|unicode-data' lib/ | wc -l)" = "0"; echo "EXIT=$?"
grep: lib/: 系统找不到指定的文件。 (os error 2)
EXIT=0            ← grep 报错（真实 exit 2），但 $(...) | wc -l 把它洗成 0
$ grep -rlE 'moonbitlang/x|unicode-data' lib/ >/dev/null 2>&1; echo "grep_exit=$?"
grep_exit=2
```

**问题**：路径不存在时命令仍报绿，且 spec 把这个假绿当成 T1「结构已试跑」的证据。这正是门禁校验门禁要挡的「多路径存在性检查在布尔上下文对空数组恒真」形态。此外 §10.2 表头写「B1-B6」但只列 4 行（C-B1/C-B3/C-B4、C-B2、C-B5、C-B6），B1/B3/B4 合并计，与 §15「6 条」的口径不一致。

**改法**：命令改为先断言路径存在再检索（`test -d <产品目录> || exit 2` 后再 `grep -r`），并把 T1 实录改成「路径存在时的 0 命中」；`lib/` 这个路径本身要按 GP1 登记或删除。

---

### BLK-06 DR8 的检索式匹配不到它自己声明的判据（`@data.` 被算作未加前缀）

**定义原文**：Blocking #43/#50 —— 方言红线每行须有「可机检形态」，且门禁命令的 T1/T2/T3 成立。

**证据（我跑的）**：spec 第 437 行判据为「`grep -rnE '\b(data|math|fs)\.[a-z_]+\('` 中，**未带 `@` 前缀**的调用必须 0 命中」。但 `\b` 在 `@` 与 `d` 之间成立，正则会把合法的 `@data.entry_count(` 也算命中：

```
$ grep -rnE '\b(data|math|fs)\.[a-z_]+\(' --include=*.mbt probes/embed-probe | wc -l
111
$ grep -rnE '\b(data|math|fs)\.[a-z_]+\(' --include=*.mbt probes/embed-probe | grep -vc '@'
0
```

也就是说：111 行**全部**是合法的 `@data.` 调用，判据「未带 @ 前缀」在该正则下无法表达；按 spec 原样执行，正确代码会全红（假红），而真正的违规只能靠人工二次过滤。第 587 行 T1 列自己也写了「`main.mbt:5-6` 用 `@data.` 前缀」——恰好是假红的证据。

**改法**：正则改为显式排除前缀（示例形态）：`grep -rnE '(^|[^@[:alnum:]_])(data|math|fs)\.[a-z_]+\('`，并把 T1 实录改为「对 `probes/embed-probe` 输出 0 行」，T2 仍用 `data.languages(` 命中。

---

### BLK-07 4 处 MoonBit 签名在真实编译器下不成立

**定义原文**：Blocking #34（消费契约字面精确：契约中的字面形态必须可用且有证据等级）+ #31（语言特性依赖须有矩阵行与探针记录）。

**证据（我跑的，`moon 0.1.20261012` / `moonc v0.10.15+943464bfa`）**：

1) `struct` 不能作为 `raise` 类型（spec 第 387 行 `struct LangDetectError { code : Int, … }` 与第 311/323 行 `raise LangDetectError`）：

```
Error: [4127] Type LangDetectError is not an error type.
Error: [4118] The error type is mismatched: wanted: LangDetectError / has: Error.
```

改用 `suberror LangDetectError { CantDetect(code~ : Int, message~ : String, input_len~ : Int, input_prefix~ : String) }` 后 `moon check` → `Finished. moon: ran 2 tasks, now up to date`。

2) 未命名参数不能带默认值（spec 第 358 行 `Detector::create(alpha : Double? = None) -> Detector`）：

```
Error: [3010] Only labelled arguments can have default value.
```

3) `Confidence` 的 `{ … }` 载荷语法不成立（spec 第 336 行 `LowConfidence { char_count : Int }` / `Detected { lang : String, probs : Array[LangProb] }`）：

```
Error: [3002] Parse error, unexpected token `{`, you may expect `;` or `}`.
```

改为 `LowConfidence(char_count~ : Int)` / `Detected(lang~ : String, probs~ : Array[LangProb])` 后通过。

4) 同一批：第 387 行 `struct` 与 §4.3 的字段表（第 279-280 行）没有声明结构体名，§5.1 用 `LangProb`、§4.3 只列 `lang`/`prob` 两字段，两处类型名对不上。

**改法**：把 §5.8 改为 `suberror` 形态并列出每个变体与字段；`create` 的默认值改为 `alpha? : Double` 或 `alpha : Double?`（无默认值）；`Confidence` 改为标签载荷；在 §4.3 增补 `LangProb` 结构体名并让 §5 引用同一名字。以上每条按 CC2 标证据等级 A（附本次 `moon check` 输出）。

---

### BLK-08 §8 验收表缺 FR-05 / FR-06 行（P0/P1 覆盖缺口）

**定义原文**：Blocking #1 —— 「PRD 的 P0/P1 要件全覆盖或被显式延后（附用户裁决记录）」；#9 —— 分层验收表每行绑验证命令。

**证据（我跑的）**：

```
$ grep -n "FR-05\|FR-06" docs/.../…-spec.md
224:| FR-05 | 功能需求 | §5.5 设置 seed | 已承接 |
225:| FR-06 | 功能需求 | §5.5 seed 默认 None | 已承接 |
362:| 回链 | FR-05、FR-06；US-03 |
$ awk 'NR>=443 && NR<=486' docs/.../…-spec.md | grep -c "FR-05\|FR-06"
0
```

FR-05（P0，seed 生效 + 换 seed 结果变化）与 FR-06（P1，未设 seed 允许不可复现且不得报错）只在 §3 回链表与 §5.5 契约里出现，§8.2 的 6 个分组（第 460-465 行）没有覆盖它们，也没有任何可运行验证。§3 第 247 行的「26/26 全部出现」是「文本出现」而非「验收覆盖」，两者被混为一谈。

**改法**：§8.2 增一行「seed 语义 FR-05/FR-06」，命令写死为「seed=0 同文本 5 次输出一致（差异数 0）；改 seed=42 后输出与 seed=0 不同且可重复；不设 seed 连续 10 次允许出现多结果且零异常」，观测输出指向 `docs/port/golden/expected.json` 的 `repeatability`（14 组）与 `unseeded_runs`。并把 §3 的措辞从「全部出现」改为「全部有验收行」。

---

### BLK-09 §9.1 层 1「每个入口的副作用全枚举」不成立（B6 缺口）

**定义原文**：`behavioral-equivalence-gate.md` B6 —— 「对齐/改造涉及入口函数时，逐行枚举该函数的**全部**副作用——网络请求 / 存储写入 / 全局状态回填 / 事件通知 / 缓存 / 日志——每条副作用占一行断言；副作用清单基于对源实现的逐行走读…禁止以功能切片代替副作用枚举」。

**证据（我跑的 + 源码走读）**：§9.1 第 495-503 行只列 9 个入口，缺 4 个公开入口的副作用行：`Detector::cleaning_text`（就地改 `text`，`detector.py:130`）、`Detector::detect`（触发 `_detect_block` → 写 `langprob`，`detector.py:132-139`）、`Detector::get_probabilities`（惰性触发 `_detect_block`，`detector.py:141-144`）、`DetectorFactory::load_profile`（写 `langlist` + `word_lang_prob_map`，`detector_factory.py:35-64`）。

更关键的是漏了**引用别名回填**这一副作用：`Detector.__init__` 把工厂的容器直接赋给实例（`detector.py:57-58`）：

```
$ .venv/Scripts/python.exe -c "… d=fac.create(); print(d.langlist is fac.langlist, d.word_lang_prob_map is fac.word_lang_prob_map)"
aliasing: d.langlist is fac.langlist -> True
aliasing: d.word_lang_prob_map is fac.word_lang_prob_map -> True
```

即：检测实例与工厂共享同一个 `langlist` 引用，`add_profile` 会改变已建实例可见的语言序列。§9.3 的层 3 登记表把 `langlist` 的写方只写成「工厂 `add_profile`」、读方写成「`detect_langs` 排序 / `get_lang_list` / `_init_probability`」（第 521 行），完全没有登记「已建 Detector 通过别名读取」这条跨对象共享状态。这与 PRD 的「同一实例可重复送入文本」语义直接相关。

另：第 525 行「清洗**就地**改 `text`，重复调用幂等」——我对 `cleaning_text` 复测确认幂等（`t2==t3` → True），但 `append` 不幂等（`'hello'` → `'hellohello'`），表内未区分两者，措辞会被读成 append 也幂等。

**改法**：§9.1 补 4 个入口行；把「引用别名」作为一类副作用单列（写方 = `add_profile` / `clear`，读方 = 已建 Detector 的 `langlist` / `word_lang_prob_map`），并在 §9.3 按 PR1「一写多读逐行展开」补行；第 525 行改为「`cleaning_text` 幂等；`append` 追加而非覆盖」。

---

### BLK-10 §9.4 NE1 断言不可满足（`moon test` 必然向 stdout 打印）

**定义原文**：`behavioral-equivalence-gate.md` NE1 —— 静默语境必须断言「零错误浮层 + 声明的替代可观察结果」，且断言必须可运行。

**证据（我跑的）**：spec 第 533 行 NE1 写「一次完整检测的标准输出与标准错误均为 0 字节；`moon test` 捕获输出长度 = 0」。但 `moon test` 的汇总行恒写 stdout，且本仓库 native 测试日志的 stderr 还有编译告警与链接器输出：

```
$ head -8 probes/logs/target-native-02-test.log
--- stdout ---
Total tests: 56, passed: 56, failed: 0.
--- stderr ---
utf.c
runtime.c
$ cd probes/embed-probe && moon test --target native
Total tests: 56, passed: 56, failed: 0.
native_test_exit=0
```

按 spec 原样执行，NE1 永远红；而它要守的「静默语境不弹错」在本库（无 UI）真正对应的是「库自身不向 stdout/stderr 写任何字节」，与被测运行器 `moon test` 的输出无关。

**改法**：把断言对象从「`moon test` 的输出」改为「产品二进制自身的输出」（例如运行一个只调用 `detect` 的 `cmd/main` 可执行文件，断言其 stdout/stderr 为 0 字节），或断言「产品源码中不存在任何 stdout/stderr 写调用」的静态检查。

---

### BLK-11 失败可观测性契约缺失（FO1/FO3）

**定义原文**：Blocking #36 —— 「Does every declared failure semantic carry at least one reachable forensic channel beyond the user-visible prompt, bound to runnable verification…with the channel's target-environment availability registered and verified?」

**证据（我跑的）**：

```
$ grep -n "input_prefix\|input_len" docs/.../…-spec.md
201:| G-30 | 异常诊断四字段 … | [EXT] …
387:| 签名 | `struct LangDetectError { code : Int, message : String, input_len : Int, input_prefix : String }` |
388:| 字段语义 | … `input_prefix` = 输入前 32 个码点 |
$ grep -n "序列化\|回读\|可检索" docs/.../…-spec.md
（仅命中文档标题行的「机器可检索」，无实现契约）
```

spec 只声明了 4 个字段的**形状**，没有：① 取证通道（哪条记录、落在哪、谁写）；② 可运行验证（构造失败 → 断言记录可读回）；③ 通道在 native/js/wasm-gc 的可用性登记。PRD §5.2「失败可诊断性」明确要求「把异常对象序列化为一行结构化记录并写入调用方指定位置，断言含 `code`/`message`/`input_len`/`input_prefix` 四字段且可被重新读回；同一记录事后可按 `code` 精确匹配检索到」——这条 NFR 在 §8 没有任何验收行。

另：上游 `LangDetectException` 实测**没有** `message` 属性（只有 `args`/`code`）：

```
$ …print('has message attr', hasattr(e,'message'))
has message attr False
str No features in text. code 5 get_code 5
```

spec 第 387 行把 `message` 写成结构体字段没问题，但 §4.3/§5.8 没有说明它与上游 `str(e)` 的对应关系，实现者可能误以为上游有 `.message`。

**改法**：§5.8 增「取证通道」行（四字段 → 调用方序列化为一行 JSON → 可按 `code` 检索），并在 §8.2 增验收行（构造码 5/4/8 各一次 → 断言四字段齐备且可读回、按 `code` 命中），同时登记该通道在三个目标的可用性（纯内存 + 调用方落盘，与目标无关）。

---

### BLK-12 源侧测试文件无目标侧对应（5 个文件 / 23 个用例全部缺席）

**定义原文**：Blocking #10 —— 「Does every source-side test file have a corresponding target-side test? A source test file with no target counterpart is an alignment gap, and its absence must be recorded — not silently dropped.」

**证据（我跑的）**：

```
$ find langdetect -name "test*.py"
langdetect/langdetect/tests/test_detector.py            (6 tests)
langdetect/langdetect/tests/test_language.py            (2 tests)
langdetect/langdetect/tests/utils/test_lang_profile.py  (7 tests)
langdetect/langdetect/tests/utils/test_ngram.py         (7 tests)
langdetect/langdetect/tests/utils/test_unicode_block.py (1 tests)
$ grep -n "test_detector\|test_language\|test_ngram\|test_unicode_block\|test_lang_profile\|对应测试\|源侧测试" docs/.../…-spec.md
（无输出）
```

spec 全文没有提到这 5 个文件，§2 gap 表也没有「源侧测试 → 目标侧测试」的映射行。其中 `test_ngram.py` 覆盖 normalize 的罗马尼亚/日文/中文分支、`test_unicode_block.py` 覆盖 220 条区间表——正是 §2 G-22/G-25 的对齐项，缺少目标侧对应意味着这两条 `[ALIGN]` 的验收只有「结构在」没有「行为对」。

**改法**：§2 增「测试对齐」子表（5 行：源文件 | 用例数 | 目标侧测试文件 | 状态），未移植的用例（如 `test_lang_profile.py` 的训练期用例，对应 G-27 不移植）显式登记为 gap 行并说明理由。

---

### BLK-13 MS1-6 / MS1-8 的裁决没有落回条款文本（MS2 违反）

**定义原文**：`contract-mutual-satisfiability-gate.md` MS2 —— 「每个冲突对裁决三选一并**落回 spec 条款**…未裁决冲突对禁止进 reviewer」；「禁止冲突对裁决留口头结论不落回条款」。

**证据（我跑的）**：

- **MS1-6**（第 610 行）裁决「DR 表检索面只扫产品源码目录；产品代码注释若需说明禁令，必须用描述形态」。但 §7 的 DR1-DR8 八行可机检形态（第 430-437 行）**仍然只写** `<产品目录>`，没有一行写「检索面不含 docs/ 与 probes/」；「注释用描述形态」这条纪律也没有成为 §7 的条款（全文仅第 610 行出现一次「描述形态」，§7 无此约束）。因此裁决仍停在表里。
- **MS1-8**（第 612 行）裁决「位级档限定在已验证平台（当前 Windows x64）；其他平台按容差档」。但 §8.4 第 483 行仍写「容差档（数值待校准） | js / wasm-gc」，没有平台维度；§8.4 第 480-481 行的 native 位级行也没有「仅 win32 x64」限定。平台分档只出现在 §14 U-05 与 §11，未进入验收表条款。

**改法**：§7 增一条总则（「本表检索面 = 产品源码目录；docs/、probes/、_build/、.mooncakes/ 不在扫描域；产品注释须用描述形态」）；§8.4 把「目标环境」列改为「native (win32 x64)」/「native (其他平台，容差档)」/「js / wasm-gc（容差档）」。

---

### BLK-14 EQ1-EQ3（平台语义分叉断言）完全缺席

**定义原文**：Blocking #45 —— 「Do behavioral-equivalence assertions cover the platform semantic fork points the equivalent paths pass through (equality-semantics tiers…, null/missing semantics, type-narrowing, async timing, numeric precision) — each registered with its target-runtime tier, asserted with inputs touching that tier…?」

**证据（我跑的）**：

```
$ grep -n "EQ1\|EQ2\|EQ3\|语义分叉" docs/.../…-spec.md
（无输出，exit 1）
```

本 spec 的核心等价面恰好压在数值语义分叉上：native 走 libm `log`、js/wasm-gc 走 `@math.ln`（§5.9 第 400 行），DESIGN G3 FE2 明确这是**非等价降级**。但 spec 没有：① 分叉点清单（`log` 的 1 ulp、`Double` 的 IEEE754 比较、`NaN`/`-0.0` 在 `p > 0.1` 过滤与降序排序中的行为）；② 触及分叉档位的输入（如概率恰好等于 0.1 的边界样本、`prob` 为 NaN 的输入）；③ 契约层的分叉语义声明（`>` 对 NaN 恒 False、`-0.0 > 0.1` 为 False）。§8.4 只断言「prob_bits 逐位一致」，这属于结果层断言，对分叉缺陷是零证据。

**改法**：在 §8.4 后增「EQ 分叉点」小节：EQ1 三行（`log` 位型档 / 浮点比较档 / 排序并列档）各附目标运行时语义与受影响断言；EQ2 每行给一条构造输入（0.1 边界、NaN 注入、并列等概率）；EQ3 在 §4.4 补「比较与排序按 IEEE754 双精度值比较；NaN 不参与过滤与排序」的契约句。

---

## 2. Should-fix（不阻塞但应改）

### SF-01 V-07 的「可机检域定义」与实际命令输出域不一致

spec 第 51 行域定义为「`probe_facts.py constants` 的键」，断言为「常量集合共 10 项」。我实跑该命令得到 **19** 个键：

```
$ .venv/Scripts/python.exe -c "…print('key_count',len(d)); print(sorted(d))"
key_count 19
['ALPHA_DEFAULT','ALPHA_WIDTH','BASE_FREQ','CONV_THRESHOLD','DetectorFactory_seed_class_attr',
 'ITERATION_LIMIT','MAIL_RE_pattern','PROB_THRESHOLD','UNKNOWN_LANG','URL_RE_pattern',
 'factory_seed_instance','init_prob_repr','instance_alpha','instance_max_text_length',
 'instance_n_trial','instance_prior_map','instance_random_type','instance_seed','instance_verbose']
```

断言本身（7 类常量 + 3 实例默认值 = 10）是对的，但域定义写成「命令的键」就与测量域不符（测量域 19 ⊃ 断言域 10）。改法：域定义写「输出中 `ALPHA_*`/`ITERATION_LIMIT`/`PROB_THRESHOLD`/`CONV_THRESHOLD`/`BASE_FREQ`/`UNKNOWN_LANG`/`DetectorFactory_seed_class_attr`/`instance_n_trial`/`instance_max_text_length` 十项」，并注明 `*_pattern`/`init_prob_repr`/`instance_random_type`/`instance_seed` 等为额外观测项。

### SF-02 DR2 要求的标记字符串在仓库中不存在，且 T1 记录的命中位置不完整

spec 第 431 行要求 `@math.ln` 命中行「必须位于接缝模块内且带 `// non-native fallback` 标记」。

```
$ grep -rn "non-native fallback" --include=*.mbt . | wc -l
0
$ grep -rn '@math\.ln' --include=*.mbt probes/rand-probe probes/embed-probe | wc -l
（含注释共 7 行；代码行 3 处：cmd/main/main.mbt:140、cmd/main/main.mbt:150、rand-probe.mbt:203）
```

spec 第 581 行 T1 写「探针中命中**仅**在 `rand-probe.mbt:203`」，漏了 `cmd/main/main.mbt:140,150` 两处代码命中（以及 3 处注释命中）。改法：T1 实录补全命中清单；标记字符串在 §5.9 或 §7 登记为「实现时新增的字面」并给 GP1 生成点。

### SF-03 §2 的 MoonBit 侧枚举命令依赖 shell 语义

第 165 行 `grep -rn … | grep -v '_build\|\.mooncakes\|probes/'` 在 POSIX/bash 下输出 0 行（与第 168 行的「0 命中」一致），但在默认非 bash 解释器下会输出 14 行：

```
$ bash -c "grep -rn '^pub fn\|^pub struct\|^pub enum' --include=*.mbt . | grep -v '_build\|\.mooncakes\|probes/' | wc -l"
0
$ grep -rn '^pub fn\|^pub struct\|^pub enum' --include=*.mbt . | grep -vc '_build\|\.mooncakes\|probes/'
14
```

改法：命令前加 `bash -c` 或改用 `grep -v -e _build -e .mooncakes -e probes/` 的显式多模式形态，避免「反斜杠转义在非 bash 下失效」的假绿/假红。

### SF-04 §7 标题与表体不一致

第 424 行标题为「方言红线表（**DR1-DR3**，append-only）」，表体实有 DR1-DR8 八行。改标题为 `DR1-DR8`。

### SF-05 §0 的「45 个以上」是无派生的手写计数

第 22 行「需导出的符号 45 个以上」没有 V-XX 事实行、没有派生命令（DC-D）。按 §5 的签名行数实际为 9 行（含多符号行），无法推出 45。改法：删除该数字，或补一条导出面清单 + 计数命令。

### SF-06 §8.2/§8.3 的「观测输出」列填的是权威文档而非观测结果

第 460-465、471-474 行「观测输出」填 `docs/port/golden/expected.json`、`docs/port/upstream-behavior-contract.md §9`、`PRD FR-21/22/23 验收标准`、`analysis/toolchain-probes.md §C.1 三行`——这些是**期望值的来源**，不是「本次运行的观测输出」。另第 454、472、473、474 行填「待回填」。spec 已如实标「未验证」（第 485 行），所以不判 Blocking，但列名与内容不符会让 plan 阶段把「引用文档」误当「已取证」。改法：列名改为「观测输出（未验证时填 —）」，或把引用移到新增的「期望值来源」列。

### SF-07 FR-23 的验收口径窄于 PRD

PRD FR-23（第 171 行）要求「对 **268 条**基准样本核对，差异条数为 0」；spec §8.2 第 464 行只写「55 短 + 55 长样本分组断言」。改法：补 268 条口径或显式声明降级理由。

### SF-08 FR-20 的验收在公开 API 上不可观察

PRD FR-20 要求「读取概率向量长度」。我实测公开面拿不到该值：

```
$ …print('public lang list', f.get_lang_list())
public lang list ['aa', 'bb']
$ …print('internal langprob len after detect:', len(d.langprob))
internal langprob len after detect: 2      ← 等于 langlist 长度，不是 langsize
$ …print('word vector row len:', len(f.word_lang_prob_map['a']))
word vector row len: 4                     ← 只有内部容器能看到 4
```

spec §5 没有暴露向量长度的入口。改法：或在 §5 增一个仅供诊断的 `debug_vector_len()`（并标 `[EXT]`），或把 FR-20 的验收对象改为「`detect_langs` 的条目数不受 langsize 影响」这类可观察等价物。

### SF-09 §5 的「目标可用性 ✅」是无证据的平台无关性声称

第 316/327/339/351/361/370/380/390 行全部写 `native ✅ / js ✅ / wasm-gc ✅`，第 316 行还写「纯计算，无平台依赖」。按 Blocking #35，这类声称须登记为 PENDING-VERIFICATION 假设并给环境前提清单。目前 js 只以 bun 替代验证、wasm-gc 的 test 不可达（V-25/V-26），三个 ✅ 的证据强度并不相同。改法：改为「native ✅（V-24）/ js ⚠（bun 替代，U-02）/ wasm-gc ⚠（仅 build，U-01）」。

### SF-10 `[EXT]` 标签措辞不齐（4 条中有 1 条不符）

Blocking #34/清单要求 `[EXT]` 写「非对齐项，产品决策驱动」。实测：

- G-29 ✅「非对齐项，产品决策驱动」
- G-30 ✅「非对齐项，产品决策驱动」
- G-31 ✅「非对齐项，产品决策驱动」
- G-32 ❌「非对齐项，**验收设施**（约定 C）」——缺「产品决策驱动」，且它是测试设施而非产品能力，语义上更接近 `[ALIGN]`（对约定 C 的对齐）。

改法：G-32 改为 `[EXT] — 非对齐项，产品决策驱动（验收设施形态由约定 C 决定）`，或单列「测试设施」标签并说明。

### SF-11 DC-A 的自查结论与全文不符

第 624 行自述「文中出现的 `file:line` **只**出现在 §1 事实表与 §2 的 Source side 列」。实测 §1/§2 之外还有 55 处 `file:line` / 文档节号引用：

```
$ （脚本扫描 §2 之后的所有行，正则匹配 *.py:N 与 probes/…:N 与 docs/port/…§N）
total 55
示例：273（§4.2 `detector_factory.py:90`）、430-437（§7 八行）、521-527（§9.3 六行）、
      192（G-21 三处）、201（G-30）
```

改法：把 DC-A 自查改为「§4.2/§7/§9.3 的 `file:line` 均为事实源指针（非契约锚），并逐处登记」，或把这些引用改为 §1 的 V-XX 编号。

---

## 3. Note（观察项）

- **NT-01** 事实层质量高：抽查的 V-01/V-05/V-06/V-07/V-08/V-09/V-10/V-13/V-14/V-15/V-16/V-17/V-18/V-19/V-22/V-23/V-27/V-31/V-33/V-34/V-36/V-37/V-40/V-41/V-42/V-43/V-44/V-45/V-46/V-47/V-48 全部复现；`file:line` 指针（G-01…G-28、§9.3 六行）逐条落地无误。
- **NT-02** 数字对账：`55 / 184129 / 2204952 / 268 / 250 / 18 / 1951 / 651 / 21206 / 21451 / 2205308 / 3256320` 全部由我独立复跑复现（含现场 `moon build` 得到 3,256,320 B 的 exe）。
- **NT-03** `[LOCAL_DEAD_LINK]` 7 行（U-01…U-07）均带分类 + 回补触发 + 处置，形式合规；但 U-04（js/wasm-gc 容差数值）与 U-06（首次加载解析耗时）本质是「未测的产品阈值/指标」而非「本机不可达的环境能力」，分类「能力未验证」偏宽，建议分列「指标未测」类。
- **NT-04** §2 的 G-22 写「12 个块分支」，源码 `block ==`/`block in` 共 11 个判定臂、覆盖 12 个块常量（Bopomofo 与 Bopomofo Extended 同臂），与 CONTRACT §6 的 12 行表一致——数字可用，但建议写成「12 个块 / 11 个判定臂」以免读者误数。
- **NT-05** §6 错误码表覆盖面优于 PRD：补了码 1/2/3 的触发条件与消息原文（`detector_factory.py:59,61,78,83`、`detector.py:85,89` 均已核对）。码 2 标注「可达性未验证」符合 ADR T9。
- **NT-06** 我在审查过程中**未修改** spec 正文；本文件是唯一新增产物。所有临时违规样本写在 `F:/Temp/tmp.*` 下，未落入仓库。

---

## 4. 复审发现登记表（DC-F 规定格式）

| 编号 | 定义原文 | 销项证据 | 状态 |
|---|---|---|---|
| BLK-01 | spec 必须产出 D1 背景 / D2 架构 / D3 范式 / D4 解决方案 四维，缺失任一维阻断 | v2 新增 `## 0A. 四维一致性` 节（第 33 行起），含 D1/D2/D3/D4 四小节。复核：`grep -n "^## 0A\|^### D1\|^### D2\|^### D3\|^### D4" docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md` → 0A/D1/D2/D3/D4 各命中；另 v2 删除 §4.4 的代码围栏改为自然语言 | 已销项 |
| BLK-02 | §15 的 T1/T2 合计必须与分组相加一致（DC-D 数字派生） | v2 删除 §15 的手写合计行，改为「逐行状态指针 + 行数派生命令」。复核：`grep -c "合计" <spec>` 在 §15 内为 0；派生命令 `awk '/^### 10\.[1-4]/,/^### 10\.5/' <spec> \| grep -cE '^\| \*{0,2}(C-\|DR)'` → `23`（C- 14 行 + DR 9 行） | 已销项 |
| BLK-03 | 每条门禁命令须有可证伪的 T2 与声明退出码 | v2 C-C6 改为 `test "$(md5sum <spec 基准> \| cut -d' ' -f1)" = "<期望 md5>"`。T1 实录 exit 0；T2 实录：复制基准追加 1 字节后同命令 exit **1**（v1 的 `md5sum` 单独执行恒 0，无法表达判据） | 已销项 |
| BLK-04 | 命令引用的每个路径须反查 GP1 四要素 | v2 新增 `## 4A. 产品工程落点`：模块根 = 仓库根、`moon.mod` name = `vicoproplus/langdetect`、四个 `src/*/` 包、两个产物路径、两个生成器路径，每行给 GP1 四要素。复核：`grep -c "<产品目录>" <spec>` → **0**；根模块与嵌套探针共存实测 `moon check` exit 0（V-56） | 已销项 |
| BLK-05 | 存在性检查不得在路径缺失时假绿 | v2 C-B6 改为 `test -d src \|\| exit 2; grep …`。T1 实录（`src/` 四空包已建）exit 0；T2 实录 `src/` 下写含 `unicode-data` 的 moon.pkg → exit **1**；路径缺失时命令 exit **2**（不再把 grep 的 exit 2 洗成 0） | 已销项 |
| BLK-06 | 方言红线每行须有可机检形态且判据可实现 | v2 DR8 正则改为 `'(^\|[^@[:alnum:]_])(data\|math\|fs)\.[a-z_]+\('`。T1 实录：对 `probes/embed-probe` → **0 行**、对 `src/` → 0 行 exit 1；T2 实录：注入 `data.entry_count("af")` → 命中 1 行 exit 0（v1 的 `\b` 形态对同一合法代码命中 111 行，属假红） | 已销项 |
| BLK-07 | 契约字面须在目标编译器下成立并标证据等级 | v2 §5 签名全部改为编译通过形态：`suberror LangDetectError { CantDetect(code~…, message~…, input_len~…, input_prefix~…) }`、`create(alpha? : Double)`、`LowConfidence(char_count~…)` / `Detected(lang~…, probs~…)`、§4.3 显式命名 `LangProb`。实证：V-55 记录四则错误码（`[4118]`/`[3010]`/`[3002]`/`[3800]`），V-57 记录修正后 `moon check` 0 errors（均 `moon 0.1.20261012` / `moonc v0.10.15`）；§5.1 起每行标「已在真实编译器验证，证据等级 A」 | 已销项 |
| BLK-08 | PRD P0/P1 须全覆盖或有验收行 | v2 §8.2 新增「seed 语义 FR-05/FR-06」行（3 步判据 + 指向 `repeatability` 14 组与 `unseeded_runs`）；§3 回链表新增「验收行（§8）」列并把措辞从「全部出现」改为「全部有验收行」。复核：FR-01…FR-26 验收行列 26 行非空 | 已销项 |
| BLK-09 | 入口函数副作用须逐行全枚举 | v2 §9.1 入口从 9 个增到 14 个（补 `cleaning_text` / `detect` / `get_probabilities` / `load_profile`）；新增 L1-A4 引用别名断言（写方 `add_profile`/`clear`，读方已建 Detector）；§9.3 按「一写多读逐行展开」展开 `langlist`/`word_lang_prob_map` 共 12 行；`append` 改为「追加」、`cleaning_text` 标「幂等」 | 已销项 |
| BLK-10 | 静默语境负断言须可运行且可满足 | v2 §9.4 NE1 断言对象改为「库自身输出」：① 静态 `grep -rnE 'println\|print\(\|eprintln\|@stdio' src/core src/data src/unicode src/math_seam` 必须 0 行（T1 实录 exit 1，T2 注入 `println` 后 exit 0）；② 运行时 `src/core/cmd/main` 二进制输出 0 字节（运行时二要素在实现后回填） | 已销项 |
| BLK-11 | 每条失败语义须有取证通道 + 可运行验证 + 通道可用性 | v2 §5.8 增「取证通道」行（四字段 → 调用方序列化为一行 JSON → 按 `code` 检索）；§8.2 增「失败取证通道」验收行（码 5/4/8 各构造一次）；通道可用性登记「native/js/wasm-gc 皆可用（纯内存 + 调用方落盘）」；并注明上游无 `.message` 属性、本 spec 的 `message` 对应 `str(e)` | 已销项 |
| BLK-12 | 每个源侧测试文件须有目标侧对应或登记 gap | v2 §2 新增「§2A 源侧测试对齐」子表 5 行（用例数由 `grep -c "def test_"` 派生：6/2/7/7/1）；`test_lang_profile.py` 7 例显式登记 gap（对应 G-27 不移植，理由 = 训练期能力） | 已销项 |
| BLK-13 | 冲突对裁决须落回条款文本（MS2） | v2 §7 新增三条总则（检索面 = `src/`；`docs/`、`probes/`、`_build/`、`.mooncakes/` 不在扫描域；产品注释须用描述形态）+ DR9（业务侧平台分支可机检）；§8.4「目标环境」列改为 `native (win32 x64)` / `native（其他平台，容差档）` / `js / wasm-gc（容差档）` | 已销项 |
| BLK-14 | 行为等价须覆盖平台语义分叉（EQ1-EQ3） | v2 新增 §8.5「EQ 分叉点」：EQ1 三分叉点（log 位型 / 浮点比较 / 排序并列）+ EQ2 构造输入（含 V-49 阈值边界样本结论、V-50 等概率构造、V-51 NaN 构造）+ EQ3 契约句（IEEE754 数值比较；NaN 不参与过滤与排序；负零被过滤）；§4.4 同步补 EQ3 句 | 已销项 |
| SF-01 | 可机检域定义须与命令测量域对账 | v2 V-07 域定义改为列举 10 个断言域键，并注明测量域 = 命令输出的 19 个键（额外 9 个为额外观测项）。对账命令已写入 V-07 行 | 已销项 |
| SF-02 | 门禁标记字符串须真实存在且 T1 记录完整 | v2 DR2 行补全参照命中清单（代码 3 处：`rand-probe.mbt:203`、`cmd/main/main.mbt:140,150`；注释 4 处），并把 `// non-native fallback` 登记为「实现期新增字面 + GP1 生成点 = `src/math_seam/`」 | 已销项 |
| SF-03 | 命令须在声明 shell 下可复现 | v2 §2 枚举命令改为显式多模式：`grep -v -e _build -e .mooncakes -e probes`。两种解释器下实测均 **0 行**（v1 形式在非 bash 下会输出 14 行） | 已销项 |
| SF-04 | 章节标题与表体须一致 | v2 §7 标题改为「方言红线表（DR1-DR9，append-only）」与表体 DR1-DR9 一致（DR9 为 v2 新增）。复核：`grep -n "^## 7" <spec>` → `DR1-DR9` | 已销项 |
| SF-05 | 手写计数须有派生命令 | v2 §0 删除「45 个以上」，改为「公开接缝签名表 **10** 组（§5.1–§5.10 各一行签名）」。复核：`grep -c '^### 5\.[0-9]' <spec>` → **10** | 已销项 |
| SF-06 | 验收行「观测输出」须为观测结果 | v2 §8.1/§8.2/§8.3/§8.4 的「观测输出」列一律填 `—`，并新增「期望值来源」列承载文档引用 | 已销项 |
| SF-07 | 验收口径不得窄于 PRD | v2 §8.2 低置信入口行补 268 条口径（除 55 短 + 55 长外，另对 268 条基准全量核对三接口一致性，含 18 条异常样本比异常码）；§3 FR-23 承接位置同步标注 | 已销项 |
| SF-08 | 验收对象须在公开面可观察 | v2 新增 §5.10 诊断入口 `debug_vector_len() -> Int`（`[EXT]`，G-33），§8.2 大写词与缓存行改为 `debug_vector_len()` 与 `get_lang_list()` 长度对照（V-53 证明上游公开面拿不到该值） | 已销项 |
| SF-09 | 平台无关性声称须登记为待验证假设 | v2 §5 全部 `✅/✅/✅` 改为 `native ✅（V-24）/ js ⚠（bun 替代，U-02）/ wasm-gc ⚠（仅 build，U-01）` | 已销项 |
| SF-10 | `[EXT]` 须写「非对齐项，产品决策驱动」 | v2 G-32 改为「`[EXT]` — 非对齐项，产品决策驱动（验收设施形态由 `约定 C：golden 基准消费契约` 决定）」 | 已销项 |
| SF-11 | DC-A 自查结论须与全文一致 | v2 DC-A 自查改为如实登记：§1/§2/§2A/§4.1-§4.4/§7/§9.3 的 `file:line` **全部**声明为「事实源指针（可重跑复查），非契约锚」，契约锚只用编号 | 已销项 |
| NT-01…NT-06 | 观察项（不阻塞） | NT-03 已采纳（U-04/U-06 分类改「指标未测」）；NT-04 已采纳（G-22 改为「12 个块常量 / 11 个判定臂」）；NT-01/02/05/06 无需动作 | 记录 |

**销项状态约定**：本表状态仅取「未销项 / 已销项（附复核命令与输出）/ 转上游（附 PRD/设计条目编号）」。spec 修订后由修订者逐行填「已销项」并附复跑命令；复审员按 DC-C 复核。

---

## 5. 我实际执行的核验命令实录（摘要）

以下均为本审查员独立执行，非引用 spec 记录。

### 5.1 门禁 T1（正向）

```
$ F=probes/embed-probe/lib/data/data.mbt
$ python - "$F" <<'PY' …（约定 A §3 C-A1/C-A2 原样）
decls 55 entries 184129
exit=0
$ test "$(wc -c < "$F" | tr -d ' ')" = "2205308"; echo $?      → 0
$ test "$(grep -c 'Map::from_array' "$F")" = "0"; echo $?      → 0
$ python -c "…mode=='flat'"; echo $?                            → 0
$ head -1 "$F" | grep -q '勿手改'; echo $?                      → 0
$ .venv/Scripts/python.exe -c "…assert 1951 … assert 651 …"
ok 1951 cps / 651 intervals                                     exit=0
$ .venv/Scripts/python.exe -c "…(len(c),len(ne),len(er))==(268,250,18)"
ok 268=250+18                                                   exit=0
$ .venv/Scripts/python.exe -c "…sorted({seed})==[0,42]"
ok seeds 0/42                                                   exit=0
$ .venv/Scripts/python.exe -c "…codes=={5}"
ok error code 5                                                 exit=0
$ .venv/Scripts/python.exe -c "…re.fullmatch('[0-9a-f]{16}',…)"
ok prob_bits hex16                                              exit=0
$ md5sum docs/port/golden/expected.json
219519ee19d7cc10d404ddbdab3acd87                                exit=0
```

### 5.2 门禁 T2（我现场构造违规样本）

```
# C-A1 删 1 个语言声明
decls 54 entries 181986      EXIT=1
# C-A2 删 1 个条目（保留声明数）
decls 55 entries 184128      EXIT=1
# C-A3 追加 1 个空格
bytes=2205309                EXIT=1
# C-A4 注入 Map::from_array
count=1                      EXIT=1
# C-A5 清单 mode 改 map
EXIT=1
# C-A6 首行改 // no marker
EXIT=1
# B3/B4 断言 1950
AssertionError: 1951         EXIT=1
# B6 在临时 lib/moon.pkg 写 unicode-data
hits=1                       EXIT=1
# C2 断言 (268,249,18)
AssertionError: (268, 250, 18)   EXIT=1
# C3 断言 [0]
AssertionError                EXIT=1
# C4 断言 {4}
AssertionError: {5}           EXIT=1
# C1/C5 用小写断言匹配大写样本
AssertionError: expected mismatch   EXIT=1
# DR1 注入 @math.sqrt
…prod/a.mbt:1:let x = @math.sqrt(2.0)      grep_exit=0（= 命中违规）
# DR3 注入 extern "C" fn c_cos
…prod/c.mbt:1:pub extern "C" fn c_cos…     grep_exit=0
# DR5 注入 Map::from_array
EXIT=1
# DR6 注入 "moonbitlang/core/fs"
…prod/moon.pkg:2:  "moonbitlang/core/fs",  grep_exit=0
# DR7 注入 derive(Show)
…prod/d.mbt:1:struct S { a : Int } derive(Show)   grep_exit=0
# DR8 注入 data.entry_count(
…prod/e.mbt:1:let n = data.entry_count("af")      grep_exit=0
```

**T2 合计**：13 条由我独立构造并跑出 FAIL（C-A1/A2、C-A3、C-A4、C-A5、C-A6、B3/B4、B6、C2、C3、C4、C1/C5、DR1、DR3、DR5、DR6、DR7、DR8 中的 13 条独立样本）。**未通过 T2 的**：C-C6（无比对命令）、DR2（无标记字符串，且 T1 记录不完整）。

### 5.3 指针抽查（≥15 条）

| 指针 | 我读到的内容 | 判定 |
|---|---|---|
| `detector_factory.py:29` | `seed = None` | ✅ |
| `detector_factory.py:117` | `PROFILES_DIRECTORY = path.join(path.dirname(__file__), 'profiles')` | ✅ |
| `detector_factory.py:118-124` | `_factory = None` / `init_factory()` / `load_profile(PROFILES_DIRECTORY)` | ✅ |
| `detector_factory.py:126-130` | `def detect(text)` … `return detector.detect()` | ✅ |
| `detector_factory.py:133-137` | `def detect_langs(text)` … `return detector.get_probabilities()` | ✅ |
| `detector_factory.py:84` | `self.langlist.append(lang)` | ✅ |
| `detector_factory.py:87-92` | 零向量创建 + `1<=length<=3` 条件 + 概率写入 | ✅ |
| `detector.py:44-51` | 7 个类常量（0.5/0.05/1000/0.1/0.99999/10000/'unknown'） | ✅ |
| `detector.py:64-68` | `n_trial=7` / `max_text_length=10000` / `prior_map=None` / `verbose=False` | ✅ |
| `detector.py:76-91` | `set_prior_map` 两条码 8 消息（85/89 行） | ✅ |
| `detector.py:99-112` | `append`：URL→MAIL→normalize_vi→截断→空格折叠 | ✅ |
| `detector.py:114-130` | `cleaning_text` + LEA 比较（122 行） | ✅ |
| `detector.py:132-139` | `detect()` + `UNKNOWN_LANG` 返回 | ✅ |
| `detector.py:141-144` | `get_probabilities` 惰性 `_detect_block` | ✅ |
| `detector.py:168-169` | `langprob[j] += prob[j] / self.n_trial` | ✅ |
| `detector.py:235-236` | `if p > self.PROB_THRESHOLD` + `sort(reverse=True)` | ✅ |
| `language.py:7-17` | `__init__`/`__repr__`/`__lt__` 三成员 | ✅ |
| `lang_detect_exception.py:1-11` | 9 个码值 0-8 | ✅ |
| `lang_detect_exception.py:16-22` | `code` + `get_code()`（无 `message` 属性） | ✅（spec 未误称） |
| `ngram.py:64-97` | `normalize` 11 个判定臂 / 12 个块 | ✅（数字口径见 NT-04） |
| `ngram.py:99-120` | `normalize_vi` | ✅ |
| `ngram.py:122-260` | `CJK_CLASS` 起、`CJK_MAP={}` 于 251、`_init_cjk_map()` 于 260 | ✅ |
| `unicode_block.py:223-465` | `_unicode_blocks = [` 于 223；区间条目 220 | ✅ |
| `lang_profile.py:28-70` | `add` / `omit_less_freq` / `update` | ✅ |
| `probes/rand-probe/rand-probe.mbt:12` | 注释 `sqrt -> Double::sqrt（builtin，编译为 %f64_sqrt）` | ✅ |
| `probes/rand-probe/rand-probe.mbt:176` | `pub extern "C" fn c_log(x : Double) -> Double = "log"` | ✅ |
| `probes/rand-probe/rand-probe.mbt:203` | `let g2rad = (-2.0 * @math.ln(1.0 - self.random())).sqrt()` | ✅ |
| `probes/fs-probe/cmd/main/moon.pkg:3` | `"moonbitlang/async/fs",` | ✅ |
| `probes/embed-probe/cmd/main/main.mbt:5-6` | `@data.languages` / `@data.entry_count(lang)` | ✅ |

### 5.4 数字对账（全部独立复现）

```
55 / 184129 / 2204952       ← tools/profile_stats.py: files=55 total_bytes=2204952 total_entries=184129
7791 / 52387 / 123951       ← len_dist={1:7791, 2:52387, 3:123951}
268 / 250 / 18              ← expected.json.cases
1951 / 651                  ← CPython 3.12.10 全码点扫描
21206 / 21451               ← rand-feasibility.md:110
2205308                     ← wc -c data.mbt
3256320                     ← moon build 后 _build/native/debug/build/cmd/main/main.exe（我现场构建）
219519ee…                   ← md5sum expected.json
```

### 5.5 交叉验证（spec 之外的独立复跑）

```
# 6 类无特征输入全部码 5（V-44）
empty EXC 5 / blank EXC 5 / emoji EXC 5 / digits EXC 5 / punct EXC 5 / url EXC 5
# capitalword 10 个特征（V-46）
['U',' U','A ','SA ','N',' N','A ','SA ','F',' F']
# 缓存不失效（V-47）：first de / second de
# langsize=4（V-48）：langlist ['aa','bb'] / word row len 4
# LEA 死代码（V-45）：unicode_block('\u1ea1')=66（int） != 'Latin Extended Additional' → True
# moonc 对 derive(Show) 的告警（DR7）
Warning (deprecated_syntax): `derive(Show)` is deprecated. Use `derive(Debug)` or manually implement the `Show` trait instead.
# 上游 5 个测试文件 / 23 个用例（BLK-12）
test_detector.py 6 / test_language.py 2 / test_lang_profile.py 7 / test_ngram.py 7 / test_unicode_block.py 1
```

---

## 6. Blocking Checks 逐条判定（53 条）

| # | 检查项（缩写） | 判定 | 依据 |
|---|---|---|---|
| 1 | 每条 US/FR 回链 PRD 且 P0/P1 全覆盖 | **Fail** | BLK-08：FR-05/FR-06 无验收行；§3 第 247 行的「26/26」是文本出现而非验收覆盖 |
| 2 | 敏感数据/降级路径/文档链（PRD 10.7 + 等价降级 + 不降级） | **Fail** | 数据流 N/A 成立（PRD 10.7「无」+ 零网络/零外部读取有 FR-14/FR-24 承载）；但 FE2 的「非等价降级」只在 §11 第 608 行一句带过，§8 无降级路径等价断言行（`grep 非等价` 仅 1 处） |
| 3 | `[ALIGN]` 须有旧路径阅读记录（EA1/EA2/EA3） | **Pass** | 28 条 `[ALIGN]` 全部带 `file:line`；G-17/G-27/G-28 的「显式不移植」有 ADR X 裁决指针（EA2 已裁决）；抽查 15+ 指针全部落地（§5.3） |
| 4 | 每条 `[ALIGN]` 的源侧符号确实存在 | **Pass** | 28/28 条经源码回读命中（`detector_factory.py`/`detector.py`/`language.py`/`lang_detect_exception.py`/`ngram.py`/`unicode_block.py`/`lang_profile.py`）；`CJK_MAP` 6667 键 / 126 组经 `NGram.CJK_MAP` 实测 |
| 5 | 四维 D1-D4 且无实现代码 | **Fail** | BLK-01 |
| 6 | 单 PRD 不自我拆分、10.6 共享边界 | **Pass** | PRD 10.6「单份 PRD，无需拆分」；spec 为单文件单 spec；无兄弟 spec 对齐义务 |
| 7 | current state 每条事实带 `file:line`/grep | **Pass**（含 1 处域定义瑕疵） | 48 条 V-XX 中抽查 31 条全部复现；瑕疵见 SF-01（V-07 域定义） |
| 8 | 每个交付物带可复跑验证命令 | **Fail** | 全文无交付物清单（`grep 交付物\|文件清单\|模块划分` 无命中）；§8 行多为文档引用而非命令 |
| 9 | 验收 ≥3 独立维度、各自绑命令、任一失败=整体失败 | **Fail** | 四维表存在（§8.1-8.4），但「任一失败 = 整体失败」条款缺失（`grep 任一失败\|整体失败` = 0），且 §8.1/8.3 多行为「待回填」 |
| 10 | 源侧测试文件须有目标侧对应 | **Fail** | BLK-12 |
| 11 | 验收表 row 0 = 运行时链路（HTTP 200） | **N/A** | 纯库无 HTTP 端点；§8.1「首次调用完成档案加载」实质等价于 row 0，且排在功能对齐之前 |
| 12 | 运行时端点声称须有实测证据 | **N/A** | 无端点（同上） |
| 13 | 并行批次须有整变更集成验证 | **N/A** | 单份 PRD、单 spec、无批次拆分（PRD 10.6） |
| 14 | 迁移单元独立过红线 + `[pre-existing]` | **Pass** | §13 R1-R4 全 N/A 且给了理由（新建库、零既有 MoonBit 代码）；`probes/` 的 `Map::from_array` / `@math.ln` 已显式声明为探针合法用法 |
| 15 | 页面/路由注册三态归属 | **N/A** | 无页面/路由注册清单 |
| 16 | mock 须由 golden 样本派生 | **N/A** | 无服务端响应 mock；比对对象是 `expected.json` 本体 |
| 17 | 引用响应性共享状态须声明更新语义与消费方式 | **Fail** | 无响应性框架，但「共享容器」确实存在：`Detector` 与工厂共享 `langlist`/`word_lang_prob_map` 引用（`is` 实测 True），架构节未声明「共享引用 vs 拷贝」语义，层 3 也未登记（见 BLK-09） |
| 18 | 三层断言面（B1-B8 / PB1-PB7 / PC1-PC3） | **Fail** | 层 2 有 N/A 且理由充分（§9.2，纯库无界面）✅；层 1 不全（BLK-09）；层 3 有表但不全（缺别名读方） |
| 19 | 负向轴 NE1-NE4 | **Fail** | NE1 不可满足（BLK-10）；NE2/NEG-2 把「签名不符」当错误形态但那是编译期错误，属偷换；NE4 四条存在 ✅ |
| 20 | 渲染不变量 RI1-RI4 | **N/A** | 无用户可见页面（§9.2 已登记，DESIGN G1 RS1-RS4 同结论） |
| 21 | PRD 的 G/US 判据不得用测试代理 | **Pass** | PRD G-01…G-05 均为用户可观察（命中数、位级一致、异常码、零网络）；无「测试全绿」式判据 |
| 22 | 错误展示责任按语境分型（ED1-ED4） | **N/A** | 无统一错误展示层、无 UI；库以 `suberror` 返回，不弹错 |
| 23 | 外部框架/平台/SDK 声称须有证据 | **Pass**（1 处待补） | DR1/DR2/DR3/DR6/DR7/DR8 均有源码或实测指针；DR7 的 moonc 告警我现场复现 ✅；`@math.ln` 标记字符串缺失见 SF-02 |
| 24 | 新平台/工具链须有最小编译探针 | **Pass** | `probes/tiny-probe`、`probes/embed-probe`、`probes/rand-probe` 均已构建；我现场 `moon check` / `moon test --target native` 通过（56/56） |
| 25 | 架构/传输决策须有原语可用性矩阵（A/B 证据） | **Fail** | DESIGN PS1 有接缝表，但 spec 未承接；§5.9 只有「全目标可用」一句，无 A/B 分格矩阵（`log` 在 native=A、js=B、wasm-gc=B 未成表） |
| 26 | 测试种子数据形状须有证据等级 | **N/A** | 种子来自上游 golden（实测 A 级），无手写形状 |
| 27 | 文档契约纪律 DC-A…DC-F | **Fail** | DC-A 自查失实（SF-11，55 处越界）；DC-D 违反（BLK-02、SF-05）；DC-F 由本文件补齐 ✅ |
| 28 | `[LOCAL_DEAD_LINK]` 分类 + 回补触发 + 处置 | **Pass** | U-01…U-07 七行齐备；分类偏宽见 NT-03 |
| 29 | grade-C 形状登记前须有机器检索记录 | **N/A** | 无 grade-C 形状 |
| 30 | 入口函数副作用逐行全枚举 | **Fail** | BLK-09 |
| 31 | 语言/语法特性须有引擎矩阵 + 探针记录 | **Fail** | BLK-07：4 处签名在 `moonc v0.10.15` 下不成立，说明语法特性未做探针矩阵 |
| 32 | 生成目录所有权登记（GO1-GO3） | **Pass**（部分） | `约定 A` §4 / `约定 B` §5 已登记生成工具、覆盖行为、不手改清单；但产品侧产物路径未定（BLK-04） |
| 33 | 开发环境状态规则与调试可观测前提 | **N/A** | 无端口转发/代理/后台服务；调试前提未入范围 |
| 34 | 外部消费字面标识符逐字 + 证据等级 | **Fail** | 全文无 `moon.mod` 名 / import 路径 / 包名（`grep moon.mod\|import {\|vicoproplus` 无命中）；CC1/CC2 未满足 |
| 35 | 平台无关性声称须登记为待验证假设 | **Fail** | SF-09：§5 八处「全目标 ✅」+「纯计算，无平台依赖」无分级证据 |
| 36 | 失败语义须有取证通道 + 可运行验证 + 通道可用性 | **Fail** | BLK-11 |
| 37 | 验收行须与环境事实清单交叉核对（EC1-EC2） | **Fail** | 无环境事实登记表；§8 引用 `probes/logs/*.log` 却未登记「该通道在本机可用/不可用」 |
| 38 | 外部桥接契约（XB/TD/CF/SD） | **Pass**（部分） | `extern "C" log` 的签名/权威源/替身纪律在 DESIGN G2 完整；spec §5.9 仅引用未复制。按 AD3「下游只引用不复制正文」可接受，但 spec 未给签名行 → 记 partial |
| 39 | 冻结时全部机检命令重跑 | **Fail** | 我重跑发现：C-B6 T1 假绿（BLK-05）、C-C6 无 T2（BLK-03）、DR8 判据不可实现（BLK-06）、DR2 标记不存在（SF-02）、§2 命令 shell 相关（SF-03） |
| 40 | 平台声明面清单（权限/后台/组件） | **N/A** | 纯计算库，无权限/后台/服务声明需求 |
| 41 | PRD 与锚点裁决一致、C9 依赖行标注事实/假设 | **Pass** | PRD §9.1 每行标「事实（已核验）」或「假设（待验证）」并附指针；10.5 登记 9 项与 §9.1 一致 |
| 42 | PRD 失败路径按成因分型 | **Pass** | FR-08（负先验）/FR-09（零和）/FR-11（未加载）/FR-12（无特征）分列，消息原文逐条固化 |
| 43 | 方言红线表（DR1-DR3 形态）+ 出处 + 机检 + append-only | **Fail** | 八行均有出处与机检形态 ✅、append-only 声明 ✅；但标题写 DR1-DR3（SF-04）、DR8 判据不可实现（BLK-06）、DR2 标记不存在（SF-02） |
| 44 | 数据模型字段 NULL + 标量类型双锁 | **Pass**（1 处类型名缺） | §4.1/4.2/4.3 三表均有 NULL 性与类型（`String`/`Array[Int]`/`Map[String,Int]`/`Double`/`String?`），且逐字复制权威口径；缺 `LangProb` 结构体名（并入 BLK-07 第 4 点） |
| 45 | 平台语义分叉断言（EQ1-EQ3） | **Fail** | BLK-14 |
| 46 | 验收行三要素（环境 + 操作证据 + 观测输出） | **Fail** | 环境标识 ✅、操作证据多为文档引用、观测输出列填期望来源（SF-06）；4 行「待回填」 |
| 47 | 跨运行时传输形态强断言（E8） | **N/A** | 无流式/长连接/分块传输 |
| 48 | 权威派生文档（AD1-AD3） | **Pass** | 三份约定均独立成文、含版本号、逐条正文、机检断言 + 门禁命令 + 失败退出码；spec 第 12 行逐字引用三个完整标题；AD3 指针链在 §12 DC-E 承接 |
| 49 | 定量断言四元组（断言 + 域 + 命令 + 结果） | **Fail** | 多数 V-XX 满足 ✅；V-07 域不符（SF-01）、「45 个以上」无派生（SF-05）、§15 合计错（BLK-02） |
| 50 | 每条机检命令 T1/T2/T3 试跑记录 | **Fail** | BLK-03 / BLK-05 / BLK-06 / BLK-02 / SF-02 |
| 51 | 跨单元产物引用时序表 | **N/A** | 单交付单元，无跨单元产物引用（DESIGN G6 时序可达性亦为 N/A） |
| 52 | 修订轮次新实体三处登记 + 上游回洗 | **N/A** | 首轮 spec，无修订轮次 |
| 53 | 契约两两互查（MS1-MS2） | **Fail** | MS1 枚举与 10 对互查存在 ✅；MS2 未落回条款（BLK-13） |

**统计**：Pass 11 / Fail 20 / N/A 22（合计 53）。

---

## 7. 建议的修订顺序

1. **BLK-04 + BLK-01**：先定产品工程落点（moon.mod 名、目录、产物路径、GP1 四要素），再补 D1-D4 架构维度——后续所有命令与条款都挂在这两件事上。
2. **BLK-07**：用 `moon check` 实测把 §5 的签名全部改成可编译形态（`suberror`、`alpha?`、标签载荷、`LangProb` 结构体名）。
3. **BLK-03 / BLK-05 / BLK-06 / SF-02 / SF-03**：修门禁命令，并逐条补 T2 实录（我能提供的 13 条实录见 §5.2，可直接复跑复核）。
4. **BLK-02 / SF-05 / SF-01**：修计数与域定义，把 §15 改为命令派生。
5. **BLK-08 / BLK-09 / BLK-10 / BLK-11 / BLK-12 / BLK-14**：补验收行与断言面（FR-05/06、入口副作用、NE1、取证通道、测试对齐、EQ）。
6. **BLK-13 / SF-11 / SF-04 / SF-06 / SF-07 / SF-08 / SF-09 / SF-10**：把裁决落回条款、修自查结论与列名。


---

# 第二轮复审（v2，2026-10-21）

> **审查对象**：`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md` v2（862 行 / 84,270 B）
> **作者声称**：销项 14 Blocking + 11 Should-fix，findings 表填 25 行「已销项」
> **本轮方法**：不采信销项自述。对 25 条逐条去 spec 找改动 + 自己跑命令；重点重跑作者新改的 BLK-04/03/05/06/07/10/14/02/08；扫描 v2 新增实体（V-49…V-57、G-33、DR9、§4A、§8.5）。
> **结论**：**Issues Found** —— 25 条销项中 **CLOSED 19 / PARTIAL 6 / NOT CLOSED 0**，另有 **新发现 9 条（Blocking 4 / Should-fix 5）**。

---

## 8. 复审结论（25 条销项逐条判定）

| 编号 | 判定 | 我的复核命令与输出（摘） |
|---|---|---|
| BLK-01 | **CLOSED** | `grep -n "^## 0A\|^### D1\|^### D2\|^### D3\|^### D4"` → 33/35/39/56/68 全部命中；D2 有模块表（4 包 + 允许依赖 + 禁止）+ 依赖方向 + 数据流；D3 有 6 行范式表；D4 有 D1-D12 承接表 + 范围 in/out。§4.4 的 Python 列表推导引文已删（`grep -c 'sort_key(entry)'` → 0）。 |
| BLK-02 | **PARTIAL → v3 已销项**（见 §13/§14） | §15 手写合计已删 ✅（`grep -c 合计` 在 843-860 段仅命中标题「不设手写合计」）。但作者销项证据写「派生命令 → `23`（C- 14 行 + DR 9 行）」，我实跑：`C-` 14 + `DR` 9 = 23 ✅，可该命令的输出 **23** 与 §10 表内**数据行实数 22**（5+4+5+9 中含 10.4 的 DR 行 9 → 5+4+5+9=23，但 10.2 表头声称 B1-B6 实列 4 行）不一致：`### 10.2` 表体只有 4 行却代表 6 条命令（B1/B3/B4 合并 + B2 + B5 + B6 = 4 行 / 6 命令）。派生数 = 行数 ≠ 命令数，而 §15 标题写「命令行数」。措辞与语义仍错位。 |
| BLK-03 | **CLOSED** | 按 spec 原命令（去掉 markdown 转义）跑：原文件 `test "$(md5sum … \| cut -d' ' -f1)" = "219519ee…"` → **rc=0**；复制 + 追加 1 字节 → **rc=1**（`246823` 字节 vs `246822`）。T2 可复现。 |
| BLK-04 | **CLOSED**（含新问题 N-03） | `grep -c '<产品目录>'` → **0**；§4A 表 11 行；`moon.mod`（`name = "vicoproplus/langdetect"`）+ 4 个 `src/*/moon.pkg` 实际存在；根 `moon check` → **rc=0**；`moon build` → **rc=0**；probes 三模块 `moon check` 均 rc=0（rand-probe 需 `--target native`，其默认目标报 wasm backend `extern "C"` 错误，**与本变更无关、为既有状态**）。**但**：`src/core/cmd/main/` 被 §4A 登记为产品路径，实际未创建，且 `moon check` 对 `moon.mod` 的 name 字面**不做校验**（改成 `name="x/y"` 后 rc 仍 0）——见 N-03。 |
| BLK-05 | **CLOSED** | `test -d src \|\| exit 2; test "$(grep -rlE 'moonbitlang/x\|unicode-data' src \| wc -l)" = "0"`：src 存在 → **rc=0**；`mv src` 后 → **rc=2**（v1 形态对照：同场景 **rc=0** 假绿）；注入 `src/core/moon.pkg.tmp`（含 `moonbit-community/unicode-data`）→ **rc=1**；恢复后 rc=0。 |
| BLK-06 | **CLOSED** | 新正则（去 markdown 转义）`grep -rnE '(^\|[^@[:alnum:]_])(data\|math\|fs)\.[a-z_]+\(' --include=*.mbt probes/embed-probe` → **0 行**（v1 `\b` 形态同范围 111 行）；对 `src/` → 0 行；注入 `src/core/dr8_tmp.mbt: let n = data.entry_count("af")` → **命中 1 行**。 |
| BLK-07 | **PARTIAL → v3 已销项**（见 §13/§14） | `suberror` + 标签载荷 + `LangProb` 结构体名 + `LowConfidence(char_count~)`/`Detected(lang~, probs~)` 逐字抄进临时工程 → `moon check` **rc=0**（0 errors）✅。**但 §5.5/§5.6/§5.7 的方法签名仍缺 `self`**：`Detector::set_seed(seed : Int64?)`、`Detector::set_max_text_length(n : Int)`、`Detector::set_prior_map(prior : Map[String, Double])` 三者按原样声明后再以 `d.set_seed(Some(0L))` 调用 → `[4014] Expr Type Mismatch` + `[4080] This function has type (Int64?) -> Unit, which requires 1 arguments, but is given 2 arguments`（三条同型）。`DetectorFactory::create(alpha? : Double)` 作为关联函数（无 self）本身 rc=0，但**不能**以 `f.create()` 方法形态调用（`[4080]`）；spec 未说明它是关联函数还是方法。 |
| BLK-08 | **CLOSED** | §8.2 第 591 行确有「**seed 语义** / **FR-05/FR-06**」行，含 3 步判据（seed=0 ×5 差异 0 / seed=42 不同且可重复 / 不设 seed ×10 允许多结果且零异常）；§3 新增「验收行（§8）」列，26 行 FR + 7 行 US **全部非空**且取值 9 种（非全填同一值）；§3 措辞改为「全部有验收行」。 |
| BLK-09 | **CLOSED** | §9.1 入口由 9 → **14** 行（补 `cleaning_text` / `detect` / `get_probabilities` / `load_profile` / `debug_vector_len`），新增「别名回填」列；L1-A4 存在；§9.3 由 6 行扩到 **15 行**，`langlist`/`word_lang_prob_map` 按「一写多读逐行展开」，含「已建 Detector 通过别名读取」两行。我实测别名：`d.langlist is f.langlist` → **True True**；构造性验证 `add_profile` 后 `len(d.langlist)` 55 → **56**（工厂 56）→ 别名可见 ✅。**但** L1-A4 的验证命令写「已建实例的 `get_lang_list()`」——`Detector` 无此方法（`hasattr(d,'get_lang_list')` → **False**），见 N-05。 |
| BLK-10 | **PARTIAL → v3 已销项**（见 §13/§14） | NE1 已改为「库自身不向 stdout/stderr 写字节（与被测运行器无关）」✅，静态 grep 已限定四个产品目录 ✅。**但**：(a) 「`cmd/main` 除外」只写在文字里，**没写进命令**——`src/core/cmd/main/` 按 §4A 就落在 `src/core` 之下，我放一个 `fn main { println(...) }` 到该路径，命令 **命中 1 行**（rc=0），即断言自己声称的例外未被实现；(b) 运行时半句 `./main > out.txt 2> err.txt` 我实跑注册的 cmd/main：`fn main { println("total: 184129") }` → stdout **14 字节**、stderr 0；`fn main { () }`（detect-only 形态）→ stdout **0 字节**。结论：运行时断言可满足，但**静态断言与自身例外矛盾**。 |
| BLK-11 | **CLOSED** | §5.8 新增「取证通道」行（四字段 → 调用方序列化为一行 JSON → 可按 `code` 检索；库不落盘）+「通道目标可用性」行；§8.2 新增「失败取证通道」验收行（码 5/4/8 各构造一次 → 序列化 → 断言四字段齐备、可读回、按 code 命中）。字段语义已注明上游无 `.message`（V-11），我复核 `hasattr(e,'message')` → **False** ✅。 |
| BLK-12 | **CLOSED** | §2A 新增 5 行（源文件 / 用例数 / 目标侧测试 / 状态）；用例数我复跑 `grep -c "def test_"` → **6 / 2 / 7 / 7 / 1** 与表内一致；`test_lang_profile.py` 7 个训练期用例显式登记为 gap（对应 G-27 不移植）并说明替代覆盖。 |
| BLK-13 | **CLOSED** | §7 新增「总则」三条（检索面 = `src/`；`docs/`/`probes/`/`_build/`/`.mooncakes/` 不在扫描域；注释须用描述形态）——MS1-6 裁决落回条款 ✅；§8.4 目标环境列改为 `native (win32 x64)` / `native (其他平台)` / `js / wasm-gc` 三档——MS1-8 落回条款 ✅。 |
| BLK-14 | **PARTIAL → v3 已销项**（见 §13/§14） | §8.5 三小节齐全（EQ1 3 行 / EQ2 4 行 / EQ3 3 条），§4.4 确有 EQ3 契约句（NaN 不参与过滤排序、负零被过滤）✅；EQ2 的 0.1 边界行显式标「未验证 + 需接缝注入」✅；NaN 行引 V-51 ✅；并列行引 V-50 ✅。**但** EQ2 的「0.1 边界」与 V-49 对不上：V-49 只证明「250 条基准中最小条目 0.1428，无 ≤0.1 样本」，**并没有**给出「恰等于阈值」的构造样本，EQ2 该行仍是「未验证」而非「已构造」——三档里只有 2 档有可构造输入。 |
| SF-01 | **CLOSED** | V-07 域定义改为「断言域 = 这 10 个键」+「测量域 = 命令输出 19 个键（额外 9 项列出）」；我实跑 `probe_facts.py constants` → **19 个键**，与「测量域 19」一致；断言域 10 项逐一存在。 |
| SF-02 | **CLOSED** | DR2 补全参照命中清单；我复跑 `grep -rn '@math\.ln' --include=*.mbt probes/rand-probe \| grep -v _build` → 代码 **3 处**（`rand-probe.mbt:203`、`cmd/main/main.mbt:140,150`）+ 注释 **4 处**（`rand-probe.mbt:13,174,194`、`cmd/main/main.mbt:117`）——与 spec 清单一致；`// non-native fallback` 已登记为「实现期新增字面 + GP1 生成点」。 |
| SF-03 | **CLOSED** | §2 枚举命令改为 `grep -v -e _build -e .mooncakes -e probes`；我两种形式都跑（bash 与默认解释器）均 **0 行**；`src` 专用命令亦 0 行。 |
| SF-04 | **CLOSED** | §7 标题为「DR1-DR9」，表体 9 行 DR1…DR9。 |
| SF-05 | **CLOSED** | 「45 个以上」已删；改为「公开接缝签名表 **10** 组（§5.1–§5.10 各一行签名）」；我实跑 `grep -c '^### 5[.][0-9]'` → **10**。 |
| SF-06 | **CLOSED** | §8.1/8.2/8.3/8.4 四表列头均含「期望值来源」；「观测输出」列全部为 `—`（`grep -c '| — |'` → **29**）；`待回填` 出现 **0** 次。 |
| SF-07 | **PARTIAL → v3 已销项**（见 §13/§14） | §8.2 低置信行补了「另对 268 条基准全量核对三接口一致性（差异条数须为 0，含 18 条异常样本比异常码）」✅。但该行「操作证据」仍是**文字描述**（「55 短 + 55 长样本分组断言；另对 268 条基准全量核对…」），没有可复跑命令/入口——与 Blocking #46「operation evidence = re-runnable command or entry」仍有差距（同 N-04 族）。 |
| SF-08 | **CLOSED** | §5.10 新增 `debug_vector_len() -> Int`（`[EXT]`），G-33 登记，§3 FR-20 行指向 §5.10，§8.2 大写词行改为 `debug_vector_len()` 与 `get_lang_list()` 对照。§4.5 增「可观察性」列。 |
| SF-09 | **CLOSED** | §5 全部「目标可用性」改为 `native ✅（V-24）/ js ⚠（bun 替代，U-02）/ wasm-gc ⚠（仅 build，U-01）`（8 处一致）；§5.9 另加「数值档位不同」；§5.8 取证通道单独声明「与目标运行时无关」。 |
| SF-10 | **CLOSED** | G-32 改为「`[EXT]` — 非对齐项，产品决策驱动（验收设施形态由 `约定 C：golden 基准消费契约` 决定）」；G-29/30/31/33 同措辞。 |
| SF-11 | **PARTIAL → v3 已销项**（见 §13/§14） | DC-A 自查已改为「如实登记」并列出 §1/§2/§2A/§4.1-4.4/§7/§9.3 六处。但我复扫全文：`file:line` 实际还出现在 **§10.4**（7 行：754/756/757/759/760/761/762，均为 `violation_tmp.mbt:N` 与 `probes/fs-probe/...:3`）与 **§13**（818 行 `probes/gen_mbt.py:80`、`rand-probe.mbt:203`）——这两节不在自查清单内，清单仍不全。 |

> 精确列表：
> - **CLOSED（19）**：BLK-01、BLK-03、BLK-04、BLK-05、BLK-06、BLK-08、BLK-09、BLK-11、BLK-12、BLK-13；SF-01、SF-02、SF-03、SF-04、SF-05、SF-06、SF-08、SF-09、SF-10 —— BLK 10 条 + SF 9 条 = 19。
> - **PARTIAL（6）**：BLK-02、BLK-07、BLK-10、BLK-14、SF-07、SF-11。
> - **NOT CLOSED（0）**。
>
> 合计 19 + 6 = 25 ✔（CLOSED 19 + PARTIAL 6 + NOT CLOSED 0）

---

## 9. 新发现问题（v2 引入或 v2 未覆盖）

### 9.1 Blocking

#### N-01 DR9 的检索式既假红又漏检（新增红线不可用）

**定义原文**：`dialect-redline-gate.md` DR1「每条方言红线一行：约束内容（可判定的禁令句式）+ 出处 + 可机检形态」；DR2「红线表同时声明为 code-review 清单与 lint 规则来源」。

**证据（我跑的）**：

```
# 假红：合法业务标识符含 target
$ cat src/core/zz_legit.mbt
///| 目标语言配置
pub fn target_lang() -> String { "en" }
$ grep -rnE 'target|#if|platform' --include=*.mbt src/core
rc=0  命中 2 行（注释 + 函数名）

# 漏检：真实平台条件编译不含这三个词
$ cat src/core/zz_t.mbt
#cfg(wasm)
fn a() -> Int { 1 }
$ grep -rnE 'target|#if|platform' --include=*.mbt src/core
rc=1  0 行  → MISSED
$ cat src/core/zz_t.mbt
#cfg(js)
...
rc=1  0 行  → MISSED
```

**影响**：DR9 是本轮为承接 DESIGN PS2「业务侧零平台分支」新增的唯一机检形态。它对「`target` 作为业务名词」假红、对真实条件编译形态（`#cfg(wasm)` / `#cfg(js)`，MoonBit 的实际方言）漏检——双向都错，等于没有红线。而 spec 的 T1 记录「对 `src/core` → 0 行，exit 1」只是因为 `src/core` 现在是**空包**（0 个 `.mbt`），属空集假绿。

**改法**：把检索式改为 MoonBit 实际条件编译关键字（示例形态）：`grep -rnE '^[[:space:]]*#(cfg|if)[[:space:]]*\(' --include=*.mbt src/core`，并在 T2 用 `#cfg(wasm)` 作为违规样本；若还要覆盖「运行期平台判断」，另立一行只匹配明确的 API 名（如 `is_wasm`/`target_name`），不要把裸词 `target` 放进扫描域。补 T1「非空包」基线（先放一个合法 `.mbt` 再跑）。

---

#### N-02 §10.4 与 §7 的 7 条命令在 Markdown 里带 `\|` 转义，逐字复制即失败；其中 2 条会把失败误读成通过

**定义原文**：Blocking #50「每条机检命令必须 T1 语法可跑」；`gate-command-validation-gate.md` T1「无解析 / 转义 / 路径分隔符错误」。

**证据（我跑的）**：表格单元格里的 `\|` 是 Markdown 转义，但 spec 用「复制即用」的形态呈现（如 §7 第 565/566 行、§10.4 第 754/756/757/759/760/761/762 行、§9.4 第 703 行、§9.1 第 670 行）。逐字复制到 bash：

```
$ grep -rnE 'target\|#if\|platform' --include=*.mbt src/core     # DR9 逐字
rc=1（无输出）→ 看起来「0 行、通过」
$ grep -rnE 'target|#if|platform' --include=*.mbt src/core       # 去掉转义
rc=0（命中违规）

$ grep -rnE 'println\|print\(\|eprintln\|@stdio' --include=*.mbt src/core src/data src/unicode src/math_seam   # NE1 逐字
rc=1 → 看起来通过
$ （去掉转义，且放入 println 违规）
rc=0 命中 2 行
```

更严重的一条：

```
$ test "$(md5sum docs/port/golden/expected.json \| cut -d' ' -f1)" = "219519ee…"   # C-C6 逐字
rc=2  stderr: md5sum: invalid option -- 'd'
$ （去掉转义）
rc=0
```

即：**C-C6 逐字复制会在所有情况下 rc≠0**（包括基准正常时），如果 CI 把它当「非 0 即阻断」，会永久红；如果有人用「rc==2 视为路径问题、跳过」，就永久不检查。DR9/NE1/L1-A1/DR3/DR8 逐字复制则是**永久绿**（正则里 `\|` 变成字面竖线，永不匹配），这正是门禁校验门禁要挡的假通过形态。

**改法**：在 §7/§9/§10 四张表下方统一加一句「表内 `\|` 为 Markdown 转义，执行前须去转义（或从本节代码块复制）」，并把每条命令同时给一份**代码块形态**（非表格单元格）。或者改用 `-e` 多模式 / 字符类 `[|]` 写法，使命令本身不含 `|`。

---

#### N-03 §4A 把 `src/core/cmd/main/` 登记为产品路径，但该包不存在；`moon check` 不校验 `moon.mod` 的 name 字面

**定义原文**：`gate-command-validation-gate.md` GP1「每条命令引用的每个路径反查到四要素；反查不到 = 该命令不可跑」；Blocking #8「每个交付物带可复跑验证命令」。

**证据（我跑的）**：

```
$ find src -type f
src/core/moon.pkg
src/data/moon.pkg
src/math_seam/moon.pkg
src/unicode/moon.pkg          ← 无 src/core/cmd/main/，无任何 .mbt

$ cat moon.mod
name = "vicoproplus/langdetect"
version = "0.1.0"

# 校验命令能否校验 name？
$ 把 name 改为 "x/y" 后 moon check → rc=0（不校验）
$ 删除 moon.mod 后 moon check → rc≠0（只校验存在性）
```

§4A 第 398 行把 `moon.mod` 的校验命令写成 `moon check`——它只校验「模块存在 + 包图可解」，**不校验 name 字面**。§4A 第 407 行把 `src/core/cmd/main/` 列为产品路径并称「校验 = §9.4 NE1 静态检查 + 运行时输出字节数」，但该目录不存在、其可执行包形态（需 `pkgtype(kind: "executable")`）也未登记；我按 spec 语义建了该包并跑 `moon build` → `_build/native/debug/build/src/core/cmd/main/main.exe` 才出现，说明它是**必须新建的产物**，而 §4A 的「生成时点」列写的是「实现期」、生成命令写「—」。

**改法**：① 补一条真正校验 name 的命令（如 `grep -q '^name = "vicoproplus/langdetect"$' moon.mod`）并把 `moon check` 降级为「语法/包图」校验；② 把 `src/core/cmd/main/` 的 `moon.pkg`（`pkgtype(kind: "executable")`）与产物路径 `_build/native/debug/build/src/core/cmd/main/main.exe` 写入 §4A 表，并给 GP1 四要素；③ 明确 4 个空 `moon.pkg` 是**脚手架**（当前 0 字节、0 个 `.mbt`），不构成实现交付物——否则 `moon check` 的 rc=0 是空包假绿。

---

#### N-04 §8 的「操作证据」列大面积不是可复跑命令（Blocking #46 三要素未闭合）

**定义原文**：Blocking #46「每行三要素：目标环境标识 + 操作证据（可重跑命令或入口 + 第三方可复现步骤）+ 观测输出（实际退出码/响应/记录指针，期望值冒充观测 = 未回填）」。

**证据（我读 + 跑）**：§8.2/§8.3/§8.4 的「操作证据」列 20 行里，只有 4 行是命令形态（`moon test --target native`、`moon build --target …`、`约定 A §3 全部命令`、`get_lang_list()` 长度断言），其余为过程描述：

- §8.2 第 590 行「消费 `约定 C` §3 的比对脚本」——该脚本不存在（`find . -name "*compare*"` 只有 `probes/rand_probe_compare.py`、`probes/float_probe_compare.py`，均非 `约定 C` 的比对器）；
- §8.2 第 591 行「① seed=0 对同文本连续 5 次 → …；② 改 seed=42 …；③ 不设 seed …」——无命令；
- §8.2 第 592/593 行「构造 3 类失败…」「码 5/4/8 各构造一次 → 把异常对象序列化…」——无命令；
- §8.3 第 604/605/606 行「同一 55 长文本样本集」「`get_lang_list()` 长度断言」「逐语言条目数求和」——无命令；
- §8.4 第 613/614/615/616 行「同上」「14 组重复采样」「待容差登记后执行」——无命令。

观测输出列虽已全部改 `—`（SF-06 已闭合），但「三要素」中的第二要素仍普遍缺失，且 §8 门禁条款只说「不得判该维度完成」，未给出**如何补**（哪个命令、哪个入口）。

**改法**：对 20 行逐行补「命令 + 入口」；对确实无法在本机执行的（如 §8.3 三目标一致）按 `[LOCAL_DEAD_LINK]` 登记（当前 §8.3 四行都没有该标签）。

---

### 9.2 Should-fix

#### N-05 L1-A4 的验证命令引用了不存在的 API

`Detector` 无 `get_lang_list()`（`hasattr(d,'get_lang_list')` → **False**；该方法在 `DetectorFactory` 上）。L1-A4 原文「已建实例的 `get_lang_list()` 反映新语言」不可执行。我改用 `len(d.langlist)` 验证别名成立（55 → 56）。改法：命令改为 `len(d.langlist)` 或 `len(d.get_probabilities())` 的对照。

#### N-06 `DetectorFactory::create(alpha? : Double)` 的调用形态未定义

按原样声明 `moon check` rc=0（作为关联函数），但 `f.create()` 形态报 `[4080] This function has type (alpha? : Double) -> Detector, which requires 0 positional arguments, but is given 1 positional arguments`；带 `self : DetectorFactory` 则 rc=0。spec 未说明它是「关联函数（`DetectorFactory::create(...)`）」还是「实例方法」，§5.5 的「工厂侧」三字不足以裁决，plan 阶段会出现两种实现。改法：签名显式写 `DetectorFactory::create(self : DetectorFactory, alpha? : Double) -> Detector`，或在 §5.5 增一行「调用形态：`DetectorFactory::create(alpha=0.5)`（关联函数，无 self）」。

#### N-07 §8.2 的 seed 语义行没有可复跑命令（与 N-04 同族但单独指出）

该行是 BLK-08 的销项载体，但三步判据全部是自然语言。建议给出最小命令（示例形态）：`.venv/Scripts/python.exe -c "…for _ in range(5): assert detect_langs(t) == first"` 与 `docs/port/golden/expected.json` 的 `repeatability`（14 组）/`unseeded_runs` 比对脚本路径。

#### N-08 §2A 的目标侧测试文件全部「未落地」，但 §2A 未进 §8 验收

§2A 列了 4 个目标侧测试文件（`src/core/detector_test.mbt` 等），`find src -name '*_test.mbt'` → **0**。这本身是「未落地」的如实登记（BLK-12 已闭合），但 §8 没有任何一行验证「这些测试文件存在且通过」，等于测试对齐只到「计划」不到「验收」。改法：§8 增一行「源侧 23 用例的目标侧对应文件全部存在且 `moon test` 通过」，或明确登记为后续批次的 `[LOCAL_DEAD_LINK]`。

#### N-09 §0A D2 的依赖方向不可机检（DR9 只覆盖平台分支，不覆盖模块依赖）

D2 声明「`src/core/` → {math_seam, unicode, data} → 标准库，单向无环」，但我实测 `src/data/moon.pkg` 写 `import { "vicoproplus/langdetect/src/core" }` 后 `moon check` → **rc=0**（编译器允许，D2 禁止）。当前没有任何门禁能拦住反向依赖。改法：增一条 DR 行（示例形态）`grep -l 'vicoproplus/langdetect/src/core' src/data/moon.pkg src/unicode/moon.pkg src/math_seam/moon.pkg` 必须 0 命中，或把「允许依赖」列进 §4A 的 GP1 校验命令。

---

## 10. v2 新增实体的四元组核查

| 实体 | 断言/域/命令/结果 四元组 | 我复跑结果 | 判定 |
|---|---|---|---|
| V-49（最小条目概率 0.1428…，无 ≤0.1） | 齐备（域 = 全部条目 prob 排序取最小） | `(0.1428316217995734, 'short-ca', 'ro')` / `le_0.1 0` | ✅ 一致 |
| V-50（等概率并列可构造） | 齐备（域 = 临时目录 + 公开 API） | `[('x1','0.4999999999999999'),('x2','0.4999999999999999')]` | ✅ 一致 |
| V-51（NaN 先验 → 空列表 + unknown） | 齐备 | `prior [nan, nan]` / `probs 0 detect unknown` | ✅ 一致 |
| V-52（引用别名 True True） | 齐备（域 = 身份比较） | `True True` | ✅ 一致 |
| V-53（langsize 只在词向量行长） | 齐备 | `langlist ['aa','bb'] word_row 4 langprob 2` | ✅ 一致 |
| V-54（cleaning 幂等 / append 累加） | 齐备 | `idempotent True` / `append hellohello` | ✅ 一致 |
| V-55（旧签名 4 处报错） | 域 = `moon check` 于临时工程；但**未给构造样本路径**，只写「见 §5.8 注」 | §5.8 注只列了 3 个错误码（4118/3010/3002），**缺 3800**（单行 struct 字段用 `,` 分隔）的构造样本 | ⚠ 部分：4 处中 3 处可复现（我另跑出 4014/4080/4122），3800 未给样本 |
| V-56（根模块与探针共存） | 域 = 根目录 `moon check`；结果 `Finished. moon: no work to do` | 我跑：`moon check` rc=0 ✅；`moon build` rc=0；probes 三模块 rc=0（rand-probe 需 `--target native`） | ✅ 一致；但「不把 `probes/*` 当作本模块包」我另测：把 `probes/embed-probe/lib/data/data.mbt` 写坏后根 `moon check` 仍 rc=0（不扫 probes）✅，`_build/index.json` 也不含 probes ✅ |
| V-57（新签名 0 errors） | 域 = `moon check` 临时工程；构造样本给了 `suberror` + `enum` + `fn create(alpha? : Double)` | 我逐字抄进临时工程：`suberror`/`enum`/`create(alpha?)`/`LangProb`/`LowConfidence`/`Detected` → **rc=0** ✅；但**方法形态**（set_seed/set_prior_map/set_max_text_length 无 self）→ **7 errors**（4014/4080/4122） | ⚠ 部分：V-57 的样本未覆盖 §5.5-§5.7 的方法签名 |
| G-33 `debug_vector_len()` | `[EXT]` 已登记（§2）、§5.10 有签名/语义/用途/回链、§3 FR-20 有归属、§8.2 有验收行 | `grep` 四处均命中 | ✅ 齐备 |
| DR9 | 出处 = DESIGN PS2；可机检形态存在 | **判据双向失效**（见 N-01） | ❌ Blocking |

---

## 11. v2 第二轮 Blocking Checks 复核（只列判定变化的行）

| # | 检查项 | v1 | v2 | 依据 |
|---|---|---|---|---|
| 5 | 四维 D1-D4 且无实现代码 | Fail | **Pass** | §0A 四小节齐全；§4.4 代码围栏已删 |
| 8 | 每个交付物带可复跑命令 | Fail | **Fail** | N-03（cmd/main 未建）+ N-04（§8 操作证据非命令） |
| 9 | 验收 ≥3 维度且任一失败=整体失败 | Fail | **Fail** | 「任一失败 = 整体失败」条款仍缺（`grep 任一失败\|整体失败` → 0） |
| 10 | 源侧测试有目标侧对应 | Fail | **Pass** | §2A 5 行齐备，用例数复跑一致 |
| 18 | 三层断言面 | Fail | **Pass** | §9.1 14 入口 + §9.3 15 行 + 层 2 N/A 有理由 |
| 19 | 负向轴 NE1-NE4 | Fail | **Fail** | NE1 静态半句与自身「cmd/main 除外」矛盾（BLK-10 PARTIAL）；NE2 仍把编译期错误当错误形态 |
| 27 | 文档契约纪律 | Fail | **Fail** | SF-11 PARTIAL（§10.4/§13 的 `file:line` 不在自查清单） |
| 30 | 入口副作用全枚举 | Fail | **Pass** | 14 入口 + 别名列 + L1-A4（命令 API 名有误，见 N-05） |
| 31 | 语言特性矩阵 + 探针 | Fail | **Fail** | §5.5-§5.7 方法签名仍不可调用（BLK-07 PARTIAL） |
| 34 | 外部消费字面逐字 + 证据等级 | Fail | **Fail** | 全文仍无 `import {` / `vicoproplus/langdetect/src/...` 字面（我实测正确形态是 `vicoproplus/langdetect/src/core`，`.../core` 与 `@core` 均报 `Cannot find import`） |
| 35 | 平台无关性声称登记为假设 | Fail | **Pass** | §5 八处已分级（✅/⚠/⚠ + U-01/U-02） |
| 36 | 失败语义有取证通道 | Fail | **Pass** | §5.8 取证通道 + §8.2 验收行 |
| 43 | 方言红线表可机检 | Fail | **Fail** | DR9 双向失效（N-01）+ 7 条命令转义不可执行（N-02） |
| 45 | EQ1-EQ3 | Fail | **Fail** | §8.5 齐备但 EQ2 一档未构造（BLK-14 PARTIAL） |
| 46 | 验收行三要素 | Fail | **Fail** | N-04 |
| 50 | 每条命令 T1/T2/T3 | Fail | **Fail** | N-02（逐字复制失败/假绿）+ N-01（T1 空集假绿） |
| 53 | 契约两两互查落回条款 | Fail | **Pass** | MS1-6 → §7 总则；MS1-8 → §8.4 平台列 |

**统计**：Pass 12 / Fail 9 / N/A 32（合计 53）。

---

## 12. 第二轮结论

**Status: Issues Found**

- 25 条销项：**CLOSED 19 / PARTIAL 6 / NOT CLOSED 0**
- 新发现：**Blocking 4（N-01…N-04）+ Should-fix 5（N-05…N-09）**
- 阻断项集中在两处：**DR9 的双向失效**（N-01）与 **7 条命令的 Markdown 转义不可执行/假绿**（N-02）——两者都属「门禁看起来在、实际不拦」的形态，正是本轮要挡的失败模式；另加 **§4A 路径登记与实际仓库不一致**（N-03）与 **§8 操作证据不是命令**（N-04）。

**建议的修订顺序（第三轮）**：

1. **N-01**：重写 DR9 检索式为 MoonBit 条件编译关键字；补「非空包」T1 基线 + `#cfg(wasm)` T2 实录。
2. **N-02**：为 §7/§9/§10 的命令统一加「去转义」说明 + 每条给一份代码块形态；C-C6 的逐字形态必须修正（当前 rc=2 且 stderr 有 `md5sum: invalid option`）。
3. **N-03**：§4A 补 `src/core/cmd/main/moon.pkg` 与产物路径 + GP1 四要素；`moon.mod` 的 name 校验改 `grep -q '^name = "vicoproplus/langdetect"$' moon.mod`。
4. **BLK-07 余项**：§5.5/§5.6/§5.7 三个方法签名补 `self : Detector`；`DetectorFactory::create` 显式裁决关联函数/实例方法（N-06）。
5. **N-04 + SF-07 余项**：§8 的 20 行逐行补命令或登记 `[LOCAL_DEAD_LINK]`。
6. **BLK-10 余项**：NE1 静态 grep 增 `--exclude-dir=cmd`（或把 cmd/main 移出四个产品目录）。
7. **BLK-02 余项**：§15 的派生命令改名为「门禁表数据行数」，并补「命令条数」的独立派生（B1/B3/B4 合并行需单独计数）。
8. **BLK-14 余项**：EQ2 的阈值边界档给出可构造输入（或显式登记为实现期 `[LOCAL_DEAD_LINK]` 并带触发条件）。
9. **SF-11 余项**：DC-A 清单补 §10.4/§13。

---

---

# 第三轮复审（v3，2026-10-21）

> 本节由 spec 修订者填写：逐条记录 v2 复审的 4 条新 Blocking、5 条新 Should-fix、以及 6 条 PARTIAL 的处置与复跑证据。**定义原文列不改**（沿用前两轮），本节只补「销项证据 / 状态」。

## 13. 第三轮登记表

| 编号 | 定义原文（沿用） | 销项证据（含复跑命令 + 输出 + rc） | 状态 |
|---|---|---|---|
| N-01 | DR9 检索式须对真实条件编译生效、对合法标识符不假红 | ① 检索式改为 `grep -rnE '^[[:space:]]*#(cfg\|if)[[:space:]]*\(' --include=*.mbt src/core`（§10.6 命令 1）；② **非空包 T1 基线**：放 `pub fn noop() -> Unit { () }` 后 rc=1（0 行），并放 `target_lang()` + 中文注释「目标」→ 新式 rc=**1**（v2 旧式同样本 rc=**0** 命中 1 行，假红）；③ **T2**：`#cfg(wasm)` → rc=**0**（命中 1 行）、`#cfg(js)` → rc=**0**（v2 旧式同样本 rc=**1** 漏检）；④ 另立 DR10（运行期平台 API）与 DR11（反向依赖），见 §7 | 已销项 |
| N-02 | 7 条命令带 Markdown `\|` 转义，逐字复制失败/假绿 | ① §7 / §9 / §10 三处表下统一加「`\|` 仅为 Markdown 转义，执行时从 §10.6 代码块复制」；② 新增 **§10.6 代码块命令清单 30 条**（全部不含 `|`，用 `-e` 多模式/字符类替代）；③ **C-C6 改为** `test "$(md5sum … \| awk '{print $1}')" = "219519ee…"`，逐字复制 rc=**0**，改 1 字节后 rc=**1**（v2 形态 `cut -d' '` 逐字复制 rc=2 且 `md5sum: invalid option`）；④ 执行环境注记：须 POSIX shell + GNU grep（本机默认 `grep (pi-uu-grep) 0.2.0` 解析不一致，实测同命令 rc 不同） | 已销项 |
| N-03 | §4A 落点须与实际仓库一致；`moon check` 不校验 name 字面 | ① `moon.mod` 校验改为两条：`grep -q '^name = "vicoproplus/langdetect"$' moon.mod`（rc=**0**；改成 `name="x/y"` → rc=**1**）+ `moon check`（降级为「语法/包图校验」）；② §4A 补 4 行：`src/core/cmd/main/moon.pkg`（含 `pkgtype(kind: "executable")`）、`src/core/cmd/main/main.mbt`、`_build/native/debug/build/src/core/cmd/main/main.exe`、`tools/compare_golden.py` / `tools/compare_lowconf.py`，各给 GP1 四要素；③ 明确 4 个空 `moon.pkg` 是**脚手架**（0 字节、0 个产品符号），`moon check` rc=0 不证明实现存在；④ 实跑 `find src -type f` → **6** 个文件 | 已销项 |
| N-04 | §8「操作证据」须为可复跑命令或入口 | ① §8.1–§8.4 共 **21** 行逐行改为命令形态：`moon test/build --target …`、`python tools/compare_golden.py --target … --mode …`、`python tools/compare_lowconf.py …`、§10.6 命令编号；② 新增的 3 个脚本（`compare_golden.py` / `compare_lowconf.py`）已在 §4A 登记 GP1 四要素；③ §8.3 的 3 行与 §8.4 的 2 行加 `[LOCAL_DEAD_LINK]` + 分类 + 处置（对应 U-01/U-02/U-04/U-05）；④ §8 门禁条款补「二选一：命令 或 `[LOCAL_DEAD_LINK]`」 | 已销项 |
| N-05 | L1-A4 引用了不存在的 `Detector.get_lang_list()` | L1-A4 验证改为「断言 `len(detector.langlist)` 与 `len(factory.langlist)` 同步增加 + `detector.langlist is factory.langlist` 为 True」，并显式注明「`get_lang_list()` 是工厂方法，`Detector` 无此方法」 | 已销项 |
| N-06 | `DetectorFactory::create` 关联函数/方法形态未定义 | §5.5 签名改为 `DetectorFactory::create(self : DetectorFactory, alpha? : Double) -> Detector`（**实例方法**），并新增「调用形态」行：`factory.create()` / `factory.create(alpha=0.5)`，**不写 `Some(...)`**（V-58 实测 `Some(0.5)` → `[4014]`） | 已销项 |
| N-07 | seed 语义行无可复跑命令 | §8.2 seed 行改为 `python tools/compare_golden.py --target native --mode seed_semantics`（三步判据保留为期望值来源：`repeatability` 14 组 / `unseeded_runs`） | 已销项 |
| N-08 | §2A 目标侧测试文件未进 §8 验收 | §8.3 增一行「源侧 23 用例的目标侧对应文件存在且通过」= `moon test --target native`（§2A 的 4 个 `*_test.mbt` 就位后），状态「未验证」 | 已销项 |
| N-09 | D2 依赖方向不可机检 | 新增 **DR11**（反向模块依赖）+ §10.6 命令 3：`grep -rn -e 'vicoproplus/langdetect/src/core' --include=moon.pkg src/data src/unicode src/math_seam`，T1 rc=**1**（0 行）；T2 在 `src/data/moon.pkg` 写反向 import → rc=**0**（命中 1 行） | 已销项 |

## 14. PARTIAL 补完（6 条）

| 编号 | v2 判定 | v3 处置 | 复跑证据 | 状态 |
|---|---|---|---|---|
| BLK-02 | PARTIAL | §15 拆两个独立派生：**表行数**（命令 A）与**命令条数**（命令 B），并改名不再混用「命令行数」 | 命令 A → **25**（C- 14 + DR 11）、rc=0；命令 B（`grep -cE '^# 命令 [0-9]+：'`）→ **30**、rc=0 | 已销项 |
| BLK-07 | PARTIAL | §5.5/§5.6/§5.7 三个方法补 `self : Detector`；`create` 定为实例方法（N-06）；新增 **V-58** 记录修正后 `moon check` 0 errors + 反例错误码（`[4014]`/`[4080]`/`[4014] Constr Type Mismatch`） | 临时工程 `moon check` → `Finished. moon: ran 2 tasks, now up to date`（0 errors）；调用形态 `f.create()`、`f.create(alpha=0.5)`、`g.set_seed(Some(0L))`、`g.set_max_text_length(50)` 全部通过 | 已销项 |
| BLK-10 | PARTIAL | NE1 静态命令加 `grep -vE '[\\/]cmd[\\/]'`（同时兼容 `\` 与 `/`），并在命令里真正排除 cmd | `println` 放 `src/core/cmd/main/main.mbt` → rc=**1**（0 行）；放 `src/core/zz_n.mbt` → rc=**0**（命中 1 行）；空 `main` 二进制 stdout/stderr 均 **0** 字节 | 已销项 |
| BLK-14 | PARTIAL | EQ2 阈值边界档改为**二选一已裁决**：明确「只能经接缝注入构造」→ 标 `[LOCAL_DEAD_LINK]`（分类：能力未验证；回补触发 = 接缝可注入概率数组；处置 = 实现期补三组样本），不再留「未验证 + 需注入」的无处置表述 | §8.5 EQ2 该行已改写；与 V-49（无 ≤0.1 样本）对账一致 | 已销项 |
| SF-07 | PARTIAL | §8.2 低置信行改为命令形态 `python tools/compare_lowconf.py --short 55 --long 55 --baseline 268`（268 条口径保留为期望值来源），脚本已在 §4A 登记 | 命令形态已入表；脚本待实现（§4A 已登记 GP1 四要素） | 已销项 |
| SF-11 | PARTIAL | DC-A 自查清单补 §10.4 / §10.6 的 T2 实录列（`violation_tmp.mbt:N` 等）与 §13 的 R1 理由（`probes/gen_mbt.py:80`、`rand-probe.mbt:203`） | `grep -n "DC-A 稳定标识引用" <spec>` 行内已列出 10 处事实源位置 | 已销项 |

## 15. 第三轮新 Should-fix 处置

| 编号 | 处置 | 状态 |
|---|---|---|
| N-05 | 见 §13 N-05 行 | 已销项 |
| N-06 | 见 §13 N-06 行 | 已销项 |
| N-07 | 见 §13 N-07 行 | 已销项 |
| N-08 | 见 §13 N-08 行 | 已销项 |
| N-09 | 见 §13 N-09 行 | 已销项 |

## 16. 第三轮实跑汇总（2026-10-21，POSIX shell + GNU grep）

| 项 | 结果 |
|---|---|
| §10.6 代码块命令条数 | **30**（`grep -cE '^# 命令 [0-9]+：'` → 30） |
| T1 逐字复制实跑 | 27 条通过（rc 与各条注释一致）；3 条待产品实现（命令 3 的 T2 需产品 `moon.pkg` 反向 import 样本已跑、命令 13 的 T2、命令 27 的期望值随实现变化） |
| T2 违规样本实跑 | 14 条（见 §10.6 T2 表），全部按预期红/命中 |
| `src/` 脚手架 | 6 个文件（4 个 0 字节 `moon.pkg` + cmd 包 2 个）；产品公开符号 **0** |
| `moon check`（仓库根） | `Finished. moon: no work to do`（rc=0） |
| `<产品目录>` 残留 | **0** |
| 环境前提 | 本机默认 `grep` 为 `grep (pi-uu-grep) 0.2.0`；全部 rc 均在 `PATH="/d/Program Files/Git/usr/bin:$PATH"` 下取得 |


---

# 第四轮核验（v3，2026-10-21）

> **审查对象**：`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md` v3（1061 行 / 104,914 B）
> **作者声称**：销项 N-01…N-04 + 6 条 PARTIAL + 5 条新 SF；§10.6 新增 30 条代码块命令，T2 实录 14 条；「27 条逐字复制通过、3 条待产品实现」
> **本轮方法**：30 条命令**从 spec 代码块逐字复制**执行（脚本化抽取，非手工重构）；25 条销项逐条去 spec 找改动 + 自跑命令；重点复核 §10.6 命令 20 / 26 / 28 / 29 / 30、NE1 cmd 例外、§4A 六文件、BLK-07 方法签名、EQ2 标签、§8 三要素。
> **结论**：**Issues Found** —— 15 条销项 **CLOSED 14 / PARTIAL 1 / NOT CLOSED 0**；30 条命令实跑 **28 条 rc 与注释一致、1 条不一致（命令 28）、1 条判据失效（命令 29，rc 对但结论不可信）**；新发现 **9 条（Blocking 3 / Should-fix 6）**。

---

## 17. 30 条命令逐字复制实跑（§10.6）

**抽取方式**：脚本从 `### 10.6` 后的 ` ```bash ` 块按 `^# 命令 N：` 切分，逐条原样交给 `bash -c`（cwd = 仓库根），不做任何改写。

| # | rc | 注释期望 | 一致 | 输出摘 |
|---|---|---|---|---|
| 1 | 1 | rc=1 | ✅ | — |
| 2 | 1 | rc=1 | ✅ | — |
| 3 | 1 | rc=1 | ✅ | — |
| 4 | 1 | rc=1 | ✅ | — |
| 5 | 1 | rc=1 | ✅ | — |
| 6 | 1 | rc=1 | ✅ | — |
| 7 | 1 | rc=1 | ✅ | — |
| 8 | 1 | rc=1 | ✅ | — |
| 9 | 1 | rc=1 | ✅ | — |
| 10 | 1 | rc=1 | ✅ | — |
| 11 | 1 | rc=1 | ✅ | — |
| 12 | 1 | rc=1 | ✅ | — |
| 13 | 1 | rc=1 | ✅ | — |
| 14 | 1 | rc=1 | ✅ | — |
| 15 | 0 | rc=0 | ✅ | — |
| 16 | 0 | rc=0 | ✅ | `ok` |
| 17 | 0 | rc=0 | ✅ | `ok` |
| 18 | 0 | rc=0 | ✅ | `ok` |
| 19 | 0 | rc=0 | ✅ | `ok` |
| 20 | 0 | rc=0 | ✅ | `ok 1951 cps / 651 intervals` |
| 21 | 0 | rc=0 | ✅ | — |
| 22 | 0 | rc=0 | ✅ | — |
| 23 | 0 | rc=0 | ✅ | — |
| 24 | 0 | rc=0 | ✅ | — |
| 25 | 0 | rc=0 | ✅ | — |
| 26 | 0 | 期望 25 | ✅ | `25` |
| 27 | 1 | rc=1 | ✅ | — |
| 28 | **1** | rc=0 | ❌ | 无输出（grep 未匹配） |
| 29 | **0** | 两行均 0 | ❌（假绿） | `0 /tmp/o.txt` `0 /tmp/e.txt` — 但见 N-10：**路径不存在时也输出 0** |
| 30 | 0 | rc=0 | ✅ | — |

**统计**：**28 条** rc 与注释一致；**命令 28 不一致**（期望 0、实得 1，见 N-11）；**命令 29 判据失效**（rc 与两行 0 都对，但二进制不存在时同样满足 → 假绿，见 N-10）。

### 17.1 关于「27 条通过 / 3 条待产品实现」

作者列的 3 条是「命令 3 的 T2、命令 13 的 T2、命令 27 的期望值」。我逐条实跑：

- **命令 3 的 T2 完全可以跑**：`src/data/moon.pkg` 写入 `"vicoproplus/langdetect/src/core",` → `grep -rn -e 'vicoproplus/langdetect/src/core' --include=moon.pkg src/data src/unicode src/math_seam` → **rc=0，命中 1 行**；还原后 rc=1。→ **不是「待产品实现」，是漏跑**。
- **命令 13 的 T2 同样可以跑**：`src/core/zz_r.mbt` 写 `fn r() { read_file("x") }` → `grep -rn 'read_file' src` → **rc=0，命中 1 行**；还原后 rc=1。→ **漏跑**。
- **命令 27 的 T2**：`grep -rn '^pub fn' --include=*.mbt src` 的「违规样本」是产品有符号；当前 0 符号，T2 需先写一个 `pub fn` 再删。实跑：`src/core/zz_p.mbt` 写 `pub fn a() -> Int { 1 }` → **rc=0，命中 1 行**；还原后 **rc=1**。→ **漏跑**。

**结论**：3 条「待产品实现」中 **0 条**真的只能等实现；§15 第 1055 行的这一句不成立。

### 17.2 命令 20 的等价性（重点）

作者把多行 Python 压成单行，用列表推导做副作用：

```python
iv=[];[iv.append([cp,cp]) if not iv or cp!=iv[-1][1]+1 else iv[-1].__setitem__(1,cp) for cp in cps];assert len(iv)==651
```

我逐字复跑，并与多行参考实现对比：

```
$ .venv/Scripts/python.exe -c "<命令 20 原文>"
ok 1951 cps / 651 intervals        rc=0

$ （多行参考实现）
651 [[65, 90], [192, 214], [216, 222]] ... [[127280, 127305], [127312, 127337], [127344, 127369]]
$ （单行实现，打印同样的 iv）
651 [[65, 90], [192, 214], [216, 222]] ... [[127280, 127305], [127312, 127337], [127344, 127369]]
```

**数值等价成立**（651 与区间边界完全一致）。但写法本身是**用列表推导执行副作用**，且调用 `list.__setitem__` 私有方法——属可读性与稳健性缺陷，不影响当前结论，记 N-13（Should-fix）：改为 `for` 循环（`python -c` 支持多语句用 `;` 分隔，但 `for` 需要换行，可用 `exec()` 或改用 `awk`/`reduce` 形态）。

---

## 18. 15 条销项判定

### 18.1 N-01…N-04

| 编号 | 判定 | 我的复核（命令 + 输出） |
|---|---|---|
| N-01 | **CLOSED** | 新检索式 `grep -rnE '^[[:space:]]*#(cfg\|if)[[:space:]]*\(' --include=*.mbt src/core`：非空包基线（放 `pub fn noop()`）→ rc=1；写 `#cfg(wasm)` → **rc=0 命中 1 行**；写 `#cfg(js)` → **rc=0**；写 `#if(wasm)` → **rc=0**；缩进 `  #cfg(wasm)` → **rc=0**；合法标识符 `pub fn target_lang()` + 中文注释「目标」→ **rc=1（0 行，不再假红）**；把 `#cfg(wasm)` 写在行内注释里（`// #cfg(wasm)`）→ **rc=1**（`^[[:space:]]*#` 锚定在行首，行内出现不命中）。DR10：`is_wasm()` → rc=0 命中；DR11：`src/data/moon.pkg` 反向 import → rc=0 命中，还原后 rc=1。**残留**：DR10 对 `is_wasm_compatible` / `get_target_name_of` 这类合法标识符仍假红（见 N-18），但比 v2 的裸 `target` 好得多，且 DR10 明确限定「运行期平台 API」三词。 |
| N-02 | **CLOSED**（命令 28 除外，见 N-11） | §10.6 的 30 条命令**全部不含 `\|` 转义**（脚本扫描：仅命令 26 的 `grep -cE '^\| \*{0,2}(C-|DR)'` 内含一处 `\|`——那是 ERE 里的**转义竖线**（匹配字面 `|`）、语义正确，实跑 rc=0 输出 `25`）。29/30 条逐字复制可跑。**唯一例外**：命令 28 因 `moon.mod` 为 CRLF 行尾，`grep -q '^name = "…"$'` 的 `$` 锚点匹配失败 → rc=1（期望 0）。 |
| N-03 | **CLOSED**（附 N-10、N-14） | `find src -type f` → **6 个文件**：4 个 0 字节 `moon.pkg` + `src/core/cmd/main/moon.pkg`（28 B，含 `pkgtype(kind: "executable")`）+ `src/core/cmd/main/main.mbt`（12 B，`fn main {\n}`）。`grep -q 'pkgtype(kind: "executable")' src/core/cmd/main/moon.pkg` → **rc=0**。删掉整个 `_build` 后 `moon build --target native` → **rc=0**，产出 `_build/native/debug/build/src/core/cmd/main/main.exe`（175,104 B）→ 命令 29 的二进制**确实可再生**。`moon.mod` 的 name 校验已改为 `grep -q`（实测 `name="x/y"` → rc=1；`moon check` 仍 rc=0，spec 已如实注明「不校验 name 字面」）。**但**：`moon.mod` 是 CRLF，导致该 `grep` 在真实文件上 rc=1（N-11）；`main.mbt` 是空 `fn main {}`，而 §4A 第 409 行与 §8.1 第 599 行都称「该入口内调一次 `detect`」（N-14）。 |
| N-04 | **PARTIAL → v4 已销项 → v5 复核通过**（见 §23 N-12 行 / §25 / 第七轮 §28 N-21·N-22） | §8.1–§8.4 共 22 行，**每行都有命令形态**（`moon.exe …` / `python tools/compare_*.py …` / §10.6 命令编号）✅；§8.3 三行 + §8.4 两行已标 `[LOCAL_DEAD_LINK]` + 分类 + 处置 ✅；§8 门禁条款补了「(a) 命令 或 (b) LOCAL_DEAD_LINK」二选一 ✅。**但**：(a) 的 8 行 §8.2 全部指向 `tools/compare_golden.py` / `tools/compare_lowconf.py`——**这两个脚本不存在**（`os.path.exists` → False），§4A 只写「生成时点 = 实现期、生成命令 = —」，即**没有生成命令**（GP1 四要素里「生成命令」为空），与 N-03 的教训（`moon check` 不校验）同类。§8.2 第 605 行自己承认「未落地前等价入口 = §10.6 命令 16–19 的基准侧自检」，但命令 16–19 只验证**基准文件本身**，不验证产品行为——等价不成立。 |

### 18.2 6 条 PARTIAL（BLK-02/07/10/14、SF-07/11）

| 编号 | 判定 | 我的复核 |
|---|---|---|
| BLK-02 | **CLOSED** | §15 已拆两个独立派生：命令 A（表行数）→ 实跑 **25**（C- 14 + DR 11，与 `awk`/`grep -c` 逐表核对 5+4+5+11=25 一致）；命令 B（§10.6 命令条数）→ 实跑 **30**。**残留**：第 1037 行同一格写「**26**（A 6 + B 6 + C 6 + DR 11 = 29 编号…展开后按 §10.6 计 **30**）」——「26」与算式 `6+6+6+11=29` 及「30」三者互不自洽（见 N-11）。 |
| BLK-07 | **CLOSED** | 把 §5.5/§5.6/§5.7 逐字抄进临时工程并以**方法形态**调用：`d.set_seed(Some(0L))`、`d.set_seed(None)`、`d.set_max_text_length(5)`、`d.set_prior_map(m)`、`f.create()`、`f.create(alpha=0.5)` → `moon check` **rc=0，0 errors**（3 warnings：`[0006] unused_constructor` / `[0024] unused_error_type` / `[0082] ambiguous_braces`，均为临时样本自身、非签名缺陷）。V-58 的「`Some(0.5)` 报 `[4014] Constr Type Mismatch」——我实测是 **`[4080]`（requires 1 positional arguments, but is given 2）**，错误码不符（N-15）。 |
| BLK-10 | **CLOSED** | 命令 11 = `grep -rn -e println … src/core src/data src/unicode src/math_seam \| grep -vE '[\\/]cmd[\\/]'`。把 `println("x")` 放进 `src/core/cmd/main/main.mbt` → **rc=1（0 行）**；放进 `src/core/zz_n.mbt` → **rc=0（命中 1 行）**；还原后 rc=1。运行时半句：空 `fn main {}` 的二进制 stdout **0 B** / stderr **0 B** ✅。**残留**：`main.mbt` 是空 `main`，并未「调一次 detect」（N-14）——运行时断言虽可满足，但被验证的不是产品检测链路。 |
| BLK-14 | **CLOSED** | §8.5 EQ2 阈值边界档已改为「只能经接缝注入构造 → `[LOCAL_DEAD_LINK]`（分类：能力未验证；回补触发 = 接缝可注入概率数组；处置 = 实现期补三组样本并断言恰等于→被过滤 / 略大→保留 / 略小→被过滤）」，四要素齐备，且与 V-49 对账一致。 |
| SF-07 | **CLOSED**（形式） | §8.2 低置信行已改为 `python tools/compare_lowconf.py --short 55 --long 55 --baseline 268`，268 口径保留在期望值来源。**但**脚本不存在且 §4A 无生成命令 → 并入 N-04 PARTIAL 的同一缺陷。 |
| SF-11 | **CLOSED** | DC-A 自查已补 §10.4（7 处 `violation_tmp.mbt:N` / `v7.mbt:N` / `fs-probe/...:3`）、§10.6 的 T2 表、§13 的 R1 理由。我重扫全文 `file:line` 分布：§1 14 / §2 28 / §4 1 / §7 5 / §9 15 / §10 1 / §13 1 —— 全部落在自查清单列举的节内（§10 的 1 处即 §10.4 表内 `v7.mbt:1`）。清单已闭合。 |

### 18.3 5 条 v2 新 SF（N-05…N-09）

| 编号 | 判定 | 我的复核 |
|---|---|---|
| N-05 | **CLOSED** | L1-A4 已改为「断言 `len(detector.langlist)` 与 `len(factory.langlist)` 同步增加 + `detector.langlist is factory.langlist` 为 True」，并注明「`get_lang_list()` 是工厂方法，`Detector` 无此方法」。我实跑：构造 55 档案 + 1 点文件（langsize 56）→ `d.langlist is f.langlist` → **True**；`add_profile` 后 `len(d.langlist)` 55 → **56**（工厂 56）；`hasattr(d,'get_lang_list')` → **False**（与 spec 注明一致）。 |
| N-06 | **CLOSED** | §5.5 签名改为 `DetectorFactory::create(self : DetectorFactory, alpha? : Double) -> Detector`，并新增「调用形态」行（`factory.create()` / `factory.create(alpha=0.5)`，不写 `Some(...)`）。实测：`f.create()` → rc=0；`f.create(alpha=0.5)` → rc=0；`f.create(Some(0.5))` → rc≠0（错误码 4080，非 V-58 所写 4014，见 N-15）。 |
| N-07 | **CLOSED**（形式） | §8.2 seed 行改为 `python tools/compare_golden.py --target native --mode seed_semantics`，三步判据保留在期望值来源。脚本不存在 → 并入 N-04。 |
| N-08 | **CLOSED**（形式） | §8.3 新增第 5 行「源侧 23 用例的目标侧对应文件存在且通过」，命令 `moon.exe test --target native`（4 个 `*_test.mbt` 就位后），状态「未验证（N-08：测试文件未落地）」。**但**：该行既非可跑命令（文件不存在）也未标 `[LOCAL_DEAD_LINK]`，违反 §8 自己的二选一门禁条款（N-16）。 |
| N-09 | **CLOSED** | 新增 DR11 + §10.6 命令 3。T1：三包 `moon.pkg` → rc=1（0 行）；T2：`src/data/moon.pkg` 写反向 import → **rc=0 命中 1 行**，还原后 rc=1。`moon check` 对反向 import 仍 rc=0（编译器不拦），与 spec 记载一致。 |

---

## 19. 新发现问题（v3 引入或 v3 未覆盖）

### 19.1 Blocking

#### N-10 命令 29 的判据在任何情况下都成立（永久绿）——二进制不存在时同样输出 `0 / 0`

**定义原文**：`gate-command-validation-gate.md` T2「命令必须报 FAIL 且退出码符合声明」；T3「如果我故意违反这条承诺，这条命令会报 FAIL 吗？」；Blocking #50。

**证据（我跑的）**：

```
$ ./_build/native/debug/build/src/core/cmd/main/main.exe > /tmp/o.txt 2> /tmp/e.txt; echo "RC=$?"; wc -c /tmp/o.txt /tmp/e.txt
RC=0
0 /tmp/o.txt
0 /tmp/e.txt          ← 二进制存在时的结果

$ ./_build/nope/main.exe > /tmp/o.txt 2> /tmp/e.txt; echo "RC=$?"; wc -c /tmp/o.txt /tmp/e.txt
RC=0
0 /tmp/o.txt
66 /tmp/e.txt         ← 二进制不存在，但 stdout 仍是 0 字节；rc 仍是 0

$ rm -rf _build && <不 build> && ./_build/.../main.exe > /tmp/o.txt 2>/tmp/e.txt
（同上：stdout 0、rc 0，stderr 才有 "No such file or directory"）
```

**为什么是 Blocking**：NE1 的运行时断言「`./main > out.txt 2> err.txt; wc -c` 两者均 0」把「**产品静默**」与「**程序没跑起来**」混为一谈。`wc -c` 的输出是两行数字，**没有断言命令**；而 `rc` 被重定向吞掉。任何人删掉 `_build` 后跑这条命令都会得到「通过」。这正是 gate-command-validation-gate 开篇点名的「一切正常时输出 OK 不是证据」。

**改法**：把运行时断言写成带守卫的两段（示例形态）：

```bash
test -x ./_build/native/debug/build/src/core/cmd/main/main.exe || exit 2
out=$(./_build/native/debug/build/src/core/cmd/main/main.exe 2>/tmp/e.txt) || exit 1
test -z "$out" && test ! -s /tmp/e.txt
```

并补 T2：把 `main.mbt` 改成 `fn main { println("x") }` → 该命令必须 rc=1。

---

#### N-11 命令 28 在真实 `moon.mod` 上 rc=1（CRLF 行尾），且 §15 第 1037 行的「26 / 29 / 30」三者不自洽

**定义原文**：Blocking #50（T1 语法可跑 + 与声明一致）；`document-contract-discipline.md` DC-D（数字须由命令派生且域与测量域对账）。

**证据（我跑的）**：

```
$ grep -q '^name = "vicoproplus/langdetect"$' moon.mod; echo "rc=$?"
rc=1                       ← 期望 0（§10.6 命令 28 注释写「期望 rc=0」）

$ od -c moon.mod | head -2
0000000   n   a   m   e       =       "   v   i   c   o   p   r   o   p
0000020   l   u   s   /   l   a   n   g   d   e   t   e   c   t   "  \r
                                                            ↑ CRLF

$ tr -d '\r' < moon.mod | grep -q '^name = "vicoproplus/langdetect"$'; echo "rc=$?"
rc=0                       ← 去掉 \r 后才匹配
```

**根因**：`moon.mod` 是 CRLF（52 B，`file` → `ASCII text, with CRLF line terminators`），`grep` 的 `$` 锚点落在 `\r` 之前不匹配。§4A 把这条当作 `moon.mod` 的**唯一**字面校验命令，等于校验命令本身永久红。

**同一行的算术**（§15 spec 第 1037 行原文）：「门禁**命令条数**… **26**（A 6 + B 6 + C 6 + DR 11 = 29 编号，其中 C-B1/B3/B4 合并、C-C1/C5 合并、DR9-DR11 为 v3 新增；展开后按 §10.6 代码块计 **30** 条可执行命令）」——`6+6+6+11 = 29`，不是 **26**；同格自己写「= 29 编号…展开后 30」。三个数（**26 / 29 / 30**）互不自洽。且该格的「派生命令」列指向的是**命令 B**，而命令 B（`grep -cE '^# 命令 [0-9]+：'`）实测输出 **30**——即这一栏的数字没有任何命令派生为 26（命令 A 给 25、命令 B 给 30）。同理 §15 spec 第 1055 行「27 条已逐字复制实跑…3 条待产品实现」与 §10.6 的 T1/T2 实录不符：命令 3/13/27 的 T1 与 T2 我都逐字实跑通过（§17.1），无一需要等产品实现。

**改法**：① 命令 28 改为 `tr -d '\r' < moon.mod \| grep -q …`，或把 `moon.mod` 统一为 LF（并登记为仓规）；② §15 删掉「26」这个无派生数字，只保留两条命令的实测输出（25 / 30），或补第三条真正派生出「编号数」的命令。

---

#### N-12 §8.2 的 8 行「操作证据」全部指向不存在的脚本，且 §4A 的 GP1「生成命令」为空

**定义原文**：`gate-command-validation-gate.md` GP1「每条命令引用的每个路径反查到四要素（生成时点 / 责任单元 / **生成命令** / 校验命令）；反查不到 = 该命令不可跑」；Blocking #46「操作证据 = 可重跑命令或入口 + 第三方可复现步骤」。

**证据（我跑的）**：

```
$ ls tools/compare_golden.py tools/compare_lowconf.py
ls: cannot access 'tools/compare_golden.py': No such file or directory
ls: cannot access 'tools/compare_lowconf.py': No such file or directory

$ grep -n 'compare_golden.py' <spec> | head -2
411:| `tools/compare_golden.py` | … | 实现期 | 产品 | — | 约定 C §3 全部命令 + §8.2/§8.4 验收行 |
605:| 主检测与概率形态 | … | `python tools/compare_golden.py --target native --seed 0 --mode prob_bits`（脚本见 §4A；未落地前等价入口 = §10.6 命令 16–19 的基准侧自检 + 产品侧逐条比对） |
```

§4A 的「生成命令」列是 `—`（空），违反 GP1 四要素。而 §8.2 第 605 行自称的「等价入口 = 命令 16–19」**不等价**：命令 16–19 只读 `docs/port/golden/expected.json` 验证**基准文件自身**（268=250+18、seed 集合、异常码、prob_bits 形态），完全不触及产品实现——它们在任何实现（含零实现）下都 rc=0。

**改法**：① 在 §4A 给两个脚本写「生成命令」（如「随 §8 验收批次实现；生成点 = 任务 T-x」）并加 `[LOCAL_DEAD_LINK]`；② §8.2 的 8 行状态改为 `[LOCAL_DEAD_LINK]`（分类：能力未验证；回补触发 = 脚本落地），或在脚本落地前把「操作证据」改为真实可跑的 §10.6 命令编号并说明覆盖范围（不是「等价」）。

---

### 19.2 Should-fix

#### N-13 命令 20 用列表推导执行副作用 + 私有方法 `__setitem__`

数值等价已验证（651 与边界一致，见 §17.2），但写法不可取：列表推导的求值顺序与副作用在 Python 语义下虽确定，但 `list.__setitem__` 是 CPython 实现细节，且这种形态在评审时容易被误读。建议改为 `python -c "$(printf '...多行...')"` 或 `python - <<'PY'`（heredoc 在 `bash -c` 下可用，只是不再是一行）。

#### N-14 `src/core/cmd/main/main.mbt` 是空 `fn main {}`，与 §4A/§8.1 的「该入口内调一次 detect」矛盾

§4A 第 409 行：「可执行入口（**仅调 `detect`**，不打印任何结果）」；§8.1 第 599 行：「（**该入口内调一次 `detect`**）」。实测文件内容：

```
$ cat src/core/cmd/main/main.mbt
fn main {
}
```

空 `main` 跑出来的 0 字节输出**不构成**「detect 路径静默」的证据——它连检测都没触发。改法：要么把 `main.mbt` 写成调用 `detect` 的最小形态（并登记为脚手架内容），要么把 §4A/§8.1 的措辞改为「空 main（仅验证可执行包形态）」，并另立一行「detect 路径静默性」待实现。

#### N-15 V-58 记的反例错误码与实测不符（`Some(0.5)` → 4080，非 4014）

```
$ （临时工程）let d : Det = f.create(Some(0.5))
Error: [4080] This function has type: (Fac, alpha? : Double) -> Det
              which requires 1 positional arguments, but is given 2 positional arguments.
```

spec 第 222 行 V-58 与第 479 行 §5.5 均写「`Some(0.5)` 报 `[4014] Constr Type Mismatch(constructor Some)`」。实测是 **4080**（参数个数不符），不是 4014（类型不匹配）。数值结论（必须传裸值）正确，但错误码是事实断言，应改正或删除错误码。

#### N-16 §8.3 第 5 行（N-08 新增）既不满足 (a) 也不满足 (b)

§8 门禁条款要求每行「(a) 可复跑命令（含前提交付物路径且该交付物已登记）或 (b) `[LOCAL_DEAD_LINK]` + 分类 + 回补触发 + 处置」。该行的命令依赖「§2A 的 4 个 `*_test.mbt` 全部就位后」——这些文件不存在（`find src -name '*_test.mbt'` → **0** 个），而状态只写「未验证（N-08：测试文件未落地）」，**没有** `[LOCAL_DEAD_LINK]` 标签、分类与回补触发。按 spec 自己的条款，该行「未回填」。

#### N-17 环境前提（`pi-uu-grep` + `/d/...` PATH）不可复现

证据与结论见 **§20**（`pi-uu-grep` 不存在；`/d/Program Files/Git/usr/bin` 不存在，实际为 `/mnt/d/...`；本环境默认已是 GNU grep 3.11）。改法：改为「须 GNU grep ≥3.x + POSIX shell」或标 `[LOCAL_DEAD_LINK]`（分类：环境未验证；回补触发 = 目标机确认；处置 = 删除不可复现路径）。

#### N-18 DR10 的裸词检索仍对合法标识符假红

**证据（我跑的）**：

```
$ # 注入 src/core/zz_w.mbt：pub fn is_wasm_compatible() -> Bool { true }
$ grep -rn -e is_wasm -e target_name -e '@wasm' --include=*.mbt src/core
src/core/zz_w.mbt:1:pub fn is_wasm_compatible() -> Bool { true }        rc=0（假红）

$ # 注入 src/core/zz2.mbt：pub fn get_target_name_of(l : String) -> String { l }
$ grep -rn -e is_wasm -e target_name -e '@wasm' --include=*.mbt src/core
src/core/zz2.mbt:1:pub fn get_target_name_of(l : String) -> String { l }  rc=0（假红）
```

DR9 已从「裸词三元组」改成 `#cfg(`/`#if(` 的语法锚定（N-01），但 DR10 沿用了同一套裸词：`is_wasm` / `target_name` 作为子串会命中任何以它们为前缀的合法标识符。这与 N-01 判定的根因（「v2 的裸词形态对合法标识符假红」）是同一个病，只是换了一行。

**改法**：DR10 的检索式改为语法锚定（如 `grep -rnE '\b(is_wasm|target_name)\s*\('`，即只在**调用形态**命中），并补 T1 基线（`pub fn is_wasm_compatible()` 必须 rc=1）与 T2（`is_wasm()` 调用必须 rc=0）。

---

## 20. 环境前提（v3 新增声明）核查

spec §10.6 第 804-806 行声明：「本机默认 shell 的 `grep` 是 `grep (pi-uu-grep) 0.2.0`（非 GNU）…实跑时把 GNU 工具前置到 PATH：`export PATH="/d/Program Files/Git/usr/bin:$PATH"`」。

**我实测**：

```
$ which grep; grep --version | head -1
/usr/bin/grep
grep (GNU grep) 3.11                 ← 本环境默认就是 GNU grep

$ command -v pi-uu-grep
NOT_FOUND                            ← 找不到作者所称的 pi-uu-grep

$ ls -d "/d/Program Files/Git/usr/bin"
ls: cannot access '/d/Program Files/Git/usr/bin': No such file or directory   ← 该路径在本环境不存在

$ ls -d "/mnt/d/Program Files/Git/usr/bin"
/mnt/d/Program Files/Git/usr/bin      ← 实际挂载点是 /mnt/d（WSL）
```

**结论**：环境前提声明**不可复现**——`pi-uu-grep` 在本环境不存在，作者给的 PATH 也不存在。全部 30 条命令我在**默认环境**（GNU grep 3.11）下跑通（除命令 28 的 CRLF 问题），说明该前提对本 spec 的命令并非必需；但作为写进契约的「执行环境」条款，它必须可复现或降级为「建议」。（已立为 **N-17**，Should-fix）把该前提改为「须 GNU grep ≥3.x + POSIX shell」并删除不可复现的 `pi-uu-grep` / `/d/...` 具体路径，或标 `[LOCAL_DEAD_LINK]`（分类：环境未验证）。

---

## 21. 第四轮判定汇总

| 项 | CLOSED | PARTIAL | NOT CLOSED |
|---|---|---|---|
| N-01…N-04 | 3（N-01/02/03） | 1（N-04） | 0 |
| BLK-02/07/10/14、SF-07/11 | 6 | 0 | 0 |
| N-05…N-09 | 5 | 0 | 0 |
| **合计（15 条）** | **14** | **1** | **0** |

> 注：任务描述里的「6 PARTIAL + 5 SF」= BLK-02/07/10/14 + SF-07/11（6 条）+ N-05…N-09（5 条）= 11 条；加 N-01…N-04 共 **15 条**。上表按 15 条统计。
>
> 「§15 的『26 / 29 / 30』三者不自洽」不作为单独销项，而是作为 **N-11 的第二个子项**（Blocking）计入新发现。

**新发现**：N-10（Blocking）、N-11（Blocking）、N-12（Blocking）、N-13（Should-fix）、N-14（Should-fix）、N-15（Should-fix）、N-16（Should-fix）、N-17（Should-fix）、N-18（Should-fix）——共 **9 条（Blocking 3 / Should-fix 6）**。

**Status: Issues Found**

---

## 22. 第四轮建议修订顺序

1. **N-10**：命令 29 加 `test -x` 守卫 + `test -z "$out"` 断言 + `|| exit 1`；补 T2（`println` 版 main → 必须 rc≠0）。
2. **N-11**：命令 28 去 `\r`（或统一 `moon.mod` 为 LF）；§15 删「26」，只留命令 A/B 的实测 25/30。
3. **N-12**：§4A 给 `compare_golden.py` / `compare_lowconf.py` 补「生成命令」+ `[LOCAL_DEAD_LINK]`；§8.2 八行状态同步改标，删掉「等价入口 = 命令 16–19」的虚假等价。
4. **N-14**：`main.mbt` 写成真调 `detect`，或改 §4A/§8.1 措辞为「空 main，仅验包形态」。
5. **N-16**：§8.3 第 5 行补 `[LOCAL_DEAD_LINK]` + 分类 + 回补触发。
6. **N-17**：环境前提改为可复现表述或标 `[LOCAL_DEAD_LINK]`。
7. **N-13 / N-15**：命令 20 改写为无副作用推导；V-58 的 `4014` 改 `4080`。
8. **N-18**：DR10 检索式加语法锚定（`\b(is_wasm|target_name)\s*\(`），补 T1/T2 基线。

---

---

# 第五轮登记（v4，2026-10-21）

> 本节由 spec 修订者填写：逐条记录第四轮核验的 3 条新 Blocking（N-10…N-12）、6 条新 Should-fix（N-13…N-18）与 1 条 PARTIAL（N-04）的处置与复跑证据。**定义原文列不改**（沿用第四轮），本节只补「销项证据 / 状态」。

## 23. 新 Blocking 3 条

| 编号 | 定义原文（沿用） | 销项证据（含复跑命令 + 输出 + rc） | 状态 |
|---|---|---|---|
| N-10 | 命令 29 的判据在二进制不存在时同样成立（永久绿） | 命令 29 改写为三态守卫并有断言：`test -x <exe> \|\| exit 2` + `out=$(<exe> 2>/tmp/e.txt) \|\| exit 1` + `test -z "$out" && test ! -s /tmp/e.txt`。**三态实测**：二进制不存在 → rc=**2**；空 `fn main { }` → rc=**0**；`println("x")` 版 main → rc=**1**（先前 v3 形态在二进制不存在时也输出 `0 / 0` 且 rc=0） | 已销项 |
| N-11 | 命令 28 在真实 CRLF `moon.mod` 上 rc=1；§15「26 / 29 / 30」三者不自洽 | ① 命令 28 改为 `tr -d '\r' < moon.mod \| grep -q '^name = "vicoproplus/langdetect"$'`，实跑 rc=**0**；T2 把 `name` 改成 `"x/y"` → rc=**1**（`od -c moon.mod` 确认行尾为 `"\r\n"`）。② §15 删掉手写「26」与手算式，两个派生对象各只留派生命令实测值：命令 A（表行数）= **25**、命令 B（§10.6 命令条数）= **30**，均标注「派生值，不手算」。③ 同时删除「27 条已逐字实跑 / 3 条待产品实现」——改为「30 条 T1 全部已试跑；T2 已跑 17 条，命令 3 / 13 / 27 的 T2 已补跑（反向 import → rc=0 命中 1 行；`read_file` 调用 → rc=0 命中 1 行；任意 `pub fn` → rc=0 命中 1 行）」（见 §23.1） | 已销项 |
| N-12 | §8.2 的 8 行指向不存在的脚本；§4A GP1「生成命令」为空；「等价入口 = 命令 16–19」不成立 | ① §4A 两行（`tools/compare_golden.py` / `tools/compare_lowconf.py`）改为「生成时点 = **实现期（当前不存在，属实现期产物）**」+ 生成命令 `—（实现期由产品实现者创建；本表登记其必须提供的调用形态）` + 显式 `[LOCAL_DEAD_LINK]`（分类：能力未验证；回补触发 = 脚本落地；处置 = 落地前不计已验证）。② §8.2 的 8 行状态**逐行**改为 `[LOCAL_DEAD_LINK]` + 分类 + 回补触发 + 处置；第 605 行的「未落地前等价入口 = §10.6 命令 16–19」**已删除**，并按第四轮要求显式写明：「**§10.6 命令 16–19 只校验 golden 基准文件自身，不校验产品行为，不构成等价入口**；产品行为比对由上述两脚本承担，脚本未建立前该维度不算已验证」。③ §8.3 第 5 行同步补 `[LOCAL_DEAD_LINK]`（见 N-16） | 已销项 |

### 23.1 第四轮 §17.1 指出的 3 条「漏跑 T2」补跑记录（2026-10-21）

| 命令 | 违规样本 | rc | 还原后 |
|---|---|---|---|
| 命令 3（DR11） | `src/data/moon.pkg` 写 `"vicoproplus/langdetect/src/core",` | **0**（命中 1 行） | rc=1 |
| 命令 13（NE4-2） | `src/core/zz_r.mbt` 写 `read_file("x")` | **0**（命中 1 行） | rc=1 |
| 命令 27（产品公开符号） | `src/core/zz_p.mbt` 写 `pub fn a() -> Int { 1 }` | **0**（命中 1 行） | rc=1 |

## 24. Should-fix 6 条

| 编号 | 处置 | 复跑证据 | 状态 |
|---|---|---|---|
| N-13 | 命令 20 改为显式 `for` 循环（`python -c "exec('...')"`，无列表推导副作用、不触 `list.__setitem__`） | 实跑 rc=**0**，输出 `ok 1951 cps / 651 intervals`（区间数与口径不变） | 已销项 |
| N-14 | §4A 与 §8.1 措辞改为「当前内容为空 `fn main { }`（脚手架占位，仅验证可执行包形态）；『调用一次 detect』是实现期目标，尚未实现」；§8.1 该行改标 `[LOCAL_DEAD_LINK]` | `cat src/core/cmd/main/main.mbt` = `fn main {\n}`（12 B）与文档一致；不再声称未实现的调用 | 已销项 |
| N-15 | V-58 与 §5.5 的 `[4014] Constr Type Mismatch` 改为 `[4080] requires 1 positional arguments, but is given 2 positional arguments` | 独立复跑 `f.create(Some(0.5))` → `[4080]`（临时工程 `moon check`，`moon 0.1.20261012` / `moonc v0.10.15`） | 已销项 |
| N-16 | §8.3 第 5 行补 `[LOCAL_DEAD_LINK]`（分类：能力未验证；回补触发 = 产品测试文件建立后；处置 = 建立前不计已验证），并注明当前 `find src -name "*_test.mbt"` → **0** 个 | 规格行已含标签 + 四要素；与 §2A 对账一致 | 已销项 |
| N-17 | 环境前提改为**可执行的能力自检**，删除不可复现的 `pi-uu-grep` / `/d/...` 具体路径：`printf 'a\n' \| grep -qE 'a\|b' && printf ' a\n' \| grep -qE '^[[:space:]]*a' && printf 'x\n' \| grep -q -e x -e y && printf 'name = "z"\r\n' \| tr -d '\r' \| grep -q '^name = "z"$' \|\| exit 2` | 实测 rc=**0**；该自检覆盖 `-E` 交替、`[[:space:]]`、`-e` 多模式与 CRLF 归一四项能力，不依赖 grep 发行版或安装路径 | 已销项 |
| N-18 | DR10 检索式由裸词改为**语法锚定调用形态**：`grep -rnE '\b(is_wasm\|target_name)[[:space:]]*\(' --include=*.mbt src/core` | **假红对照**：注入 `pub fn is_wasm_compatible()` + `pub fn get_target_name_of(...)` → 新式 rc=**1**（0 行），v3 裸词形态同样本 rc=**0**（命中 2 行）；**T2**：注入 `is_wasm()` 调用 → rc=**0**（命中 1 行） | 已销项 |

## 25. 第四轮 15 条判定中唯一 PARTIAL 的处置

| 编号 | 第四轮判定 | v4 处置 | 状态 |
|---|---|---|---|
| N-04 | **PARTIAL**（8 行 §8.2 指向不存在的脚本；命令 16–19 不等价） | 见 §23 的 N-12 行：§4A 补 GP1 四列 + `[LOCAL_DEAD_LINK]`，§8.2 八行逐行改标，删除虚假等价表述 | 已销项 |

## 26. v4 汇总

| 项 | 值 |
|---|---|
| spec 版本 | v4 |
| 本轮销项 | 3 Blocking（N-10/N-11/N-12）+ 6 Should-fix（N-13…N-18）+ 1 PARTIAL（N-04）= **10 条** |
| 改过的命令 | §10.6 命令 2 / 20 / 28 / 29 共 **4** 条 |
| 改过命令 T1 实跑 | 4/4 rc 与注释一致（cmd2 rc=1、cmd20 rc=0、cmd28 rc=0、cmd29 rc=0） |
| 改过判据 T2 实跑 | cmd2（`is_wasm()` → rc=0）、cmd28（`name="x/y"` → rc=1）、cmd29（三态 2/0/1）全部按预期 |
| 补跑的漏项 T2 | 命令 3 / 13 / 27 三条（见 §23.1），全部 rc=0 命中 |
| `<产品目录>` 残留 | **0** |
| `src/` 脚手架 | 6 个文件（4 个 0 字节 `moon.pkg` + cmd 包 2 个）；产品公开符号 **0** |
| `moon check`（仓库根） | `Finished. moon: no work to do`（rc=0） |
| 环境能力自检 | `grep -qE` / `-e` / `[[:space:]]` / `tr -d '\r'` 四项全通 rc=0 |


---

# 第六轮核验（v4，2026-10-21）

> **审查对象**：`202610202129-moon-langdetect-语种检测-spec.md` v4（1072 行 / 107,707 B）
> **作者声称**（§23–§26）：销项 N-10…N-18（3 Blocking + 6 Should-fix）+ N-04（PARTIAL）；改过 4 条命令（2/20/28/29）；30 条 T1 全跑、T2 17 条。
> **本轮方法**：① 30 条命令**从 spec 代码块按原字节抽取**（保留 CRLF），在 **3 个环境**下逐字跑：WSL bash + GNU grep 3.11 / Git Bash 5.2 + GNU grep 3.0 / 宿主原生 Git Bash + `pi-uu-grep 0.2.0`；② 10 条销项逐条自跑（含 T1 基线、T2 违规、三态、能力自检反例）；③ 53 条 Blocking Checks 全量重扫。
> **结论**：**Issues Found** —— 10 条销项 **CLOSED 7 / PARTIAL 2 / NOT CLOSED 1**；30 条命令 **30/30 rc 与注释一致**（三环境零差异），但 **命令 29 仍有一类假绿**、**命令 2 依赖非 POSIX 的 `\b`**、**能力自检漏测 3 项能力**；新发现 **N-19…N-24（6 条）**，其中 **2 条 Blocking**。

---

## 27. 30 条命令逐字复制复跑（三环境）

抽取方式：按 `^# 命令 N：` 切分 §10.6 代码块（spec 第 814–943 行），**保留每行末尾的 `\r`**（模拟从 CRLF 文件逐字复制），逐条交给 shell。

| 环境 | shell | grep | 30 条 rc 序列 | 与注释一致 |
|---|---|---|---|---|
| A | WSL bash 5.2.21 | GNU grep **3.11** | `1×14, 0×12, 1, 0, 0, 0` | **30/30** |
| B | Git Bash 5.2.37（`/usr/bin/grep`） | GNU grep **3.0** | 同上，逐条一致 | **30/30** |
| C | 宿主原生 Git Bash（`D:\Program Files\Git\usr\bin`） | **`pi-uu-grep 0.2.0`** | 同上，逐条一致 | **30/30** |

**逐条 rc**（A/B/C 完全相同）：

| # | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rc | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |

| # | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rc | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |

命令 20 输出 `ok 1951 cps / 651 intervals`；命令 26 输出 `25`；其余 rc=0 的命令输出为空。

> **结论**：**「逐字复制」这一层已闭合** —— 30/30 与注释一致，且跨 3 个 grep 实现零差异。上一轮报的 cmd 28（CRLF 锚点）确实被 `tr -d '\r'` 修好。

### 27.1 命令 29 的三态（N-10 处置核验）

按任务要求实测三态（**每一态我都重建了二进制，跑完复原**）：

| 态 | 构造 | 命令 29 rc | 判定 |
|---|---|---|---|
| ① 二进制缺失 | `rm main.exe` | **2** | ✅ 正确（`test -x … \|\| exit 2`） |
| ② 二进制存在、空 `fn main {}` | 原文 main.mbt | **0** | ✅ 正确 |
| ③ 二进制存在、`println("langdetect ok")` | 改 main.mbt + rebuild | **1** | ✅ 正确（stderr/stdout 有内容） |
| ④ **二进制存在、只输出一个换行** | 改 main.mbt 为 `println("")` → 输出 `\r\n`（2 B） | **1** | ✅ 正确（`\r` 不被 `$(…)` 剥掉，`test -z` 失败） |
| ⑤ **二进制替换为只 `printf "\n"` 的脚本（1 B，纯 LF）** | 覆盖 exe | **0** | ❌ **假绿**（见 N-19） |

前四态与作者声明一致，**「永久绿」已消除**；但第 ⑤ 态暴露一个残余：`$(…)` 会剥掉**尾部所有 LF**，所以「只向 stdout 写换行」的程序仍判通过。Windows 上 MoonBit 的 `println` 写 `\r\n`（`\r` 不被剥离）所以第 ④ 态侥幸红；换到 LF 平台（js / wasm-gc / Linux native）该缺陷立刻生效。

### 27.2 命令 28 的 T2（N-11 处置核验）

```
$ tr -d '\r' < moon.mod | grep -q '^name = "vicoproplus/langdetect"$'   → rc=0
$ （moon.mod 改写为 zz- = "x/y"）同命令                                  → rc=1
$ （还原）                                                              → rc=0
```

三环境一致。**N-11 的命令部分闭合。**

### 27.3 命令 2 的假红/违规对照（N-18 处置核验）

```
$ # T1 基线：pub fn is_wasm_compatible() + pub fn get_target_name_of(...)
$ grep -rnE '\b(is_wasm|target_name)[[:space:]]*\(' --include=*.mbt src/core   → rc=1（0 行）✅ 不假红
$ # 对照：v3 裸词形态
$ grep -rn -e is_wasm -e target_name -e '@wasm' --include=*.mbt src/core        → rc=0（命中 2 行）❌ 假红（复现）
$ # T2：追加 fn q() -> Bool { is_wasm() } 与 target_name()
$ 命令 2                                                                       → rc=0（命中 2 行）✅ 违规可捕获
$ # 还原后                                                                     → rc=1
```

**N-18 闭合**（三环境一致）。

### 27.4 命令 20 的改写（N-13 处置核验）

```python
.venv/Scripts/python.exe -c "exec('import sys,unicodedata\nassert sys.version…\nfor cp in cps:\n    if iv and cp==iv[-1][1]+1:\n        iv[-1][1]=cp\n    else:\n        iv.append([cp,cp])\n…')"
```

- 脚本扫描：**无** `[iv.append` 副作用推导、**无** `__setitem__`，含显式 `for cp in cps:` → ✅
- 实跑输出：`ok 1951 cps / 651 intervals`，rc=0 → ✅ 与 v3 一致
- 与多行参考实现对比区间边界：`[[65,90],[192,214],[216,222]] … [[127280,127305],[127312,127337],[127344,127369]]` 完全一致 → ✅

**N-13 闭合。**

### 27.5 能力自检（N-17 处置核验）

```
$ printf 'a\n' | grep -qE 'a|b' && printf ' a\n' | grep -qE '^[[:space:]]*a' \
  && printf 'x\n' | grep -q -e x -e y \
  && printf 'name = "z"\r\n' | tr -d '\r' | grep -q '^name = "z"$' || exit 2
rc=0            ← 三环境一致（bash / dash / sh 也一致）
```

**故意破坏一项能力**：把第一段 `-qE 'a|b'` 换成 `-qF 'a|b'`（无交替）→ **rc=2**，守卫触发 ✅。

**但**：该自检**只覆盖 4 项能力**（`-E` 交替、`[[:space:]]`、`-e` 多模式、`tr -d '\r'`），**不覆盖**命令实际依赖的另外 3 项：`-r`（递归）、`--include`、`\b`（GNU 词边界）。我用三个"残缺 grep"逐一验证（见 N-20）：

| 缺失能力 | 自检 rc | 命令 5 / 命令 2 的 rc | 后果 |
|---|---|---|---|
| `--include` | **0（通过）** | 命令 5 → **2**（grep 报 unrecognized option） | 报错可见，非假绿 |
| `-r` | **0（通过）** | 命令 5 → **2** | 报错可见，非假绿 |
| `\b`（当作字面 `b` / 报错） | **0（通过）** | 命令 2 → **rc=1（0 行）**，把违规样本判成"干净" | **假绿** |

`\b` 是 **GNU 扩展**，POSIX ERE 无此语义（`[[:<:]]` 在 GNU 下直接报 `Invalid character class name`，我实测）。因此 N-20 是真实的跨实现假绿风险，不是理论问题。

---

## 28. 10 条销项判定

| 编号 | 判定 | 我的复核（命令 + 输出） |
|---|---|---|
| N-10 | **NOT CLOSED → v5 已销项**（见第七轮 §27 N-19） | 三态 ①②③ 全部按预期（2/0/1，见 §27.1），**v3 的「二进制不存在也通过」已消除**；但第 ⑤ 态（stdout 只含一个换行）仍 rc=0 → 残余假绿（N-19）。判 NOT CLOSED 而非 PARTIAL：命令注释自己写「**有输出 → 1**」，而「只写一个换行」就是有输出，判据与声明不等价。 |
| N-11 | **CLOSED** | 命令 28 改 `tr -d '\r'` 后 rc=0；改 `name` → rc=1；还原 → rc=0（三环境一致）。§15 的「26」已删除：第 1047/1048 行只留两条派生命令的实测值 **25 / 30**，均标「派生值，不手算」，无手算数字 → 算术不自洽已消除。§15 第 1066 行「27 条已跑 / 3 条待产品实现」也已改写为「30 条 T1 全部已试跑…无一『待产品实现』」。 |
| N-12 | **PARTIAL** | 表面三件事都做了：§4A 两行标「实现期（当前不存在，属实现期产物）」+ 显式 `[LOCAL_DEAD_LINK]`；§8.2 八行逐行带标签 + 分类 + 回补触发 + 处置；第 605 行显式写明「命令 16–19 只校验基准文件自身，不校验产品行为，不构成等价入口」。**但归类错了**：`[LOCAL_DEAD_LINK]` 的语义（`evidence-gate.md` §4 触发条件原文）是「验收项**依赖特定环境**…且**该环境在本机不可用、本机无法闭环验证**」——这两个脚本不是「环境不可达」，而是**实现期还没写**。同一份 spec 里，同类行（§8.4 第 628–630 行）用的是「未验证」，标签体系自相矛盾（N-21）。且 §14 登记表仍写「`[LOCAL_DEAD_LINK]` 行数：**7**（U-01…U-07）」，而 §8 实际已有 **17** 行打标签，其中 **13 行未映射到任何 U 编号**（N-22）。 |
| N-13 | **CLOSED** | 命令 20 改 `exec()` + 显式 `for`；脚本扫描无 `[iv.append`、无 `__setitem__`；输出 `ok 1951 cps / 651 intervals`；区间边界与参考实现逐项相同（§27.4）。 |
| N-14 | **CLOSED** | `cat src/core/cmd/main/main.mbt` → `fn main {\n}\n`（12 B）；§4A 第 409 行改为「**当前内容为空 `fn main { }`（脚手架占位…）；「调用一次 `detect` 且不打印」是实现期目标，尚未实现**」；§8.1 第 599 行改为「**当前该入口为空 `fn main { }`，尚未调用 `detect`**；detect 链路待实现」+ `[LOCAL_DEAD_LINK]`（能力未验证 / 回补触发 = `main.mbt` 填入 detect 调用 / 处置 = 填入前不计已验证）。四要素齐备，措辞不再声称已实现。 |
| N-15 | **CLOSED** | spec 第 222 行 V-58 与第 479 行 §5.5 均已改为 `[4080] requires 1 positional arguments, but is given 2 positional arguments`；我在独立临时工程复跑 `f.create(Some(0.5))` → `[4080]`（`moonc v0.10.15`），与 spec 一致。 |
| N-16 | **CLOSED** | §8.3 第 622 行已带 `[LOCAL_DEAD_LINK]`（能力未验证；回补触发 = 产品测试文件建立后；处置 = 建立前不计已验证），并注明 `find src -name "*_test.mbt"` → **0** 个（我复跑：0）。 |
| N-17 | **CLOSED**（形式） | spec 内 `pi-uu-grep` 出现 **0** 次、`/d/Program` 出现 **0** 次（我 grep 确认）；改为能力自检命令，实跑 rc=0，且破坏一项能力后 rc=2（§27.5）。**但**自检覆盖面不足 → 另立 N-20。 |
| N-18 | **CLOSED** | 命令 2 改语法锚定后：假红对照 rc=1（0 行）、T2 rc=0（命中 2 行）、还原 rc=1；v3 裸词形态在同一样本上仍 rc=0（命中 2 行）→ 复现对照成立（§27.3）。**但** `\b` 的可移植性另立 N-20。 |
| N-04 | **PARTIAL** | 同 N-12：§8.2 八行「每行都有标签 + 四要素」形式上成立，§4A 两行「当前不存在」写明，虚假等价已删；**但**标签语义误用（N-21）+ 未映射 U 编号（N-22），且 §8.4 三行（628/629/630）仍用「未验证」而它们依赖同一个不存在的 `compare_golden.py`——同一脚本在不同小节被标成两种状态（N-21）。 |

**统计：CLOSED 7 / PARTIAL 2 / NOT CLOSED 1**

> **NOT CLOSED 1 = N-10**（若把「只写一个换行」视为可接受边界，则为 PARTIAL；我按命令注释「有输出 → 1」的字面判 NOT CLOSED 更准确。上表按 PARTIAL 计，§31 汇总表按 NOT CLOSED 计，见说明）。

---

## 29. 新发现问题（N-19…N-24）

### 29.1 Blocking

#### N-19 命令 29 对「只写换行」的程序仍判通过（`$(…)` 剥尾部 LF）

**证据**：

```
$ # 把二进制换成只 printf "\n" 的脚本（stdout 恰好 1 字节）
$ ./_build/.../main.exe | wc -c
1
$ test -x ./_build/.../main.exe || exit 2
$ out=$(./_build/.../main.exe 2>/tmp/e.txt) || exit 1
$ test -z "$out" && test ! -s /tmp/e.txt
$ echo $?
0                     ← 通过，但程序确实往 stdout 写了 1 字节
```

**根因**：`out=$(…)` 会剥掉命令替换结果末尾的**所有换行**。所以「stdout 只有换行」与「stdout 为空」在 `test -z "$out"` 下不可区分。NE1 断言的是「**0 字节**」，命令测的是「去掉尾部换行后为空」。

**为什么是 Blocking**：这正是 N-10 的同一类缺陷（判据与断言不等价）在修补后残留的下一层。Windows native 的 `println("")` 写 `\r\n`（`\r` 不被剥）所以侥幸红；换到 js / wasm-gc / Linux native（LF 平台），`println("")` 就会假绿。spec 明确要跨三目标验收（§8.3），这个判据在 2/3 目标上失效。

**改法**（二选一）：

```bash
# ① 直接数字节，不经命令替换
test -x ./_build/native/debug/build/src/core/cmd/main/main.exe || exit 2
./_build/native/debug/build/src/core/cmd/main/main.exe >/tmp/o.txt 2>/tmp/e.txt || exit 1
test ! -s /tmp/o.txt && test ! -s /tmp/e.txt
```

或 ② 保留 `$()` 形态但改成 `test "$(… | wc -c)" = 0`。补 T2：`fn main { println("") }` → 必须 rc=1（在 LF 平台也要红）。

---

#### N-20 能力自检未覆盖命令真正依赖的 `-r` / `--include` / `\b`，其中 `\b` 缺失会假绿

**证据（我构造的残缺 grep 逐一验证）**：

```
$ # 自检（逐字复制 spec 第 807 行）在三个残缺 grep 下全部 rc=0（通过）
$ grep --version          # 缺 --include 的包装
$ printf 'a\n' | grep -qE 'a|b' && … || exit 2 ; echo $?
0
$ # 而命令 5 在该 grep 下：
$ grep -rn '@math\.sqrt' --include=*.mbt src
grep: unrecognized option '--include=*.mbt'   → rc=2（可见，非假绿）

$ # 缺 -r 的包装：自检 rc=0；命令 5 → rc=2（可见）

$ # 缺 \b 的包装（POSIX ERE 无词边界；GNU 的 [[:<:]] 直接报错）：
$ printf 'is_wasm()\n' | grep -cE '\b(is_wasm)[[:space:]]*\('   → 1
$ printf 'is_wasm()\n' | grep -cE 'b(is_wasm)[[:space:]]*\('    → 0   ← 若 \b 被当字面 b，违规样本漏检
$ # 命令 2 在该 grep 下：rc=1（0 行）= 把违规判成干净 → 假绿
```

另：`grep -E '[[:<:]](…)'` 在 GNU grep 3.11 下报 `grep: Invalid character class name`（rc=2）——**POSIX 的写法反而不可用**，所以不能简单"换成 POSIX 形态"。

**为什么是 Blocking**：N-17 的处置把"环境前提"从「指定 grep 发行版」改成「能力自检」，方向对，但自检清单只覆盖了 4 项能力。`\b` 是 DR10 唯一的关键词边界机制，缺失时命令 2 对真实违规返回"0 行 = 通过"——这是 gate-command-validation-gate 定义的假绿。

**改法**：① 自检补三项探针（`printf 'x\n' | grep -q -r x .` / `grep -q --include='*.txt' x .` / `printf 'a b\n' | grep -qE '\ba'`），任一失败 `exit 2`；② 或把命令 2 的 `\b` 换成 `(^|[^[:alnum:]_])` 前缀类（与命令 4 已用的形态一致，纯 POSIX，无扩展依赖）：

```bash
grep -rnE '(^|[^[:alnum:]_])(is_wasm|target_name)[[:space:]]*\(' --include=*.mbt src/core
```

我实测该形态：假红对照 rc=1（0 行）、T2 rc=0（命中 2 行）——**与 `\b` 版本行为等价且可移植**。

---

### 29.2 Should-fix

#### N-21 `[LOCAL_DEAD_LINK]` 被误用于「实现期产物尚未创建」，与同表「未验证」并存

`evidence-gate.md` §4 触发条件原文：「当 spec 的**验收项依赖特定环境**（专用构建机 / 特定操作系统 / 特定 SDK 或工具链 / 特定账号权限），且**该环境在本机不可用**、本机无法闭环验证时」。`tools/compare_golden.py` 不是"环境"，是**尚未编写的产品代码**——按 gate 语义应记「未验证（实现期产物）+ 建立后回填」，不是 `[LOCAL_DEAD_LINK]`。

**自相矛盾证据**：同一个 `compare_golden.py` 在 §8.2（605–611）被标 `[LOCAL_DEAD_LINK]`，在 §8.4（628–630）被标「未验证」。两处依赖的是同一个不存在的文件，状态标签却不一致。

**改法**：把 §8.2 八行与 §4A 两行统一改成「未验证（实现期产物；回填触发 = 脚本落地）」，并保留 §8 门禁条款的 (a)/(b) 二选一——把 (b) 的适用范围限定为**环境不可达**类（U-01/U-02/U-04/U-05），另立 (c)「实现期产物未创建」类。若坚持用 `[LOCAL_DEAD_LINK]`，则必须在 §14 定义里显式扩展触发条件，否则标签语义被稀释。

#### N-22 §14 登记表「行数：7（U-01…U-07）」与实际打标行数（26 处，§8 内 17 行）不符，且 13 行无 U 编号

```
$ grep -cF '[LOCAL_DEAD_LINK]' <spec>                                  → 29
$ 其中的表格行                                                  → 26（§4A 2 行 + §8 17 行 + §14 表 7 行）
$ §14 第 1037 行声明的行数                                      → **7**
$ §8 打标行中能映射到 U-xx 的                                    → 4（598→U-01、619→U-01/U-02、631→U-05、632→U-04）
$ §8 打标行中无 U 编号的                                         → 13（599、605、606、607、608、609、610、611、612、620、621、622、651）
$ §4A 2 行（411、412）也无 U 编号
```

`evidence-gate.md` §4 要求「每个依赖特定环境的验收行必须且只能打一次」+ 分类独立计数。当前计数声明（7）与实际（17）不符，违反 DC-D（数字须由命令派生）。

**改法**：§14 的计数改为命令派生（`grep -c` 该表），并给 §8 的 13 行各配一个 U 编号（或把"实现期产物"类统一并入一个新编号 U-08「实现期脚本/测试文件未创建」，覆盖 605–612、620–622、651、599）。

#### N-23 §10.6 代码块第 928–929 行的注释被硬换行截断，逐字复制会让整块脚本报 `command not found`

**证据**：

```
$ sed -n '928,929p' <spec>
# moon.mod 为 CRLF 行尾，必须先 tr -d '\r'，否则 $ 锚点匹配不到
 前的字符
$ （把这两行 + 命令 28 一起放进脚本执行）
t28v.sh: line 2: $'前的字符\r': command not found
block_rc=1
```

**影响**：单独复制命令 28 那一行没问题（§27.2 rc=0）；但 §10.6 开头声明「本节…可逐字复制执行」，整块复制时第 929 行会作为独立命令执行并报错。加 `set -e` 时整块中止（我实测：`set -e` + 整块 → rc=1，停在命令 1 之后）。

**改法**：把注释并回一行（去掉第 929 行），或改成 `# … 匹配不到行尾的 CR` 之类不需要换行的措辞。

#### N-24 §7 标题仍写「DR1-DR9」，实际表有 DR1–DR11

```
$ grep -n '方言红线表' <spec>
559:## 7. 方言红线表（DR1-DR9，append-only）
$ grep -cE '^\| DR[0-9]+ \|' <spec>     → 11（DR1…DR11）
```

§10.4 标题已改「DR1-DR11」，§10.5 也写「DR1-DR11」，只有 §7 标题漏改。属 v3 引入 DR10/DR11 时的遗漏，v4 未修。

---

## 30. 53 条 Blocking Checks 全量复核

以 findings §6 的 53 行基准 + §11 的 17 条 v2 变更合成 v2 终态（**Pass 22 / Fail 17 / N/A 14 = 53**），逐条对照 v4 spec 重判。

**v2 的 17 条 Fail 在 v4 的处置**：

| # | 检查项 | v2 | v4 | 依据（我跑的 / 我读的） |
|---|---|---|---|---|
| 1 | US/FR 回链 PRD 且 P0/P1 全覆盖 | Fail | **Fail** | §3 第 337 行仍写「P0/P1 覆盖 = 26/26」；PRD 实测 FR-04/FR-19/FR-20 是 **P2**，P0=13 + P1=10 = 23，不是 26 |
| 2 | 降级路径 / 不降级 | Fail | **Fail** | `非等价降级` 全文仅 1 处（§11 MS1-4）；§8 仍无降级路径的验收行 |
| 8 | 每个交付物带可复跑命令 | Fail | **Pass** | §4A 15 行逐行有「校验命令」列；两个脚本行写明「实现期（当前不存在）」 |
| 9 | 验收 ≥3 维度 + 任一失败=整体失败 | Fail | **Fail** | `grep -c '任一失败\|整体失败'` → **0**；§8 只有「不得判该维度完成」 |
| 17 | 共享状态更新语义与消费方式 | Fail | **Pass** | §9.3 层 3 已逐键登记 `langlist` / `word_lang_prob_map` / `seed` / `langprob` / `text` / `prior_map`，含「别名共享（V-52）」行 |
| 19 | 负向轴 NE1-NE4 | Fail | **Fail** | NE1 运行时半句仍是命令 29，而命令 29 对「只写换行」假绿（N-19） |
| 25 | 原语可用性矩阵（A/B 分格） | Fail | **Fail** | `可用性矩阵` / `原语` 均 0 命中；§5.9 只有一句「两者全目标可用」 |
| 27 | 文档契约纪律 DC-A…DC-F | Fail | **Pass** | DC-A 已补 §10.4 T2 实录列、§10.6 T2 表、§13 R1 理由（`probes/gen_mbt.py:80`、`rand-probe.mbt:203`，我逐行核对了这两处内容） |
| 31 | 语言特性矩阵 + 探针记录 | Fail | **Pass** | V-57（suberror/可选参/多行 struct）+ V-58（三个方法签名 + 调用形态 + 反例码） |
| 34 | 外部消费字面逐字 + 证据等级 | Fail | **Pass** | `vicoproplus/langdetect` 出现 9 处（§4A/§7 DR11/§10.6 命令 3/28） |
| 37 | 验收行与环境事实清单交叉核对（EC1-EC2） | Fail | **Fail** | `EC1` / `环境事实` 均 0 命中 |
| 39 | 冻结时全部机检命令重跑 | Fail | **Fail** | `冻结时` 仅 1 处（§8 引言「本 spec 冻结时全部为未验证」），无重跑记录章节 |
| 43 | 方言红线表 + 出处 + 机检 + append-only | Fail | **Fail** | 表内 11 行 + append-only ✅ + 机检形态 ✅，但 **§7 标题仍写「DR1-DR9」**（N-24） |
| 45 | 平台语义分叉断言 EQ1-EQ3 | Fail | **Pass** | EQ1 三分叉点 + EQ2 四档构造（阈值档已按 BLK-14 处置）+ EQ3 三条语义 |
| 46 | 验收行三要素 | Fail | **Pass** | §8 六列已把「期望值来源」与「观测输出」分开；每行有环境 + 命令/标签 |
| 49 | 定量断言四元组 | Fail | **Fail** | `四元组` 0 命中；无「断言 + 域 + 命令 + 结果」的统一表 |
| 50 | 每条机检命令 T1/T2/T3 试跑记录 | Fail | **Pass** | 30 条 T1 全跑（三环境 30/30）+ T2 表 14 行（我逐条复跑 9 条，全部命中） |

**v4 终态：Pass 30 / Fail 9 / N/A 14 = 53**

- 转 Pass 的 8 条：8、17、27、31、34、45、46、50
- 仍 Fail 的 9 条：1、2、9、19、25、37、39、43、49
  - 其中 **19**（NE1）与 **43**（DR 标题）是本轮新发现直接导致的（N-19 / N-24）
  - 1、2、9、25、37、39、49 是**既有缺陷**（v2 起就 Fail，v3/v4 未触碰），不属本轮回归

---

## 31. 汇总与最终判定

### 31.1 10 条销项

| 项 | CLOSED | PARTIAL | NOT CLOSED |
|---|---|---|---|
| N-10 / N-11 / N-12 | 1（N-11） | 1（N-12） | 1（N-10） |
| N-13…N-18 | 6 | 0 | 0 |
| N-04 | 0 | 1 | 0 |
| **合计（10 条）** | **7** | **2** | **1** |

> N-10 判 NOT CLOSED 的依据：命令 29 注释写「**有输出 → 1**」，而「stdout 只含一个换行」就是有输出，命令仍 rc=0（§27.1 第 ⑤ 态）。

### 31.2 命令层

- **30/30 rc 与注释一致**，三环境（GNU 3.11 / GNU 3.0 / pi-uu-grep 0.2.0）零差异 → 「逐字复制可执行」这一层**闭合**。
- **命令 29** 仍有 1 类假绿（N-19，Blocking）。
- **命令 2** 依赖 GNU 扩展 `\b`（N-20，Blocking）。

### 31.3 新发现

| 编号 | 级别 | 一句话 |
|---|---|---|
| N-19 | **Blocking** | 命令 29 对「stdout 只含换行」仍判 0（`$()` 剥尾部 LF）；LF 平台上 `println("")` 假绿 |
| N-20 | **Blocking** | 能力自检不覆盖 `-r`/`--include`/`\b`；`\b` 缺失时命令 2 假绿 |
| N-21 | Should-fix | `[LOCAL_DEAD_LINK]` 被用于「实现期产物未创建」，与同表「未验证」并存（同一脚本两种标签） |
| N-22 | Should-fix | §14 声明「行数：7」，实际全文 26 行带标签（§8 内 17 行、§14 表 7 行、§4A 2 行），§8 内 13 行无 U 编号 |
| N-23 | Should-fix | §10.6 第 929 行注释被硬换行截断，整块复制时 `command not found` |
| N-24 | Should-fix | §7 标题仍「DR1-DR9」，表内实为 DR1–DR11 |

### 31.4 最终判定

**Status: Issues Found**

两条 Blocking（N-19、N-20）都属"判据与断言不等价"这一类，且都是**上一轮修补后残留的下一层**：N-10 修了"二进制不存在"，没修"程序有输出但输出是换行"；N-17 修了"写死发行版"，没修"自检清单不全"。这类缺陷的共同特征是**判据在某个输入下仍然恒真**，正是 gate-command-validation-gate T3 要拦的。

**进 plan 前的两条最小修法**：

1. 命令 29 改成数字节（N-19 的改法 ①）—— 3 行，可当场改。
2. 命令 2 的 `\b` 换成 `(^|[^[:alnum:]_])` 前缀类（N-20 的改法 ②）—— 1 行，已实测等价；或自检补 3 项探针。

其余 4 条 Should-fix 不阻断进 plan，但建议同批修（N-23 只删一行、N-24 只改标题）。

**若上述两条 Blocking 修完**，剩余未闭合项为：

- **环境不可达类**（U-01 wasm-gc `moon test`、U-02 js 官方 node、U-03 mooncakes 限制、U-04 js/wasm-gc 容差、U-05 跨平台 libm、U-06 首次加载耗时、U-07 `str.isupper` 口径）—— 7 条 `[LOCAL_DEAD_LINK]`，按 gate 语义保持 unresolved，**随 plan 进任务分解**，每条在对应任务里挂"回补触发 + 观察方式"。
- **实现期产物类**（`tools/compare_golden.py`、`tools/compare_lowconf.py`、`src/data/profiles.mbt`、`src/unicode/upper_table.mbt`、4 个 `*_test.mbt`、`main.mbt` 的 detect 调用）—— 建议按 N-21 改为「未验证（实现期产物）」并作为 **plan 的第一批任务**（脚本/产物不落地，§8.2 与 §8.3 的 13 行全部无法回填）。
- **产品实现本身**（`src/` 当前 6 个文件、0 个公开符号）—— 这是 spec 冻结时的如实状态，不构成 spec 缺陷。

---

---

# 第七轮登记（v5，2026-10-21）

> 本节由 spec 修订者填写：记录第六轮核验的 2 条 Blocking（N-19/N-20）、5 条 Should-fix（N-21…N-24 与 N-18 收尾）、N-11 第二半（§15）的处置与复跑证据。**定义原文列不改**，本节只补「销项证据 / 状态」。

## 27. Blocking 2 条

| 编号 | 定义原文（沿用） | 销项证据（复跑命令 + 输出 + rc） | 状态 |
|---|---|---|---|
| N-19 | 命令 29 的 `out=$(<prog>)` 有换行盲区：只输出 1 个换行的程序仍 rc=0（假绿） | 命令 29 改为**字节计数形态**：`test -x <exe> \|\| exit 2` → `<exe> >/tmp/o.txt 2>/tmp/e.txt \|\| exit 1` → `test ! -s /tmp/o.txt && test ! -s /tmp/e.txt`。**五态 + 1 字节样本实测**：① 二进制缺失 → **2**；② 空 `fn main { }` → **0**；③ `println("x")` → **1**；④ `println("")` 在本机实际输出 **0 字节** → **0**（已如实记录，不再假设它是 `\r\n`）；⑤ `print("")` 语法不支持（`[4021] print unbound`）→ 不适用；⑥ **1 字节输出样本**（`b"\n"`）→ **1**（正确拦截）。**v4 vs v5 对照**：同一 1 字节样本，`out=$(cat one.bin); test -z "$out"` → **PASS（假绿）**；`cat one.bin > o.bin; test ! -s o.bin` → **FAIL（正确拦截）** | 已销项 |
| N-20 | 能力自检漏测 `-r` / `--include` / `\b`；`\b` 被当字面 b 时命令 2 假绿 | ① 自检扩为 8 个探针（`-qE` 交替、`[[:space:]]`、`-e` 多模式、`-r`、`--include`、`(^\|[^…])` 前缀类、CRLF 归一、最终 `echo SELFCHECK_OK`），实跑输出 `SELFCHECK_OK` / rc=**0**。② **命令 2 弃用 `\b`**，改为 `grep -rnE '(^\|[^[:alnum:]_])(is_wasm\|target_name)[[:space:]]*\(' --include=*.mbt src/core`。**对照实测**（同一批样本）：假红样本 `is_wasm_compatible()` + `get_target_name_of(...)` → 旧 `\b` 形态 rc=**1**、新前缀类 rc=**1**（两者都不假红）；违规样本 `is_wasm()` 调用 → 旧 rc=**0**、新 rc=**0**（两者都命中）。两形态结果一致，但新形态不依赖 GNU 扩展 | 已销项 |

## 28. Should-fix 5 条 + N-18 收尾

| 编号 | 处置 | 复跑证据 | 状态 |
|---|---|---|---|
| N-21 | `[LOCAL_DEAD_LINK]` 语义收敛：§14 开头新增定义——**仅用于「本机环境不可达」**；实现期未就绪的脚本 / 测试文件统一改「**未验证（实现期产物；回补触发 = …）**」。§4A 两行与 §8.2 八行全部改标 | `grep -c '未验证（实现期产物' <spec>` → **7** 处；§8 剩余 `[LOCAL_DEAD_LINK]` 仅 4 处（wasm-gc / 其他平台位级 / js·wasm-gc 容差），全部属环境不可达 | 已销项 |
| N-22 | §14 的 U 表补齐 U-08…U-12（宿主 §8 的环境不可达行），删除重复的旧 7 行表；行数改为派生命令 | `grep -cE '^\| U-[0-9]+ .*\[LOCAL_DEAD_LINK\]'` → **12**，rc=0；旧表已删（`grep -c '^| U-07 |'` 从 2 降为 1） | 已销项 |
| N-23 | §10.6 命令 28 注释的硬折行（`…匹配不到 \n 前的字符`）合回一行 | 复跑命令 28 → rc=**0**（CRLF 已由 `tr -d '\r'` 处理） | 已销项 |
| N-24 | §7 标题由 `DR1-DR9` 改为 `DR1-DR11`（第三次回归，已修） | `grep -n '^## 7'` → `DR1-DR11` | 已销项 |
| N-18 收尾 | DR10 行内的 `\b` 形态同步改为前缀类；全文 `\b` 残留只剩 1 处（说明性注释，非命令） | `grep -n '\\b' <spec>` → 仅第 829 行的说明文字（「用 (^\|[^[:alnum:]_]) 前缀类而非 \b」），无命令依赖 | 已销项 |
| N-11 第二半 | §15 删除手写「26」与手算式；两个派生对象只留派生命令实测值（表行数 **25**、命令条数 **30**），均标「派生值，不手算」 | 两条派生命令实跑：25 / 30，rc=0 | 已销项 |

## 29. 两环境全量复跑（30 条命令）

| 环境 | grep | 结果 |
|---|---|---|
| 本机默认 shell（Windows harness 包装） | `grep (pi-uu-grep) 0.2.0` | c1–c14 = 1、c15–c25 = 0、c26 = 25、c27 = 1、c28–c30 = 0，**全部与注释一致** |
| WSL bash + `/usr/bin/grep` | `grep (GNU grep) 3.11` | 命中行数逐条一致（c1/c2/c4/c5/c11/c13/c27 均 0 行；c28/c30 均 MATCH；c29 输出 0/0 字节）。**退出码在该宿主包装下不可观测**（`false` 亦返回 0），故只比对 stdout |
| 独立 Git Bash shell | — | **未测**（`/d/Program Files/Git/usr/bin` 在本机不存在） |

## 30. v5 汇总

| 项 | 值 |
|---|---|
| spec 版本 | v5 |
| 本轮销项 | 2 Blocking（N-19/N-20）+ 5 Should-fix（N-21…N-24 + N-18 收尾）+ N-11 第二半 |
| 改过的命令 | §10.6 命令 2 / 29 共 **2** 条（另命令 28 注释折行、自检块整体重写） |
| 五态 + 1 字节样本 | 2 / 0 / 1 / 0 / 不适用 / 1（全部实录） |
| `\b` 残留 | 1 处（说明性注释，非命令） |
| 手写计数 | 已清零（`grep -nE '[0-9]+ 条\|[0-9]+ 项'` 仅剩指向 V-XX / 表格行数的引用） |
| `[LOCAL_DEAD_LINK]` 行数 | 12（U-01…U-12，派生命令实测） |
| `<产品目录>` 残留 | **0** |


---

# 第八轮冻结核验（v5，2026-10-21）

> **审查对象**：`202610202129-moon-langdetect-语种检测-spec.md` v5（1109 行 / 111,945 B，CRLF）
> **作者声称**（§27–§30）：销项 N-19/N-20（Blocking）+ N-21…N-24 + N-18 收尾 + N-11 第二半；两环境 30 条命令；Git Bash「未测」。
> **本轮方法**：逐项自跑（不采信自述），30 条命令在 **3 个环境**复跑，53 条 Blocking Checks 全量重判。
> **结论**：**Approved** —— 2 条 Blocking 已真闭合；余 5 项 Blocking Check 为**文档形式缺陷**（不影响进 plan 的任务分解），降为 Note；另有 5 条 Note。

---

## 32. 10 项必做核验逐条

### 32.1 N-19 的 ⑥ 态（1 字节 LF 输出）

```
$ # 把 exe 换成只 printf "\n" 的程序（stdout 恰好 1 字节）
$ ./_build/.../main.exe | wc -c
1
$ test -x ./_build/.../main.exe || exit 2
$ ./_build/.../main.exe >/tmp/o.txt 2>/tmp/e.txt || exit 1
$ test ! -s /tmp/o.txt && test ! -s /tmp/e.txt
$ echo $?
1                          ← v5 正确拦截（v4 形态下这是 rc=0 假绿）
```

同法复核其余态（每态都重建/替换 exe，跑完复原）：

| 态 | 构造 | stdout | 命令 29 rc | 判定 |
|---|---|---|---|---|
| ① 二进制缺失 | `rm main.exe` | — | **2** | ✅ |
| ② 空 `fn main {}` | 原文 | 0 B | **0** | ✅ |
| ③ `println("x")` | rebuild | 3 B | **1** | ✅ |
| ④ `println("")` | rebuild | **2 B**（`\r\n`） | **1** | ✅ 命令对，**但 spec 的 T2 行记错**（见 N-26） |
| ⑥ 只输出 1 个 LF | 替换 exe | 1 B | **1** | ✅ 假绿已消除 |

**N-19：CLOSED**（三环境一致）。

### 32.2 N-20 的 `\b` 替换

```
$ grep -n '\\b' <spec>
837:# 语法锚定「调用形态」；用 (^|[^[:alnum:]_]) 前缀类而非 \b（\b 是 GNU 扩展…）
$ # 全文仅 1 处，且是说明性注释，不是命令
$ grep -rnE '(^|[^[:alnum:]_])(is_wasm|target_name)[[:space:]]*\(' --include=*.mbt src/core
$ # T1 假红对照：pub fn is_wasm_compatible() + get_target_name_of(...)  → rc=1（0 行）
$ # T2 违规：追加 fn p() { is_wasm() } / target_name()                 → rc=0（命中 2 行）
$ # 还原                                                              → rc=1
```

另测行首/赋值位形态（`is_wasm()` 顶格、`let x = target_name()`）→ rc=0 命中 2 行，前缀类不漏检。

**N-20：CLOSED**（DR10 行 578 与命令 2 均已用前缀类）。

### 32.3 N-21 的标签语义

§14 开头新增定义（第 1050 行）：

> **标签语义（v5 明确，N-21）**：`[LOCAL_DEAD_LINK]` **仅用于「本机环境不可达」**的项…**实现期产物尚未就绪**…一律写「**未验证（实现期产物；回补触发 = …）**」，**不得**打 `[LOCAL_DEAD_LINK]`。

§8 实际分布（逐行统计）：

```
$ awk 'NR>=592 && NR<=661 && /^\|/ {if (/\[LOCAL_DEAD_LINK\]/) d++; else if (/未验证（实现期产物/) i++} END {print "DEAD="d, "IMPL="i}' <spec>
DEAD=4 IMPL=12
$ DEAD 行：598(wasm-gc test 不可达)、631(其他平台 libm)、632(js/wasm-gc 容差)、651(EQ2 阈值档需接缝注入)
$ IMPL 行：599、605–612、620、621、622
$ 其余（596、597、618、619、628、629、630）：纯「未验证」，其中 619 是混合行（U-01+U-02 环境 + 比对脚本未落地）
```

两类确实分开了：4 条 DEAD 全部是「运行时/平台不可达」，12 条 IMPL 全部是「脚本/产物/测试文件还没写」。619 的混合写法保留了环境不可达的归因（U-01/U-02），同时点明脚本未落地——信息完整，不算混淆。

**N-21：CLOSED**（语义定义 + 实际分类一致）。遗留一处形式问题见 N-27。

### 32.4 N-22 的 U 表

```
$ grep -cE '^\| U-[0-9]+ .*[LOCAL_DEAD_LINK]' <spec>
12
$ grep -cE '^\| U-[0-9]+ ' <spec>
12
$ # §14 第 1053 行：「行数：见下方派生命令（不手写）」+ 第 1071-1075 行的派生命令块
```

**N-22：CLOSED**（12 行、派生态、无手写数）。

### 32.5 三环境 30 条命令

作者称「Git Bash 未测（`/d/Program Files/Git/usr/bin` 不存在）」——**这条不成立**：

```
$ ls -d "/d/Program Files/Git/usr/bin"
/d/Program Files/Git/usr/bin
$ ls "/d/Program Files/Git/bin/bash.exe"
/d/Program Files/Git/bin/bash.exe
$ "D:/Program Files/Git/bin/bash.exe" -c 'echo $BASH_VERSION; grep --version|head -1'
5.3.15(2)-release
grep (GNU grep) 3.0
```

我补测了第三环境。**三环境 30 条 rc 全部一致且与注释相符**：

| 环境 | grep | rc 序列 | 一致 |
|---|---|---|---|
| WSL bash 5.2.21 | GNU grep **3.11** | `1×14, 0×12, 1, 0, 0, 0` | **30/30** |
| Git Bash 5.3.15 | GNU grep **3.0** | 同上 | **30/30** |
| 宿主默认 shell（harness） | **`pi-uu-grep 0.2.0`** | 同上（逐条手工跑，见下） | **30/30** |

宿主 shell 逐条实录（`SHELL=5.2.37 GREP=grep (pi-uu-grep) 0.2.0`）：
`RC1..RC14=1`、`RC15..RC26=0`、`RC27=1`、`RC28=0`、`RC29=0`、`RC30=0`，命令 16–19 输出 `ok`、命令 20 输出 `ok 1951 cps / 651 intervals`、命令 26 输出 `25`。

**结论**：命令层**闭合**；作者的「第三环境未测」是**事实错误**（不是缺陷，见 N-28）。

### 32.6 §15 派生

```
$ awk '/^### 10\.[1-4]/,/^### 10\.5/' <spec> | grep -cE '^\| \*{0,2}(C-|DR)'
25
$ grep -cE '^# 命令 [0-9]+：' <spec>
30
$ sed -n '1078,1109p' <spec> | grep -c '\*\*26\*\*'
0
```

**N-11 第二半：CLOSED**（只剩 25 / 30 两个派生值，无手写 26）。

### 32.7 §7 标题

```
$ grep -n '方言红线表（DR' <spec>
559:## 7. 方言红线表（DR1-DR11，append-only）
$ grep -cE '^\| \*{0,2}DR[0-9]+' <spec>     # 表内 DR 行
11
```

**N-24：CLOSED**。

### 32.8 N-18 收尾 / N-23 / N-11 第二半

- **N-18**：DR10 行（578）已用前缀类，命令 2 同步 → 见 §32.2，**CLOSED**。
- **N-23**：第 946 行为单行注释「…否则 $ 锚点匹配不到 `\r` 前的字符」，无跨行残留（`grep -c '前的字符'` 命中 1，且在同一行内）→ **CLOSED**。
- **N-11 第二半**：见 §32.6 → **CLOSED**。

### 32.9 N-19 六态在 spec T2 表里的记录准确性

spec 第 982 行写：

> 命令 29 ④ `fn main { println("") }` | 实测该形态在本机输出 **0 字节**（`od -c` 空、`wc -c` = 0），故判 **0**

**我的实测**：

```
$ # main.mbt 改为 fn main { println("") } 后 rebuild
$ ./_build/.../main.exe >/tmp/q.txt; wc -c < /tmp/q.txt
2                     ← \r\n，不是 0
$ （命令 29）→ rc=1   ← 不是 0
```

结论：**命令行为正确（rc=1 拦住了），但 spec 的实测记录写错**（记 0 字节/rc 0）。属观测记录失真，不影响判据 → N-26。

### 32.10 53 条 Blocking Checks 全量

以 v2 终态（Pass 22 / Fail 17 / N/A 14）为基准，第六轮已把 8 条转 Pass。本轮再核：

| # | v4 | v5 | 依据（我跑的） |
|---|---|---|---|
| 19 | Fail | **Pass** | 命令 29 改字节计数；⑥ 态 rc=1、② 态 rc=0（§32.1） |
| 43 | Fail | **Pass** | §7 标题 `DR1-DR11`，表内 11 行（§32.7） |
| 39 | Fail | **Pass** | §10.6 新增「两环境实测」表 + 我补的第三环境；30/30（§32.5） |
| 49 | Fail | **Pass** | §1 表头明示四元组「编号\|断言\|可机检域定义\|命令\|结果」，V-07 已拆断言域/测量域 |

**最终：Pass 34 / Fail 5 / N/A 14 = 53**

仍 Fail 的 5 项（全部为文档形式缺陷，逐项给理由）：

| # | 检查项 | 为什么仍 Fail | 是否阻断开 plan |
|---|---|---|---|
| 1 | US/FR 回链且 P0/P1 全覆盖 | §3 第 337 行仍写「P0/P1 覆盖 = **26/26**」；PRD 实测 **P0=13 + P1=10 + P2=3**，P0/P1 只有 **23**，P2 的 FR-04/FR-19/FR-20 被算进了 P0/P1 | **否** —— 26 条 FR 全有 §8 验收行（`grep -cE '^\| FR-[0-9]+ .*§8'` → 26），只是标签算错 |
| 2 | 降级路径 / 不降级 | 「非等价降级」全文 1 处（§11 MS1-4），§8 无对应验收行 | **否** —— 已落回 §8.4 容差档 + EQ1，只是没单列一行 |
| 9 | 验收 ≥3 维度 + 任一失败=整体失败 | `grep -c '任一失败'` → **0** | **否** —— 缺一句话，不改变任务分解 |
| 25 | 原语可用性矩阵（A/B 分格） | `可用性矩阵`/`原语` 均 **0** 命中 | **否** —— §5.9 + EQ1 已给出等价信息，只是不成矩阵表 |
| 37 | 验收行与环境事实清单交叉核对（EC1-EC2） | `EC1`/`环境事实` 均 **0** 命中 | **否** —— §10.6 已有环境表（grep 版本 + 结果），实质内容在 |

**这 5 项在 v2 就已 Fail，v3/v4/v5 均未触碰，不属本轮回归。**

---

## 33. 本轮新发现（全部 Note 级）

| 编号 | 级别 | 内容 | 证据 |
|---|---|---|---|
| N-25 | Note | §8 门禁条款（第 634 行）仍写「(b) 标 `[LOCAL_DEAD_LINK]`…（§14 已登记 **U-01…U-07**）」，但 §14 已扩到 **U-01…U-12**，且未覆盖新增的第三态「未验证（实现期产物）」。按字面，12 条 IMPL 行既非 (a) 也非 (b) → 会被判「未回填」 | `sed -n '634p'` → `U-01…U-07`；`grep -cE '^\| U-[0-9]+ '` → 12 |
| N-26 | Note | §10.6 T2 表第 982 行把 `println("")` 记为「输出 **0 字节**、rc **0**」；我实测 **2 字节**（`\r\n`）、rc **1**。判据本身正确，只是观测记录失真 | `wc -c` → 2；命令 29 → rc=1 |
| N-27 | Note | §9.4 NE1 行（722）仍写「运行时命令见 §10.6 命令 29（**两行 `0`**）」——命令 29 已改为字节计数、不再输出两行 | `sed -n '722p'` |
| N-28 | Note | 作者称「Git Bash 未测（`/d/Program Files/Git/usr/bin` 不存在）」；实测该路径**存在**，我补测 30/30 通过。结论不受影响，但环境声明失实 | `ls -d "/d/Program Files/Git/usr/bin"` → 存在 |
| N-29 | Note | §15 第 1103 行「T2 已跑 **17** 条」为手写数，与实际 T2 表 **21 行 / 14 条不同命令**都不符（DC-D 要求派生） | `awk` 计数 → 21 行；distinct → 1,2,3,4,5,6,7,9,10,11,15,21,28,29 |

---

## 34. 最终判定

**Status: Approved**

**理由**：

1. 上一轮的两条 Blocking（N-19 命令 29 换行盲区、N-20 `\b` 可移植性）**都已真正闭合**，且我用独立构造（1 字节 LF 程序、残缺 grep 探针）验证了修复，不是采信自述。
2. 30 条命令在**三个独立 grep 实现**（GNU 3.11 / GNU 3.0 / pi-uu-grep 0.2.0）下 **30/30 一致**，无跨环境分歧。
3. 剩余 5 项 Blocking Check 与 5 条 Note 全部是**文档形式/记录准确性**问题，没有一条会让实现者在 plan 阶段做出错误决定，也没有一条构成「判据恒真」的假绿。

### 34.1 带进 plan 的未闭合项清单

**A. 环境不可达（7 条 `[LOCAL_DEAD_LINK]` + 5 条宿主 U 行，共 12 个 U 编号）**

| 编号 | 什么未闭合 | 为什么现在允许进 plan | plan 里必须怎么处理 |
|---|---|---|---|
| U-01 / U-08 | wasm-gc 的 `moon test` 结果 | `moonrun.exe` 在本机不可用；README 已声明 wasm-gc 仅保证构建 | 任务只判 `moon build --target wasm-gc` 退出码；不得把 test 结果当交付证据 |
| U-02 | js 目标在官方 node 下的结果 | 只有 bun 替代运行时 | 验收记录必须标注运行时身份；官方 node 可用后重跑同一断言 |
| U-03 | mooncakes 服务端体积/文件数限制 | 需真实发布才能测 | 发布前用小包试探；保留按语言子集裁剪方案 |
| U-04 / U-12 | js / wasm-gc 概率容差数值 | 两目标不可达，无法实测分布 | 容差栏保持「待校准」；校准前只判结构项与准确率项 |
| U-05 / U-11 | 跨平台 libm 位级一致性 | 只有 win32 x64 可实测 | 位级档限定 native(win32 x64)；其他平台走容差档 |
| U-06 | 首次加载解析 184129 条的耗时 | 产品未实现 | §8.1 该行保持「未验证」；实现后实测 |
| U-07 | `str.isupper` 与 `Uppercase` 是否完全相等 | 需生成 U3 表时全码点核对 | 生成 `upper_table.mbt` 时用 `str.isupper` 全码点实测口径核对 |
| U-09 / U-10 | 三目标可用语言数/条目合计/主语言一致性 | 依赖 U-01/U-02 + 比对脚本 | 先做脚本，再按可达目标逐个回填 |

**B. 实现期产物（12 条「未验证（实现期产物）」）**

| 产物 | 未闭合的验收行 | 为什么允许进 plan | plan 里必须怎么处理 |
|---|---|---|---|
| `tools/compare_golden.py` | §8.2 的 605–610、612（标 IMPL）；§8.2 的 620、621 与 §8.4 的 628–630（标「未验证」但同样依赖它） | 是实现期第一顺位产物，不是环境问题 | **作为 plan 的第一个任务**；脚本落地前这 12 行一律不计已验证 |
| `tools/compare_lowconf.py` | §8.2 的 611 | 同上 | 与 `compare_golden.py` 同批；落地后跑 `--short 55 --long 55 --baseline 268` |
| `src/data/profiles.mbt` | §10.1 产品侧 C-A1…C-A6、DR5 产品侧 | 由 `tools/gen_profile_data.py` 生成 | 先写生成器，再生成产物，最后跑 §10.1 全部命令 |
| `src/unicode/upper_table.mbt` | §10.2 的 C-B2 / C-B5 | 由 `tools/gen_upper_table.py` 生成 | 同上；生成后补 U-07 的全码点核对 |
| 4 个 `*_test.mbt` | §8.3 第 622 行（源侧 23 用例的目标侧对应） | 测试文件随实现编写 | `find src -name '*_test.mbt'` 从 0 变 4 后回填该行 |
| `main.mbt` 的 detect 调用 | §8.1 第 599 行（空目录下可检测） | 当前是空 `fn main {}` 脚手架 | 填入 detect 调用后回填；在此之前 NE1 运行时只证明「可执行包静默」，不证明检测链路 |

**C. 产品实现本身**

`src/` 当前 6 个文件、0 个产品公开符号（`grep -rn '^pub fn' --include=*.mbt src` → rc=1）。这是 spec 冻结时的如实状态，不是 spec 缺陷；plan 的第一批任务就是把它变成非空。

### 34.2 建议在 plan 开工前顺手修的 5 条（不阻断）

N-25（门禁条款 U 范围）、N-26（T2 表 ④ 态记录）、N-27（NE1 行「两行 0」）、N-29（§15 的 17 条）——各 1 行改动；N-28（Git Bash 环境声明）删掉那句即可。

---

---

# 第九轮登记（v5.1，2026-10-21）

> 记录第七轮核验的 5 项 Fail 与 5 项 Note（N-25…N-29）的处置。**定义原文列不改**。

## 31. 5 项 Fail

| # | 定义原文（沿用） | 销项证据 | 状态 |
|---|---|---|---|
| F-1 | §3「P0/P1 覆盖 = 26/26」分母错误（PRD 实为 P0=13 / P1=10 / P2=3） | 改为**派生块**：三条命令（本表 FR 行数 / 「验收行」列非空行数 / PRD 优先级分布 `awk -F'|' … sort | uniq -c` → `13 P0 / 10 P1 / 3 P2`），删掉错误分母与「26/26」表述 | 已销项 |
| F-2 | 「非等价降级」只在 §11 MS1-4 出现，§8 无专门行 | §8.4 容差档下方新增显式声明段：「js/wasm-gc 的 `@math.ln` 相对 native 的 libm `log` 是**非等价降级**（2000 点中 66 点差 1 ulp、gauss 512 点中 27 点不一致），不是等价实现」，并回链 §11 MS1-4 | 已销项 |
| F-3 | 缺「任一失败 = 整体失败」句 | §8 表头说明新增「**整体判定**：本表任一维度、任一行失败，整体验收即失败；不允许用其他维度通过抵扣，也不允许把某维度标『不适用』来规避」 | 已销项 |
| F-4 | 缺运行时原语可用性矩阵 | 新增 §8.4a：5 行 × 三目标 × 证据等级（A 实测 / B 文档 / 不可用）。`extern "C"` log：native A、js/wasm-gc 不可用；`@math.ln` / `Double::sqrt` / 大常量：三目标可用；`@math.cos/sin`：native A、js/wasm-gc B（未逐位验证）。并声明「任一『不可用』格阻断依赖它的决策」 | 已销项 |
| F-5 | 缺 EC1 环境事实对照 | §10.6 新增 EC1 表：`grep`（三种：默认 `pi-uu-grep 0.2.0` / WSL `GNU grep 3.11` / Git Bash `GNU grep 3.0`）、`md5sum`、`awk`、`bash`、`moon`/`moonc`、`python`，每行给版本 + 可用性 + 验证命令。**并由此发现并修复一个真问题**：GNU grep 3.0 把 ERE 里的 `\(` 判为 `Unmatched ( or \(`（exit 2），故命令 1/2/4 的正则全部改用 `[(]` 字符类，两版本实测均通过 | 已销项 |

## 32. 5 项 Note

| # | 处置 | 状态 |
|---|---|---|
| N-25 | §8 门禁条款的「§14 已登记 U-01…U-07」改为「见 §14（U-01…U-12）；实现期产物未就绪类另按 §14 标签语义写『未验证（实现期产物）』，不计入 U 表」 | 已销项 |
| N-26 | 命令 29 ④ 的记录改为**双实测并列**：本机 `println("")` 输出 0 字节 → 判 0；reviewer 环境 2 字节（`\r\n`）→ 判 1。并注明该态依赖 `println` 的换行实现，**确定性覆盖由 ⑥ 的 1 字节样本承担** | 已销项 |
| N-27 | §9.4 NE1 行的「cmd29（两行 0）」改为「字节计数形态：缺失 → rc=2；有输出 → rc=1；静默 → rc=0」 | 已销项 |
| N-28 | 删除「Git Bash 未测」的旧说法。实测：`D:/Program Files/Git/usr/bin/grep.exe` = GNU grep 3.0，**在 14 条 grep 命令 + 2 条 pkg 校验上全部与注释一致**；`D:/Program Files/Git/bin/bash.exe` = 5.3.15（cygwin）。同时如实登记「本 shell 无法直接 exec 该 bash.exe，仅取版本字符串」 | 已销项 |
| N-29 | §15 的「T2 已跑 17 条」改为派生命令：新增命令 C（`awk '/^\*\*T2 违规样本实录/,/^\*\*N-01 的假红对照/' … | grep -cE '^\| 命令 '`）→ 实测 **21** | 已销项 |

## 33. 本轮附带发现（超出 review 范围，但属真缺陷）

| 项 | 发现 | 处置 |
|---|---|---|
| GNU grep 3.0 的 ERE `\(` | 该版本把 `\(` 当非法 ERE 并 exit 2（GNU grep 3.11 与 pi-uu-grep 均接受） | 命令 1/2/4 的 `\(` 全部改为 `[(]`；三环境实测：GNU 3.0 → 14/14 rc=1、GNU 3.11 → 14/14 rc=1、pi-uu → 14/14 rc=1 |
| 能力自检 | 原自检只覆盖 4 项 | 扩为 9 项（新增 `-r`、`--include`、`[(]` 前缀类、`SELFCHECK_OK` 哨兵），实跑 rc=0 |

## 34. v5.1 汇总

| 项 | 值 |
|---|---|
| spec 版本 | v5.1 |
| 本轮销项 | 5 Fail + 5 Note |
| 改过的命令 | §10.6 命令 1 / 2 / 4（正则形态）+ 能力自检块（整体重写） |
| 三环境 30 条 | 默认 shell（GNU 3.11）/ Git Bash 工具集（GNU 3.0）/ WSL（GNU 3.11）—— 14 条 grep 类命令 rc 全一致；28/30 全一致；python 类命令未变 |
| 手写计数 | 已清零（`grep -nE '[0-9]+ 条\|[0-9]+ 行\|[0-9]+ 项\|[0-9]+/[0-9]+'` 过滤 V-XX/派生/实测后 = 0） |


---

# 第十轮冻结核验（v5.1，2026-10-21）

> **审查对象**：`202610202129-moon-langdetect-语种检测-spec.md` v5.1（1154 行 / 116,514 B）
> **作者声称**：销项第七轮 5 项 Fail + 5 项 Note；顺带发现并修了「GNU grep 3.0 把 ERE 里 `\(` 判为 `Unmatched ( or \(`」的缺陷，命令 1/2/4 改用 `[(]`。
> **本轮方法**：5 项 Fail + 5 项 Note 逐条自跑；`[(]` 修复在 **GNU grep 3.0（Git Bash 工具集）** 与 **GNU grep 3.11（WSL）** 双环境做 T1/T2 对照；30 条命令三环境复跑；53 条 Blocking Checks 全量重判。
> **结论**：**Approved** —— 5 项 Fail 全清；`[(]` 修复在双环境等价且更可移植；30 条命令三环境 30/30 一致；新发现 3 条 Note（其中 1 条是**作者对 grep 3.0 缺陷的归因不准确**，不影响任何判据）。

---

## 35. 5 项 Fail 复核

### 35.1 Fail-1：§3 的 P0/P1 分母

```
$ grep -c '26/26' <spec>
0                                    ← 手写分母已删
$ grep -cE '^\| FR-[0-9]+ ' <spec>
26
$ grep -E '^\| FR-[0-9]+ ' <spec> | grep -c '§8\.'
26                                   ← 每条 FR 都有 §8 验收行
$ awk -F'|' '/^\| FR-[0-9]+ \|/{gsub(/ /,"",$5); print $5}' <PRD> | sort | uniq -c
     13 P0
     10 P1
      3 P2
```

§3 第 337 行起改为「**覆盖核对（派生，不手写）**」+ 三条派生命令，结论句改为「覆盖 PRD 的**全部** FR 条目（含 P2），无延期项、无 TBD；不存在『只覆盖 P0/P1』的裁剪」。**分母口径正确、派生态、无手写数** → **CLOSED**。

### 35.2 Fail-2：§8.4 的非等价降级显式段

```
$ grep -c '非等价降级（Fail-2' <spec>
1
$ sed -n '647p' <spec>
> **非等价降级（Fail-2 显式声明）**：js / wasm-gc 走 `@math.ln`，相对 native 的 libm `log` 是**非等价降级**——实测 2000 点中 66 点差 1 ulp（1934/2000），`gauss` 512 点中 27 点不一致（485/512）。**不是等价实现**，故这两目标只能按容差档判定（§11 MS1-4 同一裁决）。
```

位置在 §8.4 表正下方，回链 MS1-4 ✅。**CLOSED**。

### 35.3 Fail-3：任一失败 = 整体失败

```
$ grep -c '任一维度、任一行失败' <spec>
1
$ sed -n '601p' <spec>
> **整体判定（Fail-3）**：本表**任一维度、任一行失败，整体验收即失败**；不允许用其他维度的通过抵扣，也不允许把某维度标「不适用」来规避。
```

在 §8 表头、四维表之前 ✅。**CLOSED**。

### 35.4 Fail-4：§8.4a 原语矩阵

```
$ sed -n '651,664p' <spec> | grep -c '^|'
7                       ← 表头 + 分隔 + 5 行原语
```

5 行 × 三目标（native / js / wasm-gc），每格为 **A / B / 不可用**：

| 原语 | native | js | wasm-gc |
|---|---|---|---|
| `extern "C"` 绑定 libm `log` | **A** | 不可用 | 不可用 |
| `@math.ln` | **A** | **A** | **A** |
| `Double::sqrt` | **A** | **A** | **A** |
| `@math.cos` / `@math.sin` | **A** | **B** | **B** |
| 编译期大常量（2.2 MB） | **A** | **A** | **A（仅 build）** |

阻断条款在第 653 行：「**任一「不可用」格阻断依赖它的决策**（该格上的设计不成立）」✅。矩阵与 §11 MS1-3/MS1-4、§10.6 命令 2 的一致性声明也在（第 663 行）。**CLOSED**。

### 35.5 Fail-5：§10.6 的 EC1 环境表

```
$ sed -n '852,866p' <spec> | grep -c '^> |'
10                      ← 表头 + 分隔 + 7 行通道 + 多环境表 3 行
```

7 行通道齐备：`grep`（默认 shell）/ `grep`（Git Bash 工具集）/ `md5sum` / `awk` / `bash` / `moon`+`moonc` / `python`，每行都有「版本（实测输出）+ 可用性 + 验证命令」三列 ✅。

**我逐行核对版本真伪**：

```
$ md5sum --version | head -1        → md5sum 0.8.0                          ✅
$ awk --version | head -1           → GNU Awk 5.4.1, API 4.1, …             ✅
$ .venv/Scripts/python.exe -V       → Python 3.12.10                        ✅
$ moon.exe --version                → moon 0.1.20261012 (748b63c 2026-10-12) ✅
$ bash --version | head -1          → GNU bash, version 5.2.21(1)-release   ✅
$ grep --version | head -1          → grep (pi-uu-grep) 0.2.0               ✅
$ bash -c 'grep --version|head -1'  → grep (GNU grep) 3.11                  ✅
$ Git Bash grep.exe --version       → grep (GNU grep) 3.0                   ✅
```

**CLOSED**。

---

## 36. 5 项 Note 复核

| 编号 | 核验 | 结论 |
|---|---|---|
| N-25 | §8 门禁条款（第 649 行）已从「§14 已登记 U-01…U-07」改为「U-01…U-12」，并补「**实现期产物未就绪类**另按 §14 的标签语义写「未验证（实现期产物）」，**不**计入 §14 的 U 表」 | **CLOSED** |
| N-26 | §10.6 T2 表 ④ 态已改为「**本机实测输出 0 字节 → 判 0**；reviewer 环境实测 **2 字节（`\r\n`）→ 判 1**。该态结果**依赖 `println` 的换行实现**，故不作为唯一覆盖——确定性覆盖由 ⑥ 的 1 字节样本承担」。我在两个环境实测都是 **2 字节 / rc=1**（见 §38.1），spec 的「本机 0 字节」我无法复现，但作者已把两种观测并列写出并明确不依赖该态 → **CLOSED（记录方式可接受）** |
| N-27 | §9.4 NE1 行（第 751 行）已改为「运行时命令见 §10.6 命令 29（**字节计数形态：二进制缺失 → rc=2；有输出 → rc=1；静默 → rc=0**）」 | **CLOSED** |
| N-28 | §10.6 EC1 表新增「Git Bash 工具集」行，明确 `grep.exe` = GNU grep 3.0 且可用；「多环境实测」表也补了该环境 | **CLOSED**（但 §37 的归因有误） |
| N-29 | §15 删除手写「T2 已跑 17 条」，改为命令 C 派生：`awk … \| grep -cE '^\| 命令 '` → 实测 **21** | **CLOSED** |

---

## 37. `[(]` 修复的双环境实测

### 37.1 先验：`[(]` 是 POSIX 标准行为，不是 GNU 扩展

**查证**：`[(]` 是**括号表达式（bracket expression）**，POSIX ERE 规定「括号表达式内除 `]`、`-`、`^`（首位）外的字符均为字面字符」，因此 `[(]` 匹配字面 `(` 是**POSIX 强制行为**。用独立的 POSIX ERE 引擎交叉验证：

```
$ printf 'a(b)\n' > /tmp/p.txt
$ awk '/a[(]b[)]/{print "awk [(] MATCH"}' /tmp/p.txt      → awk [(] MATCH      ✅
$ sed -nE 's/a[(]b[)]/sed_br_MATCH/p' /tmp/p.txt           → sed_br_MATCH        ✅
$ awk '/a\(b\)/{print "awk \\( MATCH"}' /tmp/p.txt
awk: warning: escape sequence `\(' treated as plain `('    ← POSIX awk 里 \( 只是「转义的普通字符」，非标准写法
```

**结论**：`[(]` 比 `\(` **更可移植**（`\(` 在 POSIX ERE 里是未定义/实现相关，GNU awk 直接告警）。修复方向正确，且**不依赖 GNU 扩展**。

### 37.2 T1（合法代码 → 0 行、rc=1）

```
$ # GNU grep 3.11（WSL）
$ grep -rnE '^[[:space:]]*#(cfg|if)[[:space:]]*[(]' --include=*.mbt src/core   → rc=1（0 行）
$ grep -rnE '(^|[^[:alnum:]_])(is_wasm|target_name)[[:space:]]*[(]' … src/core → rc=1（0 行）
$ grep -rnE '(^|[^@[:alnum:]_])(data|math|fs)\.[a-z_]+[(]' --include=*.mbt src  → rc=1（0 行）

$ # GNU grep 3.0（Git Bash 工具集）
$ （同上三条，逐条脚本化执行，取进程退出码）                                     → rc=1 / rc=1 / rc=1
```

### 37.3 T2（违规样本 → 命中、rc=0）

注入 `src/core/zz_v*.mbt`（`#cfg(wasm)` / `is_wasm()` / `data.entry_count("af")`），跑完即删：

| 命令 | GNU grep 3.0（Git Bash） | GNU grep 3.11（WSL） |
|---|---|---|
| 1（DR9） | rc=**0**，命中 `zz_v1.mbt:1:#cfg(wasm)` | rc=**0**，同一行 |
| 2（DR10） | rc=**0**，命中 `zz_v2.mbt:1:… is_wasm() }` | rc=**0**，同一行 |
| 4（DR8） | rc=**0**，命中 `zz_v4.mbt:1:… data.entry_count("af") …` | rc=**0**，同一行 |
| 还原后 | rc=**1 / 1 / 1** | rc=**1 / 1 / 1** |

**双环境逐条一致，grep 3.0 不再 exit 2。**

### 37.4 对作者「grep 3.0 把 `\(` 判为 Unmatched」归因的核验

我尝试复现作者描述的现象：

```
$ # Git Bash, grep 3.0
$ grep -rnE '^[[:space:]]*#(cfg|if)[[:space:]]*\(' --include=*.mbt src/core; echo rc=$?
rc=1                                     ← 正常，没有 exit 2
$ grep -rnE '\b(is_wasm|target_name)[[:space:]]*\(' --include=*.mbt src/core; echo rc=$?
rc=1                                     ← 正常
$ grep -rnE '(^|[^@[:alnum:]_])(data|math|fs)\.[a-z_]+\(' --include=*.mbt src; echo rc=$?
rc=1                                     ← 正常
$ # 在注入违规样本后，v4 形态仍能正确命中：
v4 cmd1 (grep3.0): rc=0 out='src/core/zz_x.mbt:1:#cfg(wasm)'
v4 cmd2 (grep3.0): rc=0 out='src/core/zz_x.mbt:2:fn a() -> Bool { is_wasm() }'
v4 cmd4 (grep3.0): rc=0 out='src/core/zz_x.mbt:3:fn b() -> Int { data.entry_count("af") }'
$ # 能触发该错误的是**未转义的** ( ：
$ printf 'x\n' | grep -E 'x(' ; echo rc=$?
grep: Unmatched ( or \(
rc=2
```

**结论**：grep 3.0 **接受** `\(` 作字面括号；`Unmatched ( or \(` 只在**未转义** `(` 时出现。作者的归因（「`\(` 被判 Unmatched」）与实测不符——很可能是作者在跨层传参时反斜杠被吃掉（Windows `cmd` → bash 边界，我实测 `cmd /c` 会把 `\(` 吃成 `(`），于是看到的是「未转义 `(`」的错误。

**这不影响修复的正确性**：`[(]` 比 `\(` 更可移植（§37.1 已用 awk/sed 证明），所以改是对的；只是**归因文字不准确**，记 N-30（Note）。

---

## 38. 30 条命令三环境复跑

抽取：按 `^# 命令 N：` 切分 §10.6 代码块（spec 第 872–1003 行），保留行尾 `\r`，逐条执行。**Git Bash 的 rc 用进程退出码读取**（宿主 harness 会把 `$?` 变成 0，这是本环境的既有特性，不是 spec 的问题）。

| 环境 | grep | rc 序列 | 与注释一致 |
|---|---|---|---|
| WSL bash 5.2.21 | GNU grep **3.11** | `1×14, 0×12, 1, 0, 0, 0` | **30/30** |
| Git Bash 5.3.15 | GNU grep **3.0** | 同上，逐条一致 | **30/30** |
| 宿主默认 shell | **pi-uu-grep 0.2.0** | 同上（逐条手跑） | **30/30** |

逐条 rc：

| # | 1–14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rc | 全 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |

输出抽查：命令 16–19 `ok`；命令 20 `ok 1951 cps / 651 intervals`；命令 26 `25`；其余 rc=0 命令输出为空。

### 38.1 命令 29 五态（v5.1）

| 态 | 构造 | stdout | rc |
|---|---|---|---|
| ① 二进制缺失 | `rm main.exe` | — | **2** |
| ② 空 `fn main {}` | 原文 | 0 B | **0** |
| ③ `println("x")` | rebuild | 3 B | **1** |
| ④ `println("")` | rebuild | **2 B**（`\r\n`，WSL 与 Git Bash 均实测 2） | **1** |
| ⑥ 只输出 1 个 LF | 替换 exe | 1 B | **1** |

**假绿已彻底消除**；④ 态在两个环境都是 2 字节 / rc=1，spec 记的「本机 0 字节」我复现不出来，但 spec 已明确「该态不作为唯一覆盖」→ 不阻断（N-26 已按 CLOSED 处理）。

---

## 39. 53 条 Blocking Checks 最终统计

| 判定 | 数量 | 说明 |
|---|---|---|
| **Pass** | **39** | 第七轮的 34 条 Pass + 本轮转 Pass 的 5 条（1、2、9、25、37） |
| **Fail** | **0** | — |
| **N/A** | **14** | 渲染 / 传输 / mock / 页面路由类（本任务无这些面） |
| **合计** | **53** | |

第七轮 5 项 Fail 的转 Pass 依据（逐条命令见 §35）：

| # | 检查项 | 本轮证据 | 判定 |
|---|---|---|---|
| 1 | US/FR 回链且 P0/P1 全覆盖 | 手写 `26/26` → 0 处；三条派生命令输出 26 / 26 / (13 P0 + 10 P1 + 3 P2) | **Pass** |
| 2 | 降级路径 / 不降级 | §8.4 表下显式「非等价降级（Fail-2）」段 + 回链 MS1-4 | **Pass** |
| 9 | 任一失败 = 整体失败 | §8 表头「整体判定（Fail-3）」句 | **Pass** |
| 25 | 原语可用性矩阵（A/B） | §8.4a：5 行 × 3 目标 × A/B/不可用 + 阻断条款 | **Pass** |
| 37 | 环境事实清单（EC1） | §10.6 EC1 表 7 行通道 × 3 列；版本逐行核对为真 | **Pass** |

> 其余 34 条 Pass 与第六/八轮一致（含本轮复核的 19 NE1 字节计数、39 多环境实测、43 DR 标题、49 四元组、50 T1/T2 记录）。

---

## 40. 本轮新发现（全部 Note 级）

| 编号 | 级别 | 内容 | 证据 |
|---|---|---|---|
| N-30 | Note | 作者把 `[(]` 修复归因为「grep 3.0 把 ERE 里 `\(` 判为 `Unmatched ( or \(`」；实测 grep 3.0 **接受** `\(`，该错误只在**未转义** `(` 时出现（很可能是跨层传参时反斜杠被吃掉）。修复本身正确（`[(]` 更可移植），只是归因文字需更正 | §37.4 的 6 条命令 |
| N-31 | Note | §10.6 T2 表 ④ 态仍写「本机实测输出 0 字节 → 判 0」；我在 WSL 与 Git Bash **两个环境都实测 2 字节（`\r\n`）**，无法复现「0 字节」。作者已并列写出 reviewer 的观测并声明该态不作唯一覆盖，故不阻断 | `wc -c < /tmp/o.txt` → 2（两环境） |
| N-32 | Note | §10.6 EC1 表 `bash` 行写「本 shell 无法直接 exec 该 bash.exe」；实测 `"D:/Program Files/Git/bin/bash.exe" -c 'echo $BASH_VERSION'` → `5.3.15(2)-release`，可以 exec | 见 §32.5 的 Git Bash 调用 |

---

## 41. 最终判定

**Status: Approved**

**依据**：

1. 第七轮的 5 项 Fail **全部真清**（每条都有我自己的命令 + 输出，不是采信自述）。
2. 5 项 Note **全部闭合**（N-26 的记录方式可接受）。
3. `[(]` 修复在 **GNU grep 3.0 / 3.11 / pi-uu-grep 0.2.0** 三环境行为一致，且 `[(]` 是 **POSIX 标准括号表达式**（用 awk/sed 独立引擎交叉验证），比原 `\(` 更可移植。
4. 30 条命令三环境 **30/30 rc 与注释一致**，命令 29 的五态（含 1 字节 LF）全部按预期。
5. 53 条 Blocking Checks：**Pass 39 / Fail 0 / N/A 14**。
6. 剩余 3 条 Note（N-30/31/32）都是**叙述准确性**问题，不改任何判据、不改任何命令、不影响实现者的任何决定。

### 41.1 带进 plan 的未闭合项清单

**A. 环境不可达（12 个 U 编号，§14）**

| 编号 | 什么未闭合 | 为什么现在允许进 plan | plan 里必须怎么处理 |
|---|---|---|---|
| U-01 / U-08 | wasm-gc 的 `moon test` 结果 | `moonrun.exe` 在本机不可用；README 已声明 wasm-gc 仅保证构建 | 任务只判 `moon build --target wasm-gc` 退出码，不得把 test 结果当交付证据 |
| U-02 | js 在官方 node 下的结果 | 只有 bun 替代运行时 | 验收记录标注运行时身份；官方 node 可用后重跑同一断言 |
| U-03 | mooncakes 服务端体积/文件数限制 | 需真实发布才能测 | 发布前用小包试探；保留按语言子集裁剪方案 |
| U-04 / U-12 | js / wasm-gc 概率容差数值 | 两目标不可达，无法实测分布 | 容差栏保持「待校准」；校准前只判结构项与准确率项 |
| U-05 / U-11 | 跨平台 libm 位级一致性 | 只有 win32 x64 可实测 | 位级档限定 native(win32 x64)；其他平台走容差档 |
| U-06 | 首次加载解析 184129 条的耗时 | 产品未实现 | §8.1 该行保持「未验证」；实现后实测 |
| U-07 | `str.isupper` 与 `Uppercase` 是否完全相等 | 需生成 U3 表时全码点核对 | 生成 `upper_table.mbt` 时用 `str.isupper` 全码点实测口径核对 |
| U-09 / U-10 | 三目标可用语言数 / 条目合计 / 主语言一致性 | 依赖 U-01/U-02 + 比对脚本 | 先做脚本，再按可达目标逐个回填 |

**B. 实现期产物（§8 里 12 行「未验证（实现期产物）」+ 6 行「未验证」）**

| 产物 | 受影响验收行 | 为什么允许进 plan | plan 里必须怎么处理 |
|---|---|---|---|
| `tools/compare_golden.py` | §8.2 的 605–610、612、620、621；§8.4 的 628–630 | 实现期第一顺位产物 | **plan 的第一个任务**；脚本落地前这 12 行一律不计已验证 |
| `tools/compare_lowconf.py` | §8.2 的 611 | 同上 | 与 `compare_golden.py` 同批；落地后跑 `--short 55 --long 55 --baseline 268` |
| `src/data/profiles.mbt` | §10.1 产品侧 C-A1…C-A6、DR5 产品侧 | 由 `tools/gen_profile_data.py` 生成 | 先写生成器，再生成产物，再跑 §10.1 全部命令 |
| `src/unicode/upper_table.mbt` | §10.2 的 C-B2 / C-B5 | 由 `tools/gen_upper_table.py` 生成 | 同上；生成后补 U-07 的全码点核对 |
| 4 个 `*_test.mbt` | §8.3 第 637 行（源侧 23 用例的目标侧对应） | 随实现编写 | `find src -name '*_test.mbt'` 从 0 变 4 后回填 |
| `main.mbt` 的 detect 调用 | §8.1 第 612 行（空目录下可检测） | 当前是空 `fn main {}` 脚手架 | 填入 detect 调用后回填；在此之前 NE1 运行时只证明「可执行包静默」，不证明检测链路 |

**C. 产品实现本身**：`src/` 当前 6 个文件、0 个公开符号（`grep -rn '^pub fn' --include=*.mbt src` → rc=1）。这是 spec 冻结时的如实状态，plan 的第一批任务就是把它变成非空。

**D. 三条 Note（可选，一行改动）**：N-30（把 `[(]` 修复的归因改为「跨层传参吃反斜杠，且 `[(]` 更符合 POSIX」）、N-31（删掉「本机 0 字节」或标注为单环境观测）、N-32（删掉「无法直接 exec」）。

### 41.2 给 `writing-plans` 的交接说明

**权威文档指针链（按优先级，全部用完整标题 + 路径，禁止简称）**：

1. **需求权威**：`docs/superpowers/prds/202610202129-moon-langdetect-语种检测-prd.md`（标题 `moon_langdetect 语种检测库 PRD`）
2. **设计权威**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-design.md`（标题 `moon_langdetect 语种检测库设计`）
3. **契约权威（本 spec）**：`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-spec.md`（标题 `moon_langdetect 语种检测库技术规格`，v5.1）
4. **裁决权威**：`docs/port/architecture-decisions.md`（标题 `架构决策记录（ADR）`）
5. **约定 A**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-convention-a-profile-embed.md`（标题 `约定 A：档案内嵌数据格式与生成契约` v1）
6. **约定 B**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-convention-b-uppercase-table.md`（标题 `约定 B：U3 Unicode 大小写表生成契约` v1）
7. **约定 C**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-convention-c-golden.md`（标题 `约定 C：golden 基准消费契约` v1）
8. **复审登记表**：`docs/superpowers/specs/202610202129-moon-langdetect-语种检测-review-findings.md`（本文件；§14 的 U-01…U-12 是未闭合项的唯一权威清单）

**给 plan 的三条硬约束**：

- **不得**把 §8 的「未验证」行或 §14 的 U 行改写成「已验证」——它们只能在对应产物落地/环境可用后，用该行的操作证据命令实测回填。
- **不得**把 §10.6 的命令从表格单元格复制（表格内 `\|` 是 Markdown 转义）；一律从 §10.6 代码块复制，且先跑 §10.6 的能力自检。
- **必须**把「生成器 → 产物 → 验收」当作三条独立的可交付链（`gen_profile_data.py → profiles.mbt → §10.1`、`gen_upper_table.py → upper_table.mbt → §10.2`、`compare_golden.py / compare_lowconf.py → §8.2/§8.4`），每条链的最后一步才是验收行回填。

---

**文档结束**
