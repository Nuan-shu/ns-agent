"""NsAgent 入口 — 加载工具 → 启动 Agent。"""
# 导入工具模块 = 触发 register() 报到
import tools.time_tool      # noqa: F401
import tools.file_tools     # noqa: F401
import tools.terminal_tool  # noqa: F401
import tools.search_tool    # noqa: F401

from core.agent import chat

if __name__ == "__main__":
    chat()
