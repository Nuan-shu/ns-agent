"""知识库搜索工具 — 调用 knowledge.search 统一搜索。"""

from knowledge.search import search_formatted
from tools.registry import register


def search_knowledge(query):
    """搜索知识库(年报 + Agent文档 + Wiki)，返回格式化结果。"""
    return search_formatted(query)


SEARCH_DEF = {
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": "搜索本地知识库，包括年报、Agent工程文档等。用来查找事实、数据、技术方案。",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词或问题"}},
            "required": ["query"],
        },
    },
}

register("search_knowledge", SEARCH_DEF, search_knowledge)
