"""技能注册表 — 知识模块的注册、匹配、注入。

工具 = LLM 调用的函数（function calling）
技能 = 注入 System Prompt 的知识模块（关键词触发）
"""

from typing import Any

_skills: dict[str, dict[str, Any]] = {}


def register_skill(name: str, trigger: str, description: str, content: str) -> None:
    """注册一个技能。

    name: 技能名（唯一标识）
    trigger: 触发关键词（匹配用户输入）
    description: 一句话描述（给开发者看的）
    content: 注入到 System Prompt 的知识内容
    """
    _skills[name] = {
        "trigger": trigger,
        "description": description,
        "content": content,
    }


def match_skills(user_input: str) -> list[dict[str, Any]]:
    """根据用户输入匹配已注册的技能。

    匹配规则：trigger 中的任一关键词出现在用户输入中（不区分大小写）。
    trigger 可用 `|` 分隔多个关键词。
    """
    matched = []
    user_lower = user_input.lower()
    for _name, skill in _skills.items():
        keywords = skill["trigger"].split("|")
        if any(kw.strip().lower() in user_lower for kw in keywords):
            matched.append(skill)
    return matched


def inject_skills(
    messages: list[dict[str, Any]], matched: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """将匹配到的技能内容注入 System Prompt。

    在第一条 system 消息末尾追加技能内容。
    """
    if not matched:
        return messages

    skill_text = "\n\n".join(f"## {s['description']}\n{s['content']}" for s in matched)
    messages[0]["content"] += f"\n\n---\n## 已激活的知识模块\n{skill_text}"
    return messages


def list_skills() -> list[dict[str, str]]:
    """列出所有已注册的技能（名称 + 描述）。"""
    return [{"name": name, "description": s["description"]} for name, s in _skills.items()]
