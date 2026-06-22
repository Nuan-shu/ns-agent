"""NsAgent 入口 — 加载工具 → 启动 Agent。

用法：
  python main.py              # 交互 REPL
  python main.py --query "..." # 单次查询，非交互模式（子Agent用）
"""

import argparse

from core.agent import build_prompt, run
from core.logging import get_logger, new_trace_id, setup_logging

# ── 导入工具模块 = 触发 register() 报到 ──
import skills.finance  # noqa: F401
import tools.file_tools  # noqa: F401
import tools.finance.financial_report  # noqa: F401
import tools.finance.market_data  # noqa: F401
import tools.search_tool  # noqa: F401
import tools.subagent_tool  # noqa: F401
import tools.task_tool  # noqa: F401
import tools.terminal_tool  # noqa: F401
import tools.time_tool  # noqa: F401


SUBAGENT_PROMPT = """你是 NsAgent 子Agent。你被主 Agent 分配了一个独立任务。
规则：
1. 直接完成任务，返回结果。不要反问、不要确认、不要闲聊。
2. 用工具获取需要的信息，最后给出简洁的结论。
3. 如果无法完成，直接说明原因，不要猜测。"""


def single_query(query: str):
    """非交互模式：处理一次查询并输出结果。"""
    trace_id = new_trace_id()
    log = get_logger(trace_id=trace_id, module="subagent")
    setup_logging(dev_mode=False)  # 子Agent 用 JSON 日志避免污染输出

    messages = [{"role": "system", "content": SUBAGENT_PROMPT}]
    messages.append({"role": "user", "content": query})
    log.info("subagent.start", query=query[:100])
    run(messages=messages, log=log)
    log.info("subagent.end")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NsAgent — 统一 AI Agent 框架")
    parser.add_argument("--query", "-q", help="单次查询模式，直接返回结果（用于子Agent调用）")
    args = parser.parse_args()

    if args.query:
        single_query(args.query)
    else:
        from core.agent import chat
        chat()
