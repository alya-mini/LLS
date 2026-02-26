import json
import math
import os
import random
import sqlite3
import string
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room

# ------------------------------------------------------------
# Flask uygulama ayarları
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "brain_speed.db"

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "brain-speed-secret")

# CORS açık tutuldu; multiplayer testleri için gerekli.
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=30,
    ping_interval=10,
)


# ------------------------------------------------------------
# Yardımcı veri yapıları
# ------------------------------------------------------------
ONLINE_USERS = {}
ROOMS = {}
ACTIVE_MATCHES = {}

BRAIN_TYPES = [
    "Hızlı Düşünür",
    "Stratejik Analist",
    "Yaratıcı Sentezci",
    "Dengeli Zihin",
]

COUNTRIES = ["TR", "US", "DE", "FR", "GB", "JP", "KR", "BR", "ES", "IT"]


# ------------------------------------------------------------
# DB yardımcıları
# ------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """İlk açılışta tüm tabloları oluşturur."""
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            country TEXT DEFAULT 'TR',
            created_at TEXT NOT NULL,
            preferred_lang TEXT DEFAULT 'tr'
        );

        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_type TEXT NOT NULL,
            accuracy REAL NOT NULL,
            avg_reaction_ms REAL NOT NULL,
            score REAL NOT NULL,
            percentile REAL DEFAULT 0,
            brain_type TEXT,
            details_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT NOT NULL,
            winner_user_id INTEGER,
            status TEXT NOT NULL,
            started_at TEXT,
            ended_at TEXT
        );

        CREATE TABLE IF NOT EXISTS match_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            total_score REAL DEFAULT 0,
            avg_reaction_ms REAL DEFAULT 0,
            FOREIGN KEY(match_id) REFERENCES matches(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            payload_json TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    conn.commit()
    conn.close()


# ------------------------------------------------------------
# İş kuralları
# ------------------------------------------------------------
def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def normalize(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.0
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def compute_score(accuracy: float, avg_reaction_ms: float) -> float:
    """Skor = (Doğruluk x 80) + (Hız x 20)."""
    speed = 1.0 - normalize(avg_reaction_ms, 120, 1500)
    weighted = (accuracy * 80.0) + (speed * 20.0)
    return round(weighted, 2)


def infer_brain_type(test_results: list) -> str:
    """Test sonuç desenine göre beyin tipi döndürür."""
    if not test_results:
        return "Dengeli Zihin"

    avg_acc = sum(x.get("accuracy", 0) for x in test_results) / len(test_results)
    avg_ms = sum(x.get("reactionMs", 800) for x in test_results) / len(test_results)
    variance = _variance([x.get("reactionMs", 800) for x in test_results])

    if avg_ms < 320 and avg_acc > 0.7:
        return "Hızlı Düşünür"
    if avg_acc > 0.85 and variance < 12000:
        return "Stratejik Analist"
    if variance > 70000:
        return "Yaratıcı Sentezci"
    return "Dengeli Zihin"


def _variance(values: list) -> float:
    if not values:
        return 0.0
    m = sum(values) / len(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def calculate_percentile(score: float) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM scores")
    total = cur.fetchone()["c"]
    if total == 0:
        conn.close()
        return 100.0

    cur.execute("SELECT COUNT(*) as c FROM scores WHERE score <= ?", (score,))
    lower_or_equal = cur.fetchone()["c"]
    conn.close()
    percentile = (lower_or_equal / total) * 100
    return round(percentile, 2)


def ensure_user(username: str, country: str = "TR", lang: str = "tr") -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if row:
        user_id = row["id"]
    else:
        cur.execute(
            "INSERT INTO users (username, country, created_at, preferred_lang) VALUES (?, ?, ?, ?)",
            (username, country, now_iso(), lang),
        )
        user_id = cur.lastrowid
        conn.commit()
    conn.close()
    return user_id


def track_event(event_name: str, payload: dict | None = None) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO analytics (event_name, payload_json, created_at) VALUES (?, ?, ?)",
        (event_name, json.dumps(payload or {}), now_iso()),
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------
# HTTP route'ları
# ------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/manifest.json")
def manifest():
    return send_from_directory(BASE_DIR / "static", "manifest.json")


@app.get("/service-worker.js")
def service_worker():
    return send_from_directory(BASE_DIR / "static", "service-worker.js")


@app.post("/api/submit_score")
def submit_score():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "guest")[:32]
    country = data.get("country", "TR")
    lang = data.get("lang", "tr")
    test_type = data.get("testType", "mixed")
    accuracy = float(data.get("accuracy", 0.0))
    avg_reaction_ms = float(data.get("avgReactionMs", 1000))
    details = data.get("details", [])

    user_id = ensure_user(username, country=country, lang=lang)
    score = compute_score(accuracy, avg_reaction_ms)
    brain_type = infer_brain_type(details if isinstance(details, list) else [])
    percentile = calculate_percentile(score)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO scores (
            user_id, test_type, accuracy, avg_reaction_ms, score, percentile,
            brain_type, details_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            test_type,
            accuracy,
            avg_reaction_ms,
            score,
            percentile,
            brain_type,
            json.dumps(details),
            now_iso(),
        ),
    )
    conn.commit()
    conn.close()

    track_event("submit_score", {"username": username, "score": score, "testType": test_type})

    payload = {
        "ok": True,
        "score": score,
        "percentile": percentile,
        "brainType": brain_type,
    }
    socketio.emit("leaderboard_updated", get_leaderboard_payload())
    return jsonify(payload)


@app.get("/api/leaderboard")
def leaderboard():
    return jsonify(get_leaderboard_payload())


@app.get("/api/analytics")
def analytics():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT event_name, COUNT(*) as count FROM analytics GROUP BY event_name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"events": rows})


@app.post("/api/create_room")
def create_room():
    data = request.get_json(silent=True) or {}
    room_code = _gen_room_code()
    username = data.get("username", "guest")[:32]
    user_id = ensure_user(username, country=data.get("country", "TR"), lang=data.get("lang", "tr"))

    ROOMS[room_code] = {
        "host": username,
        "players": {username: {"user_id": user_id, "ready": False, "score": 0}},
        "created": time.time(),
        "status": "waiting",
    }
    track_event("room_created", {"room": room_code, "host": username})
    return jsonify({"ok": True, "roomCode": room_code})


@app.post("/api/join_room")
def join_room_http():
    data = request.get_json(silent=True) or {}
    room_code = (data.get("roomCode") or "").upper()
    username = data.get("username", "guest")[:32]

    if room_code not in ROOMS:
        return jsonify({"ok": False, "error": "Room not found"}), 404

    room = ROOMS[room_code]
    if len(room["players"]) >= 4 and username not in room["players"]:
        return jsonify({"ok": False, "error": "Room full"}), 400

    user_id = ensure_user(username, country=data.get("country", "TR"), lang=data.get("lang", "tr"))
    room["players"][username] = {"user_id": user_id, "ready": False, "score": 0}

    track_event("room_joined", {"room": room_code, "user": username})
    socketio.emit("room_state", room_snapshot(room_code), to=room_code)
    return jsonify({"ok": True, "room": room_snapshot(room_code)})


@app.get("/api/countries")
def countries():
    return jsonify({"countries": COUNTRIES})


# ------------------------------------------------------------
# SocketIO event'leri
# ------------------------------------------------------------
@socketio.on("connect")
def on_connect():
    emit("connected", {"id": request.sid, "timestamp": now_iso()})


@socketio.on("disconnect")
def on_disconnect():
    user = ONLINE_USERS.pop(request.sid, None)
    if not user:
        return
    room_code = user.get("room")
    username = user.get("username")
    if room_code in ROOMS and username in ROOMS[room_code]["players"]:
        ROOMS[room_code]["players"].pop(username, None)
        emit("room_state", room_snapshot(room_code), to=room_code)


@socketio.on("presence")
def on_presence(data):
    username = (data or {}).get("username", "guest")[:32]
    ONLINE_USERS[request.sid] = {"username": username, "room": None}
    emit("presence_ack", {"online": len(ONLINE_USERS)})


@socketio.on("join_room")
def on_join_room(data):
    data = data or {}
    room_code = (data.get("roomCode") or "").upper()
    username = data.get("username", "guest")[:32]

    if room_code not in ROOMS:
        emit("error_msg", {"error": "Room not found"})
        return

    join_room(room_code)
    ONLINE_USERS.setdefault(request.sid, {})["username"] = username
    ONLINE_USERS[request.sid]["room"] = room_code

    if username not in ROOMS[room_code]["players"]:
        user_id = ensure_user(username)
        ROOMS[room_code]["players"][username] = {"user_id": user_id, "ready": False, "score": 0}

    emit("room_state", room_snapshot(room_code), to=room_code)


@socketio.on("leave_room")
def on_leave_room(data):
    data = data or {}
    room_code = (data.get("roomCode") or "").upper()
    username = data.get("username", "guest")[:32]

    leave_room(room_code)
    if room_code in ROOMS:
        ROOMS[room_code]["players"].pop(username, None)
        emit("room_state", room_snapshot(room_code), to=room_code)


@socketio.on("player_ready")
def on_player_ready(data):
    data = data or {}
    room_code = (data.get("roomCode") or "").upper()
    username = data.get("username", "guest")[:32]

    room = ROOMS.get(room_code)
    if not room:
        emit("error_msg", {"error": "Room not found"})
        return

    if username in room["players"]:
        room["players"][username]["ready"] = True

    ready_count = sum(1 for p in room["players"].values() if p.get("ready"))
    emit("room_state", room_snapshot(room_code), to=room_code)

    if ready_count >= 2:
        start_match(room_code)


@socketio.on("match_progress")
def on_match_progress(data):
    data = data or {}
    room_code = (data.get("roomCode") or "").upper()
    username = data.get("username", "guest")[:32]
    score = float(data.get("score", 0))

    room = ROOMS.get(room_code)
    if not room:
        return

    if username in room["players"]:
        room["players"][username]["score"] = score

    emit(
        "live_progress",
        {
            "roomCode": room_code,
            "players": [
                {"username": u, "score": p.get("score", 0)}
                for u, p in room["players"].items()
            ],
        },
        to=room_code,
    )


@socketio.on("finish_match")
def on_finish_match(data):
    data = data or {}
    room_code = (data.get("roomCode") or "").upper()
    username = data.get("username", "guest")[:32]
    final_score = float(data.get("finalScore", 0))
    reaction_ms = float(data.get("avgReactionMs", 900))

    room = ROOMS.get(room_code)
    if not room:
        emit("error_msg", {"error": "Room not found"})
        return

    room["players"].setdefault(username, {"score": 0, "ready": True})
    room["players"][username]["score"] = final_score
    room["players"][username]["avgReactionMs"] = reaction_ms
    room["players"][username]["finished"] = True

    all_finished = all(p.get("finished") for p in room["players"].values() if p.get("ready"))
    emit("room_state", room_snapshot(room_code), to=room_code)

    if all_finished:
        finalize_match(room_code)


# ------------------------------------------------------------
# Multiplayer yardımcıları
# ------------------------------------------------------------
def _gen_room_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(alphabet) for _ in range(6))
        if code not in ROOMS:
            return code


def room_snapshot(room_code: str) -> dict:
    room = ROOMS.get(room_code, {"players": {}})
    return {
        "roomCode": room_code,
        "status": room.get("status", "waiting"),
        "host": room.get("host"),
        "players": [
            {
                "username": username,
                "ready": data.get("ready", False),
                "score": round(data.get("score", 0), 2),
                "finished": data.get("finished", False),
            }
            for username, data in room.get("players", {}).items()
        ],
    }


def start_match(room_code: str):
    room = ROOMS.get(room_code)
    if not room:
        return

    room["status"] = "running"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO matches (room_code, status, started_at) VALUES (?, ?, ?)",
        (room_code, "running", now_iso()),
    )
    match_id = cur.lastrowid

    for username, pdata in room["players"].items():
        cur.execute(
            "INSERT INTO match_players (match_id, user_id, total_score, avg_reaction_ms) VALUES (?, ?, ?, ?)",
            (match_id, pdata.get("user_id", ensure_user(username)), 0, 0),
        )

    conn.commit()
    conn.close()

    ACTIVE_MATCHES[room_code] = {"match_id": match_id, "started_at": time.time()}
    track_event("match_started", {"room": room_code, "matchId": match_id})

    emit("match_started", {"roomCode": room_code, "matchId": match_id}, to=room_code)


def finalize_match(room_code: str):
    room = ROOMS.get(room_code)
    active = ACTIVE_MATCHES.get(room_code)
    if not room or not active:
        return

    ranked = sorted(room["players"].items(), key=lambda x: x[1].get("score", 0), reverse=True)
    winner_username = ranked[0][0] if ranked else None
    winner_data = ranked[0][1] if ranked else {}

    conn = get_conn()
    cur = conn.cursor()

    winner_user_id = winner_data.get("user_id") if winner_data else None
    cur.execute(
        "UPDATE matches SET winner_user_id = ?, status = ?, ended_at = ? WHERE id = ?",
        (winner_user_id, "finished", now_iso(), active["match_id"]),
    )

    for username, pdata in room["players"].items():
        uid = pdata.get("user_id", ensure_user(username))
        cur.execute(
            "UPDATE match_players SET total_score = ?, avg_reaction_ms = ? WHERE match_id = ? AND user_id = ?",
            (pdata.get("score", 0), pdata.get("avgReactionMs", 0), active["match_id"], uid),
        )

    conn.commit()
    conn.close()

    room["status"] = "finished"
    track_event("match_finished", {"room": room_code, "winner": winner_username})

    emit(
        "match_finished",
        {
            "roomCode": room_code,
            "winner": winner_username,
            "ranking": [
                {"username": u, "score": round(d.get("score", 0), 2)} for u, d in ranked
            ],
        },
        to=room_code,
    )


def get_leaderboard_payload() -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.score, s.avg_reaction_ms, s.brain_type, s.percentile, s.created_at,
               u.username, u.country
        FROM scores s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.score DESC, s.avg_reaction_ms ASC
        LIMIT 50
        """
    )
    rows = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT u.country, MAX(s.score) as top_score
        FROM scores s
        JOIN users u ON u.id = s.user_id
        GROUP BY u.country
        ORDER BY top_score DESC
        LIMIT 10
        """
    )
    country_rows = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {"global": rows, "countries": country_rows, "updatedAt": now_iso()}


# ------------------------------------------------------------
# Hata yönetimi
# ------------------------------------------------------------
@app.errorhandler(404)
def not_found(_e):
    return jsonify({"ok": False, "error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    track_event("server_error", {"msg": str(e)})
    return jsonify({"ok": False, "error": "Server error"}), 500


# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("🧠 Düşünce Hızı Testi çalışıyor: http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
