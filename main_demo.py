"""NsAgent Demo — 精简版入口，只用核心工具"""
import argparse
from core.agent import run
from core.logging import get_logger, new_trace_id, setup_logging

# 只导入轻量工具（不加载 akshare 金融工具）
import tools.time_tool    # noqa: F401
import tools.file_tools   # noqa: F401
import tools.search_tool  # noqa: F401
import tools.task_tool    # noqa: F401

from dotenv import load_dotenv

load_dotenv()

PROMPT = """你是 NsAgent Demo。回答用户问题，可以用工具获取信息。
知识库包含 A 股年报数据（茅台/比亚迪/宁德时代 2025 年报）。
规则：简洁回答，信息来源注明出处。"""


def single_query(query: str):
    trace_id = new_trace_id()
    log = get_logger(trace_id=trace_id, module="demo")
    setup_logging(dev_mode=False)
    msgs = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": query},
    ]
    run(messages=msgs, log=log, stream=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--query", "-q")
    args = p.parse_args()
    if args.query:
        single_query(args.query)
