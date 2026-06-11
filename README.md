# NsAgent

统一 AI Agent 框架 — 1 个 Agent + N 个工具集。

## 架构

```
ns-agent/
├── main.py              # 入口：加载工具 → 启动 REPL
├── core/
│   └── agent.py         # Agent Loop（while True → LLM → 工具调用）
├── tools/
│   ├── registry.py      # 工具注册表（加工具只改这里，不改 loop）
│   ├── time_tool.py     # get_current_time
│   ├── file_tools.py    # read_file / write_file
│   ├── terminal_tool.py # 终端命令执行
│   └── search_tool.py   # 知识库搜索
├── knowledge/
│   └── search.py        # 统一多源搜索（年报 + Agent 文档 + Wiki）
└── memory/              # 会话持久化（开发中）
```

## 核心设计

**工具注册表**：加新工具 = 新建一个文件 + 一行 `register()`。Agent Loop 不需要改。

**统一多源搜索**：一个查询并行搜索 ChromaDB 中的多个知识库（年报 1683 块 + Agent 文档 27 块 + Wiki 待入库），按相关度合并返回。

## 路线图

- [x] v0.1.0 — 框架筑基：工具注册表 + 多源搜索 + Agent Loop
- [ ] v0.2.0 — Wiki 入库 + 会话持久化
- [ ] v0.3.0 — 金融工具集（行情/筛选/报告）
- [ ] v0.4.0 — 企业级特性（安全 + 子 Agent + 流式输出）

## 运行

```bash
cd ns-agent
python main.py
```

依赖：`openai`、`chromadb`、`sentence-transformers`、`python-dotenv`

## 关联项目

- [agent-framework](https://github.com/Nuan-shu/agent-framework) — Agent Loop 原型（v1→v2→v3）
- rag-project — 金融 RAG 问答系统（年报知识库）
