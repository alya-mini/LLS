import json
import os
import random
import sqlite3
from datetime import date, datetime

from flask import Flask, jsonify, render_template, request

try:
    from openai import OpenAI
except Exception:  # optional dependency runtime safety
    OpenAI = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "timelines.db")

app = Flask(__name__, template_folder="templates", static_folder="static")

PERSONAS = {
    5: {"tone": "masum, oyunbaz, meraklı", "focus": "oyun, aile, güven"},
    15: {"tone": "asi, duygusal, kimlik arayışında", "focus": "arkadaşlar, özgürlük, sınırlar"},
    30: {"tone": "kariyer odaklı, pragmatik", "focus": "iş, ilişki, hedefler"},
    60: {"tone": "bilge, nostaljik, sakin", "focus": "anlam, sağlık, miras"},
}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dialogues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            age INTEGER NOT NULL,
            mood TEXT NOT NULL,
            user_text TEXT NOT NULL,
            ai_text TEXT NOT NULL,
            interesting_score INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS time_capsules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            open_year INTEGER NOT NULL,
            message TEXT NOT NULL,
            author_alias TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_persona(age: int):
    if age in PERSONAS:
        return PERSONAS[age]
    if age < 10:
        return {"tone": "çocuksu, hayalperest", "focus": "eğlence, güven"}
    if age < 20:
        return {"tone": "enerjik, sorgulayıcı", "focus": "kimlik, arkadaşlar"}
    if age < 40:
        return {"tone": "hedef odaklı", "focus": "kariyer, denge"}
    if age < 55:
        return {"tone": "olgun, mentorvari", "focus": "sürdürülebilirlik"}
    return {"tone": "bilge, yavaş ve derin", "focus": "huzur, miras"}


def fallback_reply(age: int, mood: str, message: str):
    persona = get_persona(age)
    seeds = [
        f"{age} yaşındaki ben olarak söylüyorum: {mood} hissetmen çok anlaşılır.",
        f"Şu anki odak alanım {persona['focus']}. Küçük bir adım at: bugün 15 dakikalık mini bir aksiyon seç.",
        f"Mesajındaki ana tema '{message[:80]}' bana bir pivot anını hatırlatıyor.",
    ]
    return " ".join(seeds)


def openai_reply(age: int, mood: str, message: str, birth_date: str, api_key: str | None):
    if not api_key or OpenAI is None:
        return fallback_reply(age, mood, message)

    persona = get_persona(age)
    client = OpenAI(api_key=api_key)
    system_prompt = (
        "Sen kullanıcının farklı bir yaştaki versiyonusun. "
        f"Yaş: {age}, ton: {persona['tone']}, odak: {persona['focus']}. "
        "Kısa, empatik ve Türkçe cevap ver. 4-6 cümle, bir soru ile bitir."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.8,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Doğum tarihi: {birth_date}, mood: {mood}, mesaj: {message}",
            },
        ],
    )
    return completion.choices[0].message.content


def save_dialogue(age: int, mood: str, user_text: str, ai_text: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    score = min(100, len(set(user_text.lower().split())) * 8 + random.randint(5, 30))
    cur.execute(
        "INSERT INTO dialogues(created_at, age, mood, user_text, ai_text, interesting_score) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), age, mood, user_text, ai_text, score),
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(force=True)
    age = int(payload.get("age", 30))
    mood = payload.get("mood", "neutral")
    message = payload.get("message", "")
    birth_date = payload.get("birthDate", "")
    api_key = payload.get("apiKey") or os.getenv("OPENAI_API_KEY")

    try:
        reply = openai_reply(age, mood, message, birth_date, api_key)
    except Exception:
        reply = fallback_reply(age, mood, message)

    save_dialogue(age, mood, message, reply)
    return jsonify({"reply": reply, "persona": get_persona(age)})


@app.route("/api/pivot-analysis", methods=["POST"])
def pivot_analysis():
    payload = request.get_json(force=True)
    mood = payload.get("mood", "neutral")
    age = int(payload.get("age", 30))

    pivots = [
        {"title": "Eğitim Yolu", "impact": random.randint(60, 95), "age": 18},
        {"title": "İlk Büyük Kariyer Kararı", "impact": random.randint(55, 92), "age": 25},
        {"title": "İlişki / Aile Dengesi", "impact": random.randint(50, 90), "age": 33},
    ]
    mood_corr = {"happy": 0.78, "anxious": 0.64, "motivated": 0.81, "sad": 0.52}.get(mood, 0.67)
    return jsonify(
        {
            "age": age,
            "mood": mood,
            "moodCorrelation": mood_corr,
            "pivots": sorted(pivots, key=lambda p: p["impact"], reverse=True),
            "paradoxRisk": round((1 - mood_corr) * random.uniform(0.2, 0.8), 2),
        }
    )


@app.route("/api/alternative-life", methods=["POST"])
def alternative_life():
    scenarios = [
        {"path": "Doktor", "happiness": 82, "wealth": 74, "social": 68},
        {"path": "Sanatçı", "happiness": 67, "wealth": 49, "social": 84},
        {"path": "Girişimci", "happiness": 71, "wealth": 86, "social": 62},
        {"path": "Akademisyen", "happiness": 76, "wealth": 58, "social": 73},
    ]
    return jsonify({"scenarios": scenarios})


@app.route("/api/dialogues/top")
def top_dialogues():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT age, mood, user_text, ai_text, interesting_score FROM dialogues ORDER BY interesting_score DESC, id DESC LIMIT 12"
    )
    rows = cur.fetchall()
    conn.close()

    return jsonify(
        {
            "items": [
                {
                    "age": r[0],
                    "mood": r[1],
                    "userText": r[2],
                    "aiText": r[3],
                    "score": r[4],
                }
                for r in rows
            ]
        }
    )


@app.route("/api/time-capsule", methods=["POST"])
def time_capsule():
    payload = request.get_json(force=True)
    open_year = int(payload.get("openYear", date.today().year + 10))
    message = payload.get("message", "")
    alias = payload.get("alias", "Anonim")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO time_capsules(created_at, open_year, message, author_alias) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), open_year, message, alias),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
