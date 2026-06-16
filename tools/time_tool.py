"""获取当前时间的工具。"""

from datetime import datetime

from tools.registry import register


def get_current_time():
    """返回当前日期时间字符串。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取当前日期和时间",
        "parameters": {"type": "object", "properties": {}},
    },
}

register("get_current_time", TOOL_DEFINITION, get_current_time)
