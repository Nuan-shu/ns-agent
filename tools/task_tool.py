"""任务管理工具 — 创建、更新、查看任务列表。

Agent 用这些工具把复杂任务拆成步骤，跟踪进度。
"""

from memory.task import create, get, list_active, format_task, update
from tools.registry import register


def task_create(title: str, items: list[str]) -> str:
    """创建一个新的任务列表。"""
    task_id = create(title, items)
    task = get(task_id)
    if task is None:
        return f"错误：任务 {task_id} 创建后无法读取"
    return f"已创建任务 [{task_id}]：\n{format_task(task)}"


def task_update(task_id: str, item_index: int, status: str) -> str:
    """更新任务步骤状态。"""
    return update(task_id, item_index, status)


def task_list() -> str:
    """查看当前活跃任务。"""
    tasks = list_active()
    if not tasks:
        return "没有活跃任务。"
    return "\n\n".join(
        f"[{t['id']}] {format_task(t)}" for t in tasks
    )


# ── 工具定义 ──

TASK_CREATE_DEF = {
    "type": "function",
    "function": {
        "name": "task_create",
        "description": (
            "创建一个任务列表，把复杂任务拆成步骤。"
            "每步一句话，3-7步为宜。返回 task_id 用于后续更新。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "任务名称"},
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "步骤列表，每项一句话描述",
                },
            },
            "required": ["title", "items"],
        },
    },
}

TASK_UPDATE_DEF = {
    "type": "function",
    "function": {
        "name": "task_update",
        "description": "更新任务中某一步的状态。status 可用：in_progress / completed / cancelled。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务ID（task_create 返回的）"},
                "item_index": {"type": "integer", "description": "步骤序号（从0开始）"},
                "status": {"type": "string", "description": "新状态：in_progress / completed / cancelled"},
            },
            "required": ["task_id", "item_index", "status"],
        },
    },
}

TASK_LIST_DEF = {
    "type": "function",
    "function": {
        "name": "task_list",
        "description": "查看所有活跃任务及进度。",
        "parameters": {"type": "object", "properties": {}},
    },
}

register("task_create", TASK_CREATE_DEF, task_create)
register("task_update", TASK_UPDATE_DEF, task_update)
register("task_list", TASK_LIST_DEF, task_list)
