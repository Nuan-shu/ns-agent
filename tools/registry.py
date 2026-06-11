"""工具注册表 — 所有工具在这里报到。加新工具不改 Agent Loop。"""

_registry = {}  # {工具名: {"definition": {...}, "handler": 函数}}


def register(name, definition, handler):
    """注册一个工具。definition 是给 LLM 看的 JSON Schema。"""
    _registry[name] = {"definition": definition, "handler": handler}


def get_tool_definitions():
    """返回所有工具的 definition 列表（给 LLM 的 tools 参数）。"""
    return [item["definition"] for item in _registry.values()]


def execute(name, args):
    """根据工具名执行对应函数。"""
    if name not in _registry:
        return f"错误：未知工具 {name}"
    return _registry[name]["handler"](**args)
