# 探针数据汇总（脚本生成）

由 `python tools/summarize_probes.py` 从 `probes/results/*.json` 生成。

## B. 内嵌规模测量

| 标签 | 编码 | 语言数 | 条目数 | 生成 data.mbt 字节 | 冷编译耗时(s) | 可执行文件字节 | _build 总字节 | moon test |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| s1-map | map | 1 | 1874 | 30320 | 0.721–0.864 | 404480 | 1973350 | 通过 |
| s5-map | map | 5 | 9961 | 173424 | 0.924–0.929 | 1247232 | 4481004 | 通过 |
| s55-map | map | 55 | 184129 | 3495481 | 15.019–15.357 | 19826688 | 60782304 | 失败：`The test executable exited with exit code: 0xc00000fd` |
| s1-flat | flat | 1 | 1874 | 17498 | 0.692–0.709 | 245248 | 1520247 | 通过 |
| s5-flat | flat | 5 | 9961 | 103877 | 0.695–0.727 | 385536 | 1872890 | 通过 |
| s55-flat | flat | 55 | 184129 | 2205308 | 2.814–2.830 | 3256320 | 9390104 | 通过 |

### 逐次冷编译耗时

| 标签 | 第 1 次 | 第 2 次 | 第 3 次 | 退出码 |
| --- | ---: | ---: | ---: | --- |
| s1-map | 0.721 | 0.864 | 0.746 | 0,0,0 |
| s5-map | 0.929 | 0.926 | 0.924 | 0,0,0 |
| s55-map | 15.019 | 15.357 | — | 0,0 |
| s1-flat | 0.694 | 0.709 | 0.692 | 0,0,0 |
| s5-flat | 0.727 | 0.706 | 0.695 | 0,0,0 |
| s55-flat | 2.814 | 2.830 | — | 0,0 |

## C. 三目标（55 语言 flat 数据 + 56 条断言）

| 目标 | build 退出码 | build 秒 | test 退出码 | test 秒 | 关键输出 |
| --- | ---: | ---: | ---: | ---: | --- |
| native | 0 | 4.969 | 0 | 4.624 | Total tests: 56, passed: 56, failed: 0. |
| wasm-gc | 0 | 2.610 | 4294967295 | 3.063 | The test executable exited with exit code: 0xc0000139 |
| js | 0 | 2.808 | 0 | 3.928 | Total tests: 56, passed: 56, failed: 0. |

### 空工程对照（probes/tiny-probe，1 条断言，无大数据）

| 目标 | test 退出码 | 关键输出 |
| --- | ---: | --- |
| native | 0 | Total tests: 1, passed: 1, failed: 0. |
| wasm-gc | 4294967295 | The test executable exited with exit code: 0xc0000139 |
| js | 0 | Total tests: 1, passed: 1, failed: 0. |

## 产物体积（55 语言 flat，按目标）

| 目标 | 全部文件字节 | 最大文件 |
| --- | ---: | --- |
| native | 34653899 | `debug/test/__moonbit_link_core__/embed-probe.blackbox_test.obj` (4124103) |
| wasm-gc | 26199542 | `debug/test/embed-probe.blackbox_test.wasm.map` (3462091) |
| js | 7185589 | `debug/build/cmd/main/main.js.map` (3052327) |

## 紧凑编码相对 map 的比值（55 语言）

| 指标 | map | flat | flat/map |
| --- | ---: | ---: | ---: |
| 生成字节 | 3495481 | 2205308 | 0.6309 |
| 冷编译秒(最小) | 15.019 | 2.814 | 0.1874 |
| 可执行文件字节 | 19826688 | 3256320 | 0.1642 |
| _build 字节 | 60782304 | 9390104 | 0.1545 |
