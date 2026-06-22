"""任务持久化 — SQLite 存储任务列表，支持增删改查。

独立于会话（session）：任务跨会话存在，直到主动删除。
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表（幂等）。"""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            items TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def create(title: str, items: list[str]) -> str:
    """创建任务列表，返回 task_id。

    items: ["查茅台净利润", "查比亚迪净利润", "汇总对比"]
    """
    task_id = uuid.uuid4().hex[:8]
    now = datetime.now().isoformat()
    items_json = json.dumps(
        [{"content": item, "status": "pending"} for item in items],
        ensure_ascii=False,
    )
    conn = _connect()
    conn.execute(
        "INSERT INTO tasks (id, title, items, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (task_id, title, items_json, now, now),
    )
    conn.commit()
    conn.close()
    return task_id


def update(task_id: str, item_index: int, status: str) -> str:
    """更新某一步的状态。status: pending / in_progress / completed / cancelled。

    返回：更新后的那一步描述，或错误信息。
    """
    conn = _connect()
    row = conn.execute("SELECT items FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        return f"错误：任务 {task_id} 不存在"

    items = json.loads(row["items"])
    if item_index < 0 or item_index >= len(items):
        conn.close()
        return f"错误：序号 {item_index} 超出范围（共 {len(items)} 步）"

    old_status = items[item_index]["status"]
    if old_status == "completed":
        conn.close()
        return f"步骤 {item_index} 已完成，无需重复标记"

    items[item_index]["status"] = status
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE tasks SET items = ?, updated_at = ? WHERE id = ?",
        (json.dumps(items, ensure_ascii=False), now, task_id),
    )
    conn.commit()
    conn.close()

    return (
        f"任务「{row['title']}」步骤 {item_index} "
        f"「{items[item_index]['content']}」→ {status}"
    )


def get(task_id: str) -> dict | None:
    """获取单个任务详情。"""
    conn = _connect()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "items": json.loads(row["items"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_active() -> list[dict]:
    """列出所有未全部完成的任务。"""
    conn = _connect()
    rows = conn.execute("SELECT * FROM tasks ORDER BY updated_at DESC").fetchall()
    conn.close()

    result = []
    for row in rows:
        items = json.loads(row["items"])
        all_done = all(item["status"] == "completed" for item in items)
        if all_done:
            continue
        done = sum(1 for item in items if item["status"] == "completed")
        result.append({
            "id": row["id"],
            "title": row["title"],
            "items": items,
            "progress": f"{done}/{len(items)}",
            "created_at": row["created_at"],
        })
    return result


def format_task(task: dict) -> str:
    """格式化任务为可读文本。"""
    lines = [f"任务：{task['title']}  [{task.get('progress', '')}]"]
    for i, item in enumerate(task["items"]):
        icon = {"pending": " ", "in_progress": "▸", "completed": "✓"}.get(item["status"], " ")
        lines.append(f"  [{icon}] {i}. {item['content']}")
    return "\n".join(lines)
