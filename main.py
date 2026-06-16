"""NsAgent 入口 — 加载工具 → 启动 Agent。"""

# 导入工具模块 = 触发 register() 报到
from core.agent import chat
import skills.finance  # noqa: F401
import tools.file_tools  # noqa: F401
import tools.finance.financial_report  # noqa: F401
import tools.finance.market_data  # noqa: F401
import tools.search_tool  # noqa: F401
import tools.terminal_tool  # noqa: F401
import tools.time_tool  # noqa: F401

if __name__ == "__main__":
    chat()
