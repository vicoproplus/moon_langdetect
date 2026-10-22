# MoonBit 移植 langdetect：工具链与档案数据实测报告

本文件只记录实测结果。所有数字均由 `tools/` 与 `probes/` 下的脚本或命令产出，原始输出保存在 `probes/logs/`。
未实测项统一列入「未测 / 失败 / 超时」章节，不做估算；本报告不含任何外推数字。

- 工作目录：`F:/moonbit比赛/moon_langdetect`
- 工具链：`moon 0.1.20261012 (748b63c 2026-10-12)`，`moonc v0.10.15+943464bfa`，路径 `C:\Users\Administrator\.moon\bin\moon.exe`
- Python：3.12.10；OS：win32 10.0.19045
- 只读输入：`langdetect/langdetect/profiles/`（55 个无扩展名单行 JSON）

---

## A. 档案数据事实

复现命令：

```
python tools/profile_stats.py
```

脚本输出（关键行）：

```
files=55
total_bytes=2204952
total_entries=184129
len_dist={1: 7791, 2: 52387, 3: 123951}
non_bmp_total=0
max_entries=ko:23031
min_entries=gu:1474
max_bytes=ko:307193
min_bytes=so:16786
```

生成物：`analysis/profile-facts.csv`（55 行明细 + 表头，UTF-8 BOM）、`analysis/profile-facts.md`（中文明细）。

### A.1 汇总表

| 指标 | 实测值 |
|---|---:|
| 档案文件数 | 55 |
| 总字节 | 2,204,952 |
| freq 条目总数 | 184,129 |
| count 总和 | 3,607,422,986 |
| 1 字符键条目 | 7,791（4.2313%） |
| 2 字符键条目 | 52,387（28.4512%） |
| 3 字符键条目 | 123,951（67.3175%） |
| 长度不为 1/2/3 的键条目 | 0 |
| 含非 BMP 字符（码点 > U+FFFF）的条目 | 0 |
| 条目数最多 | `ko` 23,031 |
| 条目数最少 | `gu` 1,474 |
| 字节数最多 | `ko` 307,193 |
| 字节数最少 | `so` 16,786 |

补充事实（同一次脚本运行、`analysis/profile-facts.csv` 逐行数据）：

- 最大单条 count：`en` 的 `e` = 27,848,709；`count 最大` 列可逐语言核对。
- 键字符集共 3,160 个不同码点；最大码点 `U+FFFD`；键中不含 `"`、`\` 与控制字符（`probes/logs/` 未落盘，该结论来自 `python` 一次性检查，命令见下）。

键字符集检查命令（一次性，输出即上文数字）：

```
python -c "import json;from pathlib import Path;P=Path('langdetect/langdetect/profiles');chars=set();[chars.update(k) for p in P.iterdir() for k in json.loads(p.read_text(encoding='utf-8'))['freq']];print(len(chars), hex(max(map(ord,chars))), '\"' in chars, '\\\\' in chars)"
```

> 说明：A 段全部数字来自 `tools/profile_stats.py`；上表的百分比由脚本内 `len_dist/total` 计算后写入 `analysis/profile-facts.md`。

---

## B. MoonBit 编译期内嵌探针

工程：`probes/embed-probe/`（`moon new` 创建，`moon.mod` 中 `preferred_target = "native"`）。
生成器：`probes/gen_mbt.py`；测量脚本：`probes/measure_scale.py`。

复现命令（每档均先 `moon clean` 再全量编译，因此是冷编译）：

```
python probes/measure_scale.py --mode map  --langs 1   --label s1-map   --builds 3
python probes/measure_scale.py --mode map  --langs 5   --label s5-map   --builds 3
python probes/measure_scale.py --mode map  --langs all --label s55-map  --builds 2
python probes/measure_scale.py --mode flat --langs 1   --label s1-flat  --builds 3
python probes/measure_scale.py --mode flat --langs 5   --label s5-flat  --builds 3
python probes/measure_scale.py --mode flat --langs all --label s55-flat --builds 2
```

`--langs 5` 对应 `so,sw,tl,af,en`；`--langs all` 为 55 个语言（排序后）。

### B.1 两种编码（实际使用的形态）

| 编码 | 生成形态 | 运行时 |
|---|---|---|
| `map` | 每语言一个 `Map[String, Int]` 字面量，经 `Map::from_array([...])` 构造 | 直接查表 |
| `flat` | 每语言一个扁平 `String`，内容为 `key\tcount\n` 重复 | `profile()` 内 `split("\n")` + `split("\t")` + `@string.parse_int` 解析 |

`flat` 是本次选择的紧凑编码（扁平字符串 + 运行时解析）。生成示例（`probes/embed-probe/lib/data/data.mbt`）：

```moonbit
let so : String = "YO \t13\njec\t34\n..."
```

### B.2 测量结果总表

| 标签 | 编码 | 语言数 | 条目数 | 生成 `data.mbt` 字节 | native 冷编译耗时范围(s) | 可执行文件字节 | `_build` 总字节 | `moon test` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| s1-map | map | 1 | 1,874 | 30,320 | 0.721–0.864 | 404,480 | 1,973,350 | 通过 2/2 |
| s5-map | map | 5 | 9,961 | 173,424 | 0.924–0.929 | 1,247,232 | 4,481,004 | 通过 6/6 |
| s55-map | map | 55 | 184,129 | 3,495,481 | 15.019–15.357 | 19,826,688 | 60,782,304 | **失败**：`0xc00000fd` |
| s1-flat | flat | 1 | 1,874 | 17,498 | 0.692–0.709 | 245,248 | 1,520,247 | 通过 2/2 |
| s5-flat | flat | 5 | 9,961 | 103,877 | 0.695–0.727 | 385,536 | 1,872,890 | 通过 6/6 |
| s55-flat | flat | 55 | 184,129 | 2,205,308 | 2.814–2.830 | 3,256,320 | 9,390,104 | 通过 56/56 |

逐次耗时与日志：

| 标签 | 第 1 次(s) | 第 2 次(s) | 第 3 次(s) | 日志 |
| --- | ---: | ---: | ---: | --- |
| s1-map | 0.721 | 0.864 | 0.746 | `probes/logs/s1-map-02-build{1,2,3}.log` |
| s5-map | 0.929 | 0.926 | 0.924 | `probes/logs/s5-map-02-build{1,2,3}.log` |
| s55-map | 15.019 | 15.357 | —（按 2 次） | `probes/logs/s55-map-02-build{1,2}.log` |
| s1-flat | 0.694 | 0.709 | 0.692 | `probes/logs/s1-flat-02-build{1,2,3}.log` |
| s5-flat | 0.727 | 0.706 | 0.695 | `probes/logs/s5-flat-02-build{1,2,3}.log` |
| s55-flat | 2.814 | 2.830 | —（按 2 次） | `probes/logs/s55-flat-02-build{1,2}.log` |

### B.3 逐档证据

**s1-map** — `probes/logs/s1-map-02-build1.log`

```
$ C:\Users\Administrator\.moon\bin\moon.exe build --target native
exit=0 wall_seconds=0.721
```
`probes/logs/s1-map-03-test.log`：`Total tests: 2, passed: 2, failed: 0.`
`probes/logs/s1-map-04-run.log`：`so: 1874` / `total: 1874`，exit=0。
结论：1 语言可编译、可运行、断言通过。

**s5-map** — `probes/logs/s5-map-02-build1.log`：`exit=0 wall_seconds=0.929`。
`probes/logs/s5-map-03-test.log`：`Total tests: 6, passed: 6, failed: 0.`
`probes/logs/s5-map-04-run.log`：`so: 1874 / sw: 1770 / tl: 1873 / af: 2143 / en: 2301 / total: 9961`。
结论：5 语言通过。

**s55-map（关键失败）** — 编译成功：

```
$ C:\Users\Administrator\.moon\bin\moon.exe build --target native
exit=0 wall_seconds=15.019
Finished. moon: ran 10 tasks, now up to date (1 warnings, 0 errors)
```

运行失败（`probes/logs/s55-map-04-run.log`）：

```
$ ...\_build\native\debug\build\cmd\main\main.exe
exit=3221225725 wall_seconds=0.133
--- stdout ---
（空）
```

测试失败（`probes/logs/s55-map-03-test.log`，第 53 行）：

```
Error: failed to run test for target Native
Caused by:
    Failed to run the test: ...\embed-probe.blackbox_test.exe
    The test executable exited with exit code: 0xc00000fd
```

`3221225725 = 0xC00000FD`（STATUS_STACK_OVERFLOW）。测试进程耗时 19.563 s 后崩溃，未打印 `Total tests`。
结论：55 语言 `Map` 字面量可编译链接，但产物启动即栈溢出，断言未执行。

**s1-flat** — `probes/logs/s1-flat-02-build1.log`：`exit=0 wall_seconds=0.694`；`s1-flat-03-test.log`：`Total tests: 2, passed: 2, failed: 0.`。

**s5-flat** — `probes/logs/s5-flat-02-build1.log`：`exit=0 wall_seconds=0.727`；`s5-flat-03-test.log`：`Total tests: 6, passed: 6, failed: 0.`；`s5-flat-04-run.log`：`total: 9961`。

**s55-flat（关键成功）** — `probes/logs/s55-flat-02-build1.log`：

```
$ C:\Users\Administrator\.moon\bin\moon.exe build --target native
exit=0 wall_seconds=2.814
```

`probes/logs/s55-flat-03-test.log`：

```
exit=0 wall_seconds=4.206
Total tests: 56, passed: 56, failed: 0.
```

`probes/logs/s55-flat-04-run.log`：

```
exit=0 wall_seconds=0.323
af: 2143
ar: 2626
...
zh-tw: 2104
total: 184129
```

56 条测试 = 55 条「每语言条目数 + 抽样键值」断言 + 1 条「语言数=55」断言，由 `gen_mbt.py` 生成到 `probes/embed-probe/embed-probe_test.mbt`。
结论：55 语言全部内嵌、编译、测试、运行均通过。

### B.4 紧凑编码与 map 的对比（55 语言）

| 指标 | map | flat | flat / map |
| --- | ---: | ---: | ---: |
| 生成 `data.mbt` 字节 | 3,495,481 | 2,205,308 | 0.6309 |
| native 冷编译（最小值） | 15.019 s | 2.814 s | 0.1874 |
| 可执行文件字节 | 19,826,688 | 3,256,320 | 0.1642 |
| `_build` 总字节 | 60,782,304 | 9,390,104 | 0.1545 |

比值由 `python tools/summarize_probes.py` 从 `probes/results/*.json` 计算，见 `analysis/probe-tables.md`。

### B.5 编译期体积旁证

55 语言 `flat` 下各目标 `_build` 体积（`python` 扫描 `_build/<target>`，结果存 `probes/results/artifacts.json`）：

| 目标 | 全部文件字节 | 最大文件 |
| --- | ---: | --- |
| native | 34,653,899 | `debug/test/__moonbit_link_core__/embed-probe.blackbox_test.obj` (4,124,103) |
| wasm-gc | 26,199,542 | `debug/test/embed-probe.blackbox_test.wasm.map` (3,462,091) |
| js | 7,185,589 | `debug/build/cmd/main/main.js.map` (3,052,327) |

---

## C. 目标可用性探针

探针数据形态固定为：55 语言 `flat` 编码 + 56 条断言（与 `s55-flat` 相同）。
脚本：`probes/probe_targets.py`；结果：`probes/results/targets.json`。

复现命令：

```
python probes/gen_mbt.py --mode flat --langs all
python probes/probe_targets.py
```

### C.1 三目标 build / test

| 目标 | 命令 | build 退出码 | build 秒 | test 退出码 | test 秒 | 结论 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| native | `moon build --target native` / `moon test --target native` | 0 | 4.969 | 0 | 4.624 | 通过（56/56） |
| wasm-gc | `moon build --target wasm-gc` / `moon test --target wasm-gc` | 0 | 2.610 | 4294967295 | 3.063 | build 通过，test 失败 `0xc0000139` |
| js | `moon build --target js` / `moon test --target js` | 0 | 2.808 | 0 | 3.928 | 通过（56/56，需可用 node） |

原始输出关键行：

- `probes/logs/target-native-01-build.log`：`exit=0`；`target-native-02-test.log` 第 5 行：`Total tests: 56, passed: 56, failed: 0.`
- `probes/logs/target-wasm-gc-01-build.log`：`exit=0`；`target-wasm-gc-02-test.log` 第 53 行：
  `The test executable exited with exit code: 0xc0000139`
- `probes/logs/target-js-01-build.log`：`exit=0`；`target-js-02-test.log` 第 5 行：`Total tests: 56, passed: 56, failed: 0.`

`4294967295` 是 Python 对进程返回 `-1` 的无符号表示；`0xC0000139` = `STATUS_ENTRYPOINT_NOT_FOUND`。

### C.2 历史现象复核

**wasm-gc 的 `0xc0000139`：可复现，且与档案数据无关。**
空工程对照 `probes/tiny-probe`（`moon new` 后仅加 1 条 `assert_eq(1 + 1, 2)`）：

```
python probes/probe_tiny.py
```

`probes/logs/tinyprobe-test-wasm-gc.log`：

```
$ moon test --target wasm-gc
exit=4294967295
Caused by:
    Failed to run the test: ...\tiny-probe\_build\wasm-gc\debug\test\p\p.internal_test.wasm
    The test executable exited with exit code: 0xc0000139
```

同一空工程 native 与 js 均通过（`tinyprobe-test-native.log`：`Total tests: 1, passed: 1, failed: 0.`；`tinyprobe-test-js.log` 同）。

进一步定位：`moonrun.exe` 自身即无法启动——

```
$ C:\Users\Administrator\.moon\bin\moonrun.exe
exit=3221225785 (0xc0000139)
（stdout/stderr 均为空）
```

日志：`probes/logs/moonrun-noargs.log`、`moonrun-help.log`、`moonrun-tiny-main.log`、`moonrun-embed-main.log`（四者均 `0xc0000139`）。
PE 导入表检查（`python` 解析 `moonrun.exe`）：依赖 `VCRUNTIME140.dll`、`VCRUNTIME140_1.dll` 等；`C:\Windows\System32\vcruntime140.dll` 与 `vcruntime140_1.dll` 版本均为 `14.51.36247.0`，文件存在。
结论：wasm-gc 测试失败是**本机 `moonrun.exe` 无法加载**导致，任何 wasm-gc 测试都会失败，与内嵌数据规模无关；根因未定位到具体缺失符号（未测）。

**js 的 “path not found”：可复现，原因是 `node` 不可用。**
本机 `node` 来自 `C:\Users\Administrator\.bunpm\bin\node.cmd`，其内容指向不存在的路径：

```
@echo off
"D:\nvm4w\nodejs\bun" %*
```

实测：

```
$ node --version
exit=1
The system cannot find the path specified.
```

（`probes/logs/node-plain-version.log`）

无 shim 时 `moon test --target js`（`probes/logs/target-js-02-test-noshim.log`）：

```
exit=4294967295
The system cannot find the path specified.
Error: failed to run test for target Js
Caused by:
    Failed to run the test: ...\embed-probe.blackbox_test.js
    The test executable exited with exit code: 1
```

使用 `probes/bin/node.cmd`（指向真实 `C:\Users\Administrator\.bun\bin\bun.EXE`）前置到 PATH 后，js 测试通过：

```
$ probes\bin\node.cmd --version
exit=0
1.4.3
```

（`probes/logs/node-shim-version.log`；`probes/logs/jsrunner-moon-test-js.log` 显示 `Total tests: 2, passed: 2, failed: 0.` 为小规模复测，`target-js-02-test.log` 为 56 条全量。）
结论：js 目标本身可用，历史 “path not found” 是本机 node 安装损坏；本报告所有 js 通过结论均建立在 `probes/bin/node.cmd` → bun 的替代运行时上（非官方 node）。

### C.3 native 侧文件读取能力

检索命令与原始输出：

```
$ moon ide doc @fs
package "moonbitlang/async/fs" // moonbitlang/async@0.21.3
pub async fn read_file(StringView, sync_timestamp? : Bool) -> &@io.Data
...
pub async fn open(StringView, mode~ : Mode, ...) -> File
```

（`probes/logs/idedoc-at-fs.log`）

```
$ moon ide doc read_file
package "moonbitlang/async/fs" // moonbitlang/async@0.21.3
pub async fn read_file(StringView, sync_timestamp? : Bool) -> &@io.Data
  Read the contents of the file located at `path`.
```

（`probes/logs/idedoc-read_file.log`）

```
$ moon ide doc open_file
exit=1
No results found for query: 'open_file'
```

（`probes/logs/idedoc-open_file.log`）

包与符号确认：

- 包名：`moonbitlang/async/fs`（`moonbitlang/async@0.21.3`），符号 `read_file`、`open`、`File`、`File::read_all`。
- 本机缓存位置：`C:\Users\Administrator\.moon\registry\cache\moonbitlang\async\0.21.3.zip`，`src/fs/file.mbt:491` 定义 `pub async fn read_file`。
- 未找到名为 `@fs` 的 core 包；`@fs` 查询命中的是 `moonbitlang/async/fs`。

可用性实测（`probes/fs-probe`，`moon add moonbitlang/async@0.21.3`）：

```
$ moon build --target native
exit=0
$ ...\fs-probe\_build\native\debug\build\cmd\main\main.exe
exit=0
chars=28151
has_freq=true
```

（`probes/logs/fsprobe-build.log`、`probes/logs/fsprobe-run.log`）
该程序用 `@fs.read_file("../../langdetect/langdetect/profiles/en")` 读取真实档案并检查内容包含 `freq`，读到的字符数 28,151 与档案字节数 28,154 相符（差值为文件末尾换行/字符计数口径）。
结论：native 侧存在可用的文件读取 API，并已实测读取真实档案成功。

跨目标限制（同一 fs-probe）：

```
$ moon build --target wasm-gc
exit=4294967295
Value read_file not found in package `fs`.
```

（`probes/logs/fsprobe-build-wasm-gc.log`；js 同样 `failed when building project`，见 `fsprobe-build-js.log`）
原因：`moonbitlang/async` 的 `src/fs/moon.pkg` 用 `targets:` 把 `file.mbt` 限定为 `["native", "wasm"]`，wasm-gc/js 无该符号。
结论：文件读取 API 仅 native（及 wasm）可用，wasm-gc/js 不可用。

### C.4 发布侧体积/文件数限制

```
$ moon publish --help
exit=0
Publish the current module
...（输出中无体积或文件数限制条款）
```

（`probes/logs/publish-help.log`）

```
$ mooncake --help
exit=1
`mooncake` should not be called directly. Please use `moon` instead.
```

（`probes/logs/mooncake-help.log`）

打包实测（`moon package`，55 语言 flat 数据）：

```
$ moon package
exit=0
Package to ...\_build\publish\vicoproplus-embed-probe-0.1.0.zip
```

（`probes/logs/package.log`；`probes/results/package.json`）

| 指标 | 实测 |
|---|---:|
| zip 字节 | 949,937 |
| zip 内文件数 | 12 |
| 最大成员 | `lib/data/data.mbt` 2,205,308 字节 |

`moon publish --dry-run` 尝试联网发布，实测失败于网络而非体积：

```
request or response body error for url (https://mooncakes.io/api/v0/publish): send failed because receiver is gone
Error: `moon publish` failed
```

（同一次 `python` 调用输出，未落独立日志；命令为 `moon publish --dry-run`，cwd=`probes/embed-probe`）
结论：`moon publish --help` 与 `mooncake --help` 中**未出现**包体积或文件数限制；无法据此认定存在限制。服务端是否限制：**未取证**（未成功发布）。

---

## D. 未测 / 失败 / 超时

| 类别 | 项目 | 说明 |
| --- | --- | --- |
| 失败 | `s55-map` 的 `moon test --target native` | `0xC00000FD` 栈溢出，测试未执行完（`probes/logs/s55-map-03-test.log`） |
| 失败 | `s55-map` 的可执行文件运行 | 退出码 `3221225725`，无输出（`probes/logs/s55-map-04-run.log`） |
| 失败 | `moon test --target wasm-gc`（任何工程） | `0xC0000139`；空工程同样失败，`moonrun.exe` 自身无法启动 |
| 失败 | `moon test --target js`（默认 PATH） | `The system cannot find the path specified.`；本机 `node.cmd` 指向不存在的 `D:\nvm4w\nodejs\bun` |
| 失败 | `moon build --target wasm-gc` / `js`（`probes/fs-probe`） | `Value read_file not found in package fs`（`fs` 仅 native/wasm） |
| 失败 | `moon publish --dry-run` | 网络错误 `send failed because receiver is gone` |
| 未测 | wasm-gc 目标在「可用 moonrun」环境下的真实结果 | 本机 moonrun 无法启动，无法区分目标问题与运行器问题 |
| 未测 | js 目标在官方 node 下的结果 | 本机 node 损坏，仅用 bun 替代验证 |
| 未测 | `moon publish` 服务端体积/文件数限制 | 未成功发布，`--help` 无相关条款 |
| 未测 | `s55-map` 失败的具体栈溢出调用点 | 未做栈回溯/调试 |
| 超时 | — | 无。55 语言 map 编译 15.019–15.357 s，远低于 15 分钟阈值，因此**未触发超时，也无外推** |

---

## E. 汇总表（A + B + C）

| 段 | 指标 | 数值 |
| --- | --- | ---: |
| A | 档案文件数 | 55 |
| A | 档案总字节 | 2,204,952 |
| A | 条目总数 | 184,129 |
| A | 键长 1/2/3 | 7,791 / 52,387 / 123,951 |
| A | 非 1~3 长度键、非 BMP 条目 | 0 / 0 |
| B | 55 语言 map：生成字节 / 编译秒 / exe 字节 | 3,495,481 / 15.019–15.357 / 19,826,688 |
| B | 55 语言 flat：生成字节 / 编译秒 / exe 字节 | 2,205,308 / 2.814–2.830 / 3,256,320 |
| B | 55 语言 flat 测试 | 56/56 通过 |
| B | 55 语言 map 测试 | 失败 `0xC00000FD` |
| C | native build/test | 通过 / 通过（56/56） |
| C | wasm-gc build/test | 通过 / 失败 `0xC0000139`（空工程同样失败） |
| C | js build/test | 通过 / 通过（56/56，依赖 bun 替代 node） |
| C | native 文件读取 | `moonbitlang/async/fs.read_file` 实测读取档案成功 |

## F. 复现清单

```
python tools/profile_stats.py
python probes/gen_mbt.py --mode flat --langs all
python probes/measure_scale.py --mode map  --langs 1   --label s1-map   --builds 3
python probes/measure_scale.py --mode map  --langs 5   --label s5-map   --builds 3
python probes/measure_scale.py --mode map  --langs all --label s55-map  --builds 2
python probes/measure_scale.py --mode flat --langs 1   --label s1-flat  --builds 3
python probes/measure_scale.py --mode flat --langs 5   --label s5-flat  --builds 3
python probes/measure_scale.py --mode flat --langs all --label s55-flat --builds 2
python probes/probe_targets.py
python probes/probe_js_runner.py
python probes/probe_tiny.py
python tools/summarize_probes.py
```

补充命令（按需）：

```
moon ide doc @fs
moon ide doc read_file
moon publish --help
mooncake --help
moon package
moon test --target wasm-gc        # cwd = probes/tiny-probe（空工程对照）
C:\Users\Administrator\.moon\bin\moonrun.exe      # 复现 0xc0000139
```

`probes/probe_targets.py` 会在 PATH 前置 `probes/bin`（内含 `node.cmd` → bun），以获得可用的 js 运行时；去掉该前置即复现 js 的 “path not found”。
