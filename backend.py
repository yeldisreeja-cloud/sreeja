# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime

app = Flask(__name__)
CORS(app)  # allow frontend JS apps to connect (React, HTML)

DB = "wellness.db"

# --- Database setup ---
def init_db():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                mood INTEGER,
                note TEXT
            )
        ''')
        conn.commit()

init_db()

# --- Sensitive text analysis (demo heuristic) ---
FLAGS = ["suicide", "kill", "die", "hurt", "hopeless", "alone", "worthless"]

def analyze_text(note: str):
    if not note:
        return {"score": 0, "found": []}
    lowered = note.lower()
    found = [w for w in FLAGS if w in lowered]
    score = min(1, len(found) / 2)  # crude scoring
    return {"score": score, "found": found}


# --- API Routes ---
@app.route("/checkin", methods=["POST"])
def add_checkin():
    data = request.json
    mood = data.get("mood")
    note = data.get("note", "")

    if mood is None:
        return jsonify({"error": "Mood is required"}), 400

    timestamp = datetime.datetime.utcnow().isoformat()
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO checkins (timestamp, mood, note) VALUES (?, ?, ?)", 
                    (timestamp, mood, note))
        conn.commit()
    
    analysis = analyze_text(note)
    return jsonify({
        "message": "Check-in saved",
        "timestamp": timestamp,
        "analysis": analysis
    })


@app.route("/checkins", methods=["GET"])
def get_checkins():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT timestamp, mood, note FROM checkins ORDER BY timestamp DESC LIMIT 50")
        rows = cur.fetchall()
    result = [{"timestamp": r[0], "mood": r[1], "note": r[2]} for r in rows]
    return jsonify(result)


@app.route("/recommendations", methods=["GET"])
def get_recommendations():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT mood FROM checkins ORDER BY timestamp DESC LIMIT 3")
        rows = cur.fetchall()
    moods = [r[0] for r in rows]
    avg = sum(moods)/len(moods) if moods else 3

    recs = []
    if avg <= 2.5:
        recs = [
            "Try a 5-minute breathing exercise",
            "Reach out to a friend or family member",
            "Short guided mindfulness session (10 mins)"
        ]
    elif avg <= 3.5:
        recs = [
            "Take a quick walk or stretch break",
            "Do a short gratitude list: 3 things you appreciated today"
        ]
    else:
        recs = [
            "Keep the momentum — consider journaling one positive event",
            "Celebrate your progress with a small reward"
        ]

    return jsonify(recs)
    if __name__ == "__main__":
    app.run(debug=True)


