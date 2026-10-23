import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'user_store.sqlite')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            author_id TEXT PRIMARY KEY,
            author_username TEXT,
            history_json TEXT,
            credibility_score REAL
        )
    ''')
    conn.commit()
    conn.close()

def update_user_history(author_id: str, username: str, history: list, score: float):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (author_id, author_username, history_json, credibility_score)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(author_id) DO UPDATE SET
            history_json=excluded.history_json,
            credibility_score=excluded.credibility_score
    ''', (author_id, username, json.dumps(history), score))
    conn.commit()
    conn.close()

def get_user(author_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE author_id = ?', (author_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "author_id": row["author_id"],
            "author_username": row["author_username"],
            "history": json.loads(row["history_json"]),
            "credibility_score": row["credibility_score"]
        }
    return None

init_db()
