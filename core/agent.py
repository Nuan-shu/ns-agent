"""NsAgent 核心 — Agent Loop。不关心工具有哪些，只从注册表读取。"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv  # pyright: ignore
from openai import OpenAI

from core.context import compress, count_messages_tokens
from core.errors import NsAgentError
from core.prompt import build_prompt
from core.retry import call_with_retry
from memory import session as sess
from skills.registry import inject_skills, match_skills
from tools.registry import execute, get_tool_definitions

# 加载 .env（agent.py 在 core/ 下，.env 在项目根目录）
load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")


def run(messages=None, session_id=None):
    """启动 Agent Loop。messages 为初始消息列表。"""
    if messages is None:
        messages = [{"role": "system", "content": build_prompt()}]

    # 获取已注册的工具列表
    tools = get_tool_definitions()
    print(f"[NsAgent] 已加载 {len(tools)} 个工具\n")

    while True:
        # 上下文压缩：超过阈值时自动总结旧消息
        token_count = count_messages_tokens(messages)
        if token_count > 4000:
            messages, summary = compress(messages)
            if summary:
                print(f"  [压缩] {token_count} → {count_messages_tokens(messages)} tokens")

        print(f">>> 发送请求（{len(messages)} 条消息）...")

        response = call_with_retry(
            client.chat.completions.create,
            model="deepseek-chat",
            messages=messages,
            tools=tools if tools else None,
            temperature=0.7,
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
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": name, "arguments": tc.function.arguments},
                        }
                    ],
                }
            )
            if session_id:
                sess.save_message(session_id, messages[-1])
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
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
        messages = [{"role": "system", "content": build_prompt()}]
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
            messages = [{"role": "system", "content": build_prompt()}]
            sess.save_message(session_id, messages[0])
            print("新会话已开始。")
            continue

        snapshot = len(messages)
        messages.append({"role": "user", "content": user_input})
        sess.save_message(session_id, messages[-1])

        # 技能匹配：如果用户输入触发了技能，注入 System Prompt
        matched = match_skills(user_input)
        if matched:
            print(f"  [技能] 激活了 {len(matched)} 个技能")
            messages = inject_skills(messages, matched)

        try:
            run(messages=messages, session_id=session_id)
        except NsAgentError as e:
            print(f"NsAgent 错误 [{e.code}]: {e.message}")
            del messages[snapshot:]
        except Exception as e:
            print(f"未预期错误: {type(e).__name__}: {e}")
            del messages[snapshot:]
