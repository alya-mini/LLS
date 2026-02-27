import json
import os
import random
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "nutrition.db"

app = Flask(__name__)

MOODS = {
    "stres": {"focus": "magnesium", "target": "kortizol_azaltma"},
    "mutlu": {"focus": "serotonin", "target": "endorfin"},
    "yorgun": {"focus": "b12", "target": "enerji"},
    "asik": {"focus": "afrodizyak", "target": "dopamin"},
    "odak": {"focus": "omega3", "target": "konsantrasyon"},
    "uykulu": {"focus": "triptofan", "target": "uyku_kalitesi"},
    "kaygili": {"focus": "magnezyum", "target": "sakinlik"},
    "heyecanli": {"focus": "kompleks_karbonhidrat", "target": "denge"},
    "yalniz": {"focus": "prebiyotik", "target": "bagirsak_beyin"},
    "yaratici": {"focus": "antioksidan", "target": "noral_destek"},
    "romantik": {"focus": "afrodizyak", "target": "oksitosin"},
    "motivasyonsuz": {"focus": "demir", "target": "canlilik"},
}

CORE_INGREDIENTS = [
    ("Somon", "deniz", 94, 79, 84, 67, "stres,odak"),
    ("Ispanak", "sebze", 52, 58, 43, 61, "stres,yorgun"),
    ("Muz", "meyve", 37, 76, 58, 45, "mutlu,uykulu"),
    ("Bitter Çikolata", "tatli", 44, 67, 75, 38, "mutlu,yaratici"),
    ("Yumurta", "protein", 31, 42, 82, 59, "yorgun,odak"),
    ("Ceviz", "kuruyemis", 73, 54, 49, 70, "odak,stres"),
    ("Hindi", "protein", 28, 48, 66, 89, "uykulu,odak"),
    ("Çilek", "meyve", 21, 62, 29, 40, "asik,mutlu"),
    ("İstiridye", "deniz", 35, 46, 61, 33, "asik,romantik"),
    ("Kırmızı Et", "protein", 18, 35, 91, 30, "yorgun,motivasyonsuz"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            omega3 INTEGER,
            serotonin INTEGER,
            b12 INTEGER,
            tryptophan INTEGER,
            mood_tags TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            mood TEXT,
            recipe_title TEXT,
            mood_boost REAL,
            notes TEXT
        )
        """
    )

    current_count = cur.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0]
    if current_count < 1000:
        cur.execute("DELETE FROM ingredients")
        rows = list(CORE_INGREDIENTS)
        for idx in range(990):
            base = random.choice(CORE_INGREDIENTS)
            rows.append(
                (
                    f"{base[0]} Variant {idx+1}",
                    base[1],
                    max(5, min(99, base[2] + random.randint(-12, 12))),
                    max(5, min(99, base[3] + random.randint(-12, 12))),
                    max(5, min(99, base[4] + random.randint(-12, 12))),
                    max(5, min(99, base[5] + random.randint(-12, 12))),
                    base[6],
                )
            )

        cur.executemany(
            """
            INSERT INTO ingredients (name, category, omega3, serotonin, b12, tryptophan, mood_tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    conn.commit()
    conn.close()


def mood_boost_formula(metrics):
    serotonin = metrics.get("serotonin", 0)
    cortisol_reduction = metrics.get("cortisol_reduction", 0)
    dopamine = metrics.get("dopamine", 0)
    return round((serotonin * 0.4) + (cortisol_reduction * 0.3) + (dopamine * 0.3), 2)


def recommend_ingredients(mood, limit=10):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT * FROM ingredients
        WHERE mood_tags LIKE ?
        ORDER BY (omega3 + serotonin + b12 + tryptophan) DESC
        LIMIT ?
        """,
        (f"%{mood}%", limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_recipe_with_openai(payload, picked):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    import urllib.request

    ing_names = ", ".join(i["name"] for i in picked[:8])
    prompt = (
        "Kısa ama yaratıcı bir Türkçe tarif üret. "
        f"Mood: {payload['mood']}, Beslenme: {payload['diet']}, Porsiyon: {payload['servings']}, "
        f"Mutfak: {payload['cuisine']}, Kullanılacak malzemeler: {ing_names}. "
        "Yanıtta şu başlıklar olsun: Başlık, Hazırlık, Adımlar, Neden Bu Tarif"
    )

    body = json.dumps({
        "model": "gpt-4.1-mini",
        "input": prompt
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("output", [{}])[0].get("content", [{}])[0].get("text")
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html", moods=list(MOODS.keys()))


@app.route("/api/moods")
def moods():
    return jsonify({"moods": MOODS})


@app.route("/api/generate-recipe", methods=["POST"])
def generate_recipe():
    payload = request.get_json(force=True)
    mood = payload.get("mood", "stres")

    picked = recommend_ingredients(mood)
    metrics = {
        "serotonin": sum(i["serotonin"] for i in picked[:5]) / 5,
        "cortisol_reduction": sum(i["omega3"] for i in picked[:5]) / 5,
        "dopamine": sum(i["b12"] for i in picked[:5]) / 5,
    }
    boost = mood_boost_formula(metrics)

    ai_text = generate_recipe_with_openai(payload, picked)
    if not ai_text:
        ai_text = (
            f"Başlık: {mood.title()} Mood Bowl\n"
            "Hazırlık: 10 dk\n"
            "Adımlar:\n1) Malzemeleri doğrayın.\n2) Zeytinyağı ile soteleyin.\n"
            "3) Baharat ve limon ekleyip servis edin.\n"
            f"Neden Bu Tarif: {mood} hissi için hedef odaklı mikro besin profili sağlar."
        )

    return jsonify(
        {
            "recipe": ai_text,
            "ingredients": picked[:10],
            "analysis": {
                "serotonin": round(metrics["serotonin"], 1),
                "cortisol_reduction": round(metrics["cortisol_reduction"], 1),
                "dopamine": round(metrics["dopamine"], 1),
                "mood_boost": boost,
            },
            "share_text": f"Mood boost %{int(boost)}! {mood} için AI tarifimi denedim 🍽️",
        }
    )


@app.route("/api/journal", methods=["GET", "POST"])
def journal():
    conn = get_conn()
    if request.method == "POST":
        payload = request.get_json(force=True)
        conn.execute(
            "INSERT INTO journal (created_at, mood, recipe_title, mood_boost, notes) VALUES (?, ?, ?, ?, ?)",
            (
                datetime.utcnow().isoformat(),
                payload.get("mood"),
                payload.get("recipe_title"),
                payload.get("mood_boost"),
                payload.get("notes", ""),
            ),
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True})

    rows = conn.execute("SELECT * FROM journal ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify({"entries": [dict(r) for r in rows]})


init_db()

if __name__ == "__main__":
    app.run(debug=True)
