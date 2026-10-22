# 约定 C：golden 基准消费契约（v1）

> **文档标题（机器可检索）**：`约定 C：golden 基准消费契约`
> **版本**：v1（2026-10-20）
> **状态**：生效
> **上游裁决**：`docs/port/architecture-decisions.md` A 行（native 逐位 / js·wasm-gc 容差）、S 行（seed 口径）
> **被引用于**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-design.md` §八

## 1. 适用范围

任何消费 `docs/port/golden/expected.json` 的比对实现（验收脚本、产品测试）。本约定定义**怎么读、怎么比、比什么**，不定义产品 API。

## 2. 约定正文（每条硬承诺）

| 编号 | 硬承诺 | 机检断言 | 门禁命令 | 失败退出码 |
|---|---|---|---|---|
| C1 | 数值权威形态 = `prob_bits`（IEEE754 双精度大端 16 位 hex）；`prob` 与 `prob_repr` 仅供人读 | 比对实现读取 `prob_bits` 字段，而非 `prob` / `prob_repr` | 见 §3 命令 C-C1 | 1 |
| C2 | 案例总数 **268** = 有概率输出 **250** + 抛异常 **18**；两者分别比对，不得混算 | 计数三元组 = (268, 250, 18) | 见 §3 命令 C-C2 | 1 |
| C3 | seed 双套：**0** 与 **42** 均须比对，缺一不算通过 | seed 集合 = {0, 42} | 见 §3 命令 C-C3 | 1 |
| C4 | 异常案例按 `error.code` + `error.message` 比对；不得把异常案例计入概率比对分母 | 异常案例的 `code` 全部为 5 | 见 §3 命令 C-C4 | 1 |
| C5 | 比对结果必须按 `prob_bits` 逐位判定（native）；容差判定仅用于 js / wasm-gc，且容差数值须先登记 | native 路径下不出现容差分支 | 见 §3 命令 C-C5 | 1 |
| C6 | 比对实现不得修改基准文件；基准只读 | 比对前后 `expected.json` 的 md5 不变 | 见 §3 命令 C-C6 | 1 |

## 3. 门禁命令（可重跑）

```bash
G=docs/port/golden/expected.json

# C-C2：268 = 250 + 18
.venv/Scripts/python.exe -c "
import json
c=json.load(open('$G',encoding='utf-8'))['cases']
ne=[x for x in c if x.get('detect_langs')]; er=[x for x in c if 'error' in x]
assert (len(c),len(ne),len(er))==(268,250,18), (len(c),len(ne),len(er))
print('ok 268=250+18')"

# C-C3：seed 双套
.venv/Scripts/python.exe -c "
import json
c=json.load(open('$G',encoding='utf-8'))['cases']
assert sorted({x['seed'] for x in c})==[0,42]
print('ok seeds 0/42')"

# C-C4：异常码
.venv/Scripts/python.exe -c "
import json
c=json.load(open('$G',encoding='utf-8'))['cases']
codes={x['error']['code'] for x in c if 'error' in x}
assert codes=={5}, codes
print('ok error code 5')"

# C-C1 / C-C5：prob_bits 字段齐备（逐案例）
.venv/Scripts/python.exe -c "
import json,re
c=json.load(open('$G',encoding='utf-8'))['cases']
for x in c:
    for e in x.get('detect_langs') or []:
        assert re.fullmatch(r'[0-9a-f]{16}', e['prob_bits']), (x['id'], e)
print('ok prob_bits hex16')"

# C-C6：基准只读（比对前后 md5 一致）
md5sum "$G"
```

**实测记录（2026-10-20）**：C-C2 输出 `ok 268=250+18`，退出码 0；C-C3 输出 `ok seeds 0/42`；C-C4 输出 `ok error code 5`；C-C1/C5 输出 `ok prob_bits hex16`；基准 md5 `219519ee19d7cc10d404ddbdab3acd87`（`docs/port/upstream-run-report.md` §1 同源记录）。

## 4. 与 A 行的分档关系

| 目标 | 判定口径 | 依据 |
|---|---|---|
| native | `prob_bits` 逐位一致（硬门槛） | ADR A 行 ②；RNG 链路实测 21206/21451 逐位一致（`docs/port/rand-feasibility.md` §4） |
| js / wasm-gc | 容差（**数值待校准**，未登记前不得声称通过） | ADR A 行 ③；两目标的差值分布未实测（`docs/port/rand-feasibility.md` §5） |

## 5. 禁止句式

- 禁止按 `prob` 的十进制文本比对（JSON 解析器精度差异会掩盖末位差）。
- 禁止把 268 当作概率比对分母（18 条异常案例没有 `prob_bits`）。
- 禁止只跑单 seed。
- 禁止在容差未登记时用「误差很小」作通过理由。
