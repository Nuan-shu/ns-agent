# NsAgent 编码规范

> 从现有 16 个源文件中提取的写作约定。新增文件必须遵循本文档。

---

## 1. 文件结构

### 1.1 模块文档字符串

每个 `.py` 文件**必须**以模块级 docstring 开头，用中文简要说明职责：

```python
"""文件职责的一句话描述。"""
```

| 文件类型 | 示例 |
|----------|------|
| 工具文件 | `"""获取当前时间的工具。"""` |
| 核心模块 | `"""NsAgent 核心 — Agent Loop。..."""` |
| 入口文件 | `"""NsAgent 入口 — 加载工具 → 启动 Agent。"""` |

分隔符统一用 `—`（全角破折号）。

### 1.2 导入顺序

1. **标准库**（stdlib）
2. **第三方库**（pip install 的）
3. **项目内部模块**（`from tools.xxx import`、`from core.xxx import`）

每组之间空一行。示例：

```python
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from tools.registry import get_tool_definitions, execute
from memory import session as sess
```

**禁止**：`from module import *`（通配符导入）。

### 1.3 `__init__.py`

空文件，仅作为包识别标记。不加任何代码。

---

## 2. 命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 函数 | `snake_case` | `get_stock_price`、`run_command` |
| 变量 | `snake_case` | `session_id`、`query_vec` |
| 常量 | `UPPER_CASE` | `MAX_RETRIES`、`CHROMA_PATH` |
| 类 | `PascalCase` | `NsAgentError`、`APIError` |
| 私有模块级变量 | `_prefix` | `_registry`、`_client` |
| 私有函数 | `_prefix` | `_connect()` |

---

## 3. 工具定义规范

### 3.1 定义常量

每个工具配一个 JSON Schema 定义常量，命名 `XXX_DEF`：

```python
PRICE_DEF = {
    "type": "function",
    "function": {
        "name": "get_stock_price",
        "description": "查询 A 股实时行情，返回最新价、涨跌幅、成交量、成交额",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "股票代码，如 600519（茅台）"
                }
            },
            "required": ["code"]
        }
    }
}
```

**要点**：
- 常量名 = `功能名大写_DEF`（如 `PRICE_DEF`、`SEARCH_DEF`、`TERMINAL_DEF`）
- `description` 用中文，清晰说明工具做什么
- `parameters` 的 `description` 用中文
- `required` 列出必填参数

### 3.2 处理函数

函数签名直接接收关键字参数（因为 `execute()` 用 `**args` 展开）：

```python
def get_stock_price(code):
    """查询 A 股实时价格"""
    ...
```

**不需要** `def get_stock_price(args)` 再自己取 `args.get("code")`。

### 3.3 注册

文件末尾一行注册：

```python
register("get_stock_price", PRICE_DEF, get_stock_price)
```

### 3.4 错误处理

工具函数**返回错误字符串**，不抛异常：

```python
try:
    ...
except Exception as e:
    return f"查询失败: {e}"
```

---

## 4. 文档字符串

所有公共函数必须有 docstring：

```python
def unified_search(query, top_k=5):
    """并行搜索所有知识库，按相关度合并返回。

    返回格式：
    [
        {"source": "annual_reports", "content": "...", "distance": 0.23},
    ]
    """
```

- 单行功能 → 一行 docstring
- 复杂功能 → 多行，首行概述，空一行后详细说明

---

## 5. 注释

| 用途 | 风格 |
|------|------|
| 代码区块 | `# === 初始化 ===`（前后等号，居中对齐） |
| 解释原因 | `# 离线模式，避免 sentence-transformers 直连 huggingface` |
| 参数说明 | 行内 `# 秒：1 → 2 → 4` |

**不写**「这行做了什么」（代码自解释），**写**「为什么这样做」。

---

## 6. 入口文件 main.py

`main.py` 只做两件事：
1. `import` 所有工具模块 → 触发 `register()`
2. 调用 `chat()`

```python
"""NsAgent 入口 — 加载工具 → 启动 Agent。"""
import tools.time_tool       # noqa: F401
import tools.file_tools      # noqa: F401
import tools.finance.market_data  # noqa: F401

from core.agent import chat

if __name__ == "__main__":
    chat()
```

新增工具后只需加一行 `import`。

---

## 7. 间距与格式

- 顶层函数之间：**2 个空行**
- 类内方法之间：**1 个空行**
- 导入组之间：**1 个空行**
- 行尾不要空格
- 所有字符串用双引号 `"`

---

## 8. 配置与环境

- API 密钥：`.env` 文件 + `python-dotenv`，不硬编码
- 路径：用 `Path(__file__).parent` 相对计算，不写死绝对路径
- 私有连接：模块级 `_client`、`_embed_model` 懒初始化

---

## 9. 新增文件检查清单

- [ ] 模块 docstring 已在第一行
- [ ] 导入顺序：stdlib → 第三方 → 项目内
- [ ] 命名：函数 snake_case，常量 UPPER，类 PascalCase
- [ ] 工具：XXX_DEF + handler 函数 + register()
- [ ] handler 签名匹配 `execute()` 的 `**args` 展开方式
- [ ] 错误返回字符串，不抛异常（工具层）
- [ ] main.py 已加 import
- [ ] 无通配符导入、无 trailing whitespace

---

## 10. 模块依赖原则

### 工具层不得直接访问 ChromaDB

任何涉及知识库搜索的工具，**必须**调用 `knowledge/search.py` 的公开接口（`unified_search()` 或 `search_formatted()`），**禁止**直接 `import chromadb` 或操作 `_client`、`_embed_model`。

```python
# ✓ 正确：薄封装，不重复搜索逻辑
from knowledge.search import unified_search

# ✗ 错误：重复造轮子
import chromadb
from knowledge.search import _client, _embed_model
```

**原因**：搜索逻辑的唯一真相源是 `knowledge/search.py`。未来换模型、换向量库、调参数只改一处。工具层只做薄封装（调搜索 + 格式化输出）。

### 新增工具前先问

写任何新工具前，先回答三个问题：
1. 有没有已有模块能做这件事？（如搜索 → `unified_search`）
2. 我这个工具是「新能力」还是「薄封装」？
3. 如果是薄封装，调了哪个已有接口？
