# langdetect 上游行为契约（可移植行为取证）

- 上游：`langdetect` 1.0.9（`F:/moonbit比赛/moon_langdetect/langdetect/`，只读）
- 运行环境：Python 3.12.10（MSC v.1943 64bit），six 1.17.0
- 所有 `file:line` 均指 `langdetect/langdetect/` 下的上游文件
- 所有「实测」数字来自 `tools/probe_facts.py` 与 `tools/gen_golden.py` 的真实运行，重跑命令写在每条后面

> 阅读约定：**「契约」= 移植后必须逐位复现的行为**；**「quirk」= 非直觉但属契约的行为**，集中列在 §10。
> 概率数值只有在随机数序列与浮点运算顺序完全一致时才能逐位复现；见 §4.4 与 §8。

---

## 1. 公开 API 面

### 1.1 `__init__.py` 实际导出

`__init__.py:1-2`：

```python
from .detector_factory import DetectorFactory, PROFILES_DIRECTORY, detect, detect_langs
from .lang_detect_exception import LangDetectException
```

| 名字 | 来源 | 说明 |
|---|---|---|
| `DetectorFactory` | `detector_factory.py:15` | 工厂类 |
| `PROFILES_DIRECTORY` | `detector_factory.py:117` | 内置档案目录绝对路径 |
| `detect(text)` | `detector_factory.py:126-130` | 返回单一语言代码 |
| `detect_langs(text)` | `detector_factory.py:133-137` | 返回 `Language` 列表 |
| `LangDetectException` | `lang_detect_exception.py:16` | 唯一异常类型 |

注意 `ErrorCode`、`Detector`、`Language`、`NGram` **不在** `__init__.py` 导出；但 `import langdetect` 后 `langdetect.detector`、`langdetect.detector_factory`、`langdetect.language`、`langdetect.utils`、`langdetect.lang_detect_exception` 作为子模块属性可见（包导入的副作用）。

实测（命令：`.venv/Scripts/python.exe -c "import langdetect; print([n for n in dir(langdetect) if not n.startswith('_')])"`，从仓库根之外的目录运行）：

```
['DetectorFactory', 'LangDetectException', 'PROFILES_DIRECTORY', 'detect', 'detect_langs',
 'detector', 'detector_factory', 'lang_detect_exception', 'language', 'utils']
```

### 1.2 `detect` / `detect_langs` 的惰性单例初始化

`detector_factory.py:118-137`：

```python
_factory = None                      # 118

def init_factory():                  # 120
    global _factory
    if _factory is None:             # 122
        _factory = DetectorFactory()
        _factory.load_profile(PROFILES_DIRECTORY)

def detect(text):                    # 126
    init_factory()
    detector = _factory.create()
    detector.append(text)
    return detector.detect()

def detect_langs(text):              # 133
    init_factory()
    detector = _factory.create()
    detector.append(text)
    return detector.get_probabilities()
```

契约要点：

1. **首次调用**触发 `load_profile(PROFILES_DIRECTORY)`：读 55 个 JSON、构建 87,598 键的 `word_lang_prob_map`。实测进程内耗时中位数 **210.00 ms**（`tools/gen_golden.py` → `timing.json`）。
2. 模块级 `_factory` 是**进程级全局**；之后所有 `detect`/`detect_langs` 复用同一 factory，**不再重复加载**。
3. `DetectorFactory.seed` 是**类属性**（`detector_factory.py:29`，默认 `None`）。`detect`/`detect_langs` 走的是 `_factory.create()`，而 `Detector.__init__` 读 `factory.seed`（`detector.py:59`）；`_factory` 是 `DetectorFactory` 实例，读类属性 `DetectorFactory.seed`。因此官方推荐的 `DetectorFactory.seed = 0` 在**首次调用之后**设置依然生效（每个新 Detector 重新读取）。
   实测：`DetectorFactory.seed = 0; detect(...)` 与 `detect(...)` 在设置前调用均可复现。
4. **每次调用都新建 Detector**，`self.text` 与 `self.langprob` 不跨调用共享。
5. `PROFILES_DIRECTORY` 为 `os.path.join(os.path.dirname(__file__), 'profiles')`（`detector_factory.py:117`），实测：
   `F:\moonbit比赛\moon_langdetect\langdetect\langdetect\profiles`。

### 1.3 `DetectorFactory` 公开方法语义

| 方法 | 行 | 语义与契约细节 |
|---|---|---|
| `__init__()` | 31-33 | `word_lang_prob_map = {}`，`langlist = []`。**不**读档案。 |
| `load_profile(dir)` | 35-64 | 见 §1.3.1 |
| `load_json_profile(list[str])` | 66-78 | 每个元素是 JSON 字符串；`len < 2` 抛 `NeedLoadProfileError(4)`；任何解析/结构异常重包成 `FormatError(1)`。 |
| `add_profile(profile, index, langsize)` | 80-92 | 见 §1.3.2 |
| `clear()` | 94-96 | 清空 `langlist` 与 `word_lang_prob_map`；**不重置** `seed`。 |
| `create(alpha=None)` | 98-103 | 先 `_create_detector()`；`alpha is not None` 时 `set_alpha(alpha)`。`alpha=0.0` 也会生效（判的是 `is not None`）。 |
| `_create_detector()` | 105-108 | `langlist` 为空 → `NeedLoadProfileError(4)`「Need to load profiles.」 |
| `set_seed(seed)` | 110-111 | `self.seed = seed`（**实例属性**，遮蔽类属性；`detect()` 全局单例不走这条路）。 |
| `get_lang_list()` | 113-114 | 返回 `list(self.langlist)` 的**浅拷贝**；顺序 = 档案加载顺序。 |

#### 1.3.1 `load_profile` 细节

- `os.listdir(profile_directory)`（36）：目录不存在 → **`FileNotFoundError` 直接外抛**，不包成 `LangDetectException`（实测 `Z:/no_such_dir_xyz` → `FileNotFoundError [WinError 3]`）。目录存在但空 → `NeedLoadProfileError(4)`「Not found profile: <dir>」。
- `langsize = len(list_files)`（40）：**含点文件与子目录**。点文件（`filename.startswith('.')`，42）与非常规文件（45）会 `continue`，但已被计入 `langsize`。
  实测：临时目录放 `.hidden` + 子目录 + 2 个档案 → `langlist == ['aa','bb']`，而概率向量长度 = **4**。
- 文件名以 `.` 开头被跳过（42）；非文件被跳过（45）；**不排序**（`os.listdir` 顺序）。实测本机 `os.listdir(profiles)` 恰好等于 `sorted(...)`，但契约不保证；`langlist` 顺序决定并列概率时的输出顺序（§7）。
- 打开方式：Py3 用 `encoding='utf-8'`（50-53）。
- 异常映射（58-61）：`IOError` → `FileLoadError(2)`「Cannot open "<path>"」；**其余任何异常** → `FormatError(1)`「Profile format error in "<path>"」。因此档案里的重复语言（`DuplicateLangError`）也会被重包成 `FormatError`（实测）。`IndexError`（`n_words` 过短）、`ZeroDivisionError`（`n_words[i] == 0`）同样重包成 `FormatError`。

#### 1.3.2 `add_profile` 细节（freq → prob）

```python
lang = profile.name                       # 81
if lang in self.langlist:                 # 82
    raise LangDetectException(DuplicateLangError, ...)   # 83
self.langlist.append(lang)                # 84
for word in profile.freq:                 # 86
    if word not in self.word_lang_prob_map:
        self.word_lang_prob_map[word] = [0.0] * langsize  # 88
    length = len(word)                    # 89
    if 1 <= length <= 3:                  # 90
        prob = 1.0 * profile.freq.get(word) / profile.n_words[length - 1]  # 91
        self.word_lang_prob_map[word][index] = prob                       # 92
```

**精确公式（契约）**：

```
prob(word, lang) = freq_lang[word] / n_words_lang[len(word) - 1]
```

- 无 log、无比值、无归一化常量；纯频率除法（`1.0 *` 只是浮点提升）。
- 分母是**该语言档案自己**的 `n_words` 计数（1/2/3-gram 各自的**总出现次数**，不是去重后的词表大小）。
- 未出现的语言在该词向量里保持 `0.0`。
- `len(word) > 3` 的键仍会**建出零向量**（87-88），但不写值（90 的条件）；`len == 0` 同理。实测 `{'abcd':5,'a':3}` → 键 `'abcd'` 存在且为 `[0.0]`，`'a'` 为 `[0.3]`。
- `n_words[len-1] == 0` → `ZeroDivisionError`（在 `load_profile` 内被重包为 `FormatError`；直接调 `add_profile` 则裸抛）。
- 实测公式核对：`tools/probe_facts.py prob_formula` → `entries_checked=184129, mismatches=0, max_abs_err=0.0`。
- 55 个档案合计 `word_lang_prob_map` **87,598** 个键（去重后），键长分布 1-gram 3,159 / 2-gram 26,427 / 3-gram 58,012（实测）。

### 1.4 `Language` 的比较 / 排序 / Show

`language.py:1-17` 全文 17 行：

| 成员 | 行 | 契约 |
|---|---|---|
| `__init__(lang, prob)` | 7-9 | 两个公开字段 `lang`（str/None）、`prob`（float） |
| `__repr__` | 11-14 | `lang is None` → `''`；否则 `'%s:%s' % (lang, prob)`，即 `str(prob)`（Python 最短往返表示，等价 `repr`）。`str(Language('en', 1.0)) == 'en:1.0'`（上游测试 `tests/test_language.py:13` 断言） |
| `__lt__` | 16-17 | 仅按 `prob` 比较，**不比较 lang**；等概率时两者互不小于 |
| `__eq__` / `__gt__` | — | **未定义**；`==` 退化为对象身份（上游测试断言 `lang1 == lang2` 为 False） |

排序：`detector.py:234-237`

```python
result = [Language(lang, p) for (lang, p) in zip(self.langlist, prob) if p > self.PROB_THRESHOLD]
result.sort(reverse=True)
```

- 过滤条件 `p > 0.1` **严格大于**（`0.1` 本身被丢弃）。
- `list.sort` 是**稳定**排序；`reverse=True` 在 CPython 中通过「先反转再稳定排序再反转」实现，**等概率元素保持 `langlist` 原序**。
  实测：`Language('a',0.5), Language('b',0.5), Language('c',0.9)` 输入顺序 `[c,b,a]` → 排序后 `['c','b','a']`（`tools/probe_facts.py language_sort`）。
- 因此并列概率时的输出顺序 = **档案目录 `os.listdir` 顺序**，是契约的一部分（虽然该顺序本身不保证跨机器稳定；本机实测等于字典序）。

---

## 2. 全部常量与默认值

`detector.py:44-54`、`detector.py:64-68`、`detector_factory.py:29`：

| 名称 | 值 | 行 | 运行时实测 |
|---|---|---|---|
| `Detector.ALPHA_DEFAULT` | `0.5` | 44 | ✔ |
| `Detector.ALPHA_WIDTH` | `0.05` | 45 | ✔ |
| `Detector.ITERATION_LIMIT` | `1000` | 47 | ✔ |
| `Detector.PROB_THRESHOLD` | `0.1` | 48 | ✔ |
| `Detector.CONV_THRESHOLD` | `0.99999` | 49 | ✔ |
| `Detector.BASE_FREQ` | `10000` | 50 | ✔ |
| `Detector.UNKNOWN_LANG` | `'unknown'` | 51 | ✔ |
| `Detector.URL_RE` | `https?://[-_.?&~;+=/#0-9A-Za-z]{1,2076}` | 53 | ✔ |
| `Detector.MAIL_RE` | `[-_.0-9A-Za-z]{1,64}@[-_0-9A-Za-z]{1,255}[-_.0-9A-Za-z]{1,255}` | 54 | ✔ |
| `detector.alpha`（实例） | `ALPHA_DEFAULT` = 0.5 | 64 | ✔ |
| `detector.n_trial`（实例） | `7` | 65 | ✔ |
| `detector.max_text_length`（实例） | `10000` | 66 | ✔ |
| `detector.prior_map`（实例） | `None` | 67 | ✔ |
| `detector.verbose`（实例） | `False` | 68 | ✔ |
| `detector.seed`（实例） | `factory.seed`（默认 `None`） | 59 | ✔ |
| `DetectorFactory.seed`（类属性） | `None` | factory:29 | ✔ |
| `NGram.N_GRAM` | `3` | ngram.py:25 | ✔ |
| `NGram.LATIN1_EXCLUDED` | `'\xa0\xab\xb0\xbb'`（U+00A0, U+00AB, U+00B0, U+00BB） | ngram.py:24 | ✔ |
| `LangProfile.MINIMUM_FREQ` | `2` | lang_profile.py:11 | 仅训练期使用，运行时无影响 |
| `LangProfile.LESS_FREQ_RATIO` | `100000` | lang_profile.py:12 | 同上 |

重跑：`.venv/Scripts/python.exe tools/probe_facts.py constants`

---

## 3. `Detector.append()` 与 `cleaning_text()`

### 3.1 `append()` 清洗顺序（`detector.py:99-112`）

```python
text = self.URL_RE.sub(' ', text)        # 104
text = self.MAIL_RE.sub(' ', text)       # 105
text = NGram.normalize_vi(text)          # 106
pre = 0                                  # 107
for i in xrange(min(len(text), self.max_text_length)):   # 108
    ch = text[i]
    if ch != ' ' or pre != ' ':
        self.text += ch
    pre = ch                             # 112
```

**顺序是契约**：URL → 邮箱 → 越南语组合符规范化 → 截断并折叠连续空格 → 追加到 `self.text`。

1. **URL 剥离**：`URL_RE` 无 `re.IGNORECASE`、无 `re.UNICODE`，只匹配小写 `http`/`https`；字符类 `[-_.?&~;+=/#0-9A-Za-z]` 长度 `1..2076`。替换为单个空格。
   - **贪婪吞词后果**：字符类 `[-_.?&~;+=/#0-9A-Za-z]` 含 `.`、`-`、`/`、`?`、`&`、`=`、`;`、`+`、`~`、`#`、`_`、数字与 ASCII 字母，因此**只要 URL 后面紧跟 ASCII 字母/数字/这些标点，就会继续吞**，直到遇到空格或字符类之外的字符（中文、逗号、括号、换行等）。实测：
     - `see http://a.com/x then TEXT-more` → `see then TEXT-more`（`http://a.com/x` 被吞；`TEXT-more` 前的空格终止了匹配，故 `TEXT-more` 保留）
     - `http://a.com/x-then` → `' '`（`-` 在字符类内，`then` 被继续吞光）
     - `http://a.com/x.then` → `' '`（`.` 在字符类内，整段消失）
     - `go http://a.com/x;TEXT` → `'go '`（`;` 在字符类内）
     - `go http://a.com/x,TEXT` → `'go ,TEXT'`（`,` **不在**字符类内 → 在此截断，`,TEXT` 保留）
     - `hello https://example.com/abc` → `'hello '`（尾部 URL 整段消失）
     - `a https://example.com/中` → `'a 中'`（遇到非 ASCII 停）

2. **邮箱剥离**：`MAIL_RE` 同理，`{1,64}@{1,255}{1,255}`；实测 `mail me at john.doe@example.com please` → `mail me at please`。
3. **越南语规范化**：`NGram.normalize_vi`（`ngram.py:100-108`）把 `[AEIOUYaeiouyÂÊÔâêôĂăƠơƯư]` + `[U+0300,U+0301,U+0303,U+0309,U+0323]` 组合替换为预组合字符（`messages.properties:129-135`）。
   实测 `'Ti\u1ebfng Vi\u1ec7t'` 保持不变（已是预组合形式）。
4. **截断时机**：`min(len(text), max_text_length)` **在 URL/邮箱/VI 清洗之后**、逐字符拷贝之前计算。因此 `max_text_length` 计的是**清洗后**的码点数（Python `str` 长度 = 码点），且截断发生在**折叠连续空格之前**（循环里跳过字符，但 `i` 仍按原串推进，被跳过的空格不占输出）。
   实测：`set_max_text_length(5); append('abcdefghij')` → `'abcde'`；`set_max_text_length(3); append('aaabbb')` → `'aaa'`。
5. **连续空格折叠**：只折叠 **U+0020**；`\t`、`\n` 原样保留（实测 `'a  b\t\tc'` → `'a b\t\tc'`）。
6. `append` 可多次调用，`self.text` **累加**，且每次调用独立截断（每段最多 `max_text_length` 码点）。
7. `pre = 0`（107）初值是整数 `0`，与首字符比较时 `0 != ' '` 恒真，等价于「首字符即使是空格也保留」。

### 3.2 `cleaning_text()`（`detector.py:114-130`）

```python
latin_count, non_latin_count = 0, 0
for ch in self.text:
    if 'A' <= ch <= 'z':                       # 120
        latin_count += 1
    elif ch >= '\u0300' and unicode_block(ch) != 'Latin Extended Additional':  # 122
        non_latin_count += 1
if latin_count * 2 < non_latin_count:          # 125
    text_without_latin = ''
    for ch in self.text:
        if ch < 'A' or 'z' < ch:               # 128
            text_without_latin += ch
    self.text = text_without_latin
```

契约：

1. **latin 判定** `'A' <= ch <= 'z'`：这是**码点区间**，不是「拉丁字母」。它把 `[ \ ] ^ _ \``（U+005B..U+0060）也算作 latin。
   实测：`[c for c in "[\\]^_`" if 'A' <= c <= 'z']` → `['[', '\\', ']', '^', '_', '`']`。
2. **non-latin 判定**：`ch >= U+0300` 且 `unicode_block(ch) != 'Latin Extended Additional'`。
   - `unicode_block` 返回 **int**（`unicode_block.py:1-220` 的常量），与字符串 `'Latin Extended Additional'` 比较**恒为 False** → 该豁免条件**永不生效**（quirk §10-1）。实测：`unicode_block('\u1ea1') == 66`，`== 'Latin Extended Additional'` → `False`。
   - 因此 U+1E00–U+1EFF（越南语/拉丁扩展附加）全部计入 non-latin。
3. **触发条件** `latin_count * 2 < non_latin_count`（严格小于）。
4. **剥离规则**：保留 `ch < 'A' or 'z' < ch` 的字符——即删除 `'A' <= ch <= 'z'` 的**全部**字符（包括 `[ \ ] ^ _ \``），其余（含数字、空格、标点、非拉丁文字）保留。
   实测：`'日本語のテキストです。これはテストです。 hello'` → `'日本語のテキストです。これはテストです。 '`（末尾 `hello` 被删，latin=5 non=28）。
   实测：`'aaaaa ' + 'ạ'*20` → `' ạ'*20`（latin=5 non=20，5*2<20 成立，5 个 `a` 被删）。
5. `cleaning_text` 由 `_detect_block` 在**每次首次检测时**调用（`detector.py:147`），会**就地修改** `self.text`；重复调用是幂等的（第二次时拉丁字母已被删）。

重跑：`.venv/Scripts/python.exe tools/probe_facts.py append_cleanup`

---

## 4. `_detect_block()` 完整控制流（`detector.py:146-171`）

```python
def _detect_block(self):
    self.cleaning_text()                                    # 147
    ngrams = self._extract_ngrams()                         # 148
    if not ngrams:                                          # 149
        raise LangDetectException(CantDetectError, 'No features in text.')   # 150
    self.langprob = [0.0] * len(self.langlist)              # 152
    self.random.seed(self.seed)                             # 154
    for t in xrange(self.n_trial):                          # 155
        prob = self._init_probability()                     # 156
        alpha = self.alpha + self.random.gauss(0.0, 1.0) * self.ALPHA_WIDTH   # 157
        i = 0
        while True:
            self._update_lang_prob(prob, self.random.choice(ngrams), alpha)   # 161
            if i % 5 == 0:                                  # 162
                if self._normalize_prob(prob) > self.CONV_THRESHOLD or i >= self.ITERATION_LIMIT:  # 163
                    break
                if self.verbose: ...
            i += 1                                          # 167
        for j in xrange(len(self.langprob)):
            self.langprob[j] += prob[j] / self.n_trial      # 169
```

### 4.1 阶段

1. `cleaning_text()`（就地改 `self.text`）。
2. `_extract_ngrams()`（§5）；空列表 → `CantDetectError(5)`「No features in text.」。
3. `langprob` 清零（长度 = `len(langlist)`）。
4. **随机种子**：`self.random.seed(self.seed)` —— 在 **7 轮循环之外**，只播一次。
   - `seed=None` 时 `random.Random.seed(None)` 使用系统熵，**不可复现**。
   - `seed=0` / `seed=42` 时同一文本、同一 Python 版本 → 逐位可复现（实测 §8）。
5. **7 轮试验**（`n_trial = 7`），每轮：
   - `prob = _init_probability()`：无 prior 时 `[1/55]*55`（`detector.py:180`）；有 prior 时复制 `prior_map`（177-178）。
   - `alpha = self.alpha + gauss(0,1) * 0.05`（157）：**每轮独立扰动**；`gauss` 无界，alpha 可正可负。
6. **内层迭代**（`while True`）：
   - 每步 `random.choice(ngrams)` 取一个特征（**有放回**均匀抽样；重复出现次数越多被抽中概率越高）。
   - `_update_lang_prob`（201-213）：`weight = alpha / 10000`；`prob[i] *= weight + lang_prob_map[i]`。
     - 若该特征在所有语言里概率为 0，则 `prob[i] *= weight`（等价于整体乘 `alpha/10000`，可能为负 → 概率变负，归一化后仍可继续）。
   - **归一化时机**：`i % 5 == 0` 时（即 i=0,5,10,…）才归一化并检查收敛。`i` 从 0 起，所以**第 1 步之后立刻归一化并可能收敛**。
   - **收敛判据**：归一化后的最大概率 `> 0.99999` → 跳出。**严格大于**。
   - **迭代上限**：`i >= 1000` 时跳出（在 `i % 5 == 0` 的分支里判，因此实际最多执行到 i=1000 那次更新之后；`i` 是**已执行步数-1**，循环体最多执行 1001 次）。
   - 顺序细节：先 `_normalize_prob` 再判 `i >= ITERATION_LIMIT`，两者用 `or` 短路——收敛时不再评估 `i` 条件。
7. **轮间累加**：`langprob[j] += prob[j] / 7`，即 7 轮归一化后概率的**算术平均**（169）。`prob` 在跳出时已归一化（最后一次 `i%5==0` 归一化），所以 7 轮各分量和均为 1。
8. 最终 `get_probabilities()` → `_sort_probability(langprob)`（§1.4）。

### 4.2 与 `max_text_length` 的关系

`max_text_length` 只在 `append` 生效（§3.1），`_detect_block` 不再截断。特征数上界约 `3 * len(self.text)`（每字符最多 3 个 n-gram），实测长文本（约 230 字符）单次检测中位数 1.69 ms。

### 4.3 空概率 / 无输出

- `_sort_probability` 只保留 `p > 0.1` 的语言。理论上可能返回空列表（此时 `detect()` 返回 `'unknown'`，`detector.py:137-139`）。
- **实测未复现**：268 条 golden 案例中 250 条成功，`detect_langs` 为空的 0 条；另用 3000 条随机短串（`seed=0`）也未复现空列表。**结论：该分支存在但触发条件未测到**（见 §9 未测项）。
- `unknown` 字符串的返回路径只有 `detect()` 在概率列表为空时（`detector.py:139`）；`detect_langs` 本身**不会**返回 `'unknown'`。

### 4.4 浮点可复现性

- 每步都是 `prob[i] = prob[i] * (alpha/10000 + p)` 与 `prob[i] /= sum`，**运算顺序固定**（按 `langlist` 下标升序）。
- `sum(prob)` 用 Python 内建 `sum`（左到右顺序累加）。
- 因此只要随机数序列、特征列表、浮点运算顺序一致，**逐位可复现**。golden 中同时记录 `prob_repr`（`repr`）与 `prob_bits`（IEEE754 大端 hex）用于逐位比对。

---

## 5. `_extract_ngrams()` 取样规则（`detector.py:182-199`）

```python
RANGE = list(xrange(1, NGram.N_GRAM + 1))     # [1,2,3]
result = []
ngram = NGram()
for ch in self.text:
    ngram.add_char(ch)                         # 189
    if ngram.capitalword:                      # 190
        continue
    for n in RANGE:
        if len(ngram.grams) < n:               # 194
            break
        w = ngram.grams[-n:]                   # 196
        if w and w != ' ' and w in self.word_lang_prob_map:   # 197
            result.append(w)
return result
```

### 5.1 `NGram.add_char`（`ngram.py:31-48`）

```python
ch = self.normalize(ch)              # 33
last_char = self.grams[-1]           # 34
if last_char == ' ':
    self.grams = ' '                 # 36
    self.capitalword = False         # 37
    if ch == ' ': return             # 38-39
elif len(self.grams) >= self.N_GRAM:
    self.grams = self.grams[1:]      # 41
self.grams += ch                     # 42
if ch.isupper():                     # 44
    if last_char.isupper(): self.capitalword = True   # 46
else:
    self.capitalword = False         # 48
```

契约：

- `grams` 初始为 `' '`（27-28），因此**首字符**走 `last_char == ' '` 分支：`grams` 重置为 `' '` 再追加字符。
- 归一化后为空格且上一字符是空格 → **直接返回**，不改变 `grams`（连续空格不产生新状态）。
- `capitalword` 规则：**连续两个大写字母**（`ch.isupper()` 且 `last_char.isupper()`）置 `True`；遇到非大写字符置 `False`。
  - `isupper()` 是 Unicode 语义（`Ä`.isupper() 为 True），不只是 ASCII。
  - **首字符不可能是大写触发**（`last_char` 是 `' '`）。
- 一旦 `capitalword=True`，`_extract_ngrams` 在**该字符之后** `continue`，跳过该位置的所有 n-gram；直到出现非大写字符才恢复。
  - 效果：`USA` → `U` 保留，`US` 不保留（第二字符时 capitalword 变 True），`SA`/`SA ` 等来自后续位置。
  - 实测 `'USA NASA FBI'` → 10 个特征：`['U',' U','A ','SA ','N',' N','A ','SA ','F',' F']`。
  - 实测 `'ABC def GH'` → 16 个特征，`'ABC'` 段只留下 `'A'`、`' A'`、`'C '`、`'BC '`。
- **字典命中过滤**：只有 `w in word_lang_prob_map` 的 n-gram 才进入 `result`；不在 87,598 键集合里的碎片被丢弃。
- **空格排除**：`w != ' '`；注意 2/3-gram 可能包含空格（如 `' a'`、`'a '`），这些**是合法特征**（档案里确实有以空格开头的键）。
- `len(ngram.grams) < n` 时 `break`：文本开头不足 n 个字符时不产生 n-gram。
- `result` **保留重复**：同一 n-gram 在文本中出现 k 次就出现 k 次，直接影响 `random.choice` 的抽样权重。

---

## 6. `NGram.normalize` 全表（`ngram.py:64-97`）

`block = unicode_block(ch)` 后按块分支；`unicode_block` 返回 **int 常量**（`unicode_block.py:1-220`），`None` 表示不在任何块内。

| 块（常量） | 区间 | 规则 | 行 |
|---|---|---|---|
| `UNICODE_BASIC_LATIN` = 1 | U+0000–U+007F | 若 `ch < 'A'` 或 `'Z' < ch < 'a'` 或 `'z' < ch` → 替换为空格。即**只保留 A-Z / a-z**；数字、标点、控制符全部变空格。 | 67-69 |
| `UNICODE_LATIN_1_SUPPLEMENT` = 2 | U+0080–U+00FF | 若 `ch` 出现在 `LATIN1_EXCLUDED` 中 → 空格。`LATIN1_EXCLUDED` 原文 `messages.properties:2`：`NGram.LATIN1_EXCLUDE=\u00A0\u00AB\u00B0\u00BB`，即 **U+00A0、U+00AB、U+00B0、U+00BB**（实测 4 个字符）。其余（é、ñ、ÿ 等）原样保留。 | 70-72 |
| `UNICODE_LATIN_EXTENDED_B` = 4 | U+0180–U+024F | 罗马尼亚映射：U+0219 → U+015F；U+021B → U+0163。其余原样。 | 73-78 |
| `UNICODE_GENERAL_PUNCTUATION` = 68 | U+2000–U+206F | **整块**变空格（含 U+2013 en dash、U+2018/2019 引号等）。 | 79-80 |
| `UNICODE_ARABIC` = 13 | U+0600–U+06FF | U+06CC（Farsi yeh）→ U+064A（Arabic yeh）；其余原样。 | 81-83 |
| `UNICODE_LATIN_EXTENDED_ADDITIONAL` = 66 | U+1E00–U+1EFF | 若 `ch >= U+1EA0` → **U+1EC3**（单个代表字符）；U+1E00–U+1E9F 原样。 | 84-86 |
| `UNICODE_HIRAGANA` = 104 | U+3040–U+309F | **全部** → U+3042（あ）。 | 87-88 |
| `UNICODE_KATAKANA` = 105 | U+30A0–U+30FF | **全部** → U+30A2（ア）。 | 89-90 |
| `UNICODE_BOPOMOFO` = 106 | U+3100–U+312F | **全部** → U+3105（ㄅ）。 | 91-92 |
| `UNICODE_BOPOMOFO_EXTENDED` = 109 | U+31A0–U+31BF | **全部** → U+3105（ㄅ）。 | 91-92 |
| `UNICODE_CJK_UNIFIED_IDEOGRAPHS` = 116 | U+4E00–U+9FFF | `CJK_MAP.get(ch, ch)`：命中则映射到该组代表字，否则原样。 | 93-94 |
| `UNICODE_HANGUL_SYLLABLES` = 140 | U+AC00–U+D7AF | **全部** → U+AC00（가）。 | 95-96 |
| 其他块 / `None` | — | **原样返回**（不归一化、不置空格）。例如 U+0080（Latin-1 Supplement 以外的控制区… 实测 U+0080 属于 Latin-1 Supplement，但不在 EXCLUDED 里，故原样）、U+3000（CJK 标点，属 U+3000–U+303F，不在 GENERAL_PUNCTUATION）、U+0300（组合符）、U+20000（CJK Ext-B）全部**原样保留**。 | 97 |

**实测对照表**（`tools/probe_facts.py ngram_normalize`，`repr` 为 Python 输出）：

| 输入 | 输出 | 说明 |
|---|---|---|
| U+0020 | `' '` | BASIC_LATIN → 空格 |
| U+0030 / U+0039 | `' '` | 数字 → 空格 |
| U+002D / U+0023 / U+0040 / U+005F | `' '` | 标点 → 空格 |
| U+0041 / U+007A | `'A'` / `'z'` | 保留 |
| U+0080 | `'\x80'` | Latin-1 但不在 EXCLUDED → 原样 |
| U+00A0 / U+00AB / U+00B0 / U+00BB | `' '` | EXCLUDED |
| U+00E9 / U+00FF / U+00F1 | `'é'` / `'ÿ'` / `'ñ'` | 原样 |
| U+0219 / U+021B | `'ş'` (U+015F) / `'ţ'` (U+0163) | 罗马尼亚映射 |
| U+0250 | `'ɐ'` | Latin Ext-B 但非 0219/021B → 原样 |
| U+0300 | `'̀'` | 组合符块 → 原样 |
| U+060C / U+0627 / U+064A | 原样 | Arabic 非 06CC |
| U+06CC | `'ي'` (U+064A) | Farsi yeh 映射 |
| U+1EA0 / U+1EA1 / U+1EFF / U+1ECC | `'ể'` (U+1EC3) | `>= 1EA0` |
| U+1E00 / U+1E9F | 原样 | `< 1EA0` |
| U+2000–U+206F（如 U+2013） | `' '` | 整块 |
| U+3000 | `'\u3000'` | **不在** GENERAL_PUNCTUATION → 原样 |
| U+3042 / U+304B | `'あ'` | 平假名 |
| U+30A2 / U+30AB | `'ア'` | 片假名 |
| U+3105 / U+31A0 | `'ㄅ'` | 注音 |
| U+4E00 / U+5009 | `'一'` / `'倉'` | CJK，映射到自身组代表 |
| U+9F62 | `'亀'` (U+4E80) | CJK，映射到组代表 |
| U+AC00 / U+D7A3 | `'가'` | 谚文 |
| U+20000 | `'𠀀'` | CJK Ext-B **不在**映射表 → 原样 |

### 6.1 `CJK_MAP` 构造方式与规模

`ngram.py:122-258`：

- `CJK_CLASS` 是 **126 个字符串**的列表，每个元素来自 `messages.properties:3-128` 的 `NGram.KANJI_*` 键（共 126 个 KANJI 键，实测 `grep -c "^NGram.KANJI_"` = 126）。
- 构造（`ngram.py:253-258`）：对每个组，`representative = cjk_list[0]`，组内**每个字符**（含代表字自己）映射到代表字。
- `NGram._init_cjk_map()` 在**模块导入时**执行（`ngram.py:260`）。
- 实测：`CJK_MAP` 大小 **6,667**；组数 126；不同代表字 126；自映射 126 个（每组代表字映射到自己）；**没有任何字符出现在两个组里**（重复计数 0）。
- 未覆盖的 CJK 字符（如 Ext-B U+20000）→ `CJK_MAP.get(ch, ch)` 返回原字符。

### 6.2 `normalize_vi`

`ngram.py:100-120`：正则 `([TO_NORMALIZE_VI_CHARS])([DMARK_CLASS])`，`re.UNICODE`。
- `TO_NORMALIZE_VI_CHARS`（`messages.properties:129`）：`AEIOUYaeiouyÂÊÔâêôĂăƠơƯư`（24 个字符）。
- `DMARK_CLASS`（130）：U+0300, U+0301, U+0303, U+0309, U+0323（5 个）。
- 替换表 `NORMALIZED_VI_CHARS`（110-115）按 dmark 选行、按 `TO_NORMALIZE_VI_CHARS.find(...)` 取列。
- **只处理「字母 + 组合符」序列**，已预组合的字符不变；每次 `append` 都会跑一遍。

---

## 7. `unicode_block.py` 分块判定

### 7.1 表结构

- `_unicode_blocks`（223-444）：**220 个三元组** `(name:int, start:int, end:int)`。
- `NUM_BLOCKS = len(_unicode_blocks)`（446）→ 实测 **220**。
- 按 `start` **升序**排列，**无重叠**（实测 overlaps=0），**有 36 处空洞**（未覆盖码点，如 2144–2207、918000–983039）。
- 覆盖到 U+10FFFF（`UNICODE_SUPPLEMENTARY_PRIVATE_USE_AREA_B, 0x100000, 0x10FFFF`，443）。

### 7.2 边界语义

`unicode_block`（449-465）：

```python
cp = ord(ch)
if cp <= 0x7F: return UNICODE_BASIC_LATIN     # 452-454 特判
be, en = 0, NUM_BLOCKS - 1
while be <= en:
    mid = (be+en) >> 1
    name, start, end = _unicode_blocks[mid]
    if start <= cp <= end: return name        # 460  闭区间
    if cp < start: en = mid-1
    else: be = mid+1
# 落到函数末尾 → 隐式返回 None
```

契约：

- **端点闭区间**：`start <= cp <= end`（460）。实测 `chr(0x7F)` → 1（BASIC_LATIN）、`chr(0x80)` → 2（LATIN_1_SUPPLEMENT），相邻块端点相接不重叠。
- `cp <= 0x7F` 有**特判短路**（453），不参与二分；因 BASIC_LATIN 是第 0 项，结果与二分一致，但少一次循环。
- 未覆盖码点（空洞）→ **返回 `None`**（函数无显式 return）。实测 36 个空洞区间。
- `ord(ch)` 要求**单个码点**；传长度 2 的字符串 → `TypeError`（实测）。
- 实现是**手写二分**，不依赖 `bisect`；`mid = (be+en) >> 1`。

重跑：`.venv/Scripts/python.exe tools/probe_facts.py unicode_blocks`

---

## 8. `utils/lang_profile.py`

### 8.1 档案 JSON 字段结构

实测（`tools/probe_facts.py profile_fields`）：

- 55 个文件，**键集合恒为 `{freq, n_words, name}`**（唯一一种键组合）。
- `n_words` 长度恒为 **3**，值均为 int（非 int 值 0 个）。
- `freq` 键长度分布：1-gram **7,791** / 2-gram **52,387** / 3-gram **123,951**，合计 **184,129** 条；无负频次；无非 BMP 键（外部核验事实）。
- 例（`profiles/af`）：`name="af"`，`n_words=[1541130, 1808182, 1328687]`，`len(freq)=2143`，`min(freq.values())=155`。

### 8.2 `LangProfile` 类（`lang_profile.py:10-70`）

| 成员 | 行 | 语义 |
|---|---|---|
| `__init__(name=None, freq=None, n_words=None)` | 17-26 | `freq` 包装为 `defaultdict(int)`；`n_words` 缺省 `[0]*3`；`name` 缺省 `None` |
| `add(gram)` | 28-36 | `name is None` 或 `gram is None` → 忽略；长度不在 1..3 → 忽略；否则 `n_words[len-1] += 1`、`freq[gram] += 1` |
| `omit_less_freq()` | 38-57 | **训练期**剪枝；见 §8.3 |
| `update(text)` | 59-70 | 训练期：`normalize_vi` 后逐字符 `add_char`，对 n=1..3 调 `add(get(n))` |

**运行时**（`detect`/`detect_langs`）只用 `freq`、`n_words`、`name` 三个字段，**不调用** `add`/`omit_less_freq`/`update`。`omit_less_freq` 在包内**无任何调用点**（`grep -rn` 只命中定义处 `lang_profile.py:38` 与测试）。

### 8.3 `omit_less_freq` 的精确规则（训练期契约）

```python
threshold = max(self.n_words[0] // 100000, 2)      # 42
roman = 0
for key, count in list(self.freq.items()):         # 45
    if count <= threshold:                         # 46
        self.n_words[len(key)-1] -= count; del self.freq[key]
    elif self.ROMAN_CHAR_RE.match(key):            # 49  ^[A-Za-z]$
        roman += count
if roman < self.n_words[0] // 3:                   # 53
    for key, count in list(self.freq.items()):
        if self.ROMAN_SUBSTR_RE.match(key):        # 55  .*[A-Za-z].*
            self.n_words[len(key)-1] -= count; del self.freq[key]
```

- `threshold = max(n_words[0] // 100000, 2)`：**按 1-gram 总次数**的十万分之一与 2 取大。
- `count <= threshold` 才删（**含等于**）。
- `roman` 只累计**单字符 A-Za-z** 的频次（`^[A-Za-z]$`）。
- 若 `roman < n_words[0] // 3`（严格小于），删除**所有含 A-Za-z 子串**的键。
- 注意 `n_words[0]` 在遍历中被修改（删 1-gram 时），`roman < n_words[0]//3` 用的是**修改后**的值。

### 8.4 freq → prob（运行时，权威）

见 §1.3.2。再次强调：

```
word_lang_prob_map[word][lang_index] = freq_lang[word] / n_words_lang[len(word) - 1]
```

- **无 log**、**无平滑**、**无全局归一化**；平滑发生在检测期：`prob[i] *= alpha/10000 + p`（`detector.py:210-212`）。
- 实测 184,129 条全部吻合，`max_abs_err = 0.0`。

### 8.5 排序与截断

- 档案加载顺序 = `os.listdir` 顺序 → `langlist` 顺序（§1.3.1）。
- 词表 `word_lang_prob_map` 无排序（dict 插入序，Python 3.7+ 保序，但只影响遍历，不影响检测）。
- 输出截断只有 `_sort_probability` 的 `p > 0.1` 过滤 + 降序排序（§1.4），**没有 top-N 截断**。实测单次最多返回 **3** 个语言（268 案例中）。

---

## 9. 错误码表与消息

`lang_detect_exception.py:1-13`：

| 名称 | 码 | 触发条件（实测） | 消息原文 | 行 |
|---|---|---|---|---|
| `NoTextError` | 0 | **包内无任何抛出点**（`grep` 仅定义处） | — | 2 |
| `FormatError` | 1 | 档案 JSON 解析失败；`LangProfile(**data)` 结构不符；`n_words` 越界/除零；`load_profile` 内的重复语言；`load_json_profile` 任意异常 | `Profile format error in "<path>"` / `Profile format error.` | 3 / factory:61 / factory:78 |
| `FileLoadError` | 2 | `open()` 抛 `IOError`（`load_profile` 内） | `Cannot open "<path>"` | 4 / factory:59 |
| `DuplicateLangError` | 3 | 直接调 `add_profile` 且 `lang` 已在 `langlist` | `Duplicate the same language profile.` | 5 / factory:83 |
| `NeedLoadProfileError` | 4 | 目录存在但空；`create()` 前未加载；`load_json_profile` 少于 2 个 | `Not found profile: <dir>` / `Need to load profiles.` / `Need more than 2 profiles.` | 6 / factory:38,107,69 |
| `CantDetectError` | 5 | 清洗后无可提取特征 | `No features in text.` | 7 / detector:150 |
| `CantOpenTrainData` | 6 | **包内无抛出点**（训练工具遗留） | — | 8 |
| `TrainDataFormatError` | 7 | **包内无抛出点** | — | 9 |
| `InitParamError` | 8 | `set_prior_map` 出现负值 / 总和 ≤ 0 | `Prior probability must be non-negative.` / `More one of prior probability must be non-zero.` | 10 / detector:85,89 |

`LangDetectException`（16-22）：`code` 属性 + `get_code()`；`str(exc)` 是消息文本。

**实测异常清单**（`docs/port/golden/expected.json` 中 `error` 字段，18 条 = 9 类输入 × 2 seed）：

| 输入 | 结果 |
|---|---|
| `""` | `CantDetectError(5)` `No features in text.` |
| `"     "` | 同上 |
| `" \t\r\n  \u00a0  "` | 同上 |
| `"😀😍🎉👍🚀"` | 同上 |
| `"👨‍👩‍👧"` | 同上 |
| `"1234567890"` | 同上 |
| `"12 34 56 78"` | 同上 |
| `"!!!???...,,,"` | 同上 |
| `"https://example.com/very/long/path?x=1"` | 同上（URL 被剥离后为空） |

> 注意：**纯空白 / 纯 emoji / 纯数字 / 纯标点 / 纯 URL 全部抛异常，而不是返回 `'unknown'`**。

`messages.properties` 加载（`messages.py:7-12`）：逐行 `strip()` 后 `partition('=')`；值经 `.encode().decode('unicode_escape')` 还原转义。缺键返回 `'!<key>!'`（15）。实测 `get_string('NO.SUCH.KEY')` → `'!NO.SUCH.KEY!'`。
注意 `.strip()` 会吃掉行尾空白；`NGram.LATIN1_EXCLUDE` 行尾的 `\u00A0` 是转义文本，不受影响。

---

## 10. 上游 quirk 清单

每条给出 `file:line` + 最小复现输入 + 实测输出。

1. **`cleaning_text` 的 Latin Extended Additional 豁免是死代码**
   `detector.py:122`：`unicode_block(ch) != 'Latin Extended Additional'` —— `unicode_block` 返回 int，比较恒真。
   复现：`unicode_block('\u1ea1')` → `66`；`66 != 'Latin Extended Additional'` → `True`。
   后果：越南语 U+1E00–U+1EFF 全部计入 non-latin，可能触发拉丁剥离。
   复现：`'aaaaa ' + 'ạ'*20` → cleaning 后 `' ạ'*20`（5 个 `a` 被删）。

2. **URL 字符类贪吃：URL 尾部的 `.` `-` `/` `;` 等会把后续文本一起吞掉**
   `detector.py:53,104`。
   复现：`append('see http://a.com/x then TEXT-more')` → `self.text == 'see then TEXT-more'`（空格终止匹配，`TEXT-more` 幸存）。
   复现：`append('http://a.com/x-then')` → `self.text == ' '`（`-` 在字符类内，`then` 被吞光）。
   复现：`append('go http://a.com/x,TEXT')` → `self.text == 'go ,TEXT'`（`,` 不在字符类内 → 截断）。
   复现：`append('a http://x.com/y http://z.com/w')` → `self.text == 'a '`（两个 URL 都被吞）。

3. **空/纯符号输入抛异常而非返回 `unknown`**
   `detector.py:149-150`。
   复现：`detect('')` → `LangDetectException(code=5, 'No features in text.')`；`detect('😀')`、`detect('123')`、`detect('   ')` 同。
   `unknown` 只在概率列表为空时由 `detect()` 返回（139），而该分支**未测到**。

4. **`langprob` 缓存不随 `append` 失效**
   `detector.py:62,141-144`。
   复现：`d.append('Ein, zwei, drei, vier'); d.detect()` → `'de'`；再 `d.append(' the weather is nice today and the sun is shining brightly'); d.detect()` → **仍是 `'de'`**（`langprob` 非 None，直接复用）。

5. **`langsize` 用 `os.listdir` 长度，含点文件/子目录**
   `detector_factory.py:40`。
   复现：临时目录放 `.hidden` + 子目录 + 2 个档案 → `langlist=['aa','bb']` 但概率向量长度 **4**。

6. **`load_profile` 把重复语言重包成 `FormatError`**
   `detector_factory.py:60-61` 捕获所有 `Exception`。
   复现：目录内两个档案都 `name="same"` → `LangDetectException(code=1, 'Profile format error in "...\\x2"')`，而非 `DuplicateLangError(3)`。

7. **capitalword 丢弃连续大写词的特征**
   `detector.py:190-191` + `ngram.py:44-48`。
   复现：`_extract_ngrams('USA NASA FBI')` → 仅 10 个特征 `['U',' U','A ','SA ','N',' N','A ','SA ','F',' F']`；`'AB'` → 2 个特征 `['A',' A']`。
   后果：全大写文本（标题、缩写）可用特征极少，检测更依赖随机性。

8. **`gauss` 扰动的 alpha 无界，可为负**
   `detector.py:157`。`alpha = 0.5 + N(0,1)*0.05`；`|z|>10` 即 alpha<0（概率极低但存在）。负 alpha 使 `prob[i] *= (负权重 + p)`，若 `p` 小则概率变负，归一化后仍能收敛。未构造出实际负 alpha 的复现输入 → **未测**（需固定 seed 搜 z 值，属统计事件）。

9. **`_sort_probability` 用严格 `>` 过滤，等概率顺序依赖档案目录顺序**
   `detector.py:235-236`。
   复现：`[Language('a',0.5), Language('b',0.5), Language('c',0.9)]` 排序后 `['c','b','a']`（保持输入顺序）。
   本机 `os.listdir(profiles)` 恰为字典序，但契约不保证。

10. **`random.choice` 有放回抽样，特征重复次数即权重**
    `detector.py:161`。同一 n-gram 出现 k 次 → 被抽中概率 k/N。文本长度直接改变收敛速度与结果。

11. **`detect()` 首次调用副作用：210 ms 加载 + 进程级全局状态**
    `detector_factory.py:118-124`。之后 `DetectorFactory.seed = 0` 仍可影响新 Detector（类属性），但**已创建的 Detector** 不受影响。

12. **`str(Language)` 用 `%s` 而非 `%.Nf`**
    `language.py:14`。`repr(Language('en', 1.0))` → `'en:1.0'`；`repr(Language(None,0))` → `''`。

---

## 11. 可复现性边界（移植必读）

| 条件 | 结果 |
|---|---|
| 同 seed（0/42）+ 同文本 + 同 Python 版本 | **逐位可复现**。实测 14 组 × 5 次全部一致（`expected.json.repeatability`） |
| 不同 seed（0 vs 42） | 概率几乎必不同：134 组中 125 组 `detect_langs` 不同；其中 122 组首位语言不变 |
| 未设 seed（`None`） | 同一文本重复 10 次：7 条样本中仅 `'Otec matka syn.'` 出现 2 种结果（`fi`/`pl`），其余稳定 |

> 移植时若要复现上游数值，必须复现 **Python `random.Random` 的 Mersenne Twister + `gauss`（Box-Muller）+ `choice`（`_randbelow`）** 的精确算法与调用顺序。`expected.json` 提供 `prob_repr` 与 `prob_bits` 双份基准。

---

## 12. 未测项

- **空概率列表 → `'unknown'`**：`detector.py:137-139` 的分支存在，但 268 条 golden + 3000 条随机短串均未触发。原因：55 个语言 × 7 轮平均后最大概率几乎总 > 0.1。**未测**。
- **负 alpha**：需构造 `gauss` 极端值，未做系统性搜索。**未测**。
- **`IOError` → `FileLoadError(2)`**：Windows 上难以让 `open()` 对已存在文件抛 `IOError`（目录项已被 `isfile` 过滤）。**未测**。
- **`NoTextError(0)` / `CantOpenTrainData(6)` / `TrainDataFormatError(7)`**：包内无抛出点，**不可触发**。
- **`unicode_block` 空洞内的字符**：返回 `None`，`NGram.normalize` 走「其他」分支原样保留；未逐一枚举 36 个空洞。
