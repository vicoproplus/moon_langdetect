# rand-probe

CPython 3.12 `random.Random` 随机数管线的 MoonBit(native) 逐位复刻探针。

用途：验证「固定 seed 下 langdetect 的 detect_langs 概率能否逐位复现」。

## 运行

```bash
# 1) 生成 Python golden
.venv/Scripts/python.exe tools/gen_rand_golden.py

# 2) 构建并运行 MoonBit 探针，逐位比对
.venv/Scripts/python.exe probes/rand_probe_compare.py
```

## 文件

- `rand-probe.mbt`：MT19937 / `random()` / `getrandbits` / `_randbelow` / `gauss` 实现
- `cmd/main/main.mbt`：输出各阶段序列（stdout，一行一条）
- `cmd/diag/main.mbt`：数学函数 libm 对照诊断（非主流程）

## 关键结论

`gauss` 必须用 libm 的 `log`（本包 `c_log` 绑定 `extern "C" log`），
不能用 `@math.ln`（纯 MoonBit 多项式实现，约 3% 输入差 1 ulp）。
`cos`/`sin`/`sqrt` 与 CPython 所用 libm 逐位一致。
