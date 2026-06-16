"""文件读写工具 — read_file 和 write_file。"""

from pathlib import Path

from tools.registry import register


def read_file(path, offset=1, limit=200):
    """读取文件内容。offset 和 limit 控制读取范围。"""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"错误：文件不存在 {path}"
    try:
        lines = p.read_text(encoding="utf-8").split("\n")
        total = len(lines)
        start = max(0, offset - 1)
        end = min(total, start + limit)
        result = []
        for i in range(start, end):
            result.append(f"{i + 1}|{lines[i]}")
        header = f"文件 {path}（第 {start + 1}-{end} 行 / 共 {total} 行）\n"
        return header + "\n".join(result)
    except Exception as e:
        return f"错误：读取失败 {e}"


def write_file(path, content):
    """写入文件内容（覆盖）。"""
    p = Path(path).expanduser().resolve()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"已写入 {path}（{len(content)} 字符）"
    except Exception as e:
        return f"错误：写入失败 {e}"


READ_DEF = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "读取文件内容，返回带行号的文本",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "offset": {"type": "integer", "description": "起始行号（默认1）"},
                "limit": {"type": "integer", "description": "读取行数（默认200）"},
            },
            "required": ["path"],
        },
    },
}

WRITE_DEF = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "写入文件内容（覆盖模式）",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的内容"},
            },
            "required": ["path", "content"],
        },
    },
}

register("read_file", READ_DEF, read_file)
register("write_file", WRITE_DEF, write_file)
