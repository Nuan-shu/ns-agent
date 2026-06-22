"""NsAgent 安全模块 — 危险命令拦截 + 沙箱路径限制。

不搞交互式审批（那会打断 Agent Loop 自动流程）。
危险命令直接拒绝，返回拦截原因。
"""

import os
import re

# ── 危险命令模式 ──

DANGEROUS_PATTERNS = [
    (r"\brm\s+(-[rRf]+\s+)+[/~]", "递归强制删除文件/目录"),
    (r"\bsudo\b", "提权操作"),
    (r"\bchmod\s+777", "开放所有权限"),
    (r"\bchmod\s+[0-7]*7\b", "开放执行权限"),
    (r"\bchown\b", "修改文件所有权"),
    (r"\bmkfs\b", "格式化磁盘"),
    (r"\bdd\s+if=", "磁盘直接写入"),
    (r">\s*/dev/", "写入设备文件"),
    (r"\bcurl.*\|.*(ba)?sh", "远程下载并执行脚本"),
    (r"\bwget.*\|.*(ba)?sh", "远程下载并执行脚本"),
    (r"\bgit\s+clone.*\|.*sh", "克隆仓库后直接执行"),
    (r"\bkill\s+-9", "强制终止进程"),
    (r"\breboot\b", "重启系统"),
    (r"\bshutdown\b", "关机"),
    (r"\b:\(\)\s*{\s*:\|:&\s*}\s*;\s*:", "Fork 炸弹（拒绝服务）"),
    (r"\.\./\.\./\.\./", "多级目录穿越（可疑）"),
]

# ── 沙箱路径 ──

ALLOWED_ROOTS = [
    os.path.expanduser("~/Projects"),
    os.path.expanduser("~/Wiki"),
    os.path.expanduser("~/Documents"),
    "/tmp",
    "/var/tmp",
]


def check_command(command: str) -> tuple[bool, str]:
    """检查命令是否包含危险操作。

    Returns:
        (safe, reason): safe=False 表示被安全策略拦截，reason 说明原因。
    """
    for pattern, desc in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return False, f"安全策略拦截：{desc}。如需执行，请在终端手动操作。"
    return True, ""


def check_path(path: str) -> bool:
    """检查路径是否在沙箱允许范围内。

    用于限制文件读写的有效范围，防止越权访问敏感目录。
    """
    abs_path = os.path.abspath(os.path.expanduser(path))
    for root in ALLOWED_ROOTS:
        root_abs = os.path.abspath(root)
        if abs_path.startswith(root_abs):
            return True
    return False
