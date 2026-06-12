"""NsAgent 统一异常体系。"""


class NsAgentError(Exception):
    """NsAgent 异常基类。"""
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code        # 机器可读的错误码
        self.details = details  # 额外上下文（dict）
        super().__init__(message)

    def to_dict(self):
        d = {"error": self.message}
        if self.code:
            d["code"] = self.code
        if self.details:
            d["details"] = self.details
        return d


class APIError(NsAgentError):
    """API 调用失败（网络、限流、服务端错误）。"""


class ToolError(NsAgentError):
    """工具执行失败（文件不存在、命令超时等）。"""


class ConfigError(NsAgentError):
    """配置错误（缺少 API Key 等）。"""
