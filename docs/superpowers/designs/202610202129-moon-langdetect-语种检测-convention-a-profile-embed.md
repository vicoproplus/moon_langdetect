# 约定 A：档案内嵌数据格式与生成契约（v1）

> **文档标题（机器可检索）**：`约定 A：档案内嵌数据格式与生成契约`
> **版本**：v1（2026-10-20）
> **状态**：生效
> **上游裁决**：`docs/port/architecture-decisions.md` D 行（编译期内嵌 + flat 紧凑编码）
> **被引用于**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-design.md` §八

## 1. 适用范围

任何承载 55 个语言档案的内嵌数据产物（探针样本 `probes/embed-probe/lib/data/data.mbt`、后续产品生成物）。本约定只管**编码形态与生成契约**，不管解析实现的内部结构。

## 2. 约定正文（每条硬承诺）

| 编号 | 硬承诺 | 机检断言 | 门禁命令 | 失败退出码 |
|---|---|---|---|---|
| A1 | 每个语言一个扁平字符串声明，内容为 `key\tcount\n` 重复；语言声明数 = 55 | 声明行计数 = 55 且每行可被 `^let \w+ : String = ".*"$` 匹配 | 见 §3 命令 C-A1 | 1 |
| A2 | 条目总数（`\n` 分隔行数之和）= 184129 | 求和 = 184129 | 见 §3 命令 C-A2 | 1 |
| A3 | 参考样本字节数 = 2205308 | `wc -c` = 2205308 | 见 §3 命令 C-A3 | 1 |
| A4 | 产物内不得出现 `Map::from_array` 形式的字面量构造；仅允许运行时 `Map([])` | `grep -c "Map::from_array"` = 0 | 见 §3 命令 C-A4 | 1 |
| A5 | 生成器只产 flat 形态；`--mode map` 不得用于 55 语言 | 生成清单 `mode` 字段 = `"flat"` | 见 §3 命令 C-A5 | 1 |
| A6 | 产物首行含「由 … 生成，勿手改」标记 | 首行匹配 `生成` 且 `勿手改` | 见 §3 命令 C-A6 | 1 |

## 3. 门禁命令（可重跑）

在仓库根 `F:/moonbit比赛/moon_langdetect` 执行。`$F` 为被测产物路径。

```bash
# C-A1 / C-A2：声明数与条目数
F=probes/embed-probe/lib/data/data.mbt
python - "$F" <<'PY'
import re,sys
t=open(sys.argv[1],encoding='utf-8').read()
decls=re.findall(r'^let \w+ : String = "(.*)"$', t, re.M)
n=sum(d.count('\\n') for d in decls)
print('decls',len(decls),'entries',n)
sys.exit(0 if (len(decls)==55 and n==184129) else 1)
PY

# C-A3：字节数
test "$(wc -c < "$F" | tr -d ' ')" = "2205308"

# C-A4：禁止 Map 字面量构造
test "$(grep -c 'Map::from_array' "$F")" = "0"

# C-A5：生成清单 mode
python -c "import json,sys; sys.exit(0 if json.load(open('probes/gen-manifest.json',encoding='utf-8'))['mode']=='flat' else 1)"

# C-A6：生成标记
head -1 "$F" | grep -q '勿手改'
```

**实测记录（2026-10-20）**：C-A1/C-A2 输出 `decls 55 entries 184129`，退出码 0；C-A3 实测 2205308 字节；C-A4 实测 0 命中；C-A5 清单 `mode=flat`；C-A6 首行为 `// 由 probes/gen_mbt.py 生成，勿手改。编码: flat（key\tcount\n）`。证据：`probes/logs/s55-flat-04-run.log`（运行输出 `total: 184129`）、`analysis/toolchain-probes.md` §B.3。

## 4. 生成物所有权（GO1-GO3）

| 项 | 内容 |
|---|---|
| 生成工具 | `probes/gen_mbt.py`（探针样本）；产品生成器待定，须遵守本约定 |
| 覆盖行为 | **整文件重建**：每次生成覆盖目标 `data.mbt` 全文件 |
| 不手改清单 | `data.mbt` 全文；任何手改在下次生成时丢失，不构成交付证据 |
| 生成源优先 | 需改内容时改生成器或上游档案，不改产物 |

## 5. 已知边界

- 本条约定**不**约束产品生成器的文件路径与模块名（属 spec）。
- 字节数 2205308 是探针样本的实测值；产品产物若注释不同，A3 以产品路径重新登记基准值，但 A1/A2/A4 不得放松。
