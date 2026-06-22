"""NsAgent 结构化日志 — structlog + traceId。

替换裸 print()，为每个会话生成唯一的 trace_id。
开发环境用彩色 ConsoleRenderer，生产环境可切 JSONRenderer。
"""

import sys
import structlog
import uuid


def setup_logging(dev_mode: bool = True):
    """配置 structlog 全局参数。

    dev_mode=True: 彩色终端输出（stdout），适合本地开发。
    dev_mode=False: JSON 输出到 stderr，不污染主输出流（子Agent 模式用）。
    """
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if dev_mode:
        processors.append(structlog.dev.ConsoleRenderer())
        log_stream = sys.stdout
    else:
        processors.append(structlog.processors.JSONRenderer())
        log_stream = sys.stderr

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_stream),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def new_trace_id() -> str:
    """生成 8 位短 trace_id，用于追踪单次会话的所有日志。"""
    return uuid.uuid4().hex[:8]


def get_logger(**ctx) -> structlog.stdlib.BoundLogger:
    """获取绑定上下文的 logger。每次调用可追加新字段。

    用法：
        log = get_logger(trace_id="abc123", module="agent")
        log.info("nsagent.start", session_id="xxx")
    """
    return structlog.get_logger(**ctx)
