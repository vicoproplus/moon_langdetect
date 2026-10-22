# langdetect 上游实跑报告

- 生成日期：2026-10-20
- 工作目录：`F:/moonbit比赛/moon_langdetect`
- 上游：`langdetect` 1.0.9，只读位于 `langdetect/`（未修改任何文件）

---

## 1. 环境（实测命令输出）

| 项 | 值 | 实测命令 |
|---|---|---|
| Python | 3.12.10 (MSC v.1943 64bit) | `.venv/Scripts/python.exe -V` |
| pip | 26.2.1 | `.venv/Scripts/python.exe -m pip --version` |
| langdetect | 1.0.9（editable，指向 `langdetect/`） | `.venv/Scripts/python.exe -m pip show langdetect` |
| six | 1.17.0 | `.venv/Scripts/python.exe -m pip show six` |
| OS | win32 10.0.19045 x64 | 环境变量 |

`pip show` 实测输出：

```
Name: langdetect
Version: 1.0.9
Location: F:\moonbit比赛\moon_langdetect\.venv\Lib\site-packages
Editable project location: F:\moonbit比赛\moon_langdetect\langdetect
Name: six
Version: 1.17.0
Location: F:\moonbit比赛\moon_langdetect\.venv\Lib\site-packages
```

### 1.1 安装过程

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip -q
.venv/Scripts/python.exe -m pip install -e langdetect
```

**一次成功，无报错、无需兼容性绕过**：`six 1.17.0` 自动安装，Python 3.12 下 `six.moves.zip/xrange`、`six.iteritems`、`six.u` 均正常。`setup.py` 声明 `install_requires=['six']`（`langdetect/setup.py:22`）。安装耗时 43.80 s（含 build isolation 下载）。

### 1.2 一个必须知道的导入坑（非上游 bug，属环境）

仓库根目录下存在 `langdetect/`（git 仓库目录），**从仓库根运行 Python 时 `import langdetect` 会命中该目录，被解析为 namespace package**：

```
>>> import langdetect
>>> langdetect.__path__
_NamespacePath(['F:\\moonbit比赛\\moon_langdetect\\langdetect'])
>>> from langdetect import detect
ImportError: cannot import name 'detect' from 'langdetect' (unknown location)
```

`tools/gen_golden.py` 与 `tools/probe_facts.py` 通过 `sys.path.insert(0, <root>/langdetect)` 显式指向真正的包父目录，并断言 `langdetect.__file__` 以 `langdetect/__init__.py` 结尾，避免静默走错。

---

## 2. 复现命令

```bash
# 一次性
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e langdetect

# 生成 golden（约 3.3 s，含耗时测量）
.venv/Scripts/python.exe tools/gen_golden.py

# 逐项取证（用于核对契约文档中的每条断言）
.venv/Scripts/python.exe tools/probe_facts.py constants
.venv/Scripts/python.exe tools/probe_facts.py append_cleanup
.venv/Scripts/python.exe tools/probe_facts.py empty_variants
.venv/Scripts/python.exe tools/probe_facts.py language_sort
.venv/Scripts/python.exe tools/probe_facts.py unicode_blocks
.venv/Scripts/python.exe tools/probe_facts.py ngram_normalize
.venv/Scripts/python.exe tools/probe_facts.py profile_fields
.venv/Scripts/python.exe tools/probe_facts.py prob_formula
```

`tools/gen_golden.py` 是**幂等**的：每次覆盖 `cases.jsonl` / `expected.json` / `summary.json` / `timing.json`。同机同版本重复运行，`expected.json` 的 `cases` 段逐字节一致（seed 固定）；`timing.json` 每次不同。

---

## 3. 生成规模（全部由脚本输出）

`docs/port/golden/summary.json` 关键字段：

| 指标 | 值 |
|---|---|
| 案例总数 | **268** |
| seed=0 案例 | **134** |
| seed=42 案例 | **134** |
| 覆盖语言数 | **55** |
| `langlist` 长度 | **55** |
| 档案文件数 | **55** |
| 未设 seed 样本文本 | 7 条 × 10 次 = 70 次检测 |
| 同 seed 可重复性组 | 14 组（7 文本 × 2 seed，各 5 次） |
| seed 0 vs 42 差异组 | **125**（其中首位语言不变 122） |
| 抛异常案例 | 18（9 类输入 × 2 seed） |
| `detect_langs` 非空案例 | 250 |

语料构成（134 条 seed=0 基准）：

- `long-<lang>`：55 条，每语言 1 条中/长文本（实测 73–270 字符）
- `short-<lang>`：55 条，每语言 1 条短文本（实测 8–39 字符，全部 < 50）
- `extra-*`：24 条边界输入

24 条边界输入清单：`mixed-scripts-latin-cjk`、`mixed-scripts-cyrillic-latin`、`with-url`、`with-mail`、`with-url-and-mail`、`url-only`、`whitespace-only-spaces`、`whitespace-only-mixed`、`emoji-only`、`emoji-only-zwj`、`digits-only`、`digits-and-space`、`punctuation-only`、`empty`、`single-latin-char`、`single-ascii-upper`、`url-adjacent-text`、`capitalword-only`、`ascii-art-arrow`、`latin1-accents`、`cjk-ideographic-space`、`vietnamese-vi-normalization`、`mixed-long-en-ja`、`dotted-domains-only`。

档案量化（外部已核验，本次脚本复核一致）：55 文件、184,129 条目、键长仅 1/2/3 码点、无非 BMP 键。`word_lang_prob_map` 去重后 **87,598** 键（1-gram 3,159 / 2-gram 26,427 / 3-gram 58,012）。

---

## 4. 输出文件格式

### 4.1 `docs/port/golden/cases.jsonl`

每行一个 JSON 对象（UTF-8，无 BOM，`\n` 换行），字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 唯一 ID；seed=42 变体带 `@seed42` 后缀 |
| `text` | string | 原始输入 |
| `seed` | int | 0 或 42 |
| `tags` | string[] | `long` / `short` / `per-language` / `extra` |
| `intended_lang` | string \| null | 期望语言；`extra` 为 null |
| `text_len` | int | Python `len(text)`（码点数） |
| `text_sha256` | string | UTF-8 字节的 SHA-256，用于校验语料未被改动 |

### 4.2 `docs/port/golden/expected.json`

顶层：

```
{
  "meta":          { generator, upstream_version, python, langlist, langlist_size,
                     seeds_used, unknown_lang, note },
  "cases":         [ ... ],
  "unseeded_runs": [ ... ],
  "repeatability": [ ... ],
  "seed_diff":     [ ... ]
}
```

`cases[i]` 字段：

| 字段 | 说明 |
|---|---|
| `id` / `seed` / `tags` / `intended_lang` / `text_len` / `text_sha256` / `text` | 与 cases.jsonl 对应 |
| `detect` | `detect()` 返回值（string） |
| `detect_langs` | `[{lang, prob, prob_repr, prob_bits}, ...]`，**上游输出顺序** |
| `detect_langs_count` | 列表长度 |
| `error` | 仅异常案例：`{type, code, message}` |

浮点三份表示：
- `prob_repr`：Python `repr(float)`，最短往返字符串（可直接 `float()` 还原）
- `prob`：JSON 数字（同一 double）
- `prob_bits`：IEEE-754 double 大端 16 位 hex（如 `"3feb6db6fe663ab1"`），用于**逐位**比对，规避 JSON 解析器精度差异

示例（`long-zh-cn`，seed=0）：

```json
{"detect":"zh-cn",
 "detect_langs":[{"lang":"zh-cn","prob":0.8571429222809767,"prob_bits":"3feb6db6fe663ab1","prob_repr":"0.8571429222809767"},
                 {"lang":"ko","prob":0.1428563016252603,"prob_bits":"3fc2491d83c1064c","prob_repr":"0.1428563016252603"}],
 "detect_langs_count":2}
```

### 4.3 MoonBit 侧读取约束

- 纯 UTF-8、无 NaN/Infinity、无 Python 特有类型；`null` 只出现在 `intended_lang`。
- `prob_bits` 为权威数值，`prob_repr` 为人类可读回退。
- `cases.jsonl` 行数 = 268（实测 `wc -l` 等价）。

---

## 5. 耗时测量

方法（`tools/gen_golden.py: measure_timing`，写入 `timing.json.method`）：

- **冷启动**：新 Python 进程执行 `import langdetect.detector_factory` + `DetectorFactory().load_profile(PROFILES_DIRECTORY)`，采样 **5 次**取中位数。
- **进程内加载**：同进程内 `DetectorFactory().load_profile(...)` 单次计时。
- **单次检测**：已加载 factory 上新建 Detector，`append` 后**只计时 `get_probabilities()`**，每文本 **30 次**取中位数；seed 固定 0。

实测结果：

| 指标 | 中位数 | 备注 |
|---|---|---|
| 冷启动（import + load_profile） | **303.70 ms** | 5 样本：303.70 / 294.13 / 310.56 / 309.24 / 296.98 |
| 进程内 load_profile | **210.00 ms** | 单次 |
| `short_en`（26 字符） | **0.80 ms** | 30 样本，min 0.786 / max 1.187 |
| `long_en`（261 字符） | **1.69 ms** | 30 样本，min 1.498 / max 4.038 |
| `long_zh_cn`（85 字符） | **1.06 ms** | 30 样本，min 1.030 / max 1.885 |
| `long_ja`（91 字符） | **0.39 ms** | 30 样本，min 0.385 / max 0.709 |

观察：CJK 文本更快（归一化后大量字符塌缩为同一代表字，特征种类少、更易提前收敛到 >0.99999）；拉丁文本特征多样，迭代更久。

---

## 6. 结果质量

| 指标 | 命中 | 说明 |
|---|---|---|
| 长文本 seed=0 | **55/55** | 每语言 1 条，全部命中 |
| 短文本 seed=0 | **51/55** | miss：`short-bg`、`short-no`、`short-zh-cn`、`short-zh-tw` |
| seed=42 长文本 | 未单独统计 | 原始数据齐全，可按 `tags` 过滤自行统计 |

短文本 miss 的根因是 <50 字符时特征太少 + 7 轮随机抽样方差大；这是上游设计特性，非 bug。

---

## 7. 随机性与可复现性

| 场景 | 实测结果 | 证据 |
|---|---|---|
| 同 seed 重复 5 次（7 文本 × 2 seed = 14 组） | **全部逐字节一致** | `expected.json.repeatability[*].all_identical == true` |
| seed 0 vs 42（134 组） | **125 组** `detect_langs` 不同；其中 **122 组**首位语言不变 | `expected.json.seed_diff` |
| 未设 seed，重复 10 次（7 文本） | 仅 `"Otec matka syn."` 出现 2 种结果（`fi` / `pl`）；其余 6 条稳定 | `expected.json.unseeded_runs` |

seed 差异示例（`long-af`，首位语言相同，概率末位不同）：

```
seed=0 : af 0.9999968160091693
seed=42: af 0.9999962514686528
```

未设 seed 的不确定性示例：

```
"Otec matka syn."  → 10 次中出现 fi 与 pl 两种结果（distinct_count = 2）
```

> 结论：**只有固定 seed 才可做逐位回归**。golden 以 seed=0 / seed=42 双份固化。

---

## 8. 发现的 quirk 与兼容性坑（详见 `upstream-behavior-contract.md` §10）

1. **`cleaning_text` 的 Latin Extended Additional 豁免永不生效**（`detector.py:122` 拿 int 比字符串）→ 越南语字符被计入 non-latin，可能触发拉丁剥离。
2. **URL 字符类贪吃**：`'see http://a.com/x then TEXT-more'` → `'see then TEXT-more'`；`'http://a.com/x-then'` → `' '`（`-`/`.`/`;`/`/` 等都在字符类内，会继续吞后续 ASCII）。
3. **空/纯 emoji/纯数字/纯标点/纯 URL 抛 `CantDetectError(5)`**，不是返回 `'unknown'`。golden 中 18 条异常案例全部是这一类。
4. **`langprob` 缓存不随 `append` 失效**：同一 Detector 追加文本后 `detect()` 仍返回旧结果。
5. **`langsize` 取 `os.listdir` 长度**，点文件与子目录被计入但被跳过 → 概率向量长度可大于 `len(langlist)`。
6. **`load_profile` 把所有异常重包成 `FormatError`**，包括重复语言（本应是 `DuplicateLangError(3)`）。
7. **capitalword 规则丢弃连续大写词特征**：`'USA NASA FBI'` 仅剩 10 个碎片特征；全大写文本检测高度依赖随机性。
8. **`_sort_probability` 用严格 `>` 过滤**（`p > 0.1`），等概率时依赖稳定排序 + 档案目录顺序。

另：`gauss` 扰动的 alpha 无界（可负），但未构造出实际负值复现输入 → 未测。

---

## 9. 失败与未解决项

| 项 | 状态 | 说明 |
|---|---|---|
| 空概率列表 → `'unknown'` | **未测** | 268 golden + 3000 随机短串均未触发；分支存在于 `detector.py:137-139` |
| 负 alpha（`gauss` 极端值） | **未测** | 需系统性搜索 z 值，属统计事件 |
| `FileLoadError(2)` | **未测** | Windows 下 `open()` 对已存在文件难以抛 `IOError`；目录项已被 `isfile` 过滤 |
| `NoTextError(0)` / `CantOpenTrainData(6)` / `TrainDataFormatError(7)` | **不可触发** | 包内无抛出点（`grep` 仅定义处） |
| 跨机器 `os.listdir` 顺序 | **未验证** | 本机恰为字典序；契约不保证，影响等概率并列顺序 |
| `seed=42` 长文本准确率 | **未统计** | 原始数据已在 `expected.json`，可按 `tags` 过滤 |

无上游代码修改、无兼容性绕过、无安装失败。`git -C langdetect status --porcelain` 输出行数 **0**（上游工作树干净）。