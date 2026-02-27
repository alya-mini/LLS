import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "games.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "mind-reader-neon-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

rooms = {}


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT NOT NULL,
            player_name TEXT NOT NULL,
            score REAL NOT NULL,
            category TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def generate_room_code():
    import random
    import string
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn = get_db_conn()
        exists = conn.execute("SELECT 1 FROM rooms WHERE room_code = ?", (code,)).fetchone()
        conn.close()
        if not exists:
            return code


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/create_room", methods=["POST"])
def create_room():
    data = request.get_json(force=True)
    name = data.get("name", "Anon")[:24]
    room_code = generate_room_code()

    conn = get_db_conn()
    conn.execute(
        "INSERT INTO rooms (room_code, created_at, created_by) VALUES (?, ?, ?)",
        (room_code, datetime.utcnow().isoformat(), name),
    )
    conn.commit()
    conn.close()

    rooms[room_code] = {"players": {}, "spectators": set(), "state": "lobby"}
    return jsonify({"room_code": room_code})


@app.route("/api/leaderboard")
def leaderboard():
    conn = get_db_conn()
    global_top = conn.execute(
        """
        SELECT player_name, ROUND(AVG(score), 2) avg_score, COUNT(*) plays
        FROM scores
        GROUP BY player_name
        HAVING plays >= 1
        ORDER BY avg_score DESC
        LIMIT 20
        """
    ).fetchall()
    room_code = request.args.get("room")
    room_top = []
    if room_code:
        room_top = conn.execute(
            """
            SELECT player_name, ROUND(AVG(score), 2) avg_score, COUNT(*) plays
            FROM scores
            WHERE room_code = ?
            GROUP BY player_name
            ORDER BY avg_score DESC
            LIMIT 10
            """,
            (room_code,),
        ).fetchall()
    conn.close()
    return jsonify(
        {
            "global": [dict(row) for row in global_top],
            "friends": [dict(row) for row in room_top],
        }
    )


@app.route("/manifest.json")
def manifest():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "manifest.json")


@app.route("/service-worker.js")
def sw():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "service-worker.js")


@socketio.on("join_room")
def on_join(data):
    room_code = data.get("room_code", "").upper()
    name = data.get("name", "Anon")[:24]
    role = data.get("role", "player")

    if room_code not in rooms:
        rooms[room_code] = {"players": {}, "spectators": set(), "state": "lobby"}

    room = rooms[room_code]
    sid = request.sid

    if role == "player" and len(room["players"]) >= 4:
        emit("join_error", {"message": "Room full. Join as spectator."})
        return

    join_room(room_code)
    if role == "spectator":
        room["spectators"].add(sid)
    else:
        room["players"][sid] = {
            "name": name,
            "emotion": [0.33, 0.33, 0.34],
            "pupil": 0.5,
            "timing": None,
            "score": 0,
        }

    emit(
        "room_state",
        {
            "players": [{"sid": psid, **pdata} for psid, pdata in room["players"].items()],
            "spectator_count": len(room["spectators"]),
            "state": room["state"],
        },
        room=room_code,
    )
    emit("joined", {"sid": sid, "room_code": room_code, "role": role})


@socketio.on("signal")
def on_signal(data):
    target_sid = data.get("target")
    if target_sid:
        emit("signal", {"from": request.sid, "signal": data.get("signal")}, room=target_sid)


@socketio.on("reaction")
def on_reaction(data):
    room_code = data.get("room_code")
    emit("reaction", {"from": request.sid, "emoji": data.get("emoji", "🧠")}, room=room_code)


@socketio.on("thought_data")
def on_thought_data(data):
    room_code = data.get("room_code")
    player = rooms.get(room_code, {}).get("players", {}).get(request.sid)
    if not player:
        return

    player["emotion"] = data.get("emotion", player["emotion"])
    player["pupil"] = float(data.get("pupil", player["pupil"]))
    player["timing"] = float(data.get("timing", datetime.utcnow().timestamp()))


@socketio.on("submit_round")
def on_submit_round(data):
    room_code = data.get("room_code")
    category = data.get("category", "genel")
    room = rooms.get(room_code)
    if not room or len(room["players"]) < 2:
        return

    players = list(room["players"].items())
    timings = [p[1]["timing"] for p in players if p[1]["timing"] is not None]
    if not timings:
        timings = [datetime.utcnow().timestamp()]
    t_min, t_max = min(timings), max(timings)

    def corr(a, b):
        # tiny pearson approximation for 3 element vectors
        import math

        ma = sum(a) / len(a)
        mb = sum(b) / len(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den_a = math.sqrt(sum((x - ma) ** 2 for x in a))
        den_b = math.sqrt(sum((y - mb) ** 2 for y in b))
        if den_a == 0 or den_b == 0:
            return 0
        return max(-1.0, min(1.0, num / (den_a * den_b)))

    pair_scores = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            p1 = players[i][1]
            p2 = players[j][1]
            emotion_c = (corr(p1["emotion"], p2["emotion"]) + 1) / 2
            pupil_sync = 1 - min(1, abs(p1["pupil"] - p2["pupil"]))
            dt = abs((p1["timing"] or t_max) - (p2["timing"] or t_max))
            timing_sync = 1 - min(1, dt / 5.0)
            score = (emotion_c * 0.6) + (pupil_sync * 0.2) + (timing_sync * 0.2)
            pair_scores.append(score)

    group = sum(pair_scores) / len(pair_scores) if pair_scores else 0
    group_score = round(group * 100, 2)

    conn = get_db_conn()
    now = datetime.utcnow().isoformat()
    for sid, pdata in players:
        pdata["score"] = group_score
        conn.execute(
            "INSERT INTO scores (room_code, player_name, score, category, created_at) VALUES (?, ?, ?, ?, ?)",
            (room_code, pdata["name"], group_score, category, now),
        )
    conn.commit()
    conn.close()

    emit(
        "round_result",
        {
            "group_score": group_score,
            "players": [{"sid": sid, **pdata} for sid, pdata in players],
            "category": category,
        },
        room=room_code,
    )


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    for room_code, room in rooms.items():
        if sid in room["players"]:
            del room["players"][sid]
            leave_room(room_code)
            emit(
                "room_state",
                {
                    "players": [{"sid": psid, **pdata} for psid, pdata in room["players"].items()],
                    "spectator_count": len(room["spectators"]),
                    "state": room["state"],
                },
                room=room_code,
            )
        if sid in room["spectators"]:
            room["spectators"].remove(sid)


if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
