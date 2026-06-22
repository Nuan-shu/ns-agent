"""终端命令执行工具 — 带安全审批。"""

import subprocess

from core.security import check_command
from tools.registry import register


def run_command(command, timeout=30):
    """执行 shell 命令并返回输出。危险命令自动拦截。"""
    # ── 安全检查 ──
    safe, reason = check_command(command)
    if not safe:
        return f"[拦截] {reason}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        return output or f"命令执行完毕（退出码 {result.returncode}）"
    except subprocess.TimeoutExpired:
        return f"错误：命令超时（>{timeout}秒）"
    except Exception as e:
        return f"错误：{e}"


TERMINAL_DEF = {
    "type": "function",
    "function": {
        "name": "terminal",
        "description": "在终端执行 shell 命令并返回输出。危险命令（rm -rf/sudo/chmod 777等）会被自动拦截。",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"},
                "timeout": {"type": "integer", "description": "超时秒数（默认30）"},
            },
            "required": ["command"],
        },
    },
}

register("terminal", TERMINAL_DEF, run_command)
