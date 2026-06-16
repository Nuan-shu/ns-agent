# NsAgent 企业级开发规范化报告

> 2026-06-16 · 对照 ns-agent v0.3.0 现状，逐项分析差距与行动方案。

---

## 总览

企业级开发不是「大公司才做的事」，而是一套**让代码不腐烂**的工程实践。ns-agent 当前在 8 个维度存在差距：

| 维度 | ns-agent 现状 | 企业级标准 | 严重程度 |
|------|-------------|-----------|---------|
| 测试 | 无 | 单元+集成+CI | 高 |
| 类型注解 | 无 | 全覆盖 + mypy | 高 |
| 依赖管理 | 无文件记录 | pyproject.toml + lock | **已修复** |
| 代码检查 | 无 | ruff + pre-commit | **已修复** |
| 日志 | print() | structlog 结构化 | 中 |
| CI/CD | 无 | GitHub Actions | 中 |
| 错误处理 | 基础 try/except | 分层异常 + 错误码 | 中 |
| 项目结构 | 代码测试混放 | src/tests 分离 | 低 |

---

## 1. 测试 — 防屎山第一道防线

### 为什么最重要

没有测试 = 每次改代码都在赌。你今天改了 `registry.py` 的 `execute()` 函数，你**确信** 7 个工具都还能正常调用吗？你能做的是手动跑一遍——一次、两次可以，第 20 次呢？

测试的价值不是「证明代码正确」，而是**当代码被改坏时，第一时间告诉你**。

### 现状

```
ns-agent 测试覆盖: 0%
└── 测试文件: 0 个
└── 测试框架: 未安装
└── 验证方式: python -c "..." 手动
```

### 企业级做法

```
测试金字塔:
     ┌──────────┐
     │  E2E 测试 │  ← 少而精（启动 Agent，对话一轮）
     ├──────────┤
     │ 集成测试   │  ← 搜年报 → LLM 生成回答（不走真 API）
     ├──────────┤
     │ 单元测试   │  ← 每个函数独立测（占 70%）
     └──────────┘
```

**单元测试示例**（ns-agent 场景）：

```python
# tests/test_registry.py
from tools.registry import register, execute, get_tool_definitions

def test_register_and_execute():
    def hello(name):
        return f"你好 {name}"

    register("hello", {"type": "function", "function": {"name": "hello", ...}}, hello)
    result = execute("hello", {"name": "世界"})
    assert result == "你好 世界"

def test_execute_unknown_tool():
    result = execute("不存在的工具", {})
    assert "未知工具" in result
```

```python
# tests/test_search.py
from knowledge.search import unified_search

def test_search_annual_reports():
    results = unified_search("茅台 营业收入", top_k=3)
    assert len(results) > 0
    assert all(r["source"] in ("annual_reports", "agent_engineering", "wiki_knowledge") for r in results)
```

### 行动方案

1. 安装：`pip install pytest pytest-cov`
2. 创建 `tests/` 目录
3. 先测 3 个核心函数：`execute()`、`unified_search()`、`call_with_retry()`
4. 以后每加一个新工具，同时加它的测试
5. 覆盖率目标：先到 50%，月 3 到 80%

---

## 2. 类型注解 — 第二道防线

### 为什么重要

```python
# 没有类型注解：你不知道 args 是什么
def execute(name, args):
    ...

# 有类型注解：一目了然
def execute(name: str, args: dict[str, str]) -> str:
    ...
```

类型注解做三件事：
1. **IDE 自动补全** — 输入 `result.` 时弹出可用方法
2. **静态检查** — mypy 在你运行前就发现 `execute(123, None)` 这样的错误
3. **活文档** — 不需要翻源码就知道参数格式

### 现状

```
ns-agent 类型注解覆盖: 0%
└── 17 个 .py 文件，0 个函数有类型注解
```

### 企业级做法

```python
# 完整注解示例（ns-agent 风格）
from typing import Any

def execute(name: str, args: dict[str, Any]) -> str:
    """根据工具名执行对应函数。"""
    if name not in _registry:
        return f"错误：未知工具 {name}"
    return _registry[name]["handler"](**args)

def register(
    name: str,
    definition: dict[str, Any],
    handler: callable
) -> None:
    """注册一个工具。"""
    _registry[name] = {"definition": definition, "handler": handler}
```

### 行动方案

1. 从新文件开始强制要求
2. 逐步给核心模块补（`registry.py` → `agent.py` → `search.py`）
3. 安装 `mypy` 作为 CI 检查项
4. 不用追求 100%，核心公开接口有就行

---

## 3. 依赖管理 — 已修复

### 做了什么

创建 `pyproject.toml`，记录了所有直接依赖：

```toml
[project]
name = "ns-agent"
version = "0.3.0"
requires-python = ">=3.12"

dependencies = [
    "openai>=2.0",
    "python-dotenv>=1.0",
    "chromadb>=1.5",
    "sentence-transformers>=5.0",
    "akshare>=1.18",
]
```

### 为什么重要

- 换机器只需 `pip install -e .` 一键恢复
- `pyproject.toml` 是现代 Python 项目的标准入口
- 区分了 `dependencies`（运行时）和 `[dev]`（开发时，如 ruff/pytest）

---

## 4. 代码检查 — 已修复

### 做了什么

安装 `ruff`，配置了 7 类检查规则，自动修复了 26 个问题。

### 规则说明

| 规则 | 用途 | 示例 |
|------|------|------|
| `E/W` | pycodestyle 格式 | 空行尾随空格 |
| `F` | pyflakes 逻辑错误 | 定义了变量但没用 |
| `I` | isort 导入排序 | stdlib → 第三方 → 项目内 |
| `N` | pep8-naming 命名 | 类名应用 PascalCase |
| `UP` | pyupgrade 语法升级 | `f"{x}"` 替代 `"{}".format(x)` |
| `B` | flake8-bugbear 常见 bug | `zip()` 不加 `strict=` |
| `SIM` | 简化代码 | `if a: return True; return False` → `return bool(a)` |

### 执行结果

```
ruff check .  → 28 问题 → 自动修复 26 个 → 手动修 2 个 → 全部通过
ruff format . → 14 文件重新格式化
```

### 下一步：pre-commit 钩子

```bash
pip install pre-commit
# 创建 .pre-commit-config.yaml，提交前自动跑 ruff + mypy
```

效果：代码不通过检查**根本提交不了**，从源头堵住屎山。

---

## 5. 日志 — 从 print() 到 structlog

### 现状

```python
# core/agent.py — 混在一起的 print
print(f"[NsAgent] 已加载 {len(tools)} 个工具\n")     # 这是什么级别？info？
print(f"  [重试 {attempt}/{MAX_RETRIES}] ...")        # 这是 warn？
print(f"NsAgent 错误 [{e.code}]: {e.message}")        # 这是 error？
```

问题：无法区分调试信息、正常日志、警告和错误。排查问题时只能全文搜索。

### 企业级做法

```python
import structlog

logger = structlog.get_logger()

# 使用
logger.info("工具已加载", tool_count=len(tools))
logger.warning("API 重试", attempt=attempt, max_retries=MAX_RETRIES)
logger.error("工具执行失败", tool_name=name, error=str(e))
```

输出带时间戳和结构化字段：

```
2026-06-16 10:30:00 [info] 工具已加载 tool_count=7
2026-06-16 10:30:05 [warning] API 重试 attempt=2 max_retries=3
```

### 为什么不用 print()

1. **级别过滤** — 生产环境只看 error，开发环境看 debug
2. **结构化** — `tool_count=7` 可被日志系统搜索聚合
3. **trace_id** — 一次请求贯串所有日志，定位问题秒级

### 行动方案

1. 安装 `pip install structlog`
2. 替换 `agent.py` + `retry.py` 的 `print()`
3. 定义日志级别：debug（开发）/ info（正常）/ warning（重试）/ error（失败）

---

## 6. CI/CD — 自动化门禁

### 现状

```
git push → 人工检查 → 可能漏
```

### 企业级做法

```
git push → GitHub Actions:
  ├── ruff check（格式检查，不过直接拒绝）
  ├── mypy（类型检查）
  ├── pytest（跑所有测试）
  └── 三项全过 → 允许合并
```

### GitHub Actions 配置示例

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: pytest --cov
```

### 为什么 CI 防屎山

- **阻止坏代码入库** — 不跑 CI 不合并，坏代码连仓库都进不去
- **历史可追溯** — 每次提交都有绿灯/红灯记录，谁引入的 bug 一查便知
- **减少 review 负担** — 格式问题机器检查，人只关注逻辑

---

## 7. 错误处理 — 分层防御

### 现状

ns-agent 有 `NsAgentError` 体系但只用了一小部分：

```
NsAgentError               ← 定义了但只用基类
├── APIError               ← 定义了但 retry.py 还在裸 raise
├── ToolError              ← 定义了但工具层返回字符串而非抛异常
└── ConfigError            ← 未使用
```

### 企业级做法

```
三层防御:

第 1 层 — 工具层：抛 ToolError
  def get_stock_price(code):
      try:
          ...
      except akshare.NetworkError as e:
          raise ToolError(f"行情查询网络失败: {e}", code="FINANCE_NETWORK")

第 2 层 — Agent Loop：捕获 NsAgentError → 友好输出
  try:
      run(messages=messages)
  except NsAgentError as e:
      print(f"[{e.code}] {e.message}")  # 不崩，继续运行

第 3 层 — 入口：捕获所有 Exception → 记录 + 优雅退出
  try:
      chat()
  except Exception as e:
      logger.critical("未预期崩溃", error=str(e))
```

### 为什么这样设计

- **工具层不该直接返回字符串** — 上游不知道这是正常结果还是出错
- **Agent Loop 不该崩** — 一个工具失败，换另一个工具重试
- **入口层必须兜底** — 真的崩了也要留下日志

---

## 8. 项目结构 — 代码与测试分离

### 现状

```
ns-agent/
├── main.py
├── core/          ← 生产代码
├── tools/         ← 生产代码
├── knowledge/     ← 生产代码
├── memory/        ← 生产代码
├── data/          ← 运行时数据
└── CONVENTIONS.md ← 规范文档
```

### 企业级做法

```
ns-agent/
├── src/
│   └── ns_agent/          ← 所有生产代码
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       ├── tools/
│       ├── knowledge/
│       └── memory/
├── tests/                 ← 测试代码（镜像 src 结构）
│   ├── test_registry.py
│   ├── test_search.py
│   └── tools/
│       └── test_market_data.py
├── config/                ← 环境配置（dev/staging/prod）
├── docs/                  ← 设计文档、ADR
├── pyproject.toml
├── CONVENTIONS.md
└── README.md
```

### 为什么分离

- `src/` 布局避免 Python 路径陷阱（`import ns_agent` 而非 `import core`）
- `tests/` 镜像结构让测试文件秒找
- `config/` 环境分离：dev 连本地 ChromaDB，prod 连远程

### 行动方案

这个不用现在做——目录迁移影响所有 import。等月 3 产品化时一并重构。

---

## 防屎山核心原则

### 1. 让机器检查，别靠人脑记

```
CONVENTIONS.md → 人看，人会忘
ruff + mypy    → 机器执行，机器不忘
```

### 2. 改代码必改测试

每加一个工具，同时加它的测试。测试不是负担——它是唯一能告诉你「改坏了」的东西。

### 3. 接口稳定，实现可变

```python
# 工具都走同一个注册接口
register("name", DEF, handler)

# Agent Loop 不看具体工具，只看注册表
tools = get_tool_definitions()
```

好处：加 10 个工具，Agent Loop 一行不用改。

### 4. 分层隔离

```
入口层 → 不关心工具细节，只调 Agent Loop
Loop 层 → 不关心搜索细节，只调 execute()
工具层 → 不关心 ChromaDB 细节，只调 unified_search()
搜索层 → 唯一真相源，换模型只改这里
```

每层只知道自己下面一层，不看隔壁层。

### 5. 三不原则

- **不信任输入** — 工具函数永远校验参数
- **不吞异常** — `except Exception: pass` 是屎山之源
- **不硬编码** — 路径、密钥、阈值全部从配置读

---

## 实施路线图

```
已做（Day 10）:
  [x] pyproject.toml — 依赖声明
  [x] ruff — 代码检查 + 自动格式化
  [x] CONVENTIONS.md — 编码规范

本周（Week 4）:
  [ ] pytest — 3 个核心函数单元测试
  [ ] 新文件加类型注解
  [ ] pre-commit 钩子（提交前自动 ruff）

下周（Week 5）:
  [ ] mypy — 类型检查
  [ ] GitHub Actions CI（push 自动跑 lint + test）
  [ ] structlog 替换 print()

月 3（产品化）:
  [ ] src/tests 目录分离
  [ ] 测试覆盖率 > 80%
  [ ] 错误码体系完善
  [ ] 日志 + 指标 + 告警
```
