# 约定 B：U3 Unicode 大小写表生成契约（v1）

> **文档标题（机器可检索）**：`约定 B：U3 Unicode 大小写表生成契约`
> **版本**：v1（2026-10-20）
> **状态**：生效
> **上游裁决**：`docs/port/architecture-decisions.md` U 行（U3 内嵌表）、P 行（零第三方依赖）
> **被引用于**：`docs/superpowers/designs/202610202129-moon-langdetect-语种检测-design.md` §八

## 1. 适用范围

任何承载「字符是否为大写」判定的内嵌表（供 `is_upper_cp312` 使用）。表**只允许**由 CPython 生成；禁止由第三方 Unicode 数据集（如 `moonbit-community/unicode-data`）生成或校对。

## 2. 约定正文（每条硬承诺）

| 编号 | 硬承诺 | 机检断言 | 门禁命令 | 失败退出码 |
|---|---|---|---|---|
| B1 | 生成源 = 本仓库 `.venv` 内的 CPython **3.12.10** | `sys.version` 以 `3.12.10` 开头；`unicodedata.unidata_version` = `15.0.0` | 见 §3 命令 C-B1 | 1 |
| B2 | 判定口径 = `chr(cp).isupper()` 真值，**且**这两个字段必须写入表头 | 表头含 `python_version=3.12.10` 与 `unidata_version=15.0.0` 两行 | 见 §3 命令 C-B2 | 1 |
| B3 | True 码点数 = **1951**（跳过 2048 个 surrogate，可比 1112064 点） | 计数 = 1951 | 见 §3 命令 C-B3 | 1 |
| B4 | 压缩为区间表后区间数 = **651**（grep 实测，产品表可用矩阵计数核对） | 区间数 = 651 | 见 §3 命令 C-B4 | 1 |
| B5 | 表与 CPython 全码点对拍，不一致数 = **0** | 逐点比对不一致计数 = 0 | 见 §3 命令 C-B5 | 1 |
| B6 | 表内不得出现 `moonbitlang/x` 或 `unicode-data` 的引用 | `grep -c` = 0 | 见 §3 命令 C-B6 | 1 |

## 3. 门禁命令（可重跑）

```bash
# C-B1 / C-B3 / B4：生成源版本、True 计数、区间数
.venv/Scripts/python.exe -c "
import sys,unicodedata
assert sys.version.split()[0]=='3.12.10', sys.version
assert unicodedata.unidata_version=='15.0.0', unicodedata.unidata_version
cps=[cp for cp in range(0x110000) if not (0xD800<=cp<=0xDFFF) and chr(cp).isupper()]
assert len(cps)==1951, len(cps)
iv=[]
for cp in cps:
    if iv and cp==iv[-1][1]+1: iv[-1][1]=cp
    else: iv.append([cp,cp])
assert len(iv)==651, len(iv)
print('ok 1951 cps / 651 intervals')"

# C-B2：表头版本字段（$T = 产品表路径，生成后登记）
head -3 "$T" | grep -q 'python_version=3.12.10' && head -3 "$T" | grep -q 'unidata_version=15.0.0'

# C-B5：全码点对拍（由产品测试承载；不一致数必须为 0）
# 断言语句：@ucd 表逐点与 CPython 输出的 json goldens 比对，diff 计数 == 0

# C-B6：无第三方 Unicode 包引用
test "$(grep -rlE 'moonbitlang/x|unicode-data' lib/ | wc -l)" = "0"
```

**实测记录（2026-10-20）**：C-B1/C-B3/C-B4 输出 `ok 1951 cps / 651 intervals`，退出码 0。B2/B5/B6 在产物生成后登记（见 T16/T17）。

## 4. 诊断依据（为何必须是这个版本）

`docs/port/c1-residual-risks.md` §1 实测：CPython 3.12.10 的 `unicodedata.unidata_version` = **15.0.0**，而 `unicode-data@0.6.0` 是 **18.0.0**；两者在全码点口径下有 **75** 个不一致码点（全部 `Python=0 / MoonBit=1`，Python 类别全为 `Cn`）。该差异在任意用户输入上可触发：`rep_THE_tje` 实测首选语言从 `vi` 变 `en`（`docs/port/c1-residual-risks.md` §1.7）。因此表必须锚定 CPython 3.12.10 而非第三方数据集的版本。

## 5. 生成物所有权（GO1-GO3）

| 项 | 内容 |
|---|---|
| 生成工具 | 从 `.venv` CPython 直读 `unicodedata` 的生成脚本（待实现，T16） |
| 覆盖行为 | **整文件重建** |
| 不手改清单 | 表的区间正文与表头；改生成源或改口径（升 CPython 版本）而非改产物 |
| 版本漂移处置 | 上游改用其他 Python/Unicode 版本运行 → 重生成并把表头版本字段同步改写（ADR R13） |
