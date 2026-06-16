"""上下文压缩 — Token 计数 + 超限自动总结。"""

import json


def count_tokens(text: str) -> int:
    """粗略估算 token 数。

    中文约 2 字符/token，英文约 4 字符/token。
    用于判断是否触发压缩，不要求精确。
    """
    chinese = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other = len(text) - chinese
    return chinese // 2 + other // 4


def count_messages_tokens(messages: list[dict]) -> int:
    """估算消息列表的总 token 数。"""
    total = 0
    for msg in messages:
        content = msg.get("content") or ""
        if isinstance(content, str):
            total += count_tokens(content)
        if msg.get("tool_calls"):
            total += count_tokens(json.dumps(msg["tool_calls"], ensure_ascii=False))
    return total


def compress(
    messages: list[dict],
    max_tokens: int = 4000,
    keep_last: int = 6,
) -> tuple[list[dict], str | None]:
    """超过 max_tokens 时，压缩中间消息为摘要。

    策略：
    1. 保留 system 消息（第 0 条）
    2. 保留最后 keep_last 条消息
    3. 中间部分生成一段摘要，替换为一条 user 消息

    返回：(压缩后的消息列表, 摘要文本或 None)
    """
    total = count_messages_tokens(messages)
    if total <= max_tokens or len(messages) <= keep_last + 2:
        return messages, None

    # 中间部分：从 system 之后到倒数 keep_last 之前
    middle = messages[1:-keep_last]
    middle_text = _format_for_summary(middle)
    summary = f"[上下文摘要] 以下为之前对话的关键信息：\n{middle_text[:2000]}"

    # 重建消息列表
    compressed = [
        messages[0],  # system
        {"role": "user", "content": summary},
        *messages[-keep_last:],
    ]
    return compressed, summary


def _format_for_summary(messages: list[dict]) -> str:
    """将消息列表格式化为可总结的文本。"""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content") or ""
        if isinstance(content, str) and content.strip():
            # 截断过长内容
            short = content[:500] + "..." if len(content) > 500 else content
            lines.append(f"[{role}] {short}")
    return "\n".join(lines)
