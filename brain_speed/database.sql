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
