# NsAgent

统一 AI Agent 框架 — 1 个 Agent + N 个工具集。本地运行的迷你版 Hermes。

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](https://github.com/Nuan-shu/ns-agent/releases)
[![Files](https://img.shields.io/badge/files-12-green)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

## 架构

```
ns-agent/
├── main.py                    # 入口：加载工具 → 启动 REPL
├── core/
│   ├── agent.py               # Agent Loop（while True → LLM → 工具调用）
│   ├── retry.py               # API 指数退避重试（1s→2s→4s）
│   └── errors.py              # NsAgentError 统一异常体系
├── tools/
│   ├── registry.py            # 工具注册表（加工具只改这里，不改 loop）
│   ├── time_tool.py           # get_current_time
│   ├── file_tools.py          # read_file / write_file
│   ├── terminal_tool.py       # 终端命令执行
│   └── search_tool.py         # 知识库搜索（三源统合）
├── knowledge/
│   ├── search.py              # 统一多源搜索（年报 + Agent工程 + Wiki = 1972 块）
│   └── ingest_wiki.py         # Wiki 入库（46 篇 → 262 块 → ChromaDB）
├── memory/
│   └── session.py             # SQLite 会话持久化 + 24h 自动恢复
├── data/                      # 运行时数据（sessions.db，不入库）
└── NsAgent-graph.html         # 交互式架构网络图（版本切换 + 节点角标）
```

## 核心设计

**工具注册表**：加新工具 = 新建一个文件 + 一行 `register()`。Agent Loop 不需要改。注册表是中心枢纽，Loop 只从注册表读，不关心工具具体有几个。

**统一多源搜索**：一个查询并行搜索 ChromaDB 三个知识库（年报 1683 块 + Agent工程 27 块 + Wiki 262 块 = 1972 块），bge-small-zh-v1.5 向量化，按 cosine 距离合并排序。

**会话持久化**：每次对话自动落 SQLite。重启时 24h 内自动恢复上次会话。`/new` 开始新会话，`/exit` 输出 session_id。

**API 重试**：DeepSeek API 调用内置指数退避重试（3 次，1s→2s→4s），只重试可恢复错误（网络/限流/5xx），400/401 直接抛出。

**统一异常**：NsAgentError → APIError / ToolError / ConfigError，支持错误码和 `to_dict()` 序列化。

## 运行

```bash
cd ns-agent
python main.py
```

启动后自动恢复 24h 内会话，输入问题即可交互。

```
NsAgent v0.2.0 — 输入 /exit 退出

你: 茅台2025年营收是多少？
[NsAgent] 已加载 5 个工具
>>> 发送请求（2 条消息）...
🔧 search_knowledge({"query": "茅台2025年营收"})

2025年茅台营收约1,687.75亿元，同比下降1.08%。
```

命令：

| 命令 | 作用 |
|------|------|
| `/exit` | 退出（输出 session_id） |
| `/new`  | 开始全新会话 |

依赖：`openai` `chromadb` `sentence-transformers` `python-dotenv`

环境变量（`.env`）：`DEEPSEEK_API_KEY=sk-xxx`

## 版本历史

| 版本 | 日期 | 内容 | 增量 |
|------|------|------|------|
| **v0.2.0** | 06-12 | 三源统合 + 会话持久化 + API重试 | +4 文件 +9 函数 |
| v0.1.0 | 06-11 | 框架筑基：工具注册表 + 多源搜索 + Agent Loop | 9 文件 12 函数 |

完整架构可视化见 [NsAgent-graph.html](NsAgent-graph.html)（浏览器打开，支持版本切换）。

## 路线图

- [x] v0.1.0 — 框架筑基：工具注册表 + 多源搜索 + Agent Loop
- [x] v0.2.0 — 三源统合 + 会话持久化 + API 重试
- [ ] v0.3.0 — 金融工具集（行情/筛选/报告）
- [ ] v0.4.0 — 企业级特性（安全审批 + 子 Agent + 流式输出）

## 关联项目

- [agent-framework](https://github.com/Nuan-shu/agent-framework) — Agent Loop 原型（v1→v2→v3）
- rag-project — 金融 RAG 问答系统（年报知识库，ChromaDB 三集合）
