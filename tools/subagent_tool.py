"""子 Agent 工具 — 通过 terminal 调自身处理子任务。"""

from tools.registry import register


def delegate_task(goal: str, context: str = "") -> str:
    """生成一个子 NsAgent 处理独立任务，返回其结果。

    通过 terminal 调 python main.py --query 实现。
    子Agent 有独立的 30 秒超时。
    """
    import subprocess
    import os

    # 拼接查询：context 作为背景，goal 是具体任务
    query = goal
    if context:
        query = f"{context}\\n\\n任务：{goal}"

    # 转义引号防止 shell 注入
    safe_query = query.replace("'", "'\\''")

    cmd = (
        f"cd {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))} && "
        f".venv/bin/python3 main.py --query '{safe_query}'"
    )

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        output = result.stdout.strip()
        if result.stderr:
            # 过滤掉 bge 模型加载的进度条
            stderr_clean = "\\n".join(
                line for line in result.stderr.split("\\n")
                if "Loading weights" not in line and "it/s" not in line
            )
            if stderr_clean.strip():
                output += f"\\n[子Agent stderr]\\n{stderr_clean.strip()}"
        return output or f"子Agent 无输出（退出码 {result.returncode}）"
    except subprocess.TimeoutExpired:
        return "错误：子Agent 超时（>60秒）"
    except Exception as e:
        return f"子Agent 错误：{e}"


SUBAGENT_DEF = {
    "type": "function",
    "function": {
        "name": "delegate_task",
        "description": (
            "生成一个子 NsAgent 处理独立的子任务。子Agent 有自己的工具和上下文。"
            "适合需要独立分析、多步骤搜索或复杂计算的场景。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "子Agent 要完成的具体任务。直接描述要什么结果，不要加指令性废话。",
                },
                "context": {
                    "type": "string",
                    "description": "子Agent 需要的背景信息（可选）。给子Agent 提供必要的数据或上下文。",
                },
            },
            "required": ["goal"],
        },
    },
}

register("delegate_task", SUBAGENT_DEF, delegate_task)
