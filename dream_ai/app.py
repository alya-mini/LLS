import json
import os
import random
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

try:
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None

try:
    import swisseph as swe
except Exception:  # noqa: BLE001
    swe = None

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dreams.db"

app = Flask(__name__)

SYMBOL_DB = {
    "uçmak": "özgürlük, sınırları aşma arzusu",
    "dusmek": "kontrol kaybı ya da belirsizlik kaygısı",
    "düşmek": "kontrol kaybı ya da belirsizlik kaygısı",
    "su": "duygusal derinlik, bilinçaltı akışı",
    "deniz": "duygusal bilinçaltı, bilinmeyen",
    "okyanus": "sonsuz olasılıklar, güçlü duygu",
    "yangın": "dönüşüm, bastırılmış öfke",
    "ates": "yaşam enerjisi, yıkım ve yaratım",
    "ateş": "yaşam enerjisi, yıkım ve yaratım",
    "ev": "benlik, iç dünya",
    "oda": "mahrem alan, psikolojik katman",
    "kapı": "fırsat veya geçiş eşiği",
    "anahtar": "çözüm, keşif",
    "yol": "yaşam yönü, karar süreci",
    "araba": "kontrol, ilerleme",
    "tren": "kader akışı, toplumsal rota",
    "ucak": "yüksek hedefler, kaçış",
    "uçak": "yüksek hedefler, kaçış",
    "merdiven": "yükseliş veya düşüş",
    "asansor": "hızlı değişim",
    "asansör": "hızlı değişim",
    "dag": "engel ve başarı",
    "dağ": "engel ve başarı",
    "orman": "bilinmeyenle yüzleşme",
    "agac": "köklenme, büyüme",
    "ağaç": "köklenme, büyüme",
    "cicek": "umut, incelik",
    "çiçek": "umut, incelik",
    "yılan": "dönüşüm, korku, şifa",
    "kedi": "sezgi, bağımsızlık",
    "kopek": "sadakat, korunma",
    "köpek": "sadakat, korunma",
    "kus": "özgür ruh, haber",
    "kuş": "özgür ruh, haber",
    "at": "güç, hareket",
    "aslan": "cesaret, ego",
    "kaplan": "içgüdüsel güç",
    "fil": "hafıza, köklü bilgelik",
    "balik": "bereket, bilinçaltı",
    "balık": "bereket, bilinçaltı",
    "kurt": "içgüdü, yalnızlık",
    "ayı": "koruyuculuk, güç",
    "tavsan": "kırılganlık, hız",
    "tavşan": "kırılganlık, hız",
    "bebek": "yeni başlangıç",
    "cocuk": "masumiyet, iyileşme",
    "çocuk": "masumiyet, iyileşme",
    "anne": "şefkat, korunma",
    "baba": "otorite, yapı",
    "ogretmen": "rehberlik",
    "öğretmen": "rehberlik",
    "doktor": "iyileşme ihtiyacı",
    "hastane": "onarma, kırılganlık",
    "okul": "öğrenme döngüsü",
    "sinav": "performans kaygısı",
    "sınav": "performans kaygısı",
    "telefon": "iletişim ihtiyacı",
    "mesaj": "duygusal haber",
    "internet": "bağlantı, bilgi yükü",
    "robot": "duygudan kopma",
    "uzay": "sınırsız potansiyel",
    "yildiz": "rehberlik, umut",
    "yıldız": "rehberlik, umut",
    "ay": "duygu ritmi, sezgi",
    "gunes": "kimlik, canlılık",
    "güneş": "kimlik, canlılık",
    "karanlik": "gölge arketipi",
    "karanlık": "gölge arketipi",
    "isik": "farkındalık",
    "ışık": "farkındalık",
    "ayna": "kendilikle yüzleşme",
    "maske": "sosyal persona",
    "kan": "yaşam gücü, travma izi",
    "dis": "kaygı, kontrol",
    "diş": "kaygı, kontrol",
    "sac": "kimlik, imaj",
    "saç": "kimlik, imaj",
    "hamilelik": "yaratıcılık, üretim",
    "evlilik": "birleşme arketipi",
    "yuzuk": "bağlılık",
    "yüzük": "bağlılık",
    "altin": "özdeğer",
    "altın": "özdeğer",
    "para": "güvenlik, değer",
    "hazine": "gizli yetenek",
    "hirsiz": "sınır ihlali",
    "hırsız": "sınır ihlali",
    "polis": "düzen, vicdan",
    "mahkeme": "iç yargı",
    "hapishane": "sıkışmışlık",
    "savas": "iç çatışma",
    "savaş": "iç çatışma",
    "silah": "savunma, tehdit",
    "patlama": "ani boşalma",
    "deprem": "temel sarsıntı",
    "firtina": "duygusal kaos",
    "fırtına": "duygusal kaos",
    "yagmur": "arınma",
    "yağmur": "arınma",
    "kar": "duygusal soğuma",
    "ruzgar": "değişim",
    "rüzgar": "değişim",
    "gol": "durgun duygu",
    "göl": "durgun duygu",
    "nehir": "zaman akışı",
    "kopru": "geçiş",
    "köprü": "geçiş",
    "adalet": "denge arayışı",
    "tapinak": "manevi arayış",
    "tapınak": "manevi arayış",
    "melek": "korunma",
    "seytan": "gölge dürtü",
    "şeytan": "gölge dürtü",
    "zombi": "tükenmişlik",
    "canavar": "bastırılmış korku",
    "labirent": "karmaşa",
    "saat": "zaman baskısı",
    "gec kalmak": "yetişememe stresi",
    "geç kalmak": "yetişememe stresi",
    "ucurum": "risk",
    "uçurum": "risk",
    "gemi": "yaşam yolculuğu",
    "liman": "güvenli alan",
    "ada": "yalıtılmışlık",
    "kule": "mesafe, savunma",
    "kraliçe": "anima gücü",
    "kral": "otorite merkezi",
    "kahraman": "cesur benlik",
    "gölge": "reddedilmiş benlik",
    "anima": "duygusal iç ses",
    "animus": "eylem iradesi",
    "kayıp": "yas süreci",
    "ölüm": "dönüşüm ve kapanış",
    "yeniden doğuş": "yenilenme",
    "muzik": "ruhsal uyum",
    "müzik": "ruhsal uyum",
    "dans": "ifade özgürlüğü",
    "resim": "yaratıcılık",
    "tiyatro": "persona oyunu",
    "kahve": "uyanış",
    "çay": "dinginlik",
    "ekmek": "temel güvenlik",
    "sofra": "paylaşım",
}

POSITIVE_WORDS = {"mutlu", "huzur", "güzel", "sevgi", "neşe", "başarı", "rahat", "iyi", "umut", "özgür"}
NEGATIVE_WORDS = {"korku", "kaygı", "üzgün", "karanlık", "panik", "kabus", "yalnız", "kayıp", "ölüm", "stres"}

LANGS = {
    "tr": {"app": "Rüya Yorumlayıcı AI", "analyze": "Rüyamı Yorumla"},
    "en": {"app": "Dream Interpreter AI", "analyze": "Analyze Dream"},
    "de": {"app": "Traumdeuter KI", "analyze": "Traum analysieren"},
    "fr": {"app": "Interpréteur de Rêves IA", "analyze": "Analyser"},
    "es": {"app": "Intérprete de Sueños IA", "analyze": "Analizar"},
    "it": {"app": "Interprete dei Sogni AI", "analyze": "Analizza"},
    "pt": {"app": "Interpretador de Sonhos IA", "analyze": "Analisar"},
    "ru": {"app": "ИИ Толкователь Снов", "analyze": "Анализ"},
    "ar": {"app": "مفسر الأحلام بالذكاء الاصطناعي", "analyze": "حلل"},
    "ja": {"app": "夢診断AI", "analyze": "分析"},
    "ko": {"app": "꿈 해석 AI", "analyze": "분석"},
    "zh": {"app": "梦境解析AI", "analyze": "分析"},
}

SIGNS = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
PLANETS = {
    "Güneş": swe.SUN if swe else None,
    "Ay": swe.MOON if swe else None,
    "Merkür": swe.MERCURY if swe else None,
    "Venüs": swe.VENUS if swe else None,
    "Mars": swe.MARS if swe else None,
    "Jüpiter": swe.JUPITER if swe else None,
    "Satürn": swe.SATURN if swe else None,
}


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dreams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            dream_text TEXT NOT NULL,
            symbols TEXT NOT NULL,
            mood_score REAL NOT NULL,
            fate_score INTEGER NOT NULL,
            language TEXT NOT NULL,
            prediction TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def extract_symbols(text: str) -> list[str]:
    lowered = text.lower()
    found = [k for k in SYMBOL_DB if k in lowered]
    return sorted(set(found))[:12]


def sentiment_score(text: str) -> float:
    words = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    if not words:
        return 0.5
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    raw = (pos - neg) / max(1, len(words) / 4)
    return max(0.0, min(1.0, 0.5 + raw))


def archetypes(symbols: list[str], mood: float) -> list[str]:
    arcs = []
    if any(s in symbols for s in ["kahraman", "aslan", "dağ"]):
        arcs.append("Kahraman")
    if any(s in symbols for s in ["gölge", "karanlık", "canavar", "şeytan", "seytan"]):
        arcs.append("Gölge")
    if any(s in symbols for s in ["anne", "kraliçe", "su", "ay"]):
        arcs.append("Anima")
    if mood < 0.4:
        arcs.append("Yaralı Şifacı")
    if not arcs:
        arcs.append("Gezgin")
    return arcs


def sign_from_longitude(lon: float) -> str:
    return SIGNS[int(lon // 30) % 12]


def compute_astro(date_str: str | None = None) -> dict:
    if not date_str:
        dt = datetime.now(timezone.utc)
    else:
        cleaned = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned).astimezone(timezone.utc)
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0) if swe else None
    planets = {}
    if swe and jd:
        for name, code in PLANETS.items():
            lon = swe.calc_ut(jd, code)[0][0]
            planets[name] = {"longitude": round(lon, 3), "sign": sign_from_longitude(lon)}
    else:
        rng = random.Random(int(dt.timestamp()))
        for name in PLANETS:
            lon = rng.random() * 360
            planets[name] = {"longitude": round(lon, 3), "sign": sign_from_longitude(lon)}
    return {"datetime": dt.isoformat(), "planets": planets}


def offline_interpretation(text: str, symbols: list[str], mood: float, lang: str) -> dict:
    arcs = archetypes(symbols, mood)
    symbol_lines = [f"- {s}: {SYMBOL_DB.get(s, 'sembolik mesaj')}" for s in symbols[:6]]
    prediction = random.choice([
        "24 saat içinde beklenmedik bir mesaj alabilirsin.",
        "Yarım kalan bir konu netleşecek.",
        "Enerjini toparlayıp yeni bir adım atacaksın.",
        "İç sesini dinlersen doğru fırsatı göreceksin.",
    ])
    return {
        "summary": f"Rüyan {', '.join(arcs)} arketipleri etrafında dönüyor.",
        "symbol_analysis": "\n".join(symbol_lines) or "Belirgin sembol bulunamadı; rüyan bütünsel bir duygu taşıyor.",
        "jung_archetypes": arcs,
        "mood": round(mood, 3),
        "prediction_24h": prediction,
        "language": lang,
        "raw_text": text,
    }


def call_openai(api_key: str, text: str, symbols: list[str], mood: float, lang: str) -> dict | None:
    if not OpenAI or not api_key:
        return None
    prompt = (
        "Sen bir rüya analisti ve Jung psikolojisi uzmanısın. "
        "Kısa, sıcak ve uygulanabilir bir yorum ver. "
        f"Dil: {lang}. Sembol adayları: {symbols}. Mood:{mood}. "
        "JSON döndür: summary, symbol_analysis, jung_archetypes(list), prediction_24h."
    )
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        parsed = json.loads(response.choices[0].message.content)
        parsed["mood"] = round(mood, 3)
        parsed["language"] = lang
        parsed["raw_text"] = text
        return parsed
    except Exception:
        return None


def fate_score(mood: float, symbols: list[str], astro: dict) -> int:
    moon_sign = astro["planets"].get("Ay", {}).get("sign", "")
    harmony = 6 if moon_sign in {"Balık", "Yengeç", "Terazi"} else 0
    return int(max(35, min(99, 50 + mood * 35 + len(symbols) * 2 + harmony + random.randint(-4, 4))))


init_db()


@app.route("/")
def index():
    return render_template("index.html", languages=LANGS)


@app.route("/api/symbols")
def symbols():
    return jsonify({"count": len(SYMBOL_DB), "symbols": SYMBOL_DB})


@app.route("/api/astro", methods=["POST"])
def astro():
    payload = request.get_json(silent=True) or {}
    return jsonify(compute_astro(payload.get("datetime")))


@app.route("/api/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(force=True)
    text = (payload.get("dream", "") or "").strip()
    if len(text) < 10:
        return jsonify({"error": "Rüya metni en az 10 karakter olmalıdır."}), 400
    lang = payload.get("lang", "tr") if payload.get("lang", "tr") in LANGS else "tr"
    api_key = (payload.get("openai_key", "") or "").strip()
    symbols_found = extract_symbols(text)
    mood = sentiment_score(text)
    astro_data = compute_astro(payload.get("datetime"))

    ai_result = call_openai(api_key, text, symbols_found, mood, lang)
    result = ai_result or offline_interpretation(text, symbols_found, mood, lang)

    score = fate_score(mood, symbols_found, astro_data)
    result["fate_score"] = score
    result["astro"] = astro_data
    result["symbol_count"] = len(symbols_found)
    result["ui_text"] = LANGS[lang]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dreams(created_at, dream_text, symbols, mood_score, fate_score, language, prediction) VALUES(?,?,?,?,?,?,?)",
        (
            datetime.now().isoformat(timespec="seconds"),
            text,
            json.dumps(symbols_found, ensure_ascii=False),
            mood,
            score,
            lang,
            result.get("prediction_24h", ""),
        ),
    )
    conn.commit()
    conn.close()

    return jsonify(result)


@app.route("/api/trends")
def trends():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    since = (datetime.now() - timedelta(days=7)).isoformat(timespec="seconds")
    cur.execute("SELECT symbols FROM dreams WHERE created_at >= ?", (since,))
    rows = cur.fetchall()
    conn.close()
    counter = Counter()
    for (symbols_json,) in rows:
        try:
            counter.update(json.loads(symbols_json))
        except Exception:
            pass
    top = [{"symbol": s, "count": c, "meaning": SYMBOL_DB.get(s, "") } for s, c in counter.most_common(5)]
    return jsonify({"period": "7d", "top_symbols": top, "total_dreams": len(rows)})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
