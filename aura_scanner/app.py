from __future__ import annotations

import json
import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "auras.db"

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["JSON_SORT_KEYS"] = False


@dataclass(frozen=True)
class AuraProfile:
    key: str
    name: str
    hex: str
    chakra: str
    element: str
    personality: str
    crystal: str


AURA_PALETTE: list[AuraProfile] = [
    AuraProfile("blue", "Mavi", "#45B2FF", "Boğaz", "Su", "İletişimci, empatik, nazik lider.", "Akuamarin"),
    AuraProfile("red", "Kırmızı", "#FF4D5A", "Kök", "Ateş", "Kararlı, cesur, güç odaklı.", "Kırmızı Jasper"),
    AuraProfile("green", "Yeşil", "#37E6A1", "Kalp", "Toprak", "Şifacı, dengeleyici, doğa sever.", "Aventurin"),
    AuraProfile("violet", "Mor", "#A874FF", "Taç", "Eter", "Vizyoner, spiritüel, sezgisel.", "Ametist"),
    AuraProfile("gold", "Altın", "#F9D55B", "Solar", "Ateş", "Özgüvenli, yaratıcı, görünür.", "Sitrin"),
    AuraProfile("turquoise", "Turkuaz", "#40E8E0", "Boğaz", "Su", "Anlatıcı, akışta, ilham verici.", "Turkuaz"),
    AuraProfile("indigo", "İndigo", "#5261FF", "Üçüncü Göz", "Eter", "Derin düşünen, sezgisel analist.", "Lapis Lazuli"),
    AuraProfile("orange", "Turuncu", "#FF9A44", "Sakral", "Ateş", "Neşeli, üretken, sosyal.", "Karnelyan"),
    AuraProfile("pink", "Pembe", "#FF7AC6", "Kalp", "Su", "Romantik, sıcak, kapsayıcı.", "Gül Kuvars"),
    AuraProfile("silver", "Gümüş", "#C7D0E7", "Taç", "Hava", "Gözlemci, zihin berrak, rafine.", "Ay Taşı"),
    AuraProfile("teal", "Teal", "#22B7A8", "Kalp", "Toprak", "Sakinleştirici, güven inşa eden.", "Yeşim"),
    AuraProfile("magenta", "Magenta", "#E045B5", "Sakral", "Ateş", "Tutkulu, artistik, dönüştürücü.", "Rodonit"),
]

ZODIAC_HINTS = {
    "koç": "Ateşin yükseliyor; liderlik fırsatları açık.",
    "boğa": "Toprak enerjin sabit; finansal sezgin güçlü.",
    "ikizler": "İletişimde yıldızlı bir hafta seni bekliyor.",
    "yengeç": "Kalp çakrası çalışmasıyla duygusal netlik geliyor.",
    "aslan": "Sahne senin; görünürlükten çekinme.",
    "başak": "Rutinlerini sadeleştir, enerji kaçaklarını kapat.",
    "terazi": "İlişkilerde denge kurman güçlü sonuçlar verecek.",
    "akrep": "Derin sezgilerin doğru sinyal veriyor.",
    "yay": "Keşif ve eğitim konularında şanslısın.",
    "oğlak": "Uzun vadeli planlar için ideal hafta.",
    "kova": "İnovatif fikirlerin destek buluyor.",
    "balık": "Meditasyon ve rüya çalışmaları etkili.",
}


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    aura_key TEXT NOT NULL,
    aura_name TEXT NOT NULL,
    aura_hex TEXT NOT NULL,
    confidence REAL NOT NULL,
    warm_score REAL NOT NULL,
    cool_score REAL NOT NULL,
    eye_hue REAL NOT NULL,
    light_reflection REAL NOT NULL,
    personality TEXT NOT NULL,
    chakra_json TEXT NOT NULL,
    prediction_json TEXT NOT NULL,
    source TEXT DEFAULT 'webcam'
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    note TEXT NOT NULL,
    mood INTEGER NOT NULL,
    aura_key TEXT,
    tags TEXT
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)


def normalize(v: float, min_v: float, max_v: float) -> float:
    return max(0.0, min(1.0, (v - min_v) / (max_v - min_v)))


def weighted_aura_index(skin_rgb: list[int], eye_hsv: list[float], light_reflection: float) -> tuple[int, dict[str, float]]:
    r, g, b = skin_rgb
    hue, sat, val = eye_hsv
    warm = normalize((r - b) + 128, 0, 255)
    cool = normalize((b - r) + 128, 0, 255)
    undertone_vector = (warm * 0.6) + (cool * 0.4)
    iris_vector = (hue / 360.0 * 0.7) + (sat * 0.3)
    light_vector = normalize(light_reflection, 0, 1)

    weighted = (undertone_vector * 0.5) + (iris_vector * 0.3) + (light_vector * 0.2)
    index = int(round(weighted * (len(AURA_PALETTE) - 1)))
    details = {
        "warm": round(warm, 3),
        "cool": round(cool, 3),
        "weighted": round(weighted, 3),
    }
    return index, details


def chakra_map(profile: AuraProfile, flux: float) -> dict[str, int]:
    base = {
        "Kök": 62,
        "Sakral": 66,
        "Solar": 70,
        "Kalp": 64,
        "Boğaz": 68,
        "Üçüncü Göz": 72,
        "Taç": 74,
    }
    for chakra in base:
        jitter = random.randint(-10, 10)
        base[chakra] = max(30, min(98, base[chakra] + jitter + int(flux * 8)))

    focus_boost = random.randint(8, 16)
    base[profile.chakra] = max(35, min(99, base[profile.chakra] + focus_boost))
    return base


def lucky_day_seed(aura_key: str) -> str:
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    return days[sum(ord(ch) for ch in aura_key) % len(days)]


def weekly_prediction(aura: AuraProfile, zodiac: str | None = None) -> dict[str, Any]:
    start = datetime.now(timezone.utc)
    steps = []
    for i in range(7):
        date = (start + timedelta(days=i)).astimezone().strftime("%d.%m")
        amplitude = random.randint(45, 98)
        steps.append({"date": date, "energy": amplitude})

    zodiac_hint = ZODIAC_HINTS.get((zodiac or "").strip().lower(), "Sezgin bu hafta pusulan olacak.")
    lucky_day = lucky_day_seed(aura.key)

    return {
        "lucky_day": lucky_day,
        "summary": f"{aura.name} frekansın yükseliyor. {zodiac_hint}",
        "zodiac_hint": zodiac_hint,
        "crystal": aura.crystal,
        "timeline": steps,
    }


def serialize_row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ("chakra_json", "prediction_json"):
        if key in data and isinstance(data[key], str):
            data[key] = json.loads(data[key])
    return data


init_db()


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    skin_rgb = payload.get("skin_rgb", [188, 154, 132])
    eye_hsv = payload.get("eye_hsv", [205.0, 0.33, 0.71])
    reflection = float(payload.get("light_reflection", random.uniform(0.4, 0.9)))
    zodiac = payload.get("zodiac", "")

    aura_idx, algorithm = weighted_aura_index(skin_rgb, eye_hsv, reflection)
    aura = AURA_PALETTE[aura_idx]
    chakra = chakra_map(aura, reflection)
    prediction = weekly_prediction(aura, zodiac)
    confidence = round(0.83 + random.uniform(0.03, 0.14), 3)

    scan = {
        "created_at": datetime.utcnow().isoformat(),
        "aura": {
            "key": aura.key,
            "name": aura.name,
            "hex": aura.hex,
            "element": aura.element,
            "chakra_focus": aura.chakra,
            "personality": aura.personality,
            "crystal": aura.crystal,
        },
        "confidence": confidence,
        "algorithm": {
            "skin_rgb": skin_rgb,
            "eye_hsv": eye_hsv,
            "light_reflection": reflection,
            **algorithm,
        },
        "chakra": chakra,
        "prediction": prediction,
    }

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO scans (
                created_at, aura_key, aura_name, aura_hex, confidence,
                warm_score, cool_score, eye_hue, light_reflection,
                personality, chakra_json, prediction_json, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan["created_at"],
                aura.key,
                aura.name,
                aura.hex,
                confidence,
                algorithm["warm"],
                algorithm["cool"],
                eye_hsv[0],
                reflection,
                aura.personality,
                json.dumps(chakra, ensure_ascii=False),
                json.dumps(prediction, ensure_ascii=False),
                payload.get("source", "webcam"),
            ),
        )

    return jsonify(scan)


@app.route("/api/trends")
def trends():
    with get_conn() as conn:
        weekly = conn.execute(
            """
            SELECT aura_name, aura_hex, COUNT(*) as cnt
            FROM scans
            WHERE datetime(created_at) >= datetime('now', '-7 day')
            GROUP BY aura_name, aura_hex
            ORDER BY cnt DESC
            LIMIT 12
            """
        ).fetchall()

        total = conn.execute("SELECT COUNT(*) AS n FROM scans").fetchone()["n"]

    top = [dict(row) for row in weekly]
    winner = top[0] if top else {"aura_name": "Mavi", "aura_hex": "#45B2FF", "cnt": 0}
    return jsonify(
        {
            "global_total_scans": total,
            "weekly_top": top,
            "headline": f"Bu hafta en çok {winner['aura_name']} aura görüldü.",
            "winner": winner,
        }
    )


@app.route("/api/journal", methods=["GET", "POST"])
def journal():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        note = str(payload.get("note", "")).strip()
        mood = int(payload.get("mood", 3))
        aura_key = payload.get("aura_key")
        tags = payload.get("tags", [])
        if not note:
            return jsonify({"error": "note required"}), 400

        with get_conn() as conn:
            conn.execute(
                "INSERT INTO journal_entries (created_at, note, mood, aura_key, tags) VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.utcnow().isoformat(),
                    note,
                    max(1, min(5, mood)),
                    aura_key,
                    ",".join(tags) if isinstance(tags, list) else str(tags),
                ),
            )
        return jsonify({"ok": True})

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, created_at, note, mood, aura_key, tags FROM journal_entries ORDER BY id DESC LIMIT 50"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/api/history")
def history():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, created_at, aura_name, aura_hex, confidence, chakra_json, prediction_json FROM scans ORDER BY id DESC LIMIT 30"
        ).fetchall()
    return jsonify([serialize_row(row) for row in rows])


@app.route("/healthz")
def health():
    return jsonify({"status": "ok", "db": str(DB_PATH)})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
