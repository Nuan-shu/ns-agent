"""NsAgent 核心 — Agent Loop。不关心工具有哪些，只从注册表读取。"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv  # pyright: ignore
from openai import OpenAI

from tools.registry import get_tool_definitions, execute
from memory import session as sess
from core.retry import call_with_retry
from core.errors import NsAgentError

# 加载 .env（agent.py 在 core/ 下，.env 在项目根目录）
load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = """你是 NsAgent，一个本地 AI 助手。

你有以下工具可以使用：
- read_file: 读取文件
- write_file: 写入文件
- terminal: 执行终端命令
- search_knowledge: 搜索本地知识库（年报、技术文档）
- get_current_time: 获取当前时间

工作原则：
1. 先搜索知识库再回答
2. 修改文件前先 read_file 确认内容 3. 用中文回复"""


def run(messages=None, session_id=None):
    """启动 Agent Loop。messages 为初始消息列表。"""
    if messages is None:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 获取已注册的工具列表
    tools = get_tool_definitions()
    print(f"[NsAgent] 已加载 {len(tools)} 个工具\n")
    
    while True:
        print(f">>> 发送请求（{len(messages)} 条消息）...")
        
        response = call_with_retry(
            client.chat.completions.create,
            model="deepseek-chat",
            messages=messages,
            tools=tools if tools else None,
            temperature=0.7
        )
        
        msg = response.choices[0].message
        
        # 没有工具调用 → 输出回复 → 结束
        if not msg.tool_calls:
            print(f"\n{msg.content}\n")
            break
        
        # 处理工具调用
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            print(f"  🔧 {name}({json.dumps(args, ensure_ascii=False)})")
            
            result = execute(name, args)
            print(f"     → {result[:100]}...")
            
            # 把工具调用和结果加入消息历史
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": name, "arguments": tc.function.arguments}
                }]
            })
            if session_id:
                sess.save_message(session_id, messages[-1])
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result)
            })
            if session_id:
                sess.save_message(session_id, messages[-1])


def chat():
    """交互式 REPL。自动恢复 24h 内会话。"""
    sess.init_db()
    session_id = sess.get_last_session()

    if session_id:
        old_messages = sess.load_session(session_id)
        print(f"NsAgent v0.1.0 — 恢复了上次会话（{len(old_messages)} 条消息）")
        print("输入 /new 开始新会话，/exit 退出\n")
        messages = old_messages
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        session_id = sess.create_session()
        sess.save_message(session_id, messages[0])
        print("NsAgent v0.1.0 — 输入 /exit 退出\n")

    while True:
        user_input = input("你: ").strip()
        if not user_input:
            continue
        if user_input == "/exit":
            print(f"会话 {session_id} 已保存，再见。")
            break
        if user_input == "/new":
            session_id = sess.create_session()
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            sess.save_message(session_id, messages[0])
            print("新会话已开始。")
            continue

        snapshot = len(messages)
        messages.append({"role": "user", "content": user_input})
        sess.save_message(session_id, messages[-1])
        try:
            run(messages=messages, session_id=session_id)
        except NsAgentError as e:
            print(f"NsAgent 错误 [{e.code}]: {e.message}")
            del messages[snapshot:]
        except Exception as e:
            print(f"未预期错误: {type(e).__name__}: {e}")
            del messages[snapshot:]
