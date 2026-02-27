from __future__ import annotations

import hashlib
import random
import sqlite3
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "scents.db"

app = Flask(__name__)

TOP_NOTES = [
    "Bergamot", "Lemon", "Mint", "Mandarin", "Pink Pepper", "Cardamom", "Grapefruit", "Aldehydes"
]
MIDDLE_NOTES = [
    "Lavender", "Rose", "Jasmine", "Iris", "Peony", "Violet", "Clary Sage", "Geranium"
]
BASE_NOTES = [
    "Sandalwood", "Oud", "Vanilla", "Amber", "Musk", "Vetiver", "Cedarwood", "Patchouli", "Tonka"
]

MOOD_RULES = {
    "cozy": ["Sandalwood", "Amber", "Vanilla", "Tonka"],
    "professional": ["Vetiver", "Cedarwood", "Bergamot", "Lavender"],
    "romantic": ["Rose", "Jasmine", "Musk", "Oud"],
    "energetic": ["Grapefruit", "Mint", "Lemon", "Pink Pepper"],
}

PALETTE_RULES = {
    "warm": ["Sandalwood", "Amber", "Vanilla", "Cardamom"],
    "cool": ["Aquatic", "Ozone", "Mint", "Iris"],
    "neutral": ["Musk", "Cedarwood", "Lavender", "Bergamot"],
}

OBJECT_RULES = {
    "wood": ["Sandalwood", "Cedarwood", "Patchouli"],
    "metal": ["Ozone", "Aquatic", "Aldehydes"],
    "fabric": ["Musk", "Rose", "Peony"],
    "plant": ["Vetiver", "Mint", "Geranium"],
}



def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            top_note TEXT NOT NULL,
            middle_note TEXT NOT NULL,
            base_note TEXT NOT NULL,
            profile TEXT NOT NULL,
            mood TEXT NOT NULL,
            score REAL NOT NULL
        )
        """
    )
    cur.execute("SELECT COUNT(*) AS c FROM scents")
    count = cur.fetchone()["c"]
    if count >= 500:
        conn.close()
        return

    brands = ["Creed", "Tom Ford", "Maison Sens", "Nose Lab", "Byredo", "Le Labo", "Diptyque"]
    profiles = ["warm", "cool", "neutral"]
    moods = list(MOOD_RULES.keys())

    entries: List[tuple] = []
    for i in range(520):
        top = random.choice(TOP_NOTES)
        middle = random.choice(MIDDLE_NOTES)
        base = random.choice(BASE_NOTES)
        brand = random.choice(brands)
        profile = random.choice(profiles)
        mood = random.choice(moods)
        score = round(random.uniform(68.0, 99.4), 2)
        name = f"{base} {top} Reserve {i+1:03d}"
        entries.append((name, brand, top, middle, base, profile, mood, score))

    cur.executemany(
        """
        INSERT INTO scents (name, brand, top_note, middle_note, base_note, profile, mood, score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        entries,
    )
    conn.commit()
    conn.close()



def infer_profile(colors: List[str]) -> str:
    if not colors:
        return "neutral"

    warm_hits = sum(1 for c in colors if c.startswith(("#f", "#e", "#d", "#c")))
    cool_hits = sum(1 for c in colors if c.startswith(("#0", "#1", "#2", "#3", "#4", "#5", "#6")))
    if warm_hits > cool_hits:
        return "warm"
    if cool_hits > warm_hits:
        return "cool"
    return "neutral"



def build_signature_hash(parts: List[str]) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()

init_db()


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/recommend")
def recommend():
    data = request.get_json(silent=True) or {}
    palette = data.get("palette", [])
    objects = data.get("objects", [])
    mood = data.get("mood", "cozy")
    sliders: Dict[str, int] = data.get("sliders", {})

    profile = infer_profile(palette)
    weighted_notes = []
    weighted_notes.extend(PALETTE_RULES.get(profile, []))
    weighted_notes.extend(MOOD_RULES.get(mood, MOOD_RULES["cozy"]))
    for obj in objects:
        weighted_notes.extend(OBJECT_RULES.get(obj, []))

    sweetness = sliders.get("sweet", 50)
    woody = sliders.get("woody", 50)
    floral = sliders.get("floral", 50)
    marine = sliders.get("marine", 50)

    if woody > 65:
        weighted_notes.extend(["Oud", "Sandalwood", "Cedarwood"])
    if sweetness > 65:
        weighted_notes.extend(["Vanilla", "Tonka", "Amber"])
    if floral > 60:
        weighted_notes.extend(["Rose", "Jasmine", "Peony"])
    if marine > 60:
        weighted_notes.extend(["Aquatic", "Ozone", "Mint"])

    conn = get_db()
    placeholders = ",".join("?" for _ in weighted_notes) or "?"
    values = weighted_notes or ["Sandalwood"]

    query = f"""
        SELECT * FROM scents
        WHERE top_note IN ({placeholders})
        OR middle_note IN ({placeholders})
        OR base_note IN ({placeholders})
        ORDER BY score DESC
        LIMIT 3
    """
    rows = conn.execute(query, values * 3).fetchall()

    if not rows:
        rows = conn.execute("SELECT * FROM scents ORDER BY score DESC LIMIT 3").fetchall()

    conn.close()

    best = rows[0]
    accord_score = round((best["score"] * 0.4) + (85 * 0.3) + (80 * 0.3), 1)
    cocktail = {
        "oud": max(5, min(72, int(woody * 0.8))),
        "vanilla": max(4, min(35, int(sweetness * 0.35))),
        "floral": max(3, min(28, int(floral * 0.3))),
        "marine": max(2, min(22, int(marine * 0.25))),
    }

    signature = f"{best['base_note']} Signature"
    response = {
        "profile": profile,
        "mood": mood,
        "palette": palette,
        "objects": objects,
        "accord_score": accord_score,
        "signature": signature,
        "signature_hash": build_signature_hash([signature, mood, profile]),
        "cocktail": cocktail,
        "recommendations": [dict(r) for r in rows],
        "molecule": {
            "formula": random.choice(["C6H12O6", "C10H14O", "C12H22O11", "C11H12O2"]),
            "style": random.choice(["hex-ring", "double-helix", "spiro", "orbital"]),
        },
    }
    return jsonify(response)


@app.get("/api/trends")
def trends():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT base_note, COUNT(*) AS n, AVG(score) AS avg_score
        FROM scents
        GROUP BY base_note
        ORDER BY avg_score DESC
        LIMIT 5
        """
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
