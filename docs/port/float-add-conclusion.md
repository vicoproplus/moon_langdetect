# 浮点累加逐位一致性结论（MoonBit native vs CPython 3.12）

结论先行：**MoonBit(native) 的 `Double` 顺序累加与 CPython 3.12 逐位一致（bit-exact）**；
但上游 `_normalize_prob` 里的 `sum(prob)` **不是**朴素左到右求和——CPython 3.12 的内建
`sum()` 走 Neumaier 补偿求和，移植时必须照抄该算法，否则 `sump` 会在绝大多数组上差
1 ulp。

## 执行环境

| 项 | 值 |
| --- | --- |
| MoonBit 工具链 | moon 0.1.20261012 / moonc v0.10.15 |
| 构建 | `moon build --target native`（cwd = `probes/rand-probe`） |
| CPython | 3.12.10 (tags/v3.12.10) [MSC v.1943 64 bit (AMD64)] |
| 随机源 | `random.Random(0)`，MT19937，输入位型已被 `probes/rand_probe_compare.py` 验证一致 |

探针：`probes/rand-probe/cmd/float/main.mbt`（新包，复用根库 `@rp.Random`，
未新建工程）。输入由探针按固定配方现场生成，Python 侧同一配方重放。

## 逐场景结果（全部来自真实运行）

| 场景 | 组数 | 比较对象 | 对数 | 逐位一致 | 首个不一致 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| A-uniform（55 个 `[1/55,1)` 正数，打乱后累加） | 200 | 输入位型 | 11000 | 11000 | 无 | 一致 |
| A-uniform | 200 | 朴素左到右累加 | 200 | 200 | 无 | 一致 |
| A-uniform | 200 | Neumaier 补偿累加 | 200 | 200 | 无 | 一致 |
| B-extreme（1e300 × 1e-300 混次正规、含 1e300+(-1e300) 相消） | 50 | 输入位型 | 2750 | 2750 | 无 | 一致 |
| B-extreme | 50 | 朴素左到右累加 | 50 | 50 | 无 | 一致 |
| B-extreme | 50 | Neumaier 补偿累加 | 50 | 50 | 无 | 一致 |
| C-negative（正负巨量混合，模拟负 alpha） | 50 | 输入位型 | 2750 | 2750 | 无 | 一致 |
| C-negative | 50 | 朴素左到右累加 | 50 | 50 | 无 | 一致 |
| C-negative | 50 | Neumaier 补偿累加 | 50 | 50 | 无 | 一致 |
| C-negative | 50 | `prob[j]/sump_naive`（2750 个） | 2750 | 2750 | 无 | 一致 |
| C-negative | 50 | `prob[j]/sump_builtin`（2750 个） | 2750 | 2750 | 无 | 一致 |
| E-stochastic（完整 `_detect_block`+`_normalize_prob` 链路） | 7 | 输入位型 | 385 | 385 | 无 | 一致 |
| E-stochastic | 7 | 朴素左到右累加 | 7 | 7 | 无 | 一致 |
| E-stochastic | 7 | Neumaier 补偿累加 | 7 | 7 | 无 | 一致 |
| E-stochastic | 7 | `prob[j]/sump_naive`（385 个） | 385 | 385 | 无 | 一致 |
| E-stochastic | 7 | `prob[j]/sump_builtin`（385 个） | 385 | 385 | 无 | 一致 |
| D-langprob7（`langprob[j] += h[j]/7`，7 轮 × 55） | 7 | 每轮后 langprob 状态 | 385 | 385 | 无 | 一致 |

合计 24154 个逐位比较值（MoonBit 探针 stdout 24160 行），**没有任何首个不一致**。

产物：

- `docs/port/golden/float_add_python.json`（`tools/gen_float_golden.py` 生成）
- `docs/port/golden/float_add_compare.json`（`probes/float_probe_compare.py` 生成）

## Python 内建 `sum()` 的真实语义（必须照抄）

| 比较 | 对数 | 一致 | 首个不一致 |
| --- | --- | --- | --- |
| `sum(xs)` vs 显式 `acc = acc + x` | 307 | **69** | A-uniform 组 1：builtin `4039bd256889ff8d` vs 循环 `4039bd256889ff8c` |
| `sum(xs)` vs Neumaier 复刻 | 307 | **307** | 无 |

逐场景「内建 sum 与朴素循环不一致」的组数：A-uniform 145/200，B-extreme 50/50，
C-negative 40/50，E-stochastic 3/7。因此 `sum(prob)` 这个调用是**补偿求和**，
移植 MoonBit 侧必须实现同一个 Neumaier 循环（`hi + c` 收尾，
`abs(hi) >= abs(x)` 决定补偿项取 `(hi - total) + x` 还是 `(x - total) + hi`），
不能替换为朴素顺序累加。

归一化也连带受影响：C-negative 有 2027/2750 个 `prob[j]/sump` 因分母不同而不同，
E-stochastic 有 164/385 个。例如 C-negative 组 0：
`sum_builtin = 7e6d1b15cdc9d78e`，`sum_naive = 7e6d1b15cdc9d78f`。

## 关键事实清单

1. `Double` 的 `+`、`/`、`*` 在 MoonBit(native) 与 CPython(x64) 上同指令、同舍入，
   逐位一致；探针全部输出（16885 个输入 + 614 个求和值（307 朴素 + 307 Neumaier）
   + 6270 个归一化 + 385 个 langprob 状态）全部对上。
2. 累加**顺序/算法**是唯一自由度：同一个数组，顺序累加得 `R`，Neumaier 得 `RNEU`，
   两者与 CPython 对应算法分别一致——移植方必须锁定算法与索引序。
3. `langprob[j] += prob[j] / self.n_trial`（n_trial=7）不是补偿求和：
   实测 Python 朴素循环与 MoonBit 朴素 `+` 逐位一致（385/385），照抄即可。
4. 次正规数（5e-324）与巨量（1e300）在两侧的加法/乘法/除法行为完全一致，
   B-extreme 50/50 组同步合。
5. `1.0/55.0` 等常量在两侧同为最接近表示（`3f929e4129e4129e`），无差异。

## 证据命令

```bash
# 1) 生成 CPython golden（也可单独执行，输出即上表数据）
.venv/Scripts/python.exe tools/gen_float_golden.py

# 2) 构建 MoonBit 探针并逐位比对，写 docs/port/golden/float_add_compare.json
.venv/Scripts/python.exe probes/float_probe_compare.py

# 3) 单独验证整个 rand-probe 工程仍可编译 / 测试
cd probes/rand-probe && C:/Users/Administrator/.moon/bin/moon.exe build --target native
cd probes/rand-probe && C:/Users/Administrator/.moon/bin/moon.exe test --target native
```

`moon test --target native`：`Total tests: 4, passed: 4, failed: 0`。

## 明确答案

**MoonBit(native) 与 CPython 3.12 的顺序 `Double` 累加是逐位一致的（bit-exact）。**
在本报告覆盖的全部场景（200 组常规 + 50 组尺度极端 + 50 组负值 + 7 轮 `+= h/7` +
7 组全链路归一化，共 24154 个比较值）中没有出现任何一次末位差异。

唯一的坑不在 MoonBit，而在 Python：`sum(prob)` 在 CPython 3.12 是 Neumaier 补偿求和
（307 组里只有 69 组与朴素循环相同）。MoonBit 移植 `_normalize_prob` 时必须实现同一个
Neumaier 循环；若误用朴素顺序累加，`sump` 会在 A-uniform 145/200、B-extreme 50/50、
C-negative 40/50、E-stochastic 3/7 的组上与上游差 1 ulp，并向下游 `prob[i] = p/sump`
传播（C-negative 有 2027/2750 个归一化值因此改变）。
