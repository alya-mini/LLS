from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "avatars.db"

app = Flask(__name__)

AVATAR_STYLES = [
    "realistic",
    "anime",
    "cartoon",
    "meme",
    "cyberpunk",
    "fantasy",
    "scifi",
]

# 50+ CDN model entries
AVATAR_CATALOG = [
    {
        "id": idx,
        "name": f"Avatar {idx:02d}",
        "style": AVATAR_STYLES[idx % len(AVATAR_STYLES)],
        "thumbnail": f"https://picsum.photos/seed/avatar{idx}/240/320",
        "model_url": "https://modelviewer.dev/shared-assets/models/Astronaut.glb"
        if idx % 3 == 0
        else "https://modelviewer.dev/shared-assets/models/RobotExpressive.glb"
        if idx % 3 == 1
        else "https://modelviewer.dev/shared-assets/models/CartoonLowPoly.glb",
        "trending_score": random.randint(10, 100),
    }
    for idx in range(1, 56)
]


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS customizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avatar_id INTEGER NOT NULL,
            hair_type INTEGER NOT NULL,
            hair_color TEXT NOT NULL,
            eye_shape INTEGER NOT NULL,
            eye_color TEXT NOT NULL,
            outfit INTEGER NOT NULL,
            outfit_color TEXT NOT NULL,
            morph_smile REAL NOT NULL,
            morph_brow REAL NOT NULL,
            voice_preset TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS marketplace (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model_url TEXT NOT NULL,
            creator TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/avatars")
def api_avatars() -> Any:
    style = request.args.get("style")
    query = request.args.get("q", "").lower().strip()

    results = AVATAR_CATALOG
    if style:
        results = [item for item in results if item["style"] == style]
    if query:
        results = [item for item in results if query in item["name"].lower()]
    return jsonify({"avatars": results, "count": len(results)})


@app.get("/api/trending")
def api_trending() -> Any:
    trending = sorted(AVATAR_CATALOG, key=lambda x: x["trending_score"], reverse=True)[:12]
    return jsonify({"trending": trending})


@app.post("/api/customize")
def api_customize() -> Any:
    payload = request.get_json(force=True)
    required = [
        "avatar_id",
        "hair_type",
        "hair_color",
        "eye_shape",
        "eye_color",
        "outfit",
        "outfit_color",
        "morph_smile",
        "morph_brow",
        "voice_preset",
    ]
    missing = [field for field in required if field not in payload]
    if missing:
        return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400

    conn = get_db()
    conn.execute(
        """
        INSERT INTO customizations
        (avatar_id, hair_type, hair_color, eye_shape, eye_color, outfit, outfit_color, morph_smile, morph_brow, voice_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["avatar_id"],
            payload["hair_type"],
            payload["hair_color"],
            payload["eye_shape"],
            payload["eye_color"],
            payload["outfit"],
            payload["outfit_color"],
            payload["morph_smile"],
            payload["morph_brow"],
            payload["voice_preset"],
        ),
    )
    conn.commit()
    customization_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()
    return jsonify({"ok": True, "customization_id": customization_id})


@app.post("/api/marketplace")
def api_marketplace_upload() -> Any:
    payload = request.get_json(force=True)
    for key in ("name", "model_url", "creator"):
        if not payload.get(key):
            return jsonify({"error": f"{key} required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO marketplace(name, model_url, creator) VALUES (?, ?, ?)",
        (payload["name"], payload["model_url"], payload["creator"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.get("/api/marketplace")
def api_marketplace() -> Any:
    conn = get_db()
    rows = conn.execute("SELECT * FROM marketplace ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()
    return jsonify({"items": [dict(row) for row in rows]})


@app.get("/api/config")
def api_config() -> Any:
    return jsonify(
        {
            "languages": [
                "tr-TR",
                "en-US",
                "es-ES",
                "fr-FR",
                "de-DE",
                "it-IT",
                "ja-JP",
                "ko-KR",
                "pt-BR",
                "ar-SA",
                "ru-RU",
                "hi-IN",
            ],
            "voice_presets": ["natural", "robot", "child", "deep", "celebrity"],
            "limits": {
                "record_seconds": 15,
                "target_latency_ms": 50,
                "target_fps": 60,
            },
        }
    )


@app.get("/manifest.json")
def manifest() -> Any:
    data = json.loads((BASE_DIR / "static" / "manifest.json").read_text(encoding="utf-8"))
    return jsonify(data)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
