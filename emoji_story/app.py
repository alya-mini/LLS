"""
Emoji Story Anlatıcı - Flask Backend
------------------------------------
Bu dosya aşağıdaki görevleri üstlenir:
1) SQLite veritabanını ilk açılışta otomatik kurar.
2) Hikaye kayıtlarını alır, emojileri ve skorları saklar.
3) Trending / global galeri API'leri sağlar.
4) Basit analytics sayaçları (share/export/listen) tutar.
5) Push subscription endpoint'ini (demo) saklar.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory

# ---------------------------------------------------------------------------
# Flask application configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "stories.db"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(__name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATES_DIR))
app.config["JSON_AS_ASCII"] = False


@dataclass
class StoryPayload:
    """Client'tan gelen hikaye gövdesi için doğrulanmış taşıyıcı."""

    text: str
    emoji_sequence: str
    language: str
    mood: str
    title: str
    author_name: str
    duration_seconds: int
    theme: str
    score: int = 0


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """SQLite bağlantısı döner ve row factory ile dict-benzeri erişim açılır."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def create_tables() -> None:
    """Uygulama için gereken tüm tabloları oluşturur."""
    with closing(get_db()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                emoji_sequence TEXT NOT NULL,
                language TEXT NOT NULL,
                mood TEXT NOT NULL,
                author_name TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL DEFAULT 15,
                theme TEXT NOT NULL DEFAULT 'cinematic',
                score INTEGER NOT NULL DEFAULT 0,
                shares INTEGER NOT NULL DEFAULT 0,
                exports INTEGER NOT NULL DEFAULT 0,
                plays INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                event_name TEXT NOT NULL,
                meta_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(story_id) REFERENCES stories(id)
            );

            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_stories_created_at ON stories(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_stories_score ON stories(score DESC, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_analytics_event_name ON analytics_events(event_name);
            """
        )
        conn.commit()


def now_iso() -> str:
    """UTC ISO timestamp üretir."""
    return datetime.now(tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def parse_story_payload(payload: Dict[str, Any]) -> StoryPayload:
    """API'den gelen veriyi temizler ve zorunlu alanları doğrular."""
    text = str(payload.get("text", "")).strip()
    emoji_sequence = str(payload.get("emoji_sequence", "")).strip()
    language = str(payload.get("language", "tr")).strip().lower()
    mood = str(payload.get("mood", "funny")).strip().lower()
    title = str(payload.get("title", "Emoji Story")).strip()
    author_name = str(payload.get("author_name", "Anonim")).strip()
    theme = str(payload.get("theme", "cinematic")).strip().lower()

    try:
        duration_seconds = int(payload.get("duration_seconds", 15))
    except (TypeError, ValueError):
        duration_seconds = 15

    try:
        score = int(payload.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    if not text:
        raise ValueError("text alanı boş olamaz")
    if not emoji_sequence:
        raise ValueError("emoji_sequence alanı boş olamaz")
    if duration_seconds < 5 or duration_seconds > 60:
        raise ValueError("duration_seconds 5-60 arasında olmalıdır")

    return StoryPayload(
        text=text,
        emoji_sequence=emoji_sequence,
        language=language,
        mood=mood,
        title=title[:80],
        author_name=author_name[:50],
        duration_seconds=duration_seconds,
        theme=theme[:40],
        score=max(0, min(score, 10_000)),
    )


def row_to_story(row: sqlite3.Row) -> Dict[str, Any]:
    """SQLite satırını JSON dostu dict formatına dönüştürür."""
    return {
        "id": row["id"],
        "title": row["title"],
        "text": row["text"],
        "emoji_sequence": row["emoji_sequence"],
        "language": row["language"],
        "mood": row["mood"],
        "author_name": row["author_name"],
        "duration_seconds": row["duration_seconds"],
        "theme": row["theme"],
        "score": row["score"],
        "shares": row["shares"],
        "exports": row["exports"],
        "plays": row["plays"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ---------------------------------------------------------------------------
# Core routes
# ---------------------------------------------------------------------------
@app.route("/")
def index() -> str:
    """Single-page PWA arayüzü."""
    return render_template("index.html")


@app.route("/health")
def health() -> Any:
    """Hızlı healthcheck endpoint."""
    return jsonify({"status": "ok", "time": now_iso()})


@app.route("/api/stories", methods=["GET"])
def list_stories() -> Any:
    """Global hikaye galerisi için son kayıtları döndürür."""
    limit = min(int(request.args.get("limit", 20)), 100)
    language = request.args.get("language")

    query = "SELECT * FROM stories"
    params: List[Any] = []
    if language:
        query += " WHERE language = ?"
        params.append(language.lower())

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with closing(get_db()) as conn:
        rows = conn.execute(query, params).fetchall()

    return jsonify({"items": [row_to_story(r) for r in rows]})


@app.route("/api/stories", methods=["POST"])
def create_story() -> Any:
    """Yeni hikaye oluşturur ve DB'ye kaydeder."""
    payload = request.get_json(silent=True) or {}
    try:
        story = parse_story_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    story_id = str(uuid.uuid4())
    now = now_iso()

    with closing(get_db()) as conn:
        conn.execute(
            """
            INSERT INTO stories (
                id, title, text, emoji_sequence, language, mood,
                author_name, duration_seconds, theme, score,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                story_id,
                story.title,
                story.text,
                story.emoji_sequence,
                story.language,
                story.mood,
                story.author_name,
                story.duration_seconds,
                story.theme,
                story.score,
                now,
                now,
            ),
        )
        conn.commit()

    return jsonify({"id": story_id, "message": "story created"}), 201


@app.route("/api/stories/<story_id>", methods=["GET"])
def get_story(story_id: str) -> Any:
    """Tek hikaye detayını getirir."""
    with closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM stories WHERE id = ?", (story_id,)).fetchone()

    if not row:
        return jsonify({"error": "story not found"}), 404

    return jsonify(row_to_story(row))


@app.route("/api/stories/<story_id>/event", methods=["POST"])
def log_story_event(story_id: str) -> Any:
    """Share/export/play gibi aksiyonları sayar ve analytics event'i oluşturur."""
    payload = request.get_json(silent=True) or {}
    event_name = str(payload.get("event_name", "unknown")).strip().lower()
    meta = payload.get("meta", {})
    if not event_name:
        return jsonify({"error": "event_name required"}), 400

    counters = {
        "share": "shares",
        "export": "exports",
        "play": "plays",
    }
    now = now_iso()

    with closing(get_db()) as conn:
        story_exists = conn.execute(
            "SELECT 1 FROM stories WHERE id = ?", (story_id,)
        ).fetchone()
        if not story_exists:
            return jsonify({"error": "story not found"}), 404

        if event_name in counters:
            col = counters[event_name]
            conn.execute(
                f"UPDATE stories SET {col} = {col} + 1, updated_at = ? WHERE id = ?",
                (now, story_id),
            )

        conn.execute(
            """
            INSERT INTO analytics_events (story_id, event_name, meta_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (story_id, event_name, json.dumps(meta, ensure_ascii=False), now),
        )
        conn.commit()

    return jsonify({"message": "event logged"})


@app.route("/api/trending", methods=["GET"])
def trending() -> Any:
    """Skor + etkileşim ağırlıklı trending listesi."""
    limit = min(int(request.args.get("limit", 10)), 50)
    with closing(get_db()) as conn:
        rows = conn.execute(
            """
            SELECT *,
                (score * 2 + shares * 4 + exports * 3 + plays) AS trend_score
            FROM stories
            ORDER BY trend_score DESC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    items: List[Dict[str, Any]] = []
    for row in rows:
        item = row_to_story(row)
        item["trend_score"] = row["trend_score"]
        items.append(item)

    return jsonify({"items": items})


@app.route("/api/analytics/summary", methods=["GET"])
def analytics_summary() -> Any:
    """Basit toplam metrikleri döndürür."""
    with closing(get_db()) as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS story_count,
                SUM(shares) AS total_shares,
                SUM(exports) AS total_exports,
                SUM(plays) AS total_plays
            FROM stories
            """
        ).fetchone()
        events = conn.execute(
            """
            SELECT event_name, COUNT(*) AS count
            FROM analytics_events
            GROUP BY event_name
            ORDER BY count DESC
            """
        ).fetchall()

    return jsonify(
        {
            "story_count": totals["story_count"] or 0,
            "total_shares": totals["total_shares"] or 0,
            "total_exports": totals["total_exports"] or 0,
            "total_plays": totals["total_plays"] or 0,
            "events": [{"event": e["event_name"], "count": e["count"]} for e in events],
        }
    )


@app.route("/api/push/subscribe", methods=["POST"])
def subscribe_push() -> Any:
    """Push subscription payload'unu DB'de saklar (demo amaçlı)."""
    payload = request.get_json(silent=True) or {}
    endpoint = str(payload.get("endpoint", "")).strip()
    if not endpoint:
        return jsonify({"error": "endpoint required"}), 400

    with closing(get_db()) as conn:
        conn.execute(
            """
            INSERT INTO push_subscriptions (endpoint, payload_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(endpoint) DO UPDATE SET payload_json=excluded.payload_json
            """,
            (endpoint, json.dumps(payload, ensure_ascii=False), now_iso()),
        )
        conn.commit()

    return jsonify({"message": "subscription saved"})


@app.route("/manifest.json")
def manifest() -> Any:
    """PWA manifest servisi."""
    return send_from_directory(STATIC_DIR, "manifest.json")


@app.route("/service-worker.js")
def service_worker() -> Any:
    """Service worker dosyası."""
    return send_from_directory(STATIC_DIR, "service-worker.js")


@app.route("/api/seed", methods=["POST"])
def seed_demo_data() -> Any:
    """Geliştirme sırasında galeri boş olmasın diye örnek veri ekler."""
    demo = [
        {
            "title": "Kedi Macerası",
            "text": "Dün parkta bir kedi gördüm ve çok komikti",
            "emoji_sequence": "😺🌳😂🏃‍♂️💨",
            "language": "tr",
            "mood": "funny",
            "author_name": "DemoUser",
            "theme": "funny",
            "score": 87,
        },
        {
            "title": "Love Story",
            "text": "We met under stars and fell in love",
            "emoji_sequence": "🌙✨❤️🥰",
            "language": "en",
            "mood": "romantic",
            "author_name": "RomanticAI",
            "theme": "romantic",
            "score": 95,
        },
    ]

    inserted = 0
    with closing(get_db()) as conn:
        for payload in demo:
            story_id = str(uuid.uuid4())
            now = now_iso()
            conn.execute(
                """
                INSERT INTO stories (
                    id, title, text, emoji_sequence, language, mood,
                    author_name, duration_seconds, theme, score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    story_id,
                    payload["title"],
                    payload["text"],
                    payload["emoji_sequence"],
                    payload["language"],
                    payload["mood"],
                    payload["author_name"],
                    15,
                    payload["theme"],
                    payload["score"],
                    now,
                    now,
                ),
            )
            inserted += 1
        conn.commit()

    return jsonify({"inserted": inserted})


def bootstrap() -> None:
    """Uygulama ayağa kalkmadan önce gerekli hazırlıkları yapar."""
    os.makedirs(STATIC_DIR, exist_ok=True)
    create_tables()


bootstrap()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
