# -*- coding: utf-8 -*-
"""用真实运行的上游 langdetect 生成 golden 数据。

用法（工作目录必须是仓库根）:
    .venv/Scripts/python.exe tools/gen_golden.py

产出:
    docs/port/golden/cases.jsonl      输入（text/seed/tags/id）
    docs/port/golden/expected.json    期望输出（detect / detect_langs 全量，浮点保留 repr）
    docs/port/golden/timing.json      耗时测量结果
    docs/port/golden/summary.json     规模统计（条数/语言数）

约束:
    - 只读 langdetect/，不修改其任何文件。
    - 所有数字为运行时实测。
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import struct
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "port" / "golden"
PKG_PARENT = ROOT / "langdetect"  # 内含真正的 langdetect 包


def import_upstream():
    """导入仓库内的 langdetect 源码包（绕开仓库根同名目录造成的 namespace 遮蔽）。"""
    if str(PKG_PARENT) not in sys.path:
        sys.path.insert(0, str(PKG_PARENT))
    import langdetect  # noqa: PLC0415

    f = str(langdetect.__file__)
    assert f.endswith(os.path.join("langdetect", "__init__.py")), f
    return langdetect


LANG_LONG = {
    "af": "Die woordeboek is 'n versameling van woorde wat in 'n taal gebruik word. Dit bevat gewoonlik die betekenis van elke woord, asook hoe die woord uitgespreek en gespel word. Sonder 'n woordeboek sou dit baie moeilik wees om 'n vreemde taal te leer en te verstaan.",
    "ar": "اللغة العربية هي واحدة من أكثر اللغات انتشارا في العالم، ويتحدث بها ملايين الناس في مختلف الدول. تتميز بحروفها الجميلة وقواعدها الدقيقة، وقد كتب بها العلماء والشعراء أعظم الأعمال عبر التاريخ.",
    "bg": "Българският език е южнославянски език, който се говори от милиони хора в България и съседните страни. Той използва кирилица и има богата литературна традиция, започнала още през средновековието.",
    "bn": "বাংলা ভাষা দক্ষিণ এশিয়ার একটি গুরুত্বপূর্ণ ভাষা। এই ভাষায় অসংখ্য কবিতা, গল্প ও গান রচিত হয়েছে। বিশ্বের বহু মানুষ এই ভাষায় কথা বলেন এবং লেখেন, আর এর সাহিত্য খুবই সমৃদ্ধ।",
    "ca": "El català és una llengua romànica que es parla a Catalunya, el País Valencià i les Illes Balears. Té una llarga tradició literària i cultural, i avui dia la fan servir milions de persones en la vida quotidiana.",
    "cs": "Čeština je západoslovanský jazyk, kterým mluví miliony lidí ve střední Evropě. Je bohatá na tvary slov a má dlouhou literární tradici, od středověkých kronik až po moderní romány a básně.",
    "cy": "Mae'r Gymraeg yn iaith Geltaidd sy'n cael ei siarad yng Nghymru. Mae ganddi hanes hir a llenyddiaeth gyfoethog, ac mae nifer o bobl yn ei dysgu a'i defnyddio bob dydd yn y gwaith a'r cartref.",
    "da": "Dansk er et nordgermansk sprog, som tales af millioner af mennesker i Danmark og andre lande. Sproget har en lang litterær tradition og deler mange træk med de øvrige skandinaviske sprog.",
    "de": "Die deutsche Sprache gehört zu den germanischen Sprachen und wird von vielen Millionen Menschen gesprochen. Sie hat eine reiche Literatur und eine lange Tradition in Wissenschaft, Philosophie und Musik, und ihre Grammatik ist für Lernende oft eine große Herausforderung.",
    "el": "Η ελληνική γλώσσα έχει μακρά ιστορία που ξεκινά από την αρχαιότητα. Αποτελεί τη βάση πολλών επιστημονικών όρων και χρησιμοποιείται σήμερα από εκατομμύρια ανθρώπους στην Ελλάδα και στην Κύπρο.",
    "en": "Language detection is the task of identifying the language in which a given piece of text is written. It is used in search engines, translation services and social media platforms, where huge amounts of text arrive every second in dozens of different languages.",
    "es": "El idioma español es una lengua romance hablada por millones de personas en España y América Latina. Cuenta con una literatura muy rica y es uno de los idiomas más estudiados del mundo por quienes quieren viajar o trabajar en el extranjero.",
    "et": "Eesti keel on läänemeresoome keel, mida räägivad miljonid inimesed Eestis ja välismaal. Keeles on palju käändeid ning pikk kirjanduse ja rahvaluule traditsioon, mis ulatub sajandite taha.",
    "fa": "زبان فارسی یکی از زبان‌های مهم خاورمیانه است و میلیون‌ها نفر در ایران و کشورهای همسایه به آن سخن می‌گویند. این زبان دارای ادبیات بسیار غنی و شاعرانی بزرگ است که آثارشان در جهان شناخته شده است.",
    "fi": "Suomen kieli kuuluu uralilaisiin kieliin ja sitä puhuvat miljoonat ihmiset Suomessa. Kieli on rakenteeltaan omaleimainen ja siinä on pitkä kirjallinen perinne aina kansanrunoudesta nykyaikaiseen romaaniin sekä nykyaikaiseen tieteenkieliseen tekstiin.",
    "fr": "Le français est une langue romane parlée par des millions de personnes en Europe, en Afrique et en Amérique du Nord. Elle possède une longue tradition littéraire et joue un rôle important dans la diplomatie et la culture internationale depuis plusieurs siècles.",
    "gu": "ગુજરાતી ભાષા ભારતના પશ્ચિમ ભાગમાં વસતા લોકોની મુખ્ય ભાષા છે. આ ભાષામાં અનેક પુસ્તકો, કવિતાઓ અને ગીતો લખાયા છે, અને તેની સાહિત્યિક પરંપરા ખૂબ જ જૂની છે.",
    "he": "השפה העברית היא שפה שמית עתיקה שהתחדשה כשפה מדוברת בעת החדשה. היא משמשת מיליוני אנשים בישראל ובעולם, ויש לה מסורת ספרותית עשירה שהחלה לפני אלפי שנים.",
    "hi": "हिन्दी भाषा भारत की सबसे अधिक बोली जाने वाली भाषाओं में से एक है। इसमें अनेक कविताएँ, कहानियाँ और उपन्यास लिखे गए हैं, और यह दुनिया भर में करोड़ों लोगों द्वारा बोली और समझी जाती है।",
    "hr": "Hrvatski je južnoslavenski jezik kojim govori nekoliko milijuna ljudi u Hrvatskoj i susjednim zemljama. Jezik ima bogatu književnost i pisanu tradiciju koja seže od srednjeg vijeka do suvremenih romana.",
    "hu": "A magyar nyelv a finnugor nyelvcsaládba tartozik, és több millió ember beszéli Magyarországon és a szomszédos országokban. Nyelvtanában sok toldalékot használ, irodalma pedig gazdag és sokszínű.",
    "id": "Bahasa Indonesia adalah bahasa resmi negara Indonesia dan digunakan oleh ratusan juta orang di seluruh kepulauan. Bahasa ini terus berkembang dan menjadi alat pemersatu bagi masyarakat yang berbeda suku dan budaya.",
    "it": "L'italiano è una lingua romanza parlata da milioni di persone in Italia e in molte altre parti del mondo. Ha una tradizione letteraria antichissima e fama internazionale nel campo della musica, dell'arte e della cucina.",
    "ja": "日本語は日本で広く使われている言語であり、世界でも多くの人が学習しています。漢字、ひらがな、かたかなの三種類の文字を組み合わせて文章を書き、文学や科学の分野で長い歴史を持っています。",
    "kn": "ಕನ್ನಡ ಭಾಷೆ ಕರ್ನಾಟಕದ ಮುಖ್ಯ ಭಾಷೆಯಾಗಿದ್ದು, ಲಕ್ಷಾಂತರ ಜನ ಇದನ್ನು ಮಾತನಾಡುತ್ತಾರೆ. ಈ ಭಾಷೆಗೆ ದೀರ್ಘ ಸಾಹಿತ್ಯ ಪರಂಪರೆ ಇದೆ ಮತ್ತು ಹಲವು ಪ್ರಸಿದ್ಧ ಕವಿಗಳನ್ನು ನೀಡಿದೆ.",
    "ko": "한국어는 한국과 여러 지역에서 사용되는 언어이며, 독특한 문자 체계인 한글을 사용합니다. 오랜 역사 동안 많은 문학 작품과 기록이 남아 있고, 오늘날에는 인터넷과 방송에서도 널리 쓰이고 있습니다.",
    "lt": "Lietuvių kalba yra baltų kalbų grupės kalba, kuria kalba keli milijonai žmonių Lietuvoje. Ji išlaikė daug archajiškų bruožų ir turi turtingą tautosakos bei literatūros paveldą.",
    "lv": "Latviešu valoda ir baltu valodu grupas valoda, kurā runā miljoniem cilvēku Latvijā. Valodai ir sena rakstu un tautasdziesmu tradīcija, un tā joprojām ir nozīmīga sabiedrības dzīvē.",
    "mk": "Македонскиот јазик е јужнословенски јазик што се зборува во Северна Македонија и во соседните земји. Има богата народна книжевност и современа литература напишана на кирилица.",
    "ml": "മലയാളം ഭാഷ കേരളത്തിലെ പ്രധാന ഭാഷയാണ്. ഈ ഭാഷയിൽ ധാരാളം കവിതകളും കഥകളും നോവലുകളും എഴുതപ്പെട്ടിട്ടുണ്ട്, കൂടാതെ ലോകത്തിന്റെ പല ഭാഗങ്ങളിലും ഇത് സംസാരിക്കുന്നവരുണ്ട്.",
    "mr": "मराठी भाषा महाराष्ट्रातील लोकांची प्रमुख भाषा आहे आणि तिला दीर्घ साहित्यिक परंपरा आहे. या भाषेत अनेक कविता, नाटके आणि कादंबऱ्या लिहिल्या गेल्या आहेत.",
    "ne": "नेपाली भाषा नेपालको राष्ट्रभाषा हो र यसलाई करोडौं मानिसहरूले बोल्छन्। यो भाषा देवनागरी लिपिमा लेखिन्छ र यसको साहित्य परम्परा पुरानो र समृद्ध छ।",
    "nl": "Het Nederlands is een Germaanse taal die door miljoenen mensen in Nederland en België wordt gesproken. De taal heeft een rijke literatuur en wordt ook gebruikt in het onderwijs en de wetenschap over de hele wereld.",
    "no": "Norsk er et nordgermansk språk som snakkes av millioner av mennesker i Norge. Språket finnes i to skriftlige varianter og har en lang tradisjon innen litteratur, teater og forskning.",
    "pa": "ਪੰਜਾਬੀ ਭਾਸ਼ਾ ਪੰਜਾਬ ਦੇ ਲੋਕਾਂ ਦੀ ਮਾਂ ਬੋਲੀ ਹੈ ਅਤੇ ਇਸ ਨੂੰ ਕਰੋੜਾਂ ਲੋਕ ਬੋਲਦੇ ਹਨ। ਇਸ ਭਾਸ਼ਾ ਵਿੱਚ ਬਹੁਤ ਸਾਰੀ ਕਵਿਤਾ, ਗੀਤ ਅਤੇ ਕਹਾਣੀਆਂ ਲਿਖੀਆਂ ਗਈਆਂ ਹਨ।",
    "pl": "Język polski należy do zachodniosłowiańskich języków i jest używany przez miliony ludzi w Polsce oraz poza jej granicami. Ma bogatą literaturę i skomplikowaną gramatykę, znaną z licznych przypadków i wyjątków.",
    "pt": "O português é uma língua românica falada por milhões de pessoas em Portugal, no Brasil e em vários países da África e da Ásia. Tem uma literatura muito rica e é um dos idiomas mais importantes do mundo contemporâneo.",
    "ro": "Limba română este o limbă romanică vorbită de milioane de oameni în România și în Republica Moldova. Are o literatură bogată și numeroase influențe din limbile vecine, păstrând totuși o structură latină puternică.",
    "ru": "Русский язык относится к восточнославянским языкам и является одним из самых распространённых в мире. На нём написаны великие произведения литературы, и он широко используется в науке, технике и международном общении.",
    "sk": "Slovenčina je západoslovanský jazyk, ktorým hovoria milióny ľudí na Slovensku. Má bohatú ľudovú slovesnosť aj modernú literatúru a používa sa v školstve, vede a verejnom živote.",
    "sl": "Slovenščina je južnoslovanski jezik, ki ga govori nekaj milijonov ljudi v Sloveniji in zamejstvu. Jezik ima dvojino in bogato književno tradicijo, ki sega od ljudskih pesmi do sodobne proze.",
    "so": "Af Soomaaligu waa luqad ku hadasha malaayiin qof oo ku nool Geeska Afrika iyo qurbaha. Waxay leedahay suugaan hodan ah oo ay ku jiraan gabayo iyo sheekooyin dhaqameed oo la soo dhaxlay.",
    "sq": "Gjuha shqipe është një gjuhë indo-evropiane që flitet nga miliona njerëz në Shqipëri, Kosovë dhe në diasporë. Ajo ka një traditë të gjatë gojore dhe letrare, me shumë këngë dhe legjenda popullore.",
    "sv": "Svenska är ett nordgermanskt språk som talas av miljontals människor i Sverige och Finland. Språket har en lång litterär tradition och används idag i skola, forskning, medier och förvaltning.",
    "sw": "Kiswahili ni lugha ya Kibantu inayozungumzwa na mamilioni ya watu katika Afrika Mashariki. Lugha hii ina historia ndefu ya biashara na utamaduni, na inatumika katika shule, vyombo vya habari na serikali.",
    "ta": "தமிழ் மொழி உலகின் மிகப் பழமையான மொழிகளில் ஒன்றாகக் கருதப்படுகிறது. இது தமிழ்நாட்டிலும் இலங்கையிலும் பேசப்படுகிறது, மேலும் அதற்கு வளமான இலக்கிய மரபு உள்ளது.",
    "te": "తెలుగు భాష ఆంధ్రప్రదేశ్ మరియు తెలంగాణ ప్రజల ప్రధాన భాష. దీనికి దీర్ఘ సాహిత్య చరిత్ర ఉంది మరియు అనేక కవులు, రచయితలు ఈ భాషలో విలువైన రచనలు చేసారు.",
    "th": "ภาษาไทยเป็นภาษาราชการของประเทศไทยและมีผู้พูดหลายล้านคนทั่วโลก ภาษานี้มีระบบเสียงวรรณยุกต์ที่ซับซ้อน และมีวรรณคดีที่มีชื่อเสียงมายาวนานหลายศตวรรษ",
    "tl": "Ang wikang Tagalog ay isa sa mga pangunahing wika sa Pilipinas at ginagamit ng milyon-milyong tao sa araw-araw na pamumuhay. Marami itong panitikan, awitin at tula na nagpapakita ng mayamang kultura ng bansa.",
    "tr": "Türkçe, Ural-Altay dil ailesine bağlı olduğu düşünülen ve milyonlarca insan tarafından konuşulan bir dildir. Eklemeli yapısı sayesinde uzun kelimeler türetilebilir ve zengin bir edebiyat geleneğine sahiptir.",
    "uk": "Українська мова належить до східнослов'янських мов і нею розмовляють мільйони людей в Україні та за кордоном. Вона має багату літературу, пісенну традицію і власну систему правопису.",
    "ur": "اردو زبان پاکستان کی قومی زبان ہے اور برصغیر کے بہت سے لوگ اسے بولتے اور سمجھتے ہیں۔ اس میں بے شمار شاعری، افسانے اور ناول لکھے گئے ہیں اور اس کا ادب بہت مالدار ہے۔",
    "vi": "Tiếng Việt là ngôn ngữ chính thức của Việt Nam và được hàng triệu người sử dụng. Ngôn ngữ này có thanh điệu phong phú, được viết bằng chữ quốc ngữ và có một nền văn học lâu đời.",
    "zh-cn": "中文是世界上最古老的语言之一，使用人数众多，分布在世界各地。汉语的书写系统使用汉字，经过数千年的发展，形成了丰富的文学作品、诗词和典籍，对周边国家的文化产生了深远的影响。",
    "zh-tw": "繁體中文在台灣、香港與海外華人社區廣泛使用，保留了傳統漢字的寫法。這種文字系統歷史悠久，承載著豐富的典籍、詩詞與文學作品，也是中華文化的重要載體。",
}

LANG_SHORT = {
    "af": "Die son skyn vandag.",
    "ar": "الجو جميل اليوم.",
    "bg": "Днес времето е хубаво.",
    "bn": "আজ আকাশ পরিষ্কার।",
    "ca": "Avui fa molt bon dia.",
    "cs": "Dnes je hezké počasí.",
    "cy": "Mae'r tywydd yn braf heddiw.",
    "da": "Vejret er godt i dag.",
    "de": "Das Wetter ist heute schön.",
    "el": "Ο καιρός είναι ωραίος σήμερα.",
    "en": "The weather is nice today.",
    "es": "Hoy hace muy buen tiempo.",
    "et": "Ilm on täna ilus.",
    "fa": "امروز هوا خوب است.",
    "fi": "Sää on tänään kaunis.",
    "fr": "Il fait très beau aujourd'hui.",
    "gu": "આજે હવામાન સરસ છે.",
    "he": "מזג האוויר נחמד היום.",
    "hi": "आज मौसम बहुत अच्छा है।",
    "hr": "Danas je lijepo vrijeme.",
    "hu": "Ma nagyon szép idő van.",
    "id": "Cuaca hari ini sangat cerah.",
    "it": "Oggi il tempo è bellissimo.",
    "ja": "今日はとても良い天気です。",
    "kn": "ಇಂದು ಹವಾಮಾನ ಚೆನ್ನಾಗಿದೆ.",
    "ko": "오늘 날씨가 정말 좋습니다.",
    "lt": "Šiandien oras labai gražus.",
    "lv": "Šodien laiks ir ļoti jauks.",
    "mk": "Денес времето е многу убаво.",
    "ml": "ഇന്ന് കാലാവസ്ഥ നല്ലതാണ്.",
    "mr": "आज हवामान खूप छान आहे.",
    "ne": "आज मौसम राम्रो छ।",
    "nl": "Het weer is vandaag erg mooi.",
    "no": "Været er fint i dag.",
    "pa": "ਅੱਜ ਮੌਸਮ ਬਹੁਤ ਵਧੀਆ ਹੈ।",
    "pl": "Dzisiaj jest bardzo ładna pogoda.",
    "pt": "O tempo está muito bom hoje.",
    "ro": "Astăzi vremea este foarte frumoasă.",
    "ru": "Сегодня очень хорошая погода.",
    "sk": "Dnes je veľmi pekné počasie.",
    "sl": "Danes je zelo lepo vreme.",
    "so": "Maanta cimiladu aad bay u fiican tahay.",
    "sq": "Sot moti është shumë i mirë.",
    "sv": "Vädret är fint idag.",
    "sw": "Hali ya hewa ni nzuri leo.",
    "ta": "இன்று வானிலை மிகவும் நன்றாக உள்ளது.",
    "te": "ఈ రోజు వాతావరణం బాగుంది.",
    "th": "วันนี้อากาศดีมาก",
    "tl": "Maganda ang panahon ngayon.",
    "tr": "Bugün hava çok güzel.",
    "uk": "Сьогодні дуже гарна погода.",
    "ur": "آج موسم بہت اچھا ہے۔",
    "vi": "Hôm nay thời tiết rất đẹp.",
    "zh-cn": "今天天气非常好。",
    "zh-tw": "今天天氣非常好。",
}

EXTRA_CASES = {
    "mixed-scripts-latin-cjk": "Hello world 你好 世界 hello again こんにちは world",
    "mixed-scripts-cyrillic-latin": "Privet mir hello world привет мир hello",
    "with-url": "Read more at https://example.com/news/2024?id=42&ref=abc about this topic today.",
    "with-mail": "Please write to john.doe@example.org for further details about the report.",
    "with-url-and-mail": "Contact first.last@example.com or visit http://example.com/docs#top for the manual.",
    "url-only": "https://example.com/very/long/path?x=1",
    "whitespace-only-spaces": "     ",
    "whitespace-only-mixed": " \t\r\n  \u00a0  ",
    "emoji-only": "\U0001f600\U0001f60d\U0001f389\U0001f44d\U0001f680",
    "emoji-only-zwj": "\U0001f468\u200d\U0001f469\u200d\U0001f467",
    "digits-only": "1234567890",
    "digits-and-space": "12 34 56 78",
    "punctuation-only": "!!!???...,,,",
    "empty": "",
    "single-latin-char": "a",
    "single-ascii-upper": "AB",
    "url-adjacent-text": "see http://a.com/x then TEXT-more",
    "capitalword-only": "USA NASA FBI",
    "ascii-art-arrow": "a -> b",
    "latin1-accents": "\u00e9\u00e8\u00ea\u00eb \u00e0\u00e2 \u00f4\u00f6",
    "cjk-ideographic-space": "\u3000\u4e00\u3000\u4e8c\u3000",
    "vietnamese-vi-normalization": "Ti\u1ebfng Vi\u1ec7t r\u1ea5t \u0111\u1eb9p v\u00e0 phong ph\u00fa",
    "mixed-long-en-ja": "The weather is nice today. \u4eca\u65e5\u306f\u3068\u3066\u3082\u826f\u3044\u5929\u6c17\u3067\u3059\u3002 The weather is nice today.",
    "dotted-domains-only": "example.com foo.bar.org test.net",
}


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def detect_with(detector, text, seed):
    """对一个文本跑 detect 与 get_probabilities，返回可 JSON 化的结果。"""
    from langdetect.lang_detect_exception import LangDetectException

    rec = {}
    d = detector(seed)
    d.append(text)
    try:
        probs = d.get_probabilities()
    except LangDetectException as exc:
        return {
            "error": {
                "type": type(exc).__name__,
                "code": exc.code,
                "message": str(exc),
            }
        }
    rec["detect"] = probs[0].lang if probs else "unknown"
    rec["detect_langs"] = [
        {
            "lang": p.lang,
            "prob_repr": repr(p.prob),
            "prob": p.prob,
            "prob_bits": struct.pack(">d", p.prob).hex(),
        }
        for p in probs
    ]
    rec["detect_langs_count"] = len(probs)
    return rec


def build_cases():
    cases = []
    for lang in sorted(LANG_LONG):
        cases.append({"id": "long-%s" % lang, "intended_lang": lang, "tags": ["long", "per-language"], "text": LANG_LONG[lang], "seed": 0})
    for lang in sorted(LANG_SHORT):
        cases.append({"id": "short-%s" % lang, "intended_lang": lang, "tags": ["short", "per-language"], "text": LANG_SHORT[lang], "seed": 0})
    for name, text in sorted(EXTRA_CASES.items()):
        cases.append({"id": "extra-%s" % name, "intended_lang": None, "tags": ["extra"], "text": text, "seed": 0})
    # seed=42 变体：覆盖全部语料，用于验证不同 seed 下结果差异
    seeded = []
    for c in cases:
        c42 = dict(c)
        c42["id"] = c["id"] + "@seed42"
        c42["seed"] = 42
        seeded.append(c42)
    cases.extend(seeded)
    for c in cases:
        c["text_len"] = len(c["text"])
        c["text_sha256"] = hashlib.sha256(c["text"].encode("utf-8")).hexdigest()
    return cases


def main() -> int:
    import_upstream()
    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    factory = DetectorFactory()
    factory.load_profile(str(PROFILES_DIRECTORY))
    langlist = factory.get_lang_list()

    def make(text_seed):
        seed = text_seed
        f = DetectorFactory()
        f.langlist = list(factory.langlist)
        f.word_lang_prob_map = factory.word_lang_prob_map
        f.seed = seed
        return f.create()

    def detector(seed):
        d = make(seed)
        return d

    cases = build_cases()
    cases_path = OUT_DIR / "cases.jsonl"
    with cases_path.open("w", encoding="utf-8", newline="\n") as fh:
        for c in cases:
            fh.write(json.dumps({"id": c["id"], "text": c["text"], "seed": c["seed"],
                                 "tags": c["tags"], "intended_lang": c["intended_lang"],
                                 "text_len": c["text_len"], "text_sha256": c["text_sha256"]},
                                ensure_ascii=False, sort_keys=True) + "\n")

    results = []
    for c in cases:
        rec = {"id": c["id"], "seed": c["seed"], "tags": c["tags"],
               "intended_lang": c["intended_lang"], "text_len": c["text_len"],
               "text_sha256": c["text_sha256"], "text": c["text"]}
        rec.update(detect_with(detector, c["text"], c["seed"]))
        results.append(rec)

    # 未设 seed（None）的不确定性证据：同一文本重复 10 次
    unseeded_texts = [
        "Otec matka syn.",
        "Ein, zwei, drei, vier",
        "hi",
        "a b c",
        "The weather is nice today.",
        EXTRA_CASES["mixed-scripts-latin-cjk"],
        LANG_LONG["en"][:60],
    ]
    unseeded = []
    for text in unseeded_texts:
        runs = []
        for _ in range(10):
            d = detector(None)
            d.append(text)
            try:
                probs = d.get_probabilities()
                runs.append({"detect": probs[0].lang if probs else "unknown",
                             "top": [{"lang": p.lang, "prob_repr": repr(p.prob)} for p in probs[:3]]})
            except Exception as exc:  # noqa: BLE001
                runs.append({"error": type(exc).__name__ + ": " + str(exc)})
        distinct = sorted({r.get("detect", "ERR") for r in runs})
        unseeded.append({"text": text, "text_len": len(text), "runs": runs,
                         "distinct_langs": distinct, "distinct_count": len(distinct)})

    # 同 seed 可重复性：seed=0 与 seed=42 各重复 5 次
    repeat_ids = ["long-en", "long-fr", "long-zh-cn", "short-en", "short-ja",
                  "extra-mixed-scripts-latin-cjk", "extra-capitalword-only"]
    by_id = {c["id"]: c for c in cases}
    repeat = []
    for rid in repeat_ids:
        c = by_id[rid]
        for seed in (0, 42):
            outs = []
            for _ in range(5):
                r = detect_with(detector, c["text"], seed)
                outs.append(json.dumps(r, sort_keys=True, ensure_ascii=False))
            repeat.append({"id": rid, "seed": seed, "runs": 5,
                           "all_identical": len(set(outs)) == 1,
                           "sample": json.loads(outs[0])})

    # seed=0 vs seed=42 差异
    diff = []
    for c in cases:
        if c["seed"] != 0:
            continue
        other = by_id.get(c["id"] + "@seed42")
        if other is None:
            continue
        a = next(r for r in results if r["id"] == c["id"])
        b = next(r for r in results if r["id"] == other["id"])
        same_detect = a.get("detect") == b.get("detect")
        same_all = json.dumps(a.get("detect_langs"), sort_keys=True) == json.dumps(
            b.get("detect_langs"), sort_keys=True)
        if not same_all:
            diff.append({"id": c["id"], "seed0_detect": a.get("detect"),
                         "seed42_detect": b.get("detect"), "same_detect": same_detect,
                         "seed0_langs": a.get("detect_langs"),
                         "seed42_langs": b.get("detect_langs")})

    expected = {
        "meta": {
            "generator": "tools/gen_golden.py",
            "upstream_version": "1.0.9",
            "python": sys.version.split()[0],
            "langlist": langlist,
            "langlist_size": len(langlist),
            "seeds_used": [0, 42],
            "unknown_lang": "unknown",
            "note": ("detect_langs 顺序即上游 _sort_probability 的输出顺序；prob_repr 为 float repr 全精度，"
                     "prob_bits 为 IEEE754 double 大端十六进制；error 表示上游抛 LangDetectException。"),
        },
        "cases": results,
        "unseeded_runs": unseeded,
        "repeatability": repeat,
        "seed_diff": diff,
    }
    (OUT_DIR / "expected.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    timing = measure_timing()
    (OUT_DIR / "timing.json").write_text(
        json.dumps(timing, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "case_count": len(cases),
        "case_count_seed0": sum(1 for c in cases if c["seed"] == 0),
        "case_count_seed42": sum(1 for c in cases if c["seed"] == 42),
        "languages_covered": len({c["intended_lang"] for c in cases if c["intended_lang"]}),
        "langlist_size": len(langlist),
        "profile_file_count": len(os.listdir(str(PROFILES_DIRECTORY))),
        "unseeded_text_count": len(unseeded_texts),
        "unseeded_runs_per_text": 10,
        "unseeded_distinct_gt1": [u["text"] for u in unseeded if u["distinct_count"] > 1],
        "repeatability_cases": len(repeat),
        "repeatability_all_identical": all(r["all_identical"] for r in repeat),
        "seed_diff_count": len(diff),
        "seed_diff_same_detect_count": sum(1 for d in diff if d["same_detect"]),
        "error_cases": [r["id"] for r in results if "error" in r],
        "detect_langs_nonempty": sum(1 for r in results if r.get("detect_langs")),
        "detect_accuracy_long_seed0": accuracy(results, "long", 0),
        "detect_accuracy_short_seed0": accuracy(results, "short", 0),
        "timing_median_ms": timing["summary"],
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


def accuracy(results, tag, seed):
    rows = [r for r in results if tag in r["tags"] and r["seed"] == seed and r.get("intended_lang")]
    if not rows:
        return None
    hit = sum(1 for r in rows if r.get("detect") == r["intended_lang"])
    return {"n": len(rows), "hit": hit, "miss": len(rows) - hit,
            "miss_ids": [r["id"] for r in rows if r.get("detect") != r["intended_lang"]]}


def measure_timing():
    """耗时：冷启动（新进程 import + load_profile）与单次检测，各采样后取中位数。

    冷启动用 subprocess 反复跑同一段脚本；单次检测在进程内重复 30 次取中位数。
    """
    cold_cmd = [
        sys.executable, "-c",
        "import sys; sys.path.insert(0, %r);"
        "from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY;"
        "f=DetectorFactory(); f.load_profile(PROFILES_DIRECTORY)" % str(PKG_PARENT),
    ]
    cold = []
    for _ in range(5):
        t0 = time.perf_counter()
        subprocess.run(cold_cmd, check=True, capture_output=True)
        cold.append((time.perf_counter() - t0) * 1000.0)

    from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY

    t0 = time.perf_counter()
    factory = DetectorFactory()
    factory.load_profile(str(PROFILES_DIRECTORY))
    load_ms = (time.perf_counter() - t0) * 1000.0
    factory.seed = 0

    texts = {
        "short_en": "The weather is nice today.",
        "long_en": LANG_LONG["en"],
        "long_zh_cn": LANG_LONG["zh-cn"],
        "long_ja": LANG_LONG["ja"],
    }
    per_text = {}
    for name, text in texts.items():
        samples = []
        for _ in range(30):
            d = factory.create()
            d.append(text)
            t = time.perf_counter()
            d.get_probabilities()
            samples.append((time.perf_counter() - t) * 1000.0)
        per_text[name] = {
            "text_len": len(text),
            "samples": len(samples),
            "median_ms": statistics.median(samples),
            "min_ms": min(samples),
            "max_ms": max(samples),
        }

    summary = {
        "cold_start_import_and_load_profile_ms_median": statistics.median(cold),
        "cold_start_samples_ms": cold,
        "load_profile_inprocess_ms": load_ms,
        "detect_median_ms": {k: v["median_ms"] for k, v in per_text.items()},
    }
    return {
        "method": ("冷启动=新 Python 进程执行 `import langdetect.detector_factory` + "
                   "`DetectorFactory().load_profile(PROFILES_DIRECTORY)`，采样 5 次取中位数；"
                   "单次检测=同一进程内对已加载 factory 新建 Detector，append 后只计时 "
                   "get_probabilities()，每个文本 30 次取中位数；seed 固定 0。"),
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "cold_start": cold,
        "load_profile_ms": load_ms,
        "per_text": per_text,
        "summary": summary,
    }


if __name__ == "__main__":
    raise SystemExit(main())
