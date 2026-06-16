"""工具注册表 — 所有工具在这里报到。加新工具不改 Agent Loop。"""

_registry = {}  # {工具名: {"definition": {...}, "handler": 函数}}


# 调用工具时,会自动来这报道.在tools里调用该函数
def register(name, definition, handler):
    """注册一个工具。definition 是给 LLM 看的 JSON Schema。"""
    _registry[name] = {"definition": definition, "handler": handler}


# 让LLM知道有哪些工具(main函数开具就调用了工具,所以可以直接让LLM知悉)
def get_tool_definitions():
    """返回所有工具的 definition 列表（给 LLM 的 tools 参数）。"""
    return [item["definition"] for item in _registry.values()]


# 执行工具
def execute(name, args):
    """根据工具名执行对应函数。"""
    if name not in _registry:
        return f"错误：未知工具 {name}"
    return _registry[name]["handler"](**args)


"""
示例
     _registry = {
         "read_file":   {"definition": {...给LLM看的JSON...}, "handler": <read_file函数>},
         "write_file":  {"definition": {...}, "handler": <write_file函数>},
         "terminal":    {"definition": {...}, "handler": <run_command函数>},
         ...
     }

 Agent Loop 只需要知道 get_tool_definitions() 和 execute() 两个入口，不关心注册表里有什么。

"""
