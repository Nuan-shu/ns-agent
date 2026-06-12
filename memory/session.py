"""会话持久化 — SQLite 存储对话历史，启动时恢复。"""
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表（幂等）。"""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            tool_calls TEXT,
            tool_call_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)
    conn.commit()
    conn.close()


def create_session():
    """新建会话，返回 session_id。"""
    sid = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    conn = _connect()
    conn.execute(
        "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
        (sid, now, now)
    )
    conn.commit()
    conn.close()
    return sid


def save_message(session_id, msg):
    """保存一条消息。

    msg 格式（OpenAI messages 列表中的一条）：
      {"role": "user", "content": "你好"}
      {"role": "assistant", "content": "你好！", "tool_calls": null}
      {"role": "tool", "tool_call_id": "xxx", "content": "..."}
    """
    now = datetime.now().isoformat()
    conn = _connect()
    conn.execute(
        """INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            msg.get("role"),
            msg.get("content"),
            json.dumps(msg.get("tool_calls")) if msg.get("tool_calls") else None,
            msg.get("tool_call_id"),
            now
        )
    )
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (now, session_id)
    )
    conn.commit()
    conn.close()


def load_session(session_id):
    """从数据库恢复消息列表。"""
    conn = _connect()
    rows = conn.execute(
        "SELECT role, content, tool_calls, tool_call_id FROM messages "
        "WHERE session_id = ? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()

    messages = []
    for row in rows:
        msg = {"role": row["role"]}
        if row["content"] is not None:
            msg["content"] = row["content"]
        if row["tool_calls"]:
            msg["tool_calls"] = json.loads(row["tool_calls"])
            msg["content"] = None  # OpenAI 格式要求
        if row["tool_call_id"]:
            msg["tool_call_id"] = row["tool_call_id"]
        messages.append(msg)
    return messages


def get_last_session():
    """获取最近 24 小时内的最新会话 ID，没有则返回 None。"""
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    conn = _connect()
    row = conn.execute(
        "SELECT id FROM sessions WHERE updated_at >= ? ORDER BY updated_at DESC LIMIT 1",
        (cutoff,)
    ).fetchone()
    conn.close()
    return row["id"] if row else None
