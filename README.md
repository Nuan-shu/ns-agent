# NsAgent

统一 AI Agent 框架 — 1 个 Agent + N 个工具集。本地运行的迷你版 Hermes。

[![Version](https://img.shields.io/badge/version-0.4.0-blue)](https://github.com/Nuan-shu/ns-agent/releases)
[![Files](https://img.shields.io/badge/files-30-green)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

## 架构

```
ns-agent/
├── main.py                         # 入口：REPL 或 --query 非交互模式
├── core/
│   ├── agent.py                    # Agent Loop（流式/非流式双模式）
│   ├── prompt.py                   # System Prompt 分层（身份/工具/规则/安全）
│   ├── context.py                  # Token 计数 + 上下文超限自动压缩
│   ├── logging.py                  # structlog 结构化日志 + traceId 追踪
│   ├── security.py                 # 危险命令拦截 + 路径沙箱
│   ├── fallback.py                 # 多模型优先级链（.env 配置）
│   ├── retry.py                    # API 指数退避重试（1s→2s→4s）
│   └── errors.py                   # NsAgentError 统一异常体系
├── tools/
│   ├── registry.py                 # 工具注册表（加工具只改这里，不改 loop）
│   ├── time_tool.py                # get_current_time
│   ├── file_tools.py               # read_file / write_file
│   ├── terminal_tool.py            # 终端命令执行（集成安全检查）
│   ├── search_tool.py              # 知识库搜索（三源统合）
│   ├── subagent_tool.py            # delegate_task — 子Agent 并行处理
│   ├── task_tool.py                # task_create/update/list — 任务追踪
│   └── finance/                    # 金融工具集
│       ├── market_data.py          # 实时行情查询（akshare）
│       └── financial_report.py     # 年报结构化报告（多指标并行搜索）
├── skills/
│   ├── registry.py                 # 技能注册表（注册/匹配/注入）
│   └── finance.py                  # 财报分析技能（关键词触发）
├── knowledge/
│   ├── search.py                   # 统一多源搜索（年报+Agent工程+Wiki=1972块）
│   └── ingest_wiki.py              # Wiki 入库（46篇→262块→ChromaDB）
├── memory/
│   ├── session.py                  # SQLite 会话持久化 + 24h 恢复
│   └── task.py                     # SQLite 任务存储（跨会话）
├── pyproject.toml                  # 依赖管理 + ruff/pytest 配置
├── CONVENTIONS.md                  # 编码规范
├── docs/                           # 设计文档
└── data/                           # 运行时数据（不入库）
```

## 核心设计

**工具注册表**：加新工具 = 新建一个文件 + 一行 `register()`。Agent Loop 不需要改。注册表是中心枢纽，Loop 只从注册表读，不关心工具具体有几个。

**统一多源搜索**：一个查询并行搜索 ChromaDB 三个知识库（年报 1683 块 + Agent工程 27 块 + Wiki 262 块 = 1972 块），bge-small-zh-v1.5 向量化。支持 `collections` 参数定向搜索。

**技能系统**：技能是注入 System Prompt 的知识模块。用户问题命中关键词时自动激活——工具负责调用函数，技能负责注入专业知识。加新技能不改 Agent Loop。

**System Prompt 分层**：身份/工具/规则/安全四层独立维护，`build_prompt()` 按需组装，支持技能内容动态注入。

**结构化日志**：structlog 替代裸 print。每个会话一条 traceId 贯穿所有操作。REPL 模式彩色输出，子Agent 模式 JSON 输出到 stderr（不污染主输出流）。

**危险命令审批**：16 条正则拦截 rm -rf/sudo/chmod 777/curl|bash 等危险操作。路径沙箱限制文件访问范围。拦截直接返回原因，不打断 Agent Loop 自动流程。

**子 Agent 并行**：`delegate_task` 工具通过 terminal 调 `python main.py --query` 生成子进程，独立处理子任务。子Agent 用精简 Prompt + JSON 日志 + Fallback 链。

**流式输出**：`_stream_response()` 逐 token 打印 LLM 回复。工具调用 delta 累积拼接后一次性执行。非流式模式（子Agent）用 call_with_fallback。

**任务系统**：Agent 用 task_create/update/list 拆分复杂任务、追踪每步进度。SQLite 存储，跨会话存在。

**多模型 Fallback**：按优先级尝试模型链，任一成功即返回。默认 DeepSeek，在 `.env` 设 `FALLBACK_MODELS` JSON 即可扩展。

**上下文压缩**：Token 计数 + 超限自动压缩。对话超过 4000 tokens 时将中间消息总结为摘要，防止长对话撑爆 LLM 上下文窗口。

**会话持久化**：每次对话自动落 SQLite。重启时 24h 内自动恢复。`/new` 开始新会话，`/exit` 输出 session_id。

**API 重试**：DeepSeek API 调用内置指数退避重试（3 次，1s→2s→4s）。

**统一异常**：NsAgentError → APIError / ToolError / ConfigError，支持错误码和 `to_dict()` 序列化。

## 运行

```bash
cd ns-agent
pip install -e .
python main.py              # 交互 REPL
python main.py --query "问题"  # 非交互模式（子Agent 用）
```

启动后自动恢复 24h 内会话，输入问题即可交互。

```
NsAgent v0.4.0 — 输入 /exit 退出

你: 比亚迪2024年营收利润分析
[NsAgent] 已加载 10 个工具
>>> 流式输出逐 token 打印...
```

命令：

| 命令 | 作用 |
|------|------|
| `/exit` | 退出（输出 session_id） |
| `/new`  | 开始全新会话 |

依赖：`openai` `chromadb` `sentence-transformers` `python-dotenv` `akshare` `structlog`

环境变量（`.env`）：`DEEPSEEK_API_KEY=sk-xxx`

可选：`FALLBACK_MODELS='[{"model":"...","base_url":"...","api_key":"..."}]'`

## 版本历史

| 版本 | 日期 | 内容 | 增量 |
|------|------|------|------|
| **v0.4.0** | 06-22 | 企业级特性：结构化日志 + 安全审批 + 子Agent + 流式输出 + 任务系统 + Fallback链 | +6 文件 |
| v0.3.0 | 06-16 | 金融工具集 + 技能系统 + Prompt分层 + 上下文压缩 + 基础设施规范化 | +11 文件 |
| v0.2.0 | 06-12 | 三源统合 + 会话持久化 + API重试 | +4 文件 |
| v0.1.0 | 06-11 | 框架筑基：工具注册表 + 多源搜索 + Agent Loop | 9 文件 |

完整架构可视化见 [NsAgent-graph.html](NsAgent-graph.html)（浏览器打开，支持版本切换）。

## 路线图

- [x] v0.1.0 — 框架筑基：工具注册表 + 多源搜索 + Agent Loop
- [x] v0.2.0 — 三源统合 + 会话持久化 + API 重试
- [x] v0.3.0 — 金融工具集 + 技能系统 + Prompt 分层 + 上下文压缩
- [x] v0.4.0 — 企业级特性：安全审批 + 子Agent + 流式输出 + 任务系统 + Fallback链
- [ ] v0.5.0 — 月3 产品化

## 关联项目

- [agent-framework](https://github.com/Nuan-shu/agent-framework) — Agent Loop 原型（v1→v2→v3）
- rag-project — 金融 RAG 问答系统（年报知识库，ChromaDB 三集合）
